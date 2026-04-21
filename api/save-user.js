const { bcrypt, getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded) return res.status(401).json({ error: 'No autorizado' });

  const u = req.body;
  if (!u || !u.id) return res.status(400).json({ error: 'Datos inválidos' });

  if (decoded.rol !== 'admin' && decoded.id !== u.id) return res.status(403).json({ error: 'Sin permisos' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  try {
    const row = { ...u };
    if (row.password && !row.password.startsWith('$2')) {
      row.password = await bcrypt.hash(row.password, 10);
    } else if (!row.password) {
      delete row.password;
    }
    if (!Array.isArray(row.contactos)) row.contactos = [];

    const { error } = await supa.from('usuarios').upsert(row, { onConflict: 'id' });
    if (error) return res.status(400).json({ ok: false, error: error.message });
    res.json({ ok: true });
  } catch(e) {
    res.status(500).json({ ok: false, error: 'Error interno del servidor' });
  }
};
