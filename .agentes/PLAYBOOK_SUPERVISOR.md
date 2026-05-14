# PLAYBOOK SUPERVISOR — Cómo manejar los agentes sin romper nada

> Documento permanente. Lo lee cualquier supervisor que tome el control: Claude próxima sesión, Codex, otro.
> No tiene fecha porque las prácticas no caducan. Lo que sí caduca va en el RELEVO_*.md de cada sesión.

---

## Reglas absolutas (líneas rojas)

**NO TOCAR JAMÁS sin permiso explícito del usuario:**
- `src/api/login.js` — auth, dispositivos, emails
- `src/api/save-user.js` — escala de roles, escudo anti-escalación
- `src/utils.js` `verifyToken()` — verificación de JWT
- Migrations / schemas de Supabase (DROP, ALTER TABLE destructivo)

**NO HACER NUNCA:**
- `git push --force` a `main`
- `wrangler delete` (borra el worker entero)
- `wrangler secret delete` sin asegurarse del valor
- `git reset --hard` sobre cambios no commiteados ajenos
- DROP TABLE, DROP DATABASE, TRUNCATE en Supabase

**NO ASUMIR:**
- Que una columna existe porque "tiene sentido que exista" → siempre verificar en el código real
- Que un endpoint funciona porque la lógica se ve correcta → siempre hacer smoke test post-deploy
- Que `select('*')` es seguro → puede exponer tokens/secretos. Listar columnas explícitamente

---

## Cómo lanzar agentes correctamente

### 1. Decide qué tipo necesitás

| Necesidad | Agente | Por qué |
|---|---|---|
| Encontrar archivos / símbolos / referencias | **Explore** | Read-only, rápido, no modifica |
| Diseñar plan para un cambio grande | **Plan** | Devuelve estrategia, no edita |
| Investigación abierta multi-paso | **general-purpose** | Tiene todas las herramientas |
| Auditar código / encontrar bugs | **Explore** o **general-purpose** | Si solo leen → Explore. Si pueden necesitar correr `node --check` → general |

### 2. Patrón de prompt efectivo

Brief al agente como a un colega que recién entra:
- Qué tiene que hacer (objetivo, no pasos micro)
- Qué información ya conocemos (las "columnas reales" que descubrimos hoy)
- Qué archivos / áreas explorar
- Formato de respuesta esperado (severidad, file:line, fix recomendado)
- Tope de palabras si es para un report ("under 300 words")

**NO le digas:** "haz X y luego Y y luego Z y luego repórtame en un JSON con tales keys". Si lo encadenás demasiado, el agente sigue tu mapa muerto en vez de descubrir cosas.

### 3. Paralelización

Cuando tenés varios slices independientes:
```
Una sola assistant turn con múltiples Agent calls en paralelo
run_in_background: true
Cada agente cubre un slice diferente
Esperar notificaciones, NO polling
```

Ejemplo correcto: "Round 7 — 4 agentes auditando archivos distintos del worker".
Ejemplo incorrecto: lanzar 1 agente y esperar antes de lanzar el siguiente cuando podían correr en paralelo.

### 4. Cómo evitar duplicar trabajo

Mantener registro mental (o en el RELEVO) de qué áreas ya se auditaron. Si lanzás Round N, no le des los mismos archivos que la Round N-1.

---

## Workflow de fix → deploy → verificación

Cada cambio sigue este ciclo (lo violamos hoy una vez y metimos una regresión):

1. **Read** el archivo a modificar (obligatorio antes de Edit)
2. **Edit** con cambio mínimo y focalizado
3. **node --check** sobre el archivo modificado (sintaxis)
4. **git add <archivo específico>** — nunca `git add .` ni `-A`
5. **git commit** con mensaje claro y prefijo:
   - `fix(seg):` seguridad
   - `fix(regression):` rompimos algo que andaba
   - `fix:` bug funcional
   - `feat:` nueva feature
   - `docs:` solo documentación
6. **wrangler deploy --minify** — anota la version ID
7. **Smoke test** con `curl` al endpoint afectado
8. Si falla → `wrangler tail` para ver el error real de Postgres / runtime
9. Si todo OK → próximo cambio

**Regla de oro:** Un commit = un fix lógico. No mezclar.

---

## Manejo de regresiones

Hoy metí una regresión al cambiar `select('*')` por columnas explícitas en `dispositivos-pendientes.js`: incluí `usuario_id` que NO existe.

**Lección:** cuando reemplazás `select('*')`, las columnas que listás tienen que ser exactamente las que existen en la BD. No las que "deberían existir según el nombre del FK".

**Cómo evitarlo:**
1. Antes de listar columnas explícitas, verificar contra otro archivo que haga INSERT/UPDATE a esa misma tabla (ahí se ven las columnas reales)
2. O contra el frontend (busca `_supa.from('TABLA').upsert` en `public/index.html`)
3. Si dudás, dejá un FIXME y abrí una tarea separada para auditar columnas

---

