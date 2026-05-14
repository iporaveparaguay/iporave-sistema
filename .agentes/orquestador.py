"""
ORQUESTADOR AUTONOMO — Iporave Connect
Usa Gemini 2.5 Flash para decidir tareas y Aider para ejecutarlas.
Incluye: cascada de modelos, tracking de costos, log de contexto cada N ciclos.

Uso: python orquestador.py
Detener: Ctrl+C
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Fix encoding en Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT        = "rugged-shell-430212-f6"
LOCATION       = "us-central1"
MODEL          = "gemini-2.5-flash"
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
CLAVE_JSON     = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
WRAPPER        = str(Path(__file__).parent / "aider-wrapper.py")
LOG_DIR        = Path(__file__).parent / "logs"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"
WORKER_DIR     = r"C:\Users\USUARIO\iporave-worker"
INTERVALO_SEG  = 120   # revisar cada 2 minutos
LOG_CADA_N     = 5     # guardar log de contexto cada 5 ciclos (~10 min)

# ─── ARCHIVOS PROHIBIDOS (nunca tocar) ────────────────────────────────────────
ARCHIVOS_PROHIBIDOS = [
    "utils.js", "login.js", "verifyToken", "SAFE_SELF_FIELDS"
]

# ─── COSTO ESTIMADO POR MODELO (USD por 1000 tokens de input aprox.) ─────────
# Estos son estimados conservadores para control de gasto.
COSTO_POR_MODELO = {
    "vertex_ai/gemini-2.5-flash":      0.000075,   # $0.075 / 1M tokens
    "vertex_ai/gemini-2.5-flash-lite": 0.000010,   # $0.010 / 1M tokens
    "ollama/qwen2.5-coder:7b":         0.0,         # GRATIS local
    "ollama/qwen2.5-coder:32b":        0.0,         # GRATIS local
    "groq/llama-3.3-70b-versatile":    0.0,         # GRATIS tier Groq
}

# ─── ESTADO GLOBAL DE SESION ──────────────────────────────────────────────────
sesion = {
    "inicio": datetime.now().isoformat(),
    "ciclos": 0,
    "tareas_completadas": [],
    "tareas_fallidas": [],
    "costo_estimado_usd": 0.0,
    "modelo_actual": MODEL,
}

# Contador de fallos por tarea — después de MAX_FALLOS se salta
fallos_por_tarea = {}
MAX_FALLOS = 3

# Importar utilidades base
_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from orq_base import verificar_parada_critica

# ─── HELPER: llamar a Gemini via Vertex AI ────────────────────────────────────
def llamar_gemini(prompt: str) -> str:
    try:
        from google import genai
        from google.genai import types

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
        os.environ["VERTEXAI_PROJECT"] = PROJECT
        os.environ["VERTEXAI_LOCATION"] = LOCATION

        client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            )
        )
        # Estimar costo del ciclo de orquestacion (prompt ~3000 tokens)
        costo = 3000 * COSTO_POR_MODELO.get(f"vertex_ai/{MODEL}", 0.000075) / 1000
        sesion["costo_estimado_usd"] += costo
        return response.text.strip()
    except Exception as e:
        return f"ERROR_GEMINI: {e}"

# ─── HELPER: leer pizarron ────────────────────────────────────────────────────
def leer_pizarron() -> list:
    try:
        req = urllib.request.Request(PIZARRON_URL, headers={
            "Accept": "application/json",
            "User-Agent": "IporaveAgent/1.0"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("registros", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [pizarron] Error al leer: {e}")
        return []

# ─── HELPER: reportar al pizarron ─────────────────────────────────────────────
def reportar(tarea: str, archivos: str, estado: str, resumen: str):
    body = json.dumps({
        "agente": "Orquestador-Gemini",
        "tarea": tarea,
        "archivos": archivos,
        "estado": estado,
        "resumen": resumen
    }).encode()
    try:
        req = urllib.request.Request(
            PIZARRON_URL,
            data=body,
            headers={"Content-Type": "application/json",
                     "User-Agent": "IporaveAgent/1.0"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"  [pizarron] Reportado: {tarea} — {estado}")
    except Exception as e:
        print(f"  [pizarron] Error al reportar: {e}")

# ─── HELPER: leer siguiente tarea de la cola en ORQUESTADOR.md ───────────────
def leer_siguiente_tarea_cola() -> dict | None:
    """Lee la primera tarea [ ] pendiente de ORQUESTADOR.md y la retorna como dict."""
    if not ORQUESTADOR_MD.exists():
        return None
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        lineas = contenido.splitlines()
        for linea in lineas:
            if linea.strip().startswith("- [ ]"):
                # Formato: - [ ] **nombre-tarea** — instruccion. archivo inferido del contexto
                parte = linea.strip()[5:].strip()  # quitar "- [ ]"
                # Extraer nombre entre ** **
                nombre = "tarea-cola"
                instruccion = parte
                if "**" in parte:
                    nombre = parte.split("**")[1].strip()
                    instruccion = parte.split("**")[-1].strip(" —-")

                # Inferir archivo segun zona
                archivo = r"C:\Users\USUARIO\iporave-sistema\public\index.html"
                if "catalog" in nombre or "catalog" in instruccion.lower():
                    archivo = r"C:\Users\USUARIO\iporave-sistema\public\catalog.html"
                elif "worker" in nombre or any(x in instruccion.lower() for x in ["calificaciones","catalog-public","notif","geocode","order-status"]):
                    nombre_js = nombre.replace("worker-","") + ".js"
                    archivo = fr"C:\Users\USUARIO\iporave-worker\src\api\{nombre_js}"
                elif "paginas" in nombre:
                    archivo = r"C:\Users\USUARIO\iporave-sistema\public\index.html"

                return {"archivo": archivo, "mensaje": instruccion, "nombre": nombre}
    except Exception as e:
        print(f"  [cola] Error leyendo cola: {e}")
    return None

def marcar_tarea_completada(nombre: str):
    """Marca una tarea de la cola como completada [x]."""
    if not ORQUESTADOR_MD.exists():
        return
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        nuevo = []
        for linea in contenido.splitlines():
            if f"**{nombre}**" in linea and "- [ ]" in linea:
                linea = linea.replace("- [ ]", f"- [x]", 1)
            nuevo.append(linea)
        ORQUESTADOR_MD.write_text("\n".join(nuevo), encoding="utf-8")
        print(f"  [cola] Tarea marcada completada: {nombre}")
    except Exception as e:
        print(f"  [cola] Error marcando tarea: {e}")

def marcar_tarea_bloqueada(nombre: str):
    """Marca tarea como bloqueada [!] después de MAX_FALLOS intentos."""
    if not ORQUESTADOR_MD.exists():
        return
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        nuevo = []
        for linea in contenido.splitlines():
            if f"**{nombre}**" in linea and "- [ ]" in linea:
                linea = linea.replace("- [ ]", "- [!]", 1)
            nuevo.append(linea)
        ORQUESTADOR_MD.write_text("\n".join(nuevo), encoding="utf-8")
        print(f"  [cola] Tarea BLOQUEADA tras {MAX_FALLOS} fallos: {nombre}")
    except Exception as e:
        print(f"  [cola] Error marcando bloqueada: {e}")

# ─── HELPER: leer comandos remotos del pizarron (desde celular) ───────────────
def leer_comando_remoto() -> dict | None:
    """
    Lee el pizarron buscando entradas con agente=COMANDO y estado=Pendiente.
    Permite enviar tareas desde el celular via POST al pizarron.
    """
    try:
        pizarron = leer_pizarron()
        for entrada in reversed(pizarron):  # mas reciente primero
            if entrada.get("agente") == "COMANDO" and entrada.get("estado") == "Pendiente":
                print(f"  [comando remoto] Encontrado: {entrada.get('tarea')}")
                return {
                    "archivo": entrada.get("archivos", ""),
                    "mensaje": entrada.get("resumen", ""),
                    "nombre":  entrada.get("tarea", "cmd-remoto")
                }
    except Exception as e:
        print(f"  [comando remoto] Error: {e}")
    return None

# ─── HELPER: guardar log de contexto ──────────────────────────────────────────
def guardar_log_contexto():
    """
    Guarda un snapshot del estado actual en logs/estado_YYYY-MM-DD_HH-MM.md
    Permite que cualquier otro orquestador retome desde aqui si este se cae.
    """
    LOG_DIR.mkdir(exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_path = LOG_DIR / f"estado_{fecha}.md"

    completadas = "\n".join(
        f"- {t['hora']} | {t['nombre']} | {t['archivo']} | {t['modelo']} | ~${t['costo_usd']:.4f}"
        for t in sesion["tareas_completadas"]
    ) or "- (ninguna en esta sesion)"

    fallidas = "\n".join(
        f"- {t['hora']} | {t['nombre']} | motivo: {t['error'][:80]}"
        for t in sesion["tareas_fallidas"]
    ) or "- (ninguna)"

    contenido = f"""# Estado Orquestador — {fecha}

