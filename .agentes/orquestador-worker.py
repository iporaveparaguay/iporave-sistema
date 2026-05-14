"""
ORQUESTADOR WORKER — Iporave Connect
Especializado en archivos del Worker API (src/api/*.js)
Usa modelos GRATIS: Groq, Cerebras, OpenRouter
Costo: $0

Uso: python orquestador-worker.py
"""

import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PIZARRON_URL  = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
LOG_DIR        = Path(__file__).parent / "logs"
WORKER_DIR     = r"C:\Users\USUARIO\iporave-worker"
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
INTERVALO_SEG  = 90
ZONA           = "worker"
AGENTE_NOMBRE  = "Orquestador-Worker"

ARCHIVOS_PROHIBIDOS = ["utils.js", "login.js", "verifyToken", "SAFE_SELF_FIELDS"]

# Modelos GRATIS → luego DeepSeek (usa saldo hasta que se acabe) → Gemini como respaldo
# DeepSeek: costo casi cero, 128k ctx — perfecto para archivos Worker pequeños
# Cuando DeepSeek se quede sin saldo, falla silenciosamente y pasa al siguiente
MODELOS_CASCADA = [
    "groq/llama-3.3-70b-versatile",          # GRATIS, 128k ctx
    "cerebras/llama3.1-8b",                   # GRATIS, rápido
    "openrouter/qwen/qwen-2.5-coder-32b-instruct",  # GRATIS OpenRouter
    "ollama/qwen2.5-coder:7b",                # GRATIS local
    "openrouter/deepseek/deepseek-chat",      # Saldo hasta $0 → falla → siguiente
    "vertex_ai/gemini-2.5-flash-lite",        # Último recurso pago (barato)
]

sesion = {"ciclos": 0, "completadas": [], "fallidas": []}
fallos_por_tarea = {}

WRAPPER = str(Path(__file__).parent / "aider-wrapper.py")

# Importar utilidades base
_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from orq_base import verificar_parada_critica, ejecutar_con_reintentos, marcar_completada as _base_marcar_completada

def cargar_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["AIDER_NO_BROWSER"] = "1"
    try:
        with open(KEYS_PATH, encoding="utf-8") as f:
            keys = json.load(f)
        env["GROQ_API_KEY"]       = keys.get("groq", "")
        env["CEREBRAS_API_KEY"]   = keys.get("cerebras", "")
        env["OPENROUTER_API_KEY"] = keys.get("openrouter", "")
    except: pass
    return env

def reportar(tarea, archivos, estado, resumen):
    body = json.dumps({"agente": AGENTE_NOMBRE, "tarea": tarea,
                       "archivos": archivos, "estado": estado, "resumen": resumen}).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

