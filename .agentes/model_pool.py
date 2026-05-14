"""
MODEL POOL — Iporãve Connect
Gestiona rotación automática entre los 4 modelos Gemini gratuitos (AI Studio).
Cuando un modelo agota su cuota diaria, pasa al siguiente automáticamente.

Dos pools independientes:
  FLASH pool: gemini-2.5-flash → gemini-1.5-flash → vertex_ai (crédito, último recurso)
  PRO pool:   gemini-2.5-pro   → gemini-1.5-pro   (para cerebro-monitor)

Límites gratuitos AI Studio:
  Flash: 1500 req/día, 15 RPM, 1M TPM
  Pro:   50 req/día,   2 RPM,  2M TPM

Switch al 85% del límite para evitar cortes inesperados.
Reset automático a medianoche.
"""

import json
import os
import time
from datetime import datetime, date, timedelta
from pathlib import Path


def _escribir_alerta_pool(texto, nivel="info"):
    try:
        alertas = []
        if ALERTS_FILE.exists():
            try:
                alertas = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
            except:
                alertas = []
        from datetime import datetime
        alertas.append({"timestamp": datetime.now().isoformat(), "nivel": nivel, "mensaje": texto})
        alertas = alertas[-100:]
        ALERTS_FILE.write_text(json.dumps(alertas, indent=2, ensure_ascii=False), encoding="utf-8")
    except:
        pass

# ─── CONFIG ───────────────────────────────────────────────────────────────────
_BASE        = Path(__file__).parent
KEYS_PATH    = r"C:\Users\USUARIO\node-red-config\api-keys.json"
ESTADO_FILE  = _BASE / "pool_estado.json"
ALERTS_FILE  = _BASE / "alerts.json"
PIZARRON_URL = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"

# Límites y umbrales de switch (85% del límite)
FLASH_CONFIG = {
    "gemini-2.5-flash-latest": {"limite": 1500, "switch_en": 1275, "rpm": 15},
    "gemini-1.5-flash-latest": {"limite": 1500, "switch_en": 1275, "rpm": 15},
    "vertex_ai/gemini-2.5-flash": {"limite": 99999, "switch_en": 99999, "rpm": 15},  # último recurso
}
PRO_CONFIG = {
    "gemini-2.5-pro-latest": {"limite": 50, "switch_en": 42, "rpm": 2},
    "gemini-1.5-pro-latest": {"limite": 50, "switch_en": 42, "rpm": 2},
}

FLASH_ORDER = ["gemini-2.5-flash-latest", "gemini-1.5-flash-latest", "vertex_ai/gemini-2.5-flash"]
PRO_ORDER   = ["gemini-2.5-pro-latest", "gemini-1.5-pro-latest"]

# ─── LOCK SIMPLE ──────────────────────────────────────────────────────────────
import sys
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

try:
    from lock_util import adquirir_lock, liberar_lock
    _USE_LOCK = True
except ImportError:
    _USE_LOCK = False
    def adquirir_lock(timeout_seg=15, agente="model_pool"): return True
    def liberar_lock(): pass

def _lock_pool():
    return adquirir_lock(timeout_seg=15, agente="model_pool") if _USE_LOCK else True

def _unlock_pool():
    if _USE_LOCK:
        liberar_lock()

# ─── ESTADO ───────────────────────────────────────────────────────────────────
def _estado_default():
    hoy = str(date.today())
    return {
        "fecha": hoy,
        "flash": {
            "activo": "gemini-2.5-flash-latest",
            **{m: {"usadas": 0} for m in FLASH_ORDER}
        },
        "pro": {
            "activo": "gemini-2.5-pro-latest",
            **{m: {"usadas": 0} for m in PRO_ORDER}
        }
    }

def _leer_estado():
    """Lee estado del pool. Si el archivo es de un día anterior, resetea."""
    if not ESTADO_FILE.exists():
        return _estado_default()
    try:
        s = json.loads(ESTADO_FILE.read_text(encoding="utf-8"))
        if s.get("fecha") != str(date.today()):
            # Nuevo día — resetear contadores
            nuevo = _estado_default()
            _guardar_estado(nuevo)
            return nuevo
        return s
    except Exception:
        return _estado_default()

def _guardar_estado(estado):
    """Guarda estado con lock para evitar race conditions."""
    _lock_pool()
    try:
        ESTADO_FILE.write_text(json.dumps(estado, indent=2), encoding="utf-8")
    finally:
        _unlock_pool()

