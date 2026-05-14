#!/usr/bin/env python3
"""
crear-datos-prueba.py
Script para crear datos de prueba ficticios en el sistema Iporave.
Llama a la API del worker y a Supabase REST directamente.

Uso:
    python crear-datos-prueba.py --user superadmin@email.com --pass mipassword
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

WORKER_URL  = "https://iporave-api.iporaveparaguay.workers.dev"
SUPABASE_URL = "https://hrpnqbmknmgdaaokjelb.supabase.co"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers HTTP
# ─────────────────────────────────────────────────────────────────────────────

def _request(method, url, body=None, headers=None):
    """Realiza una request HTTP y devuelve (status_code, dict_respuesta)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "IporaveAgent/1.0")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"_raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw}
    except Exception as exc:
        return 0, {"error": str(exc)}


def post(url, body, token=None, extra_headers=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    return _request("POST", url, body, headers)


def get(url, token=None, extra_headers=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    return _request("GET", url, headers=headers)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Login
# ─────────────────────────────────────────────────────────────────────────────

def login(email, password):
    print(f"\n[LOGIN] Autenticando como {email} ...")
    status, resp = post(f"{WORKER_URL}/api/login", {"email": email, "password": password})
    if status == 200 and resp.get("ok"):
        token = resp.get("token")
        user  = resp.get("user", {})
        print(f"  OK — rol: {user.get('rol')} | id interno: {user.get('id')}")
        return token, user
    print(f"  ERROR {status}: {resp.get('error', resp)}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Obtener anon key de Supabase (necesaria para REST directo)
# ─────────────────────────────────────────────────────────────────────────────

def get_supabase_anon_key(token):
    print("\n[CONFIG] Obteniendo anon key de Supabase ...")
    status, resp = get(f"{WORKER_URL}/api/config", token=token)
    if status == 200 and resp.get("ok"):
        key = resp.get("supabaseKey")
        if key:
            print("  OK — anon key obtenida")
            return key
    # Si el rol no es admin/superadmin el endpoint puede responder 403 sin la key
    print(f"  AVISO {status}: no se pudo obtener la anon key ({resp.get('error', '')})")
    print("  Las operaciones directas a Supabase se omitirán.")
    return None


def get_max_id_supabase(tabla, anon_key, token):
    """
    Consulta el ID máximo actual en una tabla de Supabase.
    Devuelve el valor entero del max id, o 0 si la tabla está vacía / hay error.
    """
    url = f"{SUPABASE_URL}/rest/v1/{tabla}?select=id&order=id.desc&limit=1"
    headers = {
        "apikey":  anon_key,
        "Accept":  "application/json",
    }
    status, resp = get(url, token=token, extra_headers=headers)
    if status == 200 and isinstance(resp, list) and len(resp) > 0:
        return int(resp[0].get("id", 0))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Crear usuarios de prueba
# ─────────────────────────────────────────────────────────────────────────────

USUARIOS_PRUEBA = [
    # ── Vendedores ────────────────────────────────────────────────────
    {
        "email":    "vendedor1@iporave.test",
        "nombre":   "Ana Vendedora",
        "rol":      "vendedor",
        "whatsapp": "0981000001",
        "ciudad":   "Asunción",
        "barrio":   "Villa Morra",
        "departamento": "Central",
        "pais":     "Paraguay",
    },
    {
        "email":    "vendedor2@iporave.test",
        "nombre":   "Carlos Vendedor",
        "rol":      "vendedor",
        "whatsapp": "0981000002",
        "ciudad":   "Asunción",
        "barrio":   "San Lorenzo",
        "departamento": "Central",
        "pais":     "Paraguay",
    },
    # ── Proveedor ─────────────────────────────────────────────────────
    {
        "email":    "proveedor1@iporave.test",
        "nombre":   "Distribuidora Central",
        "rol":      "proveedor",
        "whatsapp": "0981000003",
        "ciudad":   "Asunción",
        "barrio":   "Mercado 4",
        "departamento": "Central",
        "pais":     "Paraguay",
    },
    # ── Deliveries ────────────────────────────────────────────────────
    {
        "email":    "delivery1@iporave.test",
        "nombre":   "Juan Delivery",
        "rol":      "delivery",
        "whatsapp": "0981000004",
        "ciudad":   "Asunción",
        "barrio":   "Herrera",
        "departamento": "Central",
        "pais":     "Paraguay",
        "vehiculo": "Moto",
        "patente":  "AAA 001",
    },
    {
        "email":    "delivery2@iporave.test",
        "nombre":   "Luis Delivery",
        "rol":      "delivery",
        "whatsapp": "0981000005",
        "ciudad":   "Asunción",
        "barrio":   "Manorá",
        "departamento": "Central",
        "pais":     "Paraguay",
        "vehiculo": "Moto",
        "patente":  "BBB 002",
    },
    # ── Dropshipper ───────────────────────────────────────────────────
    {
        "email":    "drop1@iporave.test",
        "nombre":   "Marta Drop",
        "rol":      "dropshipper",
        "whatsapp": "0981000006",
        "ciudad":   "Asunción",
        "barrio":   "Centro",
        "departamento": "Central",
        "pais":     "Paraguay",
    },
    # ── Admin ────────────────────────────────────────────────────────
    {
        "email":    "admin1@iporave.test",
        "nombre":   "Admin Prueba",
        "rol":      "admin",
        "whatsapp": "0981000007",
        "ciudad":   "Asunción",
        "barrio":   "Centro",
        "departamento": "Central",
        "pais":     "Paraguay",
    },
]
PASS_PRUEBA = "Test1234!"


def crear_usuarios(token, anon_key):
    print("\n[USUARIOS] Creando usuarios de prueba ...")
    # Fix 1: id es entero serial — consultar max actual para evitar ERROR 500
    max_id = 0
    if anon_key:
        max_id = get_max_id_supabase("usuarios", anon_key, token)
        print(f"  Max id actual en 'usuarios': {max_id}")
    else:
        print("  AVISO: sin anon key no se puede consultar max id. Se omite el campo id.")

    creados = 0
    for i, u in enumerate(USUARIOS_PRUEBA):
        body = {
            "email":    u["email"],
            "nombre":   u["nombre"],
            "rol":      u["rol"],
            "password": PASS_PRUEBA,
        }
        # Campos opcionales de perfil extendido
        for campo in ("whatsapp", "ciudad", "barrio", "departamento", "pais", "vehiculo", "patente"):
            if campo in u:
                body[campo] = u[campo]
        # Solo incluir id si pudimos calcular el siguiente entero
        if anon_key:
            body["id"] = max_id + i + 1

        status, resp = post(f"{WORKER_URL}/api/save-user", body, token=token)
        if resp.get("ok"):
            print(f"  OK — {u['email']} ({u['rol']})")
            creados += 1
        else:
            err = resp.get("error", resp.get("_raw", str(resp)))
            print(f"  ERROR {status} — {u['email']}: {err}")
    return creados


# ─────────────────────────────────────────────────────────────────────────────
# 4. Agregar productos al catálogo via Supabase REST
# ─────────────────────────────────────────────────────────────────────────────

PRODUCTOS_PRUEBA = [
    {
        "nombre":        "Yerba Mate 1kg",
        "presentaciones": [{"nombre": "1kg", "precio": 15000}],
        "categoria":     "Alimentación",
        "stock":         50,
        "publicar_tienda": True,
    },
    {
        "nombre":        "Aceite Cañuelas 900ml",
        "presentaciones": [{"nombre": "900ml", "precio": 8500}],
        "categoria":     "Alimentación",
        "stock":         30,
        "publicar_tienda": True,
    },
    {
        "nombre":        "Azúcar 1kg",
        "presentaciones": [{"nombre": "1kg", "precio": 4500}],
        "categoria":     "Alimentación",
        "stock":         100,
        "publicar_tienda": True,
    },
    # Productos extendidos (TAREA_DATOS_PRUEBA_EXTENDIDOS)
    {
        "nombre":        "Fideos Tallarin 500g",
        "presentaciones": [{"nombre": "500g", "precio": 3200}],
        "categoria":     "Alimentación",
        "stock":         80,
        "publicar_tienda": True,
    },
    {
        "nombre":        "Leche Entera 1L",
        "presentaciones": [{"nombre": "1L", "precio": 5800}],
        "categoria":     "Alimentación",
        "stock":         60,
        "publicar_tienda": True,
    },
    {
        "nombre":        "Arroz Largo Fino 1kg",
        "presentaciones": [{"nombre": "1kg", "precio": 6500}],
        "categoria":     "Alimentación",
        "stock":         75,
        "publicar_tienda": True,
    },
]


def crear_productos_supabase(token, anon_key, owner_user_id):
    """
    Inserta productos en la tabla 'catalogo' via Supabase REST.
    Requiere el JWT del usuario (token) y la anon key como apikey.
    """
    print("\n[CATÁLOGO] Creando productos de prueba via Supabase REST ...")
    if not anon_key:
        print("  OMITIDO — no se pudo obtener la anon key de Supabase.")
        return 0

    # Fix 2: consultar max id para evitar ERROR 400 "null value in column 'id'"
    max_id = get_max_id_supabase("catalogo", anon_key, token)
    print(f"  Max id actual en 'catalogo': {max_id}")

    url = f"{SUPABASE_URL}/rest/v1/catalogo"
    headers = {
        "apikey":      anon_key,
        "Prefer":      "return=minimal",
    }
    creados = 0
    for i, p in enumerate(PRODUCTOS_PRUEBA):
        body = dict(p)
        body["id"]           = max_id + i + 1
        body["owner_user_id"] = owner_user_id
        # Supabase acepta JSON nativo para columnas JSONB
        if isinstance(body.get("presentaciones"), list):
            body["presentaciones"] = body["presentaciones"]

        status, resp = post(url, body, token=token, extra_headers=headers)
        # Supabase REST devuelve 201 en inserción exitosa con Prefer: return=minimal
        if status in (200, 201):
            print(f"  OK — {p['nombre']}")
            creados += 1
        else:
            err = resp.get("message") or resp.get("error") or resp.get("_raw", str(resp))
            print(f"  ERROR {status} — {p['nombre']}: {err}")
    return creados


# ─────────────────────────────────────────────────────────────────────────────
# 5. Crear pedidos via Supabase REST
#    Primero intenta /api/orders (worker), luego /api/pedidos,
#    y finalmente Supabase REST directamente.
# ─────────────────────────────────────────────────────────────────────────────

# Número de contacto para pruebas (real, del dueño del sistema)
TEL_PRUEBA = "982547222"  # +595 982 547 222 → sin prefijo +595 (el sistema lo agrega)

PEDIDOS_PRUEBA = [
    # ── Pedidos base ──────────────────────────────────────────────────
    {
        "cliente":   "María García",
        "telefono":  TEL_PRUEBA,
        "direccion": "Avda. España 1234, Villa Morra, Asunción",
        "notas":     "Tocar timbre. Edificio Olimpia, 3er piso.",
        "producto":  "Yerba Mate 1kg",
        "qty":       2,
        "precio":    15000,
        "estado":    "pendiente",
        "prioridad": False,
    },
    {
        "cliente":   "Juan López",
        "telefono":  TEL_PRUEBA,
        "direccion": "Calle Palma 567, Centro, Asunción",
        "notas":     "Casa color verde. Frente a la panadería.",
        "producto":  "Aceite Cañuelas 900ml",
        "qty":       3,
        "precio":    8500,
        "estado":    "En camino",
        "prioridad": False,
    },
    {
        "cliente":   "Ana Rodríguez",
        "telefono":  TEL_PRUEBA,
        "direccion": "Calle Brasil 890, San Lorenzo, Paraguay",
        "notas":     "Entregar a vecina si no hay nadie.",
        "producto":  "Azúcar 1kg",
        "qty":       5,
        "precio":    4500,
        "estado":    "Entregado",
        "prioridad": False,
    },
    # ── Pedidos extendidos — distintos formatos de dirección ──────────
    {
        "cliente":   "Carlos Benítez",
        "telefono":  TEL_PRUEBA,
        "direccion": "Mercado 4, Asunción, Paraguay",
        "notas":     "Cliente en puesto 42, sector frutas.",
        "producto":  "Fideos Tallarin 500g",
        "qty":       10,
        "precio":    3200,
        "estado":    "pendiente",
        "prioridad": True,   # ⚡ prioridad para probar animación del pin
    },
    {
        "cliente":   "Laura Gómez",
        "telefono":  TEL_PRUEBA,
        "direccion": "-25.2867, -57.6470",   # coordenadas GPS exactas (Asunción centro)
        "notas":     "GPS confirmado. Depto 4B, intercomunicador 42.",
        "producto":  "Leche Entera 1L",
        "qty":       4,
        "precio":    5800,
        "estado":    "Despachado",
        "prioridad": False,
    },
    {
        "cliente":   "Miguel Torres",
        "telefono":  TEL_PRUEBA,
        "direccion": "Av. Mcal. López 1234, Barrio Manorá, Asunción",
        "notas":     "Llamar 10 min antes de llegar.",
        "producto":  "Arroz Largo Fino 1kg",
        "qty":       2,
        "precio":    6500,
        "estado":    "pendiente",
        "prioridad": False,
    },
    {
        "cliente":   "Rosa Ferreira",
        "telefono":  TEL_PRUEBA,
        "direccion": "Av. Artigas 3650, Barrio Herrera, Asunción",
        "notas":     "Portón azul. Buscar a Doña Rosa.",
        "producto":  "Yerba Mate 1kg",
        "qty":       1,
        "precio":    15000,
        "estado":    "Cancelado",
        "prioridad": False,
    },
    # ── Pedido extra — para probar mapa con estado En Ruta ────────────
    {
        "cliente":   "Pedro Villalba",
        "telefono":  TEL_PRUEBA,
        "direccion": "Av. Eusebio Ayala 4521, Asunción",
        "notas":     "Segundo piso, oficina 8. Horario: 8am-6pm.",
        "producto":  "Aceite Cañuelas 900ml",
        "qty":       6,
        "precio":    8500,
        "estado":    "En Ruta",
        "prioridad": False,
    },
]


def _intentar_crear_pedido_worker(pedido_body, token, endpoint):
    """Intenta crear un pedido via un endpoint del worker. Devuelve True si OK."""
    url = f"{WORKER_URL}{endpoint}"
    status, resp = post(url, pedido_body, token=token)
    if status in (200, 201) and (resp.get("ok") or resp.get("id")):
        return True, resp
    return False, resp


def _crear_pedido_supabase(pedido_body, token, anon_key):
    """Inserta un pedido directamente en Supabase REST."""
    if not anon_key:
        return False, {"error": "anon key no disponible"}
    url = f"{SUPABASE_URL}/rest/v1/pedidos"
    headers = {
        "apikey": anon_key,
        "Prefer": "return=minimal",
    }
    status, resp = post(url, pedido_body, token=token, extra_headers=headers)
    if status in (200, 201):
        return True, resp
    return False, resp


def crear_pedidos(token, anon_key, vendedor_id):
    print("\n[PEDIDOS] Creando pedidos de prueba ...")
    # Fix 3a: consultar max id de pedidos para asignar ids enteros
    max_id = 0
    if anon_key:
        max_id = get_max_id_supabase("pedidos", anon_key, token)
        print(f"  Max id actual en 'pedidos': {max_id}")

    creados = 0
    for i, p in enumerate(PEDIDOS_PRUEBA):
        telefono = p.get("telefono", "")
        notas    = p.get("notas", f"Pedido de prueba — {p['producto']}")
        qty      = p.get("qty", 1)
        precio   = p.get("precio", 0)
        prioridad= p.get("prioridad", False)

        body_worker = {
            "cliente":   p["cliente"],
            "telefono":  telefono,
            "direccion": p["direccion"],
            "producto":  p["producto"],
            "estado":    p["estado"],
            "qty":       qty,
            "precio":    precio,
            "notas":     notas,
            "prioridad": prioridad,
        }
        body_supa = {
            "cliente":    p["cliente"],
            "telefono":   telefono,
            "direccion":  p["direccion"],
            "notas":      notas,
            "estado":     p["estado"],
            "vendedor_id": vendedor_id,
            "qty":        qty,
            "precio":     precio,
            "prioridad":  prioridad,
        }
        if anon_key:
            body_supa["id"] = max_id + i + 1

        ok = False
        # Intento 1: POST /api/orders
        ok, resp = _intentar_crear_pedido_worker(body_worker, token, "/api/orders")
        if ok:
            print(f"  OK (/api/orders) — {p['cliente']}")
            creados += 1
            continue

        # Intento 2: POST /api/pedidos
        ok, resp = _intentar_crear_pedido_worker(body_worker, token, "/api/pedidos")
        if ok:
            print(f"  OK (/api/pedidos) — {p['cliente']}")
            creados += 1
            continue

        # Intento 3: Supabase REST directo
        ok, resp = _crear_pedido_supabase(body_supa, token, anon_key)
        if ok:
            print(f"  OK (Supabase REST) — {p['cliente']}")
            creados += 1
            continue

        err = resp.get("message") or resp.get("error") or resp.get("_raw", str(resp))
        print(f"  ERROR — {p['cliente']}: {err}")

    return creados


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crea datos de prueba en el sistema Iporave."
    )
    parser.add_argument("--user", required=True, help="Email del superadmin")
    parser.add_argument("--pass", dest="password", required=True, help="Contraseña del superadmin")
    args = parser.parse_args()

    print("=" * 60)
    print("  IPORAVE — Generador de datos de prueba")
    print(f"  Worker:   {WORKER_URL}")
    print(f"  Supabase: {SUPABASE_URL}")
    print("=" * 60)

    # 1. Login
    token, user = login(args.user, args.password)

    # 2. Obtener anon key (solo funciona si el usuario es admin/superadmin)
    anon_key = get_supabase_anon_key(token)

    # ID interno del superadmin (para asignar como owner en catálogo y pedidos)
    owner_id = user.get("id")

    # 3. Crear usuarios
    usuarios_creados = crear_usuarios(token, anon_key)

    # 4. Crear productos en catálogo
    productos_creados = crear_productos_supabase(token, anon_key, owner_id)

    # 5. Crear pedidos
    pedidos_creados = crear_pedidos(token, anon_key, owner_id)

    # ── Resumen ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    print(f"  Usuarios creados:  {usuarios_creados} / {len(USUARIOS_PRUEBA)}")
    print(f"  Productos creados: {productos_creados} / {len(PRODUCTOS_PRUEBA)}")
    print(f"  Pedidos creados:   {pedidos_creados} / {len(PEDIDOS_PRUEBA)}")
    print("=" * 60)

    total_esperado = len(USUARIOS_PRUEBA) + len(PRODUCTOS_PRUEBA) + len(PEDIDOS_PRUEBA)
    total_creados  = usuarios_creados + productos_creados + pedidos_creados

    if total_creados == total_esperado:
        print("  Todo OK — todos los datos de prueba fueron creados exitosamente.")
    else:
        fallidos = total_esperado - total_creados
        print(f"  {fallidos} operación(es) fallaron. Revisar los mensajes de ERROR arriba.")

    print()


if __name__ == "__main__":
    main()
