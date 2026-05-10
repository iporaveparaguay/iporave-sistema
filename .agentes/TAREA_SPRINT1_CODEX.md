# 📋 TAREA PARTE 1 — CODEX
# Director: Claude Code | Aprobación requerida antes de Parte 2

---

## TU ROL EN ESTA PARTE
Agregar la página de **Clientes Recurrentes** para el rol vendedor.

---

## QUÉ TENÉS QUE HACER

### Nueva página: `PAGES.clientes_recurrentes`

Agregar este panel DESPUÉS de la línea **4671** (después de `PAGES.analitica_drop`).

El panel debe mostrar:
1. **Lista de clientes** que repiten pedidos con este vendedor
   - Nombre del cliente
   - Cantidad de pedidos realizados
   - Monto total acumulado
   - Fecha del último pedido
   - Botón para abrir chat con ese cliente

2. **Tarjeta de resumen** arriba:
   - Total de clientes únicos
   - % que repitió más de 1 vez
   - Cliente más frecuente (nombre + cantidad)

3. **Ordenar por**: más pedidos primero

### Cómo calcular
Usar `_ordersCache` (ya cargado en memoria).
Filtrar: `o.vendedorId === CU.id` (pedidos de este vendedor).
Agrupar por `o.cliente` (nombre del cliente).

### Agregar al NAV del vendedor
Buscar `NAV_CFG` en el archivo, sección `vendedor`.
Agregar entrada:
```javascript
{ id: 'clientes_recurrentes', label: '👥 Clientes Recurrentes' }
```

---

## ZONA ASIGNADA — ÚNICAMENTE estas líneas

| Zona | Líneas | Qué hacer |
|---|---|---|
| Nueva función | Insertar después de línea 4751 | `PAGES.clientes_recurrentes` |
| NAV_CFG vendedor | Buscar y editar | Agregar ítem al nav |

---

## ❌ PROHIBIDO — NO TOCAR

- Líneas 1–2258 (auth, utils, DL, realtime)
- `verifyToken`, `login`, `SAFE_SELF_FIELDS`
- Cualquier función existente que ya funciona
- `openA()` — usarla con exactamente 4 argumentos: `openA(title, body, footer, size)`
- `getVisibleOrders()` — usar SIEMPRE en vez de `_ordersCache` directo cuando mostrás pedidos al usuario

---

## REGLAS TÉCNICAS OBLIGATORIAS

1. NUNCA escribir `</script>` dentro de strings JS — rompe todo. Usar `'<scr'+'ipt>'`
2. `openA(title, body, footer, size)` — exactamente 4 args
3. Ejecutar `node validate.js` antes de reportar
4. No hacer commit, no hacer deploy — solo escribir el código

---

## CÓMO REPORTAR cuando terminás

```bash
node C:\Users\USUARIO\iporave-sistema\validate.js

curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"Codex\",\"tarea\":\"PARTE1_clientes_recurrentes\",\"archivos\":\"public/index.html\",\"resumen\":\"Agregada página clientes recurrentes para vendedor con stats y lista ordenada por frecuencia\",\"estado\":\"Finalizado\"}"
```

Después esperá confirmación VALIDADO. No avances hasta que Claude Code apruebe la Parte 1 completa.
