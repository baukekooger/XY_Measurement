from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from gui_design.main import Ui_MainWindow
import time


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)

        self.ui.pushButton_transmission.clicked.connect(lambda state, page=0: self.goto_experiment(page))
        self.ui.pushButton_excitationEmission.clicked.connect(lambda state, page=1: self.goto_experiment(page))
        self.ui.pushButton_decay.clicked.connect(lambda state, page=2: self.goto_experiment(page))
        self.ui.pushButton_Return.clicked.connect(self.goto_home)
        self.ui.pushButton_StartExperiment.clicked.connect(self.start_experiment)


    def goto_experiment(self, page):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_experiment.setCurrentIndex(page)

    def goto_home(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def start_experiment(self):
        print('the experiment has started')
        self.ui.pushButton_Return.setEnabled(False)
        QTimer.singleShot(1000, self.experiment_finished)

    def experiment_finished(self):
        print('the experiment has finished')
        self.ui.pushButton_Return.setEnabled(True)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
