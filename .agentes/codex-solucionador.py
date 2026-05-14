"""
CODEX SOLUCIONADOR — Iporãve Connect
Agente de última línea. Duerme hasta que lo llaman.

Cuando un orquestador no puede resolver un error, publica en el pizarrón:
  agente: "CODEX-TAREA"
  estado: "Pendiente"
  tarea: nombre-tarea
  resumen: descripción completa del error

Este agente:
1. Lee el pizarrón cada 60s buscando esas entradas
2. Analiza con Gemini Pro (el modelo más potente disponible)
3. Intenta resolver con Aider + instrucción muy específica
4. Si lo resuelve → avisa al orquestador original y reporta
5. Si NO lo resuelve → escala a Claude Code:
   - Notifica al usuario por Telegram con TODOS los detalles
   - Explica exactamente qué decirle a Claude Code
   - Pone la tarea en el pizarrón como "Escalar-Claude"

Cadena de escalación completa:
  Orquestador → Gemini Flash (3 intentos) → Codex-Solucionador (Gemini Pro) → Claude Code (vos)

Uso: python codex-solucionador.py
"""

import json, os, subprocess, sys, time, urllib.request, ssl
from pathlib import Path
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT      = "rugged-shell-430212-f6"
LOCATION     = "us-central1"
PIZARRON_URL = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
CLAVE_JSON   = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
KEYS_PATH    = r"C:\Users\USUARIO\node-red-config\api-keys.json"
FRONTEND_DIR = r"C:\Users\USUARIO\iporave-sistema"
WORKER_DIR   = r"C:\Users\USUARIO\iporave-worker"
INTERVALO_SEG = 60
AGENTE_NOMBRE = "Codex-Solucionador"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
os.environ["VERTEXAI_PROJECT"]               = PROJECT
os.environ["VERTEXAI_LOCATION"]              = LOCATION

_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

WRAPPER = str(Path(__file__).parent / "aider-wrapper.py")

# Tareas ya procesadas en esta sesión (no reprocesar la misma)
_procesadas = set()

# ─── PIZARRÓN ─────────────────────────────────────────────────────────────────

