"""
ORQ BASE — Iporãve Connect
Funciones compartidas por los 5 orquestadores.

Incluye:
- Marcar tarea [~] en progreso, [x] completada, [!] bloqueada
- Registrar fallo con análisis Gemini + reintentos inteligentes
- git checkout antes de reintentar
- File lock para ORQUESTADOR.md
- Verificar parada crítica al arrancar
- Protocolo completo: falla → Gemini analiza → reintenta mejorado → escala → bloquea

Uso:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from orq_base import (
        marcar_en_progreso, marcar_completada, marcar_bloqueada,
        ejecutar_con_reintentos, verificar_parada_critica
    )
"""

import json, os, subprocess, sys, time
from pathlib import Path
from datetime import datetime

ORQUESTADOR_MD = Path(__file__).parent / "ORQUESTADOR.md"
FRONTEND_DIR   = r"C:\Users\USUARIO\iporave-sistema"

# ─── IMPORTAR UTILIDADES ──────────────────────────────────────────────────────

_BASE = Path(__file__).parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from lock_util import adquirir_lock, liberar_lock, marcar_en_uso, liberar_archivo

# ─── PARADA CRÍTICA ───────────────────────────────────────────────────────────

def verificar_parada_critica():
    """
    Si existe PARADA_CRITICA.txt, este agente no debe trabajar.
    Retorna True si hay parada crítica (el agente debe detenerse).
    """
    archivo = Path(__file__).parent / "PARADA_CRITICA.txt"
    if archivo.exists():
        print("\n  ⛔ PARADA CRÍTICA ACTIVA — esperando resolución manual")
        print(f"  Leer {archivo} para ver el motivo")
        print("  Cuando Claude Code lo resuelva, borrar ese archivo y reiniciar\n")
        return True
    return False

# ─── MODIFICAR ORQUESTADOR.md CON LOCK ───────────────────────────────────────

def marcar_en_progreso(nombre, agente="orquestador"):
    """Marca tarea como [~] en progreso con file lock."""
    _modificar_estado_tarea(nombre, "[ ]", "[~]", agente)

def marcar_completada(nombre, agente="orquestador"):
    """Marca tarea como [x] completada con file lock."""
    # Puede venir de [~] (en progreso) o de [ ] (pendiente)
    contenido = ORQUESTADOR_MD.read_text(encoding="utf-8") if ORQUESTADOR_MD.exists() else ""
    if f"[~] **{nombre}**" in contenido:
        _modificar_estado_tarea(nombre, "[~]", "[x]", agente)
    else:
        _modificar_estado_tarea(nombre, "[ ]", "[x]", agente)

def marcar_bloqueada(nombre, agente="orquestador"):
    """Marca tarea como [!] bloqueada con file lock."""
    contenido = ORQUESTADOR_MD.read_text(encoding="utf-8") if ORQUESTADOR_MD.exists() else ""
    if f"[~] **{nombre}**" in contenido:
        _modificar_estado_tarea(nombre, "[~]", "[!]", agente)
    else:
        _modificar_estado_tarea(nombre, "[ ]", "[!]", agente)

def _modificar_estado_tarea(nombre, desde, hasta, agente):
    if not ORQUESTADOR_MD.exists():
        return
    ok = adquirir_lock(timeout_seg=15, agente=agente)
    if not ok:
        print(f"  [base] No pude adquirir lock para marcar {nombre} — timeout")
        return
    try:
        contenido = ORQUESTADOR_MD.read_text(encoding="utf-8")
        nuevo = []
        for linea in contenido.splitlines():
            if f"**{nombre}**" in linea and desde in linea:
                linea = linea.replace(desde, hasta, 1)
            nuevo.append(linea)
        ORQUESTADOR_MD.write_text("\n".join(nuevo), encoding="utf-8")
        print(f"  [base] Tarea {nombre}: {desde} → {hasta}")
    finally:
        liberar_lock()

# ─── GIT CHECKOUT ANTES DE REINTENTAR ────────────────────────────────────────

