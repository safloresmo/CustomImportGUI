# Instrucciones para Crear un Release

Este documento explica cómo crear un release del plugin Custom Import GUI para que los usuarios puedan instalarlo fácilmente desde el Plugin and Content Manager (PCM) de KiCad.

## Requisitos Previos

- Tener Python 3.x instalado
- Tener git configurado
- Tener acceso de escritura al repositorio en GitHub

## ⚠️ IMPORTANTE: Diferencia entre ZIP de GitHub y ZIP del Plugin

### ZIP de GitHub (❌ NO SIRVE para PCM)
Cuando haces "Code" → "Download ZIP" en GitHub:
- Descarga el código fuente directamente
- **NO incluye submódulos** (easyeda2kicad, kiutils)
- **NO tiene la estructura correcta** para KiCad PCM
- **NO se puede instalar** con "Install from File..."

### ZIP del Plugin (✅ SÍ SIRVE para PCM)
El que generamos con `generate_zip.py`:
- Incluye **TODOS los submódulos**
- Tiene la **estructura correcta** (`plugins/` como raíz)
- **Se puede instalar** en KiCad PCM
- Lo **subes manualmente** al release

**Por eso es CRÍTICO seguir estos pasos correctamente.**

---

## Pasos para Crear un Release

### 1. Preparar el Release

Antes de crear el release, asegúrate de que:

- ✅ Todos los cambios estén committed
- ✅ Los submódulos estén actualizados (`git submodule update --init --recursive`)
- ✅ El código esté probado y funcionando
- ✅ El archivo `metadata.json` tenga la versión correcta
- ✅ El archivo `plugin.json` esté actualizado

### 2. Generar el Archivo ZIP

Ejecuta el script de generación:

```bash
cd c:\Users\Samuel\Documents\GitHub\CustomImportGUI
python generate_zip.py
```

Responde `s` cuando pregunte si quieres actualizar `metadata.json`.

El script creará:
- `CustomImportGUI-v1.0.0.zip` (o la versión que tengas configurada)
- Actualizará automáticamente `metadata.json` con el SHA256 y tamaños

**Salida esperada:**
```
============================================================
  Custom Import GUI - Generador de Paquete PCM
============================================================

[*] Creando CustomImportGUI-v1.0.0.zip...
[*] Version: 1.0.0

[*] Añadiendo archivos principales...
  + Añadiendo: __init__.py
  + Añadiendo: custom_import_action.py
  ...

[OK] Archivo creado exitosamente!
[*] Informacion del paquete:
   Nombre: CustomImportGUI-v1.0.0.zip
   Tamanio: 175,474 bytes (0.17 MB)
   SHA256: 9afb085267d3e24482f640f1ec816c881c5f356f928d310b83dfb6ebdae75036
```

### 3. Verificar el Archivo ZIP

**Importante:** Prueba el ZIP en KiCad antes de publicar:

1. Abre KiCad
2. Ve a Plugin and Content Manager
3. Haz clic en "Install from File..."
4. Selecciona `CustomImportGUI-v1.0.0.zip`
5. Verifica que se instale correctamente
6. Prueba las funciones básicas del plugin

### 4. Commit y Push de los Cambios

```bash
git add metadata.json
git commit -m "Release v1.0.0: Update metadata with package info"
git push origin main
```

### 5. Crear el Tag

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 6. Crear el Release en GitHub

#### Opción A: Desde la Web (Recomendado)

1. Ve a tu repositorio en GitHub: https://github.com/safloresmo/CustomImportGUI
2. Haz clic en **"Releases"** (derecha)
3. Haz clic en **"Draft a new release"**
4. Completa la información:

   **Choose a tag:** `v1.0.0` (debe coincidir con el tag que creaste)

   **Release title:** `Custom Import GUI v1.0.0`

   **Descripción:**
   ```markdown
   ## Custom Import GUI v1.0.0

   Primer release oficial del plugin Custom Import GUI para KiCad 8.0+

   ### Características

   - ✨ Completamente personalizable (nombre de librería y variables)
   - 🌍 Soporte multiidioma (Español e Inglés)
   - 📦 Importación desde múltiples fuentes:
     - EasyEDA / LCSC
     - Octopart
     - Samacsys
     - Ultralibrarian
     - Snapeda
   - 🔄 Importación automática o manual
   - 🎯 Drag & drop de archivos ZIP

   ### Instalación

   1. Descarga el archivo `CustomImportGUI-v1.0.0.zip`
   2. Abre KiCad → Plugin and Content Manager
   3. Haz clic en "Install from File..."
   4. Selecciona el archivo ZIP descargado

   ### Documentación

   - [README completo](https://github.com/safloresmo/CustomImportGUI#readme)
   - [Instrucciones de configuración](https://github.com/safloresmo/CustomImportGUI#configuración-inicial)

   ### Requisitos

   - KiCad 8.0 o superior
   - Python 3.x (incluido con KiCad)

   ---

   **Basado en:** [Import-LIB-KiCad-Plugin](https://github.com/Steffen-W/Import-LIB-KiCad-Plugin)
   ```

