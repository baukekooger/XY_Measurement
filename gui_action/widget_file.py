from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from gui_design.file import Ui_Form


class FileWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.lineEdit_append_file.setDisabled(True)
        self.ui.toolButton_append_file.setDisabled(True)
        self.ui.checkBox_append_file.setChecked(False)
        self.filename = None

    def connect_signals_slots(self):
        self.ui.toolButton_directory.clicked.connect(self.select_filedir)
        self.ui.checkBox_append_file.clicked.connect(self.enable_append)
        self.ui.toolButton_append_file.clicked.connect(self.select_file_append)

    def disconnect_signals_slots(self):
        self.ui.toolButton_directory.clicked.disconnect()
        self.ui.checkBox_append_file.clicked.disconnect()
        self.ui.toolButton_append_file.clicked.disconnect()

    def select_filedir(self):
        filedir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.ui.lineEdit_directory.setText(filedir)

    def enable_append(self):
        if self.ui.checkBox_append_file.isChecked():
            self.ui.lineEdit_sample.setDisabled(True)
            self.ui.comboBox_substrate.setDisabled(True)
            self.ui.lineEdit_directory.setDisabled(True)
            self.ui.toolButton_directory.setDisabled(True)
            self.ui.lineEdit_append_file.setEnabled(True)
            self.ui.toolButton_append_file.setEnabled(True)
        else:
            self.ui.lineEdit_sample.setEnabled(True)
            self.ui.comboBox_substrate.setEnabled(True)
            self.ui.lineEdit_directory.setEnabled(True)
            self.ui.toolButton_directory.setEnabled(True)
            self.ui.lineEdit_append_file.setDisabled(True)
            self.ui.toolButton_append_file.setDisabled(True)

    def reset(self):
        self.ui.checkBox_append_file.setChecked(False)
        self.ui.lineEdit_sample.setEnabled(True)
        self.ui.comboBox_substrate.setEnabled(True)
        self.ui.lineEdit_directory.setEnabled(True)
        self.ui.toolButton_directory.setEnabled(True)
        self.ui.lineEdit_append_file.setDisabled(True)
        self.ui.toolButton_append_file.setDisabled(True)

    def select_file_append(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Select File to Append to", "/",
                                                         "Measurement files (*.hdf5)")
        self.ui.lineEdit_append_file.setText(filename[0])




if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FileWidget()
    window.show()
    sys.exit(app.exec_())