## Cómo leer el pizarrón

Los agentes Python (orquestador-supervisor, etc) reportan a la tabla `pizarron` vía `POST /api/pizarron`. Para ver qué hicieron:

```bash
curl -A "IporaveAgent/1.0" https://iporave-api.iporaveparaguay.workers.dev/api/pizarron
```

Estructura de cada registro: `{ agente, tarea, archivos, resumen, estado, validacion, created_at }`.

**Estado nuevo:** Pendiente. **Estado validado:** "Finalizado" + validacion="OK".

Si ves spam de errores del mismo agente, probablemente está en bucle. Detener con:
```powershell
Stop-Process -Name python -Force  # ojo, mata todos los Python
```
Mejor: `Get-Process python | where { $_.MainWindowTitle -like "*supervisor*" } | Stop-Process`.

---

## Comandos clave (cheat sheet)

```powershell
# Ver versión y estado del worker
cd C:\Users\USUARIO\iporave-worker
git log --oneline -5

# Tail en vivo (capturar errores reales de Postgres)
npx wrangler tail --format pretty

# Smoke test rápido
curl -s -w "HTTP %{http_code}\n" -A "IporaveAgent/1.0" https://iporave-api.iporaveparaguay.workers.dev/api/<endpoint>

# Buscar columnas reales de una tabla
grep -A 10 "from('TABLA').*upsert\|from('TABLA').*insert" C:\Users\USUARIO\iporave-sistema\public\index.html

# Deploy
npx wrangler deploy --minify

# Ver qué políticas RLS existen en Supabase (corre en SQL Editor)
SELECT tablename, policyname FROM pg_policies WHERE schemaname='public' ORDER BY tablename;

# Ver columnas reales de una tabla (corre en SQL Editor)
SELECT column_name, data_type FROM information_schema.columns WHERE table_name='TABLA';
```

---

## Pifies frecuentes que ya descubrí (evitarlas)

1. **Incluir columnas inexistentes en `select()` explícito.** Solución: verificar contra INSERT/UPDATE en el mismo proyecto antes de listar.

2. **`select('*')` deja escapar tokens.** Si la tabla tiene `token_aprobacion`, `password_hash`, etc, el frontend recibe eso. Listar explícitamente.

3. **Asumir que `cliente_id` existe** porque hay `vendedor_id`, `delivery_id`. NO: el cliente es texto en muchos modelos legacy.

4. **Asumir que `precio` existe** en `catalogo`. NO: está dentro del JSON `presentaciones`.

5. **Asumir que `dropshipper_id` existe**. NO: es `drop_id`.

6. **Confundir `mensajes.de`/`para` (no existen) con `de_id`/`para_id` (sí existen).** Lo mismo con `de_nombre`.

7. **Romper al supervisor Python** al agregar auth admin al GET de `/api/pizarron`. El supervisor NO tiene token JWT, así que ese endpoint debe quedar abierto o con `X-Agent-Key` (env `PIZARRON_SECRET`).

8. **Caracteres Unicode decorativos en SQL para Supabase.** Box-drawing como `═══` rompe el parser del SQL Editor. Usar solo ASCII.

9. **Endpoints legacy en estilo Express** dentro del worker. No corren (Workers no es Node), pero son tentadores para "auditar". Verificar primero si están montados en `src/index.js`. Si no, son código muerto.

10. **Heredocs en PowerShell.** No funcionan con `<<EOF`. Usar `@'...'@` o escribir a archivo temporal con `Out-File -Encoding utf8` y luego `git commit -F file.txt`.

---

## Filosofía operativa

- **Mejor un fix chico que se prueba que un refactor grande que se commit a ciegas.**
- **Smoke test inmediato post-deploy.** El user no tiene por qué darse cuenta antes que yo.
- **Verificar al verificar.** Si un agente dice "esto está limpio", releer su trabajo si tenés tiempo. Los agentes alucinan.
- **Documentar lo que descubrís.** Si tardaste 30 minutos en encontrar el nombre real de una columna, anotalo en este playbook para que el próximo no pierda 30 minutos.
- **Cuando el usuario dice "modo automático" o "permiso total":** trabajar a fondo. NO pedir confirmaciones. SÍ respetar líneas rojas.

---

## Contacto con el usuario

- Idioma: **español rioplatense/paraguayo**. SIEMPRE responder en español.
- El usuario es el dueño del negocio Iporãve. No es programador profundo, pero entiende lo que pasa.
- Si hace pregunta técnica: respuesta concisa, sin jerga, con ejemplos concretos cuando se pueda.
- Si dice "dame X minutos": NO lanzar más cosas que requieran su atención. Aprovechar para hacer trabajo silencioso (docs, audits, fixes seguros).
- Si pide guía paso-a-paso para hacer algo en una UI externa (Supabase, Meta, etc): números + lo que va a ver en pantalla.

---

— Playbook escrito por Claude Sonnet 4.6, 2026-05-13. Mantener actualizado en cada sesión.
