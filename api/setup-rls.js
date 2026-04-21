const { verifyToken, allowCors } = require('./_utils');

const PROJECT_REF = 'hrpnqbmknmgdaaokjelb';

const SQL = `
-- Crear tabla dispositivos si no existe con estructura completa
CREATE TABLE IF NOT EXISTS dispositivos (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid,
  username text,
  nombre text,
  device_hash text,
  device_info jsonb,
  ip text,
  autorizado boolean DEFAULT false,
  token_aprobacion text,
  token_expires_at timestamptz,
  creado_at timestamptz DEFAULT now(),
  aprobado_at timestamptz
);

-- Agregar columnas faltantes si la tabla ya existía con estructura incompleta
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS nombre text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS device_info jsonb;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS ip text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS token_expires_at timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS aprobado_at timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS creado_at timestamptz DEFAULT now();

-- Activar RLS en tabla usuarios
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- Activar RLS en tabla dispositivos
ALTER TABLE dispositivos ENABLE ROW LEVEL SECURITY;

-- Eliminar políticas previas si existen (para re-ejecución segura)
DROP POLICY IF EXISTS "bloquear_anon_usuarios" ON usuarios;
DROP POLICY IF EXISTS "bloquear_anon_dispositivos" ON dispositivos;

-- Política: denegar todo acceso anónimo directo (todo debe pasar por la API del servidor)
CREATE POLICY "bloquear_anon_usuarios"
  ON usuarios FOR ALL TO anon USING (false);

CREATE POLICY "bloquear_anon_dispositivos"
  ON dispositivos FOR ALL TO anon USING (false);
`;

module.exports = async function (req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const decoded = verifyToken(req);
  if (!decoded || decoded.rol !== 'admin') {
    return res.status(403).json({ error: 'Solo el administrador puede ejecutar esta configuración' });
  }

  const accessToken = process.env.SUPABASE_ACCESS_TOKEN;
  if (!accessToken) {
    return res.status(503).json({ error: 'SUPABASE_ACCESS_TOKEN no configurado en variables de entorno' });
  }

  try {
    const response = await fetch(`https://api.supabase.com/v1/projects/${PROJECT_REF}/database/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: SQL }),
    });

    const result = await response.json();

    if (!response.ok) {
      return res.status(400).json({ ok: false, error: result });
    }

    res.json({ ok: true, message: 'Tabla dispositivos migrada, RLS activado y políticas creadas correctamente', result });
  } catch (e) {
    console.error('Error setup-rls:', e.message);
    res.status(500).json({ ok: false, error: e.message });
  }
};
