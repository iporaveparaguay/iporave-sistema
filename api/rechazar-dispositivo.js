const { getSupaAdmin, APP_URL, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  const token = req.query.token;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).send('<h2>Servidor no configurado</h2>');

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
