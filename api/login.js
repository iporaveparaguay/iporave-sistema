const crypto = require('crypto');
const nodemailer = require('nodemailer');
const { bcrypt, jwt, JWT_SECRET, ADMIN_EMAIL, APP_URL, getSupaAdmin, getClientIP, allowCors } = require('./_utils');

async function enviarEmailDispositivo(username, deviceInfo, approvalToken) {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) { console.warn('Email no configurado'); return; }

  const transporter = nodemailer.createTransport({ service: 'gmail', auth: { user, pass } });
  const approveUrl = `${APP_URL}/api/aprobar-dispositivo?token=${approvalToken}`;
  const rejectUrl  = `${APP_URL}/api/rechazar-dispositivo?token=${approvalToken}`;

  await transporter.sendMail({
    from: `"Iporãve Sistema" <${user}>`,
    to: ADMIN_EMAIL,
    subject: `⚠️ Nuevo dispositivo: ${username} — ${new Date().toLocaleString('es-PY', {timeZone:'America/Asuncion'})}`,
    html: `
      <div style="font-family:sans-serif;max-width:600px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
        <div style="background:#ef4444;color:white;padding:20px 24px">
          <h2 style="margin:0">⚠️ Nuevo dispositivo detectado — Iporãve</h2>
        </div>
        <div style="padding:24px">
          <p>El usuario <b>${username}</b> intentó ingresar desde un dispositivo <b>no reconocido</b>.</p>
          <table style="width:100%;border-collapse:collapse;margin:16px 0">
            <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">IP</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.ip||'—'}</td></tr>
            <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Navegador</td><td style="padding:8px 12px;border:1px solid #e5e7eb;font-size:12px">${(deviceInfo.userAgent||'—').substring(0,100)}</td></tr>
            <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Pantalla</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.screen||'—'}</td></tr>
            <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Idioma</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.language||'—'}</td></tr>
            <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Zona horaria</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${deviceInfo.timezone||'—'}</td></tr>
            <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Fecha / hora</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${new Date().toLocaleString('es-PY',{timeZone:'America/Asuncion'})}</td></tr>
          </table>
          <div style="display:flex;gap:12px;margin-top:24px">
            <a href="${approveUrl}" style="flex:1;text-align:center;background:#22c55e;color:white;padding:14px 20px;text-decoration:none;border-radius:8px;font-weight:700">✅ Autorizar acceso</a>
            <a href="${rejectUrl}" style="flex:1;text-align:center;background:#ef4444;color:white;padding:14px 20px;text-decoration:none;border-radius:8px;font-weight:700">❌ Rechazar</a>
          </div>
        </div>
      </div>`,
  });
}

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const { username, password, device_hash, device_info } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'Datos incompletos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado. Contactá al administrador.' });

  try {
    const { data, error } = await supa.from('usuarios').select('*').eq('username', username).single();
    if (error || !data) return res.status(401).json({ error: 'Usuario o contraseña incorrectos' });

    let match = false;
    if (data.password && data.password.startsWith('$2')) {
      match = await bcrypt.compare(password, data.password);
    } else {
      match = password === data.password;
      if (match) {
        const hash = await bcrypt.hash(password, 10);
        await supa.from('usuarios').update({ password: hash }).eq('id', data.id);
      }
    }
    if (!match) return res.status(401).json({ error: 'Usuario o contraseña incorrectos' });

    const { password: _pw, ...user } = data;
    if (typeof user.contactos === 'string') {
      try { user.contactos = JSON.parse(user.contactos || '[]'); } catch { user.contactos = []; }
    }

    // Verificación de dispositivo (solo usuarios no-admin)
    if (user.rol !== 'admin' && device_hash) {
      const ip = getClientIP(req);
      const fullInfo = { ...(device_info || {}), ip };

      const { data: dev } = await supa.from('dispositivos').select('id,autorizado').eq('user_id', user.id).eq('device_hash', device_hash).maybeSingle();

      if (!dev) {
        const token = crypto.randomBytes(32).toString('hex');
        await supa.from('dispositivos').insert({
          user_id: user.id, username: user.username, nombre: user.nombre,
          device_hash, device_info: fullInfo, ip, autorizado: false,
          token_aprobacion: token, creado_at: new Date().toISOString(),
        });
        try { await enviarEmailDispositivo(user.username, fullInfo, token); } catch(e) { console.error('Email error:', e.message); }
        return res.status(403).json({ ok: false, device_pending: true, error: 'Dispositivo no reconocido. Se envió una notificación al administrador para aprobar el acceso.' });
      }

      if (!dev.autorizado) {
        return res.status(403).json({ ok: false, device_pending: true, error: 'Tu dispositivo está pendiente de aprobación. Esperá la confirmación del administrador.' });
      }
    }

    const token = jwt.sign({ id: user.id, username: user.username, rol: user.rol }, JWT_SECRET, { expiresIn: '12h' });
    res.json({ ok: true, user, token });
  } catch(e) {
    console.error('Error login:', e.message);
    res.status(500).json({ error: 'Error interno del servidor' });
  }
};
