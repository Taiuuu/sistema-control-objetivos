# VESP Control de Objetivos - API REST

API REST avanzada para el sistema de control de objetivos VESP, con autenticación JWT, rate limiting y notificaciones en tiempo real vía SSE.

## Características

- ✅ CRUD completo para objetivos, supervisores y pasadas
- ✅ Autenticación JWT (simplificada)
- ✅ Rate limiting (200/día, 50/hora)
- ✅ Notificaciones SSE en tiempo real
- ✅ Documentación OpenAPI/Swagger
- ✅ Integración con sincronización del sistema desktop

## Endpoints Principales

### Autenticación
- `POST /api/auth/login` - Login (usuario cualquiera por ahora)

### Objetivos
- `GET /api/objetivos` - Listar objetivos
- `POST /api/objetivos` - Crear objetivo
- `PUT /api/objetivos/<id>` - Actualizar objetivo
- `DELETE /api/objetivos/<id>` - Dar de baja objetivo

### Supervisores
- `GET /api/supervisores` - Listar supervisores
- `POST /api/supervisores` - Crear supervisor
- `PUT /api/supervisores/<id>` - Actualizar supervisor
- `DELETE /api/supervisores/<id>` - Eliminar supervisor

### Pasadas
- `POST /api/pasadas` - Registrar pasada
- `GET /api/pasadas/dia/<fecha>` - Obtener pasadas del día

### Reportes
- `GET /api/reportes/mensual/<anio>/<mes>` - Reporte mensual
- `GET /api/reportes/diario/<fecha>` - Reporte diario

### Notificaciones
- `GET /api/sse/events` - Stream SSE (requiere JWT)
- `POST /api/sse/publish` - Publicar evento (interno)

## Documentación

Accede a `/api/docs` para ver la documentación completa en formato OpenAPI.

## Inicio

```bash
python -m api.app
```

La API estará disponible en `http://127.0.0.1:5000`

## Integración

La API se integra automáticamente con el sistema de sincronización del desktop. Los cambios en la BD emiten notificaciones SSE que pueden ser consumidas por clientes externos.