def revertir_archivo(archivo_path):
    """
    Hace git checkout del archivo para dejar el estado limpio antes de reintentar.
    Evita que Aider trabaje sobre un archivo ya modificado a medias.
    """
    directorio = FRONTEND_DIR
    if "iporave-worker" in str(archivo_path):
        directorio = r"C:\Users\USUARIO\iporave-worker"
    try:
        nombre_relativo = Path(archivo_path).name
        result = subprocess.run(
            ["git", "checkout", "--", nombre_relativo],
            cwd=directorio, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print(f"  [base] git checkout OK — {nombre_relativo} revertido")
        else:
            # Intentar con ruta completa relativa
            ruta_rel = str(Path(archivo_path)).replace(str(directorio), "").lstrip("/\\")
            subprocess.run(
                ["git", "checkout", "--", ruta_rel],
                cwd=directorio, capture_output=True, text=True, timeout=15
            )
            print(f"  [base] git checkout (ruta relativa) — {ruta_rel}")
    except Exception as e:
        print(f"  [base] Error en git checkout: {e}")

# ─── PROTOCOLO DE FALLOS CON GEMINI ──────────────────────────────────────────

MAX_INTENTOS = 3

def ejecutar_con_reintentos(
    nombre_tarea,
    instruccion_original,
    archivo_path,
    fn_ejecutar,          # función que ejecuta Aider: fn(instruccion) → (exito, salida, modelo)
    fn_validar,           # función que valida: fn() → (ok, error_msg)
    agente,
    fn_reportar,          # función para reportar al pizarrón: fn(nombre, estado, resumen)
    fallos_por_tarea,     # dict global del orquestador
):
    """
    Ejecuta una tarea con hasta MAX_INTENTOS intentos inteligentes.

    Flujo:
    1. Ejecuta con instrucción original
    2. Si falla → Gemini analiza → genera instrucción mejorada → reintenta
    3. En intento 2 → Gemini Flash con más contexto
    4. En intento 3 → Gemini Pro (máxima potencia)
    5. Si los 3 intentos fallan → bloquea tarea + escala a Claude

    Retorna: "completada" | "bloqueada" | "parada_critica"
    """
    from gemini_resolver import (
        analizar_error, avisar_fallo_inicial, avisar_reintento,
        avisar_tarea_resuelta, avisar_tarea_abandonada,
        notificar_escalar_a_claude, parar_sistema_critico
    )

    instruccion = instruccion_original

    for intento in range(1, MAX_INTENTOS + 1):
        print(f"\n  [{agente}] Intento {intento}/{MAX_INTENTOS}: {nombre_tarea}")

        # Marcar en progreso en ORQUESTADOR.md (solo primer intento)
        if intento == 1:
            marcar_en_progreso(nombre_tarea, agente)

        # Adquirir lock de archivo
        if not marcar_en_uso(archivo_path, agente):
            en_uso_por = "otro agente"
            print(f"  [{agente}] {Path(archivo_path).name} en uso — esperando 30s...")
            time.sleep(30)
            if not marcar_en_uso(archivo_path, agente):
                print(f"  [{agente}] Sigue en uso — saltando tarea por ahora")
                marcar_en_progreso(nombre_tarea, agente)  # volver a [ ] sería marcar_pendiente
                _modificar_estado_tarea(nombre_tarea, "[~]", "[ ]", agente)
                return "postergada"

        try:
            exito, salida, modelo_usado = fn_ejecutar(instruccion)
        finally:
            liberar_archivo(archivo_path)

        # Verificar parada crítica por todos los modelos fallados
        if "TODOS LOS MODELOS FALLARON" in salida:
            parar_sistema_critico(agente, f"Todos los modelos fallaron en tarea {nombre_tarea}. {salida[:200]}")
            marcar_bloqueada(nombre_tarea, agente)
            return "parada_critica"

        if exito:
            # Validar
            val_ok, val_error = fn_validar()
            if val_ok:
                marcar_completada(nombre_tarea, agente)
                fn_reportar(nombre_tarea, "Finalizado",
                            f"[intento {intento}] [{modelo_usado}] Completado.")
                if intento > 1:
                    avisar_tarea_resuelta(nombre_tarea, intento, agente)
                print(f"  [{agente}] ✅ {nombre_tarea} completada (intento {intento})")
                fallos_por_tarea.pop(nombre_tarea, None)
                return "completada"
            else:
                salida = val_error or "validate.js fallo"
                exito = False

        # Falló — analizar con Gemini
        print(f"  [{agente}] Intento {intento} falló: {salida[:100]}")
        fn_reportar(nombre_tarea, f"Error-{intento}", salida[:200])

        usar_pro = (intento == MAX_INTENTOS)  # último intento → Gemini Pro
        print(f"  [{agente}] Analizando error con Gemini {'Pro' if usar_pro else 'Flash'}...")

        analisis = analizar_error(
            nombre_tarea, instruccion, salida, archivo_path,
            intento_num=intento, usar_pro=usar_pro
        )

        diagnostico    = analisis.get("diagnostico", "Error desconocido")
        causa_tecnica  = analisis.get("causa_tecnica", "")
        nueva          = analisis.get("nueva_instruccion", instruccion)
        solucionable   = analisis.get("solucionable", True)
        necesita_claude = analisis.get("necesita_claude", False)
        accion         = analisis.get("accion_sugerida", "Revisar manualmente")

        if intento == 1:
            avisar_fallo_inicial(nombre_tarea, diagnostico, intento, MAX_INTENTOS, agente)

        # Si Gemini dice que no es solucionable o necesita Claude → no reintentar más
        if not solucionable or necesita_claude:
            marcar_bloqueada(nombre_tarea, agente)
            avisar_tarea_abandonada(nombre_tarea, diagnostico, causa_tecnica,
                                    accion, agente, escalar_claude=necesita_claude)
            if necesita_claude:
                notificar_escalar_a_claude(nombre_tarea, instruccion_original,
                                           salida, archivo_path,
                                           diagnostico, causa_tecnica, agente)
            fallos_por_tarea[nombre_tarea] = MAX_INTENTOS
            return "bloqueada"

        # Revertir archivo antes de reintentar
        revertir_archivo(archivo_path)

        # Actualizar instrucción para el siguiente intento
        instruccion = nueva
        if intento < MAX_INTENTOS:
            avisar_reintento(nombre_tarea, intento + 1, MAX_INTENTOS, nueva, agente)
            print(f"  [{agente}] Nueva instrucción: {nueva[:120]}...")

    # Si llegó aquí, los 3 intentos fallaron
    marcar_bloqueada(nombre_tarea, agente)
    avisar_tarea_abandonada(nombre_tarea,
                            f"Falló {MAX_INTENTOS} veces sin poder resolverse",
                            "Máximo de intentos alcanzado",
                            "Revisar manualmente con Claude Code",
                            agente, escalar_claude=True)
    notificar_escalar_a_claude(nombre_tarea, instruccion_original,
                               salida, archivo_path,
                               "Máximo de intentos alcanzado", causa_tecnica, agente)
    fallos_por_tarea[nombre_tarea] = MAX_INTENTOS
    return "bloqueada"
