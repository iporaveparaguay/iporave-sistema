"""
CEREBRO MONITOR - IporÃ£ve Connect
Analiza el sistema cada 30 minutos usando Gemini 2.5 Pro (AI Studio, GRATIS).
Si detecta errores â†' alerta directamente al usuario por Telegram con diagnÃ³stico completo.

DiseÃ±o:
- Lee pizarrÃ³n + alerts.json + estado del pool
- EnvÃ­a TODO el contexto a Gemini 2.5 Pro (2M tokens = puede leer TODO)
- Si hay errores nuevos â†' alerta con diagnÃ³stico detallado + acciones concretas
- Anti-spam: no repite la misma alerta â†' solo alerta si hay errores NUEVOS
- Si los errores persisten 3 ciclos â†' eleva la alerta (mÃ¡s urgente)
- NO toma decisiones, NO modifica archivos - SOLO alerta y diagnostica

Costo: $0 (AI Studio gratis, 50 req/dÃ­a con Gemini 2.5 Pro)
Uso: python cerebro-monitor.py
"""

import json, sys, time, urllib.request, urllib.error, hashlib, ssl
from pathlib import Path
from datetime import datetime, timezone

ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# â"€â"€â"€ CONFIG â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
_BASE          = Path(__file__).parent
PIZARRON_URL   = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
KEYS_PATH      = r"C:\Users\USUARIO\node-red-config\api-keys.json"
ORQUESTADOR_MD = _BASE / "ORQUESTADOR.md"
ALERTS_FILE    = _BASE / "alerts.json"
PARADA_CRITICA = _BASE / "PARADA_CRITICA.txt"

INTERVALO_NORMAL_SEG  = 600   # 10 min en reposo
INTERVALO_ALERTA_SEG  = 300   # 5 min cuando hay errores activos
MAX_ERRORES_PERSISTEN = 3     # escalada de alerta despuÃ©s de 3 ciclos con error
ANALISIS_PROFUNDO_CADA_N = 4  # si no hay seÃ±ales, usar IA solo cada 4 ciclos

AGENTE_NOMBRE = "Cerebro-Monitor"
ARRANQUE_VIGILADO_CICLOS = 0  # legacy desactivado (sin rampa)

# AI Studio endpoint
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Mapeo: nombres del pool (usados por aider) â†' nombres reales de la REST API
# Ver: GET https://generativelanguage.googleapis.com/v1beta/models"key=...
_NOMBRE_REST = {
    "gemini-2.5-pro-latest":  "gemini-2.5-pro",
    "gemini-1.5-pro-latest":  "gemini-pro-latest",
    "gemini-2.5-flash-latest":"gemini-2.5-flash",
    "gemini-1.5-flash-latest":"gemini-flash-latest",
    "vertex_ai/gemini-2.5-flash": "gemini-2.5-flash",
}

# Lista de modelos Pro + Flash como fallback para el cerebro-monitor
# Si Pro da 429 (rate limit 2 RPM) â†' usar Flash que tiene 15 RPM
_MODELOS_CEREBRO = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

# â"€â"€â"€ IMPORTS DEL POOL â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

try:
    from model_pool import (get_modelo_pro, get_api_key,
                            registrar_uso_pro, registrar_uso_flash,
                            get_estado_resumen)
    _POOL_OK = True
except ImportError:
    _POOL_OK = False
    def get_modelo_pro():   return "gemini-2.5-pro-latest"
    def get_api_key():
        try:
            with open(KEYS_PATH, encoding="utf-8") as f:
                return json.load(f).get("google_ai_studio", "")
        except: return ""
    def registrar_uso_pro(): pass
    def registrar_uso_flash(): pass
    def get_estado_resumen(): return "pool no disponible"

# â"€â"€â"€ ESTADO EN MEMORIA â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
# hash_errores_anterior: fingerprint de los errores del ciclo anterior
# para detectar si son errores NUEVOS o los mismos de antes
_estado = {
    "hash_errores_anterior": "",
    "ciclos_con_error":      0,
    "ciclos_totales":        0,
    "ultimo_error_notif":    "",
}

