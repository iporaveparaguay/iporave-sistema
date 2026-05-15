#!/usr/bin/env python3
"""
crear-pedidos-prueba-usuarios.py
Crea pedidos de prueba asignados a los usuarios de test ya existentes:
  - vendedor REBECA   (vendedor@iporave.com)
  - delivery ISIDRO   (delivery@iporave.com)
  - dropshipper RAUL  (dropshipper@iporave.com)
  - proveedor MANUEL  (proveedor@iporave.com)
  - cliente ARTURO    (cliente@iporave.com)
  - admin LUIS        (admin@iporave.com)

Uso:
    python crear-pedidos-prueba-usuarios.py
"""

import json
import sys
import urllib.request
import urllib.error

WORKER_URL  = "https://iporave-api.iporaveparaguay.workers.dev"
SUPABASE_URL = "https://hrpnqbmknmgdaaokjelb.supabase.co"

ADMIN_EMAIL = "admin@iporave.com"
ADMIN_PASS  = "ivan12345"

USERS_TEST = {
    "vendedor":    {"email": "vendedor@iporave.com",    "pass": "ivan12345"},
    "delivery":    {"email": "delivery@iporave.com",    "pass": "ivan12345"},
    "dropshipper": {"email": "dropshipper@iporave.com", "pass": "ivan12345"},
    "proveedor":   {"email": "proveedor@iporave.com",   "pass": "ivan12345"},
    "cliente":     {"email": "cliente@iporave.com",     "pass": "ivan12345"},
    "admin":       {"email": "admin@iporave.com",       "pass": "ivan12345"},
}

TEL_PRUEBA = "982547222"


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

def _request(method, url, body=None, headers=None):
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
# 1. Login admin → token + anon key
# ─────────────────────────────────────────────────────────────────────────────

def login(email, password):
    print(f"\n[LOGIN] {email} ...")
    status, resp = post(f"{WORKER_URL}/api/login", {"email": email, "password": password})
    if status == 200 and resp.get("ok"):
        token = resp.get("token")
        user  = resp.get("user", {})
        print(f"  OK — rol={user.get('rol')} id={user.get('id')}")
        return token, user
    print(f"  ERROR {status}: {resp.get('error', resp)}")
    return None, None


def get_anon_key(token):
    print("\n[CONFIG] Obteniendo anon key ...")
    status, resp = get(f"{WORKER_URL}/api/config", token=token)
    if status == 200 and resp.get("ok"):
        key = resp.get("supabaseKey")
        if key:
            print("  OK — anon key obtenida")
            return key
    print(f"  ERROR {status}: {resp.get('error', resp)}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Obtener IDs de usuarios desde Supabase
# ─────────────────────────────────────────────────────────────────────────────

def buscar_id_usuario(email, anon_key, token):
    """
    Consulta tabla usuarios por email, devuelve id interno (int) o None.
    """
    url = f"{SUPABASE_URL}/rest/v1/usuarios?select=id,email,nombre,rol&email=eq.{urllib.parse.quote(email)}"
    headers = {"apikey": anon_key}
    status, resp = get(url, token=token, extra_headers=headers)
    if status == 200 and isinstance(resp, list) and len(resp) > 0:
        return resp[0]
    return None


def get_max_id(tabla, anon_key, token):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}?select=id&order=id.desc&limit=1"
    headers = {"apikey": anon_key}
    status, resp = get(url, token=token, extra_headers=headers)
    if status == 200 and isinstance(resp, list) and len(resp) > 0:
        return int(resp[0].get("id", 0))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Definición de pedidos a crear
# ─────────────────────────────────────────────────────────────────────────────

import urllib.parse


