const { getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Sin permisos' });

  const { device_id } = req.body || {};
  if (!device_id) return res.status(400).json({ error: 'ID requerido' });

  const supa = getSupaAdmin();
  const { error } = await supa.from('dispositivos').update({ autorizado: true, aprobado_at: new Date().toISOString() }).eq('id', device_id);
  if (error) return res.status(400).json({ ok: false, error: error.message });
  res.json({ ok: true });
};
