# 📋 TAREA SPRINT 2 — CODEX
# Director: Claude Code

## TU TAREA: Notificaciones in-app (badge + lista)

### Qué hacer:
1. Agregar un badge de notificaciones en el NAV (número rojo con cantidad)
2. Al hacer clic en el badge → abre panel lateral con lista de notificaciones
3. Las notificaciones son: cambios de estado de pedidos del usuario

### Zona asignada: index.html líneas 2669–4888
### NO tocar: líneas 1–2668, verifyToken, login, SAFE_SELF_FIELDS

### Implementación:
- Badge: `<span id="notifBadge">` en el NAV, se actualiza con `_notifUnread`
- Panel: div fixed a la derecha, lista de `_notifHistory`
- Cada notif: ícono + texto + tiempo relativo

### Reglas:
1. NUNCA escribir `</script>` dentro de strings JS
2. `openA(title, body, footer, size)` — exactamente 4 args
3. Ejecutar `node validate.js` antes de reportar

### Reportar al terminar:
```
curl -X POST http://localhost:1880/reporte -H "Content-Type: application/json" -d "{\"agente\":\"Codex\",\"tarea\":\"SPRINT2-B_notificaciones\",\"archivos\":\"public/index.html\",\"resumen\":\"[describir qué hiciste]\",\"estado\":\"Finalizado\"}"
```
