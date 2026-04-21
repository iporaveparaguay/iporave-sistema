const https = require('https');

const PROJECT_REF = 'hrpnqbmknmgdaaokjelb';
const accessToken = process.env.SUPABASE_ACCESS_TOKEN;

if (!accessToken) {
  console.log('⚠️  SUPABASE_ACCESS_TOKEN no configurado — saltando migración.');
  process.exit(0);
}

const SQL = `
-- ── 1. Extensión pgcrypto para hashear contraseñas desde SQL ─────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── 2. Tabla dispositivos — crear si no existe, agregar columnas faltantes ────
CREATE TABLE IF NOT EXISTS dispositivos (
  id            uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       uuid,
  username      text,
  nombre        text,
  device_hash   text,
  device_info   jsonb,
  ip            text,
  autorizado    boolean     DEFAULT false,
  token_aprobacion  text,
  token_expires_at  timestamptz,
  creado_at     timestamptz DEFAULT now(),
  aprobado_at   timestamptz
);
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS nombre           text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS device_info      jsonb;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS ip               text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS token_expires_at timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS aprobado_at      timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS creado_at        timestamptz DEFAULT now();

-- ── 3. Hashear contraseñas en texto plano con bcrypt (work factor 10) ─────────
UPDATE usuarios
SET password = crypt(password, gen_salt('bf', 10))
WHERE password IS NOT NULL
  AND password NOT LIKE '$2%';

-- ── 4. Activar RLS en ambas tablas ────────────────────────────────────────────
ALTER TABLE usuarios     ENABLE ROW LEVEL SECURITY;
ALTER TABLE dispositivos ENABLE ROW LEVEL SECURITY;

-- ── 5. Políticas de seguridad — bloquear acceso anónimo directo ───────────────
DROP POLICY IF EXISTS "bloquear_anon_usuarios"     ON usuarios;
DROP POLICY IF EXISTS "bloquear_anon_dispositivos" ON dispositivos;

CREATE POLICY "bloquear_anon_usuarios"
  ON usuarios FOR ALL TO anon USING (false);

CREATE POLICY "bloquear_anon_dispositivos"
  ON dispositivos FOR ALL TO anon USING (false);
`;

function runSQL(sql) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ query: sql });
    const options = {
      hostname: 'api.supabase.com',
      path: `/v1/projects/${PROJECT_REF}/database/query`,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

(async () => {
  try {
    console.log('🔧 Ejecutando migración de seguridad...');
    await runSQL(SQL);
    console.log('✅ Migración completada:');
    console.log('   • Tabla dispositivos verificada y columnas completadas');
    console.log('   • Contraseñas en texto plano hasheadas con bcrypt');
    console.log('   • RLS activado en usuarios y dispositivos');
    console.log('   • Políticas de seguridad aplicadas');
  } catch (e) {
    console.error('❌ Error en migración:', e.message);
    process.exit(0); // No bloquear el deploy por esto
  }
})();