def build_pedidos(ids):
    """
    Construye la lista de pedidos a crear, usando los IDs reales obtenidos.
    ids = {'vendedor': X, 'delivery': X, 'dropshipper': X, 'proveedor': X, 'cliente': X, 'admin': X}
    """
    vid = ids.get("vendedor")
    did = ids.get("delivery")
    drp = ids.get("dropshipper")
    pid = ids.get("proveedor")

    pedidos = []

    # ─────────────────────────────────────────────
    # 10 pedidos asignados a vendedor REBECA
    # ─────────────────────────────────────────────

    # 3 PENDIENTE
    pedidos.append({
        "cliente": "María García",
        "telefono": TEL_PRUEBA,
        "direccion": "Avda. España 1234, Villa Morra, Asunción",
        "notas": "Tocar timbre. Edificio Olimpia, 3er piso.",
        "producto": "Yerba Mate 1kg",
        "qty": 2, "precio": 15000, "costo": 9000,
        "estado": "Pendiente",
        "vendedor_id": vid,
        "_grupo": "vendedor_pendiente",
    })
    pedidos.append({
        "cliente": "Juan López",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Palma 567, Centro, Asunción",
        "notas": "Casa color verde frente a la panadería.",
        "producto": "Aceite Cañuelas 900ml",
        "qty": 3, "precio": 8500, "costo": 5500,
        "estado": "Pendiente",
        "vendedor_id": vid,
        "_grupo": "vendedor_pendiente",
    })
    pedidos.append({
        "cliente": "Carlos Benítez",
        "telefono": TEL_PRUEBA,
        "direccion": "Mercado 4, Asunción, Paraguay",
        "notas": "Cliente en puesto 42, sector frutas. URGENTE!",
        "producto": "Fideos Tallarin 500g",
        "qty": 10, "precio": 3200, "costo": 2000,
        "estado": "Pendiente",
        "vendedor_id": vid,
        "prioridad": True,
        "_grupo": "vendedor_pendiente",
    })

    # 2 DESPACHADO (asignados sólo a vendedor; aún sin delivery)
    pedidos.append({
        "cliente": "Laura Gómez",
        "telefono": TEL_PRUEBA,
        "direccion": "Av. Mcal. López 567, Manorá, Asunción",
        "notas": "Depto 4B, intercomunicador 42.",
        "producto": "Leche Entera 1L",
        "qty": 4, "precio": 5800, "costo": 3600,
        "estado": "Despachado",
        "vendedor_id": vid,
        "_grupo": "vendedor_despachado",
    })
    pedidos.append({
        "cliente": "Roberto Pérez",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Brasil 890, San Lorenzo",
        "notas": "Casa amarilla portón negro.",
        "producto": "Azúcar 1kg",
        "qty": 5, "precio": 4500, "costo": 2800,
        "estado": "Despachado",
        "vendedor_id": vid,
        "_grupo": "vendedor_despachado",
    })

    # 2 EN RUTA (delivery ISIDRO)
    pedidos.append({
        "cliente": "Miguel Torres",
        "telefono": TEL_PRUEBA,
        "direccion": "Av. Mcal. López 1234, Manorá, Asunción",
        "notas": "Llamar 10 min antes de llegar.",
        "producto": "Arroz Largo Fino 1kg",
        "qty": 2, "precio": 6500, "costo": 4200,
        "estado": "En Ruta",
        "vendedor_id": vid,
        "delivery_id": did,
        "_grupo": "vendedor_enruta",
    })
    pedidos.append({
        "cliente": "Lucía Aquino",
        "telefono": TEL_PRUEBA,
        "direccion": "Avda. Eusebio Ayala 4521, Asunción",
        "notas": "Edificio gris, depto 12.",
        "producto": "Aceite Cañuelas 900ml",
        "qty": 1, "precio": 8500, "costo": 5500,
        "estado": "En Ruta",
        "vendedor_id": vid,
        "delivery_id": did,
        "_grupo": "vendedor_enruta",
    })

    # 2 ENTREGADO (con foto + monto cobrado)
    pedidos.append({
        "cliente": "Pedro Villalba",
        "telefono": TEL_PRUEBA,
        "direccion": "Av. Eusebio Ayala 4521, Asunción",
        "notas": "Oficina 8, segundo piso. Horario 8am-6pm.",
        "producto": "Aceite Cañuelas 900ml",
        "qty": 6, "precio": 8500, "costo": 5500,
        "estado": "Entregado",
        "vendedor_id": vid,
        "delivery_id": did,
        "metodo_cobro": "Efectivo",
        "foto_entrega": True,
        "_grupo": "vendedor_entregado",
    })
    pedidos.append({
        "cliente": "Sofía Martínez",
        "telefono": TEL_PRUEBA,
        "direccion": "Av. Boggiani 2345, Asunción",
        "notas": "Recepcionista toma el pedido.",
        "producto": "Azúcar 1kg",
        "qty": 8, "precio": 4500, "costo": 2800,
        "estado": "Entregado",
        "vendedor_id": vid,
        "delivery_id": did,
        "metodo_cobro": "Transferencia",
        "foto_entrega": True,
        "_grupo": "vendedor_entregado",
    })

    # 1 CANCELADO
    pedidos.append({
        "cliente": "Rosa Ferreira",
        "telefono": TEL_PRUEBA,
        "direccion": "Av. Artigas 3650, Herrera, Asunción",
        "notas": "Portón azul. Cliente canceló por teléfono.",
        "producto": "Yerba Mate 1kg",
        "qty": 1, "precio": 15000, "costo": 9000,
        "estado": "Cancelado",
        "vendedor_id": vid,
        "_grupo": "vendedor_cancelado",
    })

    # ─────────────────────────────────────────────
    # 3 pedidos asignados a dropshipper RAUL (con comisión)
    # ─────────────────────────────────────────────
    pedidos.append({
        "cliente": "Andrea Núñez",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Estrella 234, Centro, Asunción",
        "notas": "Pedido Dropshipping — comisión 15%.",
        "producto": "Yerba Mate 1kg",
        "qty": 3, "precio": 15000, "costo": 9000,
        "comision": 6750,  # 15% × 45000
        "estado": "Pendiente",
        "vendedor_id": vid,
        "drop_id": drp,
        "_grupo": "drop_pendiente",
    })
    pedidos.append({
        "cliente": "Fernando Silva",
        "telefono": TEL_PRUEBA,
        "direccion": "Avda. Choferes del Chaco 1100, Asunción",
        "notas": "Pedido Dropshipping — entrega oficina.",
        "producto": "Aceite Cañuelas 900ml",
        "qty": 6, "precio": 8500, "costo": 5500,
        "comision": 5100,  # 10% × 51000
        "estado": "Despachado",
        "vendedor_id": vid,
        "drop_id": drp,
        "delivery_id": did,
        "_grupo": "drop_despachado",
    })
    pedidos.append({
        "cliente": "Patricia Caballero",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Quesada 890, Fernando de la Mora",
        "notas": "Dropshipping — pago en efectivo.",
        "producto": "Leche Entera 1L",
        "qty": 4, "precio": 5800, "costo": 3600,
        "comision": 2320,  # 10% × 23200
        "estado": "Entregado",
        "vendedor_id": vid,
        "drop_id": drp,
        "delivery_id": did,
        "metodo_cobro": "Efectivo",
        "foto_entrega": True,
        "_grupo": "drop_entregado",
    })

    # ─────────────────────────────────────────────
    # 3 pedidos asignados a proveedor MANUEL (estado Despachado)
    # ─────────────────────────────────────────────
    pedidos.append({
        "cliente": "Diego Acosta",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Coronel Romero 456, Lambaré",
        "notas": "Pedido del proveedor MANUEL.",
        "producto": "Yerba Mate 1kg",
        "qty": 5, "precio": 15000, "costo": 9000,
        "estado": "Despachado",
        "vendedor_id": vid,
        "proveedor_id": pid,
        "proveedor": "Distribuidora Manuel",
        "_grupo": "proveedor_despachado",
    })
    pedidos.append({
        "cliente": "Mariana López",
        "telefono": TEL_PRUEBA,
        "direccion": "Avda. Bernardino Caballero 789, San Lorenzo",
        "notas": "Stock proveedor MANUEL.",
        "producto": "Arroz Largo Fino 1kg",
        "qty": 10, "precio": 6500, "costo": 4200,
        "estado": "Despachado",
        "vendedor_id": vid,
        "proveedor_id": pid,
        "proveedor": "Distribuidora Manuel",
        "_grupo": "proveedor_despachado",
    })
    pedidos.append({
        "cliente": "Hugo Ramírez",
        "telefono": TEL_PRUEBA,
        "direccion": "Calle Cerro Corá 1200, Asunción",
        "notas": "Proveedor MANUEL despachó hoy.",
        "producto": "Fideos Tallarin 500g",
        "qty": 8, "precio": 3200, "costo": 2000,
        "estado": "Despachado",
        "vendedor_id": vid,
        "proveedor_id": pid,
        "proveedor": "Distribuidora Manuel",
        "_grupo": "proveedor_despachado",
    })

    return pedidos


