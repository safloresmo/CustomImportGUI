# Changelog - Custom Import GUI

## Version 1.1.0 - Metadatos Personalizados y Correcciones

### Nuevas Características

#### 📝 Sistema de Metadatos Automáticos
- ✅ Todos los componentes importados incluyen metadatos personalizados
- ✅ Campos añadidos a cada símbolo:
  - `ImportedBy`: CustomImportGUI v1.1.0
  - `Author`: Samuel Flores
  - `Repository`: github.com/safloresmo/CustomImportGUI
  - `Website`: www.mictlanteam.com
  - `ImportDate`: Fecha de importación
  - `OriginalSource`: Fuente original (EasyEDA, Snapeda, etc.)
- ✅ Metadatos ocultos en esquemático pero visibles en propiedades
- ✅ Trazabilidad completa de componentes importados

#### 🔧 Correcciones de Bugs
- ✅ **Bug crítico EasyEDA:** Las importaciones desde EasyEDA/LCSC ahora respetan el perfil seleccionado
  - Antes: Creaba librería separada "EasyEDA.kicad_sym"
  - Ahora: Usa el nombre del perfil activo (ej: "MictlanTeam.kicad_sym")
- ✅ Corregida variable de entorno en importaciones EasyEDA
  - Antes: Usaba hardcoded `${KICAD_3RD_PARTY}`
  - Ahora: Usa la variable del perfil configurado

#### 🎨 Mejoras de Interfaz
- ✅ Descripción del plugin mejorada en Plugin Manager
- ✅ Información más clara sobre funcionalidades

### Archivos Modificados

1. **`impart_action.py` (líneas 1031-1036)**
   - Corregido ImportConfig para EasyEDA para usar configuración del perfil

2. **`KiCadImport/__init__.py`**
   - Añadida función `_add_custom_metadata()` (líneas 504-558)
   - Integración de metadatos antes de guardar símbolos (línea 856)

3. **`impart_easyeda.py`**
   - Añadida función `_add_metadata_to_symbol()` (líneas 180-232)
   - Integración de metadatos en importaciones EasyEDA (línea 242)

4. **`plugin.json`**
   - Actualizada descripción para mejor visualización en PCM

5. **`metadata.json`**
   - Actualizada versión a 1.1.0

### Documentación

- ✅ README.md actualizado con:
  - Nueva sección de Metadatos de Componentes
  - Características actualizadas
  - Sistema de perfiles documentado

### Beneficios de Esta Versión

1. **Trazabilidad Completa:**
   - Identifica origen de cada componente
   - Fecha de importación registrada
   - Información de contacto disponible

2. **Consistencia:**
   - Todas las importaciones usan el mismo perfil
   - No más librerías separadas inesperadas

3. **Profesionalismo:**
   - Componentes con metadatos organizados
   - Información de autoría clara

### Migración desde v1.0.0

No se requiere migración. Los componentes importados con v1.0.0 seguirán funcionando normalmente. Los nuevos componentes incluirán automáticamente los metadatos.

---

## Version 1.0.0 - Transformación a Custom Import GUI

### Cambios Principales

#### 🌍 Sistema de Internacionalización (i18n)
- ✅ Creado módulo `i18n.py` con soporte completo de traducciones
- ✅ Archivos de traducción en `locales/`:
  - `es_ES.json` - Español (idioma por defecto)
  - `en_US.json` - Inglés
- ✅ Detección automática del idioma del sistema
- ✅ Función de traducción `_()` para uso sencillo

#### 🎨 Personalización Total
- ✅ Valores por defecto genéricos en `ConfigHandler`:
  - Librería: `CustomLibrary` (antes: `MictlanTeam`)
  - Variable: `${CUSTOM_LIBRARY}` (antes: `${MICTLAN_LIBRARY}`)
- ✅ Interfaz GUI con campos editables para:
  - Nombre de librería personalizable
  - Variable de entorno personalizable
- ✅ Los usuarios pueden configurar sus propios nombres sin tocar código

#### 🔧 Correcciones de Código
- ✅ Corregida referencia `ImpartFrontend` → `CustomImportFrontend` en línea 1063
- ✅ Actualizado valor por defecto en `KiCadImport/__main__.py`
- ✅ Todos los archivos principales ya renombrados:
  - `custom_import_action.py`
  - `custom_import_gui.py`
  - `custom_import_easyeda.py`
  - `custom_import_migration.py`

#### 📚 Documentación
- ✅ README.md completamente reescrito:
  - Secciones en español e inglés
  - Instrucciones de instalación detalladas
  - Guía de configuración paso a paso
  - Solución de problemas
  - Estructura del proyecto
- ✅ `.gitignore` creado para archivos temporales y de configuración