## Datos de sesion
- Inicio: {sesion['inicio']}
- Ciclos ejecutados: {sesion['ciclos']}
- Modelo principal: {sesion['modelo_actual']}
- **Costo estimado sesion: ${sesion['costo_estimado_usd']:.4f} USD**

## Tareas completadas esta sesion
{completadas}

## Tareas fallidas esta sesion
{fallidas}

## Para retomar
1. Leer ORQUESTADOR.md para contexto del proyecto
2. Leer este archivo para saber donde se quedo
3. Continuar con las tareas pendientes en ORQUESTADOR.md
4. Reportar al pizarron: {PIZARRON_URL}

## Modelos disponibles (de mas barato a mas caro)
| Modelo | Costo/1K tokens | Estado |
|--------|----------------|--------|
| ollama/qwen2.5-coder:32b | GRATIS | Local |
| ollama/qwen2.5-coder:7b | GRATIS | Local |
| groq/llama-3.3-70b-versatile | GRATIS | API |
| vertex_ai/gemini-2.5-flash-lite | ~$0.01/1M | Vertex AI |
| vertex_ai/gemini-2.5-flash | ~$0.075/1M | Vertex AI |
"""
    log_path.write_text(contenido, encoding="utf-8")
    print(f"  [log] Contexto guardado: {log_path.name}")

    # Tambien limpiar logs viejos (conservar solo los ultimos 20)
    todos = sorted(LOG_DIR.glob("estado_*.md"))
    if len(todos) > 20:
        for viejo in todos[:-20]:
            viejo.unlink()

# ─── MODELOS EN CASCADA ───────────────────────────────────────────────────────
# index.html tiene 175k tokens — SOLO modelos con 1M de contexto
# Groq/Cerebras tienen 128k → NO usar para index.html nunca
MODELOS_CASCADA = [
    ("vertex_ai", "vertex_ai/gemini-2.5-flash-lite"),   # Flash Lite — barato, 1M ctx
    ("vertex_ai", f"vertex_ai/{MODEL}"),                 # Flash — principal, 1M ctx
]

# ─── HELPER: correr Aider ─────────────────────────────────────────────────────
def correr_aider(mensaje: str, archivo: str, modelo_idx: int = 0) -> tuple[bool, str, str]:
    # Verificar que no toca archivos prohibidos
    for prohibido in ARCHIVOS_PROHIBIDOS:
        if prohibido in archivo:
            return False, f"BLOQUEADO: {archivo} es archivo prohibido", "ninguno"

    env = os.environ.copy()
    env["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
    env["VERTEXAI_PROJECT"] = PROJECT
    env["VERTEXAI_LOCATION"] = LOCATION
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Inyectar webbrowser.py falso — bloquea cualquier intento de abrir browser
    _overrides = str(Path(__file__).parent / "pyoverrides")
    env["PYTHONPATH"] = _overrides + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")
    env["AIDER_NO_BROWSER"] = "1"
    env["AIDER_NO_BROWSER"] = "1"

    # Cargar API keys para modelos alternativos
    try:
        keys_path = r"C:\Users\USUARIO\node-red-config\api-keys.json"
        with open(keys_path, encoding="utf-8") as f:
            keys = json.load(f)
        env["GROQ_API_KEY"]       = keys.get("groq", "")
        env["OPENROUTER_API_KEY"] = keys.get("openrouter", "")
        env["CEREBRAS_API_KEY"]   = keys.get("cerebras", "")
    except:
        pass

    modelos_validos = MODELOS_CASCADA

    # Intentar con cascada de modelos
    for i, (proveedor, modelo) in enumerate(modelos_validos):
        if i < modelo_idx:
            continue
        print(f"  Usando modelo: {modelo}")
        sesion["modelo_actual"] = modelo

        cmd = [
            sys.executable, WRAPPER,
            "--model", modelo,
            "--yes", "--no-git", "--no-auto-commits",
            "--no-show-model-warnings",
            "--message", mensaje,
            archivo
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                env=env, input="N\n"  # responde N a cualquier prompt interactivo
            )
            salida = result.stdout + result.stderr

            # Estimar costo si es modelo pago
            tokens_aprox = len(mensaje) // 4 + len(salida) // 4
            costo = tokens_aprox * COSTO_POR_MODELO.get(modelo, 0.0) / 1000
            sesion["costo_estimado_usd"] += costo

            exito = result.returncode == 0

            # Si fallo por credenciales/quota, probar siguiente
            if not exito and any(x in salida for x in ["quota", "RESOURCE_EXHAUSTED", "403", "401", "API key", "permission"]):
                print(f"  Modelo {modelo} sin cuota — escalando al siguiente...")
                continue

            return exito, salida[-2000:], modelo
        except subprocess.TimeoutExpired:
            print(f"  Timeout con {modelo} — escalando...")
            continue
        except Exception as e:
            print(f"  Error con {modelo}: {e} — escalando...")
            continue

    return False, "TODOS LOS MODELOS FALLARON — revisar credenciales", "ninguno"

# ─── HELPER: validate.js ──────────────────────────────────────────────────────
def validar_frontend() -> bool:
    try:
        result = subprocess.run(
            ["node", "validate.js"],
            cwd=FRONTEND_DIR,
            capture_output=True, text=True, timeout=30
        )
        return "Todo OK" in result.stdout
    except:
        return False

# ─── HELPER: git commit + push ───────────────────────────────────────────────
def git_commit_push(mensaje: str, archivo: str, directorio: str) -> bool:
    if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
        print("  Auto-commit desactivado. No se suben cambios sin revision humana.")
        return True
    try:
        subprocess.run(["git", "add", archivo], cwd=directorio, timeout=30)
        subprocess.run(["git", "commit", "-m", mensaje], cwd=directorio, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], cwd=directorio, timeout=60)
        return True
    except:
        return False

# ─── HELPER: commitear cambios pendientes de agentes externos ────────────────
def commitear_pendientes():
    """
    Detecta archivos modificados por Codex/Antigravity/Qwen y los commitea.
    El orquestador es el unico responsable de validate + commit + push.
    """
    if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
        print("  [pendientes] Auto-commit desactivado. No se suben cambios sin revision humana.")
        return

    for directorio, rama, es_frontend in [
        (FRONTEND_DIR, "main", True),
        (WORKER_DIR, "master", False),
    ]:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=directorio, capture_output=True, text=True, timeout=15
            )
            cambios = result.stdout.strip()
            if not cambios:
                continue

            archivos_modificados = [l[3:].strip() for l in cambios.splitlines() if l.strip()]
            print(f"  [pendientes] Archivos modificados en {directorio}: {archivos_modificados}")

            # Validar si es frontend
            if es_frontend:
                if not validar_frontend():
                    print("  [pendientes] validate.js FALLO — no se commitea")
                    reportar("pendientes-agentes", str(archivos_modificados), "Error", "validate.js fallo en cambios pendientes")
                    continue
                print("  [pendientes] validate.js OK")

            # Commit de todos los cambios pendientes
            subprocess.run(["git", "add", "-A"], cwd=directorio, timeout=30)
            msg = f"feat: mejoras agentes autonomos — {', '.join(archivos_modificados[:3])}"
            subprocess.run(["git", "commit", "-m", msg], cwd=directorio, timeout=30)
            push_rama = "main" if es_frontend else "master"
            subprocess.run(["git", "push", "origin", push_rama], cwd=directorio, timeout=60)

            reportar("commit-agentes", str(archivos_modificados), "Finalizado",
                     f"Commit automatico de cambios pendientes: {archivos_modificados}")
            print(f"  [pendientes] Commiteado y pusheado: {archivos_modificados}")

        except Exception as e:
            print(f"  [pendientes] Error: {e}")

# ─── CICLO PRINCIPAL ──────────────────────────────────────────────────────────
def ciclo():
    sesion["ciclos"] += 1
    print("\n" + "="*60)
    print(f"  CICLO {sesion['ciclos']} | Costo sesion: ${sesion['costo_estimado_usd']:.4f} USD")
    print("="*60)

    # Guardar log de contexto cada N ciclos
    if sesion["ciclos"] % LOG_CADA_N == 0:
        guardar_log_contexto()

    # Primero: commitear cualquier cambio pendiente de otros agentes
    commitear_pendientes()

    # 1. Leer contexto
    contexto_md = ORQUESTADOR_MD.read_text(encoding="utf-8") if ORQUESTADOR_MD.exists() else ""
    pizarron = leer_pizarron()
    ultimas = json.dumps(pizarron[-5:], ensure_ascii=False) if pizarron else "[]"

    # Leer ultimo log si existe (para dar contexto de sesiones anteriores)
    ultimo_log = ""
    if LOG_DIR.exists():
        logs = sorted(LOG_DIR.glob("estado_*.md"))
        if logs:
            try:
                ultimo_log = logs[-1].read_text(encoding="utf-8")[:800]
            except:
                pass

    # 2. Preguntar a Gemini que hacer
    prompt = f"""Sos el orquestador del proyecto Iporave Connect.
