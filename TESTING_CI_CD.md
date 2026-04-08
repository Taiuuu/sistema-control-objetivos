# Testing & CI/CD

Documentación completa para testing, integración continua y despliegue.

---

## 🧪 Testing

### Setup

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=services --cov=database --cov=api

# Tests específicos
pytest tests/test_usuarios.py::TestCrearUsuario
pytest -k "test_reporte" -v

# Con marcadores
pytest -m "unit"
pytest -m "api"
```

### Test Coverage

```bash
pytest --cov=.  --cov-report=html

# Abrir reporte HTML
open htmlcov/index.html
```

### Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidas
├── test_usuarios.py         # Tests de usuarios
├── test_reportes.py         # Tests de reportes
└── test_api.py              # Tests de API
```

### Fixtures Disponibles

- `test_db` - Database temporal para tests
- `db_initialized` - DB inicializada con esquema
- `admin_user` - Usuario admin de prueba
- `operador_user` - Usuario operador de prueba
- `test_objetivo` - Objetivo de prueba
- `test_supervisor` - Supervisor de prueba
- `api_client` - Cliente Flask para tests de API
- `auth_token` - Token JWT válido

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Workflows automáticos en `.github/workflows/`:

#### `tests.yml` - Testing & Quality

Ejecuta en cada push y PR:

- **Tests**: pytest en Python 3.10, 3.11, 3.12
- **Linting**: flake8, black check, isort
- **Seguridad**: bandit, safety
- **Coverage**: Envío a Codecov
- **Build**: PyInstaller

**Triggers:**
- Push a `main` o `develop`
- PRs contra `main` o `develop`

#### `release.yml` - Releases

Se ejecuta al crear un tag `v*`:

- Extrae version del tag
- Actualiza archivos de versión
- Construye ejecutable con PyInstaller
- Construye instalador con Inno Setup
- Publica release en GitHub

**Uso:**

```bash
# Crear una nueva release
git tag v1.1.0
git push origin v1.1.0
```

### Configuración Local

#### Pre-commit Hooks

```bash
# Instalar
pre-commit install

# Configurar en .pre-commit-config.yaml
```

#### Matriz de Tests

- **OS**: ubuntu-latest, windows-latest
- **Python**: 3.10, 3.11, 3.12
- **Total combinaciones**: 6

---

## 📦 Despliegue

### Build Manual

```bash
# Compilar EXE
pyinstaller "VESP Control.spec"

# Compilar instalador (requiere Inno Setup)
iscc.exe instalador.iss

# Salida
dist/VESP Control.exe
Output/VESP_Control_Instalador.exe
```

### Semantic Versioning

Seguido: `MAJOR.MINOR.PATCH`

- **MAJOR**: Cambios incompatibles
- **MINOR**: Nuevas características
- **PATCH**: Correcciones de bugs

Ejemplos:
- v1.0.0 - Primera versión
- v1.1.0 - Nuevas funciones
- v1.1.1 - Parches
- v2.0.0 - Cambio mayor

---

## 📊 Métricas

### Coverage Targets

| Módulo | Target | Actual |
|--------|--------|--------|
| services | 80% | -
| database | 85% | -
| api | 75% | -
| **Total** | **80%** | -

### Quality Gates

- ✅ Tests deben pasar al 100%
- ✅ Lint errors: 0
- ✅ Coverage: mínimo 60%
- ✅ Security: sin vulnerabilidades críticas

---

## 🔐 Security Testing

Ejecutado con:

- **Bandit**: Detecta problemas comunes de seguridad
- **Safety**: Verifica dependencias contra vulnerabilidades conocidas

```bash
bandit -r services api database -ll
safety check
```

---

## 📝 Reporte de Cobertura

El reporte HTML se genera automáticamente:

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

Archivos generados:
- `htmlcov/index.html` - Resumen de coverage
- `htmlcov/` - Detalles por archivo
- `.coverage` - Data file (binario)

---

## ⚡ Tips & Tricks

### Ejecutar solo tests rápidos

```bash
pytest -m "not slow"
```

### Debug de tests

```bash
pytest -v --pdb  # Abre debugger en fallo
pytest --tb=long --verbose
```

### Generar XML para CI

```bash
pytest --junit-xml=junit/test-results.xml
```

### Watch mode

```bash
ptw  # Requiere pytest-watch
```

---

## 🐛 Troubleshooting

**LA BD está locked?**
- Asegurate que no hay instancia de la app corriendo
- Limpia archivos temporales en `~/.pytest_cache`

**Tests fallan localmente pero pasan en CI?**
- Verifica Python version: `python --version`
- Limpia cache: `pytest --cache-clear`

**Coverage no incluye todos los modules?**
- Verifica `pytest.ini` configuration
- Asegurate de que estás en la raíz del proyecto

---

## 📚 Referencias

- [pytest docs](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Bandit](https://bandit.readthedocs.io/)
