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
    await supa.from('dispositivos').delete().eq('id', device_id);
    return res.json({ ok: true });
  }

  // GET desde el link del email (token)
  const token = req.query.token;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  await supa.from('dispositivos').delete().eq('token_aprobacion', token);

  res.send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <div style="max-width:400px;margin:auto">
        <div style="font-size:64px;margin-bottom:16px">🚫</div>
        <h2 style="color:#ef4444">Acceso rechazado</h2>
        <p>El dispositivo fue bloqueado.</p>
        <a href="${APP_URL}" style="display:inline-block;margin-top:20px;background:#6b7280;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:700">Ir al sistema</a>
      </div>
    </body></html>`);
};
