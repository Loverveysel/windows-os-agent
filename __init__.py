from PyQt5.QtWidgets import QApplication
import sys
from src.views import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Load optional style
    try:
        with open("./src/ui/styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())