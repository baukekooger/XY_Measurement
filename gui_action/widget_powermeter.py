from PyQt5 import QtWidgets
from gui_design.powermeter import Ui_Form


class PowerMeterWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

    def connect_signals_slots(self):
        pass


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = PowerMeterWidget()
    window.show()
    sys.exit(app.exec_())
