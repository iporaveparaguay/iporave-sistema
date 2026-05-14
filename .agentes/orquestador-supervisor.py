"""
SUPERVISOR — Iporãve Connect
Monitorea los 5 orquestadores cada 2 minutos.
- Si un orquestador lleva +15 min sin reportar → lo reinicia solo
- Si después de 3 reinicios sigue fallando → escribe alerta crítica y para de intentar
- Detecta PARADA_CRITICA.txt → escribe alerta, no reinicia nada
- Circuit breaker en pizarrón: 3 fallos seguidos → pausa 5 min
- Detecta tareas [!] bloqueadas → avisa UNA SOLA VEZ (anti-spam)
- Lee comandos STOP/RESTART del pizarrón
- NOTIFICACIONES: alerts.json local (sin Telegram)

Uso: python orquestador-supervisor.py
"""

import json, os, subprocess, sys, time, urllib.request, ssl
from pathlib import Path
from datetime import datetime, timezone

ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PIZARRON_URL     = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
ORQUESTADOR_MD   = Path(__file__).parent / "ORQUESTADOR.md"
PARADA_CRITICA   = Path(__file__).parent / "PARADA_CRITICA.txt"
ALERTS_FILE      = Path(__file__).parent / "alerts.json"
FRONTEND_DIR     = r"C:\Users\USUARIO\iporave-sistema"
INTERVALO_SEG    = 120
MAX_INACTIVO_MIN = 15
MAX_REINICIOS    = 3

# Circuit breaker pizarrón
_pizarron_fallos  = 0
PIZARRON_MAX_FALLOS = 3
PIZARRON_PAUSA_SEG  = 300  # 5 min de pausa cuando falla repetido

ORQUESTADORES = [
    {"nombre": "Orquestador-Features",  "script": ".agentes/orquestador-features.py"},
    {"nombre": "Orquestador-Catalog",   "script": ".agentes/orquestador-catalog.py"},
    {"nombre": "Orquestador-Worker",    "script": ".agentes/orquestador-worker.py"},
    {"nombre": "Orquestador-Paginas",   "script": ".agentes/orquestador-paginas.py"},
    {"nombre": "Orquestador-Principal", "script": ".agentes/orquestador.py"},
    # Codex-Solucionador REMOVIDO (2026-05-14): script roto que el supervisor reanimaba sin parar.
    # Si se arregla codex-solucionador.py, volver a agregarlo aquí.
]

# ─── LOCK FILE (evitar 2 supervisores corriendo en paralelo) ──────────────────
LOCK_FILE = Path(__file__).parent / ".supervisor.lock"

def _pid_vivo(pid):
    """True si el PID está vivo en Windows. False si no existe o no se puede verificar."""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode(errors="replace")
        return str(pid) in out
    except Exception:
        return False

def adquirir_lock():
    """Crea .supervisor.lock con el PID actual. Aborta si ya hay otro supervisor vivo."""
    if LOCK_FILE.exists():
        try:
            otro_pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            if _pid_vivo(otro_pid) and otro_pid != os.getpid():
                print(f"  ⛔ Ya hay un supervisor corriendo (PID {otro_pid}). Abortando.")
                escribir_alerta(
                    f"Intento de lanzar segundo supervisor — ya corre PID {otro_pid}. "
                    f"Abortado para evitar procesos duplicados.",
                    nivel="warning"
                )
                return False
            else:
                print(f"  [Supervisor] Lock huérfano (PID {otro_pid} muerto). Liberando.")
        except Exception:
            print(f"  [Supervisor] Lock corrupto. Sobrescribiendo.")
    try:
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        print(f"  [Supervisor] Lock adquirido (PID {os.getpid()})")
        return True
    except Exception as e:
        print(f"  [Supervisor] No se pudo escribir lock: {e}")
        return True  # no bloquear por error de escritura

def liberar_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            print(f"  [Supervisor] Lock liberado")
    except Exception:
        pass

import atexit
atexit.register(liberar_lock)

estado_agentes = {
    orq["nombre"]: {"proc": None, "reinicios": 0, "abandonado": False}
    for orq in ORQUESTADORES
}

_tareas_bloqueadas_ya_avisadas = set()
_agentes_detenidos = set()

# ─── ALERTAS (reemplaza Telegram) ─────────────────────────────────────────────

