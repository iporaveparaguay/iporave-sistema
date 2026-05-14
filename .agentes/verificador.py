"""
VERIFICADOR DEL SISTEMA — Iporave Connect
Chequea que la API y el frontend esten operativos.
Reporta al pizarron el resultado.

Uso: python verificador.py
"""

import json
import urllib.request
import urllib.error
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PIZARRON_URL = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
FRONTEND_URL = "https://iporave-sistema.vercel.app"
API_BASE     = "https://iporave-api.iporaveparaguay.workers.dev"

ENDPOINTS = [
    # (nombre, url, expected_status, requiere_auth)
    ("Frontend principal",     FRONTEND_URL,                       200, False),
    ("API pizarron GET",       f"{PIZARRON_URL}",                  200, False),
    ("API catalog-public",     f"{API_BASE}/api/catalog-public",   200, False),
    # Los siguientes devuelven 401 sin JWT — eso confirma Worker vivo
    ("API get-users",          f"{API_BASE}/api/get-users",        401, True),
    ("API config",             f"{API_BASE}/api/config",           401, True),
    ("API dispositivos-pend.", f"{API_BASE}/api/dispositivos-pendientes", 401, True),
]

def verificar_endpoint(nombre, url, expected_status, requiere_auth=False):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Verificador-Iporave/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.getcode()
            ok = (status == expected_status)
            return ok, status, None
    except urllib.error.HTTPError as e:
        # Endpoints con auth: 401/403/404 significa que el Worker esta vivo
        if requiere_auth and e.code in (401, 403, 404):
            return True, e.code, "Worker OK (requiere JWT)"
        if e.code in (401, 403):
            return True, e.code, "OK (requiere token)"
        return False, e.code, str(e)
    except Exception as e:
        return False, 0, str(e)

def reportar(estado, resumen):
    body = json.dumps({
        "agente": "Verificador-Sistema",
        "tarea": "health-check",
        "archivos": "-",
        "estado": estado,
        "resumen": resumen
    }).encode()
    try:
        req = urllib.request.Request(
            PIZARRON_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "IporaveAgent/1.0"
            },
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [pizarron] Error: {e}")

def main():
    print("\n" + "="*55)
    print("  VERIFICADOR IPORAVE CONNECT")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

    resultados = []
    errores = []

    for nombre, url, expected, *rest in ENDPOINTS:
        requiere_auth = rest[0] if rest else False
        ok, status, msg = verificar_endpoint(nombre, url, expected, requiere_auth)
        icono = "OK" if ok else "FALLO"
        print(f"  [{icono}] {nombre}: HTTP {status}" + (f" — {msg}" if msg else ""))
        resultados.append(f"{nombre}: {'OK' if ok else 'FALLO'} (HTTP {status})")
        if not ok:
            errores.append(f"{nombre} HTTP {status}")

    print("="*55)

    if errores:
        resumen = f"FALLOS detectados: {', '.join(errores)}. {'; '.join(resultados)}"
        estado = "Error"
        print(f"  ESTADO: SISTEMA CON PROBLEMAS")
    else:
        resumen = f"Todos los endpoints OK. {'; '.join(resultados)}"
        estado = "OK"
        print(f"  ESTADO: SISTEMA OPERATIVO")

    reportar(estado, resumen)
    print(f"  Reportado al pizarron: {estado}")
    print("="*55 + "\n")
    return len(errores) == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
