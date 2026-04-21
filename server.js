const express = require('express');
const path = require('path');
const https = require('https');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const nodemailer = require('nodemailer');
const { createClient } = require('@supabase/supabase-js');

const app = express();
const PORT = process.env.PORT || 8080;

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) throw new Error('JWT_SECRET no configurado en variables de entorno');

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'iporaveparaguay@gmail.com';
const APP_URL     = process.env.APP_URL || 'https://iporaveparaguay.com';

// ── Cliente Supabase con service key (solo servidor, nunca al navegador) ──────
function getSupaAdmin() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) return null;
  return createClient(url, key);
}

// ── Verificar JWT de sesión ───────────────────────────────────────────────────
function verifyToken(req) {
  const auth = (req.headers.authorization || '').replace('Bearer ', '');
  if (!auth) return null;
  try { return jwt.verify(auth, JWT_SECRET); }
  catch { return null; }
}

// ── Obtener IP real del cliente ───────────────────────────────────────────────
function getClientIP(req) {
  return (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.ip || 'desconocida';
}

// ── Enviar email al administrador cuando aparece un dispositivo nuevo ─────────
async function enviarEmailDispositivoNuevo(username, deviceInfo, approvalToken) {
  const user = process.env.GMAIL_USER;
  const pass  = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) {
    console.warn('⚠️  Email no configurado (GMAIL_USER / GMAIL_APP_PASSWORD)');
    return;
  }

  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: { user, pass },
  });

  const approveUrl = `${APP_URL}/api/aprobar-dispositivo?token=${approvalToken}`;
  const rejectUrl  = `${APP_URL}/api/rechazar-dispositivo?token=${approvalToken}`;

  const html = `
    <div style="font-family:sans-serif;max-width:600px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
      <div style="background:#ef4444;color:white;padding:20px 24px">
        <h2 style="margin:0">⚠️ Nuevo dispositivo detectado — Iporãve</h2>
      </div>
      <div style="padding:24px">
        <p>El usuario <b>${username}</b> intentó ingresar desde un dispositivo <b>no reconocido</b>.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Usuario</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${username}</td></tr>
          <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">IP</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.ip || 'desconocida'}</td></tr>
          <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Navegador</td><td style="padding:8px 12px;border:1px solid #e5e7eb;font-size:12px">${deviceInfo.userAgent || 'desconocido'}</td></tr>
          <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Pantalla</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.screen || 'desconocida'}</td></tr>
          <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Idioma</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.language || 'desconocido'}</td></tr>
          <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Zona horaria</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.timezone || 'desconocida'}</td></tr>
          <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Fecha / hora</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${new Date().toLocaleString('es-PY', {timeZone:'America/Asuncion'})}</td></tr>
        </table>
        <div style="display:flex;gap:12px;margin-top:24px">
          <a href="${approveUrl}" style="flex:1;text-align:center;background:#22c55e;color:white;padding:14px 20px;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px">
            ✅ Autorizar acceso
          </a>
          <a href="${rejectUrl}" style="flex:1;text-align:center;background:#ef4444;color:white;padding:14px 20px;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px">
            ❌ Rechazar
          </a>
        </div>
        <p style="color:#9ca3af;font-size:12px;margin-top:16px">
          Si no reconocés este intento de acceso, hacé clic en Rechazar o ignorá este correo.
        </p>
      </div>
    </div>
  `;

  await transporter.sendMail({
    from: `"Iporãve Sistema" <${user}>`,
    to: ADMIN_EMAIL,
    subject: `⚠️ Nuevo dispositivo: ${username} — ${new Date().toLocaleString('es-PY', {timeZone:'America/Asuncion'})}`,
    html,
  });
}

app.use(express.json({ limit: '2mb' }));

// ── Bloquear acceso directo a archivos sensibles ──────────────────────────────
const BLOCKED = [
  '/server.js', '/package.json', '/package-lock.json',
  '/.gitignore', '/.env', '/CREDENCIALES.txt', '/instrucciones.txt',
];
app.use((req, res, next) => {
  const p = req.path.toLowerCase();
  if (BLOCKED.includes(p)) return res.status(403).json({ error: 'Acceso denegado' });
  next();
});

// ── Configuración pública (sin claves secretas) ───────────────────────────────
// Sirve la anon key de Supabase desde env vars para que no esté en el código fuente
app.get('/api/config', (req, res) => {
  res.json({
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabaseKey: process.env.SUPABASE_ANON_KEY || '',
  });
});