5. **⚠️ IMPORTANTE - Adjuntar archivo manualmente:**
   - Arrastra y suelta `CustomImportGUI-v1.0.0.zip` en la sección "Attach binaries"
   - O usa el botón para seleccionar el archivo desde tu computadora

   **NOTA CRÍTICA:**
   - NO uses el ZIP que GitHub genera automáticamente
   - DEBES subir el ZIP que generaste con `generate_zip.py`
   - Este es el archivo que está en tu carpeta local del proyecto

6. **Verificar URL:**
   - Asegúrate de que la URL del archivo sea:
   - `https://github.com/safloresmo/CustomImportGUI/releases/download/v1.0.0/CustomImportGUI-v1.0.0.zip`
   - Esta debe coincidir con la URL en `metadata.json`

7. Haz clic en **"Publish release"**

   **Después de publicar:**
   - GitHub mostrará dos archivos ZIP:
     - ✅ `CustomImportGUI-v1.0.0.zip` (el que subiste manualmente) ← **Este es el correcto**
     - ❌ `Source code (zip)` (generado automáticamente por GitHub) ← **Este NO sirve**
   - Los usuarios deben descargar el primero

#### Opción B: Desde la Línea de Comandos (con gh CLI)

Si tienes instalado GitHub CLI:

```bash
gh release create v1.0.0 \
  CustomImportGUI-v1.0.0.zip \
  --title "Custom Import GUI v1.0.0" \
  --notes-file RELEASE_NOTES.md
```

### 7. Verificar el Release

Después de publicar:

1. ✅ Verifica que el archivo ZIP esté disponible en la página de releases
2. ✅ Verifica que la URL del release coincida con `metadata.json`
3. ✅ Descarga el ZIP desde GitHub y pruébalo en KiCad
4. ✅ Verifica que el SHA256 coincida:
   ```bash
   certutil -hashfile CustomImportGUI-v1.0.0.zip SHA256
   ```

## Actualizar a una Nueva Versión

### 1. Actualizar el Número de Versión

Edita `metadata.json` y cambia el número de versión:

```json
{
  "versions": [
    {
      "version": "1.1.0",  // <-- Cambiar aquí
      "status": "stable",
      ...
    }
  ]
}
```

### 2. Actualizar el CHANGELOG

Edita `CHANGELOG.md` y agrega una nueva sección:

```markdown
## Version 1.1.0 - Nuevas Características

### Cambios

- Nueva característica 1
- Corrección de bug 2
- Mejora 3
```

### 3. Generar Nuevo ZIP

```bash
python generate_zip.py
```

### 4. Repetir los Pasos 4-7

Crear el nuevo tag, commit, y release siguiendo los pasos anteriores.

## Solución de Problemas

### Error: "El archivo no contiene un archivo .json de metadatos válido"

**Causa:** El `metadata.json` no está incluido en el ZIP o tiene errores de sintaxis.

**Solución:**
1. Verifica que `metadata.json` esté en la lista de `INCLUDE_FILES` en `generate_zip.py`
2. Valida el JSON: https://jsonlint.com/
3. Regenera el ZIP

### Error: SHA256 no coincide

**Causa:** El archivo fue modificado después de calcular el hash.

**Solución:**
1. Regenera el ZIP con `python generate_zip.py`
2. Responde `s` para actualizar `metadata.json`
3. Commit el `metadata.json` actualizado
4. Vuelve a subir el archivo al release

### El plugin no se instala en KiCad

**Causa:** Estructura incorrecta del ZIP.

**Solución:**
1. Verifica que el ZIP contenga la carpeta `plugins/`
2. Dentro debe estar todo el código
3. Estructura correcta:
   ```
   CustomImportGUI-v1.0.0.zip
   └── plugins/
       ├── __init__.py
       ├── custom_import_action.py
       ├── plugin.json
       ├── metadata.json
       ├── locales/
       └── ...
   ```

## Checklist Final

Antes de publicar un release:

- [ ] Código probado y funcionando
- [ ] Versión actualizada en `metadata.json`
- [ ] `CHANGELOG.md` actualizado
- [ ] ZIP generado con `generate_zip.py`
- [ ] ZIP probado en KiCad
- [ ] `metadata.json` committed con info correcta
- [ ] Tag creado y pusheado
- [ ] Release creado en GitHub
- [ ] Archivo ZIP adjunto al release
- [ ] URL del release verificada
- [ ] SHA256 verificado
- [ ] Descarga desde GitHub probada

## Recursos

- [KiCad PCM Schema](https://go.kicad.org/pcm/schemas/v1)
- [GitHub Releases Docs](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)

---

**Nota:** Guarda este archivo en tu repositorio para referencia futura.