# ─── NOTIFICACIONES ───────────────────────────────────────────────────────────
def _cargar_keys():
    try:
        with open(KEYS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _alerta_removida(mensaje):
    """Wrapper post-remoción de Telegram: solo escribe a alerts.json."""
    return _escribir_alerta_pool(mensaje, "info")

def _escribir_alerta(mensaje, tipo="switch"):
    """Escribe alerta en alerts.json como canal de respaldo."""
    _lock_pool()
    try:
        alerts = []
        if ALERTS_FILE.exists():
            try:
                alerts = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
            except Exception:
                alerts = []
        limite_ack = datetime.now() - timedelta(hours=24)
        depuradas = []
        for a in alerts:
            if a.get("ack"):
                try:
                    ts = datetime.fromisoformat(str(a.get("timestamp", "")).replace("Z", "+00:00")).replace(tzinfo=None)
                    if ts < limite_ack:
                        continue
                except Exception:
                    continue
            depuradas.append(a)
        alerts = depuradas[-100:]
        alerts.append({
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "mensaje": mensaje,
            "ack": False
        })
        ALERTS_FILE.write_text(json.dumps(alerts, indent=2, ensure_ascii=False), encoding="utf-8")
    finally:
        _unlock_pool()

def _notificar_switch(pool_nombre, modelo_viejo, modelo_nuevo, usadas, limite):
    """Notifica cuando hay switch de modelo."""
    msg = (f"⚠️ *SWITCH DE MODELO — {pool_nombre.upper()}*\n\n"
           f"Modelo agotado: `{modelo_viejo}`\n"
           f"Llamadas usadas: {usadas}/{limite} ({int(usadas/limite*100)}%)\n"
           f"Nuevo modelo activo: `{modelo_nuevo}`\n"
           f"Hora: {datetime.now().strftime('%H:%M')}")
    _escribir_alerta_pool(msg, "switch_modelo")
    print(f"  [pool] {pool_nombre}: {modelo_viejo} → {modelo_nuevo} ({usadas}/{limite} usadas)")

# ─── INTERFAZ PÚBLICA ─────────────────────────────────────────────────────────
def get_modelo_flash():
    """
    Devuelve el modelo Flash activo.
    Si el activo está al límite, hace switch al siguiente.
    """
    estado = _leer_estado()
    pool = estado["flash"]
    activo = pool["activo"]
    config = FLASH_CONFIG.get(activo, {})
    usadas = pool.get(activo, {}).get("usadas", 0)
    switch_en = config.get("switch_en", 1275)

    if usadas >= switch_en:
        # Buscar el siguiente disponible
        idx_actual = FLASH_ORDER.index(activo)
        for siguiente in FLASH_ORDER[idx_actual + 1:]:
            usadas_sig = pool.get(siguiente, {}).get("usadas", 0)
            config_sig = FLASH_CONFIG.get(siguiente, {})
            if usadas_sig < config_sig.get("switch_en", 1275):
                _notificar_switch("flash", activo, siguiente, usadas, config.get("limite", 1500))
                pool["activo"] = siguiente
                estado["flash"]["ultimo_switch"] = {
                    "timestamp": datetime.now().isoformat(),
                    "de": activo,
                    "a": siguiente,
                    "motivo": "cuota_85pct"
                }
                _guardar_estado(estado)
                return siguiente
        # Todos agotados — usar el último (Vertex AI)
        return FLASH_ORDER[-1]

    return activo

def get_modelo_pro():
    """
    Devuelve el modelo Pro activo para el cerebro-monitor.
    Si el activo está al límite, hace switch al siguiente.
    """
    estado = _leer_estado()
    pool = estado["pro"]
    activo = pool["activo"]
    config = PRO_CONFIG.get(activo, {})
    usadas = pool.get(activo, {}).get("usadas", 0)
    switch_en = config.get("switch_en", 42)

    if usadas >= switch_en:
        idx_actual = PRO_ORDER.index(activo)
        for siguiente in PRO_ORDER[idx_actual + 1:]:
            usadas_sig = pool.get(siguiente, {}).get("usadas", 0)
            config_sig = PRO_CONFIG.get(siguiente, {})
            if usadas_sig < config_sig.get("switch_en", 42):
                _notificar_switch("pro", activo, siguiente, usadas, config.get("limite", 50))
                pool["activo"] = siguiente
                estado["pro"]["ultimo_switch"] = {
                    "timestamp": datetime.now().isoformat(),
                    "de": activo,
                    "a": siguiente,
                    "motivo": "cuota_85pct"
                }
                _guardar_estado(estado)
                return siguiente
        # Ambos Pro agotados — usar Flash como cerebro de respaldo
        print("  [pool] ADVERTENCIA: modelos Pro agotados, usando Flash como cerebro")
        return get_modelo_flash()

    return activo

def registrar_uso_flash():
    """Llama esto DESPUÉS de cada llamada exitosa al pool Flash."""
    estado = _leer_estado()
    activo = estado["flash"]["activo"]
    if activo not in estado["flash"]:
        estado["flash"][activo] = {"usadas": 0}
    estado["flash"][activo]["usadas"] = estado["flash"][activo].get("usadas", 0) + 1
    _guardar_estado(estado)

def registrar_uso_pro():
    """Llama esto DESPUÉS de cada llamada exitosa al pool Pro."""
    estado = _leer_estado()
    activo = estado["pro"]["activo"]
    if activo not in estado["pro"]:
        estado["pro"][activo] = {"usadas": 0}
    estado["pro"][activo]["usadas"] = estado["pro"][activo].get("usadas", 0) + 1
    _guardar_estado(estado)

def get_api_key():
    """Devuelve la API key de Google AI Studio."""
    keys = _cargar_keys()
    return keys.get("google_ai_studio", "")

def get_estado_resumen():
    """Devuelve resumen del estado del pool para mostrar en logs/Telegram."""
    estado = _leer_estado()
    flash = estado["flash"]
    pro = estado["pro"]
    activo_f = flash["activo"]
    activo_p = pro["activo"]
    usadas_f = flash.get(activo_f, {}).get("usadas", 0)
    usadas_p = pro.get(activo_p, {}).get("usadas", 0)
    limite_f = FLASH_CONFIG.get(activo_f, {}).get("limite", 1500)
    limite_p = PRO_CONFIG.get(activo_p, {}).get("limite", 50)
    return (f"Pool Flash: {activo_f} ({usadas_f}/{limite_f}) | "
            f"Pool Pro: {activo_p} ({usadas_p}/{limite_p})")

if __name__ == "__main__":
    print("Estado actual del pool:")
    print(get_estado_resumen())
    print(f"Modelo Flash activo: {get_modelo_flash()}")
    print(f"Modelo Pro activo:   {get_modelo_pro()}")
    print(f"API key cargada:     {'OK' if get_api_key() else 'FALTA'}")
