from PyQt5 import QtWidgets
from gui_design.shuttercontrol import Ui_Form
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from PyQt5.QtCore import pyqtSlot, QTimer


class ShutterControlWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.shuttercontrol = QShutterControl()
        # self.shuttercontrol.connect()
        self.shutterstatus = False

        # self.connect_signals_slots()
        # self.hb = QTimer()
        # self.hb.setInterval(100)
        # self.hb.timeout.connect(self.shuttercontrol.measure)
        # self.hb.start()

    def connect_signals_slots(self):
        self.shuttercontrol.shutter_status.connect(self.handle_shutterstatus)
        self.ui.pushButton_shutter.clicked.connect(self.handle_shutter_open_close)

    def disconnect_signals_slots(self):
        self.shuttercontrol.shutter_status.disconnect()
        self.ui.pushButton_shutter.clicked.disconnect()

    @pyqtSlot(bool)
    def handle_shutterstatus(self, status):
        if status:
            self.shutterstatus = status
            self.ui.checkBox.setChecked(True)
        else:
            self.shutterstatus = False
            self.ui.checkBox.setChecked(False)

    def handle_shutter_open_close(self):
        self.shuttercontrol.measure()
        if self.shutterstatus:
            self.shuttercontrol.disable()
        else:
            self.shuttercontrol.enable()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ShutterControlWidget()
    window.show()
    sys.exit(app.exec_())