#### 🔄 Identificación del Plugin
- ✅ Identificador único: `com.github.safloresmo.customimportgui`
- ✅ Nombre visible: "Custom Import GUI"
- ✅ Descripción actualizada en `plugin.json`

### Archivos Creados
1. `i18n.py` - Sistema de traducciones
2. `locales/es_ES.json` - Traducciones al español
3. `locales/en_US.json` - Traducciones al inglés
4. `README.md` - Documentación completa
5. `.gitignore` - Exclusiones de git
6. `CHANGELOG.md` - Este archivo

### Archivos Modificados
1. `ConfigHandler/__init__.py` - Valores por defecto genéricos
2. `KiCadImport/__main__.py` - Variable por defecto
3. `custom_import_action.py` - Corrección de nombre de clase
4. `plugin.json` - Ya actualizado con nueva identidad

### Próximos Pasos Sugeridos

#### Integración de i18n (Opcional - Para fase 2)
El sistema de traducción está listo pero no integrado aún en la GUI. Para integrarlo:

1. **En `custom_import_action.py`:**
   ```python
   from i18n import get_i18n, _

   # Ejemplo de uso:
   self.backend.print_to_buffer(_("messages.initial_warning"))
   ```

2. **En `custom_import_gui.py`:**
   ```python
   from i18n import get_i18n, _

   # Cambiar textos hardcodeados por:
   self.m_button.Label = _("gui.start_button")
   ```

3. **Ventajas de integrar:**
   - Interfaz completamente traducible
   - Fácil agregar más idiomas
   - Mensajes consistentes

4. **Sin integrar (estado actual):**
   - El plugin funciona perfectamente
   - Los textos están en inglés en el código
   - Los usuarios pueden personalizar librería y variable

### Estado del Proyecto

✅ **Plugin Funcional y Personalizable**
- El plugin está listo para usar
- Usuarios pueden configurar su propia librería
- Coexiste con el plugin original
- Documentación completa en español e inglés

🚀 **Listo para Producción**
- Todos los archivos renombrados correctamente
- Valores por defecto genéricos
- Identificador único
- Sin conflictos con plugin original

📝 **Opcional: Traducción de GUI**
- Sistema i18n está implementado
- Archivos de traducción creados
- Integración en GUI pendiente (no crítico)

### Cómo Usar el Plugin

1. **Instalación:**
   ```bash
   git clone https://github.com/safloresmo/CustomImportGUI.git
   cd CustomImportGUI
   git submodule update --init --recursive
   ```

2. **Copiar a KiCad:**
   - Windows: `%APPDATA%\kicad\8.0\3rdparty\plugins\CustomImportGUI`

3. **Primera ejecución:**
   - Configura nombre de librería (ej: "MiProyecto")
   - Configura variable de entorno (ej: "${MI_PROYECTO}")
   - Configura rutas de origen y destino

4. **En KiCad:**
   - Preferencias → Configurar Rutas
   - Agregar variable: `MI_PROYECTO` → ruta de tu librería
   - Reiniciar KiCad

### Compatibilidad

- ✅ KiCad 8.0+
- ✅ Python 3.x (incluido en KiCad)
- ✅ Windows, Linux, macOS
- ✅ Coexiste con plugin original

### Licencia

MIT License - Ver archivo LICENSE

### Créditos

- Desarrollado por: Samuel Flores
- Basado en: Import-LIB-KiCad-Plugin por Steffen-W
- Utiliza: easyeda2kicad, kiutils

---

## Notas de Desarrollo

### Estructura de Configuración

El sistema de configuración tiene 3 niveles:

1. **Valores por defecto (código):**
   - `ConfigHandler/__init__.py`: `CustomLibrary`, `${CUSTOM_LIBRARY}`

2. **Configuración del usuario (`config.ini`):**
   - Se guarda automáticamente al cambiar valores en GUI
   - Persiste entre sesiones

3. **GUI en tiempo real:**
   - Usuario puede cambiar en cualquier momento
   - Se actualiza inmediatamente en el backend

### Sistema de Traducciones

```python
# Uso básico
from i18n import _

# Texto simple
mensaje = _("gui.window_title")

# Con parámetros
error = _("messages.import_error", error="File not found")

# Cambiar idioma
from i18n import get_i18n
get_i18n().set_language("en_US")
```

### Agregar Nuevas Traducciones

1. Crear archivo `locales/CODIGO.json` (ej: `fr_FR.json`)
2. Copiar estructura de `es_ES.json`
3. Traducir todos los textos
4. El sistema lo detectará automáticamente

---

## Feedback y Contribuciones

- Issues: https://github.com/safloresmo/CustomImportGUI/issues
- Pull Requests: Bienvenidos
- Discusiones: GitHub Discussions
