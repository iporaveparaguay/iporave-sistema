const { getSupaAdmin, verifyToken, APP_URL, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  // POST desde el panel admin (JWT)
  if (req.method === 'POST') {
    const decoded = verifyToken(req);
    if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });
    const { device_id } = req.body || {};
    if (!device_id) return res.status(400).json({ error: 'ID requerido' });
    const { error } = await supa.from('dispositivos').update({ autorizado: true, aprobado_at: new Date().toISOString() }).eq('id', device_id);
    if (error) return res.status(400).json({ ok: false, error: error.message });
    return res.json({ ok: true });
  }

  // GET desde el link del email (token)
  const token = req.query.token;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  const { data: dispositivo } = await supa.from('dispositivos')
    .select('id, username, token_expires_at')
    .eq('token_aprobacion', token).maybeSingle();

  if (!dispositivo) return res.status(400).send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <h2 style="color:#ef4444">❌ Token inválido</h2><p>El enlace no es válido.</p>
      <a href="${APP_URL}" style="color:#60a5fa">Ir al sistema</a>
    </body></html>`);

  if (dispositivo.token_expires_at && new Date(dispositivo.token_expires_at) < new Date()) {
    return res.status(400).send(`
      <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
        <h2 style="color:#ef4444">⏱️ Enlace vencido</h2><p>El enlace expiró. Autorizá manualmente desde el panel.</p>
        <a href="${APP_URL}" style="color:#60a5fa">Ir al sistema</a>
      </body></html>`);
  }

  const { data, error } = await supa.from('dispositivos')
    .update({ autorizado: true, aprobado_at: new Date().toISOString() })
    .eq('id', dispositivo.id).select().single();

  if (error || !data) return res.status(400).send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <h2 style="color:#ef4444">❌ Error</h2><p>El enlace ya fue usado o no es válido.</p>
      <a href="${APP_URL}" style="color:#60a5fa">Ir al sistema</a>
    </body></html>`);

  res.send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <div style="max-width:400px;margin:auto">
        <div style="font-size:64px;margin-bottom:16px">✅</div>
        <h2 style="color:#22c55e">Dispositivo autorizado</h2>
        <p>El usuario <b>${data.username||''}</b> ya puede iniciar sesión.</p>
        <a href="${APP_URL}" style="display:inline-block;margin-top:20px;background:#22c55e;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:700">Ir al sistema</a>
      </div>
    </body></html>`);
};
