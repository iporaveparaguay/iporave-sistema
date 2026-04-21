const { getSupaAdmin, APP_URL, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  const token = req.query.token;
  if (!token) return res.status(400).send('<h2>Token inválido</h2>');

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).send('<h2>Servidor no configurado</h2>');

  const { data, error } = await supa.from('dispositivos')
    .update({ autorizado: true, aprobado_at: new Date().toISOString() })
    .eq('token_aprobacion', token).select().single();

  if (error || !data) return res.status(400).send(`
    <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#0b0d12;color:white">
      <h2 style="color:#ef4444">❌ Token inválido</h2><p>El enlace ya fue usado o no es válido.</p>
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
