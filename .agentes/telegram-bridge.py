"""
TELEGRAM BRIDGE — Iporãve Connect
Puente entre el bot @Iporave_Bot y el sistema de orquestadores.

Flujo:
  Mensaje tuyo en Telegram
    → Gemini 2.5 Flash lo procesa
    → Se registra en el Pizarrón como COMANDO
    → Orquestador lo ejecuta
    → Supervisor reporta resultado
    → Bot te responde con confirmación

Primer uso: enviá cualquier mensaje al bot para capturar tu Telegram ID.
Uso: python telegram-bridge.py
"""

import json, os, sys, time, urllib.request, urllib.parse, ssl
from pathlib import Path
from datetime import datetime

# Fix SSL en Windows — evita el error de certificado autofirmado
ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIG ───────────────────────────────────────────────────────────────────
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
CLAVE_JSON     = r"C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json"
PROJECT        = "rugged-shell-430212-f6"
LOCATION       = "us-central1"
CONFIG_FILE    = Path(__file__).parent / "telegram-config.json"
MEMORIA_FILE   = Path(__file__).parent / "telegram-memoria.json"
CONTEXTO_FILE  = Path(__file__).parent / "CONTEXTO_SISTEMA.md"
ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
INTERVALO_SEG  = 3   # revisar Telegram cada 3 segundos

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLAVE_JSON
os.environ["VERTEXAI_PROJECT"]               = PROJECT
os.environ["VERTEXAI_LOCATION"]              = LOCATION

# ─── CARGAR KEYS ──────────────────────────────────────────────────────────────
with open(KEYS_PATH, encoding="utf-8") as f:
    keys = json.load(f)

TOKEN    = keys["telegram_token"]
TG_API   = f"https://api.telegram.org/bot{TOKEN}"
GROQ_API_KEY = keys.get("groq", "")
GROQ_MODELOS = ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile"]

# ─── CONFIG PERSISTENTE (guarda tu chat_id) ───────────────────────────────────
def cargar_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {"admin_chat_id": None, "ultimo_update_id": 0}

def guardar_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

config = cargar_config()

# ─── TELEGRAM API ─────────────────────────────────────────────────────────────
def tg_request(metodo, datos=None):
    url  = f"{TG_API}/{metodo}"
    body = json.dumps(datos).encode() if datos else None
    headers = {"Content-Type": "application/json"} if body else {}
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [TG] Error {metodo}: {e}")
        return None

