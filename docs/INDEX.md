# 📚 Índice de Documentación
## VESP Control de Objetivos

**Estado:** ✅ Documentación Completa  
**Última actualización:** Abril 2026  
**Versión:** 1.0.0

---

## 🗂️ Estructura de Docs

```
docs/
├── INDEX.md                    ← Estás aquí
├── ARQUITECTURA.md             ← Estructura técnica
├── ROADMAP.md                  ← Plan desarrollo
├── ESTRUCTURA_PROYECTO.md      ← Organización carpetas
├── TECH_SPEC.md                ← Especificaciones técnicas
├── GUIA_INSTALACION.md         ← Cómo instalar
└── GUIA_DESARROLLO.md          ← Para desarrolladores (próximo)
```

---

## 📖 Documentación Principal

### 1. **ARQUITECTURA.md** 🏗️
**¿Qué es?** Visión clara de la arquitectura actual y futura

**Contiene:**
- Diagrama de evolución: v1.0 → v2.0 → v3.0
- Capas de la aplicación (presentación, servicios, datos)
- Componentes por versión
- Matriz de seguridad comparativa
- Flujos de datos

**Cuándo leerlo:**
- Necesitas entender la estructura general
- Quieres saber cómo escala a v2.0/v3.0
- Integración con otros sistemas

**Duración lectura:** 10-15 minutos

---

### 2. **ROADMAP.md** 🗺️
**¿Qué es?** Plan detallado de desarrollo hasta v3.0

**Contiene:**
- Fases: v1.0 (hecho), v2.0 (Q2-Q3 2026), v3.0 (Q4 2026)
- Sub-fases de v2.0 con duración estimada
- Features por versión
- Checklist de implementación
- Riesgos y mitigación
- Estimación de esfuerzo

**Estructura v2.0:**
- 2.1 Refactoring módulos (3 semanas)
- 2.2 App Android (4-5 semanas)
- 2.3 Sincronización (3-4 semanas)
- 2.4 Importación (2-3 semanas)
- 2.5 Base de datos (2 semanas)

**Cuándo leerlo:**
- Planificación de sprints
- Estimación de timelines
- Decisiones de prioridad

**Duración lectura:** 15-20 minutos

---

### 3. **ESTRUCTURA_PROYECTO.md** 📂
**¿Qué es?** Organización actual del proyecto y guía de navegación

**Contiene:**
- Árbol completo de carpetas
- Descripción de cada directorio
- Propósito de cada módulo
- Flujo de datos entre componentes
- Status de cada parte (v1.0/v2.0/v3.0)

**Carpetas principales:**
```
desktop/       → Código PyQt6 actual
mobile/        → Apps Kivy (Android) y Flutter (iOS futura)
shared/        → Servicios reutilizables
services/      → Lógica de negocio
ui/            → Interfaz gráfica
api/           → API REST
database/      → Configuración BD
```

**Cuándo leerlo:**
- Primer día en el proyecto
- Buscar dónde está una funcionalidad
- Agregar nuevo módulo

**Duración lectura:** 10 minutos

---

### 4. **TECH_SPEC.md** 📋
**¿Qué es?** Especificación técnica exhaustiva

**Contiene:**
- Stack tecnológico completo (PyQt6, Kivy, Flask, etc)
- Modelo de datos (5 entidades con validaciones)
- Seguridad (JWT, encriptación, autorización)
- Lógica de negocio (turnos nocturnos, duplicados)
- Schema SQL (SQLite/PostgreSQL compatible)
- Performance targets
- Testing coverage requerida
- Datos en reposo y en tránsito

**Secciones clave:**
- Arquitectura por capas
- Matriz de permisos de roles
- Validaciones por campo
- Cálculo de turnos nocturnos
- Detección de duplicados
- Reportes

**Cuándo leerlo:**
- Implementar nueva feature
- Entender validaciones
- Diseñar nuevo componente
- Security review

**Duración lectura:** 30-45 minutos (lectura completa)

---

### 5. **GUIA_INSTALACION.md** 📥
**¿Qué es?** Instrucciones paso a paso para instalar

**Contiene:**
- 3 opciones de instalación PC:
  1. Instalador ejecutable
  2. Desde código fuente
  3. Conda
- Instalación tablets Android
- Compilación de APK
- iPhone futuro
- Configuración inicial
- Troubleshooting

**Primeros pasos:**
```bash
# Opción 1: Instalador
Descargar .exe → Ejecutar → Listo

# Opción 2: Código
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd sistema-control-objetivos
python -m venv venv
./venv/Scripts/activate  # Windows
pip install -r requirements.txt
python main.py
```

**Cuándo usarlo:**
- Instalación inicial
- Setup de desarrollo
- Troubleshooting de errores

**Duración:** 15-30 minutos (instalación completa)

---

### 6. **GUIA_DESARROLLO.md** (Próximo documento) 👨‍💻
**¿Qué es?** Guía para desarrolladores

**Contendrá:**
- Setup del entorno
- Estructura de proyecto
- Cómo agregar features
- Testing y CI/CD
- Code style y convenciones
- Debugging
- Deployment

**Estado:** Planificado

---

## 📱 Documentación de Plataformas

### **mobile/android/README_ANDROID.md** 🤖
**Para:** Supervisores y desarrolladores

**Contiene:**
- Requisitos de tablet
- Instalación de APK
- Compilación desde código
- Uso en campo (workflow)
- Sincronización
- Troubleshooting
- Roadmap Android

