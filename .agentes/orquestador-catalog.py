"""
ORQUESTADOR CATALOG / ANTIGRAVITY — Iporave Connect
Especializado en catalog.html (tienda publica) y mejoras visuales del sistema.

Lógica Antigravity:
  1. Primero busca tareas catalog-* pendientes → las hace
  2. Si no hay tareas catalog, busca visual-* de index.html que no estén en uso
  3. Si index.html está en uso, busca tareas de paginas públicas (paginas-*)
  4. Si todo está ocupado → espera al próximo ciclo

Modelos: Gemini Flash (solo 1M ctx)
Costo: mínimo

Uso: python orquestador-catalog.py
"""

import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT        = "rugged-shell-430212-f6"
LOCATION       = "us-central1"
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"
CLAVE_JSON     = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
ARCHIVO_CATALOG = r"C:\Users\USUARIO\iporave-sistema\public\catalog.html"
ARCHIVO_INDEX   = r"C:\Users\USUARIO\iporave-sistema\public\index.html"
PAGINAS_DIR     = Path(r"C:\Users\USUARIO\iporave-sistema\public")
INTERVALO_SEG   = 100
AGENTE_NOMBRE   = "Orquestador-Catalog"

# Importar utilidades base
_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from orq_base import verificar_parada_critica, ejecutar_con_reintentos
from lock_util import archivo_en_uso

# Modelos con contexto largo
MODELOS_CASCADA = [
    "vertex_ai/gemini-2.5-flash-lite",
    "vertex_ai/gemini-2.5-flash",
]

