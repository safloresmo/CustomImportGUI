"""
Design Blocks tab mixin for ImpartFrontend.
Handles listing, importing, creating and deleting KiCad 10 design blocks.
"""

import logging
from pathlib import Path

import wx

try:
    from .DesignBlocks import (
        get_design_blocks_path,
        list_design_blocks,
        create_design_block,
        delete_design_block,
        import_sch_as_block,
        update_block_metadata,
        register_in_kicad,
    )
    from .i18n import _ as tr
except ImportError:
    from DesignBlocks import (
        get_design_blocks_path,
        list_design_blocks,
        create_design_block,
        delete_design_block,
        import_sch_as_block,
        update_block_metadata,
        register_in_kicad,
    )
    from i18n import _ as tr


class DesignBlocksMixin:
    """Mixin providing Design Blocks tab functionality."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_blocks_path(self) -> Path:
        """Return the .kicad_blocks directory for the current profile."""
        dest_path = self.backend.config.get_DEST_PATH()
        lib_name = self.backend.config.get_library_name()
        return get_design_blocks_path(dest_path, lib_name)

    # ── refresh ───────────────────────────────────────────────────────────────

    def _refresh_blocks_tab(self) -> None:
        if not hasattr(self, "m_blocks_list"):
            self._blocks_count = 0
            return

        self.m_blocks_list.DeleteAllItems()
        self._blocks_items = []

        try:
            blocks_path = self._get_blocks_path()
            blocks = list_design_blocks(blocks_path)
        except Exception as e:
            logging.warning(f"Could not list design blocks: {e}")
            blocks = []

        for block in blocks:
            idx = self.m_blocks_list.InsertItem(
                self.m_blocks_list.GetItemCount(), block["name"]
            )
            self.m_blocks_list.SetItem(idx, 1, block["description"])
            self.m_blocks_list.SetItem(idx, 2, block["keywords"])
            self.m_blocks_list.SetItem(idx, 3, "\u2713" if block["has_sch"] else "\u2717")
            self.m_blocks_list.SetItem(idx, 4, "\u2713" if block["has_pcb"] else "\u2717")
            self._blocks_items.append(block["name"])

        self._blocks_count = len(blocks)

        if self._blocks_count == 0:
            self.m_blocks_status.SetLabel(tr("messages.blocks_empty"))
        else:
            self.m_blocks_status.SetLabel(
                tr("messages.blocks_status", count=self._blocks_count)
            )

    def _on_refresh_blocks(self, event) -> None:
        self._refresh_blocks_tab()
        self.notebook.SetPageText(
            self._blocks_tab_idx,
            tr("gui.tab_blocks", count=self._blocks_count),
        )
        if event is not None:
            event.Skip()

    # ── import schematic ──────────────────────────────────────────────────────

    def _on_blocks_import_sch(self, event) -> None:
        dlg = wx.FileDialog(
            self,
            tr("messages.blocks_import_sch"),
            wildcard="KiCad Schematic (*.kicad_sch)|*.kicad_sch",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            event.Skip()
            return

        sch_path = dlg.GetPath()
        dlg.Destroy()

        try:
            blocks_path = self._get_blocks_path()
            block_name = import_sch_as_block(blocks_path, sch_path)
            self._try_register_blocks(blocks_path)
            self.backend.print_to_buffer(
                tr("messages.blocks_imported", name=block_name)
            )
            self._on_refresh_blocks(None)
        except Exception as e:
            logging.error(f"Failed to import schematic as design block: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

        event.Skip()

    # ── new block ─────────────────────────────────────────────────────────────

    def _on_blocks_new(self, event) -> None:
        dlg = wx.TextEntryDialog(
            self,
            tr("messages.blocks_name_prompt"),
            tr("messages.blocks_name_title"),
            "",
        )
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            event.Skip()
            return

        name = dlg.GetValue().strip().replace(" ", "_").replace("/", "_")
        dlg.Destroy()
        if not name:
            event.Skip()
            return

        try:
            blocks_path = self._get_blocks_path()
            create_design_block(blocks_path, name)
            self._try_register_blocks(blocks_path)
            self.backend.print_to_buffer(
                tr("messages.blocks_created", name=name)
            )
            self._on_refresh_blocks(None)
        except Exception as e:
            logging.error(f"Failed to create design block: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

        event.Skip()

    # ── right-click context menu ──────────────────────────────────────────────

    def _on_blocks_right_click(self, event) -> None:
        idx = event.GetIndex()
        if idx < 0 or idx >= len(self._blocks_items):
            return

        self.m_blocks_list.Select(idx)
        block_name = self._blocks_items[idx]

        menu = wx.Menu()

        edit_item = menu.Append(wx.ID_ANY, tr("messages.blocks_edit_title"))
        self.Bind(
            wx.EVT_MENU,
            lambda e, n=block_name: self._on_blocks_edit_metadata(n),
            edit_item,
        )

        menu.AppendSeparator()

        delete_item = menu.Append(wx.ID_ANY, tr("messages.blocks_delete_confirm").split("'")[0].strip() or "Delete")
        self.Bind(
            wx.EVT_MENU,
            lambda e, n=block_name: self._on_blocks_delete(n),
            delete_item,
        )

        self.m_blocks_list.PopupMenu(menu)
        menu.Destroy()

    # ── edit metadata ─────────────────────────────────────────────────────────

    def _on_blocks_edit_metadata(self, block_name: str) -> None:
        try:
            blocks_path = self._get_blocks_path()
            # Read current metadata
            from pathlib import Path as _Path
            import json as _json
            block_dir = blocks_path / f"{block_name}.kicad_block"
            json_file = block_dir / f"{block_name}.json"
            meta: dict = {}
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    meta = _json.load(f)
        except Exception as e:
            logging.error(f"Could not read block metadata: {e}")
            meta = {}

        dlg = wx.Dialog(self, title=tr("messages.blocks_edit_title"), size=wx.Size(480, 200))
        panel = wx.Panel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)

        desc_row = wx.BoxSizer(wx.HORIZONTAL)
        desc_lbl = wx.StaticText(panel, label="Description:", size=wx.Size(90, -1))
        desc_ctrl = wx.TextCtrl(panel, value=meta.get("description", ""))
        desc_row.Add(desc_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        desc_row.Add(desc_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(desc_row, 0, wx.EXPAND)

        kw_row = wx.BoxSizer(wx.HORIZONTAL)
        kw_lbl = wx.StaticText(panel, label="Keywords:", size=wx.Size(90, -1))
        kw_ctrl = wx.TextCtrl(panel, value=meta.get("keywords", ""))
        kw_row.Add(kw_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        kw_row.Add(kw_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(kw_row, 0, wx.EXPAND)

        btn_sizer = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(btn_ok)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                update_block_metadata(
                    blocks_path,
                    block_name,
                    description=desc_ctrl.GetValue(),
                    keywords=kw_ctrl.GetValue(),
                )
                self._on_refresh_blocks(None)
            except Exception as e:
                logging.error(f"Failed to update block metadata: {e}")
                wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    # ── delete ────────────────────────────────────────────────────────────────

    def _on_blocks_delete(self, block_name: str) -> None:
        dlg = wx.MessageDialog(
            self,
            tr("messages.blocks_delete_confirm", name=block_name),
            tr("messages.confirm_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        try:
            blocks_path = self._get_blocks_path()
            delete_design_block(blocks_path, block_name)
            self.backend.print_to_buffer(
                tr("messages.blocks_deleted", name=block_name)
            )
            self._on_refresh_blocks(None)
        except Exception as e:
            logging.error(f"Failed to delete design block: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    # ── registration helper ───────────────────────────────────────────────────

    def _try_register_blocks(self, blocks_path: Path) -> None:
        """Silently register the library in KiCad's design-block-lib-table."""
        try:
            lib_name = self.backend.config.get_library_name()
            added = register_in_kicad(blocks_path, lib_name)
            if added:
                logging.info(f"Registered design block library '{lib_name}' in KiCad")
        except Exception as e:
            logging.warning(f"Could not register design block library: {e}")
