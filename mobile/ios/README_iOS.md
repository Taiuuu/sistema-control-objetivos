# 🍎 VESP Control - iOS Edition
## App nativa para supervisores en iPhones/iPads

**Versión:** Planificado  
**Tecnología:** Flutter  
**Plataforma:** iOS 11.0+  
**Estado:** 🟡 Planificado para Q4 2026

---

## ℹ️ Estado Actual

**iOS aún no está disponible.** Esta documentación describe la versión futura.

### Timeline
- **v1.0:** Android (Kivy) - ✅ Disponible ahora
- **v2.0:** Mejoras Android - Q2-Q3 2026
- **v3.0:** iOS (Flutter) - Q4 2026

---

## 🎯 ¿Por qué Flutter para iOS?

**Flutter ofrece:**
- ✅ Interfaz nativa iOS
- ✅ Performance excelente
- ✅ Código compartido con Android (futuro)
- ✅ Fácil actualización
- ✅ Soporte de Apple

**Comparativas:**
| Aspecto | React Native | Swift | Flutter |
|--------|-------------|-------|---------|
| Nativa | 80% | 100% | 95% |
| Performance | Buena | Excelente | Excelente |
| Desarrollo | Rápido | Lento | Rápido |
| Equipo | Mediano | Grande | Mediano |

**Conclusión:** Flutter es el mejor balance.

---

## 📋 Requisitos (Cuando esté disponible)

### iPhone/iPad
- iOS 11.0 o superior
- iPhone 6S o superior
- 100 MB de almacenamiento libre

### Compilación (Para desarrolladores)
- macOS 10.15+
- Xcode 12+
- Flutter SDK 2.0+
- CocoaPods

---

## 📥 Instalación (Cuando esté disponible)

### App Store
1. Abrir App Store
2. Buscar "VESP Control"
3. Tocar "Descargar"
4. Instalar

### TestFlight (Beta)
1. Recibir invite de VESP
2. Abrir en dispositivo
3. Tocar "Aceptar"
4. Instalar desde TestFlight

### Compilar Localmente
```bash
# Clonar repositorio
git clone https://github.com/Taiuuu/sistema-control-objetivos.git
cd mobile/ios

# Instalar dependencias
flutter pub get

# Compilar
flutter build ios --release

# Instalar en dispositivo
flutter install
```

---

## 🎯 Características Planificadas

### ✅ Base (igual a Android)
- ✅ Login seguro
- ✅ Registro de pasadas
- ✅ Selección de objetivos
- ✅ Selector de turno
- ✅ Notas/observaciones
- ✅ Offline-first

### 🟡 iOS Específicas
- 📋 Interfaz Cupertino (iOS standard)
- 📋 Soporte para Face ID / Touch ID
- 📋 Siri Shortcuts (futuro)
- 📋 Notificaciones con sonido
- 📋 Share Sheet integration
- 📋 Dark Mode nativo

### 🔵 Futuro (v3.0+)
- 📋 Push notifications
- 📋 GPS tracking
- 📋 Fotos adjuntas
- 📋 Apple Watch app
- 📋 CloudKit sync

---

## 💻 Estructura del Proyecto

```
mobile/ios/
├── flutter/               # App Flutter
│   ├── lib/
│   │   ├── main.dart      # Entry point
│   │   ├── screens/       # Pantallas
│   │   ├── services/      # Servicios
│   │   ├── models/        # Modelos
│   │   └── widgets/       # Componentes
│   ├── pubspec.yaml       # Dependencias
│   └── ios/               # Configuración nativa
├── buildozer/             # Configs nativas
└── README_iOS.md          # Este archivo
```

---

## 🔧 Desarrollo (Cuando esté disponible)

### Requisitos
```bash
# macOS + Xcode
brew install flutter

# Verificar
flutter doctor

# Instalar dependencias
cd mobile/ios
flutter pub get
```

### Estructura de carpetas

```
lib/
├── main.dart                    # Punto de entrada
├── screens/
│   ├── login_screen.dart        # Login
│   ├── main_screen.dart         # Pantalla principal
│   └── pasadas_screen.dart      # Historial
├── services/
│   ├── sync_service.dart        # Sincronización
│   ├── api_service.dart         # API calls
│   └── storage_service.dart     # Almacenamiento local
├── models/
│   ├── usuario.dart             # Usuario
│   ├── pasada.dart              # Pasada
│   └── objetivo.dart            # Objetivo
└── widgets/
    ├── custom_button.dart       # Botones
    └── custom_input.dart        # Inputs
```

