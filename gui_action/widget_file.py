from PyQt5 import QtWidgets
from gui_design.file import Ui_Form


class FileWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.lineEdit_appendfile.setDisabled(True)
        self.ui.toolButton_appendfile.setDisabled(True)
        self.ui.checkBox_append_file.setChecked(False)
        self.ui.toolButton_directory.clicked.connect(self.select_filedir)
        self.ui.checkBox_append_file.clicked.connect(self.enable_append)
        self.ui.toolButton_appendfile.clicked.connect(self.select_file_append)
        self.filename = None

    def select_filedir(self):
        filedir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.ui.lineEdit_directory.setText(filedir)

    def enable_append(self):
        if self.ui.checkBox_append_file.isChecked():
            self.ui.lineEdit_sample.setDisabled(True)
            self.ui.comboBox_substrate.setDisabled(True)
            self.ui.lineEdit_appendfile.setEnabled(True)
            self.ui.toolButton_appendfile.setEnabled(True)
        else:
            self.ui.lineEdit_sample.setEnabled(True)
            self.ui.comboBox_substrate.setEnabled(True)
            self.ui.lineEdit_appendfile.setDisabled(True)
            self.ui.toolButton_appendfile.setDisabled(True)

    def reset(self):
        self.ui.checkBox_append_file.setChecked(False)
        self.ui.lineEdit_sample.setEnabled(True)
        self.ui.comboBox_substrate.setEnabled(True)
        self.ui.lineEdit_appendfile.setDisabled(True)
        self.ui.toolButton_appendfile.setDisabled(True)

    def select_file_append(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Select File to Append to", "/",
                                                         "Measurement files (*.hdf5)")
        self.ui.lineEdit_appendfile.setText(filename[0])


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FileWidget()
    window.show()
    sys.exit(app.exec_())

