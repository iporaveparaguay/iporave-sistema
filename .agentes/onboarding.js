/**
 * ONBOARDING — Ejecutar antes de empezar a trabajar
 * Uso: node .agentes/onboarding.js
 *
 * Verifica que el entorno esté listo y muestra el contexto del proyecto.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('\n========================================');
console.log('  IPORAVE SISTEMA — ONBOARDING AGENTE');
console.log('========================================\n');

let errores = 0;

// 1. Chequear stop flag
const flagPath = 'C:/Users/USUARIO/node-red-config/stop.flag';
if (fs.existsSync(flagPath)) {
    const flag = JSON.parse(fs.readFileSync(flagPath, 'utf8'));
    console.log('⛔ STOP FLAG ACTIVO — No podés trabajar ahora');
    console.log('   Motivo:', flag.motivo);
    console.log('   Tarea:', flag.tarea);
    process.exit(1);
} else {
    console.log('✅ Stop flag: libre');
}

// 2. Verificar Node-RED activo
try {
    execSync('curl -s -o /dev/null -w "%{http_code}" http://localhost:1880', { timeout: 3000 });
    console.log('✅ Node-RED: activo en http://localhost:1880');
} catch (e) {
    console.log('⚠️  Node-RED: NO está corriendo — iniciarlo con: node-red');
    errores++;
}

// 3. Verificar archivos críticos existen
const archivos = [
    'C:/Users/USUARIO/iporave-sistema/public/index.html',
    'C:/Users/USUARIO/iporave-sistema/validate.js',
    'C:/Users/USUARIO/iporave-worker/src/utils.js',
    'C:/Users/USUARIO/iporave-worker/src/api/login.js',
    'C:/Users/USUARIO/iporave-worker/src/api/save-user.js',
    'C:/Users/USUARIO/iporave-worker/src/index.js',
    'C:/Users/USUARIO/node-red-config/google-credentials.json',
];

console.log('\n📁 Verificando archivos críticos:');
archivos.forEach(archivo => {
    if (fs.existsSync(archivo)) {
        console.log('  ✅', archivo.split('/').pop());
    } else {
        console.log('  ❌ NO ENCONTRADO:', archivo);
        errores++;
    }
});

// 4. Mostrar plan de trabajo
console.log('\n📋 Plan de trabajo: C:\\Users\\USUARIO\\iporave-sistema\\.agentes\\PLAN_AGENTES.md');
console.log('📚 Contexto completo: C:\\Users\\USUARIO\\iporave-sistema\\.agentes\\CONTEXTO_SISTEMA.md');

// 5. Mostrar cómo reportar
console.log('\n📡 Para reportar al pizarrón cuando termines una tarea:');
console.log(`
curl -X POST http://localhost:1880/reporte \\
  -H "Content-Type: application/json" \\
  -d "{\\"agente\\":\\"TU_NOMBRE\\",\\"tarea\\":\\"NOMBRE_TAREA\\",\\"archivos\\":\\"ruta/archivo.js\\",\\"resumen\\":\\"Qué se hizo\\",\\"estado\\":\\"Finalizado\\"}"
`);

// 6. Resultado final
console.log('========================================');
if (errores === 0) {
    console.log('🟢 ENTORNO LISTO — Podés empezar a trabajar');
    console.log('   Leé CONTEXTO_SISTEMA.md y PLAN_AGENTES.md primero');
} else {
    console.log(`🔴 HAY ${errores} PROBLEMA(S) — Resolver antes de continuar`);
}
console.log('========================================\n');
