from typing import List

from PySide6.QtWidgets import QWidget
from SettingsDialog.settings_tab import SettingLayout, SettingsTab, SettingType
from SettingsManager import SettingsManager


class GeneralSettingsTab(SettingsTab):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.settings_layouts: List[SettingLayout] = [
            SettingLayout(
                category="Song Library",
                key="dont_add_duplicates",
                setting_type=SettingType.CHECKBOX,
                label="Don't Add Duplicates to Library:",
                action=lambda: self.update_checkbox_setting("dont_add_duplicates"),
            ),
            SettingLayout(
                category="Song Library",
                key="auto_scan_on_load",
                setting_type=SettingType.CHECKBOX,
                label="Auto Scan on Load (using ModArchive):",
                action=lambda: self.update_checkbox_setting("auto_scan_on_load"),
            ),
            SettingLayout(
                category="ModArchive",
                key="modarchive_member_id",
                setting_type=SettingType.EDIT_TEXT_NUMERIC,
                label="ModArchive Member ID:",
                action=lambda: self.update_line_edit_setting(
                    "modarchive_member_id", numeric=True
                ),
            ),
            SettingLayout(
                category="Recording",
                key="default_record_path",
                setting_type=SettingType.FOLDER,
                label="Default Record Path:",
                action=lambda: self.update_line_edit_setting("default_record_path"),
            ),
            SettingLayout(
                category="Recording",
                key="default_record_format",
                setting_type=SettingType.COMBOBOX,
                label="Default Record Format:",
                action=lambda: self.update_combobox_setting("default_record_format"),
            ),
            SettingLayout(
                category="Recording",
                key="mp3_bitrate",
                setting_type=SettingType.COMBOBOX,
                label="MP3 Bitrate:",
                action=lambda: self.update_combobox_setting("mp3_bitrate"),
            ),
            SettingLayout(
                category="Recording",
                key="ogg_quality",
                setting_type=SettingType.COMBOBOX,
                label="OGG Quality:",
                action=lambda: self.update_combobox_setting("ogg_quality"),
            ),
        ]

        self.create_layout()

    def load_settings(
        self,
        settings: SettingsManager,
    ) -> None:
        super().load_settings(settings)

        self.fill_combo_box(
            "default_record_format",
            ["ogg", "mp3", "wav", "flac"],
        )
        self.fill_combo_box(
            "mp3_bitrate",
            ["128k", "192k", "256k", "320k"],
        )
        self.fill_combo_box(
            "ogg_quality",
            [str(i) for i in range(0, 11)],
        )

        self.load_checkbox_setting("dont_add_duplicates", False)
        self.load_line_edit_setting("modarchive_member_id", "", numeric=True)
        self.load_line_edit_setting("default_record_path", "")
        self.load_combobox_setting("default_record_format", "ogg")
        self.load_combobox_setting("mp3_bitrate", "320k")
        self.load_combobox_setting("ogg_quality", "10")
        self.load_checkbox_setting("auto_scan_on_load", False)
