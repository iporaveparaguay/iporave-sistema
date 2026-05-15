#!/usr/bin/env node
/**
 * crear-datos-prueba-v2.js
 * Inserta datos de prueba COMPLETOS en el sistema Iporave via API REST + Supabase.
 *
 * Uso:
 *   node crear-datos-prueba-v2.js
 *
 * Fuentes consultadas para construir este script:
 *   - iporave-worker/src/index.js            → endpoints disponibles
 *   - iporave-worker/src/api/login.js        → estructura de login
 *   - iporave-worker/src/api/save-user.js    → campos y lógica de usuarios
 *   - iporave-worker/src/api/get-users.js    → GET /api/get-users
 *   - iporave-worker/src/api/config.js       → devuelve supabaseUrl + supabaseKey
 *   - iporave-sistema/public/index.html      → _mapToSupa() con todos los campos de pedidos
 */

'use strict';

const https = require('https');
const http  = require('http');

// ─────────────────────────────────────────────────────────────────────────────
// Configuración
// ─────────────────────────────────────────────────────────────────────────────

const WORKER_URL   = 'https://iporave-api.iporaveparaguay.workers.dev';
const ADMIN_EMAIL  = 'iporaveparaguay@gmail.com';
const ADMIN_PASS   = 'ivan12345';
const USER_PASS    = 'ivan12345';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers HTTP (sin dependencias externas)
// ─────────────────────────────────────────────────────────────────────────────

function request(method, url, body = null, headers = {}) {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const lib    = parsed.protocol === 'https:' ? https : http;

    const payload = body !== null ? JSON.stringify(body) : null;
    const options = {
      hostname: parsed.hostname,
      port:     parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path:     parsed.pathname + parsed.search,
      method,
      headers: {
        'Content-Type':  'application/json',
        'User-Agent':    'IporaveAgentV2/1.0',
        ...headers,
      },
    };
    if (payload) {
      options.headers['Content-Length'] = Buffer.byteLength(payload);
    }

    const req = lib.request(options, (res) => {
      let raw = '';
      res.on('data', chunk => { raw += chunk; });
      res.on('end', () => {
        let data;
        try { data = JSON.parse(raw); } catch { data = { _raw: raw }; }
        resolve({ status: res.statusCode, data });
      });
    });

    req.on('error', (err) => {
      resolve({ status: 0, data: { error: err.message } });
    });

    if (payload) req.write(payload);
    req.end();
  });
}

function get(url, token = null, extraHeaders = {}) {
  const headers = token ? { Authorization: `Bearer ${token}`, ...extraHeaders } : extraHeaders;
  return request('GET', url, null, headers);
}

function post(url, body, token = null, extraHeaders = {}) {
  const headers = token ? { Authorization: `Bearer ${token}`, ...extraHeaders } : extraHeaders;
  return request('POST', url, body, headers);
}

// ─────────────────────────────────────────────────────────────────────────────
// Pausa (ms)
// ─────────────────────────────────────────────────────────────────────────────
function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. Login
// ─────────────────────────────────────────────────────────────────────────────

