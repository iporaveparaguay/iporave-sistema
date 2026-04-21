const https = require('https');

const PROJECT_REF = 'hrpnqbmknmgdaaokjelb';
const accessToken = process.env.SUPABASE_ACCESS_TOKEN;

if (!accessToken) {
  console.log('⚠️  SUPABASE_ACCESS_TOKEN no configurado — saltando migración de base de datos.');
  process.exit(0);
}

const SQL = `
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
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS nombre text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS device_info jsonb;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS ip text;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS token_expires_at timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS aprobado_at timestamptz;
ALTER TABLE dispositivos ADD COLUMN IF NOT EXISTS creado_at timestamptz DEFAULT now();
`;

const body = JSON.stringify({ query: SQL });

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
      console.log('✅ Migración de base de datos completada correctamente.');
    } else {
      console.error('❌ Error en migración:', data);
      process.exit(0); // No fallar el deploy por esto
    }
  });
});

req.on('error', (e) => {
  console.error('❌ Error de conexión en migración:', e.message);
  process.exit(0);
});

req.write(body);
req.end();