# ─────────────────────────────────────────────────────────────────────────────
# 4. Insertar pedido en Supabase
# ─────────────────────────────────────────────────────────────────────────────

def insertar_pedido(pedido_body, anon_key, token):
    url = f"{SUPABASE_URL}/rest/v1/pedidos"
    headers = {
        "apikey": anon_key,
        "Prefer": "return=minimal",
    }
    status, resp = post(url, pedido_body, token=token, extra_headers=headers)
    return status, resp


# ─────────────────────────────────────────────────────────────────────────────
# 5. Verificación: cada usuario consulta sus pedidos
# ─────────────────────────────────────────────────────────────────────────────

def verificar_get_orders(email, password):
    token, user = login(email, password)
    if not token:
        return None, None
    status, resp = get(f"{WORKER_URL}/api/get-orders", token=token)
    if status == 200 and resp.get("ok"):
        pedidos = resp.get("orders") or resp.get("pedidos") or resp.get("data") or []
        return len(pedidos), pedidos
    return 0, resp


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  IPORAVE — Crear pedidos de prueba para usuarios de test")
    print("=" * 70)

    # 1. Login admin
    token, admin_user = login(ADMIN_EMAIL, ADMIN_PASS)
    if not token:
        print("FATAL: no se pudo loguear como admin.")
        sys.exit(1)

    # 2. Anon key
    anon_key = get_anon_key(token)
    if not anon_key:
        print("FATAL: no se pudo obtener anon key.")
        sys.exit(1)

    # 3. Obtener IDs de cada usuario de prueba
    print("\n[USUARIOS] Buscando IDs de usuarios de test ...")
    ids = {}
    for rol, info in USERS_TEST.items():
        u = buscar_id_usuario(info["email"], anon_key, token)
        if u:
            ids[rol] = int(u["id"])
            print(f"  {rol:12s} -> id={u['id']:>4} nombre={u.get('nombre','')} email={u['email']}")
        else:
            print(f"  {rol:12s} -> NO ENCONTRADO ({info['email']})")
            ids[rol] = None

    # Verificación: todos los IDs críticos deben existir
    requeridos = ["vendedor", "delivery", "dropshipper", "proveedor"]
    faltantes = [r for r in requeridos if not ids.get(r)]
    if faltantes:
        print(f"\nFATAL: faltan usuarios: {faltantes}")
        sys.exit(1)

    # 4. Construir lista de pedidos
    pedidos = build_pedidos(ids)
    print(f"\n[PEDIDOS] Total a crear: {len(pedidos)}")

    # 5. Obtener max_id de pedidos
    max_id = get_max_id("pedidos", anon_key, token)
    print(f"  Max id actual en 'pedidos': {max_id}")

    # 6. Crear cada pedido
    print("\n[CREANDO] ...")
    creados = 0
    errores = []
    resumen_por_grupo = {}

    from datetime import date
    fecha_hoy = date.today().isoformat()

    for i, p in enumerate(pedidos):
        grupo = p.pop("_grupo", "otros")
        # Body limpio para Supabase
        body = {
            "id": max_id + i + 1,
            "fecha": fecha_hoy,
            "cliente": p["cliente"],
            "telefono": p["telefono"],
            "direccion": p["direccion"],
            "notas": p["notas"],
            "producto": p["producto"],
            "qty": p["qty"],
            "precio": p["precio"],
            "costo": p["costo"],
            "estado": p["estado"],
            "vendedor_id": p.get("vendedor_id"),
        }
        if p.get("delivery_id"):
            body["delivery_id"] = p["delivery_id"]
        if p.get("drop_id"):
            body["drop_id"] = p["drop_id"]
        if p.get("proveedor_id"):
            body["proveedor_id"] = p["proveedor_id"]
        if p.get("proveedor"):
            body["proveedor"] = p["proveedor"]
        if p.get("comision"):
            body["comision"] = p["comision"]
        if p.get("metodo_cobro"):
            body["metodo_cobro"] = p["metodo_cobro"]
        if p.get("foto_entrega"):
            body["foto_entrega"] = p["foto_entrega"]
        if p.get("prioridad"):
            body["prioridad"] = p["prioridad"]

        status, resp = insertar_pedido(body, anon_key, token)
        if status in (200, 201):
            print(f"  [{i+1:02d}/{len(pedidos)}] OK ({grupo:25s}) — id={body['id']} cliente={p['cliente']} estado={p['estado']}")
            creados += 1
            resumen_por_grupo[grupo] = resumen_por_grupo.get(grupo, 0) + 1
        else:
            err = resp.get("message") or resp.get("error") or resp.get("details") or resp.get("_raw", str(resp))
            print(f"  [{i+1:02d}/{len(pedidos)}] ERROR {status} — cliente={p['cliente']}: {err}")
            errores.append({"cliente": p["cliente"], "grupo": grupo, "status": status, "err": str(err)[:200]})

    # 7. Resumen
    print("\n" + "=" * 70)
    print("  RESUMEN DE CREACIÓN")
    print("=" * 70)
    print(f"  Pedidos creados: {creados}/{len(pedidos)}")
    print(f"  Errores: {len(errores)}")
    print()
    print("  Desglose por grupo:")
    for g, n in sorted(resumen_por_grupo.items()):
        print(f"    {g:30s}: {n}")
    if errores:
        print("\n  Errores:")
        for e in errores:
            print(f"    - {e['cliente']} ({e['grupo']}) status={e['status']}: {e['err']}")

    # 8. Verificación: cada usuario consulta sus pedidos
    print("\n" + "=" * 70)
    print("  VERIFICACIÓN: cada usuario llama /api/get-orders")
    print("=" * 70)
    for rol, info in USERS_TEST.items():
        n, _ = verificar_get_orders(info["email"], info["pass"])
        if n is None:
            print(f"  {rol:12s} ({info['email']}): NO PUDO LOGUEAR")
        else:
            print(f"  {rol:12s} ({info['email']}): ve {n} pedido(s)")


if __name__ == "__main__":
    main()
