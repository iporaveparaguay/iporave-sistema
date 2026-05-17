// L6 fix: auto-incrementar CACHE_VERSION en sw.js antes de cada deploy.
// Uso: node scripts/bump-sw-version.js
// Lee sw.js, extrae 'vNN', incrementa a 'v(NN+1)', reescribe la línea.

const fs = require('fs');
const path = require('path');

const SW_PATH = path.join(__dirname, '..', 'public', 'sw.js');

function bumpVersion() {
  if (!fs.existsSync(SW_PATH)) {
    console.error('[bump-sw-version] sw.js no encontrado en', SW_PATH);
    process.exit(1);
  }

  const content = fs.readFileSync(SW_PATH, 'utf8');
  const match = content.match(/const\s+CACHE_VERSION\s*=\s*'v(\d+)'/);

  if (!match) {
    console.error('[bump-sw-version] No se encontró CACHE_VERSION en sw.js');
    process.exit(1);
  }

  const oldVer = parseInt(match[1], 10);
  const newVer = oldVer + 1;
  const newContent = content.replace(
    /const\s+CACHE_VERSION\s*=\s*'v\d+'/,
    `const CACHE_VERSION = 'v${newVer}'`
  );

  fs.writeFileSync(SW_PATH, newContent, 'utf8');
  console.log(`[bump-sw-version] v${oldVer} → v${newVer}`);
}

bumpVersion();
