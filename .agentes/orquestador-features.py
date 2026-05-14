"""
ORQUESTADOR FEATURES — Iporave Connect
Especializado en features JS medianas del index.html (zonas especificas, no CSS)
Usa Gemini 2.5 Flash para JS complejo en index.html
Costo: ~$0.015/tarea

Uso: python orquestador-features.py
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT   = "rugged-shell-430212-f6"
LOCATION  = "us-central1"
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"
CLAVE_JSON     = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
ARCHIVO        = r"C:\Users\USUARIO\iporave-sistema\public\index.html"
INTERVALO_SEG  = 130
AGENTE_NOMBRE  = "Orquestador-Features"

# Importar utilidades base
_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from orq_base import verificar_parada_critica, ejecutar_con_reintentos

# Solo modelos con 1M contexto — index.html es demasiado grande para otros
MODELOS_CASCADA = [
    "vertex_ai/gemini-2.5-flash-lite",
    "vertex_ai/gemini-2.5-flash",
]

COSTO_MODELO = {
    "vertex_ai/gemini-2.5-flash-lite": 0.000010,
    "vertex_ai/gemini-2.5-flash": 0.000075,
}

sesion = {"ciclos": 0, "completadas": [], "costo": 0.0}
fallos_por_tarea = {}

WRAPPER = str(Path(__file__).parent / "aider-wrapper.py")

# ─── ENV ──────────────────────────────────────────────────────────────────────
def cargar_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["AIDER_NO_BROWSER"] = "1"
    env["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
    env["VERTEXAI_PROJECT"] = PROJECT
    env["VERTEXAI_LOCATION"] = LOCATION
    try:
        with open(KEYS_PATH, encoding="utf-8") as f:
            keys = json.load(f)
        env["OPENROUTER_API_KEY"] = keys.get("openrouter", "")
    except: pass
    return env

# ─── PIZARRÓN ─────────────────────────────────────────────────────────────────
def reportar(tarea, estado, resumen):
    body = json.dumps({"agente": AGENTE_NOMBRE, "tarea": tarea,
                       "archivos": "index.html", "estado": estado, "resumen": resumen}).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

# ─── LEER TAREA ───────────────────────────────────────────────────────────────
def leer_siguiente_tarea():
    """Lee la primera tarea feature-* pendiente [ ] del index.html"""
    if not ORQUESTADOR_MD.exists(): return None
    try:
        for linea in ORQUESTADOR_MD.read_text(encoding="utf-8").splitlines():
            if "- [ ]" in linea and "feature-" in linea.lower():
                parte = linea.strip()[5:].strip()
                nombre = parte.split("**")[1].strip() if "**" in parte else "tarea-feature"
                instruccion = parte.split("**")[-1].strip(" —-") if "**" in parte else parte
                return {"mensaje": instruccion, "nombre": nombre}
    except: pass
    return None

# ─── EJECUTAR AIDER ───────────────────────────────────────────────────────────
def correr_aider(mensaje):
    env = cargar_env()
    for modelo in MODELOS_CASCADA:
        print(f"  Modelo: {modelo}")
        try:
            result = subprocess.run(
                [sys.executable, WRAPPER, "--model", modelo, "--yes", "--no-git",
                 "--no-auto-commits", "--no-show-model-warnings",
                 "--message", mensaje, ARCHIVO],
                capture_output=True, text=True, timeout=300,
                env=env, input="N\n"
            )
            salida = result.stdout + result.stderr
            if result.returncode == 0:
                tokens = len(mensaje) // 4
                sesion["costo"] += tokens * COSTO_MODELO.get(modelo, 0.0) / 1000
                return True, salida[-1500:], modelo
            if any(x in salida for x in ["quota", "RESOURCE_EXHAUSTED", "403", "context length", "rate limit"]):
                print(f"  {modelo} sin cuota — escalando...")
                continue
            return False, salida[-1500:], modelo
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue
    return False, "TODOS LOS MODELOS FALLARON", "ninguno"

# ─── VALIDAR ──────────────────────────────────────────────────────────────────
def validar():
    result = subprocess.run(["node", "validate.js"], cwd=FRONTEND_DIR,
                            capture_output=True, text=True, timeout=30)
    if "Todo OK" in result.stdout:
        return True, ""
    return False, (result.stdout + result.stderr)[-500:]

# ─── CICLO ────────────────────────────────────────────────────────────────────
# ⛔ MODO SEGURO ACTIVADO (2026-05-14): Este orquestador NO toca index.html.
# Las tareas feature-* se reportan como DELEGADA-HUMANO y las resuelve Claude humano.
# Razón: Aider sobre Windows tiene UnicodeEncodeError que destruyó 9205 líneas
# de index.html en una sesión anterior. Defensa en profundidad.
_tareas_ya_delegadas = set()

def ciclo():
    sesion["ciclos"] += 1
    print(f"\n{'='*55}")
    print(f"  [{AGENTE_NOMBRE}] Ciclo {sesion['ciclos']} | MODO SEGURO (no toca index.html)")

    # Verificar parada crítica
    if verificar_parada_critica():
        return

    tarea = leer_siguiente_tarea()
    if not tarea:
        print("  Sin tareas feature pendientes.")
        return

    nombre  = tarea["nombre"]
    mensaje = tarea["mensaje"]
    print(f"  Tarea: {nombre} — DELEGANDO a humano (modo seguro)")

    # Solo reportar UNA VEZ por tarea para no spamear el pizarrón
    if nombre in _tareas_ya_delegadas:
        return
    _tareas_ya_delegadas.add(nombre)

    reportar(nombre, "DELEGADA-HUMANO",
             f"Tarea sobre index.html requiere intervención humana (Aider deshabilitado por seguridad). Instrucción original: {mensaje[:200]}")
    print(f"  ✅ {nombre} marcada como DELEGADA-HUMANO en pizarrón")

if __name__ == "__main__":
    print(f"{AGENTE_NOMBRE} | Zona: index.html features JS | Solo modelos 1M ctx")
    while True:
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\nDetenido.")
            break
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(INTERVALO_SEG)
