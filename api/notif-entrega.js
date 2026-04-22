const { getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded) return res.status(401).json({ error: 'No autorizado' });

  const { pedido_id, cliente, delivery, metodoCobro } = req.body || {};
  if (!pedido_id) return res.status(400).json({ error: 'Datos requeridos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  try {
    const [{ data: admin }, { data: delivUser }] = await Promise.all([
      supa.from('usuarios').select('id,nombre').eq('rol', 'admin').maybeSingle(),
      supa.from('usuarios').select('id,nombre').eq('username', decoded.username).maybeSingle()
    ]);

    if (admin && delivUser) {
      await supa.from('mensajes').insert({
        de_id: delivUser.id,
        de_nombre: delivUser.nombre || delivery,
        para_id: admin.id,
        para_nombre: admin.nombre,
        mensaje: '🚚 ENTREGADO: Pedido #' + pedido_id + ' — ' + (cliente || '') + ' | Cobro: ' + (metodoCobro || '—') + ' | Por: ' + (delivery || delivUser.nombre),
        leido: false,
        created_at: new Date().toISOString()
      });
    }
    res.json({ ok: true });
  } catch(e) {
    console.error('notif-entrega:', e.message);
    res.status(500).json({ error: 'Error al guardar notificación' });
  }
};
