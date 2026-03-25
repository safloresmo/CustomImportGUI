"""
KiCad Import Plugin for library files from various sources.
Supports Octopart, Samacsys, Ultralibrarian, Snapeda and EasyEDA.

This is the main entry point. Business logic is split into:
- impart_backend.py: Backend handler, file monitoring, library checking
- impart_frontend_search.py: Search tab (JLCPCB/LCSC search with images)
- impart_frontend_library.py: Library browser tab (sub-libraries, move/copy/delete)
- impart_frontend_profile.py: Profile management (CRUD, config persistence)
"""

import atexit
import os
import sys
import re
import socket
import logging
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Optional, List, Tuple, Any

# Setup paths for local imports
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def quick_instance_check(port: int = 59999) -> bool:
    """Quick check if another instance is running without logging."""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1.0)
        client_socket.connect(("127.0.0.1", port))
        client_socket.close()
        return True
    except (ConnectionRefusedError, socket.error, OSError):
        return False


if __name__ == "__main__":
    is_new_instance = not quick_instance_check()

    if is_new_instance:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s [%(name)s:%(filename)s:%(lineno)d]: %(message)s",
            filename=script_dir / "plugin.log",
            filemode="w",
        )
        logging.info("New instance started - log file reset")
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format="%(message)s",
            filename=script_dir / "plugin.log",
            filemode="a",
        )
        logging.warning(
            "Another instance detected - exiting or continuing with limited logging"
        )

    logging.debug("Application starting...")

# Import dependencies
try:
    import wx

    logging.info("Successfully imported wx module")
except Exception as e:
    logging.exception("Failed to import wx module")
    raise

try:
    from .impart_gui import impartGUI
    from .KiCad_Settings import KiCad_Settings
    from .KiCadSettingsPaths import KiCadApp
    from .impart_migration import find_old_lib_files, convert_lib_list
    from .single_instance_manager import SingleInstanceManager
    from .ComponentSearch import search_components
    from .i18n import _ as tr, init as i18n_init
    from .impart_backend import ImpartBackend, check_library_import, create_backend_handler
    from .impart_frontend_search import SearchMixin
    from .impart_frontend_library import LibraryMixin
    from .impart_frontend_profile import ProfileMixin
    from .impart_frontend_kicad_search import KiCadSearchMixin
    from .impart_frontend_blocks import DesignBlocksMixin
    from .update_checker import check_for_updates

    logging.info("Successfully imported all local modules using relative imports")

except ImportError as e1:
    try:
        from impart_gui import impartGUI
        from KiCad_Settings import KiCad_Settings
        from KiCadSettingsPaths import KiCadApp
        from impart_migration import find_old_lib_files, convert_lib_list
        from single_instance_manager import SingleInstanceManager
        from ComponentSearch import search_components
        from i18n import _ as tr, init as i18n_init
        from impart_backend import ImpartBackend, check_library_import, create_backend_handler
        from impart_frontend_search import SearchMixin
        from impart_frontend_library import LibraryMixin
        from impart_frontend_profile import ProfileMixin
        from impart_frontend_kicad_search import KiCadSearchMixin
        from impart_frontend_blocks import DesignBlocksMixin
        from update_checker import check_for_updates

        logging.info("Successfully imported all local modules using absolute imports")

    except ImportError as e2:
        logging.exception(
            "Failed to import local modules with both relative and absolute imports"
        )
        print(f"Relative import error: {e1}")
        print(f"Absolute import error: {e2}")
        print(f"Python path: {sys.path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {script_dir}")
        raise e2

# Event handling
EVT_UPDATE_ID = wx.NewIdRef()


def EVT_UPDATE(win: wx.Window, func: Any) -> None:
    """Bind update event to window."""
    win.Connect(-1, -1, EVT_UPDATE_ID, func)


class ResultEvent(wx.PyEvent):
    """Custom event for thread communication."""

    def __init__(self, data: str) -> None:
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_UPDATE_ID)
        self.data = data


class FileDropTarget(wx.FileDropTarget):
    """Drop target for ZIP files on the text control."""

    def __init__(self, window, callback):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.callback = callback

    def OnDropFiles(self, x, y, filenames):
        zip_files = [f for f in filenames if f.lower().endswith(".zip")]

        if zip_files:
            self.callback(zip_files)
            return True
        else:
            wx.MessageBox(
                tr("messages.zip_not_supported"),
                tr("messages.zip_invalid_title"),
                wx.OK | wx.ICON_WARNING,
            )
            return False


class PluginThread(Thread):
    """Background thread for monitoring import status."""

    def __init__(self, wx_object: wx.Window, backend) -> None:
        Thread.__init__(self)
        self.wx_object = wx_object
        self.backend = backend
        self.stop_thread = False
        self.start()

    def run(self) -> None:
        len_str = 0
        while not self.stop_thread:
            current_len = len(self.backend.print_buffer)
            if len_str != current_len:
                self.report(self.backend.print_buffer)
                len_str = current_len
            sleep(0.5)

    def report(self, status: str) -> None:
        wx.PostEvent(self.wx_object, ResultEvent(status))


instance_manager = SingleInstanceManager()
atexit.register(instance_manager.stop_server)


