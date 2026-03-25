"""
Backend handler for the import plugin.
Manages core components, file monitoring, and library checking.
"""

import os
import sys
import logging
from pathlib import Path
from time import sleep
from typing import Any

# Setup imports
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

try:
    from .FileHandler import FileHandler
    from .KiCad_Settings import KiCad_Settings
    from .ConfigHandler import ConfigHandler
    from .KiCadImport import LibImporter
    from .KiCadSettingsPaths import KiCadApp
    from .ImportHistory import ImportHistory
    from .i18n import _ as tr
except ImportError:
    from FileHandler import FileHandler
    from KiCad_Settings import KiCad_Settings
    from ConfigHandler import ConfigHandler
    from KiCadImport import LibImporter
    from KiCadSettingsPaths import KiCadApp
    from ImportHistory import ImportHistory
    from i18n import _ as tr


class ImpartBackend:
    """Backend handler for the import plugin."""

    SUPPORTED_LIBRARIES = [
        "Octopart",
        "Samacsys",
        "UltraLibrarian",
        "Snapeda",
        "EasyEDA",
    ]

    def __init__(self) -> None:
        logging.info("Initializing ImpartBackend")

        self.config_path = os.path.join(os.path.dirname(__file__), "config.ini")

        try:
            self.kicad_app = KiCadApp(prefer_ipc=True, min_version="8.0.4")
            self.config = ConfigHandler(self.config_path)
            self.kicad_settings = KiCad_Settings(self.kicad_app.settings_path)

            self.folder_handler = FileHandler(
                ".", min_size=1_000, max_size=50_000_000, file_extension=".zip"
            )

            self.importer = LibImporter()
            self.importer.print = lambda txt: self.print_to_buffer(txt)
            self.importer.set_library_name(self.config.get_library_name())
            self.importer.KICAD_3RD_PARTY_LINK = self.config.get_library_variable()
            self.importer.set_DEST_PATH(self.config.get_DEST_PATH())

            self.history = ImportHistory()
            self.importer.on_import_success = self._on_import_success

            logging.info("Successfully initialized all backend components")
            logging.info(f"KiCad settings path: {self.kicad_settings.SettingPath}")

        except Exception as e:
            logging.exception("Failed to initialize backend components")
            raise

        self.run_thread = False
        self.auto_import = False
        self.overwrite_import = False
        self.import_old_format = False
        self.local_lib = False
        self.auto_lib = True
        self.print_buffer = ""

        try:
            self.kicad_app.check_min_version(output_func=self.print_to_buffer)
        except Exception as e:
            logging.warning(f"Failed to check KiCad version: {e}")

        if not self.config.config_is_set:
            self._print_initial_warnings()

    def _print_initial_warnings(self) -> None:
        try:
            warning_msg = tr("messages.initial_warning")
            info_msg = tr("messages.initial_info")
        except Exception:
            warning_msg = "Warning: Library path not configured yet."
            info_msg = "Settings are checked after import. Enable auto setting for easy setup."

        self.print_to_buffer(warning_msg)
        self.print_to_buffer(info_msg)
        self.print_to_buffer("\n" + "=" * 50 + "\n")

    def _on_import_success(self, component_name: str, source: str, zip_file: str) -> None:
        self.history.add_entry(
            component_name=component_name,
            source=source,
            library_name=self.config.get_library_name(),
            zip_file=os.path.basename(zip_file),
            profile=self.config.get_current_profile(),
        )

    def print_to_buffer(self, *args: Any) -> None:
        for text in args:
            self.print_buffer += str(text) + "\n"

    def find_and_import_new_files(self) -> None:
        src_path = self.config.get_SRC_PATH()

        if not os.path.isdir(src_path):
            self.print_to_buffer(f"Source path does not exist: {src_path}")
            return

        while True:
            new_files = self.folder_handler.get_new_files(src_path)

            for lib_file in new_files:
                self._import_single_file(lib_file)

            if not self.run_thread:
                break
            sleep(1)

    def _import_single_file(self, lib_file: str) -> None:
        try:
            lib_path = Path(lib_file)
            result = self.importer.import_all(
                lib_path,
                overwrite_if_exists=self.overwrite_import,
                import_old_format=self.import_old_format,
            )
            if result and len(result) > 0:
                self.print_to_buffer(result[0])

        except AssertionError as e:
            self.print_to_buffer(f"Assertion Error: {e}")
        except Exception as e:
            error_msg = f"Import Error: {e}\nPython version: {sys.version}"
            self.print_to_buffer(error_msg)
            logging.exception("Import failed")
        finally:
            self.print_to_buffer("")


def check_library_import(backend: ImpartBackend, add_if_possible: bool = True) -> str:
    """Check and potentially add libraries to KiCad settings."""
    msg = ""

    if backend.local_lib:
        project_dir = backend.kicad_app.get_project_dir()
        if not project_dir:
            return "\nLocal library mode enabled but no KiCad project available."

        try:
            kicad_settings = KiCad_Settings(str(project_dir), path_prefix="${KIPRJMOD}")
            dest_path = project_dir
            logging.info("Project-specific library check completed")
        except Exception as e:
            logging.error(f"Failed to read project settings: {e}")
            return "\nCould not read project library settings."
    else:
        kicad_settings = backend.kicad_settings
        dest_path = backend.config.get_DEST_PATH()
        lib_var = backend.config.get_library_variable()
        msg = kicad_settings.check_GlobalVar(dest_path, add_if_possible, var_name=lib_var)

    for lib_name in ImpartBackend.SUPPORTED_LIBRARIES:
        msg += _check_single_library(
            kicad_settings, lib_name, dest_path, add_if_possible
        )

    return msg


def _check_single_library(
    kicad_settings: KiCad_Settings,
    lib_name: str,
    dest_path: str,
    add_if_possible: bool,
) -> str:
    msg = ""

    symbol_variants = [
        f"{lib_name}.kicad_sym",
        f"{lib_name}_kicad_sym.kicad_sym",
        f"{lib_name}_old_lib.kicad_sym",
    ]

    for variant in symbol_variants:
        if os.path.isfile(os.path.join(dest_path, variant)):
            msg += kicad_settings.check_symbollib(variant, add_if_possible)
            break

    if os.path.isdir(os.path.join(dest_path, f"{lib_name}.pretty")):
        msg += kicad_settings.check_footprintlib(lib_name, add_if_possible)

    return msg


def create_backend_handler():
    """Create a new backend handler instance."""
    try:
        backend = ImpartBackend()
        logging.info("Created new backend handler")
        return backend
    except Exception as e:
        logging.exception("Failed to create backend handler")
        raise
