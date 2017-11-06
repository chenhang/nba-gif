import sys
from PyQt4.QtGui import QApplication, QMainWindow
from main_window import Ui_NbaGifMainWindow

app = QApplication(sys.argv)
window = QMainWindow()
ui = Ui_NbaGifMainWindow()
ui.setupUi(window)
window.show()
sys.exit(app.exec_())
