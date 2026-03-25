# Custom Import GUI

**[Español](#español) | [English](#english)**

---


## Español

### Descripción

**Custom Import GUI** es un plugin totalmente personalizable para KiCad que permite importar librerías de componentes desde múltiples fuentes (EasyEDA, LCSC, Octopart, Samacsys, Ultralibrarian, Snapeda) a tu propia estructura de librerías personalizada.

### Características Principales

✨ **Completamente Personalizable**
- Elige tu propio nombre de librería
- Define tus propias variables de entorno
- Organiza los componentes a tu manera
- Sistema de perfiles predefinidos (MictlanTeam, CustomLibrary)

🌍 **Multiidioma**
- Interfaz en español por defecto
- Soporte para inglés
- Fácil de agregar más idiomas

📦 **Múltiples Fuentes**
- EasyEDA / LCSC
- Octopart
- Samacsys
- Ultralibrarian
- Snapeda

🔄 **Importación Flexible**
- Importación manual o automática
- Arrastra y suelta archivos ZIP
- Librería global o por proyecto

📝 **Metadatos Automáticos**
- Todos los componentes incluyen metadatos personalizados
- Información de autor, repositorio y fecha de importación
- Trazabilidad completa de componentes importados

### Requisitos

- KiCad 8.0 - 10.x (compatible con KiCad 10)
- Python 3.x (incluido con KiCad)

> **Nota:** Los bindings SWIG de KiCad fueron deprecados en KiCad 9 y se eliminarán en KiCad 11. Este plugin ya soporta la API IPC como alternativa.

### Instalación

#### Opción 1: Instalación desde PCM (Recomendado)

1. **Descargar el plugin:**
   - Ve a [Releases](https://github.com/safloresmo/CustomImportGUI/releases)
   - Descarga el archivo `CustomImportGUI-v1.2.0.zip`

2. **Instalar en KiCad:**
   - Abre KiCad
   - Ve a **Plugin and Content Manager** (PCM)
   - Haz clic en **"Install from File..."**
   - Selecciona el archivo ZIP descargado
   - ¡Listo! El plugin se instalará automáticamente

#### Opción 2: Instalación Manual (Desarrolladores)

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/safloresmo/CustomImportGUI.git
   cd CustomImportGUI
   ```

2. **Inicializar submódulos:**
   ```bash
   git submodule update --init --recursive
   ```

3. **Instalar en KiCad:**
   - Copia la carpeta completa a tu directorio de plugins de KiCad
   - En Windows: `%APPDATA%\kicad\<version>\3rdparty\plugins\CustomImportGUI\` (ej: `8.0`, `9.0`, `10.0`)
   - En Linux: `~/.local/share/kicad/<version>/3rdparty/plugins/CustomImportGUI/`
   - En macOS: `~/Library/Application Support/kicad/<version>/3rdparty/plugins/CustomImportGUI/`

### Configuración Inicial

Al ejecutar el plugin por primera vez:

1. **Nombre de Librería:** Elige un nombre para tu librería (ej: "MiProyecto", "Electronica", etc.)
   - Por defecto: `CustomLibrary`

2. **Variable de Entorno:** Define la variable de entorno de KiCad (ej: "${MI_PROYECTO}")
   - Por defecto: `${CUSTOM_LIBRARY}`

3. **Rutas:**
   - **Ruta de origen:** Carpeta donde se descargan los archivos ZIP (por defecto: `~/Downloads`)
   - **Ruta de librería:** Carpeta destino para las librerías (por defecto: `~/KiCad`)

### Uso

#### Importación Automática

1. Activa "Importación automática"
2. El plugin monitoreará la carpeta de origen
3. Importará automáticamente nuevos archivos ZIP

#### Importación Manual

1. Descarga el archivo ZIP del componente
2. Arrastra y suelta en la ventana del plugin
3. O coloca el archivo en la carpeta de origen y presiona "Iniciar"

#### Importación desde EasyEDA/LCSC

1. Copia el ID del componente (ej: C2040)
2. Pégalo en el campo "Manual EasyEDA/LCSC import"
3. Presiona el botón de importación

### Metadatos de Componentes

Todos los componentes importados incluyen automáticamente los siguientes metadatos personalizados (ocultos en el esquemático, visibles en las propiedades del símbolo):

- **ImportedBy:** CustomImportGUI v1.2.0
- **Author:** Samuel Flores
- **Repository:** github.com/safloresmo/CustomImportGUI
- **Website:** www.mictlanteam.com
- **ImportDate:** Fecha de importación
- **OriginalSource:** Fuente original del componente (EasyEDA, Snapeda, etc.)

Estos metadatos te permiten:
- Rastrear el origen de cada componente
- Identificar cuándo fue importado
- Mantener la trazabilidad en tus proyectos
- Contactar al autor para soporte

### Configuración de Variables de Entorno

Para que KiCad reconozca tu librería personalizada:

1. **Abre KiCad → Preferencias → Configurar Rutas**

2. **Agrega una nueva variable:**
   - Nombre: `CUSTOM_LIBRARY` (o tu variable personalizada)
   - Ruta: La ruta donde guardaste tus librerías

3. **Reinicia KiCad** para aplicar los cambios

### Estructura de Archivos

```
CustomImportGUI/
├── custom_import_action.py       # Acción principal del plugin
├── custom_import_gui.py           # Interfaz gráfica
├── custom_import_easyeda.py       # Importador de EasyEDA
├── i18n.py                        # Sistema de traducción
├── plugin.json                    # Configuración del plugin
├── config.ini                     # Configuración del usuario
├── locales/                       # Traducciones
│   ├── es_ES.json                # Español
│   └── en_US.json                # Inglés
├── ConfigHandler/                 # Manejador de configuración
├── KiCadImport/                   # Módulo de importación
├── FileHandler/                   # Manejador de archivos
└── ...
```

### Solución de Problemas

#### El plugin no aparece en KiCad
- Verifica que los submódulos estén inicializados: `git submodule update --init --recursive`
- Revisa el archivo `plugin.log` en la carpeta del plugin

#### Error al importar componentes
- Asegúrate de que la variable de entorno esté configurada correctamente
- Verifica que las rutas de origen y destino existan
- Revisa los permisos de escritura en la carpeta destino

#### Las librerías no aparecen en KiCad
- Activa "Auto-configurar librería" en el plugin
- O agrega las librerías manualmente en KiCad:
  - **Símbolos:** Preferencias → Gestionar librerías de símbolos
  - **Huellas:** Preferencias → Gestionar librerías de huellas

### Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

### Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

### Créditos

- Desarrollado por: Samuel Flores
- Basado en el trabajo original de Steffen-W
- Utiliza [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) para importación de EasyEDA
- Utiliza [kiutils](https://github.com/mvnmgrx/kiutils) para manipulación de archivos de KiCad

---

## English

### Description

**Custom Import GUI** is a fully customizable KiCad plugin that allows you to import component libraries from multiple sources (EasyEDA, LCSC, Octopart, Samacsys, Ultralibrarian, Snapeda) into your own custom library structure.

### Key Features

✨ **Fully Customizable**
- Choose your own library name
- Define your own environment variables
- Organize components your way
- Predefined profile system (MictlanTeam, CustomLibrary)

🌍 **Multi-language**
- Spanish interface by default
- English support
- Easy to add more languages

📦 **Multiple Sources**
- EasyEDA / LCSC
- Octopart
- Samacsys
- Ultralibrarian
- Snapeda

🔄 **Flexible Import**
- Manual or automatic import
- Drag and drop ZIP files
- Global or project-specific library

📝 **Automatic Metadata**
- All components include custom metadata
- Author, repository, and import date information
- Complete traceability of imported components

### Requirements

- KiCad 8.0 - 10.x (compatible with KiCad 10)
- Python 3.x (included with KiCad)

> **Note:** KiCad's SWIG bindings were deprecated in KiCad 9 and will be removed in KiCad 11. This plugin already supports the IPC API as an alternative.

### Installation

#### Option 1: Install from PCM (Recommended)

1. **Download the plugin:**
   - Go to [Releases](https://github.com/safloresmo/CustomImportGUI/releases)
   - Download the file `CustomImportGUI-v1.2.0.zip`

2. **Install in KiCad:**
   - Open KiCad
   - Go to **Plugin and Content Manager** (PCM)
   - Click **"Install from File..."**
   - Select the downloaded ZIP file
   - Done! The plugin will install automatically

#### Option 2: Manual Installation (Developers)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/safloresmo/CustomImportGUI.git
   cd CustomImportGUI
   ```

2. **Initialize submodules:**
   ```bash
   git submodule update --init --recursive
   ```

3. **Install in KiCad:**
   - Copy the complete folder to your KiCad plugins directory
   - Windows: `%APPDATA%\kicad\<version>\3rdparty\plugins\CustomImportGUI\` (e.g., `8.0`, `9.0`, `10.0`)
   - Linux: `~/.local/share/kicad/<version>/3rdparty/plugins/CustomImportGUI/`
   - macOS: `~/Library/Application Support/kicad/<version>/3rdparty/plugins/CustomImportGUI/`

### Initial Setup

When running the plugin for the first time:

1. **Library Name:** Choose a name for your library (e.g., "MyProject", "Electronics", etc.)
   - Default: `CustomLibrary`

2. **Environment Variable:** Define the KiCad environment variable (e.g., "${MY_PROJECT}")
   - Default: `${CUSTOM_LIBRARY}`

3. **Paths:**
   - **Source path:** Folder where ZIP files are downloaded (default: `~/Downloads`)
   - **Library path:** Destination folder for libraries (default: `~/KiCad`)

### Usage

#### Automatic Import

1. Enable "Auto import"
2. The plugin will monitor the source folder
3. It will automatically import new ZIP files

#### Manual Import

1. Download the component ZIP file
2. Drag and drop into the plugin window
3. Or place the file in the source folder and press "Start"

#### Import from EasyEDA/LCSC

1. Copy the component ID (e.g., C2040)
2. Paste it in the "Manual EasyEDA/LCSC import" field
3. Press the import button

### Component Metadata

All imported components automatically include the following custom metadata (hidden in schematics, visible in symbol properties):

- **ImportedBy:** CustomImportGUI v1.2.0
- **Author:** Samuel Flores
- **Repository:** github.com/safloresmo/CustomImportGUI
- **Website:** www.mictlanteam.com
- **ImportDate:** Import date
- **OriginalSource:** Original component source (EasyEDA, Snapeda, etc.)

These metadata fields allow you to:
- Track the origin of each component
- Identify when it was imported
- Maintain traceability in your projects
- Contact the author for support

### Environment Variable Configuration

For KiCad to recognize your custom library:

1. **Open KiCad → Preferences → Configure Paths**

2. **Add a new variable:**
   - Name: `CUSTOM_LIBRARY` (or your custom variable)
   - Path: The path where you saved your libraries

3. **Restart KiCad** to apply the changes

### File Structure

```
CustomImportGUI/
├── custom_import_action.py       # Main plugin action
├── custom_import_gui.py           # Graphical interface
├── custom_import_easyeda.py       # EasyEDA importer
├── i18n.py                        # Translation system
├── plugin.json                    # Plugin configuration
├── config.ini                     # User configuration
├── locales/                       # Translations
│   ├── es_ES.json                # Spanish
│   └── en_US.json                # English
├── ConfigHandler/                 # Configuration handler
├── KiCadImport/                   # Import module
├── FileHandler/                   # File handler
└── ...
```

### Troubleshooting

#### Plugin doesn't appear in KiCad
- Verify submodules are initialized: `git submodule update --init --recursive`
- Check the `plugin.log` file in the plugin folder

#### Error importing components
- Make sure the environment variable is configured correctly
- Verify that source and destination paths exist
- Check write permissions in the destination folder

#### Libraries don't appear in KiCad
- Enable "Auto-configure library" in the plugin
- Or add libraries manually in KiCad:
  - **Symbols:** Preferences → Manage Symbol Libraries
  - **Footprints:** Preferences → Manage Footprint Libraries

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.

### Credits

- Developed by: Samuel Flores
- Based on original work by Steffen-W
- Uses [easyeda2kicad](https://github.com/uPesy/easyeda2kicad) for EasyEDA import
- Uses [kiutils](https://github.com/mvnmgrx/kiutils) for KiCad file manipulation

---

## Soporte / Support

- **Issues:** [GitHub Issues](https://github.com/safloresmo/CustomImportGUI/issues)
- **Email:** Contact via GitHub
- **Original Plugin:** [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin)