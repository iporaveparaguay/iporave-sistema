"""
GEMINI RESOLVER — Iporãve Connect
Módulo inteligente compartido por todos los orquestadores.

Cuando una tarea falla, este módulo:
1. Analiza el error con Gemini 2.5 Flash
2. Diagnostica en español simple qué salió mal
3. Genera una instrucción mejorada para Aider
4. Si el error es muy complejo → escala a Gemini 2.5 Pro
5. Si nada funciona → notifica al dueño y escala a Claude Code (humano)
6. Si es error crítico (todos los modelos muertos) → PARA TODO el sistema

Uso:
    from gemini_resolver import analizar_error, notificar_telegram
    from gemini_resolver import parar_sistema_critico, notificar_escalar_a_claude
"""

import json, os, sys, urllib.request, ssl
from pathlib import Path

# Contexto SSL local (NO global) — usa CAs por defecto pero permite override per-request si hace falta.
# El monkey-patch _create_unverified_context original era inseguro (MITM en TODO el proceso Python).
_SSL_CTX = ssl.create_default_context()

CLAVE_JSON = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
PROJECT    = "rugged-shell-430212-f6"
LOCATION   = "us-central1"
KEYS_PATH  = r"C:\Users\USUARIO\node-red-config\api-keys.json"
PIZARRON_URL = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
os.environ["VERTEXAI_PROJECT"]               = PROJECT
os.environ["VERTEXAI_LOCATION"]              = LOCATION

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────

