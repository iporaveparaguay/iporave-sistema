const { allowCors, getSupaAdmin } = require('./_utils');

// Usuarios demo que nunca deben existir en el sistema
const DEMO_USERNAMES = ['vendedor', 'dropshipper', 'delivery', 'proveedor'];

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  // Eliminar usuarios demo — primero limpiar referencias para evitar error de FK
  try {
    const supa = getSupaAdmin();
    if (supa) {
      const { data: demoUsers } = await supa.from('usuarios').select('id').in('username', DEMO_USERNAMES);
      if (demoUsers && demoUsers.length > 0) {
        const ids = demoUsers.map(u => u.id);
        await supa.from('pedidos').update({ vendedor_id: null }).in('vendedor_id', ids);
        await supa.from('pedidos').update({ delivery_id: null }).in('delivery_id', ids);
        await supa.from('pedidos').update({ drop_id: null }).in('drop_id', ids);
        await supa.from('cupos').update({ delivery_id: null }).in('delivery_id', ids);
        await supa.from('dispositivos').delete().in('user_id', ids);
        await supa.from('usuarios').delete().in('id', ids);
      }
    }
  } catch(e) {
    console.error('Error limpiando usuarios demo:', e.message);
  }

  res.json({
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabaseKey: process.env.SUPABASE_ANON_KEY || '',
  });
};
