from PyQt5 import QtWidgets
from gui_design.laser import Ui_Form


class LaserWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

    def connect_signals_slots(self):
        pass

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = LaserWidget()
    window.show()
    sys.exit(app.exec_())