def leer_pizarron():
    try:
        req = urllib.request.Request(PIZARRON_URL, headers={
            "Accept": "application/json",
            "User-Agent": "IporaveAgent/1.0"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("registros", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    except: return []

def leer_siguiente_tarea_worker():
    if not ORQUESTADOR_MD.exists(): return None
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        for linea in contenido.splitlines():
            if "- [ ]" in linea and "worker-" in linea.lower():
                parte = linea.strip()[5:].strip()
                nombre = parte.split("**")[1].strip() if "**" in parte else "tarea-worker"
                instruccion = parte.split("**")[-1].strip(" —-") if "**" in parte else parte
                # Inferir nombre de archivo JS
                nombre_js = nombre.replace("worker-", "") + ".js"
                archivo = fr"C:\Users\USUARIO\iporave-worker\src\api\{nombre_js}"
                if Path(archivo).exists():
                    return {"archivo": archivo, "mensaje": instruccion, "nombre": nombre}
    except Exception as e:
        print(f"  [cola] Error: {e}")
    return None

def marcar_completada(nombre):
    if not ORQUESTADOR_MD.exists(): return
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        nuevo = [l.replace("- [ ]", "- [x]", 1) if f"**{nombre}**" in l and "- [ ]" in l else l
                 for l in contenido.splitlines()]
        ORQUESTADOR_MD.write_text("\n".join(nuevo), encoding="utf-8")
    except: pass

def correr_aider(mensaje, archivo):
    for prohibido in ARCHIVOS_PROHIBIDOS:
        if prohibido in archivo:
            return False, f"BLOQUEADO: {archivo}"
    env = cargar_env()
    for modelo in MODELOS_CASCADA:
        print(f"  Modelo: {modelo}")
        try:
            result = subprocess.run(
                [sys.executable, WRAPPER, "--model", modelo, "--yes", "--no-git",
                 "--no-auto-commits", "--no-show-model-warnings",
                 "--message", mensaje, archivo],
                capture_output=True, text=True, timeout=180,
                env=env, input="N\n"
            )
            salida = result.stdout + result.stderr
            if result.returncode == 0:
                return True, salida[-1500:]
            if any(x in salida for x in ["quota", "RESOURCE_EXHAUSTED", "403", "401", "API key", "rate limit"]):
                print(f"  {modelo} sin cuota — escalando...")
                continue
            return result.returncode == 0, salida[-1500:]
        except subprocess.TimeoutExpired:
            print(f"  Timeout con {modelo}")
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue
    return False, "TODOS LOS MODELOS FALLARON — revisar credenciales"

def validar_worker(archivo):
    try:
        result = subprocess.run(
            ["node", "--check", archivo],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except: return True  # si node no esta disponible, asumir OK

def git_commit_push(mensaje, archivo):
    if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
        print("  Auto-commit desactivado. No se suben cambios sin revision humana.")
        return True
    try:
        subprocess.run(["git", "add", archivo], cwd=WORKER_DIR, timeout=30)
        subprocess.run(["git", "commit", "-m", mensaje], cwd=WORKER_DIR, timeout=30)
        subprocess.run(["git", "push", "origin", "master"], cwd=WORKER_DIR, timeout=60)
        return True
    except: return False

def ciclo():
    sesion["ciclos"] += 1
    print(f"\n{'='*55}")
    print(f"  [{AGENTE_NOMBRE}] Ciclo {sesion['ciclos']} | {time.strftime('%H:%M:%S')}")
    print(f"{'='*55}")

    # Verificar parada crítica
    if verificar_parada_critica():
        return

    # Buscar tarea en cola
    tarea = leer_siguiente_tarea_worker()
    if not tarea:
        # Revisar comandos remotos
        pizarron = leer_pizarron()
        for entrada in reversed(pizarron):
            if entrada.get("agente") == "COMANDO-WORKER" and entrada.get("estado") == "Pendiente":
                tarea = {"archivo": entrada.get("archivos",""),
                         "mensaje": entrada.get("resumen",""),
                         "nombre": entrada.get("tarea","cmd-worker")}
                break
    if not tarea:
        print("  Sin tareas worker pendientes.")
        return

    archivo  = tarea["archivo"]
    mensaje  = tarea["mensaje"]
    nombre   = tarea["nombre"]
    print(f"  Tarea: {nombre} | {Path(archivo).name}")

    # Wrapper para correr_aider con signatura compatible con orq_base
    def fn_ejecutar(instruccion):
        exito, salida = correr_aider(instruccion, archivo)
        return exito, salida, "worker-models"

    def fn_validar():
        ok = validar_worker(archivo)
        return ok, ("node --check fallo: sintaxis JS invalida" if not ok else "")

    def fn_reportar(nom, estado, resumen):
        reportar(nom, archivo, estado, resumen)

    reportar(nombre, archivo, "En proceso", f"Worker ejecutando: {mensaje[:80]}")

    resultado = ejecutar_con_reintentos(
        nombre_tarea         = nombre,
        instruccion_original = mensaje,
        archivo_path         = archivo,
        fn_ejecutar          = fn_ejecutar,
        fn_validar           = fn_validar,
        agente               = AGENTE_NOMBRE,
        fn_reportar          = fn_reportar,
        fallos_por_tarea     = fallos_por_tarea,
    )

    if resultado == "completada":
        hora = datetime.now().strftime("%H:%M")
        git_commit_push(f"feat: {nombre} — orquestador-worker", archivo)
        sesion["completadas"].append({"hora": hora, "nombre": nombre})
        print(f"  ✅ COMPLETADO: {nombre} (pusheado a master)")

    elif resultado == "parada_critica":
        print(f"  ⛔ Parada crítica — deteniendo agente")
        sys.exit(1)

if __name__ == "__main__":
    print(f"{AGENTE_NOMBRE} iniciando | Modelos: GRATIS | Zona: Worker API")
    print(f"Intervalo: {INTERVALO_SEG}s\n")
    LOG_DIR.mkdir(exist_ok=True)
    while True:
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\nDetenido.")
            break
        except Exception as e:
            print(f"  Error: {e}")
            reportar("ciclo-error", "-", "Error", str(e)[:150])
        time.sleep(INTERVALO_SEG)
