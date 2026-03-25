"""
Profile management mixin for ImpartFrontend.
Handles profile CRUD, library config changes, and settings persistence.
"""

import json
import logging

import wx

try:
    from .i18n import _ as tr
except ImportError:
    from i18n import _ as tr


class ProfileMixin:
    """Mixin providing profile management functionality."""

    def _add_profile_controls(self) -> None:
        main_sizer = self.GetSizer()
        if not main_sizer:
            logging.warning("Could not find main sizer")
            return

        insert_index = None
        for i, item in enumerate(main_sizer.GetChildren()):
            widget = item.GetWindow()
            if widget == self.m_dirPicker_librarypath:
                insert_index = i + 1
                break

        if insert_index is None:
            logging.warning("Could not find library path picker")
            insert_index = len(main_sizer.GetChildren())

        # Profile selector
        profile_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._profile_label = wx.StaticText(self, wx.ID_ANY, tr("gui.profile_label"))
        self._profile_label.SetMinSize(wx.Size(150, -1))
        self._profile_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        profile_sizer.Add(self._profile_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        available_profiles = self.backend.config.get_available_profiles()
        current_profile = self.backend.config.get_current_profile()
        self.m_choice_profile = wx.Choice(self, wx.ID_ANY, choices=available_profiles)

        if current_profile in available_profiles:
            self.m_choice_profile.SetStringSelection(current_profile)
        elif "CustomLibrary" in available_profiles:
            self.m_choice_profile.SetStringSelection("CustomLibrary")
        else:
            self.m_choice_profile.SetSelection(0)

        self.m_choice_profile.SetMinSize(wx.Size(200, -1))
        self.m_choice_profile.SetToolTip(tr("tooltips.profile_select"))
        profile_sizer.Add(self.m_choice_profile, 0, wx.ALL, 5)

        self.m_btn_save_profile = wx.Button(self, wx.ID_ANY, tr("gui.save_as"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_btn_save_profile.SetToolTip(tr("tooltips.save_profile"))
        profile_sizer.Add(self.m_btn_save_profile, 0, wx.ALL, 5)

        self.m_btn_delete_profile = wx.Button(self, wx.ID_ANY, tr("gui.delete"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_btn_delete_profile.SetToolTip(tr("tooltips.delete_profile"))
        profile_sizer.Add(self.m_btn_delete_profile, 0, wx.ALL, 5)

        main_sizer.Insert(insert_index, profile_sizer, 0, wx.EXPAND | wx.ALL, 5)
        insert_index += 1

        # Library name and env variable
        lib_config_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._lib_name_label = wx.StaticText(self, wx.ID_ANY, tr("gui.library_name_label"))
        self._lib_name_label.SetMinSize(wx.Size(150, -1))
        lib_config_sizer.Add(self._lib_name_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_textCtrl_library_name = wx.TextCtrl(
            self, wx.ID_ANY,
            self.backend.config.get_library_name(),
            wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_textCtrl_library_name.SetMinSize(wx.Size(200, -1))
        self.m_textCtrl_library_name.SetToolTip(tr("tooltips.library_name"))
        lib_config_sizer.Add(self.m_textCtrl_library_name, 1, wx.ALL | wx.EXPAND, 5)

        self._env_var_label = wx.StaticText(self, wx.ID_ANY, tr("gui.env_var_label"))
        self._env_var_label.SetMinSize(wx.Size(100, -1))
        lib_config_sizer.Add(self._env_var_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_textCtrl_library_var = wx.TextCtrl(
            self, wx.ID_ANY,
            self.backend.config.get_library_variable(),
            wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_textCtrl_library_var.SetMinSize(wx.Size(180, -1))
        self.m_textCtrl_library_var.SetToolTip(tr("tooltips.env_var"))
        lib_config_sizer.Add(self.m_textCtrl_library_var, 0, wx.ALL, 5)

        main_sizer.Insert(insert_index, lib_config_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Bind events
        self.m_choice_profile.Bind(wx.EVT_CHOICE, self._on_profile_selected)
        self.m_btn_save_profile.Bind(wx.EVT_BUTTON, self._on_save_profile)
        self.m_btn_delete_profile.Bind(wx.EVT_BUTTON, self._on_delete_profile)
        self.m_textCtrl_library_name.Bind(wx.EVT_TEXT, self._on_library_config_changed)
        self.m_textCtrl_library_var.Bind(wx.EVT_TEXT, self._on_library_config_changed)

        self.Layout()

    def _on_profile_selected(self, event) -> None:
        selected_profile = self.m_choice_profile.GetStringSelection()
        if not selected_profile:
            return

        self._loading_profile = True

        if self.backend.config.load_profile(selected_profile):
            self.m_dirPicker_sourcepath.SetPath(self.backend.config.get_SRC_PATH())
            self.m_dirPicker_librarypath.SetPath(self.backend.config.get_DEST_PATH())
            self.m_textCtrl_library_name.SetValue(self.backend.config.get_library_name())
            self.m_textCtrl_library_var.SetValue(self.backend.config.get_library_variable())

            self.backend.importer.set_library_name(self.backend.config.get_library_name())
            self.backend.importer.KICAD_3RD_PARTY_LINK = self.backend.config.get_library_variable()
            self.backend.importer.set_DEST_PATH(self.backend.config.get_DEST_PATH())

            self.backend.print_to_buffer(f"\n✓ {tr('messages.profile_loaded', name=selected_profile)}")
            self.backend.print_to_buffer(f"  • {tr('messages.profile_library', name=self.backend.config.get_library_name())}")
            self.backend.print_to_buffer(f"  • {tr('messages.profile_variable', name=self.backend.config.get_library_variable())}")
            self.backend.print_to_buffer(f"  • {tr('messages.profile_destination', path=self.backend.config.get_DEST_PATH())}\n")

            self._refresh_library_tab()
            self.notebook.SetPageText(
                self._library_tab_idx,
                tr("messages.tab_library", count=self._library_count),
            )

        self._loading_profile = False
        event.Skip()

    def _on_library_config_changed(self, event) -> None:
        if self._loading_profile:
            event.Skip()
            return

        lib_name = self.m_textCtrl_library_name.GetValue().strip()
        lib_var = self.m_textCtrl_library_var.GetValue().strip()

        if lib_name and lib_name != self.backend.config.get_library_name():
            self.backend.config.set_library_name(lib_name)
            self.backend.importer.set_library_name(lib_name)
            logging.info(f"Library name changed to: {lib_name}")

        if lib_var and lib_var != self.backend.config.get_library_variable():
            self.backend.config.set_library_variable(lib_var)
            self.backend.importer.KICAD_3RD_PARTY_LINK = lib_var
            logging.info(f"Library variable changed to: {lib_var}")

        event.Skip()

    def _on_save_profile(self, event) -> None:
        dlg = wx.TextEntryDialog(
            self,
            tr("messages.save_profile_prompt"),
            tr("messages.save_profile_title"),
            ""
        )
        if dlg.ShowModal() == wx.ID_OK:
            profile_name = dlg.GetValue().strip()
            if profile_name and profile_name != "Default":
                if self.backend.config.save_current_as_profile(profile_name):
                    available_profiles = self.backend.config.get_available_profiles()
                    self.m_choice_profile.Clear()
                    self.m_choice_profile.AppendItems(available_profiles)
                    self.m_choice_profile.SetStringSelection(profile_name)
                    self.backend.print_to_buffer(f"\n✓ {tr('messages.profile_saved', name=profile_name)}\n")
        dlg.Destroy()
        event.Skip()

    def _on_delete_profile(self, event) -> None:
        selected_profile = self.m_choice_profile.GetStringSelection()
        if not selected_profile or selected_profile == "Default":
            wx.MessageBox(tr("messages.cannot_delete_default"), "Error", wx.OK | wx.ICON_WARNING)
            return

        dlg = wx.MessageDialog(
            self,
            tr("messages.confirm_delete_profile", name=selected_profile),
            tr("messages.confirm_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        if dlg.ShowModal() == wx.ID_YES:
            if self.backend.config.delete_profile(selected_profile):
                available_profiles = self.backend.config.get_available_profiles()
                self.m_choice_profile.Clear()
                self.m_choice_profile.AppendItems(available_profiles)
                self.m_choice_profile.SetSelection(0)
                self.backend.config.load_profile("Default")
                self.m_dirPicker_sourcepath.SetPath(self.backend.config.get_SRC_PATH())
                self.m_dirPicker_librarypath.SetPath(self.backend.config.get_DEST_PATH())
                self.backend.print_to_buffer(f"\n✓ {tr('messages.profile_deleted', name=selected_profile)}\n")
        dlg.Destroy()
        event.Skip()

    def _on_export_profile(self, event) -> None:
        profile_name = self.m_choice_profile.GetStringSelection() or "profile"
        dlg = wx.FileDialog(
            self,
            message=tr("gui.export_profile"),
            defaultFile=f"{profile_name}.json",
            wildcard="JSON files (*.json)|*.json",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            try:
                data = {
                    "profile_name": profile_name,
                    "library_name": self.backend.config.get_library_name(),
                    "library_variable": self.backend.config.get_library_variable(),
                    "source_path": self.backend.config.get_SRC_PATH(),
                    "dest_path": self.backend.config.get_DEST_PATH(),
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.backend.print_to_buffer(f"\n✓ {tr('messages.profile_exported', path=path)}\n")
            except Exception as e:
                logging.error(f"Failed to export profile: {e}")
                wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()
        event.Skip()

    def _on_import_profile(self, event) -> None:
        dlg = wx.FileDialog(
            self,
            message=tr("gui.import_profile"),
            wildcard="JSON files (*.json)|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                profile_name = data.get("profile_name", "ImportedProfile")
                lib_name = data.get("library_name", "")
                lib_var = data.get("library_variable", "")
                src_path = data.get("source_path", "")
                dest_path = data.get("dest_path", "")

                # Apply settings
                if lib_name:
                    self.backend.config.set_library_name(lib_name)
                    self.backend.importer.set_library_name(lib_name)
                    self.m_textCtrl_library_name.SetValue(lib_name)
                if lib_var:
                    self.backend.config.set_library_variable(lib_var)
                    self.backend.importer.KICAD_3RD_PARTY_LINK = lib_var
                    self.m_textCtrl_library_var.SetValue(lib_var)
                if src_path:
                    self.backend.config.set_SRC_PATH(src_path)
                    self.m_dirPicker_sourcepath.SetPath(src_path)
                if dest_path:
                    self.backend.config.set_DEST_PATH(dest_path)
                    self.backend.importer.set_DEST_PATH(dest_path)
                    self.m_dirPicker_librarypath.SetPath(dest_path)

                # Save as a named profile
                self.backend.config.save_current_as_profile(profile_name)
                available_profiles = self.backend.config.get_available_profiles()
                self.m_choice_profile.Clear()
                self.m_choice_profile.AppendItems(available_profiles)
                self.m_choice_profile.SetStringSelection(profile_name)

                self.backend.print_to_buffer(f"\n✓ {tr('messages.profile_imported', name=profile_name)}\n")
            except Exception as e:
                logging.error(f"Failed to import profile: {e}")
                wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()
        event.Skip()
