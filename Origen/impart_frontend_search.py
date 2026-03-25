"""
Search tab mixin for ImpartFrontend.
Handles JLCPCB/LCSC component search with image preview.
"""

import logging
from threading import Thread

import wx

try:
    from .ComponentSearch import search_components, fetch_component_image
    from .i18n import _ as tr
except ImportError:
    from ComponentSearch import search_components, fetch_component_image
    from i18n import _ as tr


class SearchMixin:
    """Mixin providing search tab functionality."""

    def _on_search(self, event) -> None:
        keyword = self.m_search_input.GetValue().strip()
        if not keyword:
            return

        self._search_keyword = keyword
        self._search_page = 1
        self._run_search()
        event.Skip()

    def _on_search_prev(self, event) -> None:
        if self._search_page > 1:
            self._search_page -= 1
            self._run_search()
        event.Skip()

    def _on_search_next(self, event) -> None:
        self._search_page += 1
        self._run_search()
        event.Skip()

    def _run_search(self) -> None:
        self.m_search_status.SetLabel(tr("messages.search_searching"))
        self.m_btn_search.Enable(False)
        self.m_btn_prev.Enable(False)
        self.m_btn_next.Enable(False)
        self.m_search_list.DeleteAllItems()
        self._search_results = []
        self.m_btn_search_import.Enable(False)
        self.m_btn_open_lcsc.Enable(False)
        self.m_search_image.SetBitmap(wx.NullBitmap)
        self.m_search_detail.SetValue("")
        self.m_search_duplicate.SetLabel("")

        thread = Thread(
            target=self._do_search,
            args=(self._search_keyword, self._search_page),
        )
        thread.start()

    def _do_search(self, keyword: str, page: int) -> None:
        try:
            results = search_components(keyword, page=page, page_size=self._search_page_size)
            wx.CallAfter(self._display_search_results, keyword, results, page)
        except Exception as e:
            wx.CallAfter(self._display_search_error, str(e))

    def _display_search_results(self, keyword: str, results, page: int) -> None:
        self.m_btn_search.Enable(True)
        self._search_results = results

        if not results:
            self.m_search_status.SetLabel(tr("messages.search_no_results", keyword=keyword))
            self.m_btn_prev.Enable(page > 1)
            return

        self.m_search_status.SetLabel(
            tr("messages.search_page_info", page=page, count=len(results))
        )

        self.m_btn_prev.Enable(page > 1)
        self.m_btn_next.Enable(len(results) >= self._search_page_size)
        self.m_page_label.SetLabel(f"{page}")

        for i, r in enumerate(results):
            idx = self.m_search_list.InsertItem(i, r.lcsc_id)
            self.m_search_list.SetItem(idx, 1, r.name)
            self.m_search_list.SetItem(idx, 2, r.manufacturer)
            self.m_search_list.SetItem(idx, 3, r.package)
            self.m_search_list.SetItem(idx, 4, str(r.stock))
            self.m_search_list.SetItem(idx, 5, f"${r.price:.4f}" if r.price else "")

    def _display_search_error(self, error: str) -> None:
        self.m_btn_search.Enable(True)
        self.m_search_status.SetLabel(f"Error: {error}")

    def _on_search_select(self, event) -> None:
        idx = event.GetIndex()
        if idx < 0 or idx >= len(self._search_results):
            return

        result = self._search_results[idx]
        self.m_btn_search_import.Enable(True)
        self.m_btn_open_lcsc.Enable(bool(result.lcsc_url))

        detail = (
            f"{result.name}\n"
            f"{result.manufacturer}\n"
            f"{result.category}\n"
            f"{result.package}\n"
            f"Stock: {result.stock}\n"
            f"LCSC: {result.lcsc_id}\n"
        )
        if result.description:
            detail += f"\n{result.description[:150]}"
        self.m_search_detail.SetValue(detail)

        existing = self.backend.history.is_already_imported(result.lcsc_id)
        if existing:
            self.m_search_duplicate.SetLabel(
                tr("messages.search_already_imported", date=existing.get("date", "?"))
            )
        else:
            self.m_search_duplicate.SetLabel("")

        if result.lcsc_id:
            self.m_search_image.SetBitmap(wx.NullBitmap)
            thread = Thread(target=self._load_search_image, args=(result.lcsc_id,))
            thread.start()

        event.Skip()

    def _on_open_lcsc(self, event) -> None:
        idx = self.m_search_list.GetFirstSelected()
        if idx < 0 or idx >= len(self._search_results):
            return
        result = self._search_results[idx]
        if result.lcsc_url:
            import webbrowser
            webbrowser.open(result.lcsc_url)
        event.Skip()

    def _load_search_image(self, lcsc_id: str) -> None:
        try:
            image_data = fetch_component_image(lcsc_id)
            if image_data:
                wx.CallAfter(self._display_search_image, image_data)
        except Exception:
            pass

    def _display_search_image(self, image_data: bytes) -> None:
        try:
            import io
            stream = io.BytesIO(image_data)
            image = wx.Image(stream)
            if image.IsOk():
                image = image.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
                self.m_search_image.SetBitmap(wx.Bitmap(image))
                self.m_search_image.GetParent().Layout()
        except Exception as e:
            logging.debug(f"Failed to display image: {e}")

    def _on_search_import(self, event) -> None:
        idx = self.m_search_list.GetFirstSelected()
        if idx < 0 or idx >= len(self._search_results):
            return

        result = self._search_results[idx]
        self.m_textCtrl2.SetValue(result.lcsc_id)
        self.notebook.SetSelection(0)

        self._perform_easyeda_import()

        self._refresh_history_tab()
        self.notebook.SetPageText(
            self._history_tab_idx, tr("gui.tab_history", count=self.backend.history.get_count())
        )

        event.Skip()
