const fs = require('fs');
const path = require('path');

const flagPath = 'C:/Users/USUARIO/node-red-config/stop.flag';

if (fs.existsSync(flagPath)) {
    const contenido = JSON.parse(fs.readFileSync(flagPath, 'utf8'));
    console.log('\n⛔ STOP FLAG ACTIVO — NO continuar');
    console.log('Motivo:', contenido.motivo);
    console.log('Tarea:', contenido.tarea);
    console.log('Timestamp:', contenido.timestamp);
    console.log('\nContactar al usuario antes de continuar.\n');
    process.exit(1);
} else {
    console.log('✅ Sin stop flag — podés continuar trabajando.');
    process.exit(0);
}