COSTO_MODELO = {
    "vertex_ai/gemini-2.5-flash-lite": 0.000010,
    "vertex_ai/gemini-2.5-flash":      0.000075,
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
        env["GROQ_API_KEY"]       = keys.get("groq", "")
        env["OPENROUTER_API_KEY"] = keys.get("openrouter", "")
    except: pass
    return env

# ─── PIZARRÓN ─────────────────────────────────────────────────────────────────
def reportar(tarea, estado, resumen):
    body = json.dumps({"agente": AGENTE_NOMBRE, "tarea": tarea,
                       "archivos": "-", "estado": estado, "resumen": resumen}).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

# ─── BUSCAR TAREA — LÓGICA ANTIGRAVITY ────────────────────────────────────────
def buscar_tarea():
    """
    Busca la próxima tarea según prioridad Antigravity:
    1. Tareas catalog-* del catalog.html → su zona natural
    2. Tareas visual-* del index.html si no está en uso por otro agente
    3. Tareas paginas-* de páginas públicas si index.html está ocupado
    4. Nada → esperar

    Retorna: dict con {mensaje, nombre, archivo} o None
    """
    if not ORQUESTADOR_MD.exists():
        return None

    lineas = ORQUESTADOR_MD.read_text(encoding="utf-8").splitlines()

    # Prioridad 1: tareas catalog
    for linea in lineas:
        if "- [ ]" in linea and "catalog-" in linea.lower():
            nombre, instruccion = _parsear_tarea(linea)
            return {"nombre": nombre, "mensaje": instruccion, "archivo": ARCHIVO_CATALOG}

    # Prioridad 2: visual-* del index.html si no está ocupado
    index_en_uso, quien = archivo_en_uso(ARCHIVO_INDEX)
    if not index_en_uso:
        for linea in lineas:
            if "- [ ]" in linea and "visual-" in linea.lower():
                nombre, instruccion = _parsear_tarea(linea)
                return {"nombre": nombre, "mensaje": instruccion, "archivo": ARCHIVO_INDEX}
    else:
        print(f"  [Antigravity] index.html en uso por {quien} — buscando alternativa...")

    # Prioridad 3: paginas públicas si están libres
    PAGINAS = ["tracking.html", "faq.html", "contacto.html", "terminos.html",
               "nosotros.html", "404.html"]
    for linea in lineas:
        if "- [ ]" in linea and "paginas-" in linea.lower():
            nombre, instruccion = _parsear_tarea(linea)
            # Inferir archivo de la instrucción
            archivo_pagina = str(PAGINAS_DIR / PAGINAS[0])  # default
            for p in PAGINAS:
                if p.replace(".html", "") in instruccion.lower():
                    archivo_pagina = str(PAGINAS_DIR / p)
                    break
            pagina_en_uso, _ = archivo_en_uso(archivo_pagina)
            if not pagina_en_uso:
                return {"nombre": nombre, "mensaje": instruccion, "archivo": archivo_pagina}

    return None

def _parsear_tarea(linea):
    parte = linea.strip()[5:].strip()  # quitar "- [ ]"
    nombre = parte.split("**")[1].strip() if "**" in parte else "tarea-antigravity"
    instruccion = parte.split("**")[-1].strip(" —-") if "**" in parte else parte
    return nombre, instruccion

# ─── EJECUTAR AIDER ───────────────────────────────────────────────────────────
_archivo_actual = None  # se asigna en ciclo()

def correr_aider(mensaje):
    env = cargar_env()
    for modelo in MODELOS_CASCADA:
        print(f"  Modelo: {modelo}")
        try:
            result = subprocess.run(
                [sys.executable, WRAPPER, "--model", modelo, "--yes", "--no-git",
                 "--no-auto-commits", "--no-show-model-warnings",
                 "--message", mensaje, _archivo_actual],
                capture_output=True, text=True, timeout=300,
                env=env, input="N\n"
            )
            salida = result.stdout + result.stderr
            if result.returncode == 0:
                tokens = len(mensaje) // 4
                sesion["costo"] += tokens * COSTO_MODELO.get(modelo, 0.0) / 1000
                return True, salida[-1500:], modelo
            if any(x in salida for x in ["quota", "RESOURCE_EXHAUSTED", "403", "rate limit", "context length"]):
                print(f"  {modelo} sin cuota — escalando...")
                continue
            return False, salida[-1500:], modelo
        except subprocess.TimeoutExpired:
            print(f"  Timeout {modelo}")
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
def ciclo():
    global _archivo_actual
    sesion["ciclos"] += 1
    print(f"\n{'='*55}")
    print(f"  [{AGENTE_NOMBRE}/Antigravity] Ciclo {sesion['ciclos']} | ${sesion['costo']:.4f}")

    # Verificar parada crítica
    if verificar_parada_critica():
        return

    tarea = buscar_tarea()
    if not tarea:
        print("  Sin tareas disponibles en este ciclo. Esperando...")
        return

    nombre        = tarea["nombre"]
    mensaje       = tarea["mensaje"]
    _archivo_actual = tarea["archivo"]
    nombre_archivo = Path(_archivo_actual).name

    print(f"  Tarea: {nombre} → {nombre_archivo}")
    reportar(nombre, "En proceso", f"[Antigravity/{nombre_archivo}] {mensaje[:80]}")

    resultado = ejecutar_con_reintentos(
        nombre_tarea         = nombre,
        instruccion_original = mensaje,
        archivo_path         = _archivo_actual,
        fn_ejecutar          = correr_aider,
        fn_validar           = validar,
        agente               = AGENTE_NOMBRE,
        fn_reportar          = reportar,
        fallos_por_tarea     = fallos_por_tarea,
    )

    if resultado == "completada":
        if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
            print("  Auto-commit desactivado. Cambios aplicados, sin git push.")
            sesion["completadas"].append(nombre)
            return
        # Determinar qué agregar al commit según archivo
        if "index.html" in _archivo_actual:
            git_add = "public/index.html"
        elif "catalog.html" in _archivo_actual:
            git_add = "public/catalog.html"
        else:
            git_add = f"public/{Path(_archivo_actual).name}"

        subprocess.run(["git", "add", git_add], cwd=FRONTEND_DIR, timeout=30)
        subprocess.run(["git", "commit", "-m",
                        f"feat: {nombre} — Antigravity [{nombre_archivo}]"],
                       cwd=FRONTEND_DIR, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], cwd=FRONTEND_DIR, timeout=60)
        sesion["completadas"].append(nombre)
        print(f"  ✅ COMPLETADO: {nombre} ({nombre_archivo}) | ${sesion['costo']:.4f}")

    elif resultado == "parada_critica":
        print(f"  ⛔ Parada crítica — deteniendo agente")
        sys.exit(1)

if __name__ == "__main__":
    print(f"{AGENTE_NOMBRE} (Antigravity) | Gemini cascade | Intervalo: {INTERVALO_SEG}s")
    print(f"Prioridad: catalog.html → visual index.html (si libre) → paginas publicas\n")
    while True:
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\nDetenido.")
            break
        except Exception as e:
            print(f"  Error en ciclo: {e}")
        time.sleep(INTERVALO_SEG)
