from PyQt5 import QtWidgets
from gui_design.file import Ui_Form


class FileWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FileWidget()
    window.show()
    sys.exit(app.exec_())

