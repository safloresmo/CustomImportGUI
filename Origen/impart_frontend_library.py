"""
Library browser tab mixin for ImpartFrontend.
Handles library browsing, sub-libraries, move/copy/delete, and reorganization.
"""

import logging
from pathlib import Path

import wx

try:
    from .KiCad_Settings import KiCad_Settings
    from .ComponentSearch import search_components
    from .i18n import _ as tr
except ImportError:
    from KiCad_Settings import KiCad_Settings
    from ComponentSearch import search_components
    from i18n import _ as tr


class LibraryMixin:
    """Mixin providing library browser tab functionality."""

    def _get_all_library_paths(self):
        paths = set()
        paths.add(self.backend.config.get_DEST_PATH())
        for profile in self.backend.config.get_available_profiles():
            section = f"profile_{profile}"
            try:
                p = self.backend.config.config[section].get("DEST_PATH", "")
                if p:
                    paths.add(p)
            except Exception:
                pass
        return [Path(p) for p in paths if Path(p).exists()]

    def _refresh_library_tab(self) -> None:
        if not hasattr(self, "m_library_list"):
            self._library_count = 0
            return

        self.m_library_list.DeleteAllItems()
        self._library_count = 0
        fp_count = 0
        model_count = 0
        self._library_items = []
        self._all_library_items = []

        all_paths = self._get_all_library_paths()

        for dest_path in all_paths:
            for pretty_dir in dest_path.glob("*.pretty"):
                fp_count += len(list(pretty_dir.glob("*.kicad_mod")))

            for shapes_dir in dest_path.glob("*.3dshapes"):
                model_count += len(list(shapes_dir.glob("*.step")) + list(shapes_dir.glob("*.wrl")))

        sym_files = []
        for dest_path in all_paths:
            sym_files.extend(dest_path.glob("*.kicad_sym"))
        for sym_file in sym_files:
            try:
                from kiutils.symbol import SymbolLib
                lib = SymbolLib.from_file(str(sym_file))
                for symbol in lib.symbols:
                    props = {p.key: p.value for p in symbol.properties}
                    name = symbol.entryName or props.get("Value", "?")
                    ref = props.get("Reference", "?")
                    footprint = props.get("Footprint", "")
                    source = props.get("OriginalSource", "")
                    imported = props.get("ImportDate", "")

                    file_stem = sym_file.stem
                    sub_lib = file_stem
                    for pf in self.backend.config.get_available_profiles():
                        sec = f"profile_{pf}"
                        try:
                            pf_lib = self.backend.config.config[sec].get("library_name", "")
                            if pf_lib and file_stem.startswith(pf_lib + "_"):
                                sub_lib = file_stem[len(pf_lib) + 1:].replace("_", " ")
                                break
                            elif file_stem == pf_lib:
                                sub_lib = pf_lib
                                break
                        except Exception:
                            pass

                    idx = self.m_library_list.InsertItem(
                        self.m_library_list.GetItemCount(), name
                    )
                    self.m_library_list.SetItem(idx, 1, ref)
                    self.m_library_list.SetItem(idx, 2, sub_lib)
                    self.m_library_list.SetItem(idx, 3, footprint)
                    self.m_library_list.SetItem(idx, 4, source)
                    self.m_library_list.SetItem(idx, 5, imported)
                    self._library_items.append((str(sym_file), name))
                    self._all_library_items.append((name, ref, sub_lib, footprint, source, imported))
                    self._library_count += 1
            except Exception as e:
                logging.warning(f"Could not parse {sym_file.name}: {e}")

        self.m_library_status.SetLabel(
            tr("messages.library_summary", sym=self._library_count, fp=fp_count, model=model_count)
        )

        if self._library_count == 0 and fp_count == 0:
            self.m_library_status.SetLabel(tr("messages.library_empty"))

        # Clear filter when library is refreshed
        if hasattr(self, "m_library_filter"):
            self.m_library_filter.SetValue("")

    def _on_refresh_library(self, event) -> None:
        self._refresh_library_tab()
        self.notebook.SetPageText(
            self._library_tab_idx, tr("messages.tab_library", count=self._library_count)
        )
        event.Skip()

    def _get_all_sym_files(self) -> list:
        files = []
        for p in self._get_all_library_paths():
            files.extend(p.glob("*.kicad_sym"))
        return sorted(set(files), key=lambda f: f.stem)

    def _on_library_right_click(self, event) -> None:
        idx = event.GetIndex()
        if idx < 0 or idx >= len(self._library_items):
            return

        self.m_library_list.Select(idx)
        current_file = Path(self._library_items[idx][0])

        menu = wx.Menu()

        # Edit
        edit_item = menu.Append(wx.ID_ANY, tr("messages.library_edit"))
        self.Bind(wx.EVT_MENU, lambda e: self._on_library_edit(idx), edit_item)

        # Move to submenu
        move_menu = wx.Menu()
        all_files = self._get_all_sym_files()
        for sym_file in all_files:
            if sym_file.resolve() == current_file.resolve():
                continue
            label = sym_file.stem
            item = move_menu.Append(wx.ID_ANY, label)
            self.Bind(
                wx.EVT_MENU,
                lambda e, f=str(sym_file): self._do_move_or_copy(idx, f, move=True),
                item,
            )
        move_menu.AppendSeparator()
        new_item = move_menu.Append(wx.ID_ANY, tr("messages.library_new_sublib"))
        self.Bind(wx.EVT_MENU, lambda e: self._on_library_move(idx), new_item)
        menu.AppendSubMenu(move_menu, tr("messages.library_move_to"))

        # Copy to submenu
        copy_menu = wx.Menu()
        for sym_file in all_files:
            if sym_file.resolve() == current_file.resolve():
                continue
            label = sym_file.stem
            item = copy_menu.Append(wx.ID_ANY, label)
            self.Bind(
                wx.EVT_MENU,
                lambda e, f=str(sym_file): self._do_move_or_copy(idx, f, move=False),
                item,
            )
        copy_menu.AppendSeparator()
        new_copy = copy_menu.Append(wx.ID_ANY, tr("messages.library_new_sublib"))
        self.Bind(wx.EVT_MENU, lambda e: self._on_library_copy_new(idx), new_copy)
        menu.AppendSubMenu(copy_menu, tr("messages.library_copy_to"))

        menu.AppendSeparator()

        # Delete
        delete_item = menu.Append(wx.ID_ANY, tr("messages.library_delete"))
        self.Bind(wx.EVT_MENU, lambda e: self._on_library_delete(idx), delete_item)

        self.m_library_list.PopupMenu(menu)
        menu.Destroy()

    def _do_move_or_copy(self, idx: int, target_file: str, move: bool = True) -> None:
        if idx < 0 or idx >= len(self._library_items):
            return

        src_file, entry_name = self._library_items[idx]
        target_path = Path(target_file)
        target_name = target_path.stem

        try:
            from kiutils.symbol import SymbolLib

            src_lib = SymbolLib.from_file(src_file)
            symbol = None
            for s in src_lib.symbols:
                if s.entryName == entry_name:
                    symbol = s
                    break
            if not symbol:
                return

            if target_path.exists():
                target_lib = SymbolLib.from_file(str(target_path))
            else:
                target_lib = SymbolLib()

            target_lib.symbols = [s for s in target_lib.symbols if s.entryName != entry_name]
            target_lib.symbols.append(symbol)
            target_lib.to_file(str(target_path))

            if move:
                src_lib.symbols = [s for s in src_lib.symbols if s.entryName != entry_name]
                src_lib.to_file(src_file)
                self.backend.print_to_buffer(
                    tr("messages.library_moved", name=entry_name, sub=target_name)
                )
            else:
                self.backend.print_to_buffer(
                    tr("messages.library_copied", name=entry_name, sub=target_name)
                )

            logging.info(f"{'Moved' if move else 'Copied'} '{entry_name}' to '{target_name}'")

            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx,
                tr("messages.tab_library", count=self._library_count),
            )

        except Exception as e:
            logging.error(f"Failed to {'move' if move else 'copy'} symbol: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_library_copy_new(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._library_items):
            return

        src_file, entry_name = self._library_items[idx]
        src_dir = Path(src_file).parent

        base_name = Path(src_file).stem
        for pf in self.backend.config.get_available_profiles():
            sec = f"profile_{pf}"
            try:
                pf_lib = self.backend.config.config[sec].get("library_name", "")
                if pf_lib and base_name.startswith(pf_lib):
                    base_name = pf_lib
                    break
            except Exception:
                pass

        dlg = wx.TextEntryDialog(
            self, tr("messages.library_move_prompt"),
            tr("messages.library_copy_title"), ""
        )
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        sub_name = dlg.GetValue().strip().replace(" ", "_").replace("/", "_")
        dlg.Destroy()
        if not sub_name:
            return

        target_lib_name = f"{base_name}_{sub_name}"
        target_file = str(src_dir / f"{target_lib_name}.kicad_sym")
        self._do_move_or_copy(idx, target_file, move=False)

    def _on_library_delete(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._library_items):
            return

        sym_file, entry_name = self._library_items[idx]

        dlg = wx.MessageDialog(
            self,
            tr("messages.library_delete_confirm", name=entry_name),
            tr("messages.confirm_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        try:
            from kiutils.symbol import SymbolLib
            lib = SymbolLib.from_file(sym_file)
            lib.symbols = [s for s in lib.symbols if s.entryName != entry_name]
            lib.to_file(sym_file)
            self.backend.print_to_buffer(
                tr("messages.library_deleted_component", name=entry_name)
            )
            logging.info(f"Deleted symbol '{entry_name}' from {sym_file}")
            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx,
                tr("messages.tab_library", count=self._library_count),
            )
        except Exception as e:
            logging.error(f"Failed to delete symbol: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_create_library(self, event) -> None:
        dest_path = Path(self.backend.config.get_DEST_PATH())
        lib_name = self.backend.config.get_library_name()

        dlg = wx.TextEntryDialog(
            self,
            tr("messages.library_new_prompt"),
            tr("messages.library_new_title"),
            "",
        )
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            event.Skip()
            return

        sub_name = dlg.GetValue().strip().replace(" ", "_").replace("/", "_")
        dlg.Destroy()
        if not sub_name:
            event.Skip()
            return

        new_lib_name = f"{lib_name}_{sub_name}"
        new_file = dest_path / f"{new_lib_name}.kicad_sym"

        if new_file.exists():
            wx.MessageBox(
                f"'{new_lib_name}' already exists.",
                "Error",
                wx.OK | wx.ICON_WARNING,
            )
            event.Skip()
            return

        try:
            from kiutils.symbol import SymbolLib

            empty_lib = SymbolLib()
            empty_lib.to_file(str(new_file))

            lib_var = self.backend.config.get_library_variable()
            reg_settings = KiCad_Settings(
                self.backend.kicad_settings.SettingPath, path_prefix=lib_var
            )
            reg_settings.check_symbollib(
                f"{new_lib_name}.kicad_sym", add_if_possible=True
            )

            self.backend.print_to_buffer(
                tr("messages.library_created", name=new_lib_name)
            )
            self.backend.print_to_buffer(
                f"⚠ {tr('messages.library_restart_notice')}"
            )
            logging.info(f"Created new library: {new_file}")

            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx,
                tr("messages.tab_library", count=self._library_count),
            )

        except Exception as e:
            logging.error(f"Failed to create library: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

        event.Skip()

    def _on_reorganize_library(self, event) -> None:
        all_paths = self._get_all_library_paths()
        sym_files = []
        for dest_path in all_paths:
            sym_files.extend(dest_path.glob("*.kicad_sym"))

        total_symbols = 0
        for sym_file in sym_files:
            try:
                from kiutils.symbol import SymbolLib
                lib = SymbolLib.from_file(str(sym_file))
                total_symbols += len(lib.symbols)
            except Exception:
                pass

        dlg = wx.MessageDialog(
            self,
            tr("messages.library_reorganize_confirm", count=total_symbols),
            tr("messages.confirm_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            event.Skip()
            return
        dlg.Destroy()

        try:
            from kiutils.symbol import SymbolLib

            lib_name = self.backend.config.get_library_name()
            dest_path = Path(self.backend.config.get_DEST_PATH())
            moved = 0

            self.backend.print_to_buffer("Fetching component categories...")

            for sym_file in sym_files:
                lib = SymbolLib.from_file(str(sym_file))
                file_stem = sym_file.stem

                if file_stem != lib_name:
                    continue

                symbols_to_move = {}
                symbols_to_keep = []

                for symbol in lib.symbols:
                    props = {p.key: p.value for p in symbol.properties}
                    category = None

                    lcsc_id = props.get("LCSC Part", "")
                    if lcsc_id:
                        try:
                            results = search_components(lcsc_id, page_size=1)
                            if results and results[0].category:
                                category = results[0].category
                                self._fill_missing_metadata(symbol, props, results[0], lcsc_id)
                        except Exception:
                            pass

                    if not category:
                        ref = props.get("Reference", "")
                        ref_map = {
                            "U": "ICs", "IC": "ICs", "R": "Resistors",
                            "C": "Capacitors", "L": "Inductors",
                            "D": "Diodes", "Q": "Transistors",
                            "J": "Connectors", "P": "Connectors",
                            "SW": "Switches", "K": "Relays",
                            "LED": "LEDs", "F": "Fuses",
                        }
                        for prefix, cat in ref_map.items():
                            if ref.startswith(prefix):
                                category = cat
                                break

                    if category:
                        cat_key = category.replace(" ", "_").replace("/", "_")
                        if cat_key not in symbols_to_move:
                            symbols_to_move[cat_key] = []
                        symbols_to_move[cat_key].append(symbol)
                    else:
                        symbols_to_keep.append(symbol)

                for cat_key, symbols in symbols_to_move.items():
                    sub_lib_name = f"{lib_name}_{cat_key}"
                    sub_file = dest_path / f"{sub_lib_name}.kicad_sym"

                    if sub_file.exists():
                        sub_lib = SymbolLib.from_file(str(sub_file))
                    else:
                        sub_lib = SymbolLib()

                    existing_names = {s.entryName for s in sub_lib.symbols}
                    for sym in symbols:
                        if sym.entryName not in existing_names:
                            sub_lib.symbols.append(sym)
                            moved += 1
                        else:
                            symbols_to_keep.append(sym)

                    sub_lib.to_file(str(sub_file))

                    lib_var = self.backend.config.get_library_variable()
                    reg_settings = KiCad_Settings(
                        self.backend.kicad_settings.SettingPath, path_prefix=lib_var
                    )
                    reg_settings.check_symbollib(
                        f"{sub_lib_name}.kicad_sym", add_if_possible=True
                    )

                lib.symbols = symbols_to_keep
                lib.to_file(str(sym_file))

            self.backend.print_to_buffer(
                tr("messages.library_reorganize_done", moved=moved)
            )
            if moved > 0:
                self.backend.print_to_buffer(
                    f"⚠ {tr('messages.library_restart_notice')}"
                )
                wx.MessageBox(
                    tr("messages.library_restart_notice"),
                    "Info",
                    wx.OK | wx.ICON_INFORMATION,
                )
            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx, tr("messages.tab_library", count=self._library_count)
            )

        except Exception as e:
            logging.error(f"Reorganization failed: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

        event.Skip()

    @staticmethod
    def _fill_missing_metadata(symbol, existing_props: dict, api_result, lcsc_id: str) -> None:
        from datetime import date

        metadata_map = {
            "LCSC Part": lcsc_id,
            "OriginalSource": api_result.category or "",
            "ImportDate": str(date.today()),
            "ImportedBy": "CustomImportGUI",
        }
        if hasattr(api_result, "manufacturer"):
            metadata_map["Author"] = api_result.manufacturer or ""

        for key, value in metadata_map.items():
            if key not in existing_props and value:
                try:
                    from kiutils.items.common import Property
                    new_prop = Property(key=key, value=str(value))
                    new_prop.effects = symbol.properties[0].effects
                    symbol.properties.append(new_prop)
                except Exception:
                    pass

    def _on_organize_cat_changed(self, event) -> None:
        is_checked = self.m_check_organize_cat.IsChecked()
        self.backend.config.set_organize_by_category(is_checked)
        event.Skip()

    def _on_library_move(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._library_items):
            return

        src_file, entry_name = self._library_items[idx]
        src_dir = Path(src_file).parent

        base_name = Path(src_file).stem
        for pf in self.backend.config.get_available_profiles():
            sec = f"profile_{pf}"
            try:
                pf_lib = self.backend.config.config[sec].get("library_name", "")
                if pf_lib and base_name.startswith(pf_lib):
                    base_name = pf_lib
                    break
            except Exception:
                pass

        dlg = wx.TextEntryDialog(
            self, tr("messages.library_move_prompt"),
            tr("messages.library_move_title"), ""
        )
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        sub_name = dlg.GetValue().strip().replace(" ", "_").replace("/", "_")
        dlg.Destroy()
        if not sub_name:
            return

        target_lib_name = f"{base_name}_{sub_name}"
        target_file = src_dir / f"{target_lib_name}.kicad_sym"

        try:
            from kiutils.symbol import SymbolLib

            src_lib = SymbolLib.from_file(src_file)
            symbol = None
            for s in src_lib.symbols:
                if s.entryName == entry_name:
                    symbol = s
                    break
            if not symbol:
                return

            if target_file.exists():
                target_lib = SymbolLib.from_file(str(target_file))
            else:
                target_lib = SymbolLib()

            target_lib.symbols = [s for s in target_lib.symbols if s.entryName != entry_name]
            target_lib.symbols.append(symbol)
            target_lib.to_file(str(target_file))

            src_lib.symbols = [s for s in src_lib.symbols if s.entryName != entry_name]
            src_lib.to_file(src_file)

            lib_var = self.backend.config.get_library_variable()
            reg_settings = KiCad_Settings(
                self.backend.kicad_settings.SettingPath, path_prefix=lib_var
            )
            reg_settings.check_symbollib(
                f"{target_lib_name}.kicad_sym", add_if_possible=True
            )

            self.backend.print_to_buffer(
                tr("messages.library_moved", name=entry_name, sub=sub_name)
            )
            logging.info(f"Moved '{entry_name}' to sub-library '{sub_name}'")

            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx,
                tr("messages.tab_library", count=self._library_count),
            )

        except Exception as e:
            logging.error(f"Failed to move symbol: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_library_edit(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._library_items):
            return

        sym_file, entry_name = self._library_items[idx]

        try:
            from kiutils.symbol import SymbolLib
            lib = SymbolLib.from_file(sym_file)
            symbol = None
            for s in lib.symbols:
                if s.entryName == entry_name:
                    symbol = s
                    break
            if not symbol:
                return

            props = {p.key: p.value for p in symbol.properties}

            dlg = wx.Dialog(self, title=f"Edit: {entry_name}", size=wx.Size(500, 400))
            panel = wx.Panel(dlg)
            sizer = wx.BoxSizer(wx.VERTICAL)

            editable_keys = ["Value", "Reference", "Footprint", "Datasheet",
                             "Description", "OriginalSource", "LCSC Part",
                             "Author", "ImportDate"]

            controls = {}
            for key in editable_keys:
                row = wx.BoxSizer(wx.HORIZONTAL)
                label = wx.StaticText(panel, label=f"{key}:", size=wx.Size(120, -1))
                text = wx.TextCtrl(panel, value=props.get(key, ""))
                row.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 3)
                row.Add(text, 1, wx.ALL | wx.EXPAND, 3)
                sizer.Add(row, 0, wx.EXPAND)
                controls[key] = text

            btn_sizer = wx.StdDialogButtonSizer()
            btn_ok = wx.Button(panel, wx.ID_OK)
            btn_cancel = wx.Button(panel, wx.ID_CANCEL)
            btn_sizer.AddButton(btn_ok)
            btn_sizer.AddButton(btn_cancel)
            btn_sizer.Realize()
            sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

            panel.SetSizer(sizer)

            if dlg.ShowModal() == wx.ID_OK:
                for key, ctrl in controls.items():
                    new_val = ctrl.GetValue()
                    found = False
                    for p in symbol.properties:
                        if p.key == key:
                            p.value = new_val
                            found = True
                            break
                    if not found and new_val:
                        from kiutils.items.common import Property
                        new_prop = Property(key=key, value=new_val)
                        new_prop.effects = symbol.properties[0].effects
                        symbol.properties.append(new_prop)

                if symbol.entryName != controls["Value"].GetValue():
                    symbol.entryName = controls["Value"].GetValue()

                lib.to_file(sym_file)
                self.backend.print_to_buffer(f"Updated '{entry_name}'")
                logging.info(f"Edited symbol '{entry_name}' in {sym_file}")
                self._refresh_library_tab()
                self.notebook.SetPageText(
                    self._library_tab_idx,
                    tr("messages.tab_library", count=self._library_count),
                )

            dlg.Destroy()

        except Exception as e:
            logging.error(f"Failed to edit symbol: {e}")
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
