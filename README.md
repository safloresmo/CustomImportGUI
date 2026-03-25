# Custom Import GUI

**[Español](#español) | [English](#english)**

---


## Español

### Descripción

**Custom Import GUI** es un plugin totalmente personalizable para KiCad que permite importar librerías de componentes desde múltiples fuentes a tu propia estructura de librerías personalizada.

### Características Principales

✨ **Interfaz con Pestañas**
- Importar, Buscar, Configuración, Librería, Design Blocks, Historial
- Tema oscuro compatible con KiCad 10
- Ventana redimensionable

🔍 **Búsqueda Integrada**
- Búsqueda JLCPCB/LCSC con imágenes y precios en tiempo real
- Búsqueda en librerías oficiales de KiCad (GitLab)
- Detección de componentes ya importados
- Importación directa desde resultados de búsqueda

📦 **Múltiples Fuentes**
- EasyEDA / LCSC (importación por lotes)
- KiCad Official (GitLab)
- Octopart, Samacsys, Ultralibrarian, Snapeda (vía ZIP)

📚 **Gestión de Librerías**
- Sub-librerías organizadas por categoría (automático o manual)
- Mover, copiar, editar y eliminar componentes
- Filtro de búsqueda en la pestaña Librería
- Crear nuevas librerías desde el plugin

🧩 **Design Blocks (KiCad 10)**
- Importar esquemáticos como bloques reutilizables
- Crear, editar metadatos y eliminar bloques
- Registro automático en KiCad

🔄 **Importación Flexible**
- Importación manual o automática
- Arrastra y suelta archivos ZIP
- Importación por lotes (múltiples IDs separados por coma)
- Librería global o por proyecto

👤 **Perfiles de Configuración**
- Múltiples perfiles con diferentes librerías y rutas
- Exportar e importar perfiles (JSON)
- Cambio rápido entre perfiles

📝 **Metadatos y Trazabilidad**
- Metadatos automáticos en cada componente importado
- Historial completo de importaciones
- Verificación de actualizaciones desde GitHub

🌍 **Multiidioma**
- Español e Inglés
- Detección automática del idioma del sistema

### Requisitos

- KiCad 8.0 - 10.x (compatible con KiCad 10)
- Python 3.x (incluido con KiCad)

### Instalación

#### Opción 1: Instalación desde PCM (Recomendado)

1. **Descargar el plugin:**
   - Ve a [Releases](https://github.com/safloresmo/CustomImportGUI/releases)
   - Descarga el archivo `CustomImportGUI-v1.3.0.zip`

2. **Instalar en KiCad:**
   - Abre KiCad
   - Ve a **Plugin and Content Manager** (PCM)
   - Haz clic en **"Install from File..."**
   - Selecciona el archivo ZIP descargado

#### Opción 2: Instalación Manual (Desarrolladores)

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/safloresmo/CustomImportGUI.git
   cd CustomImportGUI
   git submodule update --init --recursive
   ```

2. **Instalar en KiCad:**
   - Copia la carpeta `Origen/` al directorio de plugins de KiCad:
   - Windows: `%APPDATA%\kicad\<version>\3rdparty\plugins\CustomImportGUI\`
   - Linux: `~/.local/share/kicad/<version>/3rdparty/plugins/CustomImportGUI/`
   - macOS: `~/Library/Application Support/kicad/<version>/3rdparty/plugins/CustomImportGUI/`

### Uso

#### Búsqueda de Componentes

1. Ve a la pestaña **Buscar**
2. Selecciona la fuente: **JLCPCB/LCSC** o **KiCad Oficial**
3. Escribe el nombre o ID del componente
4. Haz clic en el resultado para ver detalles e imagen
5. Presiona **Importar Seleccionado**

#### Importación por Lotes

1. En la pestaña **Importar**, sección EasyEDA
2. Escribe múltiples IDs separados por coma: `C2040, C14663, C82899`
3. Presiona **Importar Manual**

#### Sub-librerías por Categoría

1. Ve a **Configuración** → activa **Organizar por categoría**
2. Los nuevos componentes se organizarán automáticamente
3. O usa **Reorganizar Todo por Categoría** en la pestaña Librería

#### Design Blocks

1. Ve a la pestaña **Bloques de Diseño**
2. Presiona **Importar Esquemático** para crear un bloque desde un `.kicad_sch`
3. Los bloques aparecerán en el panel Design Blocks de KiCad

### Estructura del Proyecto

```
Origen/
├── impart_action.py              # Punto de entrada y GUI principal
├── impart_backend.py             # Backend: importación y monitoreo
├── impart_frontend_search.py     # Pestaña búsqueda JLCPCB
├── impart_frontend_kicad_search.py # Búsqueda KiCad GitLab
├── impart_frontend_library.py    # Pestaña librería y sub-librerías
├── impart_frontend_profile.py    # Gestión de perfiles
├── impart_frontend_blocks.py     # Pestaña design blocks
├── impart_easyeda.py             # Importador EasyEDA
├── update_checker.py             # Verificación de actualizaciones
├── version.py                    # Versión dinámica
├── i18n.py                       # Sistema de traducción
├── ComponentSearch/              # Búsqueda JLCPCB/LCSC
├── KiCadGitLab/                  # Búsqueda KiCad GitLab
├── DesignBlocks/                 # Gestión de design blocks
├── ImportHistory/                # Historial de importaciones
├── ConfigHandler/                # Configuración y perfiles
├── KiCadImport/                  # Motor de importación
├── KiCad_Settings/               # Configuración de KiCad
├── locales/                      # Traducciones (es_ES, en_US)
└── tests/                        # Tests automatizados (101 tests)
```

### Solución de Problemas

#### El plugin no aparece en KiCad
- Verifica que los submódulos estén inicializados
- Revisa `plugin.log` en la carpeta del plugin

#### Las sub-librerías no aparecen
- Reinicia KiCad completamente después de reorganizar
- KiCad lee las tablas de librerías solo al iniciar

#### Error "KICAD_3RD_PARTY not defined"
- Activa **configuración automática de KiCad** en la pestaña Configuración
- O agrega la variable manualmente en Preferencias → Configurar Rutas

### Licencia

Este proyecto está bajo la Licencia GPL-3.0. Ver el archivo `LICENSE` para más detalles.

### Créditos

- Desarrollado por: **Samuel Flores**
- Basado en el trabajo original de Steffen-W
- Utiliza [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) para importación de EasyEDA
- Utiliza [kiutils](https://github.com/mvnmgrx/kiutils) para manipulación de archivos de KiCad

---

## English

### Description

**Custom Import GUI** is a fully customizable KiCad plugin that allows you to import component libraries from multiple sources into your own custom library structure.

### Key Features

✨ **Tabbed Interface**
- Import, Search, Configuration, Library, Design Blocks, History
- Dark theme compatible with KiCad 10
- Resizable window

🔍 **Integrated Search**
- JLCPCB/LCSC search with real-time images and pricing
- KiCad official library search (GitLab)
- Duplicate detection for already-imported components
- Direct import from search results

📦 **Multiple Sources**
- EasyEDA / LCSC (batch import)
- KiCad Official (GitLab)
- Octopart, Samacsys, Ultralibrarian, Snapeda (via ZIP)

📚 **Library Management**
- Sub-libraries organized by category (automatic or manual)
- Move, copy, edit, and delete components
- Search filter in Library tab
- Create new libraries from the plugin

🧩 **Design Blocks (KiCad 10)**
- Import schematics as reusable blocks
- Create, edit metadata, and delete blocks
- Automatic registration in KiCad

🔄 **Flexible Import**
- Manual or automatic import
- Drag and drop ZIP files
- Batch import (multiple IDs separated by comma)
- Global or project-specific library

👤 **Configuration Profiles**
- Multiple profiles with different libraries and paths
- Export and import profiles (JSON)
- Quick switching between profiles

📝 **Metadata & Traceability**
- Automatic metadata on every imported component
- Complete import history
- GitHub update checking

🌍 **Multi-language**
- Spanish and English
- Automatic system language detection

### Requirements

- KiCad 8.0 - 10.x (compatible with KiCad 10)
- Python 3.x (included with KiCad)

### Installation

#### Option 1: Install from PCM (Recommended)

1. **Download the plugin:**
   - Go to [Releases](https://github.com/safloresmo/CustomImportGUI/releases)
   - Download `CustomImportGUI-v1.3.0.zip`

2. **Install in KiCad:**
   - Open KiCad
   - Go to **Plugin and Content Manager** (PCM)
   - Click **"Install from File..."**
   - Select the downloaded ZIP file

#### Option 2: Manual Installation (Developers)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/safloresmo/CustomImportGUI.git
   cd CustomImportGUI
   git submodule update --init --recursive
   ```

2. **Install in KiCad:**
   - Copy the `Origen/` folder to your KiCad plugins directory:
   - Windows: `%APPDATA%\kicad\<version>\3rdparty\plugins\CustomImportGUI\`
   - Linux: `~/.local/share/kicad/<version>/3rdparty/plugins/CustomImportGUI/`
   - macOS: `~/Library/Application Support/kicad/<version>/3rdparty/plugins/CustomImportGUI/`

### Usage

#### Component Search

1. Go to the **Search** tab
2. Select source: **JLCPCB/LCSC** or **KiCad Official**
3. Type the component name or ID
4. Click a result to see details and image
5. Press **Import Selected**

#### Batch Import

1. In the **Import** tab, EasyEDA section
2. Type multiple IDs separated by comma: `C2040, C14663, C82899`
3. Press **Manual Import**

#### Sub-libraries by Category

1. Go to **Configuration** → enable **Organize by category**
2. New components will be automatically organized
3. Or use **Reorganize All by Category** in the Library tab

#### Design Blocks

1. Go to the **Design Blocks** tab
2. Press **Import Schematic** to create a block from a `.kicad_sch`
3. Blocks will appear in KiCad's Design Blocks panel

### License

This project is licensed under the GPL-3.0 License. See the `LICENSE` file for details.

### Credits

- Developed by: **Samuel Flores**
- Based on original work by Steffen-W
- Uses [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) for EasyEDA import
- Uses [kiutils](https://github.com/mvnmgrx/kiutils) for KiCad file manipulation

---

## Soporte / Support

- **Issues:** [GitHub Issues](https://github.com/safloresmo/CustomImportGUI/issues)
- **Email:** Contact via GitHub
- **Original Plugin:** [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin)