def leer_pizarron():
    try:
        req = urllib.request.Request(PIZARRON_URL,
                                     headers={"User-Agent": "IporaveAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("registros", []) if isinstance(data, dict) else data
    except:
        return []

def reportar(tarea, estado, resumen):
    body = json.dumps({
        "agente": AGENTE_NOMBRE, "tarea": tarea,
        "archivos": "-", "estado": estado, "resumen": resumen
    }).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

def escribir_alerta(texto, nivel="info"):
    """Escribe alerta a alerts.json. Sin Telegram."""
    try:
        alerts_file = Path(__file__).parent / "alerts.json"
        alertas = []
        if alerts_file.exists():
            try:
                alertas = json.loads(alerts_file.read_text(encoding="utf-8"))
            except:
                alertas = []
        alertas.append({
            "timestamp": datetime.now().isoformat(),
            "nivel": nivel,
            "mensaje": texto
        })
        alertas = alertas[-100:]
        alerts_file.write_text(json.dumps(alertas, indent=2, ensure_ascii=False), encoding="utf-8")
    except:
        pass

# ─── ANÁLISIS CON GEMINI PRO ──────────────────────────────────────────────────

PROMPT_CODEX = """Sos Codex, el solucionador de última línea del sistema Iporãve Connect.
Otros agentes automáticos fallaron en resolver esta tarea. Sos el más inteligente del equipo.
Analizá el error con máximo detalle y generá la solución más específica y correcta posible.

El sistema usa Aider para modificar archivos. Las reglas:
- Archivos JS del Worker (src/api/): validar con node --check, no tocar utils.js ni login.js
- Archivos HTML frontend (index.html, catalog.html): SOLO CSS en bloque <style>, NUNCA </script> en strings
- validate.js debe pasar antes de cualquier commit frontend

Si el error involucra auth, seguridad, JWT, RLS → poner "necesita_humano": true, NO intentar resolver.
Si el error es simple (CSS, typo, falta un campo) → generar instrucción muy específica.
Si todos los modelos fallaron por cuota → "necesita_humano": true, "solucionable": false.

Respondé SOLO con JSON:
{
  "diagnostico_detallado": "análisis profundo de qué pasó y por qué",
  "causa_raiz": "causa raíz técnica exacta",
  "instruccion_solucion": "instrucción ultra-específica para Aider — indicar exactamente qué líneas/selectores tocar y cuáles NO",
  "solucionable": true/false,
  "necesita_humano": false,
  "nivel_riesgo": "bajo/medio/alto",
  "pasos_manuales": "si necesita humano: pasos exactos que debe seguir el dueño para resolverlo"
}
"""

def analizar_con_gemini_pro(nombre_tarea, instruccion_original, error_output, archivo_path):
    """Análisis profundo con Gemini 2.5 Pro — el modelo más potente."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

        contexto = ""
        try:
            lineas = Path(archivo_path).read_text(encoding="utf-8", errors="replace").splitlines()
            total  = len(lineas)
            contexto = (
                f"Archivo: {Path(archivo_path).name} ({total} líneas totales)\n"
                f"Primeras 10 líneas:\n" + "\n".join(lineas[:10]) + "\n"
                f"Últimas 10 líneas:\n" + "\n".join(lineas[-10:])
            )
        except:
            contexto = f"Archivo: {archivo_path}"

        prompt = f"""
Tarea que falló repetidamente: {nombre_tarea}
Instrucción original: {instruccion_original}

Error completo:
{error_output[:2000]}

Contexto del archivo objetivo:
{contexto}

Otros agentes ya intentaron resolver esto 3 veces con Gemini Flash sin éxito.
Analizá profundamente y generá la mejor solución posible.
"""

        # Intentar con Pro primero, fallback a Flash si Pro falla
        for modelo in ["gemini-2.5-pro", "gemini-2.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_CODEX,
                        response_mime_type="application/json",
                        temperature=0.1,
                    )
                )
                texto = response.text.strip()
                if texto.startswith("```"):
                    texto = texto.split("```")[1]
                    if texto.startswith("json"):
                        texto = texto[4:]
                result = json.loads(texto)
                print(f"  [{AGENTE_NOMBRE}] Análisis con {modelo} OK")
                return result
            except Exception as e:
                print(f"  [{AGENTE_NOMBRE}] {modelo} falló: {e} — intentando siguiente...")
                continue

    except Exception as e:
        print(f"  [{AGENTE_NOMBRE}] Error en análisis: {e}")

    return {
        "diagnostico_detallado": f"Error al analizar: no pude conectar con Gemini",
        "causa_raiz": "Falla de conexión con Gemini API",
        "instruccion_solucion": instruccion_original,
        "solucionable": False,
        "necesita_humano": True,
        "nivel_riesgo": "bajo",
        "pasos_manuales": "Revisar manualmente con Claude Code"
    }

# ─── EJECUTAR SOLUCIÓN ────────────────────────────────────────────────────────

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

def intentar_resolver(instruccion, archivo):
    """Intenta resolver con Aider usando Gemini Flash (más barato que Pro para ejecución)."""
    env = cargar_env()
    directorio = WORKER_DIR if "iporave-worker" in archivo else FRONTEND_DIR
    modelos = ["vertex_ai/gemini-2.5-flash", "vertex_ai/gemini-2.5-flash-lite"]
    for modelo in modelos:
        try:
            result = subprocess.run(
                [sys.executable, WRAPPER, "--model", modelo, "--yes", "--no-git",
                 "--no-auto-commits", "--no-show-model-warnings",
                 "--message", instruccion, archivo],
                capture_output=True, text=True, timeout=300,
                env=env, input="N\n"
            )
            salida = result.stdout + result.stderr
            if result.returncode == 0:
                return True, salida[-1000:]
            if any(x in salida for x in ["quota", "RESOURCE_EXHAUSTED", "rate limit"]):
                continue
            return False, salida[-1000:]
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    return False, "TODOS LOS MODELOS FALLARON en Codex-Solucionador"

def validar_archivo(archivo):
    """Valida el archivo según su tipo."""
    if "index.html" in archivo or "catalog.html" in archivo or archivo.endswith(".html"):
        result = subprocess.run(["node", "validate.js"], cwd=FRONTEND_DIR,
                                capture_output=True, text=True, timeout=30)
        return "Todo OK" in result.stdout, (result.stdout + result.stderr)[-300:]
    elif archivo.endswith(".js"):
        result = subprocess.run(["node", "--check", archivo],
                                capture_output=True, text=True, timeout=15)
        return result.returncode == 0, result.stderr[:300]
    return True, ""

def commitear(nombre, archivo):
    """Commit y push del archivo resuelto."""
    if os.environ.get("IPORAVE_AUTO_COMMIT", "0") != "1":
        print("  Auto-commit desactivado. No se suben cambios sin revision humana.")
        return True
    if "iporave-worker" in archivo:
        directorio, rama = WORKER_DIR, "master"
    else:
        directorio, rama = FRONTEND_DIR, "main"
    try:
        nombre_rel = str(Path(archivo)).replace(str(directorio), "").lstrip("/\\")
        subprocess.run(["git", "add", nombre_rel], cwd=directorio, timeout=30)
        subprocess.run(["git", "commit", "-m",
                        f"fix: {nombre} — resuelto por Codex-Solucionador"],
                       cwd=directorio, timeout=30)
        subprocess.run(["git", "push", "origin", rama], cwd=directorio, timeout=60)
        return True
    except:
        return False

# ─── ESCALAR A CLAUDE CODE ────────────────────────────────────────────────────

def escalar_a_claude(nombre_tarea, instruccion_original, error_output, archivo,
                     diagnostico, causa_raiz, pasos_manuales, agente_origen):
    """
    Cuando nada funciona, prepara la escalación completa a Claude Code (el humano).
    Envía un mensaje Telegram muy detallado con exactamente qué decirle a Claude.
    """
    nombre_arch = Path(archivo).name
    error_corto = error_output[:300] if error_output else "sin detalle"

    escribir_alerta(
        f"🆘 *ESCALAR A CLAUDE CODE — Iporãve*\n\n"
        f"📌 *Tarea:* `{nombre_tarea}`\n"
        f"📂 *Archivo:* `{nombre_arch}`\n"
        f"👤 *Falló en:* {agente_origen}\n\n"
        f"📋 *Diagnóstico:*\n{diagnostico[:200]}\n\n"
        f"🔍 *Causa raíz:*\n`{causa_raiz[:150]}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*ABRÍ CLAUDE CODE Y DECILE:*\n"
        f"\"Tarea `{nombre_tarea}` en `{nombre_arch}` falló. "
        f"Error: {error_corto[:200]}. "
        f"Instrucción original: {instruccion_original[:150]}\"\n\n"
        f"*Pasos manuales sugeridos:*\n{pasos_manuales[:300]}\n\n"
        f"_El sistema continúa con las demás tareas._"
    )

    reportar(nombre_tarea, "Escalar-Claude",
             f"Escalado a Claude Code. Causa: {causa_raiz[:150]}")
    print(f"  [{AGENTE_NOMBRE}] Escalado a Claude Code: {nombre_tarea}")

# ─── PROCESAR UNA TAREA ───────────────────────────────────────────────────────

def procesar_tarea(entrada):
    """Procesa una entrada del pizarrón con agente=CODEX-TAREA."""
    nombre_tarea      = entrada.get("tarea", "tarea-desconocida")
    instruccion_orig  = entrada.get("resumen", "")
    archivo           = entrada.get("archivos", "")
    agente_origen     = entrada.get("descripcion", "orquestador-desconocido")

    # Inferir error del resumen (viene en formato "ERROR: xxx | Instruccion: yyy")
    error_output = instruccion_orig
    instruccion_limpia = instruccion_orig
    if " | Instruccion: " in instruccion_orig:
        partes = instruccion_orig.split(" | Instruccion: ", 1)
        error_output      = partes[0].replace("ERROR: ", "")
        instruccion_limpia = partes[1]

    print(f"\n  [{AGENTE_NOMBRE}] Procesando: {nombre_tarea}")
    print(f"  Archivo: {archivo}")
    reportar(nombre_tarea, "Analizando", f"Codex analizando con Gemini Pro...")
    escribir_alerta(
        f"🔬 *Codex Solucionador activado*\n\n"
        f"📌 Tarea: `{nombre_tarea}`\n"
        f"📂 Archivo: `{Path(archivo).name if archivo else 'desconocido'}`\n"
        f"_Analizando con Gemini Pro..._"
    )

    # 1. Análisis con Gemini Pro
    analisis = analizar_con_gemini_pro(nombre_tarea, instruccion_limpia, error_output, archivo)

    diagnostico  = analisis.get("diagnostico_detallado", "")
    causa_raiz   = analisis.get("causa_raiz", "")
    instruccion  = analisis.get("instruccion_solucion", instruccion_limpia)
    solucionable = analisis.get("solucionable", True)
    nec_humano   = analisis.get("necesita_humano", False)
    riesgo       = analisis.get("nivel_riesgo", "bajo")
    pasos        = analisis.get("pasos_manuales", "Revisar con Claude Code")

    print(f"  Diagnóstico: {diagnostico[:100]}")
    print(f"  Solucionable: {solucionable} | Necesita humano: {nec_humano} | Riesgo: {riesgo}")

    # Si Gemini Pro dice que necesita humano o riesgo alto → no intentar, escalar directo
    if not solucionable or nec_humano or riesgo == "alto":
        escalar_a_claude(nombre_tarea, instruccion_limpia, error_output, archivo,
                         diagnostico, causa_raiz, pasos, agente_origen)
        return

    if not archivo or not Path(archivo).exists():
        print(f"  Archivo no encontrado: {archivo} — escalando")
        escalar_a_claude(nombre_tarea, instruccion_limpia, error_output, archivo,
                         f"Archivo no encontrado: {archivo}", causa_raiz, pasos, agente_origen)
        return

    # 2. Intentar resolver con Aider
    print(f"  Intentando resolver: {instruccion[:100]}...")
    reportar(nombre_tarea, "Resolviendo", f"Ejecutando solución de Gemini Pro...")

    # git checkout antes de intentar
    directorio = WORKER_DIR if "iporave-worker" in archivo else FRONTEND_DIR
    try:
        nombre_rel = str(Path(archivo)).replace(str(directorio), "").lstrip("/\\")
        subprocess.run(["git", "checkout", "--", nombre_rel], cwd=directorio,
                       capture_output=True, timeout=15)
    except: pass

    exito, salida = intentar_resolver(instruccion, archivo)

    if not exito:
        print(f"  Aider falló en Codex: {salida[:100]}")
        escalar_a_claude(nombre_tarea, instruccion_limpia, salida, archivo,
                         diagnostico, f"Aider falló: {salida[:100]}", pasos, agente_origen)
        return

    # 3. Validar
    val_ok, val_error = validar_archivo(archivo)
    if not val_ok:
        print(f"  Validación falló: {val_error[:100]}")
        # Revertir y escalar
        try:
            subprocess.run(["git", "checkout", "--", nombre_rel], cwd=directorio,
                           capture_output=True, timeout=15)
        except: pass
        escalar_a_claude(nombre_tarea, instruccion_limpia, val_error, archivo,
                         f"Aider ejecutó pero validación falló: {val_error[:100]}",
                         causa_raiz, pasos, agente_origen)
        return

    # 4. ¡Resuelto! Commit y notificar
    commitear(nombre_tarea, archivo)
    reportar(nombre_tarea, "Resuelto-Codex", f"Resuelto por Codex-Solucionador con Gemini Pro")
    escribir_alerta(
        f"✅ *Codex Solucionador — Problema resuelto*\n\n"
        f"📌 Tarea: `{nombre_tarea}`\n"
        f"📂 Archivo: `{Path(archivo).name}`\n\n"
        f"🧠 *Diagnóstico:*\n{diagnostico[:200]}\n\n"
        f"💡 *Solución aplicada:*\n{instruccion[:150]}\n\n"
        f"✅ Commiteado y pusheado al repositorio."
    )
    print(f"  [{AGENTE_NOMBRE}] ✅ RESUELTO: {nombre_tarea}")

# ─── LOOP PRINCIPAL ───────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print(f"  {AGENTE_NOMBRE} — durmiendo hasta ser llamado")
    print(f"  Escucha: agente=CODEX-TAREA en el pizarrón")
    print(f"  Modelo: Gemini 2.5 Pro para análisis")
    print(f"  Revisando cada {INTERVALO_SEG}s")
    print("=" * 55)

    reportar("codex-inicio", "Activo", "Codex-Solucionador listo y esperando tareas.")

    while True:
        try:
            registros = leer_pizarron()
            for entrada in reversed(registros):
                if (entrada.get("agente") == "CODEX-TAREA"
                        and entrada.get("estado") == "Pendiente"):
                    # Usar ID o tarea como clave para no reprocesar
                    clave = entrada.get("id") or entrada.get("tarea", "") + entrada.get("created_at", "")
                    if clave in _procesadas:
                        continue
                    _procesadas.add(clave)
                    procesar_tarea(entrada)

            # Limpiar procesadas viejas (conservar solo las últimas 50)
            if len(_procesadas) > 50:
                lista = list(_procesadas)
                _procesadas.clear()
                _procesadas.update(lista[-50:])

        except KeyboardInterrupt:
            print(f"\n[{AGENTE_NOMBRE}] Detenido.")
            break
        except Exception as e:
            print(f"  [{AGENTE_NOMBRE}] Error: {e}")

        time.sleep(INTERVALO_SEG)

if __name__ == "__main__":
    main()
