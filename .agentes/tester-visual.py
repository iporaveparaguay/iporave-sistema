"""
TESTER VISUAL — Iporãve Connect
================================
Navega el sistema con Playwright, toma screenshots de cada pantalla
y los analiza con Gemini Vision para detectar errores visuales.

Uso:
    python tester-visual.py --user admin@test.com --pass mipassword

Requisitos:
    pip install playwright google-generativeai
    playwright install chromium
"""

import argparse
import base64
import json
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from pathlib import Path

# ─── CARGAR API KEY Y MODELO DESDE JSON ──────────────────────────────────────

API_KEYS_PATH = Path(r"C:\Users\USUARIO\node-red-config\api-keys.json")
BROWSER_STATE_PATH = Path(__file__).parent / "playwright_state.json"

def cargar_config_gemini():
    if not API_KEYS_PATH.exists():
        print(f"[ERROR] No encontré api-keys.json en: {API_KEYS_PATH}")
        sys.exit(1)
    with open(API_KEYS_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    api_key = data.get("google_ai_studio")
    if not api_key:
        print("[ERROR] No encontré la clave 'google_ai_studio' en el JSON")
        sys.exit(1)
    modelo = data.get("google_ai_studio_modelos", {}).get("flash_principal", "gemini-1.5-flash")
    # Quitar sufijo -latest que causa 404 con el nuevo SDK google.genai
    if modelo.endswith("-latest"):
        modelo = modelo[: -len("-latest")]
    return api_key, modelo

# ─── CONFIGURACIÓN DE PANTALLAS ───────────────────────────────────────────────

BASE_URL = "https://iporave-sistema.vercel.app"

PANTALLAS = [
    {
        "id": "01-login",
        "nombre": "Pantalla de Login",
        "descripcion": "Formulario de inicio de sesión antes de loguear",
        "requiere_login": False,
        "prompt": (
            "Esta es la pantalla de login del sistema Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Se ven bien los campos de email y contraseña? "
            "2) ¿El botón de entrar es visible y claro? "
            "3) ¿Hay textos cortados o elementos superpuestos? "
            "4) ¿El diseño se ve profesional y responsivo? "
            "5) ¿Hay algún error visible o elemento roto? "
            "Respondé en español con un diagnóstico claro, mencionando problemas encontrados si los hay."
        ),
    },
    {
        "id": "02-dashboard",
        "nombre": "Dashboard / Panel Principal",
        "descripcion": "Panel principal post-login del superadmin",
        "requiere_login": True,
        "url_extra": "/",
        "prompt": (
            "Esta es la pantalla del dashboard principal del sistema Iporãve Connect (panel superadmin). "
            "Analizá visualmente: "
            "1) ¿Se muestran estadísticas o tarjetas de resumen correctamente? "
            "2) ¿La navegación lateral o superior es visible y funcional visualmente? "
            "3) ¿Hay textos cortados, datos vacíos que no deberían estarlo, o errores de carga? "
            "4) ¿Los gráficos o tablas (si los hay) se renderizan bien? "
            "5) ¿Hay algún error de JavaScript visible (mensajes de error en pantalla)? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "03-usuarios",
        "nombre": "Panel de Usuarios",
        "descripcion": "Lista de usuarios del sistema",
        "requiere_login": True,
        "url_extra": "/usuarios",
        "prompt": (
            "Esta es la pantalla de gestión de usuarios del sistema Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Se muestra una tabla o lista de usuarios correctamente? "
            "2) ¿Los botones de acción (editar, eliminar, ver) son visibles? "
            "3) ¿Hay paginación visible si hay muchos usuarios? "
            "4) ¿Los roles de usuario se muestran claramente? "
            "5) ¿Hay errores de carga, tablas vacías inesperadas, o elementos rotos? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "04-crear-usuario",
        "nombre": "Formulario Crear Usuario",
        "descripcion": "Formulario para agregar un nuevo usuario",
        "requiere_login": True,
        "url_extra": "/usuarios/nuevo",
        "prompt": (
            "Esta es la pantalla del formulario para crear un nuevo usuario en Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Todos los campos del formulario son visibles y tienen etiquetas claras? "
            "2) ¿El selector de rol (superadmin, admin, vendedor, etc.) es visible? "
            "3) ¿Los campos de validación o campos requeridos están marcados visualmente? "
            "4) ¿El botón de guardar/crear es visible y destacado? "
            "5) ¿Hay elementos cortados, superpuestos o que no se ven bien en el formulario? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "05-catalogo",
        "nombre": "Panel Catálogo / Productos",
        "descripcion": "Lista de productos del catálogo",
        "requiere_login": True,
        "url_extra": "/catalogo",
        "prompt": (
            "Esta es la pantalla del catálogo de productos del sistema Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Los productos se muestran en tarjetas o tabla correctamente? "
            "2) ¿Las imágenes de productos cargan bien o hay imágenes rotas? "
            "3) ¿Los precios, nombres y categorías son legibles? "
            "4) ¿Hay filtros o buscador visible? "
            "5) ¿Hay errores de carga, elementos rotos o catálogo vacío inesperadamente? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "06-agregar-producto",
        "nombre": "Formulario Agregar Producto",
        "descripcion": "Formulario para agregar un nuevo producto",
        "requiere_login": True,
        "url_extra": "/catalogo/nuevo",
        "prompt": (
            "Esta es la pantalla del formulario para agregar un producto al catálogo de Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Los campos (nombre, precio, descripción, imagen, categoría) son visibles y bien organizados? "
            "2) ¿Hay un área para subir imagen o URL de imagen? "
            "3) ¿Los campos obligatorios están claramente marcados? "
            "4) ¿El botón de guardar/agregar es visible? "
            "5) ¿Hay elementos cortados, superpuestos o con mal diseño en el formulario? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "07-pedidos",
        "nombre": "Panel de Pedidos / Órdenes",
        "descripcion": "Lista y gestión de pedidos",
        "requiere_login": True,
        "url_extra": "/pedidos",
        "prompt": (
            "Esta es la pantalla de gestión de pedidos del sistema Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Los pedidos se muestran en tabla o lista correctamente con su estado? "
            "2) ¿Los estados de pedido (pendiente, en camino, entregado, etc.) son visibles con colores o badges? "
            "3) ¿Los botones de acción sobre pedidos son visibles? "
            "4) ¿Hay información de cliente, fecha y monto visible en cada pedido? "
            "5) ¿Hay errores de carga, tabla vacía inesperada o elementos rotos? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "08-perfil",
        "nombre": "Perfil del Usuario",
        "descripcion": "Pantalla de perfil del usuario logueado",
        "requiere_login": True,
        "url_extra": "/perfil",
        "prompt": (
            "Esta es la pantalla de perfil del usuario logueado en Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Los datos del usuario (nombre, email, rol, foto) se muestran correctamente? "
            "2) ¿Los campos editables son claramente distinguibles de los campos de solo lectura? "
            "3) ¿El botón de guardar cambios es visible? "
            "4) ¿Hay campos obligatorios marcados visualmente? "
            "5) ¿Hay elementos rotos, texto cortado o diseño desalineado? "
            "Respondé en español con diagnóstico detallado."
        ),
    },
    {
        "id": "09-mapa-tracking",
        "nombre": "Mapa / Tracking",
        "descripcion": "Panel de mapa o tracking de entregas",
        "requiere_login": True,
        "url_extra": "/mapa",
        "prompt": (
            "Esta es la pantalla del mapa/tracking del sistema Iporãve Connect. "
            "Analizá visualmente: "
            "1) ¿Se carga el mapa correctamente? (Leaflet o Mapbox) "
            "2) ¿Los marcadores o pins en el mapa son visibles? "
            "3) ¿Hay controles de zoom o capas visibles? "
            "4) ¿Si el mapa no cargó, hay un mensaje de error visible? "
            "5) ¿El panel lateral de información (si existe) se ve bien? "
            "NOTA: Si ves una pantalla '404 no encontrada' o similar, indicalo claramente. "
            "Respondé en español con diagnóstico detallado."
        ),
    },
]

# ─── ANÁLISIS CON GEMINI VISION ───────────────────────────────────────────────

def analizar_screenshot_con_gemini(model, screenshot_path: Path, prompt: str, nombre_pantalla: str) -> str:
    """Envía un screenshot a Gemini Vision y retorna el análisis."""
    try:
        from google.genai import types
        img_bytes = screenshot_path.read_bytes()

        response = model.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                f"Sos un tester de QA especializado en UI/UX. {prompt}"
            ]
        )

        return response.text.strip()

    except Exception as e:
        return f"[ERROR Gemini] No se pudo analizar la pantalla '{nombre_pantalla}': {e}"

# ─── SELECTORES HELPERS ───────────────────────────────────────────────────────

SELECTORES_EMAIL = [
    'input[type="email"]',
    '#loginEmail',
    'input[placeholder*="email" i]',
    'input[name="email"]',
    'input[placeholder*="correo" i]',
]

SELECTORES_PASSWORD = [
    'input[type="password"]',
    '#loginPassword',
    'input[name="password"]',
    'input[placeholder*="contrase" i]',
]

SELECTORES_BOTON_LOGIN = [
    'button:has-text("Ingresar al sistema")',
    'button:has-text("Ingresar")',
    'button:has-text("Entrar")',
    'button[type="submit"]',
    '.btn-login',
    'form button',
]

def encontrar_selector(page, selectores: list):
    """Prueba una lista de selectores y retorna el primero que encuentre."""
    for sel in selectores:
        try:
            elemento = page.locator(sel).first
            if elemento.count() > 0:
                return sel
        except Exception:
            continue
    return None

# ─── MAPEO DE url_extra → nombre de sección en nav() del SPA ─────────────────
#
# El SPA usa sessionStorage para guardar la sesión. Navegar con page.goto() a
# cualquier ruta interna borra el sessionStorage y pierde la sesión.
# En su lugar, después del login se usa page.evaluate("nav('seccion')") para
# que el SPA cambie de pantalla internamente sin recargar la página.
#
# Secciones disponibles confirmadas en PAGES de index.html:
#   dashboard, usuarios, catalogo, orders (= pedidos), mapa,
#   config, mensajes, zonas, boletas, balance, liquidacion,
#   estadisticas, analitica_admin, analitica_vend, analitica_drop,
#   analitica_prov, suministros, pagos_prov, recaudacion, cierre,
#   cupo, setup, entregas, delivery, neworder, etc.
#
# Para "perfil" no hay PAGES.perfil — se abre con openPerfilUsuario() (modal).
# Para sub-rutas como /usuarios/nuevo y /catalogo/nuevo no hay PAGES propio;
# se navega a la sección padre y se hace clic en el botón correspondiente.

URL_EXTRA_A_NAV = {
    "/":               ("nav", "dashboard"),
    "/usuarios":       ("nav", "usuarios"),
    "/usuarios/nuevo": ("click", "button:has-text('Nuevo usuario'), button:has-text('Agregar'), button:has-text('+ Usuario'), button:has-text('Crear usuario')"),
    "/catalogo":       ("nav", "catalogo"),
    "/catalogo/nuevo": ("click", "button:has-text('Agregar producto'), button:has-text('+ Producto'), button:has-text('Nuevo producto')"),
    "/pedidos":        ("nav", "orders"),
    "/perfil":         ("eval", "openPerfilUsuario()"),
    "/mapa":           ("nav", "mapa"),
}

# ─── NAVEGACIÓN POR PANTALLAS ─────────────────────────────────────────────────

def navegar_pantalla(page, pantalla: dict, screenshots_dir: Path) -> Path:
    """
    Navega a una pantalla usando navegación interna del SPA (nav()) para
    preservar la sesión guardada en sessionStorage.
    Retorna la ruta del screenshot.
    """
    screenshot_path = screenshots_dir / f"{pantalla['id']}.png"

    try:
        url_extra = pantalla.get("url_extra", "")
        if url_extra:
            accion = URL_EXTRA_A_NAV.get(url_extra)
            if accion:
                tipo, valor = accion
                if tipo == "nav":
                    # Navegación interna SPA — NO recarga la página, preserva sessionStorage
                    print(f"  → Navegación SPA interna: nav('{valor}')")
                    page.evaluate(f"nav('{valor}')")
                    page.wait_for_timeout(1500)  # esperar que el SPA renderice
                elif tipo == "eval":
                    # Llamada a función JS (p.ej. modal de perfil)
                    print(f"  → Ejecutando JS: {valor}")
                    # Primero volver al dashboard para estar en contexto limpio
                    page.evaluate("nav('dashboard')")
                    page.wait_for_timeout(800)
                    page.evaluate(valor)
                    page.wait_for_timeout(1500)
                elif tipo == "click":
                    # Navegar a sección padre y hacer clic en botón de acción
                    selectores_extra = valor
                    # Determinar sección padre según url_extra
                    if "usuarios" in url_extra:
                        page.evaluate("nav('usuarios')")
                    elif "catalogo" in url_extra:
                        page.evaluate("nav('catalogo')")
                    page.wait_for_timeout(1200)
                    # Intentar clic en el botón de crear/agregar
                    boton_encontrado = False
                    for sel in selectores_extra.split(", "):
                        sel = sel.strip()
                        try:
                            elem = page.locator(sel).first
                            if elem.count() > 0 and elem.is_visible():
                                elem.click()
                                boton_encontrado = True
                                print(f"  → Botón clickeado: {sel}")
                                break
                        except Exception:
                            continue
                    if not boton_encontrado:
                        print(f"  [WARN] No encontré botón para {url_extra} — screenshot de sección padre")
                    page.wait_for_timeout(1500)
            else:
                # url_extra no está en el mapa — fallback: navegar a dashboard
                print(f"  [WARN] url_extra '{url_extra}' no tiene mapeo SPA definido — mostrando dashboard")
                page.evaluate("nav('dashboard')")
                page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  [WARN] Error al navegar a pantalla '{pantalla['nombre']}': {e}")
        # De todas formas tomamos screenshot del estado actual

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  → Screenshot guardado: {screenshot_path.name}")
    except Exception as e:
        print(f"  [ERROR] No se pudo tomar screenshot: {e}")
        # Crear imagen placeholder vacía si falla
        screenshot_path.write_bytes(b"")

    return screenshot_path

# ─── FLUJO PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tester visual automático del sistema Iporãve Connect"
    )
    parser.add_argument("--user", required=True, help="Email del usuario para login")
    parser.add_argument("--pass", dest="password", required=True, help="Contraseña del usuario")
    args = parser.parse_args()

    EMAIL = args.user
    PASSWORD = args.password

    print("\n" + "="*60)
    print("  TESTER VISUAL — Iporãve Connect")
    print(f"  Usuario: {EMAIL}")
    print(f"  Sistema: {BASE_URL}")
    print("="*60 + "\n")

    # ── Preparar directorios ──
    base_dir = Path(__file__).parent
    screenshots_dir = base_dir / "test-screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    print(f"[INFO] Screenshots en: {screenshots_dir}\n")

    # ── Cargar Gemini ──
    print("[INFO] Cargando configuración de Gemini...")
    api_key, modelo_id = cargar_config_gemini()
    print(f"[INFO] Modelo Gemini: {modelo_id}")

    try:
        from google import genai
    except ImportError:
        print("[ERROR] google-genai no está instalado.")
        print("  Ejecutá: pip install google-genai")
        sys.exit(1)

    global modelo_id_global
    modelo_id_global = modelo_id
    model = genai.Client(api_key=api_key)
    print("[OK] Gemini configurado correctamente\n")

    # ── Iniciar Playwright ──
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] playwright no está instalado.")
        print("  Ejecutá: pip install playwright && playwright install chromium")
        sys.exit(1)

    resultados = []
    login_exitoso = False

    with sync_playwright() as pw:
        print("[INFO] Abriendo navegador Chromium (modo visible)...")
        browser = pw.chromium.launch(headless=True, slow_mo=300)
        context_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "es-PY"}
        if BROWSER_STATE_PATH.exists():
            context_opts["storage_state"] = str(BROWSER_STATE_PATH)
            print("[INFO] Cargando estado de browser guardado (dispositivo ya autorizado)")
        context = browser.new_context(**context_opts)
        page = context.new_page()

        # ═══════════════════════════════════════════════════════════
        # PANTALLA 1: LOGIN (antes de loguear)
        # ═══════════════════════════════════════════════════════════
        pantalla_login = PANTALLAS[0]
        print(f"\n[PASO 1] {pantalla_login['nombre']}")
        print(f"  Descripción: {pantalla_login['descripcion']}")

        try:
            print(f"  → Abriendo {BASE_URL}...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=20000)
            time.sleep(1)
        except Exception as e:
            print(f"  [WARN] Error al cargar página inicial: {e}")

        # Screenshot del login antes de llenar
        screenshot_login = screenshots_dir / f"{pantalla_login['id']}.png"
        try:
            page.screenshot(path=str(screenshot_login), full_page=True)
            print(f"  → Screenshot guardado: {screenshot_login.name}")
        except Exception as e:
            print(f"  [ERROR] Screenshot fallido: {e}")

        # Analizar con Gemini
        print("  → Analizando con Gemini Vision...")
        analisis_login = analizar_screenshot_con_gemini(
            model, screenshot_login, pantalla_login["prompt"], pantalla_login["nombre"]
        )
        print(f"  [GEMINI] {analisis_login[:200]}...")

        resultados.append({
            "pantalla": pantalla_login["nombre"],
            "id": pantalla_login["id"],
            "screenshot": str(screenshot_login),
            "analisis": analisis_login,
            "estado": "ok",
        })

        # ═══════════════════════════════════════════════════════════
        # REALIZAR LOGIN
        # ═══════════════════════════════════════════════════════════
        print("\n[LOGIN] Intentando iniciar sesión...")

        try:
            # Buscar campo email
            sel_email = encontrar_selector(page, SELECTORES_EMAIL)
            if sel_email:
                page.fill(sel_email, EMAIL)
                print(f"  → Email ingresado (selector: {sel_email})")
            else:
                print("  [WARN] No encontré campo de email — probando llenar de todas formas")
                page.locator(SELECTORES_EMAIL[0]).fill(EMAIL)

            # Buscar campo password
            sel_pass = encontrar_selector(page, SELECTORES_PASSWORD)
            if sel_pass:
                page.fill(sel_pass, PASSWORD)
                print(f"  → Contraseña ingresada (selector: {sel_pass})")
            else:
                print("  [WARN] No encontré campo de contraseña — probando de todas formas")
                page.locator(SELECTORES_PASSWORD[0]).fill(PASSWORD)

            # Buscar botón de submit
            boton_encontrado = False
            for sel_btn in SELECTORES_BOTON_LOGIN:
                try:
                    elemento = page.locator(sel_btn).first
                    if elemento.count() > 0:
                        elemento.click()
                        print(f"  → Botón clickeado (selector: {sel_btn})")
                        boton_encontrado = True
                        break
                except Exception:
                    continue

            if not boton_encontrado:
                print("  [WARN] No encontré botón de login — intentando primer botón visible en form")
                try:
                    page.locator('form button').first.click()
                    boton_encontrado = True
                    print("  → Clic en form button (fallback)")
                except Exception:
                    print("  [WARN] Fallback también falló, sin acción de submit")

            # Esperar carga post-click
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            time.sleep(2)

            # Verificar si el login fue exitoso chequeando URL y ausencia de campo email
            url_actual = page.url
            print(f"  → URL actual: {url_actual}")

            campo_email_visible = False
            try:
                campo_email_visible = page.locator('input[type="email"]').first.is_visible()
            except Exception:
                pass

            if "login" not in url_actual.lower() and not campo_email_visible:
                login_exitoso = True
                print("  [OK] Login aparentemente exitoso")
                context.storage_state(path=str(BROWSER_STATE_PATH))
                print(f"[INFO] Estado de browser guardado en: {BROWSER_STATE_PATH.name}")
            else:
                # Esperar un poco más por si hay redirección lenta
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                url_actual = page.url
                campo_email_visible = False
                try:
                    campo_email_visible = page.locator('input[type="email"]').first.is_visible()
                except Exception:
                    pass
                if "login" not in url_actual.lower() and not campo_email_visible:
                    login_exitoso = True
                    print("  [OK] Login exitoso (después de espera adicional)")
                    context.storage_state(path=str(BROWSER_STATE_PATH))
                    print(f"[INFO] Estado de browser guardado en: {BROWSER_STATE_PATH.name}")
                else:
                    print(f"  [WARN] Puede que el login haya fallado. URL: {url_actual}")
                    if campo_email_visible:
                        print("\n" + "="*60)
                        print("  ACCIÓN REQUERIDA: Aprobar dispositivo nuevo")
                        print("  1) Abrí el panel admin en: https://iporave-sistema.vercel.app")
                        print("  2) Entrá a la sección Dispositivos o Usuarios > Dispositivos")
                        print("  3) Aprobá el dispositivo pendiente para " + EMAIL)
                        print("  4) Volvé a correr este script")
                        print("  Si ya aprobaste, borrá el archivo playwright_state.json y reintentá")
                        print("="*60 + "\n")
                    login_exitoso = True  # intentamos continuar de todas formas

        except Exception as e:
            print(f"  [ERROR] Error durante el login: {e}")
            # Tomar screenshot del error
            error_path = screenshots_dir / "login-error.png"
            try:
                page.screenshot(path=str(error_path))
            except Exception:
                pass
            print("  [WARN] Continuando con las otras pantallas de todas formas...")
            login_exitoso = True  # intentamos continuar

        # ═══════════════════════════════════════════════════════════
        # PANTALLAS POST-LOGIN
        # ═══════════════════════════════════════════════════════════
        for i, pantalla in enumerate(PANTALLAS[1:], start=2):
            print(f"\n[PASO {i}] {pantalla['nombre']}")
            print(f"  Descripción: {pantalla['descripcion']}")

            screenshot_path = navegar_pantalla(page, pantalla, screenshots_dir)

            # Analizar solo si el screenshot tiene contenido
            if screenshot_path.exists() and screenshot_path.stat().st_size > 100:
                print("  → Analizando con Gemini Vision...")
                analisis = analizar_screenshot_con_gemini(
                    model, screenshot_path, pantalla["prompt"], pantalla["nombre"]
                )
                print(f"  [GEMINI] {analisis[:200]}...")
                estado = "ok"
            else:
                analisis = "[ERROR] El screenshot está vacío o no se pudo tomar"
                estado = "error"
                print(f"  [ERROR] Screenshot inválido para {pantalla['nombre']}")

            resultados.append({
                "pantalla": pantalla["nombre"],
                "id": pantalla["id"],
                "screenshot": str(screenshot_path),
                "analisis": analisis,
                "estado": estado,
            })

            # Pequeña pausa entre pantallas para no saturar la API
            time.sleep(1)

        # Cerrar navegador
        print("\n[INFO] Cerrando navegador...")
        browser.close()

    # ═══════════════════════════════════════════════════════════════
    # RESUMEN FINAL
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  RESUMEN DE ANÁLISIS VISUAL")
    print("="*60)

    for r in resultados:
        print(f"\n{'─'*50}")
        print(f"  Pantalla: {r['pantalla']}")
        print(f"  Estado:   {r['estado'].upper()}")
        print(f"  Screenshot: {Path(r['screenshot']).name}")
        print(f"\n  Análisis Gemini:")
        # Imprimir con indentación
        for linea in r["analisis"].splitlines():
            print(f"    {linea}")

    print("\n" + "="*60)

    # ─── GUARDAR REPORTE JSON ──────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    reporte_path = screenshots_dir / f"reporte-{timestamp}.json"

    reporte = {
        "timestamp": datetime.now().isoformat(),
        "sistema": BASE_URL,
        "usuario_testeado": EMAIL,
        "modelo_gemini": modelo_id,
        "total_pantallas": len(resultados),
        "pantallas_ok": sum(1 for r in resultados if r["estado"] == "ok"),
        "pantallas_error": sum(1 for r in resultados if r["estado"] == "error"),
        "resultados": resultados,
    }

    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Reporte guardado en: {reporte_path}")
    print(f"[OK] Screenshots en: {screenshots_dir}")
    print(f"\n  Total pantallas analizadas: {len(resultados)}")
    print(f"  OK: {reporte['pantallas_ok']} | Errores: {reporte['pantallas_error']}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
