Última actualización: 2026-10-19

Propósito: documentar la API Flask modular y su contrato operativo.
Es un servidor auxiliar independiente; no sustituye la aplicación desktop ni su login local.

Archivos clave:
- `api/app.py` — Flask, JWT, rate limiter, Redis SSE, blueprints y host/puerto.
- `api/routes/__init__.py` — registra los blueprints bajo `/api`.
- `api/routes/auth.py` — emisión de JWT y endpoint protegido de ejemplo.
- `api/routes/objetivos.py`, `api/routes/supervisores.py` — CRUD con permisos.
- `api/routes/pasadas.py`, `api/routes/reportes.py` — altas/lecturas de pasadas y reportes.
- `api/routes/sse.py` — stream y publicación SSE; `api/docs.py` expone OpenAPI.

Rutas: `POST /api/auth/login`, `GET /api/auth/protected`; `/api/objetivos` GET/POST y `/<id>` GET/PUT/DELETE; `/api/supervisores` GET/POST y `/<id>` GET/PUT/DELETE; `/api/pasadas` POST y `/dia/<fecha>` GET; `/api/reportes/mensual/<anio>/<mes>` y `/diario/<fecha>` GET; `/api/sse/events` GET y `/publish` POST; `/` GET. `/api/docs` está definida en `api/docs.py`, pero `api.app` no importa ese módulo, así que no queda registrada por el arranque normal.

Auth: login acepta campos `usuario`/`contrasena` o `username`/`password`, valida bcrypt y entrega access JWT con identidad username y claims usuario_id/rol. Rutas de datos exigen JWT y evalúan permisos; SSE events exige JWT. Rate limit predeterminado global: 200/día y 50/hora por dirección remota; backend `memory://` salvo URI configurada.

Entorno: Flask requiere `VESP_JWT_SECRET` y `VESP_SSE_PUBLISH_TOKEN` no vacío al arrancar; `VESP_DB_PATH` opcional para SQLite; `VESP_RATE_LIMIT_STORAGE_URI` opcional; `VESP_REDIS_URL` para SSE (predeterminado Redis local); `VESP_API_HOST`, `VESP_API_PORT`, `VESP_API_DEBUG` opcionales. `VESP_ENCRYPTION_KEY` lo usa el cifrado de sesión desktop, pero `api.app` no lo exige directamente. `VESP_API_KEY` aparece comentada en `.env.example`, sin referencia de consumo en el código Python revisado.

SSE: Redis es el transporte; publish requiere Authorization y un objeto JSON, stream emite `data_change`. TRAMPA: `api/routes/sse.py` carga `SSE_PUBLISH_TOKEN` pero compara Authorization con el literal `******`; `services/sincronizacion.py` también envía ese literal. No asumir que el secreto configurado se valida correctamente hasta corregir y probar ambos extremos.

Invariantes: no documentar secretos ni valores reales; rutas protegidas usan JWT y permisos donde están implementados; no introducir rutas sin registrarlas en blueprint.

Trampas conocidas: `api/docs.py` documenta un subconjunto de endpoints; API usa SQLite y permisos compartidos; las respuestas de excepción de rutas varían, revisar el handler antes de cambiar contrato.

Dependencias: API consume `models`, `services` y `database`; puntos de arranque en README. API interna HTTP separada: `services/api_rest.py`.

Cómo actualizar este archivo: contrastar rutas, decoradores, permisos, valores por defecto y cliente SSE con cada blueprint.
