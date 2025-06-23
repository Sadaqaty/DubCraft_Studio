from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMovie
import os

class LoadingOverlay(QWidget):
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(30, 30, 40, 0.7);")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Spinner GIF
        spinner_path = os.path.join(os.path.dirname(__file__), '../assets/spinner.gif')
        self.spinner = QLabel()
        self.movie = QMovie(spinner_path)
        self.spinner.setMovie(self.movie)
        layout.addWidget(self.spinner)
        # Message
        self.label = QLabel(message)
        self.label.setStyleSheet("color: #fff; font-size: 1.2em; margin-top: 16px;")
        layout.addWidget(self.label)

    def show(self, message=None):
        if message:
            self.label.setText(message)
        self.setVisible(True)
        self.movie.start()
        self.raise_()

    def hide(self):
        self.setVisible(False)
        self.movie.stop() 