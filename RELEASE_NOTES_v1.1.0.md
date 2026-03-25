# Custom Import GUI v1.1.0

Segunda versión oficial del plugin Custom Import GUI para KiCad 8.0+ con metadatos personalizados y correcciones importantes.

## ⭐ Nuevas Características

### 📝 Sistema de Metadatos Automáticos

Todos los componentes importados ahora incluyen **metadatos personalizados automáticos** que permiten trazabilidad completa:

- **ImportedBy**: CustomImportGUI v1.1.0
- **Author**: Samuel Flores
- **Repository**: github.com/safloresmo/CustomImportGUI
- **Website**: www.mictlanteam.com
- **ImportDate**: Fecha de importación
- **OriginalSource**: Fuente original (EasyEDA, Snapeda, etc.)

Los metadatos están **ocultos en el esquemático** pero son **visibles en las propiedades del símbolo**, permitiendo:
- ✅ Rastrear el origen de cada componente
- ✅ Identificar cuándo fue importado
- ✅ Mantener la trazabilidad en proyectos
- ✅ Contactar al autor para soporte

## 🐛 Correcciones Importantes

### Bug Crítico: Importaciones EasyEDA/LCSC

**Problema anterior (v1.0.0):**
- Las importaciones desde EasyEDA/LCSC creaban librerías separadas con nombre "EasyEDA"
- No respetaban el perfil seleccionado
- Usaban variable de entorno hardcoded `${KICAD_3RD_PARTY}`

**Solución (v1.1.0):**
- ✅ Ahora respeta completamente el perfil seleccionado
- ✅ Usa el nombre de librería configurado (ej: "MictlanTeam", "CustomLibrary")
- ✅ Usa la variable de entorno del perfil activo
- ✅ Consistencia total con importaciones manuales

### Mejoras de Interfaz

- ✅ Descripción mejorada del plugin en Plugin Manager
- ✅ Información más detallada sobre funcionalidades

## 📦 Características Completas

✨ **Completamente Personalizable**
- Elige tu propio nombre de librería
- Define tus propias variables de entorno
- Sistema de perfiles predefinidos (MictlanTeam, CustomLibrary)

🌍 **Multiidioma**
- Interfaz en español por defecto
- Soporte para inglés

📦 **Múltiples Fuentes**
- EasyEDA / LCSC (**ahora con perfil correcto**)
- Octopart
- Samacsys
- Ultralibrarian
- Snapeda

🔄 **Importación Flexible**
- Importación automática o manual
- Drag & drop de archivos ZIP
- Librería global o por proyecto

📝 **Metadatos Automáticos** (**NUEVO**)
- Todos los componentes incluyen información de autoría
- Trazabilidad completa
- Metadatos ocultos en esquemático

## 📥 Instalación

### Opción 1: Plugin and Content Manager (Recomendado)

