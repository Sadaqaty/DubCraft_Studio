from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
import os

class FileUploadWidget(QWidget):
    fileSelected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel("Drag & Drop your video here or click Browse")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 1.2em; color: #bdbdbd;")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.label)
        layout.addWidget(self.browse_btn)
        layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if self.is_video_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self.is_video_file(file_path):
                self.fileSelected.emit(file_path)
                self.label.setText(f"Selected: {os.path.basename(file_path)}")
                break

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.mov *.avi)")
        if file_path:
            self.fileSelected.emit(file_path)
            self.label.setText(f"Selected: {os.path.basename(file_path)}")

    def is_video_file(self, path):
        return os.path.splitext(path)[1].lower() in ['.mp4', '.mkv', '.mov', '.avi'] 