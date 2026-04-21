const { allowCors, getSupaAdmin } = require('./_utils');

// Usuarios demo que nunca deben existir en el sistema
const DEMO_USERNAMES = ['vendedor', 'dropshipper', 'delivery', 'proveedor'];

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  // Eliminar usuarios demo si existen — se ejecuta en cada carga, es idempotente
  try {
    const supa = getSupaAdmin();
    if (supa) {
      await supa.from('usuarios').delete().in('username', DEMO_USERNAMES);
    }
  } catch(e) {
    console.error('Error limpiando usuarios demo:', e.message);
  }

  res.json({
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabaseKey: process.env.SUPABASE_ANON_KEY || '',
  });
};
