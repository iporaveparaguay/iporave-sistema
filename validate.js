/**
 * validate.js — Iporãve Sistema
 * Ejecutar antes de cualquier commit: node validate.js
 * Detecta errores que rompen el sistema silenciosamente.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const HTML = path.join(__dirname, 'public', 'index.html');
let errors = 0;

function fail(msg) {
  console.error('  ✗ ' + msg);
  errors++;
}
function ok(msg) {
  console.log('  ✓ ' + msg);
}

console.log('\n🔍 Validando public/index.html...\n');
const html = fs.readFileSync(HTML, 'utf8');

// 1. Encontrar el bloque <script> principal
// Buscar '\n<script>' para no confundirse con <script> dentro de strings JS
const mainStartRaw = html.lastIndexOf('\n<script>');
const mainStart = mainStartRaw + 1; // apuntar al '<' del tag
const mainEnd = html.lastIndexOf('</script>');
if (mainStart < 1 || mainEnd < 0) {
  fail('No se encontró el bloque <script> principal');
  process.exit(1);
}
const mainScript = html.substring(mainStart + 8, mainEnd);
ok('Bloque <script> principal encontrado (' + mainScript.length + ' chars)');

// 2. Buscar </script> sin escapar dentro del script principal
// Esto cierra el bloque HTML y rompe TODO el sistema
const badScript = mainScript.indexOf('</script>');
if (badScript >= 0) {
  const line = html.substring(0, mainStart + 8 + badScript).split('\n').length;
  fail('</script> sin escapar en línea ' + line + ' — ROMPE EL SISTEMA COMPLETO');
  fail('  Fix: usar \'<scr\'+\'ipt>\' y \'<\'+\'/script>\' para dividir el tag');
} else {
  ok('Sin </script> sin escapar dentro del script principal');
}

// 3. Verificar balance básico de llaves en el script
let braces = 0;
for (let i = 0; i < mainScript.length; i++) {
  if (mainScript[i] === '{') braces++;
  else if (mainScript[i] === '}') braces--;
}
if (braces !== 0) {
  fail('Balance de llaves {} incorrecto: diferencia = ' + braces);
} else {
  ok('Balance de llaves {} correcto');
}

// 4. Verificar que el script cierra correctamente
if (!html.endsWith('</html>') && !html.trimEnd().endsWith('</html>')) {
  fail('El archivo no termina con </html>');
} else {
  ok('Archivo HTML bien cerrado');
}

// 5. Verificar CDN críticos presentes
const cdns = ['supabase', 'mapbox-gl'];
cdns.forEach(cdn => {
  if (html.includes(cdn)) ok('CDN ' + cdn + ' presente');
  else fail('CDN ' + cdn + ' FALTA');
});

// 6. Verificar sintaxis JavaScript real (detecta SyntaxError antes de deployar)
try {
  new vm.Script(mainScript);
  ok('Sintaxis JavaScript válida (vm.Script)');
} catch (e) {
  const lineMatch = e.stack ? e.stack.match(/:(\d+)/) : null;
  const lineNum = lineMatch ? lineMatch[1] : '?';
  fail('SyntaxError en línea ~' + lineNum + ': ' + e.message + ' — NO deployar');
}

// 7. Verificar funciones críticas presentes
const funcs = ['doLogin', 'PAGES.catalogo', 'DL.saveProducto', 'exportOrdersPDF'];
funcs.forEach(fn => {
  if (mainScript.includes(fn)) ok('Función ' + fn + ' presente');
  else fail('Función ' + fn + ' NO ENCONTRADA — posible corrupción');
});

console.log('\n' + (errors === 0
  ? '✅ Todo OK — seguro para commit/deploy\n'
  : '❌ ' + errors + ' error(s) encontrado(s) — NO deployar\n'));

process.exit(errors > 0 ? 1 : 0);