def notificar_telegram(texto):
    """Envía mensaje directo al dueño en Telegram."""
    try:
        cfg_file = Path(__file__).parent / "telegram-config.json"
        if not cfg_file.exists():
            return
        cfg     = json.loads(cfg_file.read_text(encoding="utf-8"))
        chat_id = cfg.get("admin_chat_id")
        if not chat_id:
            return
        with open(KEYS_PATH, encoding="utf-8") as f:
            token = json.load(f).get("telegram_token", "")
        if not token:
            return
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({
            "chat_id":    chat_id,
            "text":       texto,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [Resolver] Error Telegram: {e}")

def reportar_pizarron(agente, tarea, estado, resumen):
    """Publica en el pizarrón."""
    try:
        body = json.dumps({
            "agente": agente, "tarea": tarea,
            "archivos": "-", "estado": estado, "resumen": resumen
        }).encode()
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

# ─── PARADA CRÍTICA TOTAL ─────────────────────────────────────────────────────

def parar_sistema_critico(agente, motivo):
    """
    Cuando todos los modelos fallan o hay un error crítico:
    1. Escribe archivo PARADA_CRITICA.txt para que el supervisor sepa
    2. Notifica por Telegram con instrucciones detalladas
    3. Reporta al pizarrón como ALERTA-CRITICA
    """
    archivo_parada = Path(__file__).parent / "PARADA_CRITICA.txt"
    archivo_parada.write_text(
        f"PARADA CRITICA\nAgente: {agente}\nMotivo: {motivo}\n",
        encoding="utf-8"
    )
    reportar_pizarron(agente, "parada-critica", "ALERTA-CRITICA",
                      f"PARADA TOTAL: {motivo[:200]}")
    notificar_telegram(
        f"🚨 *PARADA CRÍTICA — Iporãve*\n\n"
        f"*Agente:* `{agente}`\n"
        f"*Motivo:* {motivo[:300]}\n\n"
        f"*Qué hacer:*\n"
        f"1️⃣ Abrí Claude Code en tu PC\n"
        f"2️⃣ Decile qué agente falló y el motivo de arriba\n"
        f"3️⃣ Cuando Claude Code lo resuelva, borrá el archivo `.agentes/PARADA_CRITICA.txt`\n"
        f"4️⃣ Volvé a correr `iniciar-todos.ps1`\n\n"
        f"_El sistema está detenido hasta que vos lo reinicies._"
    )
    print(f"\n{'='*60}")
    print(f"  ⚠️  PARADA CRÍTICA: {motivo[:100]}")
    print(f"  Se creó PARADA_CRITICA.txt")
    print(f"  Notificación enviada a Telegram")
    print(f"{'='*60}\n")

def hay_parada_critica():
    """Retorna True si existe el archivo de parada crítica."""
    return (Path(__file__).parent / "PARADA_CRITICA.txt").exists()

def limpiar_parada_critica():
    """Borra el archivo de parada crítica (solo para uso manual)."""
    f = Path(__file__).parent / "PARADA_CRITICA.txt"
    if f.exists():
        f.unlink()

# ─── ESCALACIÓN A CLAUDE ──────────────────────────────────────────────────────

def notificar_escalar_a_claude(nombre_tarea, instruccion_original, error_output,
                                archivo_path, diagnostico, causa_tecnica, agente):
    """
    Cuando ningún agente automático puede resolver el error,
    notifica al dueño para que lo resuelva con Claude Code.
    """
    resumen_error = error_output[:400] if error_output else "sin detalle"
    notificar_telegram(
        f"🆘 *Escalar a Claude Code — {agente}*\n\n"
        f"📌 *Tarea:* `{nombre_tarea}`\n"
        f"📋 *Qué pasó:* {diagnostico}\n"
        f"🔍 *Causa técnica:* `{causa_tecnica[:100]}`\n\n"
        f"📂 *Archivo:* `{Path(archivo_path).name}`\n\n"
        f"*Qué hacer:*\n"
        f"1️⃣ Abrí Claude Code\n"
        f"2️⃣ Decile exactamente esto:\n"
        f"_\"Tarea `{nombre_tarea}` en `{Path(archivo_path).name}` falló. "
        f"Error: {resumen_error[:150]}. Instrucción original: {instruccion_original[:150]}\"_\n\n"
        f"_El agente continúa con otras tareas mientras tanto._"
    )
    reportar_pizarron(agente, nombre_tarea, "Escalar-Claude",
                      f"Requiere Claude Code: {causa_tecnica[:150]}")

# ─── GEMINI ANALYZER ──────────────────────────────────────────────────────────

PROMPT_SISTEMA = """Sos el analizador de errores del sistema Iporãve Connect.
Tu trabajo es diagnosticar por qué falló una tarea y generar una solución.

El sistema usa Aider (herramienta de IA) para modificar archivos de código.
Después de cada modificación, se corre validate.js para verificar que el HTML sea válido.

ERRORES COMUNES:
- validate.js falla con </script>: Aider introdujo </script> sin escapar dentro de un string JS → solución: pedir a Aider que SOLO toque el bloque CSS <style>, y que NUNCA escriba la cadena </script> en ningún contexto
- validate.js falla estructura HTML: Aider rompió etiquetas HTML → instrucción más acotada, solo el selector CSS específico
- Todos los modelos fallaron: problema de cuota o conexión → no solucionable ahora, escalar
- Timeout: el archivo es muy grande → dividir la tarea en partes más pequeñas y específicas
- Error de git: conflicto o archivo sucio → hacer git checkout primero
- Rate limit Groq: demasiadas llamadas → esperar o escalar a Gemini

Respondé SOLO con JSON válido, sin explicaciones extra:
{
  "diagnostico": "explicación en español simple y claro de qué salió mal (para alguien no técnico)",
  "causa_tecnica": "causa técnica precisa en 1 línea",
  "nueva_instruccion": "instrucción mejorada y más específica para Aider (en español, muy clara, explicando exactamente qué selector CSS tocar y que no toque JavaScript)",
  "solucionable": true/false,
  "necesita_claude": false,
  "confianza": "alta/media/baja",
  "accion_sugerida": "qué debería hacer el dueño del sistema si esto no se puede resolver automáticamente"
}

Si el error requiere modificar lógica compleja de JavaScript, auth, o seguridad → poner "necesita_claude": true
"""

def analizar_error(nombre_tarea, instruccion_original, error_output, archivo_path,
                   intento_num=1, usar_pro=False):
    """
    Analiza un error con Gemini y devuelve diagnóstico + nueva instrucción.

    Args:
        nombre_tarea: nombre de la tarea que falló
        instruccion_original: la instrucción que se le dio a Aider
        error_output: el output del error (validate.js o Aider)
        archivo_path: ruta del archivo que se estaba modificando
        intento_num: número de intento (1, 2 o 3)
        usar_pro: si True, usa Gemini 2.5 Pro para análisis más profundo

    Returns:
        dict con: diagnostico, causa_tecnica, nueva_instruccion, solucionable,
                  necesita_claude, confianza, accion_sugerida
    """
    modelo = "gemini-2.5-pro" if usar_pro else "gemini-2.5-flash"
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

        # Leer primeras y últimas líneas del archivo para contexto
        contexto_archivo = ""
        try:
            lineas = Path(archivo_path).read_text(encoding="utf-8",
                          errors="replace").splitlines()
            total = len(lineas)
            contexto_archivo = (
                f"Archivo: {Path(archivo_path).name} ({total} líneas)\n"
                f"Primeras 5 líneas:\n" + "\n".join(lineas[:5]) + "\n"
                f"...({total - 10} líneas en el medio)...\n"
                f"Últimas 5 líneas:\n" + "\n".join(lineas[-5:])
            )
        except:
            contexto_archivo = f"Archivo: {archivo_path}"

        prompt = f"""
Tarea fallida: {nombre_tarea}
Intento número: {intento_num}/3
Instrucción original dada a Aider: {instruccion_original}

Error obtenido:
{error_output[:1500]}

Contexto del archivo:
{contexto_archivo}

Analizá el error y generá una solución.
En el intento {intento_num}/3, hacé la instrucción más específica y acotada que el intento anterior.
Si el error involucra </script> en un string, la nueva instrucción debe decir explícitamente:
"SOLO modificar el bloque <style> CSS. NO tocar ningún bloque <script>. NO escribir la cadena </script> en ningún contexto."
"""

        response = client.models.generate_content(
            model=modelo,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SISTEMA,
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        texto = response.text.strip()
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]

        result = json.loads(texto)
        # Asegurar campo necesita_claude
        if "necesita_claude" not in result:
            result["necesita_claude"] = False
        return result

    except Exception as e:
        print(f"  [Resolver] Error llamando Gemini ({modelo}): {e}")
        # Si falló con Pro, intentar con Flash
        if usar_pro:
            print(f"  [Resolver] Reintentando con Flash...")
            return analizar_error(nombre_tarea, instruccion_original, error_output,
                                  archivo_path, intento_num, usar_pro=False)
        return {
            "diagnostico": f"No pude analizar el error automáticamente: {str(e)[:100]}",
            "causa_tecnica": str(e)[:150],
            "nueva_instruccion": instruccion_original,
            "solucionable": False,
            "necesita_claude": True,
            "confianza": "baja",
            "accion_sugerida": "Revisar manualmente el error y la tarea."
        }

# ─── MENSAJES TELEGRAM FORMATEADOS ────────────────────────────────────────────

def avisar_fallo_inicial(nombre_tarea, diagnostico, intento, max_intentos, agente):
    """Avisa que una tarea falló y que está buscando solución."""
    notificar_telegram(
        f"⚠️ *{agente} — Tarea fallando*\n\n"
        f"📌 Tarea: `{nombre_tarea}`\n"
        f"📋 Qué pasó: {diagnostico}\n\n"
        f"🔧 Generando instrucción mejorada "
        f"(intento {intento}/{max_intentos})..."
    )

def avisar_reintento(nombre_tarea, intento, max_intentos, nueva_instruccion, agente):
    """Avisa que va a reintentar con nueva instrucción."""
    notificar_telegram(
        f"🔄 *{agente} — Reintentando* ({intento}/{max_intentos})\n\n"
        f"📌 Tarea: `{nombre_tarea}`\n"
        f"💡 Nueva estrategia: {nueva_instruccion[:150]}"
    )

def avisar_tarea_resuelta(nombre_tarea, intento, agente):
    """Avisa que se resolvió el problema."""
    notificar_telegram(
        f"✅ *{agente} — Problema resuelto*\n\n"
        f"📌 Tarea: `{nombre_tarea}`\n"
        f"🎉 Resuelto en intento {intento}. Continúa."
    )

def avisar_tarea_abandonada(nombre_tarea, diagnostico, causa_tecnica,
                             accion_sugerida, agente, escalar_claude=False):
    """Avisa que no se pudo resolver y detalla qué hacer."""
    emoji = "🆘" if escalar_claude else "🔴"
    extra = "\n\n🤖 *Escalando a Claude Code* — te mando los detalles aparte." if escalar_claude else ""
    notificar_telegram(
        f"{emoji} *{agente} — No pude resolver `{nombre_tarea}`*\n\n"
        f"📋 *Qué pasó:*\n{diagnostico}\n\n"
        f"🔍 *Causa técnica:*\n`{causa_tecnica[:120]}`\n\n"
        f"⏭️ Salté esta tarea y continúo con la siguiente."
        f"{extra}\n\n"
        f"🆘 *Qué necesitás hacer vos:*\n{accion_sugerida}"
    )
