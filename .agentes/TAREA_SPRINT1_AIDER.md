# 📋 TAREA PARTE 1 — AIDER
# Director: Claude Code | Aprobación requerida antes de Parte 2

---

## TU ROL EN ESTA PARTE
Limpieza de código legacy en `index.html` — zona segura asignada.

---

## QUÉ TENÉS QUE HACER

### Zona asignada: líneas 1541–1633 (utilidades de mapa y geolocalización)

En esa zona hay funciones que fueron reemplazadas o tienen código muerto. Limpiar:

1. **Línea 1541** — `function loadGoogleMaps(){}` tiene un comentario `// reemplazado por Leaflet`
   - Verificar si esta función todavía se llama en algún lado del archivo
   - Si NO se llama → eliminarla
   - Si se llama → dejar como está y documentarlo en el reporte

2. **Línea 1542** — `function onMapsLoaded(){_mapsLoaded=true;}`
   - Verificar si `_mapsLoaded` se usa en el archivo
   - Si no se usa → eliminar función y variable
   - Si se usa → dejar como está

3. **Bloque `geocodeMapbox` (línea 1543–1552)**
   - Verificar que sigue siendo la versión actual (no hay versión duplicada más abajo)
   - Si hay duplicado → dejar el más reciente, eliminar el viejo
   - Si no hay duplicado → no tocar

4. **Buscar en TODO el archivo** funciones duplicadas con estos nombres:
   - `getDeviceFingerprint` — ¿aparece más de una vez?
   - `getDeviceInfo` — ¿aparece más de una vez?
   - Si hay duplicados → reportarlo, NO eliminar sin preguntar a Claude Code

### Herramienta recomendada
Usar el modo `--no-auto-commits` de Aider.
Hacer los cambios de a uno, verificando con grep antes de eliminar cualquier función.

---

## ZONA ASIGNADA — ÚNICAMENTE estas líneas

| Zona | Líneas |
|---|---|
| Principal | 1541–1633 |
| Búsqueda de duplicados | Todo el archivo (solo lectura para detectar) |

---

## ❌ PROHIBIDO — NO TOCAR

- Líneas 1–1540 (auth, DL, Supabase, realtime, push, caches)
- Líneas 1634 en adelante (WhatsApp, AI, nav, PAGES, etc.)
- `verifyToken`, `login`, `doLogin`, `doLogout`
- `openA`, `openB`, `openC`
- `_ordersCache`, `_usersCache`, `_supaConnected`, `_sessionToken`
- NO eliminar ninguna función sin verificar primero con grep que no se usa

---

## REGLAS TÉCNICAS

1. NUNCA escribir `</script>` dentro de strings JS
2. Ejecutar `node validate.js` ANTES de reportar
3. Si encontrás algo sospechoso → reportarlo en el resumen, NO modificarlo solo
4. En caso de duda → dejar el código como está y anotar en el reporte

---

## CÓMO REPORTAR cuando terminás

```bash
node C:\Users\USUARIO\iporave-sistema\validate.js

curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"Aider\",\"tarea\":\"PARTE1_limpieza_legacy\",\"archivos\":\"public/index.html\",\"resumen\":\"[DESCRIBIR exactamente qué se eliminó, qué se dejó y por qué]\",\"estado\":\"Finalizado\"}"
```

Después esperá confirmación VALIDADO. No avances hasta que Claude Code apruebe la Parte 1 completa.
