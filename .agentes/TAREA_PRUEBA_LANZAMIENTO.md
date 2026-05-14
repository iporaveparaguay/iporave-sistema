# Tarea — Prueba completa pre-lanzamiento

## Contexto
**Fecha límite:** 2026-05-15 (mañana a la tarde)
**Objetivo:** Entregar accesos a ~10 usuarios reales. Antes de eso, prueba completa del sistema.
**Quién prueba:** Usuario + agentes automatizados

---

## 1. DATOS FICTICIOS A CARGAR (antes de probar)

### Usuarios por rol (crear en panel superadmin)
| Rol | Cantidad sugerida | Datos |
|---|---|---|
| Vendedor | 2 | nombre, email, teléfono, foto perfil ficticia |
| Delivery | 2 | nombre, email, vehículo, patente, foto perfil, foto cédula |
| Dropshipper | 1 | nombre, RUC ficticio, logo, nombre comercial |
| Empresa | 1 | nombre comercial, RUC, logo |
| Admin | 1 | (ya existe Isidro) |

### Pedidos (crear desde panel)
- Mínimo 5 pedidos en distintos estados: Pendiente, En camino, Entregado, Cancelado
- Al menos 1 con ⚡ prioridad activa
- Usar direcciones reales de Asunción para probar el mapa
- Asignar a distintos vendedores y deliveries

### Catálogo (cargar desde panel)
- 5-8 productos con foto (usar imágenes de stock libres o placeholder)
- Distintas categorías
- Al menos 1 con variantes (ej: talle S/M/L)

---

## 2. CHECKLIST DE PRUEBAS POR ROL

### Superadmin
- [ ] Login
- [ ] Crear usuario (todos los roles)
- [ ] Editar usuario
- [ ] Eliminar usuario
- [ ] Ver mapa con pedidos
- [ ] Marcar pedido como ⚡ prioridad
- [ ] Exportar CSV pedidos
- [ ] Exportar PDF pedidos
- [ ] Cambiar estado de pedido
- [ ] Asignar delivery a pedido
- [ ] Sección Config (requiere contraseña)
- [ ] Sección SQL (requiere contraseña)
- [ ] Botón scroll-to-top
- [ ] Panel notificaciones (campanita)
- [ ] Cerrar sesión

### Vendedor
- [ ] Login
- [ ] Ver sus propios pedidos
- [ ] Crear nuevo pedido
- [ ] Ver perfil → completar todos los campos
- [ ] Chat de pedido
- [ ] Exportar CSV/PDF (si tiene permiso)
- [ ] Cerrar sesión

### Delivery
- [ ] Login
- [ ] Ver pedidos asignados
- [ ] Cambiar estado del pedido (En camino / Entregado)
- [ ] Ver mapa con navegación (botón Navegar — debe ser azul)
- [ ] Perfil → completar vehículo, patente, foto
- [ ] Recibir push notification (requiere que haya subscripto)
- [ ] Cerrar sesión

### Dropshipper
- [ ] Login
- [ ] Ver panel de estadísticas
- [ ] Ver liquidaciones
- [ ] Ver catálogo
- [ ] Perfil → RUC, logo, nombre comercial
- [ ] Cerrar sesión

---

## 3. FUNCIONALIDADES A PROBAR (independiente del rol)

### Botones críticos
- [ ] Exportar CSV pedidos
- [ ] Exportar PDF pedidos
- [ ] Imprimir guía de envío
- [ ] Botón ⋮ en pedidos (abrir dropdown, todas las opciones)
- [ ] Botón ⋮ en catálogo (editar, eliminar)
- [ ] Botón ⋮ en usuarios (editar, eliminar)
- [ ] GPS / Navegar en mapa (color azul, no rojo)
- [ ] Botón IA asistente (abrir panel, no que solo arrastre)
- [ ] Botón scroll-to-top (debe notarse visualmente)

### Mapa
- [ ] Pines de pedidos visibles
- [ ] Labels con nombre del cliente legibles
- [ ] Pin con prioridad animado (shake + sonar)
- [ ] Botón GPS centrar en ubicación actual
- [ ] Abrir Waze/Google Maps con "Navegar"

### Perfil
- [ ] Guardar campos parcialmente (no debe bloquear si faltan opcionales)
- [ ] Bloqueo de nav si faltan campos obligatorios del rol
- [ ] Foto de perfil — subir imagen
- [ ] Foto cédula frente/dorso (solo roles que lo requieren)

### Mobile (probar en celular real)
- [ ] Login responsive
- [ ] Navegación inferior visible y tocable
- [ ] Botón ⋮ cómodo para tocar (44px)
- [ ] Mapa en mobile
- [ ] Formularios en mobile (teclado no tapa campos)

---

## 4. AUTOMATIZACIÓN CON AGENTES

### Ya disponible
- `crear-datos-prueba.py` — crea usuarios/productos/pedidos en DB
- `tester-visual.py` — tester con Playwright + Gemini Vision (screenshots + análisis)

### Comando para correr tester visual
```bash
python .agentes/tester-visual.py --user iporaveparaguay@gmail.com --pass ivan12345
```

### Qué automatizar con agentes en esta sesión
1. **Agente carga de datos** — ampliar `crear-datos-prueba.py` para crear usuarios por rol con datos completos
2. **Agente tester visual** — correr `tester-visual.py` en todas las secciones y generar reporte
3. **Agente revisor de reporte** — leer screenshots + análisis Gemini y listar bugs encontrados

---

## 5. BUGS CONOCIDOS PENDIENTES (antes de lanzar)

| Bug | Severidad | Archivo |
|---|---|---|
| Botón scroll-to-top negro (no resalta) | Baja | index.html — #codexScrollTopBtn |
| Campanita visible antes del login | Media | index.html — codexNotifBell |
| Refinamiento visual botones pedidos | Baja | TAREA_PEDIDOS_BOTONES_OVERFLOW.md |
| Bandera PY + título mobile | Baja | TAREA_UI_LOGIN_MOBILE.md |

---

## 6. FEATURES FUTURAS (post-lanzamiento, NO bloquean entrega)

- Correo corporativo con dominio propio (iporave@iporaveparaguay.com)
- API keys propias por cliente: WhatsApp Business, Shopify, Dropi
- Botones de integración en perfil: Meta Ads, Shopify, Dropi
- Asistente IA con voz (TAREA_ASISTENTE_VOZ_IA.md)
- Mapbox V6 (reemplazar Leaflet)
- Tienda online pública con auto-registro

---

## Prioridad: CRÍTICA — mañana es el lanzamiento