async function login(email, password) {
  console.log(`\n[LOGIN] Autenticando como ${email} ...`);
  const { status, data } = await post(`${WORKER_URL}/api/login`, { email, password });
  if (status === 200 && data.ok) {
    const { token, user } = data;
    console.log(`  OK — rol: ${user.rol} | id: ${user.id}`);
    return { token, user };
  }
  console.error(`  ERROR ${status}:`, data.error || JSON.stringify(data));
  process.exit(1);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Obtener claves de Supabase via /api/config
// ─────────────────────────────────────────────────────────────────────────────

async function getSupabaseConfig(token) {
  console.log('\n[CONFIG] Obteniendo Supabase URL + anon key ...');
  const { status, data } = await get(`${WORKER_URL}/api/config`, token);
  if (status === 200 && data.ok && data.supabaseKey) {
    console.log('  OK — supabaseUrl:', data.supabaseUrl);
    return { supabaseUrl: data.supabaseUrl, supabaseKey: data.supabaseKey };
  }
  console.error(`  ERROR ${status}:`, data.error || JSON.stringify(data));
  return { supabaseUrl: null, supabaseKey: null };
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Obtener max(id) de una tabla Supabase
// ─────────────────────────────────────────────────────────────────────────────

async function getMaxId(supabaseUrl, supabaseKey, token, tabla) {
  const url = `${supabaseUrl}/rest/v1/${tabla}?select=id&order=id.desc&limit=1`;
  const headers = { apikey: supabaseKey, Accept: 'application/json' };
  const { status, data } = await get(url, token, headers);
  if (status === 200 && Array.isArray(data) && data.length > 0) {
    return parseInt(data[0].id, 10) || 0;
  }
  return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Verificar / Crear usuarios
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Usuarios a crear según la tarea:
 *   - vendedor2@iporave.com / ivan12345 / nombre="María Vendedora" / rol=vendedor
 *   - delivery2@iporave.com / ivan12345 / nombre="Carlos Delivery" / rol=delivery
 */
const USUARIOS_NUEVOS = [
  {
    email:     'vendedor2@iporave.com',
    password:  USER_PASS,
    nombre:    'María Vendedora',
    rol:       'vendedor',
    whatsapp:  '595981000020',
    ciudad:    'Asunción',
    barrio:    'Villa Morra',
    departamento: 'Central',
    pais:      'Paraguay',
  },
  {
    email:     'delivery2@iporave.com',
    password:  USER_PASS,
    nombre:    'Carlos Delivery',
    rol:       'delivery',
    vehiculo:  'moto',
    patente:   'DEL-002',
    whatsapp:  '595981000010',
    ciudad:    'Asunción',
    barrio:    'Herrera',
    departamento: 'Central',
    pais:      'Paraguay',
  },
];

async function obtenerUsuariosExistentes(token) {
  console.log('\n[USUARIOS] Verificando usuarios existentes ...');
  const { status, data } = await get(`${WORKER_URL}/api/get-users`, token);
  if (status === 200 && data.ok) {
    console.log(`  ${data.users.length} usuarios en el sistema.`);
    return data.users;
  }
  console.warn(`  AVISO ${status}: no se pudo obtener la lista de usuarios.`);
  return [];
}

async function crearUsuariosViaWorker(token, supabaseUrl, supabaseKey, usuariosExistentes) {
  console.log('\n[USUARIOS] Creando usuarios nuevos via /api/save-user ...');
  const emailsExistentes    = new Set((usuariosExistentes || []).map(u => u.email?.toLowerCase()));
  const usernamesExistentes = new Set((usuariosExistentes || []).map(u => u.username?.toLowerCase()));

  const maxId = supabaseUrl
    ? await getMaxId(supabaseUrl, supabaseKey, token, 'usuarios')
    : 0;
  console.log(`  Max id en 'usuarios': ${maxId}`);

  let creados = 0;
  for (let i = 0; i < USUARIOS_NUEVOS.length; i++) {
    const u = USUARIOS_NUEVOS[i];
    const usernameDerivado = u.email.split('@')[0].toLowerCase();

    if (emailsExistentes.has(u.email.toLowerCase())) {
      console.log(`  OMITIDO (email ya existe) — ${u.email}`);
      continue;
    }

    if (usernamesExistentes.has(usernameDerivado)) {
      console.log(`  OMITIDO (username '${usernameDerivado}' ya existe) — ${u.email}`);
      continue;
    }

    // save-user requiere un campo 'id' para saber si es creación o edición.
    // Para nuevos usuarios, asignamos un id mayor al máximo actual.
    const nuevoId = maxId + i + 1;
    const body = {
      id:       nuevoId,
      email:    u.email,
      password: u.password,
      nombre:   u.nombre,
      rol:      u.rol,
      username: u.email.split('@')[0],
    };
    // Campos opcionales por rol
    for (const campo of ['vehiculo', 'patente', 'whatsapp', 'ciudad', 'barrio', 'departamento', 'pais']) {
      if (u[campo]) body[campo] = u[campo];
    }

    const { status, data } = await post(`${WORKER_URL}/api/save-user`, body, token);
    if (status === 200 && data.ok) {
      console.log(`  OK — ${u.email} (${u.rol})`);
      creados++;
    } else {
      console.error(`  ERROR ${status} — ${u.email}:`, data.error || data.message || JSON.stringify(data));
    }
    await sleep(300); // evitar rate limit (30 req/min)
  }
  return creados;
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Crear pedidos via Supabase REST
//
// Campos reales de la tabla 'pedidos' extraídos de _mapToSupa() en index.html:
//   id, fecha, cliente, cedula, telefono, direccion, zona_id, proveedor,
//   producto, qty, precio, costo, estado, comision, proveedor_id,
//   vendedor_id, drop_id, delivery_id, metodo_cobro, foto_entrega,
//   gps_lat, gps_lng, sitio, notas,
//   boleta_num, num_doc, razon_social, ruc, tipo_iva,
//   zona_custom_nombre, zona_custom_precio,
//   historial (JSON string), created_by, prioridad
// ─────────────────────────────────────────────────────────────────────────────

const PROV_NOMBRE   = 'Distribuidora Central';
const TEL_PRUEBA    = '595982547222';

function fechaRelativa(diasAtras) {
  const d = new Date();
  d.setDate(d.getDate() - diasAtras);
  return d.toISOString().split('T')[0]; // YYYY-MM-DD
}

/**
 * 8 pedidos en TODOS los estados con todos los campos llenos.
 * Al menos 2 con prioridad=true.
 * Los vendedor_id / delivery_id se completan en runtime con los IDs reales.
 */
function buildPedidos(vendedorId, deliveryId) {
  return [
    // 1 — Pendiente (prioridad: true)
    {
      cliente:      'María García',
      cedula:       '4.567.890',
      telefono:     TEL_PRUEBA,
      direccion:    'Avda. España 1234, Villa Morra, Asunción',
      notas:        'Tocar timbre. Edificio Olimpia, 3er piso.',
      producto:     'Yerba Mate 1kg',
      proveedor:    PROV_NOMBRE,
      qty:          2,
      precio:       15000,
      costo:        9000,
      comision:     0,
      estado:       'Pendiente',
      metodo_cobro: 'efectivo',
      sitio:        'WhatsApp',
      vendedor_id:  vendedorId,
      delivery_id:  null,
      prioridad:    true,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Centro',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(0),
      historial:    JSON.stringify([{ estado: 'Pendiente', fecha: new Date().toISOString() }]),
      created_by:   null,
    },
    // 2 — Confirmado
    {
      cliente:      'Juan López',
      cedula:       '3.456.789',
      telefono:     TEL_PRUEBA,
      direccion:    'Calle Palma 567, Centro, Asunción',
      notas:        'Casa color verde. Frente a la panadería.',
      producto:     'Aceite Cañuelas 900ml',
      proveedor:    PROV_NOMBRE,
      qty:          3,
      precio:       8500,
      costo:        5500,
      comision:     0,
      estado:       'Confirmado',
      metodo_cobro: 'efectivo',
      sitio:        'Instagram',
      vendedor_id:  vendedorId,
      delivery_id:  null,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Norte',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(1),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 1).toISOString() },
        { estado: 'Confirmado', fecha: new Date().toISOString() },
      ]),
      created_by:   null,
    },
    // 3 — Procesando (prioridad: true)
    {
      cliente:      'Ana Rodríguez',
      cedula:       '5.678.901',
      telefono:     TEL_PRUEBA,
      direccion:    'Calle Brasil 890, San Lorenzo, Paraguay',
      notas:        'Entregar a vecina si no hay nadie. Departamento 2B.',
      producto:     'Azúcar 1kg',
      proveedor:    PROV_NOMBRE,
      qty:          5,
      precio:       4500,
      costo:        2800,
      comision:     2250,
      estado:       'Procesando',
      metodo_cobro: 'transferencia',
      sitio:        'Facebook',
      vendedor_id:  vendedorId,
      delivery_id:  null,
      prioridad:    true,
      zona_id:      null,
      zona_custom_nombre: 'San Lorenzo',
      zona_custom_precio: 6000,
      fecha:        fechaRelativa(1),
      historial:    JSON.stringify([
        { estado: 'Pendiente',   fecha: new Date(Date.now() - 86400000 * 1).toISOString() },
        { estado: 'Confirmado',  fecha: new Date(Date.now() - 3600000 * 2).toISOString() },
        { estado: 'Procesando',  fecha: new Date().toISOString() },
      ]),
      created_by:   null,
    },
    // 4 — Despachado
    {
      cliente:      'Carlos Benítez',
      cedula:       '2.345.678',
      telefono:     TEL_PRUEBA,
      direccion:    'Mercado 4, Puesto 42, Asunción, Paraguay',
      notas:        'Cliente en puesto 42, sector frutas. Llamar al llegar.',
      producto:     'Fideos Tallarin 500g',
      proveedor:    PROV_NOMBRE,
      qty:          10,
      precio:       3200,
      costo:        2000,
      comision:     0,
      estado:       'Despachado',
      metodo_cobro: 'efectivo',
      sitio:        'WhatsApp',
      vendedor_id:  vendedorId,
      delivery_id:  deliveryId,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Centro',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(2),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 2).toISOString() },
        { estado: 'Confirmado', fecha: new Date(Date.now() - 86400000 * 1).toISOString() },
        { estado: 'Procesando', fecha: new Date(Date.now() - 3600000 * 4).toISOString() },
        { estado: 'Despachado', fecha: new Date().toISOString() },
      ]),
      created_by:   null,
    },
    // 5 — En ruta
    {
      cliente:      'Laura Gómez',
      cedula:       '6.789.012',
      telefono:     TEL_PRUEBA,
      direccion:    'Av. Mcal. López 1234, Barrio Manorá, Asunción',
      notas:        'Llamar 10 min antes de llegar. Portón negro.',
      producto:     'Leche Entera 1L',
      proveedor:    PROV_NOMBRE,
      qty:          4,
      precio:       5800,
      costo:        3600,
      comision:     2320,
      estado:       'En ruta',
      metodo_cobro: 'efectivo',
      sitio:        'WhatsApp',
      vendedor_id:  vendedorId,
      delivery_id:  deliveryId,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Sur',
      zona_custom_precio: 5000,
      gps_lat:      -25.2867,
      gps_lng:      -57.6470,
      fecha:        fechaRelativa(2),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 2).toISOString() },
        { estado: 'Despachado', fecha: new Date(Date.now() - 3600000 * 3).toISOString() },
        { estado: 'En ruta',    fecha: new Date().toISOString() },
      ]),
      created_by:   null,
    },
    // 6 — Entregado
    {
      cliente:      'Miguel Torres',
      cedula:       '1.234.567',
      telefono:     TEL_PRUEBA,
      direccion:    'Av. Eusebio Ayala 4521, Asunción',
      notas:        'Segundo piso, oficina 8. Horario: 8am-6pm.',
      producto:     'Arroz Largo Fino 1kg',
      proveedor:    PROV_NOMBRE,
      qty:          2,
      precio:       6500,
      costo:        4200,
      comision:     0,
      estado:       'Entregado',
      metodo_cobro: 'efectivo',
      sitio:        'Instagram',
      vendedor_id:  vendedorId,
      delivery_id:  deliveryId,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Este',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(3),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 3).toISOString() },
        { estado: 'Despachado', fecha: new Date(Date.now() - 86400000 * 2).toISOString() },
        { estado: 'En ruta',    fecha: new Date(Date.now() - 3600000 * 5).toISOString() },
        { estado: 'Entregado',  fecha: new Date(Date.now() - 3600000 * 2).toISOString() },
      ]),
      created_by:   null,
    },
    // 7 — Cancelado
    {
      cliente:      'Rosa Ferreira',
      cedula:       '7.890.123',
      telefono:     TEL_PRUEBA,
      direccion:    'Av. Artigas 3650, Barrio Herrera, Asunción',
      notas:        'Portón azul. No atendió 3 llamadas. Cancelado por inaccesible.',
      producto:     'Yerba Mate 1kg',
      proveedor:    PROV_NOMBRE,
      qty:          1,
      precio:       15000,
      costo:        9000,
      comision:     0,
      estado:       'Cancelado',
      metodo_cobro: 'efectivo',
      sitio:        'WhatsApp',
      vendedor_id:  vendedorId,
      delivery_id:  deliveryId,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Norte',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(4),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 4).toISOString() },
        { estado: 'Despachado', fecha: new Date(Date.now() - 86400000 * 3).toISOString() },
        { estado: 'Cancelado',  fecha: new Date(Date.now() - 86400000 * 2).toISOString() },
      ]),
      created_by:   null,
    },
    // 8 — Entregado (métricas de delivery / estadísticas)
    {
      cliente:      'Pedro Villalba',
      cedula:       '8.901.234',
      telefono:     TEL_PRUEBA,
      direccion:    'Av. Boggiani 2345, Asunción',
      notas:        'Recepcionista toma el pedido. Pedir firma de recibido.',
      producto:     'Aceite Cañuelas 900ml',
      proveedor:    PROV_NOMBRE,
      qty:          6,
      precio:       8500,
      costo:        5500,
      comision:     5100,
      estado:       'Entregado',
      metodo_cobro: 'transferencia',
      sitio:        'Facebook',
      vendedor_id:  vendedorId,
      delivery_id:  deliveryId,
      prioridad:    false,
      zona_id:      null,
      zona_custom_nombre: 'Asunción Oeste',
      zona_custom_precio: 5000,
      fecha:        fechaRelativa(5),
      historial:    JSON.stringify([
        { estado: 'Pendiente',  fecha: new Date(Date.now() - 86400000 * 5).toISOString() },
        { estado: 'Confirmado', fecha: new Date(Date.now() - 86400000 * 4).toISOString() },
        { estado: 'Procesando', fecha: new Date(Date.now() - 86400000 * 3).toISOString() },
        { estado: 'Despachado', fecha: new Date(Date.now() - 86400000 * 2).toISOString() },
        { estado: 'En ruta',    fecha: new Date(Date.now() - 86400000 * 1).toISOString() },
        { estado: 'Entregado',  fecha: new Date().toISOString() },
      ]),
      created_by:   null,
    },
  ];
}