### Compilación

```bash
# Debug
flutter run

# Release
flutter build ios --release

# Build para App Store
flutter build ipa --release

# Analizar código
flutter analyze

# Tests
flutter test
```

---

## 📱 UI/UX iOS

### Design System
- **Fuente:** SF Pro Display (sistema iOS)
- **Colores:** Modo claro y oscuro automático
- **Espaciado:** Múltiplos de 8px
- **Iconos:** SF Symbols de Apple

### Pantallas

#### Login
```
[Logo VESP]

Usuario: [_____________]
Contraseña: [_____________]

[Iniciar sesión]
```

#### Principal
```
[Objetivos ▼]
[Turno: diurno ▼]

[Notas...]

[REGISTRAR PASADA]

--- Historial ---
08:30 Centro Comercial
14:15 Banco Central
```

---

## 🔐 Seguridad iOS

✅ **Keychain:** Para credenciales  
✅ **Biometría:** Face ID / Touch ID  
✅ **Encriptación:** AES-256 local  
✅ **HTTPS:** Para comunicación  
✅ **App Sandbox:** Datos aislados  

---

## 🧪 Testing (Cuando esté disponible)

```bash
# Unit tests
flutter test

# Integration tests
flutter drive --target=test_driver/app.dart

# Coverage
flutter test --coverage
lcov --list coverage/lcov.info
```

---

## 📦 Distribución

### App Store
1. Crear cuenta developer de Apple
2. Generar certificados
3. Build para producción
4. Submitir a App Store
5. Revisor de Apple (2-5 días)
6. Publicar

### TestFlight
1. Upload a TestFlight
2. Agregar testers
3. Reciben link de instalación
4. Feedback antes de lanzamiento

---

## 📞 Soporte (Futuro)

**Cuando iOS esté disponible:**
- App Store: Reseñas y support
- GitHub Issues: Bug reports
- Email: soporte@vesp.com.ar
- Forum: Comunidad (futuro)

---

## 🔄 Roadmap iOS

```
Q4 2026: Lanzamiento inicial
├─ Login y autenticación
├─ Registro de pasadas
└─ Sincronización

Q1 2027: Mejoras
├─ Face ID / Touch ID
├─ Notificaciones
└─ Mejor UI

Q2 2027: Avanzado
├─ GPS tracking
├─ Fotos
└─ Apple Watch
```

---

## ⚠️ Notas Importantes

1. **iOS requiere Mac:** No se puede compilar en Windows
2. **Certificados:** Necesarios para App Store
3. **Código-signing:** Obligatorio para distribuir
4. **Testing:** iPhone real o simulator
5. **Updates:** Requieren revisión de Apple (tiempo variable)

---

## 📚 Referencias

- [Flutter Docs](https://flutter.dev)
- [Apple iOS Dev](https://developer.apple.com/ios)
- [Flutter for iOS](https://flutter.dev/docs/deployment/ios)
- [Swift UI](https://developer.apple.com/xcode/swiftui)

---

## ❓ Preguntas Frecuentes

**P: ¿Cuándo sale iOS?**  
R: Planificado para Q4 2026 (octubre-diciembre)

**P: ¿Costará dinero?**  
R: Gratis, igual que Android

**P: ¿Los datos se syncronizan entre iPhone y Android?**  
R: Sí, a través del servidor central (v2.0+)

**P: ¿Qué pasa si tengo iPhone 5?**  
R: No es compatible (requiere iOS 11+)

**P: ¿Puedo usar sin WiFi?**  
R: Sí, sincroniza cuando hay conexión

---

## 📝 Para Desarrolladores

**Si quieres contribuir a iOS:**

1. Fork del repositorio
2. Clonar rama `develop`
3. Crear rama: `feature/ios-xxx`
4. Hacer cambios
5. Tests deben pasar
6. Pull request

**Stack requerido:**
- Flutter 2.0+
- Dart 2.12+
- macOS 10.15+
- Xcode 12+

---

**Versión:** Planificado  
**Última actualización:** Abril 2026  
**Próximo release:** Q4 2026  
**Estado:** 🟡 En planificación