1. **Descarga** el archivo [`CustomImportGUI-v1.1.0.zip`](https://github.com/safloresmo/CustomImportGUI/releases/download/v1.1.0/CustomImportGUI-v1.1.0.zip)
2. Abre **KiCad**
3. Ve a **Plugin and Content Manager** (PCM)
4. Haz clic en **"Install from File..."**
5. Selecciona el archivo ZIP descargado
6. ¡Listo!

### Opción 2: Instalación Manual (Desarrolladores)

```bash
git clone https://github.com/safloresmo/CustomImportGUI.git
cd CustomImportGUI
git submodule update --init --recursive
```

Copia la carpeta a tu directorio de plugins de KiCad:
- Windows: `%APPDATA%\kicad\8.0\3rdparty\plugins\CustomImportGUI\`
- Linux: `~/.local/share/kicad/8.0/3rdparty/plugins/CustomImportGUI/`
- macOS: `~/Library/Application Support/kicad/8.0/3rdparty/plugins/CustomImportGUI/`

## 🔄 Migración desde v1.0.0

**No se requiere migración.** Los componentes importados con v1.0.0 seguirán funcionando normalmente. Los nuevos componentes importados con v1.1.0 incluirán automáticamente los metadatos.

## 📋 Requisitos

- KiCad 8.0 o superior
- Python 3.x (incluido con KiCad)

## 📚 Documentación

- [README completo](https://github.com/safloresmo/CustomImportGUI#readme)
- [Configuración inicial](https://github.com/safloresmo/CustomImportGUI#configuración-inicial)
- [Metadatos de componentes](https://github.com/safloresmo/CustomImportGUI#metadatos-de-componentes)
- [CHANGELOG](https://github.com/safloresmo/CustomImportGUI/blob/main/CHANGELOG.md)

## 📝 Información del Paquete

- **Versión**: 1.1.0
- **Tamaño**: 179,293 bytes (0.17 MB)
- **SHA256**: `0230de1c870e884404a62b6f2a186b8a5f765aaf55f13591caec3e5165bb76e8`

## 🙏 Créditos

- **Desarrollado por**: Samuel Flores
- **Basado en**: [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin) por Steffen-W
- **Utiliza**: [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) y [kiutils](https://github.com/mvnmgrx/kiutils)

## 🐛 Soporte

- **Issues**: [GitHub Issues](https://github.com/safloresmo/CustomImportGUI/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/safloresmo/CustomImportGUI/discussions)

---

**Español** | [English](#english-version)

---

# English Version

# Custom Import GUI v1.1.0

Second official release of the Custom Import GUI plugin for KiCad 8.0+ with custom metadata and important fixes.

## ⭐ New Features

### 📝 Automatic Metadata System

All imported components now include **automatic custom metadata** for complete traceability:

- **ImportedBy**: CustomImportGUI v1.1.0
- **Author**: Samuel Flores
- **Repository**: github.com/safloresmo/CustomImportGUI
- **Website**: www.mictlanteam.com
- **ImportDate**: Import date
- **OriginalSource**: Original source (EasyEDA, Snapeda, etc.)

Metadata is **hidden in schematics** but **visible in symbol properties**, allowing you to:
- ✅ Track the origin of each component
- ✅ Identify when it was imported
- ✅ Maintain traceability in projects
- ✅ Contact the author for support

## 🐛 Important Fixes

### Critical Bug: EasyEDA/LCSC Imports

**Previous problem (v1.0.0):**
- EasyEDA/LCSC imports created separate libraries named "EasyEDA"
- Did not respect the selected profile
- Used hardcoded environment variable `${KICAD_3RD_PARTY}`

**Solution (v1.1.0):**
- ✅ Now fully respects the selected profile
- ✅ Uses the configured library name (e.g., "MictlanTeam", "CustomLibrary")
- ✅ Uses the active profile's environment variable
- ✅ Total consistency with manual imports

### Interface Improvements

- ✅ Improved plugin description in Plugin Manager
- ✅ More detailed information about features

## 📦 Complete Features

✨ **Fully Customizable**
- Choose your own library name
- Define your own environment variables
- Predefined profile system (MictlanTeam, CustomLibrary)

🌍 **Multi-language**
- Spanish interface by default
- English support

📦 **Multiple Sources**
- EasyEDA / LCSC (**now with correct profile**)
- Octopart
- Samacsys
- Ultralibrarian
- Snapeda

🔄 **Flexible Import**
- Automatic or manual import
- Drag & drop ZIP files
- Global or project-specific library

📝 **Automatic Metadata** (**NEW**)
- All components include authorship information
- Complete traceability
- Hidden metadata in schematics

## 📥 Installation

### Option 1: Plugin and Content Manager (Recommended)

1. **Download** the file [`CustomImportGUI-v1.1.0.zip`](https://github.com/safloresmo/CustomImportGUI/releases/download/v1.1.0/CustomImportGUI-v1.1.0.zip)
2. Open **KiCad**
3. Go to **Plugin and Content Manager** (PCM)
4. Click **"Install from File..."**
5. Select the downloaded ZIP file
6. Done!

### Option 2: Manual Installation (Developers)

```bash
git clone https://github.com/safloresmo/CustomImportGUI.git
cd CustomImportGUI
git submodule update --init --recursive
```

Copy the folder to your KiCad plugins directory:
- Windows: `%APPDATA%\kicad\8.0\3rdparty\plugins\CustomImportGUI\`
- Linux: `~/.local/share/kicad/8.0/3rdparty/plugins/CustomImportGUI/`
- macOS: `~/Library/Application Support/kicad/8.0/3rdparty/plugins/CustomImportGUI/`

## 🔄 Migration from v1.0.0

**No migration required.** Components imported with v1.0.0 will continue to work normally. New components imported with v1.1.0 will automatically include the metadata.

## 📋 Requirements

- KiCad 8.0 or higher
- Python 3.x (included with KiCad)

## 📚 Documentation

- [Complete README](https://github.com/safloresmo/CustomImportGUI#readme)
- [Initial setup](https://github.com/safloresmo/CustomImportGUI#initial-setup)
- [Component metadata](https://github.com/safloresmo/CustomImportGUI#component-metadata)
- [CHANGELOG](https://github.com/safloresmo/CustomImportGUI/blob/main/CHANGELOG.md)

## 📝 Package Information

- **Version**: 1.1.0
- **Size**: 179,293 bytes (0.17 MB)
- **SHA256**: `0230de1c870e884404a62b6f2a186b8a5f765aaf55f13591caec3e5165bb76e8`

## 🙏 Credits

- **Developed by**: Samuel Flores
- **Based on**: [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin) by Steffen-W
- **Uses**: [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) and [kiutils](https://github.com/mvnmgrx/kiutils)

## 🐛 Support

- **Issues**: [GitHub Issues](https://github.com/safloresmo/CustomImportGUI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/safloresmo/CustomImportGUI/discussions)