// ── Login seguro — verificación de contraseña + dispositivo en el servidor ────
app.post('/api/login', async (req, res) => {
  const { username, password, device_hash, device_info } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'Datos incompletos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado. Contactá al administrador.' });

  try {
    const { data, error } = await supa
      .from('usuarios')
      .select('*')
      .eq('username', username)
      .single();

    if (error || !data) return res.status(401).json({ error: 'Usuario o contraseña incorrectos' });

    // Verificar contraseña con bcrypt
    const match = await bcrypt.compare(password, data.password);
    if (!match) return res.status(401).json({ error: 'Usuario o contraseña incorrectos' });

    const { password: _pw, ...user } = data;
    if (typeof user.contactos === 'string') {
      try { user.contactos = JSON.parse(user.contactos || '[]'); } catch { user.contactos = []; }
    }

    // ── Verificación de dispositivo (solo para usuarios no-admin) ────────────
    if (user.rol !== 'admin' && device_hash) {
      const ip = getClientIP(req);
      const fullDeviceInfo = { ...(device_info || {}), ip };

      const { data: existingDevice } = await supa
        .from('dispositivos')
        .select('id, autorizado')
        .eq('user_id', user.id)
        .eq('device_hash', device_hash)
        .maybeSingle();

      if (!existingDevice) {
        // Dispositivo nuevo — bloquear y notificar al admin
        const approvalToken = crypto.randomBytes(32).toString('hex');
        await supa.from('dispositivos').insert({
          user_id: user.id,
          username: user.username,
          nombre: user.nombre,
          device_hash,
          device_info: fullDeviceInfo,
          ip,
          autorizado: false,
          token_aprobacion: approvalToken,
          creado_at: new Date().toISOString(),
        });

        try {
          await enviarEmailDispositivoNuevo(user.username, fullDeviceInfo, approvalToken);
        } catch (emailErr) {
          console.error('Error enviando email:', emailErr.message);
        }

        return res.status(403).json({
          ok: false,
          device_pending: true,
          error: 'Dispositivo no reconocido. Se envió una notificación al administrador para que apruebe el acceso.',
        });
      }

      if (!existingDevice.autorizado) {
        return res.status(403).json({
          ok: false,
          device_pending: true,
          error: 'Tu dispositivo está pendiente de aprobación. Esperá la confirmación del administrador.',
        });
      }
    }

    // ── Login exitoso ────────────────────────────────────────────────────────
    const token = jwt.sign(
      { id: user.id, username: user.username, rol: user.rol },
      JWT_SECRET,
      { expiresIn: '12h' }
    );

    res.json({ ok: true, user, token });
  } catch (e) {
    console.error('Error login:', e.message);
    res.status(500).json({ error: 'Error interno del servidor' });
  }
});

// ── Aprobar dispositivo desde email ──────────────────────────────────────────
app.get('/api/aprobar-dispositivo', async (req, res) => {
  const { token } = req.query;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).send('<h2>Servidor no configurado</h2>');

  const { data, error } = await supa
    .from('dispositivos')
    .update({ autorizado: true, aprobado_at: new Date().toISOString() })
    .eq('token_aprobacion', token)
    .select()
    .single();

  if (error || !data) {
    return res.status(400).send(`
      <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
        <h2 style="color:#ef4444">❌ Token inválido</h2>
        <p>El enlace ya fue usado o no es válido.</p>
        <a href="${APP_URL}" style="color:#60a5fa">Ir al sistema</a>
      </body></html>
    `);
  }

  res.send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <div style="max-width:400px;margin:auto">
        <div style="font-size:64px;margin-bottom:16px">✅</div>
        <h2 style="color:#22c55e">Dispositivo autorizado</h2>
        <p>El usuario <b>${data.username || ''}</b> ya puede iniciar sesión desde este dispositivo.</p>
        <a href="${APP_URL}" style="display:inline-block;margin-top:20px;background:#22c55e;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:700">
          Ir al sistema
        </a>
      </div>
    </body></html>
  `);
});

// ── Rechazar dispositivo desde email ─────────────────────────────────────────
app.get('/api/rechazar-dispositivo', async (req, res) => {
  const { token } = req.query;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).send('<h2>Servidor no configurado</h2>');

  await supa.from('dispositivos').delete().eq('token_aprobacion', token);

  res.send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <div style="max-width:400px;margin:auto">
        <div style="font-size:64px;margin-bottom:16px">🚫</div>
        <h2 style="color:#ef4444">Acceso rechazado</h2>
        <p>El dispositivo fue bloqueado. El usuario no podrá ingresar desde ese dispositivo.</p>
        <a href="${APP_URL}" style="display:inline-block;margin-top:20px;background:#6b7280;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:700">
          Ir al sistema
        </a>
      </div>
    </body></html>
  `);
});

