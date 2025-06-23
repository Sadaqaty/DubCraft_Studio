from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal


class LanguageSelectorWidget(QWidget):
    languageChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Select Target Language:")
        self.combo = QComboBox()
        self.combo.addItems(
            [
                "English",
                "Spanish",
                "French",
                "German",
                "Chinese",
                "Japanese",
                "Korean",
                "Italian",
                "Portuguese",
                "Russian",
                "Hindi",
                "Arabic",
            ]
        )
        self.combo.currentTextChanged.connect(self.languageChanged.emit)
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addStretch()

    def get_language(self):
        return self.combo.currentText()