def escribir_alerta(texto, nivel="info"):
    """Escribe alerta a alerts.json. Sin Telegram."""
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
            "mensaje": texto
        })
        alertas = alertas[-100:]  # máximo 100 alertas
        ALERTS_FILE.write_text(json.dumps(alertas, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [ALERTA-{nivel.upper()}] {texto[:120]}")
    except Exception as e:
        print(f"  [ALERTA] No se pudo escribir en alerts.json: {e}")

# ─── PIZARRON ─────────────────────────────────────────────────────────────────

def leer_pizarron():
    global _pizarron_fallos
    try:
        req = urllib.request.Request(PIZARRON_URL, headers={
            "Accept": "application/json",
            "User-Agent": "IporaveAgent/1.0"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            _pizarron_fallos = 0
            return data.get("registros", []) if isinstance(data, dict) else data
    except Exception as e:
        _pizarron_fallos += 1
        print(f"  [pizarron] Error al leer ({_pizarron_fallos}/{PIZARRON_MAX_FALLOS}): {e}")
        if _pizarron_fallos >= PIZARRON_MAX_FALLOS:
            escribir_alerta(
                f"Pizarrón no responde después de {_pizarron_fallos} intentos. "
                f"Agentes en standby local por {PIZARRON_PAUSA_SEG//60} min.",
                nivel="critico"
            )
            print(f"  [pizarron] PAUSA {PIZARRON_PAUSA_SEG}s por fallos repetidos")
            time.sleep(PIZARRON_PAUSA_SEG)
            _pizarron_fallos = 0
        return []

def reportar(tarea, estado, resumen):
    body = json.dumps({
        "agente": "Supervisor",
        "tarea":  tarea,
        "archivos": "-",
        "estado": estado,
        "resumen": resumen
    }).encode()
    try:
        req = urllib.request.Request(PIZARRON_URL, data=body,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "IporaveAgent/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

# ─── CONTROL DE PROCESOS ──────────────────────────────────────────────────────

def esta_vivo(nombre):
    proc = estado_agentes[nombre]["proc"]
    return proc is not None and proc.poll() is None

def iniciar_orquestador(orq):
    nombre = orq["nombre"]
    if nombre in _agentes_detenidos:
        print(f"  [Supervisor] {nombre} está detenido por comando — no reiniciar")
        return False
    script = orq["script"].replace("/", os.sep)
    ruta   = os.path.join(FRONTEND_DIR, script)
    if not Path(ruta).exists():
        print(f"  [Supervisor] Script no encontrado: {ruta} — saltando")
        return False
    try:
        proc = subprocess.Popen(
            [sys.executable, ruta],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        estado_agentes[nombre]["proc"] = proc
        print(f"  [Supervisor] Iniciado {nombre} PID {proc.pid}")
        return True
    except Exception as e:
        print(f"  [Supervisor] Error iniciando {nombre}: {e}")
        escribir_alerta(f"No se pudo iniciar {nombre}: {e}", nivel="error")
        return False

def detener_orquestador(nombre):
    info = estado_agentes.get(nombre)
    if not info:
        return
    if info["proc"]:
        try:
            info["proc"].terminate()
            info["proc"].wait(timeout=5)
        except:
            try: info["proc"].kill()
            except: pass
        info["proc"] = None
    _agentes_detenidos.add(nombre)
    reportar(f"stop-{nombre.lower()}", "Detenido",
             f"{nombre} detenido por comando")
    print(f"  [Supervisor] {nombre} detenido")

def reiniciar_orquestador(orq, motivo):
    nombre = orq["nombre"]
    info   = estado_agentes[nombre]

    if info["abandonado"] or nombre in _agentes_detenidos:
        return

    info["reinicios"] += 1
    print(f"  [Supervisor] Reiniciando {nombre} (intento {info['reinicios']}/{MAX_REINICIOS}) — {motivo}")

    if info["proc"]:
        try:
            info["proc"].terminate()
            info["proc"].wait(timeout=5)
        except:
            try: info["proc"].kill()
            except: pass
        info["proc"] = None

    time.sleep(3)
    ok = iniciar_orquestador(orq)

    if ok:
        reportar(f"reinicio-{nombre.lower()}", "Reiniciado",
                 f"{nombre} reiniciado (intento {info['reinicios']}/{MAX_REINICIOS}). Motivo: {motivo}")
        if info["reinicios"] == 1:
            escribir_alerta(
                f"Reinicio automático: {nombre} — {motivo} "
                f"(intento {info['reinicios']}/{MAX_REINICIOS})",
                nivel="warning"
            )
    else:
        reportar(f"error-inicio-{nombre.lower()}", "ALERTA",
                 f"No se pudo reiniciar {nombre}. Revisar manualmente.")

    if info["reinicios"] >= MAX_REINICIOS:
        info["abandonado"] = True
        msg = (f"{nombre} falló {MAX_REINICIOS} veces seguidas. Motivo: {motivo}. "
               f"Revisar manualmente en .agentes/")
        reportar(f"abandonado-{nombre.lower()}", "ALERTA-CRITICA", msg)
        escribir_alerta(msg, nivel="critico")
        print(f"  [Supervisor] ALERTA-CRITICA: {nombre} abandonado tras {MAX_REINICIOS} reinicios")

# ─── VERIFICAR PARADA CRÍTICA ─────────────────────────────────────────────────

_parada_critica_ya_avisada = False

def verificar_parada_critica():
    global _parada_critica_ya_avisada
    if PARADA_CRITICA.exists():
        if not _parada_critica_ya_avisada:
            motivo = PARADA_CRITICA.read_text(encoding="utf-8")[:300]
            print(f"\n  ⛔ PARADA CRÍTICA ACTIVA: {motivo[:80]}")
            escribir_alerta(f"PARADA CRÍTICA activa: {motivo[:200]}", nivel="critico")
            _parada_critica_ya_avisada = True
        return True
    else:
        _parada_critica_ya_avisada = False
        return False

# ─── COMANDOS DEL PIZARRÓN ────────────────────────────────────────────────────

def verificar_comandos_supervisor(registros):
    for reg in reversed(registros[-20:]):
        if reg.get("agente") != "COMANDO-SUPERVISOR":
            continue
        if reg.get("estado") != "Pendiente":
            continue
        cmd  = reg.get("tarea", "")
        data = reg.get("resumen", "")
        if cmd == "STOP-AGENTE":
            nombre = data.strip()
            if nombre not in _agentes_detenidos:
                print(f"  [Supervisor] Comando STOP para {nombre}")
                detener_orquestador(nombre)
        elif cmd == "RESTART-AGENTE":
            nombre = data.strip()
            if nombre in _agentes_detenidos:
                _agentes_detenidos.discard(nombre)
                info = estado_agentes.get(nombre)
                if info:
                    info["abandonado"] = False
                    info["reinicios"]  = 0
                orq = next((o for o in ORQUESTADORES if o["nombre"] == nombre), None)
                if orq:
                    iniciar_orquestador(orq)
                    print(f"  [Supervisor] Restart manual: {nombre}")

# ─── VERIFICACIONES ───────────────────────────────────────────────────────────

def minutos_desde_ultimo_reporte(nombre, registros):
    ahora = datetime.now(timezone.utc)
    for reg in reversed(registros):
        if reg.get("agente", "") == nombre:
            try:
                dt = datetime.fromisoformat(reg["created_at"].replace("Z", "+00:00"))
                return (ahora - dt).total_seconds() / 60
            except:
                pass
    return None

def verificar_orquestadores(registros):
    for orq in ORQUESTADORES:
        nombre = orq["nombre"]
        info   = estado_agentes[nombre]

        if info["abandonado"]:
            print(f"  {nombre}: ABANDONADO — esperando revisión manual")
            continue

        if nombre in _agentes_detenidos:
            print(f"  {nombre}: DETENIDO por comando")
            continue

        proceso_vivo = esta_vivo(nombre)
        mins = minutos_desde_ultimo_reporte(nombre, registros)

        if not proceso_vivo:
            reiniciar_orquestador(orq, "proceso terminado inesperadamente")
        elif mins is not None and mins > MAX_INACTIVO_MIN:
            reiniciar_orquestador(orq, f"inactivo {mins:.0f} min sin reportar")
        else:
            if info["reinicios"] > 0:
                info["reinicios"] = 0
                print(f"  {nombre}: recuperado ✅")
            if mins is not None:
                print(f"  {nombre}: OK — último reporte hace {mins:.0f} min")
            else:
                print(f"  {nombre}: corriendo — sin reportes aún (recién iniciado)")

def verificar_tareas_bloqueadas(registros):
    if not ORQUESTADOR_MD.exists():
        return
    try:
        lineas = ORQUESTADOR_MD.read_text(encoding="utf-8").splitlines()
        bloqueadas_ahora = set()
        for linea in lineas:
            if "- [!]" in linea and "**" in linea:
                nombre = linea.split("**")[1].strip()
                bloqueadas_ahora.add(nombre)

        nuevas = bloqueadas_ahora - _tareas_bloqueadas_ya_avisadas
        if nuevas:
            lista = ", ".join(sorted(nuevas)[:5])
            msg = f"{len(nuevas)} tarea(s) bloqueadas: {lista}"
            reportar("tareas-bloqueadas", "ALERTA", msg)
            escribir_alerta(f"Tareas bloqueadas requieren revisión: {lista}", nivel="warning")
            _tareas_bloqueadas_ya_avisadas.update(nuevas)
            print(f"  [Supervisor] Nuevas bloqueadas: {lista}")

        resueltas = _tareas_bloqueadas_ya_avisadas - bloqueadas_ahora
        if resueltas:
            _tareas_bloqueadas_ya_avisadas.difference_update(resueltas)
            print(f"  [Supervisor] Tareas desbloqueadas: {resueltas}")
    except:
        pass

# ─── CICLO PRINCIPAL ──────────────────────────────────────────────────────────

def ciclo():
    print(f"\n[Supervisor] {datetime.now().strftime('%H:%M:%S')} — verificando {len(ORQUESTADORES)} agentes")

    if verificar_parada_critica():
        return

    registros = leer_pizarron()
    verificar_comandos_supervisor(registros)
    verificar_orquestadores(registros)
    verificar_tareas_bloqueadas(registros)

def main():
    print("=" * 55)
    print("  SUPERVISOR Iporave — reinicia y alerta")
    print(f"  Timeout: {MAX_INACTIVO_MIN}min | Max reinicios: {MAX_REINICIOS}")
    print(f"  Notificaciones: alerts.json (sin Telegram)")
    print("=" * 55)

    # Lock anti-duplicado: abortar si ya hay otro supervisor corriendo
    if not adquirir_lock():
        return

    if verificar_parada_critica():
        print("  PARADA_CRITICA activa: no se lanza ningún orquestador.")
        return

    try:
        val = subprocess.run(
            ["node", "validate.js"], cwd=FRONTEND_DIR,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30
        )
        out = val.stdout or ""
        if val.returncode != 0 or "Todo OK" not in out:
            msg = "validate.js falló antes de iniciar agentes. No se lanza ningún orquestador."
            reportar("preflight-validate", "ALERTA-CRITICA", msg)
            escribir_alerta(msg, nivel="critico")
            print(f"  validate.js falló:\n{out[-300:]}")
            return
    except Exception as e:
        reportar("preflight-validate", "ALERTA",
                 "No se pudo ejecutar validate.js: " + str(e)[:120])
        print(f"  No se pudo ejecutar validate.js: {e}")
        return

    print("\n[Supervisor] Lanzando orquestadores...")
    for orq in ORQUESTADORES:
        iniciar_orquestador(orq)
        time.sleep(2)

    reportar("supervisor-inicio", "Activo",
             f"Supervisor activo. {len(ORQUESTADORES)} orquestadores lanzados. Sin Telegram.")
    escribir_alerta(f"Sistema iniciado. {len(ORQUESTADORES)} agentes lanzados.", nivel="info")
    print(f"\n  ✅ {len(ORQUESTADORES)} agentes lanzados. Monitoreando cada {INTERVALO_SEG//60} min.")

    while True:
        try:
            ciclo()
        except KeyboardInterrupt:
            print("\n[Supervisor] Detenido por usuario.")
            escribir_alerta("Supervisor detenido manualmente.", nivel="info")
            break
        except Exception as e:
            print(f"  [Supervisor] Error en ciclo: {e}")
            reportar("supervisor-error", "Error", str(e)[:150])
        time.sleep(INTERVALO_SEG)

if __name__ == "__main__":
    main()