# â"€â"€â"€ ALERTAS (reemplaza Telegram) â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def escribir_alerta_cerebro(texto, nivel='info'):
    """Escribe diagnÃ³stico en alerts.json. Sin Telegram."""
    try:
        alertas = []
        if ALERTS_FILE.exists():
            try:
                alertas = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
            except:
                alertas = []
        alertas.append({
            "timestamp": datetime.now().isoformat(),
            "nivel": nivel,
            "mensaje": texto[:500]
        })
        alertas = alertas[-100:]
        ALERTS_FILE.write_text(json.dumps(alertas, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [ALERTA-{nivel.upper()}] guardada en alerts.json")
        return True
    except Exception as e:
        print(f"  [ALERTA] Error escribiendo: {e}")
        return False

# â"€â"€â"€ PIZARRÃ"N â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def leer_pizarron():
    try:
        req = urllib.request.Request(PIZARRON_URL, headers={
            "Accept": "application/json",
            "User-Agent": "IporaveAgent/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            registros = data.get("registros", []) if isinstance(data, dict) else data
            return registros if isinstance(registros, list) else []
    except Exception as e:
        print(f"  [PizarrÃ³n] Error: {e}")
        return []

def reportar_pizarron(tarea, estado, resumen):
    body = json.dumps({
        "agente":   AGENTE_NOMBRE,
        "tarea":    tarea,
        "archivos": "-",
        "estado":   estado,
        "resumen":  resumen
    }).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except: pass

# â"€â"€â"€ LEER CONTEXTO â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def leer_alerts_json():
    try:
        if not ALERTS_FILE.exists():
            return []
        alerts = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
        # Solo las no reconocidas (ack=False)
        return [a for a in alerts if not a.get("ack", False)][-20:]
    except:
        return []

def leer_tareas_pendientes():
    try:
        if not ORQUESTADOR_MD.exists():
            return "ORQUESTADOR.md no encontrado"
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        # Solo las primeras 3000 chars para no gastar tokens
        return contenido[:3000]
    except:
        return "Error leyendo ORQUESTADOR.md"

def _parse_fecha_registro(valor):
    try:
        if not valor:
            return None
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).replace(tzinfo=None)
    except:
        return None

def detectar_senales_sistema(registros, alerts):
    """DiagnÃ³stico barato, sin gastar tokens, antes de llamar a Gemini."""
    senales = []
    ahora = datetime.now()
    recientes = registros[-80:] if len(registros) > 80 else registros

    estados_malos = ("ERROR", "ALERTA", "BLOQUEADA", "CRITICA", "PARADA", "FALL")
    malos = []
    for r in recientes:
        estado = str(r.get("estado", "")).upper()
        resumen = str(r.get("resumen", "")).upper()
        if any(x in estado or x in resumen for x in estados_malos):
            malos.append(r)

    if malos:
        por_tarea = {}
        for r in malos:
            key = (r.get("agente", """), r.get("tarea", """))
            por_tarea[key] = por_tarea.get(key, 0) + 1
        repetidos = [f"{a}/{t}: {n}" for (a, t), n in por_tarea.items() if n >= 2]
        if repetidos:
            senales.append("Errores repetidos en pizarron: " + "; ".join(repetidos[:6]))
        else:
            senales.append(f"Hay {len(malos)} entradas recientes con error/alerta.")

    if alerts:
        senales.append(f"Hay {len(alerts)} alerta(s) local(es) sin reconocer en alerts.json.")

    try:
        if ORQUESTADOR_MD.exists():
            contenido = ORQUESTADOR_MD.read_text(encoding="utf-8", errors="replace")
            bloqueadas = [l for l in contenido.splitlines() if "- [!]" in l]
            if bloqueadas:
                senales.append(f"Hay {len(bloqueadas)} tarea(s) bloqueada(s) en ORQUESTADOR.md.")
    except:
        senales.append("No se pudo leer ORQUESTADOR.md para detectar bloqueos.")

    agentes = ["Supervisor", "Orquestador-Features", "Orquestador-Catalog",
               "Orquestador-Worker", "Orquestador-Paginas", "Orquestador-Principal",
               "Codex-Solucionador"]
    ultimo = {}
    for r in registros:
        ag = r.get("agente")
        if ag in agentes:
            dt = _parse_fecha_registro(r.get("created_at"))
            if dt:
                ultimo[ag] = max(ultimo.get(ag, dt), dt)
    inactivos = []
    for ag in agentes:
        limite_min = 10 if ag == "Supervisor" else 30
        dt = ultimo.get(ag)
        if dt and (ahora - dt).total_seconds() / 60 > limite_min:
            inactivos.append(f"{ag} sin reporte hace {int((ahora-dt).total_seconds()/60)} min")
    if inactivos:
        senales.append("Posible inactividad: " + "; ".join(inactivos[:6]))

    return senales

def construir_contexto(registros, alerts, senales=None):
    """
    Construye el contexto completo para Gemini 2.5 Pro.
    Incluye los Ãºltimos 40 registros del pizarrÃ³n + alerts no reconocidas + estado del pool.
    """
    # Filtrar los 40 mÃ¡s recientes
    ultimos = registros[-40:] if len(registros) > 40 else registros

    pizarron_str = ""
    for r in ultimos:
        ts   = r.get("created_at", "")[:16]
        ag   = r.get("agente", """)
        ta   = r.get("tarea", """)
        est  = r.get("estado", """)
        res  = r.get("resumen", "")[:120]
        pizarron_str += f"[{ts}] {ag} | {ta} | {est} | {res}\n"

    alerts_str = ""
    for a in alerts:
        ts   = a.get("timestamp", "")[:16]
        tipo = a.get("tipo", """)
        msg  = a.get("mensaje", "")[:200]
        alerts_str += f"[{ts}] [{tipo}] {msg}\n"

    tareas_str = leer_tareas_pendientes()

    pool_str = get_estado_resumen() if _POOL_OK else "pool_pool no disponible"
    senales_str = "\n".join(f"- {s}" for s in (senales or [])) or "(sin seÃ±ales determinÃ­sticas)"

    return f"""=== CONTEXTO DEL SISTEMA IPORÃƒVE CONNECT ===

SISTEMA: Plataforma logÃ­stica en Paraguay.
- Backend: Cloudflare Worker (iporave-worker/)
- Frontend: Vercel (iporave-sistema/public/index.html - 562K chars)
- Agentes: 6 orquestadores Python + Supervisor + TelegramBridge
- Estado del pool de modelos: {pool_str}
- Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M')}

=== PIZARRÃ"N - ÃšLTIMAS 40 ENTRADAS ===
{pizarron_str or '(vacÃ­o)'}

=== ALERTAS NO RECONOCIDAS (alerts.json) ===
{alerts_str or '(ninguna)'}

=== SENALES DETERMINISTICAS DETECTADAS SIN IA ===
{senales_str}

=== TAREAS PENDIENTES (ORQUESTADOR.md - primeros 3000 chars) ===
{tareas_str}
"""

# â"€â"€â"€ GEMINI 2.5 PRO - ANÃLISIS â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
SYSTEM_PROMPT_MONITOR = """Sos el cerebro monitor de IporÃ£ve Connect, un sistema logÃ­stico en Paraguay.
Tu trabajo es analizar el estado del sistema y detectar problemas reales que necesiten atenciÃ³n humana.

REGLAS:
1. Si todo funciona bien â†' no alarmes, respondÃ© con hay_errores=false
2. Solo alarmÃ¡ si hay errores REALES que bloquean el sistema o que el usuario debe saber
3. IgnorÃ¡ errores transitorios normales (una sola falla de quota, un timeout aislado)
4. SÃ­ alarmÃ¡ si: un orquestador estÃ¡ caÃ­do, una tarea estÃ¡ bloqueada [!], hay errores repetidos 3+ veces, hay corrupciÃ³n de datos, o hay algo que requiera intervenciÃ³n manual

5. IMPORTANTE POOL: el formato (usadas/limite) es consumo, no saldo. Ejemplo: 0/50 significa sin uso (saludable), NO significa agotado.
6. Solo reportÃƒÂ¡ agotamiento de modelos si usadas >= limite, o si hay error real de cuota (429/RESOURCE_EXHAUSTED).

FORMATO DE RESPUESTA (JSON estricto):
{
  "hay_errores": true/false,
  "nivel": "info" | "advertencia" | "critico",
  "errores_detectados": ["descripciÃ³n breve de cada error real"],
  "diagnostico": "anÃ¡lisis en 2-4 lÃ­neas de quÃ© estÃ¡ pasando y por quÃ©",
  "acciones_sugeridas": ["acciÃ³n concreta 1", "acciÃ³n concreta 2"],
  "resumen_estado": "una lÃ­nea describiendo el estado general del sistema"
}

SÃ© conciso, preciso y accionable. El usuario es el dueÃ±o del sistema y quiere saber exactamente quÃ© hacer."""

def _llamar_gemini_rest(modelo_rest, prompt, api_key):
    """
    Hace una llamada directa a la REST API de AI Studio.
    Devuelve el texto de respuesta, o lanza excepciÃ³n.
    """
    url = f"{GEMINI_API_BASE}/{modelo_rest}:generateContent?key={api_key}"
    # Pro models: usar thinking para mejor anÃ¡lisis
    # Flash models: deshabilitar thinking (ahorra tokens, evita truncamiento)
    es_pro = "pro" in modelo_rest
    config = {
        "response_mime_type": "application/json",
        "temperature":        0.2,
        "maxOutputTokens":    2048
    }
    if not es_pro:
        # Flash tiene thinking habilitado por defecto y consume tokens en exceso
        config["thinkingConfig"] = {"thinkingBudget": 0}

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": config
    }
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read().decode())
    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()

def analizar_con_gemini(contexto):
    """
    Llama a Gemini via AI Studio (Pro primero, Flash como fallback si 429).
    Devuelve dict con el anÃ¡lisis o None si todos fallan.
    """
    api_key = get_api_key()
    if not api_key:
        print("  [Gemini] Sin API key â€ - verificar api-keys.json")
        return None

    prompt = f"{SYSTEM_PROMPT_MONITOR}\n\n{contexto}"

    # Intentar cada modelo en _MODELOS_CEREBRO (Pro â†' Flash â†' ...)
    modelo_pool = _NOMBRE_REST.get(get_modelo_pro(), get_modelo_pro())
    modelos = []
    for m in [modelo_pool] + _MODELOS_CEREBRO:
        if m and m not in modelos:
            modelos.append(m)

    for modelo in modelos:
        print(f"  Modelo: {modelo}")
        try:
            texto = _llamar_gemini_rest(modelo, prompt, api_key)

            # Limpiar markdown si viene con ```json
            if texto.startswith("```"):
                partes = texto.split("```")
                texto  = partes[1]
                if texto.startswith("json"):
                    texto = texto[4:].strip()

            resultado = json.loads(texto)

            # Registrar uso - Pro si fue Pro, Flash si fue Flash
            if "pro" in modelo:
                registrar_uso_pro()
            else:
                registrar_uso_flash()

            print(f"  OK Respuesta de {modelo}")
            return resultado

        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode()[:200]
            if e.code == 429:
                print(f"  {modelo}: rate limit 429 - probando siguiente...")
                continue
            elif e.code == 503:
                print(f"  {modelo}: servicio no disponible 503 - probando siguiente...")
                continue
            else:
                print(f"  {modelo}: HTTP {e.code} - {cuerpo[:100]}")
                continue
        except json.JSONDecodeError as e:
            print(f"  {modelo}: respuesta no es JSON vÃ¡lido - {e}")
            continue
        except Exception as e:
            print(f"  {modelo}: Error - {e}")
            continue

    print("  [Gemini] Todos los modelos fallaron")
    return None

# â"€â"€â"€ FINGERPRINT ANTI-SPAM â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def calcular_hash_errores(errores):
    """Devuelve un hash corto del listado de errores para detectar cambios."""
    if not errores:
        return ""
    clave = "|".join(sorted(str(e)[:80] for e in errores))
    return hashlib.md5(clave.encode()).hexdigest()[:12]

# â"€â"€â"€ FORMATEAR ALERTA TELEGRAM â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def formatear_alerta(analisis, ciclos_persistentes):
    nivel      = analisis.get("nivel", "advertencia")
    errores    = analisis.get("errores_detectados", [])
    diagnostico = analisis.get("diagnostico", "")
    acciones   = analisis.get("acciones_sugeridas", [])
    resumen    = analisis.get("resumen_estado", "")

    # Emoji por nivel
    emoji_nivel = {"info": "[i]", "advertencia": "[!]", "critico": "[!!!]"}.get(nivel, "[!]")

    # Indicar si persiste
    persistencia = ""
    if ciclos_persistentes >= 2:
        persistencia = f"\n[PERSISTENTE] *Este error lleva {ciclos_persistentes} ciclos sin resolverse ({ciclos_persistentes * 30} min)*"

    # Errores
    errores_str = "\n".join(f"- {e}" for e in errores[:5])

    # Acciones
    acciones_str = "\n".join(f"{i+1}. {a}" for i, a in enumerate(acciones[:4]))

    hora = datetime.now().strftime("%H:%M")
    fecha = datetime.now().strftime("%d/%m")

    msg = (
        f"{emoji_nivel} *CEREBRO-MONITOR - {nivel.upper()}*  _{fecha} {hora}_\n"
        f"{persistencia}\n\n"
        f"[=] *Estado general:* {resumen}\n\n"
        f"[X] *Errores detectados:*\n{errores_str}\n\n"
        f"[?] *Diagnostico:*\n{diagnostico}\n\n"
        f"[>] *Acciones sugeridas:*\n{acciones_str}\n\n"
        f"_Proxima revision: 10 min_"
    )
    return msg

# â"€â"€â"€ CICLO PRINCIPAL â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def ciclo():
    _estado["ciclos_totales"] += 1
    resumen_estado = "Sin datos"
    ahora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*55}")
    print(f"  [{AGENTE_NOMBRE}] Ciclo {_estado['ciclos_totales']} | {ahora}")
    print(f"{'='*55}")

    # â"€â"€ PARADA CRÃTICA â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    if PARADA_CRITICA.exists():
        print("  - PARADA CRÃTICA activa - saltando ciclo")
        proxima = "5 min" if _estado["ciclos_totales"] < ARRANQUE_VIGILADO_CICLOS else "20 min"
        escribir_alerta_cerebro(
            f"ðŸŸ¢ *Cerebro-Monitor activo*\n\n"
            f"Ciclo: `{_estado['ciclos_totales']}`\n"
            f"Estado: {resumen_estado}\n"
            f"Errores detectados: `0`\n\n"
            f"_PrÃ³xima revisiÃ³n: {proxima}_"
        )
        return INTERVALO_ALERTA_SEG if _estado["ciclos_totales"] < ARRANQUE_VIGILADO_CICLOS else INTERVALO_NORMAL_SEG

    # â"€â"€ RECOPILAR CONTEXTO â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    print("  Leyendo pizarrÃ³n + alerts.json...")
    registros = leer_pizarron()
    alerts    = leer_alerts_json()
    print(f"  â†' {len(registros)} registros en pizarrÃ³n, {len(alerts)} alertas pendientes")

    senales = detectar_senales_sistema(registros, alerts)
    if senales:
        print("  SeÃ±ales detectadas sin IA:")
        for s in senales[:6]:
            print("   - " + s)
    elif _estado["ciclos_totales"] % ANALISIS_PROFUNDO_CADA_N != 0:
        resumen = "Sin seÃ±ales de error. Se omite anÃ¡lisis IA para ahorrar tokens."
        print("  " + resumen)
        reportar_pizarron("monitor-ciclo", "Activo", resumen)
        proxima = "5 min" if _estado["ciclos_totales"] < ARRANQUE_VIGILADO_CICLOS else "20 min"
        escribir_alerta_cerebro(
            f"ðŸŸ¢ *Cerebro-Monitor activo*\n\n"
            f"Ciclo: `{_estado['ciclos_totales']}`\n"
            f"PizarrÃ³n: `{len(registros)}` registros\n"
            f"Alertas pendientes: `{len(alerts)}`\n"
            f"Estado: sin seÃ±ales de error.\n\n"
            f"_PrÃ³xima revisiÃ³n: {proxima}_"
        )
        return INTERVALO_ALERTA_SEG if _estado["ciclos_totales"] < ARRANQUE_VIGILADO_CICLOS else INTERVALO_NORMAL_SEG

    contexto = construir_contexto(registros, alerts, senales)

    # â"€â"€ ANÃLISIS CON GEMINI PRO â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    modelo_activo = get_modelo_pro()
    print(f"  Analizando con {modelo_activo}...")
    analisis = analizar_con_gemini(contexto)

    if analisis is None:
        print("  [!] Gemini no respondiÃ³ - reintentando en el prÃ³ximo ciclo")
        reportar_pizarron("monitor-ciclo", "Error", "Gemini Pro no respondiÃ³ al anÃ¡lisis")
        return INTERVALO_NORMAL_SEG

    hay_errores    = analisis.get("hay_errores", False)
    nivel          = analisis.get("nivel", "info")
    resumen_estado = analisis.get("resumen_estado", "Sin datos")
    errores        = analisis.get("errores_detectados", [])

    print(f"  AnÃ¡lisis: hay_errores={hay_errores} | nivel={nivel}")
    print(f"  Estado: {resumen_estado}")

    # Siempre reportar al pizarrÃ³n para que el supervisor sepa que el cerebro estÃ¡ vivo
    reportar_pizarron(
        "monitor-ciclo",
        "ALERTA" if hay_errores and nivel == "critico" else "Activo",
        f"[{nivel}] {resumen_estado} | Errores: {len(errores)}"
    )

    # â"€â"€ ANTI-SPAM: Â¿Son errores NUEVOS" â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    hash_actual = calcular_hash_errores(errores)

    if hay_errores:
        if hash_actual == _estado["hash_errores_anterior"]:
            # Mismos errores de antes â†' incrementar contador de persistencia
            _estado["ciclos_con_error"] += 1
            print(f"  Mismos errores de antes (ciclos_con_error={_estado['ciclos_con_error']})")

            # Solo re-alertar en escalada: cada 3 ciclos que persiste
            if _estado["ciclos_con_error"] % 3 != 0:
                print("  Skipping alerta (no escalada todavÃ­a)")
                return INTERVALO_ALERTA_SEG
        else:
            # Errores nuevos o distintos â†' resetear contador y siempre alertar
            _estado["ciclos_con_error"] = 1
            _estado["hash_errores_anterior"] = hash_actual
            print(f"  Errores NUEVOS detectados - alertando...")

        # â"€â"€ ENVIAR ALERTA TELEGRAM â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
        msg = formatear_alerta(analisis, _estado["ciclos_con_error"])
        ok  = escribir_alerta_cerebro(msg)
        if ok:
            print(f"  âœ… Alerta Telegram enviada ({nivel})")
        else:
            print(f"  âŒ Telegram no disponible - diagnÃ³stico solo en pizarrÃ³n")

        # Guardar diagnÃ³stico en pizarrÃ³n (siempre, incluso si Telegram fallÃ³)
        diagnostico_str = analisis.get("diagnostico", "")
        acciones_str    = " | ".join(analisis.get("acciones_sugeridas", [])[:3])
        reportar_pizarron(
            f"diagnostico-{nivel}",
            f"ALERTA-{'CRITICA' if nivel == 'critico' else nivel.upper()}",
            f"{diagnostico_str[:150]} â†' {acciones_str[:100]}"
        )

        return INTERVALO_ALERTA_SEG  # revisar mÃ¡s seguido mientras hay errores

    else:
        # Todo bien - resetear contadores
        if _estado["ciclos_con_error"] > 0:
            print(f"  âœ… Errores anteriores RESUELTOS - volviendo a ciclo normal")
            escribir_alerta_cerebro(
                f"âœ… *Cerebro-Monitor - Errores Resueltos*\n\n"
                f"Los errores detectados fueron resueltos.\n"
                f"Š Estado: {resumen_estado}\n"
                f"_Volviendo a monitoreo cada 10 min._"
            )
        _estado["ciclos_con_error"]      = 0
        _estado["hash_errores_anterior"] = ""
        print(f"  âœ… Sistema OK - {resumen_estado}")
        return INTERVALO_NORMAL_SEG

