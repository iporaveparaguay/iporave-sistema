const { getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded) return res.status(401).json({ error: 'No autorizado' });
  if (decoded.rol !== 'admin') return res.status(403).json({ error: 'Solo administradores pueden eliminar usuarios' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  const { id } = req.body || {};
  if (!id) return res.status(400).json({ error: 'ID requerido' });

  // Limpiar referencias FK antes de eliminar
  try {
    await supa.from('pedidos').update({ vendedor_id: null }).eq('vendedor_id', id);
    await supa.from('pedidos').update({ delivery_id: null }).eq('delivery_id', id);
    await supa.from('pedidos').update({ drop_id: null }).eq('drop_id', id);
    await supa.from('cupos').update({ delivery_id: null }).eq('delivery_id', id);
    await supa.from('dispositivos').delete().eq('user_id', id);

    const { error } = await supa.from('usuarios').delete().eq('id', id);
    if (error) return res.status(400).json({ error: error.message });

    res.json({ ok: true });
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
};