async function crearPedidos(supabaseUrl, supabaseKey, token, vendedorId, deliveryId) {
  console.log('\n[PEDIDOS] Creando 8 pedidos de prueba via Supabase REST ...');
  if (!supabaseUrl || !supabaseKey) {
    console.error('  ERROR: no se pudo obtener Supabase URL/key. Pedidos omitidos.');
    return 0;
  }

  const maxId = await getMaxId(supabaseUrl, supabaseKey, token, 'pedidos');
  console.log(`  Max id actual en 'pedidos': ${maxId}`);

  const pedidos = buildPedidos(vendedorId, deliveryId);
  const url = `${supabaseUrl}/rest/v1/pedidos`;
  const headers = {
    apikey:  supabaseKey,
    Prefer:  'return=minimal',
  };

  let creados = 0;
  for (let i = 0; i < pedidos.length; i++) {
    const p = pedidos[i];
    const body = { ...p, id: maxId + i + 1 };

    const { status, data } = await post(url, body, token, headers);
    if (status === 201 || status === 200) {
      console.log(`  OK [${i + 1}/${pedidos.length}] ${p.estado.padEnd(12)} — ${p.cliente}${p.prioridad ? ' ⚡PRIORIDAD' : ''}`);
      creados++;
    } else {
      const err = data.message || data.error || data.details || JSON.stringify(data);
      console.error(`  ERROR ${status} — ${p.cliente} (${p.estado}): ${err}`);
    }
    await sleep(200);
  }
  return creados;
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilidad: buscar usuario por email en la lista
// ─────────────────────────────────────────────────────────────────────────────

function findByEmail(users, email) {
  return (users || []).find(u => u.email?.toLowerCase() === email.toLowerCase());
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  console.log('='.repeat(60));
  console.log('  IPORAVE — Generador de datos de prueba v2');
  console.log(`  Worker:   ${WORKER_URL}`);
  console.log(`  Fecha:    ${new Date().toLocaleString('es-PY')}`);
  console.log('='.repeat(60));

  // 1. Login como superadmin
  const { token, user: superadmin } = await login(ADMIN_EMAIL, ADMIN_PASS);

  // 2. Obtener Supabase config
  const { supabaseUrl, supabaseKey } = await getSupabaseConfig(token);

  // 3. Obtener usuarios existentes para no duplicar
  const usuariosExistentes = await obtenerUsuariosExistentes(token);

  // 4. Crear usuarios si no existen
  const usuariosCreados = await crearUsuariosViaWorker(
    token, supabaseUrl, supabaseKey, usuariosExistentes
  );

  // 5. Volver a obtener lista de usuarios (ahora deberían estar los nuevos)
  const { data: usersData } = await get(`${WORKER_URL}/api/get-users`, token);
  const todosLosUsuarios = usersData?.users || usuariosExistentes;

  // 6. Resolver IDs de vendedor y delivery para los pedidos.
  //    Prioridad: usuarios recién creados (.com) → cualquier vendedor/delivery existente → superadmin.
  let vendedorUsuario = findByEmail(todosLosUsuarios, 'vendedor2@iporave.com')
    || findByEmail(todosLosUsuarios, 'vendedor2@iporave.test')
    || todosLosUsuarios.find(u => u.rol === 'vendedor');
  let deliveryUsuario = findByEmail(todosLosUsuarios, 'delivery2@iporave.com')
    || findByEmail(todosLosUsuarios, 'delivery2@iporave.test')
    || todosLosUsuarios.find(u => u.rol === 'delivery');

  const vendedorId = vendedorUsuario?.id ?? superadmin.id;
  const deliveryId = deliveryUsuario?.id ?? null;

  console.log(`\n[IDs resueltos]`);
  console.log(`  vendedor_id : ${vendedorId}  (${vendedorUsuario?.email ?? 'superadmin como fallback'})`);
  console.log(`  delivery_id : ${deliveryId ?? '(null — no se asignará delivery)'}  (${deliveryUsuario?.email ?? ''})`);

  // 7. Crear pedidos
  const pedidosCreados = await crearPedidos(
    supabaseUrl, supabaseKey, token, vendedorId, deliveryId
  );

  // ── Resumen ──────────────────────────────────────────────────────────────
  const totalUsuariosEsperados = USUARIOS_NUEVOS.length;
  const totalPedidosEsperados  = 8;

  console.log('\n' + '='.repeat(60));
  console.log('  RESUMEN');
  console.log('='.repeat(60));
  console.log(`  Usuarios creados : ${usuariosCreados} / ${totalUsuariosEsperados}`);
  console.log(`  Pedidos creados  : ${pedidosCreados}  / ${totalPedidosEsperados}`);
  console.log('='.repeat(60));

  if (pedidosCreados === totalPedidosEsperados) {
    console.log('  Pedidos: OK — todos creados correctamente.');
  } else {
    console.log(`  Pedidos: ${totalPedidosEsperados - pedidosCreados} fallaron. Ver mensajes de ERROR arriba.`);
  }
  if (usuariosCreados < totalUsuariosEsperados) {
    console.log(`  Usuarios: ${totalUsuariosEsperados - usuariosCreados} omitidos porque ya existían (username/email duplicado).`);
    console.log('  Esto es normal si el script ya fue ejecutado antes.');
  }
  console.log();
}

main().catch(err => {
  console.error('\n[FATAL]', err.message || err);
  process.exit(1);
});