# â"€â"€â"€ ARRANQUE â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def main():
    modo_prueba = "--test" in sys.argv or "--once" in sys.argv
    print("=" * 55)
    print(f"  {AGENTE_NOMBRE} - Gemini 2.5 Pro AI Studio")
    print(f"  Ciclo: {INTERVALO_NORMAL_SEG//60} min (normal) / {INTERVALO_ALERTA_SEG//60} min (alerta)")
    print(f"  Pool: {'activo' if _POOL_OK else 'fallback directo'}")
    print("=" * 55)

    # Verificar API key
    api_key = get_api_key()
    if not api_key:
        print("  âŒ ERROR: google_ai_studio no encontrado en api-keys.json")
        print(f"     Verificar: {KEYS_PATH}")
        return

    print(f"  API key: {'*' * 20}{api_key[-6:]}")
    modelo = get_modelo_pro()
    print(f"  Modelo activo: {modelo}")

    print(f"  Alertas: {ALERTS_FILE} (sin Telegram)")

    if modo_prueba:
        print("  Modo prueba: ejecutando un solo ciclo y saliendo.")
        try:
            espera = ciclo()
            print(f"  Prueba finalizada. Proximo intervalo sugerido: {espera//60} min.")
        except Exception as e:
            print(f"  ERROR en prueba: {e}")
            reportar_pizarron("monitor-test", "Error", str(e)[:150])
        return

    # Notificar inicio
    reportar_pizarron("monitor-inicio", "Activo",
                      f"Cerebro-Monitor iniciado. Modelo: {modelo}. "
                      f"Ciclo: {INTERVALO_NORMAL_SEG//60} min.")
    escribir_alerta_cerebro(
        f"ðŸ§  *Cerebro-Monitor iniciado*\n\n"
        f"Modelo: `{modelo}`\n"
        f"Ciclo normal: cada 10 min\n"
        f"Ciclo con errores: cada 5 min\n\n"
        f"_Vigilando el sistema IporÃ£ve..._"
    )

    if "--test" in sys.argv or "--once" in sys.argv:
        print("  Modo prueba: ejecutando un solo ciclo y saliendo.")
        try:
            espera = ciclo()
            print(f"  Prueba finalizada. Proximo intervalo sugerido: {espera//60} min.")
        except Exception as e:
            print(f"  ERROR en prueba: {e}")
            reportar_pizarron("monitor-test", "Error", str(e)[:150])
        return

    # Loop principal
    siguiente_espera = INTERVALO_NORMAL_SEG
    while True:
        try:
            siguiente_espera = ciclo()
        except KeyboardInterrupt:
            print(f"\n  {AGENTE_NOMBRE} detenido.")
            reportar_pizarron("monitor-stop", "Detenido", "Cerebro-Monitor detenido manualmente")
            break
        except Exception as e:
            print(f"  [Error] {e}")
            reportar_pizarron("monitor-error", "Error", str(e)[:150])
            siguiente_espera = INTERVALO_NORMAL_SEG

        print(f"\n  PrÃ³ximo ciclo en {siguiente_espera//60} min. ({datetime.now().strftime('%H:%M')})")
        time.sleep(siguiente_espera)

if __name__ == "__main__":
    main()

