"""
KiCad Official search mixin for ImpartFrontend.
Handles browsing and importing symbols from KiCad's official GitLab repositories.
"""

import logging
from pathlib import Path
from threading import Thread

import wx

try:
    from .KiCadGitLab import list_symbol_libraries, search_symbols, download_symbol
    from .i18n import _ as tr
except ImportError:
    from KiCadGitLab import list_symbol_libraries, search_symbols, download_symbol
    from i18n import _ as tr


logger = logging.getLogger(__name__)


class KiCadSearchMixin:
    """Mixin providing KiCad Official symbol search functionality.

    Expects the following attributes to already exist on self (created by
    the main _enhance_gui setup):
      - m_search_source: wx.Choice (source selector)
      - m_search_input: wx.TextCtrl
      - m_btn_search: wx.Button
      - m_search_status: wx.StaticText
      - m_search_list: wx.ListCtrl
      - m_btn_search_import: wx.Button
      - m_btn_open_lcsc: wx.Button
      - m_search_detail: wx.TextCtrl
      - m_search_duplicate: wx.StaticText
      - m_search_image: wx.StaticBitmap
      - m_btn_prev / m_btn_next / m_page_label
      - m_kicad_lib_choice: wx.Choice (KiCad library filter dropdown)
      - backend: ImpartBackend
    """

    # ------------------------------------------------------------------
    # Source selection helpers
    # ------------------------------------------------------------------

    def _is_kicad_source(self) -> bool:
        """Return True when the user has selected 'KiCad Official' as source."""
        if not hasattr(self, "m_search_source"):
            return False
        return self.m_search_source.GetSelection() == 1  # index 1 = KiCad Official

    def _on_search_source_changed(self, event) -> None:
        """Switch UI columns and hints when the source dropdown changes."""
        if self._is_kicad_source():
            self._switch_to_kicad_columns()
            self.m_search_input.SetHint(tr("messages.kicad_search_hint"))
            self.m_btn_open_lcsc.Hide()
            if hasattr(self, "m_kicad_lib_row"):
                self.m_kicad_lib_row.ShowItems(True)
            # Load library list in background if not cached
            if not hasattr(self, "_kicad_libs_loaded") or not self._kicad_libs_loaded:
                self._load_kicad_lib_list()
        else:
            self._switch_to_jlcpcb_columns()
            self.m_search_input.SetHint(tr("messages.search_hint"))
            self.m_btn_open_lcsc.Show()
            if hasattr(self, "m_kicad_lib_row"):
                self.m_kicad_lib_row.ShowItems(False)

        self.m_search_list.DeleteAllItems()
        self.m_search_status.SetLabel("")
        if hasattr(self, "_search_panel_ref"):
            self._search_panel_ref.Layout()
        event.Skip()

    def _switch_to_kicad_columns(self) -> None:
        """Reconfigure list columns for KiCad symbol results."""
        self.m_search_list.ClearAll()
        self.m_search_list.InsertColumn(0, tr("messages.kicad_search_col_symbol"), width=220)
        self.m_search_list.InsertColumn(1, tr("messages.kicad_search_col_library"), width=250)

    def _switch_to_jlcpcb_columns(self) -> None:
        """Restore list columns for JLCPCB/LCSC results."""
        self.m_search_list.ClearAll()
        self.m_search_list.InsertColumn(0, "LCSC #", width=80)
        self.m_search_list.InsertColumn(1, tr("messages.search_col_name"), width=180)
        self.m_search_list.InsertColumn(2, tr("messages.search_col_mfr"), width=130)
        self.m_search_list.InsertColumn(3, tr("messages.search_col_package"), width=100)
        self.m_search_list.InsertColumn(4, "Stock", width=60)
        self.m_search_list.InsertColumn(5, tr("messages.search_col_price"), width=80)

    # ------------------------------------------------------------------
    # Library list loading
    # ------------------------------------------------------------------

    def _load_kicad_lib_list(self) -> None:
        """Fetch the KiCad symbol library list in the background and populate the dropdown."""
        self._kicad_libs_loaded = False
        if hasattr(self, "m_kicad_lib_choice"):
            self.m_kicad_lib_choice.Clear()
            self.m_kicad_lib_choice.Append(tr("messages.kicad_loading_libs"))
            self.m_kicad_lib_choice.SetSelection(0)
            self.m_kicad_lib_choice.Enable(False)

        thread = Thread(target=self._do_load_kicad_libs, daemon=True)
        thread.start()

    def _do_load_kicad_libs(self) -> None:
        try:
            libs = list_symbol_libraries()
            wx.CallAfter(self._on_kicad_libs_loaded, libs)
        except Exception as e:
            wx.CallAfter(self._on_kicad_libs_load_failed, str(e))

    def _on_kicad_libs_loaded(self, libs) -> None:
        self._kicad_libs_loaded = True
        self._kicad_lib_list = libs
        if hasattr(self, "m_kicad_lib_choice"):
            self.m_kicad_lib_choice.Clear()
            self.m_kicad_lib_choice.Append(tr("messages.kicad_no_lib_selected"))
            for lib in libs:
                name = lib["name"].replace(".kicad_sym", "")
                self.m_kicad_lib_choice.Append(name)
            self.m_kicad_lib_choice.SetSelection(0)
            self.m_kicad_lib_choice.Enable(True)

    def _on_kicad_libs_load_failed(self, error: str) -> None:
        self._kicad_libs_loaded = False
        if hasattr(self, "m_kicad_lib_choice"):
            self.m_kicad_lib_choice.Clear()
            self.m_kicad_lib_choice.Append(tr("messages.kicad_load_failed"))
            self.m_kicad_lib_choice.SetSelection(0)
            self.m_kicad_lib_choice.Enable(True)
        logger.error(f"KiCadSearch: failed to load library list: {error}")

    # ------------------------------------------------------------------
    # Search execution
    # ------------------------------------------------------------------

    def _run_kicad_search(self) -> None:
        """Run a KiCad Official symbol search in a background thread."""
        self.m_search_status.SetLabel(tr("messages.search_searching"))
        self.m_btn_search.Enable(False)
        self.m_search_list.DeleteAllItems()
        self._kicad_search_results = []
        self.m_btn_search_import.Enable(False)
        if hasattr(self, "m_search_detail"):
            self.m_search_detail.SetValue("")
        if hasattr(self, "m_search_duplicate"):
            self.m_search_duplicate.SetLabel("")
        if hasattr(self, "m_search_image"):
            self.m_search_image.SetBitmap(wx.NullBitmap)

        keyword = getattr(self, "_search_keyword", "")
        selected_lib = self._get_selected_kicad_lib()

        thread = Thread(
            target=self._do_kicad_search,
            args=(keyword, selected_lib),
            daemon=True,
        )
        thread.start()

    def _get_selected_kicad_lib(self) -> str:
        """Return the library name selected in the lib dropdown, or empty string."""
        if not hasattr(self, "m_kicad_lib_choice"):
            return ""
        idx = self.m_kicad_lib_choice.GetSelection()
        if idx <= 0:
            return ""
        return self.m_kicad_lib_choice.GetString(idx)

    def _do_kicad_search(self, keyword: str, library: str) -> None:
        try:
            results = search_symbols(keyword, library=library if library else None)
            wx.CallAfter(self._display_kicad_results, keyword, results)
        except Exception as e:
            wx.CallAfter(self._display_kicad_search_error, str(e))

    def _display_kicad_results(self, keyword: str, results) -> None:
        self.m_btn_search.Enable(True)
        self._kicad_search_results = results

        if not results:
            self.m_search_status.SetLabel(tr("messages.search_no_results", keyword=keyword))
            return

        self.m_search_status.SetLabel(
            tr("messages.search_results_count", count=len(results))
        )

        for i, r in enumerate(results):
            idx = self.m_search_list.InsertItem(i, r["name"])
            self.m_search_list.SetItem(idx, 1, r["library"])

    def _display_kicad_search_error(self, error: str) -> None:
        self.m_btn_search.Enable(True)
        self.m_search_status.SetLabel(f"Error: {error}")

    # ------------------------------------------------------------------
    # Selection and import
    # ------------------------------------------------------------------

    def _on_kicad_search_select(self, event) -> None:
        """Handle row selection in KiCad symbol results."""
        idx = event.GetIndex()
        results = getattr(self, "_kicad_search_results", [])
        if idx < 0 or idx >= len(results):
            event.Skip()
            return

        result = results[idx]
        self.m_btn_search_import.Enable(True)

        detail = f"{result['name']}\nLibrary: {result['library']}"
        if result.get("description"):
            detail += f"\n{result['description']}"
        if hasattr(self, "m_search_detail"):
            self.m_search_detail.SetValue(detail)
        if hasattr(self, "m_search_duplicate"):
            self.m_search_duplicate.SetLabel("")

        event.Skip()

    def _on_kicad_search_import(self, event) -> None:
        """Import the selected KiCad Official symbol into the user's library."""
        idx = self.m_search_list.GetFirstSelected()
        results = getattr(self, "_kicad_search_results", [])
        if idx < 0 or idx >= len(results):
            event.Skip()
            return

        result = results[idx]
        library_name = result["library"]
        symbol_name = result["name"]

        dest_dir = self.backend.config.get_DEST_PATH()
        lib_name = self.backend.config.get_LIBRARY_NAME() or "KiCad_Official"
        dest_path = str(Path(dest_dir) / f"{lib_name}.kicad_sym")

        self.m_search_status.SetLabel(tr("messages.search_searching"))
        self.m_btn_search_import.Enable(False)

        thread = Thread(
            target=self._do_kicad_import,
            args=(library_name, symbol_name, dest_path),
            daemon=True,
        )
        thread.start()
        event.Skip()

    def _do_kicad_import(self, library_name: str, symbol_name: str, dest_path: str) -> None:
        ok = download_symbol(library_name, symbol_name, dest_path)
        wx.CallAfter(self._on_kicad_import_done, symbol_name, ok)

    def _on_kicad_import_done(self, symbol_name: str, ok: bool) -> None:
        self.m_btn_search_import.Enable(True)
        if ok:
            msg = tr("messages.kicad_import_success", name=symbol_name)
            self.m_search_status.SetLabel(msg)
            # Refresh the library browser tab
            if hasattr(self, "_refresh_library_tab"):
                self._refresh_library_tab()
                if hasattr(self, "_library_tab_idx") and hasattr(self, "notebook"):
                    self.notebook.SetPageText(
                        self._library_tab_idx,
                        tr("messages.tab_library", count=self._library_count),
                    )
        else:
            msg = tr("messages.kicad_import_failed", name=symbol_name)
            self.m_search_status.SetLabel(msg)
