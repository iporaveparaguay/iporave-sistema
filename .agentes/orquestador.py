"""
ORQUESTADOR AUTÓNOMO — Iporãve Connect
Usa Gemini 2.5 Flash para decidir tareas y Aider para ejecutarlas.

Uso: python orquestador.py
Detener: Ctrl+C
"""

import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT        = "rugged-shell-430212-f6"
LOCATION       = "us-central1"
MODEL          = "gemini-2.5-flash"
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
CLAVE_JSON     = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"
WORKER_DIR     = r"C:\Users\USUARIO\iporave-worker"
INTERVALO_SEG  = 120  # revisar cada 2 minutos

# ─── ARCHIVOS PROHIBIDOS (nunca tocar) ────────────────────────────────────────
ARCHIVOS_PROHIBIDOS = [
    "utils.js", "login.js", "verifyToken", "SAFE_SELF_FIELDS"
]

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
        return response.text.strip()
    except Exception as e:
        return f"ERROR_GEMINI: {e}"

# ─── HELPER: leer pizarrón ────────────────────────────────────────────────────
def leer_pizarron() -> list:
    try:
        req = urllib.request.Request(PIZARRON_URL)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [pizarrón] Error al leer: {e}")
        return []

# ─── HELPER: reportar al pizarrón ─────────────────────────────────────────────
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
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"  [pizarrón] Reportado: {tarea} — {estado}")
    except Exception as e:
        print(f"  [pizarrón] Error al reportar: {e}")

# ─── HELPER: correr Aider ─────────────────────────────────────────────────────
def correr_aider(mensaje: str, archivo: str) -> tuple[bool, str]:
    # Verificar que no toca archivos prohibidos
    for prohibido in ARCHIVOS_PROHIBIDOS:
        if prohibido in archivo:
            return False, f"BLOQUEADO: {archivo} es archivo prohibido"

    env = os.environ.copy()
    env["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
    env["VERTEXAI_PROJECT"] = PROJECT
    env["VERTEXAI_LOCATION"] = LOCATION

    cmd = [
        "aider",
        "--model", f"vertex_ai/{MODEL}",
        "--yes", "--no-git", "--no-auto-commits",
        "--no-show-model-warnings",
        "--message", mensaje,
        archivo
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, env=env
        )
        salida = result.stdout + result.stderr
        exito = result.returncode == 0
        return exito, salida[-2000:]  # últimos 2000 chars
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: Aider tardó más de 5 minutos"
    except Exception as e:
        return False, f"ERROR: {e}"

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
    try:
        subprocess.run(["git", "add", archivo], cwd=directorio, timeout=30)
        subprocess.run(["git", "commit", "-m", mensaje], cwd=directorio, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], cwd=directorio, timeout=60)
        return True
    except:
        return False

# ─── CICLO PRINCIPAL ──────────────────────────────────────────────────────────
def ciclo():
    print("\n" + "="*60)
    print("  CICLO DE ORQUESTACIÓN")
    print("="*60)

    # 1. Leer contexto
    contexto_md = ORQUESTADOR_MD.read_text(encoding="utf-8") if ORQUESTADOR_MD.exists() else ""
    pizarron = leer_pizarron()
    ultimas = json.dumps(pizarron[-5:], ensure_ascii=False) if pizarron else "[]"

    # 2. Preguntar a Gemini qué hacer
    prompt = f"""Sos el orquestador del proyecto Iporãve Connect.
Leé el contexto y decidí si hay una tarea visual SEGURA para ejecutar ahora.

CONTEXTO DEL PROYECTO:
{contexto_md[:3000]}

ÚLTIMAS 5 ENTRADAS DEL PIZARRÓN:
{ultimas}

REGLAS ESTRICTAS:
- Solo hacer tareas de la sección "Pendiente" del ORQUESTADOR.md
- NUNCA tocar: utils.js, login.js, verifyToken, SAFE_SELF_FIELDS, RLS
- Solo tareas visuales/CSS pequeñas y seguras
- Si no hay tarea clara y segura, responder exactamente: SIN_TAREA
- Si hay tarea, responder en formato JSON exacto:
{{"archivo": "ruta/completa/al/archivo", "mensaje": "instruccion para aider", "nombre": "nombre-tarea-corto"}}

¿Cuál es la próxima tarea?"""

    print("  Consultando a Gemini...")
    respuesta = llamar_gemini(prompt)
    print(f"  Gemini dice: {respuesta[:200]}")

    if "SIN_TAREA" in respuesta or "ERROR_GEMINI" in respuesta:
        print("  Sin tarea nueva. Descansando...")
        return

    # 3. Parsear tarea
    try:
        # Buscar JSON en la respuesta
        inicio = respuesta.find("{")
        fin = respuesta.rfind("}") + 1
        if inicio == -1 or fin == 0:
            print("  No se encontró JSON válido en respuesta")
            return
        tarea = json.loads(respuesta[inicio:fin])
        archivo = tarea["archivo"]
        mensaje = tarea["mensaje"]
        nombre = tarea["nombre"]
    except Exception as e:
        print(f"  Error parseando respuesta: {e}")
        return

    print(f"\n  TAREA: {nombre}")
    print(f"  Archivo: {archivo}")
    print(f"  Instrucción: {mensaje[:100]}...")

    # 4. Ejecutar Aider
    reportar(nombre, archivo, "En proceso", f"Aider ejecutando tarea: {mensaje[:100]}")
    exito, salida = correr_aider(mensaje, archivo)

    if not exito:
        print(f"  Aider falló: {salida[:200]}")
        reportar(nombre, archivo, "Error", f"Aider falló: {salida[:200]}")
        return

    print(f"  Aider completó. Validando...")

    # 5. Validar si es frontend
    if "index.html" in archivo or "iporave-sistema" in archivo:
        if not validar_frontend():
            print("  validate.js FALLÓ — no se commitea")
            reportar(nombre, archivo, "Error", "validate.js falló — cambios revertidos")
            return
        print("  validate.js OK")
        directorio = FRONTEND_DIR
        rama = "main"
    else:
        directorio = WORKER_DIR
        rama = "master"

    # 6. Commit
    git_commit_push(f"feat: {nombre} — orquestador autónomo", archivo, directorio)
    reportar(nombre, archivo, "Finalizado", f"Completado por orquestador. {salida[-300:]}")
    print(f"  ✅ Tarea {nombre} completada y commiteada")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 ORQUESTADOR IPORÃVE — Iniciando")
    print(f"   Modelo: {MODEL}")
    print(f"   Proyecto: {PROJECT}")
    print(f"   Intervalo: {INTERVALO_SEG}s")
    print(f"   Pizarrón: {PIZARRON_URL}")
    print("\nPresioná Ctrl+C para detener\n")

    ciclo_num = 0
    while True:
        ciclo_num += 1
        print(f"\n[Ciclo {ciclo_num}] {time.strftime('%H:%M:%S')}")
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\n\n🛑 Orquestador detenido por el usuario")
            break
        except Exception as e:
            print(f"  Error en ciclo: {e}")
            reportar("ciclo-error", "-", "Error", str(e)[:200])

        print(f"\n  Próximo ciclo en {INTERVALO_SEG}s... (Ctrl+C para detener)")
        time.sleep(INTERVALO_SEG)
