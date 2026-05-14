"""
LOCK UTIL — Iporãve Connect
Utilidad compartida para evitar que dos orquestadores escriban
ORQUESTADOR.md o el mismo archivo al mismo tiempo.

Uso:
    from lock_util import adquirir_lock, liberar_lock, archivo_en_uso, marcar_en_uso, liberar_archivo

    # Lock para ORQUESTADOR.md
    adquirir_lock()
    try:
        # ... modificar ORQUESTADOR.md ...
    finally:
        liberar_lock()

    # Lock para un archivo de código
    if not archivo_en_uso("index.html"):
        marcar_en_uso("index.html", "Orquestador-Features")
        try:
            # ... correr Aider ...
        finally:
            liberar_archivo("index.html")
    else:
        print("  index.html en uso por otro agente — saltando")
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime

LOCK_DIR   = Path(__file__).parent / "locks"
ORQ_LOCK   = LOCK_DIR / "orquestador_md.lock"
FILES_LOCK = LOCK_DIR / "archivos_en_uso.json"

LOCK_DIR.mkdir(exist_ok=True)

# ─── LOCK PARA ORQUESTADOR.md ─────────────────────────────────────────────────

def adquirir_lock(timeout_seg=120, agente="desconocido"):
    """
    Adquiere el lock exclusivo para ORQUESTADOR.md.
    Espera hasta timeout_seg si ya está tomado.
    Timeout aumentado a 120s porque Aider + git pueden tardar 30-60s.
    Retorna True si se adquirió, False si se agotó el tiempo.
    """
    inicio = time.time()
    while time.time() - inicio < timeout_seg:
        try:
            if not ORQ_LOCK.exists():
                ORQ_LOCK.write_text(json.dumps({
                    "agente": agente,
                    "desde": datetime.now().isoformat()
                }), encoding="utf-8")
                print(f"  [lock] Adquirido por {agente}")
                return True
            else:
                # Verificar si el lock es viejo (>180s = proceso muerto)
                try:
                    data = json.loads(ORQ_LOCK.read_text(encoding="utf-8"))
                    desde = datetime.fromisoformat(data.get("desde", "2000-01-01"))
                    edad = (datetime.now() - desde).total_seconds()
                    if edad > 180:
                        print(f"  [lock] Lock viejo ({edad:.0f}s) de {data.get('agente','?')} — limpiando")
                        ORQ_LOCK.unlink()
                        continue
                except:
                    ORQ_LOCK.unlink()
                    continue
        except:
            pass
        time.sleep(0.5)
    print(f"  [lock] TIMEOUT ({timeout_seg}s) esperando lock — {agente} no pudo adquirir")
    return False  # timeout

def liberar_lock():
    """Libera el lock de ORQUESTADOR.md."""
    try:
        if ORQ_LOCK.exists():
            ORQ_LOCK.unlink()
    except:
        pass

# ─── LOCK PARA ARCHIVOS DE CÓDIGO ─────────────────────────────────────────────

def _leer_archivos_en_uso():
    try:
        if FILES_LOCK.exists():
            return json.loads(FILES_LOCK.read_text(encoding="utf-8"))
    except:
        pass
    return {}

def _guardar_archivos_en_uso(data):
    FILES_LOCK.write_text(json.dumps(data, indent=2), encoding="utf-8")

def archivo_en_uso(nombre_archivo):
    """
    Verifica si un archivo está siendo editado por otro agente.
    nombre_archivo: solo el nombre, ej. "index.html" o "catalog.html"
    Retorna (True, nombre_agente) o (False, None)
    """
    data = _leer_archivos_en_uso()
    nombre = Path(nombre_archivo).name
    if nombre in data:
        info = data[nombre]
        # Verificar que no sea un lock viejo (>10 min = proceso muerto)
        try:
            desde = datetime.fromisoformat(info.get("desde", "2000-01-01"))
            if (datetime.now() - desde).total_seconds() > 600:
                # Lock viejo — limpiar
                del data[nombre]
                _guardar_archivos_en_uso(data)
                return False, None
        except:
            pass
        return True, info.get("agente", "desconocido")
    return False, None

def marcar_en_uso(nombre_archivo, agente):
    """
    Marca un archivo como en uso por este agente.
    Retorna True si se adquirió el lock, False si ya estaba tomado.
    """
    # Adquirir lock del json primero
    adquirir_lock(timeout_seg=5, agente=agente)
    try:
        data = _leer_archivos_en_uso()
        nombre = Path(nombre_archivo).name
        en_uso, otro = archivo_en_uso(nombre_archivo)
        if en_uso:
            return False
        data[nombre] = {
            "agente": agente,
            "desde": datetime.now().isoformat(),
            "ruta_completa": str(nombre_archivo)
        }
        _guardar_archivos_en_uso(data)
        return True
    finally:
        liberar_lock()

def liberar_archivo(nombre_archivo):
    """Libera el lock de un archivo de código."""
    adquirir_lock(timeout_seg=5)
    try:
        data = _leer_archivos_en_uso()
        nombre = Path(nombre_archivo).name
        if nombre in data:
            del data[nombre]
        _guardar_archivos_en_uso(data)
    finally:
        liberar_lock()

def listar_en_uso():
    """Retorna dict de todos los archivos actualmente en uso."""
    return _leer_archivos_en_uso()
