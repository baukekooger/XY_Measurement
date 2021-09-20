from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from gui_design.file import Ui_Form


class FileWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.filename = None

    def connect_signals_slots(self):
        self.ui.toolButton_directory.clicked.connect(self.select_filedir)

    def disconnect_signals_slots(self):
        self.ui.toolButton_directory.clicked.disconnect()

    def select_filedir(self):
        filedir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.ui.lineEdit_directory.setText(filedir)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FileWidget()
    window.show()
    sys.exit(app.exec_())

