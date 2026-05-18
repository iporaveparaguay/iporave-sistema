# RELEVO MAESTRO — 2026-05-17 (CONSOLIDADO Y VERIFICADO)

> **AVISO IMPORTANTE:** Este documento es la FUENTE DE VERDAD para la próxima sesión. Reemplaza a los RELEVO v6, v7 y v8. En las últimas sesiones, Claude perdió un poco el contexto y generó reportes inexactos (ej. afirmó que "no se había tocado código", cuando en realidad múltiples agentes arreglaron más de 80 bugs).

---

## 🚀 ESTADO REAL DEL SISTEMA (AL 2026-05-17)

Tras una serie de auditorías y trabajo de agentes en paralelo:
- **Bugs Solucionados:** Se han corregido **81 de los 94 bugs** identificados (86% completado). 
- **Crashes:** Todos los bugs críticos (17/17) que provocaban crashes (como los de `_notificaciones` y `const SVG` usados antes de declaración) **YA ESTÁN ARREGLADOS**.
- **Worker:** Se aplicaron múltiples fixes de seguridad (MAPBOX_TOKEN movido a secret, validación de WhatsApp, `admin-tools.js` protegido con OTP, prevención de colisiones JWT).
- **Frontend:** Multiples commits con correcciones de viewport, CSV exports, reset de timers en doLogout, y limpiezas de UI.

---

## ⏸️ BUGS DE UI EN PAUSA (ESPERANDO CAPTURAS DEL USUARIO)

El usuario reportó 6 bugs nuevos de funcionalidad/UI que **ESTÁN EN ESPERA**. **NO TOCAR ESTOS ASPECTOS** hasta que el usuario envíe las capturas de pantalla:

1. **BUG-U1:** Campo "enlaces" de pedido muestra un dropdown negro fijo que dice "Paraguay".
2. **BUG-U2:** Falta el `<select>` para elegir proveedor existente en el formulario Nuevo Pedido.
3. **BUG-U3:** Faltan campos eliminados en Nuevo Pedido (calle, sitio, URL, GPS) y hay que agregar ciudad/barrio.
4. **BUG-U4:** Zonas no se geocodifican solas (ej. escribir "Lambaré" debería buscar coordenadas en Mapbox).
5. **BUG-U5 (CRÍTICO UI):** Los botones en el topbar/header están desorganizados en TODA la app.
6. **BUG-U6:** El sub-admin puede ver datos que deberían ser exclusivos del superadmin (revisar scope de queries).

---

## 🔴 PENDIENTES TÉCNICOS RESTANTES (13 Bugs)

Quedan 13 pendientes técnicos menores/medios. Los más importantes a abordar en la próxima sesión son:

### Prioridad Alta / Seguridad
1. **SEC9:** Falta implementar 2FA/OTP para acciones destructivas (eliminar usuario, cambiar rol, resetAll).
2. **A16:** `getPagos({})` necesita filtrar los pagos por rol también en la petición por red (RLS o worker backend).
3. **A2:** `_fotoBase64` no se limpia correctamente entre confirmaciones de diferentes pedidos (riesgo bajo, pero hay que purgarlo siempre).

### Prioridad Media / UX
4. **Boletas (M19 / M20):** 
   - El filtro de fecha de las boletas es inconsistente con el timestamp de Supabase.
   - El flete de zona siempre figura gravado a la tasa del producto en lugar de estar separado al 5%.
5. **M22:** Implementar la cascada de modelos de IA (Groq → Gemini → DeepSeek → Anthropic) para tolerancia a fallos. (Pospuesto a decisión del usuario).

---

## ⚙️ ACCIONES MANUALES DEL USUARIO (RECORDATORIO)

El usuario debe realizar lo siguiente fuera del agente:
1. **Mapbox:** Rotar el `MAPBOX_TOKEN` en la web de Mapbox (el token antiguo quedó expuesto en el historial de Git).
2. **Cloudflare:** Configurar el secret `CLEANUP_OTP` en el dashboard de Workers para que el admin-tools pueda hacer limpiezas.
3. **Supabase:** Revisar las políticas RLS para asegurarse de que ninguna tabla crítica (pedidos/usuarios) tenga `using(true)`.
4. **Verificación:** Validar en Supabase si la columna `pagado_por` en la tabla `pagos` es UUID o Integer (bug A22 pendiente de revisión manual).

---

## 🛠️ INSTRUCCIONES PARA LA PRÓXIMA SESIÓN

1. **Esperar las capturas de pantalla** del usuario antes de tocar CUALQUIER botón o layout en el Frontend.
2. Si el usuario da luz verde para avanzar sin capturas, **enfocarse en resolver SEC9 (2FA)** y los **bugs de las Boletas (M19/M20)**.
3. Siempre verificar con `node validate.js` antes de comitear al Frontend.
4. Mantener la comunicación en modo **ahorro de tokens**, usar respuestas concisas.