class ImpartFrontend(KiCadSearchMixin, SearchMixin, LibraryMixin, ProfileMixin, DesignBlocksMixin, impartGUI):
    """
    Frontend GUI supporting both IPC singleton and fallback modes.
    Inherits functionality from mixins:
    - SearchMixin: Component search tab
    - LibraryMixin: Library browser tab
    - ProfileMixin: Profile management
    - DesignBlocksMixin: Design Blocks tab
    """

    def __init__(self, fallback_mode: bool = False) -> None:
        super().__init__(None)
        self.fallback_mode = fallback_mode
        self._loading_profile = False

        # Initialize translations
        i18n_init()

        # Log the mode
        if self.fallback_mode:
            logging.info("Running in FALLBACK MODE (called from pcbnew)")
        else:
            logging.info("Running in NORMAL MODE (direct execution)")

        # Register with instance manager only if not in fallback mode
        if not self.fallback_mode:
            if not instance_manager.register_frontend(self):
                logging.warning(
                    "Frontend instance already exists - destroying this one"
                )
                self.Destroy()
                return
        else:
            logging.info("Fallback mode: Skipping IPC server registration")

        # Set window icon
        try:
            icon_path = Path(__file__).resolve().parent / "icon.png"
            if icon_path.exists():
                icon = wx.Icon(str(icon_path), wx.BITMAP_TYPE_PNG)
                self.SetIcon(icon)
        except Exception as e:
            logging.warning(f"Could not set window icon: {e}")

        self.backend = create_backend_handler()
        self.thread: Optional[PluginThread] = None

        self._setup_gui()
        self._enhance_gui()
        self._setup_events()
        self._start_monitoring_thread()
        self._print_initial_paths()

        # Check for plugin updates in the background
        try:
            from .version import __version__ as _current_version
        except ImportError:
            try:
                from version import __version__ as _current_version
            except ImportError:
                _current_version = "0.0.0"
        check_for_updates(_current_version, self._on_update_available)

        # Connect progress callback
        self.backend.importer.on_progress = self._on_progress_update

    def _setup_gui(self) -> None:
        """Initialize GUI components."""
        self.kicad_project = self.backend.kicad_app.get_project_dir()

        self._apply_translations()

        # Set values from config
        self.m_dirPicker_sourcepath.SetPath(self.backend.config.get_SRC_PATH())

        if self.kicad_project:
            self.m_checkBoxLocalLib.Enable(True)

        self.m_dirPicker_librarypath.SetPath(self.backend.config.get_DEST_PATH())
        self.m_check_autoLib.SetValue(True)

        # Add profile controls
        self._add_profile_controls()

        # Configure drag & drop
        self._setup_drag_drop()

    def _apply_translations(self) -> None:
        """Apply translations to base GUI elements."""
        self.SetTitle(tr("gui.window_title"))
        self.m_button.SetLabel(tr("gui.start"))
        self.m_autoImport.SetLabel(tr("gui.auto_import"))
        self.m_overwrite.SetLabel(tr("gui.overwrite"))
        self.m_check_autoLib.SetLabel(tr("gui.auto_config"))
        self.m_staticText_sourcepath.SetLabel(tr("gui.source_path_label"))
        self.m_staticText_librarypath.SetLabel(tr("gui.library_path_label"))
        self.m_checkBoxLocalLib.SetLabel(tr("gui.local_lib"))

    def _enhance_gui(self) -> None:
        """Restructure flat GUI into tabbed layout with modern styling."""

        # --- Style widgets ---
        self.m_button.SetFont(
            wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        )
        self.m_button.SetMinSize(wx.Size(-1, 36))
        self.m_text.SetFont(
            wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )

        # Use system colors for dark theme compatibility
        bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
        fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXTEXT)
        self.m_text.SetBackgroundColour(bg)
        self.m_text.SetForegroundColour(fg)

        self.m_textCtrl2.SetHint("C2040, C14663...")

        # --- Clear main sizer ---
        main_sizer = self.GetSizer()
        if not main_sizer:
            return

        while main_sizer.GetItemCount() > 0:
            main_sizer.Detach(0)

        # === CREATE NOTEBOOK ===
        self.notebook = wx.Notebook(self, wx.ID_ANY)

        # === TAB 1: IMPORT ===
        import_panel = wx.Panel(self.notebook)
        import_sizer = wx.BoxSizer(wx.VERTICAL)

        self.m_button_migrate.Reparent(import_panel)
        import_sizer.Add(self.m_button_migrate, 0, wx.ALL | wx.EXPAND, 5)

        self.m_button.Reparent(import_panel)
        import_sizer.Add(self.m_button, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)

        # Progress bar
        self.m_progress = wx.Gauge(import_panel, wx.ID_ANY, 100, size=wx.Size(-1, 8))
        self.m_progress.Hide()
        import_sizer.Add(self.m_progress, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.m_text.Reparent(import_panel)
        import_sizer.Add(self.m_text, 1, wx.ALL | wx.EXPAND, 5)

        # EasyEDA section
        easyeda_box = wx.StaticBox(import_panel, label="EasyEDA / LCSC Part#")
        easyeda_sizer = wx.StaticBoxSizer(easyeda_box, wx.HORIZONTAL)

        self.m_textCtrl2.Reparent(import_panel)
        easyeda_sizer.Add(self.m_textCtrl2, 1, wx.ALL | wx.EXPAND, 5)

        self.m_buttonImportManual.Reparent(import_panel)
        self.m_buttonImportManual.SetLabel(tr("gui.manual_import"))
        easyeda_sizer.Add(self.m_buttonImportManual, 0, wx.ALL, 5)

        import_sizer.Add(easyeda_sizer, 0, wx.EXPAND | wx.ALL, 5)
        import_panel.SetSizer(import_sizer)

        # === TAB 2: SEARCH ===
        search_panel = wx.Panel(self.notebook)
        search_sizer = wx.BoxSizer(wx.VERTICAL)

        # Source selector (JLCPCB / KiCad Official)
        source_bar = wx.BoxSizer(wx.HORIZONTAL)
        source_lbl = wx.StaticText(search_panel, label="Source:")
        source_bar.Add(source_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.m_search_source = wx.Choice(
            search_panel,
            choices=[tr("messages.search_source_jlcpcb"), tr("messages.search_source_kicad")],
        )
        self.m_search_source.SetSelection(0)
        source_bar.Add(self.m_search_source, 0, wx.ALL, 5)
        search_sizer.Add(source_bar, 0, wx.EXPAND)

        # Search bar
        search_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.m_search_input = wx.TextCtrl(search_panel, style=wx.TE_PROCESS_ENTER)
        self.m_search_input.SetHint(tr("messages.search_hint"))
        self.m_btn_search = wx.Button(search_panel, label=tr("messages.search_button"))
        search_bar.Add(self.m_search_input, 1, wx.ALL | wx.EXPAND, 5)
        search_bar.Add(self.m_btn_search, 0, wx.ALL, 5)
        search_sizer.Add(search_bar, 0, wx.EXPAND)

        # KiCad library filter row (hidden by default, shown when KiCad Official source is selected)
        self.m_kicad_lib_row = wx.BoxSizer(wx.HORIZONTAL)
        kicad_lib_lbl = wx.StaticText(search_panel, label=tr("messages.kicad_search_by_lib"))
        self.m_kicad_lib_row.Add(kicad_lib_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.m_kicad_lib_choice = wx.Choice(search_panel, choices=[tr("messages.kicad_no_lib_selected")])
        self.m_kicad_lib_choice.SetSelection(0)
        self.m_kicad_lib_row.Add(self.m_kicad_lib_choice, 1, wx.ALL | wx.EXPAND, 5)
        search_sizer.Add(self.m_kicad_lib_row, 0, wx.EXPAND)
        self.m_kicad_lib_row.ShowItems(False)

        # Store panel reference for layout calls in KiCadSearchMixin
        self._search_panel_ref = search_panel

        # Status + pagination
        status_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.m_search_status = wx.StaticText(search_panel, label="")
        status_bar.Add(self.m_search_status, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.m_btn_prev = wx.Button(search_panel, label="<", size=wx.Size(30, -1))
        self.m_page_label = wx.StaticText(search_panel, label="1")
        self.m_btn_next = wx.Button(search_panel, label=">", size=wx.Size(30, -1))
        self.m_btn_prev.Enable(False)
        self.m_btn_next.Enable(False)
        status_bar.Add(self.m_btn_prev, 0, wx.ALL, 2)
        status_bar.Add(self.m_page_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        status_bar.Add(self.m_btn_next, 0, wx.ALL, 2)
        search_sizer.Add(status_bar, 0, wx.EXPAND)

        # Results + detail split
        splitter = wx.BoxSizer(wx.HORIZONTAL)

        # Results list
        self.m_search_list = wx.ListCtrl(search_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.m_search_list.InsertColumn(0, "LCSC #", width=80)
        self.m_search_list.InsertColumn(1, tr("messages.search_col_name"), width=180)
        self.m_search_list.InsertColumn(2, tr("messages.search_col_mfr"), width=130)
        self.m_search_list.InsertColumn(3, tr("messages.search_col_package"), width=100)
        self.m_search_list.InsertColumn(4, "Stock", width=60)
        self.m_search_list.InsertColumn(5, tr("messages.search_col_price"), width=80)

        # Use system colors for dark theme
        self.m_search_list.SetBackgroundColour(bg)
        self.m_search_list.SetForegroundColour(fg)

        splitter.Add(self.m_search_list, 3, wx.ALL | wx.EXPAND, 5)

        # Detail panel
        detail_panel = wx.BoxSizer(wx.VERTICAL)
        self.m_search_image = wx.StaticBitmap(search_panel, size=wx.Size(200, 200))
        detail_panel.Add(self.m_search_image, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        self.m_search_detail = wx.TextCtrl(
            search_panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=wx.Size(200, 100)
        )
        self.m_search_detail.SetBackgroundColour(bg)
        self.m_search_detail.SetForegroundColour(fg)
        detail_panel.Add(self.m_search_detail, 1, wx.ALL | wx.EXPAND, 5)

        self.m_search_duplicate = wx.StaticText(search_panel, label="")
        self.m_search_duplicate.SetForegroundColour(wx.Colour(255, 165, 0))
        detail_panel.Add(self.m_search_duplicate, 0, wx.LEFT | wx.RIGHT, 5)

        # Buttons
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.m_btn_search_import = wx.Button(search_panel, label=tr("messages.search_import"))
        self.m_btn_search_import.Enable(False)
        self.m_btn_open_lcsc = wx.Button(search_panel, label="LCSC")
        self.m_btn_open_lcsc.Enable(False)
        btn_row.Add(self.m_btn_search_import, 1, wx.ALL, 5)
        btn_row.Add(self.m_btn_open_lcsc, 0, wx.ALL, 5)
        detail_panel.Add(btn_row, 0, wx.EXPAND)

        splitter.Add(detail_panel, 1, wx.EXPAND)
        search_sizer.Add(splitter, 1, wx.EXPAND)
        search_panel.SetSizer(search_sizer)

        # Search state
        self._search_results = []
        self._search_keyword = ""
        self._search_page = 1
        self._search_page_size = 50

        # Bind search events
        self.m_search_source.Bind(wx.EVT_CHOICE, self._on_search_source_changed)
        self.m_search_input.Bind(wx.EVT_TEXT_ENTER, self._on_search_dispatch)
        self.m_btn_search.Bind(wx.EVT_BUTTON, self._on_search_dispatch)
        self.m_btn_prev.Bind(wx.EVT_BUTTON, self._on_search_prev)
        self.m_btn_next.Bind(wx.EVT_BUTTON, self._on_search_next)
        self.m_search_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_search_select_dispatch)
        self.m_search_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_search_import_dispatch)
        self.m_btn_search_import.Bind(wx.EVT_BUTTON, self._on_search_import_dispatch)
        self.m_btn_open_lcsc.Bind(wx.EVT_BUTTON, self._on_open_lcsc)

        # === TAB 3: CONFIGURATION ===
        config_panel = wx.Panel(self.notebook)
        config_sizer = wx.BoxSizer(wx.VERTICAL)

        # Profile section
        profile_box = wx.StaticBox(config_panel, label=tr("gui.profile_label"))
        profile_box_sizer = wx.StaticBoxSizer(profile_box, wx.VERTICAL)

        profile_row = wx.BoxSizer(wx.HORIZONTAL)
        self.m_choice_profile.Reparent(config_panel)
        profile_row.Add(self.m_choice_profile, 1, wx.ALL, 5)
        self.m_btn_save_profile.Reparent(config_panel)
        profile_row.Add(self.m_btn_save_profile, 0, wx.ALL, 5)
        self.m_btn_delete_profile.Reparent(config_panel)
        profile_row.Add(self.m_btn_delete_profile, 0, wx.ALL, 5)

        self.m_btn_export_profile = wx.Button(config_panel, wx.ID_ANY, tr("gui.export_profile"))
        self.m_btn_export_profile.SetToolTip(tr("gui.export_profile"))
        self.m_btn_export_profile.Bind(wx.EVT_BUTTON, self._on_export_profile)
        profile_row.Add(self.m_btn_export_profile, 0, wx.ALL, 5)

        self.m_btn_import_profile = wx.Button(config_panel, wx.ID_ANY, tr("gui.import_profile"))
        self.m_btn_import_profile.SetToolTip(tr("gui.import_profile"))
        self.m_btn_import_profile.Bind(wx.EVT_BUTTON, self._on_import_profile)
        profile_row.Add(self.m_btn_import_profile, 0, wx.ALL, 5)

        profile_box_sizer.Add(profile_row, 0, wx.EXPAND)
        config_sizer.Add(profile_box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Library section
        lib_box = wx.StaticBox(config_panel, label=tr("gui.library_config_label"))
        lib_box_sizer = wx.StaticBoxSizer(lib_box, wx.VERTICAL)

        lib_row = wx.BoxSizer(wx.HORIZONTAL)
        lib_name_lbl = wx.StaticText(config_panel, label=tr("gui.library_name_label"))
        lib_row.Add(lib_name_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.m_textCtrl_library_name.Reparent(config_panel)
        lib_row.Add(self.m_textCtrl_library_name, 1, wx.ALL | wx.EXPAND, 5)
        env_lbl = wx.StaticText(config_panel, label=tr("gui.env_var_label"))
        lib_row.Add(env_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.m_textCtrl_library_var.Reparent(config_panel)
        lib_row.Add(self.m_textCtrl_library_var, 1, wx.ALL | wx.EXPAND, 5)
        lib_box_sizer.Add(lib_row, 0, wx.EXPAND)
        config_sizer.Add(lib_box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Paths section
        paths_box = wx.StaticBox(config_panel, label=tr("gui.paths_label"))
        paths_sizer = wx.StaticBoxSizer(paths_box, wx.VERTICAL)

        self.m_staticText_sourcepath.Reparent(config_panel)
        paths_sizer.Add(self.m_staticText_sourcepath, 0, wx.LEFT | wx.TOP, 5)
        self.m_dirPicker_sourcepath.Reparent(config_panel)
        paths_sizer.Add(self.m_dirPicker_sourcepath, 0, wx.EXPAND | wx.ALL, 5)

        lib_path_row = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText_librarypath.Reparent(config_panel)
        lib_path_row.Add(self.m_staticText_librarypath, 0, wx.ALL, 5)
        self.m_checkBoxLocalLib.Reparent(config_panel)
        lib_path_row.Add(self.m_checkBoxLocalLib, 0, wx.ALL, 5)
        paths_sizer.Add(lib_path_row, 0)

        self.m_dirPicker_librarypath.Reparent(config_panel)
        paths_sizer.Add(self.m_dirPicker_librarypath, 0, wx.EXPAND | wx.ALL, 5)
        config_sizer.Add(paths_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Options section
        options_box = wx.StaticBox(config_panel, label=tr("gui.options_label"))
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)

        opts_row1 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_autoImport.Reparent(config_panel)
        opts_row1.Add(self.m_autoImport, 0, wx.ALL, 5)
        self.m_overwrite.Reparent(config_panel)
        opts_row1.Add(self.m_overwrite, 0, wx.ALL, 5)
        self.m_check_autoLib.Reparent(config_panel)
        opts_row1.Add(self.m_check_autoLib, 0, wx.ALL, 5)
        options_sizer.Add(opts_row1, 0)

        # Organize by category checkbox
        self.m_check_organize_cat = wx.CheckBox(config_panel, label=tr("messages.library_organize_by_cat"))
        self.m_check_organize_cat.SetToolTip(tr("messages.library_organize_tooltip"))
        self.m_check_organize_cat.SetValue(self.backend.config.get_organize_by_category())
        self.m_check_organize_cat.Bind(wx.EVT_CHECKBOX, self._on_organize_cat_changed)
        options_sizer.Add(self.m_check_organize_cat, 0, wx.ALL, 5)

        config_sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        config_panel.SetSizer(config_sizer)

        # === TAB 4: LIBRARY BROWSER ===
        library_panel = wx.Panel(self.notebook)
        library_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top bar
        lib_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.m_library_status = wx.StaticText(library_panel, label="")
        lib_bar.Add(self.m_library_status, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_btn_new_lib = wx.Button(
            library_panel, wx.ID_ANY, tr("messages.library_new_button")
        )
        self.m_btn_new_lib.Bind(wx.EVT_BUTTON, self._on_create_library)
        lib_bar.Add(self.m_btn_new_lib, 0, wx.ALL, 5)

        self.m_btn_lib_reorganize = wx.Button(
            library_panel, wx.ID_ANY, tr("messages.library_reorganize")
        )
        self.m_btn_lib_reorganize.Bind(wx.EVT_BUTTON, self._on_reorganize_library)
        lib_bar.Add(self.m_btn_lib_reorganize, 0, wx.ALL, 5)

        m_btn_refresh_lib = wx.Button(library_panel, wx.ID_ANY, tr("messages.library_refresh"))
        m_btn_refresh_lib.Bind(wx.EVT_BUTTON, self._on_refresh_library)
        lib_bar.Add(m_btn_refresh_lib, 0, wx.ALL, 5)

        library_sizer.Add(lib_bar, 0, wx.EXPAND)

        # Filter bar
        self.m_library_filter = wx.SearchCtrl(library_panel, style=wx.TE_PROCESS_ENTER)
        self.m_library_filter.SetHint(tr("messages.library_filter_hint"))
        self.m_library_filter.ShowCancelButton(True)
        self.m_library_filter.Bind(wx.EVT_TEXT, self._on_library_filter)
        self.m_library_filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_library_filter_clear)
        library_sizer.Add(self.m_library_filter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Library list
        self.m_library_list = wx.ListCtrl(library_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.m_library_list.InsertColumn(0, tr("messages.library_col_name"), width=160)
        self.m_library_list.InsertColumn(1, "Ref", width=50)
        self.m_library_list.InsertColumn(2, "Sub-lib", width=140)
        self.m_library_list.InsertColumn(3, tr("messages.library_col_footprint"), width=200)
        self.m_library_list.InsertColumn(4, tr("messages.library_col_source"), width=100)
        self.m_library_list.InsertColumn(5, tr("messages.library_col_date"), width=90)

        self.m_library_list.SetBackgroundColour(bg)
        self.m_library_list.SetForegroundColour(fg)
        self.m_library_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_library_right_click)
        self.m_library_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda e: self._on_library_edit(e.GetIndex()))

        library_sizer.Add(self.m_library_list, 1, wx.ALL | wx.EXPAND, 5)
        library_panel.SetSizer(library_sizer)

        # Library state
        self._library_items = []
        self._all_library_items = []
        self._library_count = 0

        # === TAB 5: DESIGN BLOCKS ===
        blocks_panel = wx.Panel(self.notebook)
        blocks_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top bar
        blocks_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.m_blocks_status = wx.StaticText(blocks_panel, label="")
        blocks_bar.Add(self.m_blocks_status, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        m_btn_blocks_import_sch = wx.Button(
            blocks_panel, wx.ID_ANY, tr("messages.blocks_import_sch")
        )
        m_btn_blocks_import_sch.Bind(wx.EVT_BUTTON, self._on_blocks_import_sch)
        blocks_bar.Add(m_btn_blocks_import_sch, 0, wx.ALL, 5)

        m_btn_blocks_new = wx.Button(
            blocks_panel, wx.ID_ANY, tr("messages.blocks_new")
        )
        m_btn_blocks_new.Bind(wx.EVT_BUTTON, self._on_blocks_new)
        blocks_bar.Add(m_btn_blocks_new, 0, wx.ALL, 5)

        m_btn_blocks_refresh = wx.Button(
            blocks_panel, wx.ID_ANY, tr("messages.blocks_refresh")
        )
        m_btn_blocks_refresh.Bind(wx.EVT_BUTTON, self._on_refresh_blocks)
        blocks_bar.Add(m_btn_blocks_refresh, 0, wx.ALL, 5)

        blocks_sizer.Add(blocks_bar, 0, wx.EXPAND)

        # Blocks list
        self.m_blocks_list = wx.ListCtrl(blocks_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.m_blocks_list.InsertColumn(0, tr("messages.blocks_col_name"), width=160)
        self.m_blocks_list.InsertColumn(1, tr("messages.blocks_col_desc"), width=200)
        self.m_blocks_list.InsertColumn(2, tr("messages.blocks_col_keywords"), width=140)
        self.m_blocks_list.InsertColumn(3, tr("messages.blocks_col_sch"), width=80)
        self.m_blocks_list.InsertColumn(4, tr("messages.blocks_col_pcb"), width=80)

        self.m_blocks_list.SetBackgroundColour(bg)
        self.m_blocks_list.SetForegroundColour(fg)
        self.m_blocks_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_blocks_right_click)
        self.m_blocks_list.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            lambda e: self._on_blocks_edit_metadata(
                self._blocks_items[e.GetIndex()]
            ) if 0 <= e.GetIndex() < len(self._blocks_items) else None
        )

        blocks_sizer.Add(self.m_blocks_list, 1, wx.ALL | wx.EXPAND, 5)
        blocks_panel.SetSizer(blocks_sizer)

        # Blocks state
        self._blocks_items = []
        self._blocks_count = 0

        # === TAB 6: HISTORY ===
        history_panel = wx.Panel(self.notebook)
        history_sizer = wx.BoxSizer(wx.VERTICAL)

        hist_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.m_history_text = wx.TextCtrl(
            history_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        self.m_history_text.SetFont(
            wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )
        self.m_history_text.SetBackgroundColour(bg)
        self.m_history_text.SetForegroundColour(fg)

        m_btn_clear_history = wx.Button(history_panel, label=tr("messages.history_clear"))
        m_btn_clear_history.Bind(wx.EVT_BUTTON, self._on_clear_history)
        hist_bar.Add(m_btn_clear_history, 0, wx.ALL, 5)
        history_sizer.Add(hist_bar, 0, wx.EXPAND)
        history_sizer.Add(self.m_history_text, 1, wx.ALL | wx.EXPAND, 5)

        history_panel.SetSizer(history_sizer)

        # === ADD TABS ===
        self.notebook.AddPage(import_panel, tr("gui.tab_import"))
        self.notebook.AddPage(search_panel, tr("gui.tab_search"))
        self.notebook.AddPage(config_panel, tr("gui.tab_config"))
        self._library_tab_idx = 3
        self.notebook.AddPage(library_panel, tr("messages.tab_library", count=0))
        self._blocks_tab_idx = 4
        self.notebook.AddPage(blocks_panel, tr("gui.tab_blocks", count=0))
        self._history_tab_idx = 5
        self.notebook.AddPage(
            history_panel, tr("gui.tab_history", count=self.backend.history.get_count())
        )

        # === BOTTOM BAR ===
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 3)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.m_hyperlink.Reparent(self)
        bottom_sizer.Add(self.m_hyperlink, 0, wx.LEFT | wx.BOTTOM, 5)
        bottom_sizer.AddStretchSpacer()

        try:
            from .version import PLUGIN_VERSION_STRING
        except ImportError:
            try:
                from version import PLUGIN_VERSION_STRING
            except ImportError:
                PLUGIN_VERSION_STRING = "CustomImportGUI"

        self.m_version_label = wx.StaticText(self, label=PLUGIN_VERSION_STRING)
        self.m_version_label.SetForegroundColour(wx.Colour(140, 140, 140))
        self.m_version_label.SetFont(
            wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        )
        bottom_sizer.Add(self.m_version_label, 0, wx.RIGHT | wx.BOTTOM, 5)

        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        # Hide elements not needed in tabs
        self.m_button_migrate.Hide()

        # Hide hidden base widgets and orphan labels from _add_profile_controls
        orphan_widgets = [
            self.m_staticline11, self.m_staticline12, self.m_staticline1,
            self.m_staticText5, self.m_check_import_all, self.m_choice1,
        ]
        # Add profile labels that were created on self but not reparented
        for attr in ['_profile_label', '_lib_name_label', '_env_var_label']:
            if hasattr(self, attr):
                orphan_widgets.append(getattr(self, attr))

        for w in orphan_widgets:
            try:
                w.Hide()
            except Exception:
                pass

        self.SetMinSize(wx.Size(900, 650))
        self.SetSize(wx.Size(960, 720))
        self.Layout()

        # Initial refresh
        self._add_drag_drop_hint()
        self._refresh_library_tab()
        self.notebook.SetPageText(
            self._library_tab_idx, tr("messages.tab_library", count=self._library_count)
        )
        self._refresh_blocks_tab()
        self.notebook.SetPageText(
            self._blocks_tab_idx, tr("gui.tab_blocks", count=self._blocks_count)
        )
        self._refresh_history_tab()
        self._check_migration_possible()

    # === LIBRARY FILTER METHODS ===

    def _on_library_filter(self, event) -> None:
        if not hasattr(self, "m_library_filter"):
            return
        self._apply_library_filter(self.m_library_filter.GetValue())
        event.Skip()

    def _on_library_filter_clear(self, event) -> None:
        if hasattr(self, "m_library_filter"):
            self.m_library_filter.SetValue("")
        self._apply_library_filter("")
        event.Skip()

    def _apply_library_filter(self, text: str) -> None:
        if not hasattr(self, "m_library_list"):
            return

        text = text.lower().strip()
        self.m_library_list.DeleteAllItems()

        source = self._all_library_items if self._all_library_items else self._library_items

        for row in source:
            if not text or any(text in str(col).lower() for col in row):
                idx = self.m_library_list.InsertItem(
                    self.m_library_list.GetItemCount(), str(row[0])
                )
                for col_idx, val in enumerate(row[1:], start=1):
                    self.m_library_list.SetItem(idx, col_idx, str(val))

    # === HISTORY METHODS ===

    def _refresh_history_tab(self) -> None:
        if not hasattr(self, "m_history_text"):
            return
        entries = self.backend.history.get_entries()
        if not entries:
            self.m_history_text.SetValue(tr("messages.history_empty"))
            return

        lines = []
        for e in reversed(entries):
            lines.append(
                f"{e.get('date', '?')}  {e.get('component', '?'):<30s}  "
                f"{e.get('source', '?'):<12s}  {e.get('library', '?')}"
            )
        self.m_history_text.SetValue("\n".join(lines))

    def _on_clear_history(self, event) -> None:
        dlg = wx.MessageDialog(
            self,
            tr("messages.history_clear_confirm"),
            tr("messages.confirm_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.backend.history.clear()
            self._refresh_history_tab()
            self.notebook.SetPageText(
                self._history_tab_idx, tr("gui.tab_history", count=0)
            )
        dlg.Destroy()
        event.Skip()

    # === PROGRESS METHODS ===

    def _on_progress_update(self, step: int, total: int, message: str) -> None:
        try:
            wx.CallAfter(self._update_progress_gui, step, total, message)
        except Exception:
            pass

    def _update_progress_gui(self, step: int, total: int, message: str) -> None:
        if total <= 0:
            self.m_progress.Hide()
            self.Layout()
            return

        if not self.m_progress.IsShown():
            self.m_progress.Show()
            self.Layout()

        pct = int((step / total) * 100)
        self.m_progress.SetValue(pct)

    # === EVENT HANDLING ===

    def _on_show_history(self, event) -> None:
        self._refresh_history_tab()
        self.notebook.SetSelection(self._history_tab_idx)
        event.Skip()

    # === SEARCH DISPATCH METHODS ===
    # These route events to either the JLCPCB or KiCad Official handler based on
    # the currently selected source in m_search_source.

    def _on_search_dispatch(self, event) -> None:
        """Dispatch search button / Enter key to the correct handler."""
        keyword = self.m_search_input.GetValue().strip()
        if not keyword:
            event.Skip()
            return
        self._search_keyword = keyword
        self._search_page = 1
        if self._is_kicad_source():
            self._run_kicad_search()
        else:
            self._run_search()
        event.Skip()

    def _on_search_select_dispatch(self, event) -> None:
        """Dispatch list item selection to the correct handler."""
        if self._is_kicad_source():
            self._on_kicad_search_select(event)
        else:
            self._on_search_select(event)

    def _on_search_import_dispatch(self, event) -> None:
        """Dispatch import button / double-click to the correct handler."""
        if self._is_kicad_source():
            self._on_kicad_search_import(event)
        else:
            self._on_search_import(event)

    def _setup_events(self) -> None:
        EVT_UPDATE(self, self.update_display)

    def _setup_drag_drop(self) -> None:
        drop_target = FileDropTarget(self.m_text, self._on_files_dropped)
        self.m_text.SetDropTarget(drop_target)
        self.m_text.SetToolTip(tr("tooltips.drag_drop"))

    def _add_drag_drop_hint(self) -> None:
        hint_text = tr("messages.drag_drop_hint")
        self.backend.print_to_buffer(hint_text)
        self.backend.print_to_buffer("=" * 50)

    # === IMPORT METHODS ===

    def _on_files_dropped(self, zip_files: List[str]) -> None:
        self.backend.print_to_buffer(
            f"\n{tr('messages.files_received', count=len(zip_files))}"
        )
        for zip_file in zip_files:
            self.backend.print_to_buffer(f"  • {os.path.basename(zip_file)}")
        self.backend.print_to_buffer("")
        self._import_dropped_files(zip_files)

    def _import_dropped_files(self, zip_files: List[str]) -> None:
        self._update_backend_settings()
        for zip_file in zip_files:
            self.backend._import_single_file(zip_file)
        self._check_and_show_library_warnings()

    def _start_monitoring_thread(self) -> None:
        self.thread = PluginThread(self, self.backend)

    def _on_update_available(self, version: str, url: str) -> None:
        """Called from background thread when a newer version is found."""
        wx.CallAfter(
            self.backend.print_to_buffer,
            tr("messages.update_available", version=version, url=url)
        )

    def _print_initial_paths(self) -> None:
        src_path = self.backend.config.get_SRC_PATH()

        if self.backend.local_lib and self.kicad_project:
            dest_path = self.kicad_project
            lib_mode = tr("messages.local_library")
        else:
            dest_path = self.backend.config.get_DEST_PATH()
            lib_mode = tr("messages.global_library")

        self.backend.print_to_buffer(tr("messages.library_mode", mode=lib_mode))
        self.backend.print_to_buffer(tr("messages.source_dir", path=src_path))
        self.backend.print_to_buffer(tr("messages.dest_dir", path=dest_path))
        self.backend.print_to_buffer("=" * 50)

    def _print_path_change(self, change_type: str, new_value: str = "") -> None:
        if change_type == "library_mode":
            if self.backend.local_lib and self.kicad_project:
                dest_path = self.kicad_project
                lib_mode = tr("messages.local_library")
            else:
                dest_path = self.backend.config.get_DEST_PATH()
                lib_mode = tr("messages.global_library")
            self.backend.print_to_buffer(tr("messages.new_library_mode", mode=lib_mode))
            self.backend.print_to_buffer(tr("messages.new_dest_dir", path=dest_path))
        elif change_type == "source":
            self.backend.print_to_buffer(tr("messages.new_source_dir", path=new_value))
        elif change_type == "destination":
            if not self.backend.local_lib:
                self.backend.print_to_buffer(tr("messages.new_dest_dir", path=new_value))

    def _update_button_label(self) -> None:
        if self.backend.run_thread:
            self.m_button.Label = tr("gui.auto_import_running")
        else:
            self.m_button.Label = tr("gui.start")

    def update_display(self, status: ResultEvent) -> None:
        self.m_text.SetValue(status.data)
        self.m_text.SetInsertionPointEnd()

    def m_checkBoxLocalLibOnCheckBox(self, event: wx.CommandEvent) -> None:
        old_local_lib = self.backend.local_lib
        self.backend.local_lib = self.m_checkBoxLocalLib.IsChecked()
        self.m_dirPicker_librarypath.Enable(not self.backend.local_lib)
        if old_local_lib != self.backend.local_lib:
            self._print_path_change("library_mode")
        event.Skip()

    # === CLOSE / CLEANUP ===

    def on_close(self, event: wx.CloseEvent) -> None:
        try:
            if not self.backend.run_thread:
                self._safe_cleanup(close_ipc=not self.fallback_mode)
                logging.info("No auto import: Closing everything completely")
                event.Skip()

            elif self.fallback_mode:
                choice = self._confirm_background_process()
                if choice == "cancel":
                    event.Veto()
                    return
                elif choice == "background":
                    self._safe_cleanup(close_ipc=False, stop_backend=False)
                    logging.info("Fallback mode: GUI closed, background thread continues")
                    event.Skip()
                    return
                else:
                    self._safe_cleanup(close_ipc=False, stop_backend=True)
                    logging.info("Fallback mode: Everything stopped")
                    event.Skip()
            else:
                choice = self._confirm_background_process()
                if choice == "cancel":
                    event.Veto()
                    return
                elif choice == "background":
                    self._safe_cleanup(close_ipc=False, stop_backend=False)
                    if not self.IsIconized():
                        self.Iconize(True)
                    logging.info("IPC mode: Frontend minimized, running in background")
                    event.Veto()
                    return
                else:
                    self._safe_cleanup(close_ipc=True, stop_backend=True)
                    logging.info("IPC mode: Everything stopped")
                    event.Skip()

        except Exception as e:
            logging.exception(f"Error during close event: {e}")
            try:
                self._safe_cleanup(close_ipc=not self.fallback_mode, stop_backend=True)
            except Exception:
                pass
            event.Skip()

    def _safe_cleanup(self, close_ipc: bool = True, stop_backend: bool = True) -> None:
        try:
            self._save_settings()
        except Exception as e:
            logging.warning(f"Failed to save settings during cleanup: {e}")

        if stop_backend:
            try:
                self.backend.run_thread = False
            except Exception as e:
                logging.warning(f"Failed to stop backend thread: {e}")

        try:
            if self.thread:
                self.thread.stop_thread = True
        except Exception as e:
            logging.warning(f"Failed to stop monitoring thread: {e}")

        if close_ipc:
            try:
                instance_manager.stop_server()
            except Exception as e:
                logging.warning(f"Failed to stop IPC server: {e}")

    def _confirm_background_process(self) -> str:
        dlg = wx.MessageDialog(
            None,
            tr("messages.import_running_msg"),
            tr("messages.import_running_title"),
            wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
        )
        dlg.SetYesNoLabels(tr("messages.hide_button"), tr("messages.stop_button"))
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            return "background"
        elif result == wx.ID_NO:
            return "close"
        else:
            return "cancel"

    def _save_settings(self) -> None:
        self.backend.auto_import = self.m_autoImport.IsChecked()
        self.backend.overwrite_import = self.m_overwrite.IsChecked()
        self.backend.auto_lib = self.m_check_autoLib.IsChecked()
        self.backend.import_old_format = self.m_check_import_all.IsChecked()
        self.backend.local_lib = self.m_checkBoxLocalLib.IsChecked()

    # === MAIN BUTTON ACTIONS ===

    def BottonClick(self, event: wx.CommandEvent) -> None:
        self._update_backend_settings()
        if self.backend.run_thread:
            self._stop_import()
        else:
            self._start_import()
        event.Skip()

    def _update_backend_settings(self) -> None:
        if self.backend.local_lib:
            if not self.kicad_project:
                return
            self.backend.importer.set_DEST_PATH(Path(self.kicad_project))
            kicad_link = "${KIPRJMOD}"
        else:
            dest_path = self.backend.config.get_DEST_PATH()
            if dest_path:
                self.backend.importer.set_DEST_PATH(Path(dest_path))
            kicad_link = self.backend.config.get_library_variable()

        self.backend.importer.KICAD_3RD_PARTY_LINK = kicad_link

        overwrite_changed = (
            self.m_overwrite.IsChecked() and not self.backend.overwrite_import
        )
        if overwrite_changed:
            self.backend.folder_handler.known_files = set()

        self._save_settings()

    def _stop_import(self) -> None:
        self.backend.run_thread = False
        self.m_button.Label = tr("gui.start")

    def _start_import(self) -> None:
        if self.backend.auto_import:
            self.backend.run_thread = True
            self.m_button.Label = tr("gui.auto_import_running")
            import_thread = Thread(target=self._auto_import_and_check)
            import_thread.start()
        else:
            self.backend.run_thread = False
            self.backend.find_and_import_new_files()
            self.m_button.Label = tr("gui.start")
            self._check_and_show_library_warnings()

    def _auto_import_and_check(self) -> None:
        self.backend.find_and_import_new_files()
        try:
            wx.CallAfter(self._check_and_show_library_warnings)
        except Exception:
            pass

    def _check_and_show_library_warnings(self) -> None:
        self._refresh_history_tab()
        self.notebook.SetPageText(
            self._history_tab_idx, tr("gui.tab_history", count=self.backend.history.get_count())
        )

        add_if_possible = self.m_check_autoLib.IsChecked()
        msg = check_library_import(self.backend, add_if_possible)

        if msg:
            self._show_library_warning(msg)

    def _show_library_warning(self, msg: str) -> None:
        full_msg = f"{msg}\n\n{tr('messages.library_warning_footer')}"
        dlg = wx.MessageDialog(None, full_msg, tr("messages.warning_title"), wx.OK | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_OK:
            separator = "\n" + "=" * 50 + "\n"
            self.backend.print_to_buffer(separator + full_msg + separator)

    def DirChange(self, event: wx.CommandEvent) -> None:
        old_src = self.backend.config.get_SRC_PATH()
        old_dest = self.backend.config.get_DEST_PATH()

        new_src = self.m_dirPicker_sourcepath.GetPath()
        new_dest = self.m_dirPicker_librarypath.GetPath()

        self.backend.config.set_SRC_PATH(new_src)
        self.backend.config.set_DEST_PATH(new_dest)
        self.backend.folder_handler.known_files = set()

        if old_src != new_src:
            self._print_path_change("source", new_src)
        if old_dest != new_dest:
            self._print_path_change("destination", new_dest)

        self._check_migration_possible()
        event.Skip()

    # === EASYEDA IMPORT ===

    def ButtomManualImport(self, event: wx.CommandEvent) -> None:
        try:
            self._perform_easyeda_import()
            self._refresh_history_tab()
            self.notebook.SetPageText(
                self._history_tab_idx, tr("gui.tab_history", count=self.backend.history.get_count())
            )
        except Exception as e:
            error_msg = f"Error: {e}\nPython version: {sys.version}"
            self.backend.print_to_buffer(error_msg)
            logging.exception("Manual import failed")
        finally:
            event.Skip()

    def _perform_easyeda_import(self) -> None:
        try:
            from .impart_easyeda import import_easyeda_component, ImportConfig
        except ImportError:
            try:
                from impart_easyeda import import_easyeda_component, ImportConfig
            except ImportError as e:
                error_msg = f"Failed to import EasyEDA module: {e}"
                self.backend.print_to_buffer(error_msg)
                logging.error(f"EasyEDA import module not available: {e}")
                wx.MessageBox(
                    f"EasyEDA Import Error!\n\n{error_msg}",
                    "Import Error",
                    wx.OK | wx.ICON_ERROR,
                )
                return

        if self.backend.local_lib:
            if not self.kicad_project:
                self.backend.print_to_buffer(tr("messages.error_local_no_project"))
                return

            project_path = Path(self.kicad_project)
            if not project_path.exists() or not project_path.is_dir():
                self.backend.print_to_buffer(tr("messages.error_project_invalid", path=self.kicad_project))
                return

            path_variable = "${KIPRJMOD}"
            base_folder = project_path
        else:
            base_folder = self.backend.config.get_DEST_PATH()

        config = ImportConfig(
            base_folder=Path(base_folder),
            lib_name=self.backend.config.get_library_name(),
            overwrite=self.m_overwrite.IsChecked(),
            lib_var=self.backend.config.get_library_variable() if not self.backend.local_lib else path_variable,
        )

        raw_input = self.m_textCtrl2.GetValue().strip()
        component_ids = [
            cid.strip() for cid in re.split(r'[,;\s]+', raw_input) if cid.strip()
        ]

        if not component_ids:
            self.backend.print_to_buffer(tr("messages.error_no_component_id"))
            return

        total = len(component_ids)
        if total > 1:
            self.backend.print_to_buffer(
                f"\n{tr('messages.batch_import_start', count=total)}"
            )

        organize_by_cat = self.backend.config.get_organize_by_category()

        success_count = 0
        for i, component_id in enumerate(component_ids, 1):
            if total > 1:
                self.backend.print_to_buffer(f"\n[{i}/{total}] {component_id}")

            import_config = config
            if organize_by_cat and not self.backend.local_lib:
                try:
                    cat_results = search_components(component_id, page_size=1)
                    if cat_results and cat_results[0].category:
                        cat_name = cat_results[0].category.replace(" ", "_").replace("/", "_")
                        sub_lib_name = f"{config.lib_name}_{cat_name}"
                        import_config = ImportConfig(
                            base_folder=config.base_folder,
                            lib_name=sub_lib_name,
                            overwrite=config.overwrite,
                            lib_var=config.lib_var,
                        )
                except Exception:
                    pass

            try:
                paths = import_easyeda_component(
                    component_id=component_id,
                    config=import_config,
                    print_func=self.backend.print_to_buffer,
                )
                self.backend.print_to_buffer("")
                logging.info(f"Successfully imported EasyEDA component {component_id}")
                self.backend.history.add_entry(
                    component_name=component_id,
                    source="EasyEDA",
                    library_name=self.backend.config.get_library_name(),
                    zip_file="",
                    profile=self.backend.config.get_current_profile(),
                )
                success_count += 1

            except ValueError as e:
                self.backend.print_to_buffer(f"Error {component_id}: {e}")
                logging.error(f"Invalid component ID {component_id}: {e}")

            except RuntimeError as e:
                self.backend.print_to_buffer(f"Error {component_id}: {e}")
                logging.error(f"Runtime error importing {component_id}: {e}")

            except Exception as e:
                self.backend.print_to_buffer(f"Error {component_id}: {e}")
                logging.exception(f"Unexpected error importing {component_id}")

        if total > 1:
            self.backend.print_to_buffer(
                f"\n{tr('messages.batch_import_done', success=success_count, total=total)}"
            )

    # === MIGRATION METHODS ===

    def get_old_lib_files(self) -> dict:
        lib_path = self.m_dirPicker_librarypath.GetPath()
        return find_old_lib_files(
            folder_path=lib_path, libs=ImpartBackend.SUPPORTED_LIBRARIES
        )

    def _check_migration_possible(self) -> None:
        libs_to_migrate = self.get_old_lib_files()
        conversion_info = convert_lib_list(libs_to_migrate, drymode=True)
        if conversion_info:
            self.m_button_migrate.Show()
        else:
            self.m_button_migrate.Hide()

    def migrate_libs(self, event: wx.CommandEvent) -> None:
        libs_to_migrate = self.get_old_lib_files()
        conversion_info = convert_lib_list(libs_to_migrate, drymode=True)
        if not conversion_info:
            self.backend.print_to_buffer("Error in migrate_libs()")
            return
        self._perform_migration(libs_to_migrate, conversion_info)
        self._check_migration_possible()
        event.Skip()

    def _perform_migration(
        self, libs_to_migrate: dict, conversion_info: List[Tuple]
    ) -> None:
        msg, lib_rename = self.backend.kicad_settings.prepare_library_migration(
            conversion_info
        )
        if not self._confirm_migration(msg):
            return
        self._execute_conversion(libs_to_migrate)
        if lib_rename:
            self._handle_library_renaming(msg, lib_rename)

    def _confirm_migration(self, msg: str) -> bool:
        dlg = wx.MessageDialog(
            None, msg, "WARNING", wx.OK | wx.ICON_WARNING | wx.CANCEL
        )
        return dlg.ShowModal() == wx.ID_OK

    def _execute_conversion(self, libs_to_migrate: dict) -> None:
        self.backend.print_to_buffer("Converted libraries:")
        conversion_results = convert_lib_list(libs_to_migrate, drymode=False)
        for old_path, new_path in conversion_results:
            if new_path.endswith(".blk"):
                self.backend.print_to_buffer(f"{old_path} rename to {new_path}")
            else:
                self.backend.print_to_buffer(f"{old_path} convert to {new_path}")

    def _handle_library_renaming(self, msg: str, lib_rename: List[dict]) -> None:
        msg_lib = (
            "\nShould the change be made automatically? "
            "A restart of KiCad is then necessary to apply all changes."
        )
        dlg = wx.MessageDialog(
            None, msg + msg_lib, "WARNING", wx.OK | wx.ICON_WARNING | wx.CANCEL
        )
        if dlg.ShowModal() == wx.ID_OK:
            result_msg = self.backend.kicad_settings.execute_library_migration(
                lib_rename
            )
            self.backend.print_to_buffer(result_msg)
        else:
            self._show_manual_migration_instructions(lib_rename)

    def _show_manual_migration_instructions(self, lib_rename: List[dict]) -> None:
        if not lib_rename:
            return
        msg_summary = (
            "The following changes must be made to the list of imported Symbol libs:\n"
        )
        for item in lib_rename:
            msg_summary += f"\n{item['name']}: {item['oldURI']} \n-> {item['newURI']}"
        msg_summary += (
            "\n\nIt is necessary to adjust the settings of the imported "
            "symbol libraries in KiCad."
        )
        self.backend.print_to_buffer(msg_summary)


if __name__ == "__main__":
    logging.info("Starting application in standalone mode")

    if instance_manager.is_already_running():
        logging.info("Plugin already running - focus command sent")
        import time
        time.sleep(0.5)
        sys.exit(0)

    try:
        app = wx.App()
        frontend = ImpartFrontend(fallback_mode=False)

        if not instance_manager.start_server(frontend):
            logging.warning("Failed to start IPC server - continuing anyway")

        frontend.ShowModal()
        frontend.Destroy()
        logging.info("Application finished successfully")

    except Exception as e:
        logging.exception("Failed to run standalone application")
        raise
    finally:
        instance_manager.stop_server()
