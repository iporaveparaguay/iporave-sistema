const express = require('express');
const path = require('path');
const https = require('https');

const app = express();
const PORT = process.env.PORT || 8080;

app.use(express.json({ limit: '2mb' }));

// ── Bloquear acceso directo a archivos sensibles ──────────────────────────────
const BLOCKED = [
  '/server.js', '/package.json', '/package-lock.json',
  '/.gitignore', '/.env', '/CREDENCIALES.txt', '/instrucciones.txt',
];
app.use((req, res, next) => {
  const p = req.path.toLowerCase();
  if (BLOCKED.includes(p)) return res.status(403).json({ error: 'Acceso denegado' });
  next();
});

// ── Proxy seguro hacia Anthropic ──────────────────────────────────────────────
app.post('/api/claude', (req, res) => {
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

  const proxyReq = https.request(options, proxyRes => {
    res.status(proxyRes.statusCode);
    proxyRes.setEncoding('utf8');
    let data = '';
    proxyRes.on('data', chunk => { data += chunk; });
    proxyRes.on('end', () => {
      try { res.json(JSON.parse(data)); }
      catch { res.send(data); }
    });
  });

  proxyReq.on('error', err => {
    console.error('Error proxy Anthropic:', err.message);
    res.status(502).json({ error: 'Error al conectar con la IA' });
  });

  proxyReq.write(body);
  proxyReq.end();
});

// ── Archivos estáticos ────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname)));

// ── SPA fallback ──────────────────────────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Iporãve corriendo en http://0.0.0.0:${PORT}`);
});
