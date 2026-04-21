const { getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  const { data, error } = await supa.from('dispositivos').select('*').eq('autorizado', false).order('creado_at', { ascending: false });
  if (error) return res.status(400).json({ error: error.message });
  res.json({ ok: true, data: data || [] });
};