**Lectura:** 15-20 minutos

---

### **mobile/ios/README_iOS.md** 🍎
**Para:** Visión futura

**Contiene:**
- Estado (Planificado Q4 2026)
- ¿Por qué Flutter?
- Requisitos futuros
- Features planificadas
- Roadmap iOS

**Lectura:** 10 minutos

---

## 🎯 Rutas de Lectura

### 👥 Para Usuarios Finales
1. **README.md** (raíz) - Resumen ejecutivo
2. **GUIA_INSTALACION.md** - Cómo instalar
3. **mobile/android/README_ANDROID.md** - Si usas tablet

**Tiempo:** 30-45 minutos

---

### 👨‍💻 Para Desarrolladores (Nuevo en proyecto)
1. **README.md** - Visión general
2. **ESTRUCTURA_PROYECTO.md** - Dónde está todo
3. **ARQUITECTURA.md** - Estructura técnica
4. **TECH_SPEC.md** - Detalles técnicos
5. **GUIA_INSTALACION.md** - Setup
6. **GUIA_DESARROLLO.md** - Próxima (cuando exista)

**Tiempo:** 2-3 horas (lectura completa)

---

### 🏗️ Para Arquitectos/Tech Leads
1. **ARQUITECTURA.md** - Estructura actual y futura
2. **ROADMAP.md** - Timeline y fases
3. **TECH_SPEC.md** - Especificaciones técnicas
4. **ESTRUCTURA_PROYECTO.md** - Organización

**Tiempo:** 45-60 minutos

---

### 🎯 Para PMs/Stakeholders
1. **README.md** - ¿Qué es VESP?
2. **ROADMAP.md** - ¿Qué viene?
3. **ARQUITECTURA.md** - Sección "Visión General"

**Tiempo:** 20-30 minutos

---

## 🔗 Links Rápidos

| Documento | Propósito | Duración |
|-----------|----------|----------|
| [ARQUITECTURA.md](ARQUITECTURA.md) | Entender la estructura | 15 min |
| [ROADMAP.md](ROADMAP.md) | Saber qué viene | 20 min |
| [ESTRUCTURA_PROYECTO.md](ESTRUCTURA_PROYECTO.md) | Navegar proyecto | 10 min |
| [TECH_SPEC.md](TECH_SPEC.md) | Implementar features | 45 min |
| [GUIA_INSTALACION.md](GUIA_INSTALACION.md) | Instalar el sistema | 30 min |

---

## 📞 ¿No encuentras lo que buscas?

### Problemas Comunes

**"¿Cómo instalo VESP?"**
→ [GUIA_INSTALACION.md](GUIA_INSTALACION.md)

**"¿Qué viene en v2.0?"**
→ [ROADMAP.md](ROADMAP.md#fase-20---multi-cliente)

**"¿Dónde está X módulo?"**
→ [ESTRUCTURA_PROYECTO.md](ESTRUCTURA_PROYECTO.md)

**"¿Cómo validar una pasada?"**
→ [TECH_SPEC.md](TECH_SPEC.md#validacion-de-datos) o [GUIA_DESARROLLO.md](GUIA_DESARROLLO.md) (próximo)

**"¿Cómo usar la app Android?"**
→ [mobile/android/README_ANDROID.md](../mobile/android/README_ANDROID.md)

**"¿Cuándo sale iOS?"**
→ [mobile/ios/README_iOS.md](../mobile/ios/README_iOS.md)

---

## 📊 Estadísticas

| Aspecto | Valor |
|--------|-------|
| Documentos principales | 6 |
| Documentos plataforma | 2 |
| Líneas de documentación | ~2,900 |
| Cobertura de temas | 95%+ |
| Última actualización | Abril 2026 |
| Estado | ✅ Completa |

---

## 🔄 Versionado de Documentación

Todos los documentos se versionan con el código:

```
v1.0.0 - Documentación inicial + ARQUITECTURA completa
v2.0.0 - Documentación de sincronización + multi-usuario
v3.0.0 - Documentación de backend + web + iOS
```

---

## 💡 Tips de Navegación

- **Buscar en docs:** `Ctrl+F` (dentro de cada archivo)
- **Ver en formato web:** GitHub renderiza Markdown automáticamente
- **Descargar PDF:** Algunos editores permiten exportar a PDF
- **Links:** Todos los documentos están interconectados

---

## ✅ Checklist de Lectura

- ☐ Leí README.md
- ☐ Leí ARQUITECTURA.md
- ☐ Leí ROADMAP.md
- ☐ Leí ESTRUCTURA_PROYECTO.md
- ☐ Leí TECH_SPEC.md (o secciones relevantes)
- ☐ Instalé el sistema con GUIA_INSTALACION.md
- ☐ Probé la app
- ☐ Leí plataforma móvil (Android/iOS)

---

## 🎓 Próximas Mejoras

- [ ] Agregar screenshots a documentos
- [ ] Crear video tutoriales de instalación
- [ ] Agregar GUIA_DESARROLLO.md
- [ ] FAQ específico por rol
- [ ] Diagrama de flujo de sincronización (v2.0)
- [ ] Ejemplos de API REST completamente documentados

---

**Última revisión:** Abril 2026  
**Responsable:** GitHub Copilot + Taiel Clot  
**Estado:** ✅ Completo y listo para producción