Lee el contexto y decide si hay una tarea visual SEGURA para ejecutar ahora.

CONTEXTO DEL PROYECTO:
{contexto_md[:3000]}

ULTIMAS 5 ENTRADAS DEL PIZARRON:
{ultimas}

ULTIMO ESTADO GUARDADO (sesion anterior):
{ultimo_log}

REGLAS ESTRICTAS:
- Solo hacer tareas de la seccion "Pendiente" del ORQUESTADOR.md
- NUNCA tocar: utils.js, login.js, verifyToken, SAFE_SELF_FIELDS, RLS
- Solo tareas visuales/CSS pequenas y seguras
- No repetir tareas que ya aparecen como "Finalizado" en el pizarron
- Si no hay tarea clara y segura, responder exactamente: SIN_TAREA
- Si hay tarea, responder en formato JSON exacto:
{{"archivo": "ruta/completa/al/archivo", "mensaje": "instruccion para aider", "nombre": "nombre-tarea-corto"}}

Cual es la proxima tarea?"""

    print("  Consultando a Gemini...")
    respuesta = llamar_gemini(prompt)
    print(f"  Gemini dice: {respuesta[:200]}")

    # Verificar parada crítica antes de ejecutar
    if verificar_parada_critica():
        return

    if "SIN_TAREA" in respuesta or "ERROR_GEMINI" in respuesta:
        print("  Gemini no encontro tarea nueva — buscando en cola ORQUESTADOR.md...")
        tarea_cola = leer_siguiente_tarea_cola()
        if tarea_cola:
            respuesta = json.dumps(tarea_cola)
            print(f"  Tarea de cola: {tarea_cola['nombre']}")
        else:
            print("  Cola vacia tambien. Revisando comandos remotos...")
            cmd_remoto = leer_comando_remoto()
            if cmd_remoto:
                respuesta = json.dumps(cmd_remoto)
            else:
                print("  Sin trabajo pendiente. Esperando proximo ciclo...")
                return

    # 3. Parsear tarea
    try:
        inicio = respuesta.find("{")
        fin = respuesta.rfind("}") + 1
        if inicio == -1 or fin == 0:
            print("  No se encontro JSON valido en respuesta")
            return
        tarea = json.loads(respuesta[inicio:fin])
        archivo = tarea["archivo"]
        mensaje = tarea["mensaje"]
        nombre  = tarea["nombre"]
    except Exception as e:
        print(f"  Error parseando respuesta: {e}")
        return

    print(f"\n  TAREA: {nombre}")
    print(f"  Archivo: {archivo}")
    print(f"  Instruccion: {mensaje[:100]}...")

    # 4. Ejecutar Aider
    reportar(nombre, archivo, "En proceso", f"Aider ejecutando: {mensaje[:100]}")
    exito, salida, modelo_usado = correr_aider(mensaje, archivo)

    hora = datetime.now().strftime("%H:%M")

    def registrar_fallo(motivo):
        sesion["tareas_fallidas"].append({"hora": hora, "nombre": nombre, "error": motivo})
        fallos_por_tarea[nombre] = fallos_por_tarea.get(nombre, 0) + 1
        if fallos_por_tarea[nombre] >= MAX_FALLOS:
            marcar_tarea_bloqueada(nombre)
            reportar(nombre, archivo, "Bloqueada",
                     f"Saltada tras {MAX_FALLOS} fallos: {motivo[:100]}")
            del fallos_por_tarea[nombre]
            print(f"  TAREA BLOQUEADA — saltando a la siguiente")

    if not exito:
        print(f"  Aider fallo: {salida[:200]}")
        reportar(nombre, archivo, "Error", f"Aider fallo: {salida[:200]}")
        registrar_fallo(salida[:200])
        return

    print(f"  Aider completo con {modelo_usado}. Validando...")

    # 5. Validar si es frontend
    if "index.html" in archivo or "iporave-sistema" in archivo:
        if not validar_frontend():
            print("  validate.js FALLO — no se commitea")
            reportar(nombre, archivo, "Error", "validate.js fallo — cambios revertidos")
            registrar_fallo("validate.js fallo")
            return
        print("  validate.js OK")
        directorio = FRONTEND_DIR
    else:
        directorio = WORKER_DIR

    # 6. Commit
    git_commit_push(f"feat: {nombre} — orquestador autonomo [{modelo_usado}]", archivo, directorio)

    costo_tarea = sesion["costo_estimado_usd"]
    resumen = f"Completado con {modelo_usado}. Costo sesion: ${costo_tarea:.4f} USD. {salida[-200:]}"
    reportar(nombre, archivo, "Finalizado", resumen)

    sesion["tareas_completadas"].append({
        "hora": hora, "nombre": nombre, "archivo": archivo,
        "modelo": modelo_usado,
        "costo_usd": COSTO_POR_MODELO.get(modelo_usado, 0.0)
    })
    # Marcar tarea como completada en la cola
    marcar_tarea_completada(nombre)
    print(f"  COMPLETADO: {nombre} | modelo: {modelo_usado} | costo sesion: ${costo_tarea:.4f}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("ORQUESTADOR IPORAVE — Iniciando")
    print(f"   Modelo principal: {MODEL}")
    print(f"   Cascada: Gemini Flash > Flash Lite > Qwen32B local > Qwen7B local > Groq")
    print(f"   Intervalo: {INTERVALO_SEG}s | Log cada: {LOG_CADA_N} ciclos (~{LOG_CADA_N*INTERVALO_SEG//60} min)")
    print(f"   Pizarron: {PIZARRON_URL}")
    print(f"   Logs: {LOG_DIR}")
    print("\nPresiona Ctrl+C para detener\n")

    LOG_DIR.mkdir(exist_ok=True)

    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Ciclo {sesion['ciclos']+1}")
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\n\nOrquestador detenido por el usuario")
            guardar_log_contexto()
            print(f"Costo total estimado sesion: ${sesion['costo_estimado_usd']:.4f} USD")
            break
        except Exception as e:
            print(f"  Error en ciclo: {e}")
            reportar("ciclo-error", "-", "Error", str(e)[:200])

        print(f"\n  Proximo ciclo en {INTERVALO_SEG}s... (Ctrl+C para detener)")
        time.sleep(INTERVALO_SEG)
