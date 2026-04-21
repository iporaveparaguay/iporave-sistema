const { bcrypt, getSupaAdmin, verifyToken, allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') return res.status(403).json({ error: 'Solo el administrador puede ejecutar esta migración' });

  const supa = getSupaAdmin();
  if (!supa) return res.status(503).json({ error: 'Servidor no configurado' });

  try {
    const { data, error } = await supa.from('usuarios').select('id, username, password');
    if (error) return res.status(400).json({ error: error.message });

    let migrated = 0;
    for (const u of data) {
      if (!u.password || u.password.startsWith('$2')) continue;
      const hash = await bcrypt.hash(u.password, 10);
      const { error: updErr } = await supa.from('usuarios').update({ password: hash }).eq('id', u.id);
      if (!updErr) migrated++;
    }
    res.json({ ok: true, migrated, total: data.length });
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
};
