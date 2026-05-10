# Sprint 2-D para Aider — Consistencia de error handling en el Worker

## Zona asignada
`C:\Users\USUARIO\iporave-worker\src\api\` — todos los archivos .js de API

## Tarea
Revisá cada archivo de la carpeta src/api/ y verificá:

1. Que todos los endpoints POST validen que el body no esté vacío antes de hacer queries a Supabase
2. Que todos los errores de Supabase sean capturados y devuelvan JSON con `{ error: mensaje }` y status 400/500
3. Que ningún endpoint devuelva un error sin headers CORS (siempre usar `corsHeaders()` de utils.js)

## Archivos a revisar (en orden de prioridad)
- src/api/save-user.js
- src/api/orders.js  
- src/api/calificaciones.js
- src/api/tracking.js

## Restricciones
- NO tocar: src/api/login.js, src/utils.js, src/api/save-user.js (campo SAFE_SELF_FIELDS)
- Solo correcciones pequeñas y seguras
- Si dudás de un cambio, no lo hagas

## Al terminar
Reportar al pizarrón:
curl -X POST http://localhost:1880/reporte -H "Content-Type: application/json" -d "{\"agente\":\"Aider\",\"tarea\":\"Sprint2D-worker-errorhandling\",\"archivos\":\"src/api/\",\"resumen\":\"Revisión completa de error handling y CORS en endpoints\",\"estado\":\"Finalizado\"}"
