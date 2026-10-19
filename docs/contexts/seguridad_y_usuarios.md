Última actualización: 2026-10-19

Propósito: describir autenticación, roles, permisos, sesiones y auditoría existentes.
Cambios de autorización deben actualizar pruebas de usuarios/API y la matriz aquí.

Archivos clave:
- `services/usuarios.py` — autenticación bcrypt, CRUD, roles y contraseñas.
- `services/permisos.py` — roles/permisos, decoradores y consulta de rol JWT/sesión local.
- `services/sesion.py` — sesión global en memoria, token cifrado, expiración/actividad.
- `services/encriptacion.py` — cifrado de sesión y política de contraseña; requiere `VESP_ENCRYPTION_KEY` para cifrar.
- `ui/login.py`, `ui/cambiar_password.py`, `ui/gestionar_usuarios.py` — flujo visual de login, cambio y administración.
- `services/auditoria.py`, `services/logger.py` — auditoría estructurada y log de acciones; vistas en `ui/vista_auditoria.py`/`ui/vista_logs.py`.
- `api/routes/auth.py` — login API bcrypt → JWT; protección de rutas en blueprints.

Roles definidos: `admin`, `supervisor`, `auditor`, `gerente`, `operador`. La matriz granular está en `PERMISOS_POR_ROL` de `services/permisos.py`; nombres de permisos se agrupan en usuarios, objetivos, supervisores, pasadas, equipos, reportes, config, auditoría y notas.

Sesiones desktop: estado global de proceso en `services/sesion.py`; token cifrado, vencimiento total a 8 h e inactividad máxima a 2 h; logout limpia la sesión. No confundir ese token local con access JWT Flask.

Contraseñas: los hashes se guardan con bcrypt. `debe_cambiar_password` inicia en 1; login desktop inicia cambio obligatorio cuando el flag está presente. Política de la pantalla: 8–18 caracteres, minúscula, mayúscula, número y sin espacios; ver `ui/cambiar_password.py` para validación completa.

Auditoría: `auditoria` guarda fecha/hora, usuario, tipo, tabla/registro, valores previos/nuevos, detalles/estado; `services/auditoria.py` registra eventos, consulta e informa integridad/exportación. Tabla `logs` guarda acciones simples aparte. Importación inserta su auditoría dentro de la transacción de datos.

Invariantes: no almacenar contraseña en claro; bcrypt para autenticación; comprobar permiso antes de acciones protegidas; no asumir JWT y sesión desktop intercambiables.

Trampas conocidas: API `/auth/login` devuelve `debe_cambiar_password` pero no ofrece ruta de cambio en blueprints; `api/routes/auth.py` no selecciona `activo`, por lo tanto no afirmar que ese endpoint rechaza usuarios desactivados sin verificar un cambio. API obtiene rol de JWT, así que no necesita cifrar sesión local para las rutas JWT.

Dependencias: permisos consultan claims JWT en Flask o sesión local fuera de request; la configuración API requiere JWT secret; contexto de rutas en [api.md](./api.md).

Cómo actualizar este archivo: verificar roles, matriz, tiempos y pantallas de contraseña en servicios/UI/tests antes de documentar cambios.
