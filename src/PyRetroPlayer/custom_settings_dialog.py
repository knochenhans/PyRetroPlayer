from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
)
from SettingsDialog import SettingsDialog
from SettingsManager import SettingsManager

from PyRetroPlayer.general_settings_tab import GeneralSettingsTab


class CustomSettingsDialog(SettingsDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.application_settings: Optional[SettingsManager] = None

        self.general_settings_tab = GeneralSettingsTab(self)

        self.tab_widget.addTab(self.general_settings_tab, "General Options")

    def load_settings(
        self,
        application_settings: SettingsManager,
    ) -> None:
        self.application_settings = application_settings

        self.general_settings_tab.load_settings(application_settings)

    def on_ok_clicked(self) -> None:
        if self.application_settings:
            self.settings_changed.emit()
        self.accept()
