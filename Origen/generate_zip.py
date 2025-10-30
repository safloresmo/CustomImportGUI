#!/usr/bin/env python3
"""
Script para generar el paquete ZIP del plugin Custom Import GUI para KiCad PCM
"""

import zipfile
import json
import hashlib
from pathlib import Path

def get_version():
    """Lee la versión del metadata.json"""
    with open('metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        return metadata['versions'][0]['version']

# Archivos principales a incluir
INCLUDE_FILES = [
    '__init__.py',
    '__main__.py',
    'impart_action.py',
    'impart_gui.py',
    'impart_easyeda.py',
    'impart_migration.py',
    'single_instance_manager.py',
    'plugin.json',
    'icon.png',
    'requirements.txt',
]

# Carpetas a incluir
INCLUDE_FOLDERS = [
    'ConfigHandler',
    'FileHandler',
    'KiCad_Settings',
    'KiCadImport',
    'KiCadSettingsPaths',
    'kicad_cli',
    'easyeda2kicad',
    'kiutils',
]

# Archivos y patrones a excluir
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.pyc',
    '.pyo',
    '.git',
    '.gitignore',
    'config.ini',
    '.log',
    'generate_zip.py',
    'metadata.json',
]

def should_exclude(filepath):
    """Verifica si un archivo debe ser excluido"""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return True
    return False

def add_folder_to_zip(zipf, folder_path, arcname_base):
    """Añade una carpeta completa al ZIP recursivamente"""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"[!] Carpeta no encontrada: {folder_path}")
        return

    for item in folder.rglob('*'):
        if item.is_file() and not should_exclude(item):
            arcname = Path(arcname_base) / item.relative_to(folder)
            zipf.write(item, arcname)

def calculate_sha256(filepath):
    """Calcula el SHA256 de un archivo"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_plugin_zip():
    """Crea el archivo ZIP del plugin"""
    version = get_version()
    zip_filename = f'CustomImportGUI-v{version}.zip'

    print("=" * 60)
    print("  Custom Import GUI - Generador de Paquete PCM")
    print("=" * 60)
    print(f"\n[*] Creando {zip_filename}...")
    print(f"[*] Version: {version}\n")

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Añadir metadata.json en la raíz
        print("[*] Añadiendo metadata.json en la raiz...")
        if Path('metadata.json').exists():
            zipf.write('metadata.json', 'metadata.json')
            print("  + metadata.json (raiz)")

        # Añadir icon.png en resources/
        print("[*] Añadiendo icon.png en resources/...")
        if Path('icon.png').exists():
            zipf.write('icon.png', 'resources/icon.png')
            print("  + resources/icon.png")

        # Añadir archivos individuales dentro de plugins/
        print("\n[*] Añadiendo archivos principales...")
        for filename in INCLUDE_FILES:
            filepath = Path(filename)
            if filepath.exists():
                print(f"  + {filename}")
                zipf.write(filepath, f'plugins/{filename}')
            else:
                print(f"  ! WARNING: {filename} no encontrado")

        # Añadir carpetas
        print("\n[*] Añadiendo carpetas...")
        for folder in INCLUDE_FOLDERS:
            if Path(folder).exists():
                print(f"  + {folder}/")
                add_folder_to_zip(zipf, folder, f'plugins/{folder}')

    # Calcular información del archivo
    zip_path = Path(zip_filename)
    file_size = zip_path.stat().st_size
    file_sha256 = calculate_sha256(zip_path)

    print("\n[OK] Archivo creado exitosamente!")
    print(f"\n[*] Informacion del paquete:")
    print(f"   Nombre: {zip_filename}")
    print(f"   Tamaño: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"   SHA256: {file_sha256}")

    print(f"\n[*] Para instalar en KiCad:")
    print(f"   1. Abre KiCad")
    print(f"   2. Ve a Plugin and Content Manager")
    print(f"   3. Haz clic en 'Install from File...'")
    print(f"   4. Selecciona {zip_filename}")

    return zip_filename, file_size, file_sha256

if __name__ == '__main__':
    create_plugin_zip()
