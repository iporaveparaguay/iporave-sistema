const nodemailer = require('nodemailer');
const { getSupaAdmin, allowCors, ADMIN_EMAIL, APP_URL } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const { username } = req.body || {};
  if (!username) return res.status(400).json({ error: 'Usuario requerido' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  const { data: user } = await supa.from('usuarios').select('id,username,nombre,rol').eq('username', username).maybeSingle();
  if (!user) return res.status(404).json({ error: 'Usuario no encontrado' });

  const gmailUser = process.env.GMAIL_USER;
  const gmailPass = process.env.GMAIL_APP_PASSWORD;
  if (!gmailUser || !gmailPass) return res.status(503).json({ error: 'Email no configurado' });

  try {
    const transporter = nodemailer.createTransport({ service: 'gmail', auth: { user: gmailUser, pass: gmailPass } });
    await transporter.sendMail({
      from: `"Iporãve Sistema" <${gmailUser}>`,
      to: ADMIN_EMAIL,
      subject: `🔑 Solicitud de recuperación de contraseña — ${user.nombre}`,
      html: `
        <div style="font-family:sans-serif;max-width:600px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
          <div style="background:#f5a623;color:#000;padding:20px 24px">
            <h2 style="margin:0">🔑 Solicitud de recuperación de contraseña</h2>
          </div>
          <div style="padding:24px">
            <p>El siguiente usuario olvidó su contraseña y necesita que le asignes una nueva:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
              <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Nombre</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${user.nombre}</td></tr>
              <tr><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Usuario</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${user.username}</td></tr>
              <tr style="background:#f9fafb"><td style="padding:8px 12px;font-weight:700;border:1px solid #e5e7eb">Rol</td><td style="padding:8px 12px;border:1px solid #e5e7eb">${user.rol}</td></tr>
            </table>
            <p style="color:#6b7280;font-size:13px">Ingresá al sistema → Usuarios → Editar → asigná una contraseña nueva y avisale al usuario.</p>
            <a href="${APP_URL}" style="display:inline-block;margin-top:16px;background:#f5a623;color:#000;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:700">Ir al sistema</a>
          </div>
        </div>`,
    });
    res.json({ ok: true });
  } catch(e) {
    console.error('Email forgot-password:', e.message);
    res.status(500).json({ error: 'Error al enviar email' });
  }
};