def enviar_mensaje(chat_id, texto):
    tg_request("sendMessage", {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"})

def get_updates(offset=0):
    resp = tg_request("getUpdates", {"offset": offset, "timeout": 2, "limit": 10})
    if resp and resp.get("ok"):
        return resp.get("result", [])
    return []

# ─── PIZARRÓN ─────────────────────────────────────────────────────────────────
def leer_pizarron():
    try:
        req = urllib.request.Request(PIZARRON_URL, headers={
            "Accept": "application/json",
            "User-Agent": "IporaveAgent/1.0"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("registros", []) if isinstance(data, dict) else data
    except:
        return []

def publicar_comando(tarea, instruccion, chat_id):
    body = json.dumps({
        "agente":   "COMANDO",
        "tarea":    tarea,
        "archivos": "-",
        "estado":   "Pendiente",
        "resumen":  instruccion
    }).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"  [Pizarrón] Error publicando: {e}")
        return False

# ─── GEMINI — PROCESAR MENSAJE ────────────────────────────────────────────────
def cargar_memoria():
    try:
        if MEMORIA_FILE.exists():
            data = json.loads(MEMORIA_FILE.read_text(encoding="utf-8"))
            return data[-20:] if isinstance(data, list) else []
    except:
        pass
    return []

def guardar_memoria(memoria):
    try:
        MEMORIA_FILE.write_text(json.dumps(memoria[-20:], indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  [Memoria] Error guardando: {e}")

def construir_contexto_bot():
    partes = []
    try:
        if CONTEXTO_FILE.exists():
            partes.append("CONTEXTO_SISTEMA.md:\n" + CONTEXTO_FILE.read_text(encoding="utf-8", errors="replace")[:5000])
    except:
        pass
    try:
        if ORQUESTADOR_MD.exists():
            partes.append("ORQUESTADOR.md:\n" + ORQUESTADOR_MD.read_text(encoding="utf-8", errors="replace")[:5000])
    except:
        pass
    try:
        regs = leer_pizarron()
        ultimos = regs[-12:] if isinstance(regs, list) else []
        partes.append("PIZARRON_ULTIMAS_ENTRADAS:\n" + json.dumps(ultimos, ensure_ascii=False)[:5000])
    except:
        pass
    return "\n\n---\n\n".join(partes)

def _extraer_json(texto):
    texto = (texto or "").strip()
    if "</think>" in texto:
        texto = texto.split("</think>")[-1].strip()
    if texto.startswith("```"):
        partes = texto.split("```")
        texto = partes[1] if len(partes) > 1 else texto
        if texto.startswith("json"):
            texto = texto[4:].strip()
    inicio = texto.find("{")
    fin = texto.rfind("}") + 1
    if inicio >= 0 and fin > inicio:
        texto = texto[inicio:fin]
    return json.loads(texto)

SYSTEM_PROMPT = """Sos el asistente de control de Iporãve Connect.
El usuario te habla desde Telegram. Puede preguntarte cosas, pedirte información, o darte órdenes.

REGLA PRINCIPAL:
- Si el usuario pregunta algo, pide info, o solo conversa → tipo="consulta", NO tocar el pizarrón
- Solo si el usuario da una ORDEN EXPLÍCITA de hacer algo en el sistema (modificar código, ejecutar tarea, etc.) → tipo="tarea"
- Las consultas sobre estado del sistema → tipo="estado"

Ejemplos de CONSULTA (NO va al pizarrón):
- "¿Cómo va todo?"
- "¿Qué hicieron los agentes hoy?"
- "¿Cuánto costó esta sesión?"
- "Explicame qué hace el orquestador"

Ejemplos de TAREA (SÍ va al pizarrón):
- "Agregá un botón de exportar en el panel admin"
- "Corregí el error en el endpoint de pedidos"
- "Hacé que el catálogo muestre el precio en guaraníes"

Formato de respuesta JSON:
{
  "tipo": "tarea" | "consulta" | "estado",
  "nombre_tarea": "slug-corto-solo-si-es-tarea",
  "instruccion": "instruccion completa para aider solo si es tarea",
  "respuesta_usuario": "respuesta en español, clara y directa"
}
"""

def procesar_con_gemini(texto_usuario):
    memoria = cargar_memoria()
    contexto = construir_contexto_bot()
    mensajes = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\nContexto actual del sistema:\n" + contexto},
    ]
    for item in memoria[-20:]:
        rol = item.get("role")
        contenido = item.get("content", "")
        if rol in ("user", "assistant") and contenido:
            mensajes.append({"role": rol, "content": contenido[:1200]})
    mensajes.append({"role": "user", "content": texto_usuario})

    if not GROQ_API_KEY:
        return {
            "tipo": "consulta",
            "nombre_tarea": "",
            "instruccion": "",
            "respuesta_usuario": "No tengo configurada la clave de Groq para responder desde Telegram."
        }

    ultimo_error = ""
    for modelo in GROQ_MODELOS:
        try:
            body = json.dumps({
                "model": modelo,
                "messages": mensajes,
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + GROQ_API_KEY
                }
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode())
            texto = data["choices"][0]["message"]["content"]
            resultado = _extraer_json(texto)
            memoria.append({"role": "user", "content": texto_usuario})
            memoria.append({"role": "assistant", "content": resultado.get("respuesta_usuario", "")})
            guardar_memoria(memoria)
            return resultado
        except Exception as e:
            ultimo_error = str(e)
            print(f"  [Groq/{modelo}] Error: {e}")

    print(f"  [Groq] Todos los modelos fallaron: {ultimo_error}")
    return {
        "tipo": "consulta",
        "nombre_tarea": "",
        "instruccion": "",
        "respuesta_usuario": "No pude procesar el mensaje con la IA del bot. Error: " + ultimo_error[:160]
    }

def procesar_con_gemini_vertex_legacy(texto_usuario):
    try:
        from google import genai
        from google.genai import types

        client  = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
        model   = "gemini-2.5-flash"
        prompt  = f"{SYSTEM_PROMPT}\n\nMensaje del usuario: {texto_usuario}"

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
        )
        texto = response.text.strip()
        # limpiar markdown si viene con ```json
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        return json.loads(texto)
    except Exception as e:
        print(f"  [Gemini] Error: {e}")
        return {
            "tipo": "consulta",
            "nombre_tarea": "",
            "instruccion": "",
            "respuesta_usuario": f"Error procesando mensaje: {e}"
        }

# ─── PROCESAR ACTUALIZACIÓN DE TELEGRAM ───────────────────────────────────────
def procesar_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    texto   = msg.get("text", "")
    voz     = msg.get("voice")
    nombre  = msg["from"].get("first_name", "Usuario")

    # ── PRIMER USO: capturar el admin_chat_id ──────────────────────────────────
    if config["admin_chat_id"] is None:
        config["admin_chat_id"] = chat_id
        guardar_config(config)
        enviar_mensaje(chat_id,
            f"✅ *Iporãve Bot activado*\n\n"
            f"Tu ID: `{chat_id}`\n"
            f"Ahora solo vos podés dar órdenes.\n\n"
            f"Comandos disponibles:\n"
            f"• `/estado` — ver estado del sistema\n"
            f"• `/alertas` — ver últimas alertas\n"
            f"• Cualquier texto — procesar con IA y ejecutar"
        )
        return

    # ── FILTRO DE SEGURIDAD ───────────────────────────────────────────────────
    if chat_id != config["admin_chat_id"]:
        enviar_mensaje(chat_id, "⛔ No autorizado.")
        return

    # ── COMANDOS ESPECIALES ───────────────────────────────────────────────────
    if texto == "/estado":
        registros = leer_pizarron()
        ultimos = registros[-5:] if registros else []
        if not ultimos:
            enviar_mensaje(chat_id, "📋 Pizarrón vacío.")
            return
        lineas = []
        for r in reversed(ultimos):
            emoji = "✅" if r["estado"] == "Finalizado" else "🔴" if "ALERTA" in r["estado"] else "⏳"
            lineas.append(f"{emoji} *{r['agente']}*: {r['tarea']} — {r['estado']}")
        enviar_mensaje(chat_id, "📋 *Últimas actividades:*\n\n" + "\n".join(lineas))
        return

    if texto == "/alertas":
        registros = leer_pizarron()
        alertas = [r for r in registros if "ALERTA" in r.get("estado", "")]
        if not alertas:
            enviar_mensaje(chat_id, "✅ Sin alertas activas.")
            return
        lineas = [f"🔴 *{r['tarea']}*: {r['resumen'][:80]}" for r in alertas[-5:]]
        enviar_mensaje(chat_id, "🚨 *Alertas activas:*\n\n" + "\n".join(lineas))
        return

    # ── MENSAJE DE VOZ ────────────────────────────────────────────────────────
    if voz:
        enviar_mensaje(chat_id, "🎤 Audio recibido. Por ahora solo proceso texto. Escribí tu orden.")
        return

    if not texto:
        return

    # ── PROCESAR CON GEMINI ───────────────────────────────────────────────────
    resultado = procesar_con_gemini(texto)
    tipo      = resultado.get("tipo", "consulta")

    if tipo == "tarea":
        # Solo aquí se escribe en el pizarrón
        nombre_tarea = resultado.get("nombre_tarea", "tarea-telegram")
        instruccion  = resultado.get("instruccion", texto)
        ok = publicar_comando(nombre_tarea, instruccion, chat_id)
        if ok:
            enviar_mensaje(chat_id,
                f"✅ *Orden enviada al orquestador*\n\n"
                f"📌 Tarea: `{nombre_tarea}`\n"
                f"📝 {instruccion[:120]}\n\n"
                f"_El orquestador la toma en el próximo ciclo (~2 min)._"
            )
        else:
            enviar_mensaje(chat_id, "❌ Error al enviar la orden. Verificar conexión.")

    elif tipo == "estado":
        # Solo lee el pizarrón, no escribe
        registros = leer_pizarron()
        ultimos = [r for r in registros[-5:]]
        resumen = resultado.get("respuesta_usuario", "Estado actual:")
        lineas = [f"• *{r['agente']}*: {r['tarea']} — {r['estado']}" for r in reversed(ultimos)]
        enviar_mensaje(chat_id, f"📊 {resumen}\n\n" + "\n".join(lineas))

    else:
        # Consulta normal — solo responde, nada al pizarrón
        enviar_mensaje(chat_id, resultado.get("respuesta_usuario", "👍"))

# ─── LOOP PRINCIPAL ───────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  TELEGRAM BRIDGE — @Iporave_Bot")
    print(f"  Admin configurado: {config['admin_chat_id'] or 'pendiente (enviá un mensaje al bot)'}")
    print("=" * 55)

    # Verificar conexión con Telegram
    info = tg_request("getMe")
    if info and info.get("ok"):
        bot = info["result"]
        print(f"  Bot conectado: @{bot['username']} ({bot['first_name']})")
    else:
        print("  ERROR: No se pudo conectar con Telegram. Verificar token.")
        return

    if config["admin_chat_id"] is None:
        print("\n  ⚠️  Enviá cualquier mensaje a @Iporave_Bot para activarlo.")

    offset = config.get("ultimo_update_id", 0)

    while True:
        try:
            updates = get_updates(offset + 1)
            for update in updates:
                uid = update["update_id"]
                if uid > offset:
                    offset = uid
                    config["ultimo_update_id"] = offset
                    guardar_config(config)
                    procesar_update(update)
        except KeyboardInterrupt:
            print("\n  Bridge detenido.")
            break
        except Exception as e:
            print(f"  [Bridge] Error: {e}")
        time.sleep(INTERVALO_SEG)

if __name__ == "__main__":
    main()
