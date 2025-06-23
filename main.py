from ui.main_window import DubCraftMainWindow
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DubCraftMainWindow()
    window.show()
    sys.exit(app.exec())