// ── Dispositivos pendientes de aprobación (para panel admin) ─────────────────
app.get('/api/dispositivos-pendientes', async (req, res) => {
  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  const { data, error } = await supa
    .from('dispositivos')
    .select('*')
    .eq('autorizado', false)
    .order('creado_at', { ascending: false });

  if (error) return res.status(400).json({ error: error.message });
  res.json({ ok: true, data: data || [] });
});

// ── Aprobar dispositivo desde el panel admin ──────────────────────────────────
app.post('/api/aprobar-dispositivo-admin', async (req, res) => {
  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });

  const { device_id } = req.body;
  if (!device_id) return res.status(400).json({ error: 'ID requerido' });

  const supa = getSupaAdmin();
  const { error } = await supa
    .from('dispositivos')
    .update({ autorizado: true, aprobado_at: new Date().toISOString() })
    .eq('id', device_id);

  if (error) return res.status(400).json({ ok: false, error: error.message });
  res.json({ ok: true });
});

// ── Rechazar dispositivo desde el panel admin ─────────────────────────────────
app.post('/api/rechazar-dispositivo-admin', async (req, res) => {
  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });

  const { device_id } = req.body || {};
  if (!device_id) return res.status(400).json({ error: 'ID requerido' });

  const supa = getSupaAdmin();
  await supa.from('dispositivos').delete().eq('id', device_id);
  res.json({ ok: true });
});

// ── Guardar usuario — hashea contraseña nueva en el servidor ─────────────────
app.post('/api/save-user', async (req, res) => {
  const decoded = verifyToken(req);
  if (!decoded) return res.status(401).json({ error: 'No autorizado' });

  const u = req.body;
  if (!u || !u.id) return res.status(400).json({ error: 'Datos inválidos' });

  if (decoded.rol !== 'admin' && decoded.id !== u.id) {
    return res.status(403).json({ error: 'Sin permisos' });
  }

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  try {
    const row = { ...u };

    if (row.password && !row.password.startsWith('$2')) {
      row.password = await bcrypt.hash(row.password, 10);
    } else if (!row.password) {
      delete row.password;
    }

    if (!Array.isArray(row.contactos)) row.contactos = [];

    const { error } = await supa.from('usuarios').upsert(row, { onConflict: 'id' });
    if (error) return res.status(400).json({ ok: false, error: error.message });

    res.json({ ok: true });
  } catch (e) {
    console.error('Error save-user:', e.message);
    res.status(500).json({ ok: false, error: 'Error interno del servidor' });
  }
});

// ── Migración única: hashear contraseñas en texto plano ──────────────────────
app.post('/api/migrate-passwords', async (req, res) => {
  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') {
    return res.status(403).json({ error: 'Solo el administrador puede ejecutar esta migración' });
  }

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  try {
    const { data, error } = await supa.from('usuarios').select('id, username, password');
    if (error) return res.status(400).json({ error: error.message });

    let migrated = 0;
    for (const u of data) {
      if (!u.password || u.password.startsWith('$2')) continue;
      const hash = await bcrypt.hash(u.password, 10);
      const { error: updErr } = await supa.from('usuarios').update({ password: hash }).eq('id', u.id);
      if (updErr) console.warn(`Error migrando ${u.username}:`, updErr.message);
      else migrated++;
    }

    res.json({ ok: true, migrated, total: data.length });
  } catch (e) {
    console.error('Error migración:', e.message);
    res.status(500).json({ error: e.message });
  }
});

// ── Proxy seguro hacia Anthropic ──────────────────────────────────────────────
app.post('/api/claude', (req, res) => {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'API key no configurada en el servidor' });

  const body = JSON.stringify(req.body);

  const options = {
    hostname: 'api.anthropic.com',
    path: '/v1/messages',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Length': Buffer.byteLength(body),
    },
  };

  const proxyReq = https.request(options, proxyRes => {
    res.status(proxyRes.statusCode);
    proxyRes.setEncoding('utf8');
    let data = '';
    proxyRes.on('data', chunk => { data += chunk; });
    proxyRes.on('end', () => {
      try { res.json(JSON.parse(data)); }
      catch { res.send(data); }
    });
  });

  proxyReq.on('error', err => {
    console.error('Error proxy Anthropic:', err.message);
    res.status(502).json({ error: 'Error al conectar con la IA' });
  });

  proxyReq.write(body);
  proxyReq.end();
});

// ── Archivos estáticos ────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname)));

// ── SPA fallback ──────────────────────────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Iporãve corriendo en http://0.0.0.0:${PORT}`);
});
