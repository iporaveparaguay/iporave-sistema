"""
ORQUESTADOR PAGINAS — Iporave Connect
Especializado en paginas publicas (tracking.html, faq.html, contacto.html, etc)
Modelos: Groq/Cerebras GRATIS (archivos pequenos)
Costo: $0

Uso: python orquestador-paginas.py
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
INTERVALO_SEG  = 110
AGENTE_NOMBRE  = "Orquestador-Paginas"

PAGINAS_DIR = Path(r"C:\Users\USUARIO\iporave-sistema\public")
PAGINAS = ["tracking.html", "faq.html", "contacto.html", "terminos.html", "nosotros.html", "404.html"]

MODELOS_CASCADA = [
    "groq/llama-3.3-70b-versatile",
    "cerebras/llama3.1-8b",
    "openrouter/qwen/qwen-2.5-coder-32b-instruct",
    "ollama/qwen2.5-coder:7b",
]

sesion = {"ciclos": 0, "completadas": []}
fallos_por_tarea = {}

WRAPPER = str(Path(__file__).parent / "aider-wrapper.py")

_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from orq_base import verificar_parada_critica

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

def reportar(tarea, estado, resumen):
    body = json.dumps({"agente": AGENTE_NOMBRE, "tarea": tarea,
                       "archivos": "paginas-publicas", "estado": estado, "resumen": resumen}).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

def leer_siguiente_tarea():
    if not ORQUESTADOR_MD.exists(): return None
    try:
        for linea in ORQUESTADOR_MD.read_text(encoding="utf-8").splitlines():
            if "- [ ]" in linea and "paginas-" in linea.lower():
                parte = linea.strip()[5:].strip()
                nombre = parte.split("**")[1].strip() if "**" in parte else "tarea-paginas"
                instruccion = parte.split("**")[-1].strip(" —-") if "**" in parte else parte
                # Aplicar a todas las paginas publicas
                return {"mensaje": instruccion, "nombre": nombre, "archivos": PAGINAS}
    except: pass
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
    env = cargar_env()
    for modelo in MODELOS_CASCADA:
        try:
            result = subprocess.run(
                [sys.executable, WRAPPER, "--model", modelo, "--yes", "--no-git",
                 "--no-auto-commits", "--no-show-model-warnings",
                 "--message", mensaje, str(archivo)],
                capture_output=True, text=True, timeout=120,
                env=env, input="N\n"
            )
            salida = result.stdout + result.stderr
            if result.returncode == 0:
                return True, salida[-800:]
            if any(x in salida for x in ["quota", "rate limit", "context", "403", "401"]):
                continue
            return False, salida[-800:]
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    return False, "TODOS LOS MODELOS FALLARON — revisar credenciales"

def ciclo():
    sesion["ciclos"] += 1
    print(f"\n{'='*50}")
    print(f"  [{AGENTE_NOMBRE}] Ciclo {sesion['ciclos']} | {time.strftime('%H:%M:%S')}")

    if verificar_parada_critica():
        return

    tarea = leer_siguiente_tarea()
    if not tarea:
        print("  Sin tareas de paginas pendientes.")
        return

    nombre   = tarea["nombre"]
    mensaje  = tarea["mensaje"]
    archivos = tarea["archivos"]
    exitosos = []

    for pagina in archivos:
        ruta = PAGINAS_DIR / pagina
        if not ruta.exists():
            continue
        print(f"  Procesando: {pagina}")
        exito, _ = correr_aider(mensaje, ruta)
        if exito:
            exitosos.append(pagina)

    if exitosos:
        if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
            print("  Auto-commit desactivado. Cambios aplicados, sin git push.")
            marcar_completada(nombre)
            reportar(nombre, "Finalizado", f"Aplicado en: {exitosos}. Pendiente revision humana. Costo: $0")
            sesion["completadas"].append(nombre)
            return
        # Commit todo junto
        for f in exitosos:
            subprocess.run(["git", "add", f"public/{f}"], cwd=FRONTEND_DIR, timeout=15)
        subprocess.run(["git", "commit", "-m",
                        f"feat: {nombre} — paginas publicas [{', '.join(exitosos[:3])}]"],
                       cwd=FRONTEND_DIR, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], cwd=FRONTEND_DIR, timeout=60)
        marcar_completada(nombre)
        reportar(nombre, "Finalizado", f"Aplicado en: {exitosos}. Costo: $0")
        sesion["completadas"].append(nombre)
        print(f"  COMPLETADO: {nombre} en {len(exitosos)} paginas")

if __name__ == "__main__":
    print(f"{AGENTE_NOMBRE} | Zona: paginas publicas | Costo: $0")
    while True:
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\nDetenido.")
            break
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(INTERVALO_SEG)
