const { getSupaAdmin, verifyToken, allowCors } = require('./_utils');

const DEMO = ['vendedor', 'dropshipper', 'delivery', 'proveedor'];

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  const decoded = verifyToken(req);
  if (!decoded) return res.status(401).json({ error: 'No autorizado' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  const { data, error } = await supa
    .from('usuarios')
    .select('id,username,nombre,rol,vehiculo,patente,whatsapp,contactos');

  if (error) return res.status(400).json({ error: error.message });

  // Eliminar usuarios demo y devolver lista limpia
  const users = (data || [])
    .filter(u => !DEMO.includes((u.username || '').toLowerCase()))
    .map(u => ({
      ...u,
      contactos: typeof u.contactos === 'string'
        ? JSON.parse(u.contactos || '[]')
        : (u.contactos || [])
    }));

  res.json({ ok: true, users });
};
