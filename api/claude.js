const https = require('https');
const { allowCors } = require('./_utils');

module.exports = async function(req, res) {
  allowCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'API key no configurada en el servidor' });

  const body = JSON.stringify(req.body);

  const options = {
    hostname: 'api.anthropic.com',
    path: '/v1/messages',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Length': Buffer.byteLength(body),
    },
  };

  return new Promise((resolve) => {
    const proxyReq = https.request(options, proxyRes => {
      res.status(proxyRes.statusCode);
      let data = '';
      proxyRes.setEncoding('utf8');
      proxyRes.on('data', chunk => { data += chunk; });
      proxyRes.on('end', () => {
        try { res.json(JSON.parse(data)); } catch { res.send(data); }
        resolve();
      });
    });
    proxyReq.on('error', err => {
      res.status(502).json({ error: 'Error al conectar con la IA' });
      resolve();
    });
    proxyReq.write(body);
    proxyReq.end();
  });
};
