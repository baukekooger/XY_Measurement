# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(620, 464)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_fit_plots = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_fit_plots.setObjectName("pushButton_fit_plots")
        self.gridLayout.addWidget(self.pushButton_fit_plots, 3, 1, 1, 1)
        self.label_state = QtWidgets.QLabel(self.centralwidget)
        self.label_state.setObjectName("label_state")
        self.gridLayout.addWidget(self.label_state, 2, 1, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton_align_stop_align = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_align_stop_align.setObjectName("pushButton_align_stop_align")
        self.verticalLayout.addWidget(self.pushButton_align_stop_align)
        self.pushButton_start_stop_experiment = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_start_stop_experiment.setObjectName("pushButton_start_stop_experiment")
        self.verticalLayout.addWidget(self.pushButton_start_stop_experiment)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 4, 1)
        self.pushButton_random_number = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_random_number.setObjectName("pushButton_random_number")
        self.gridLayout.addWidget(self.pushButton_random_number, 0, 1, 1, 1)
        self.label_random_number = QtWidgets.QLabel(self.centralwidget)
        self.label_random_number.setObjectName("label_random_number")
        self.gridLayout.addWidget(self.label_random_number, 1, 1, 1, 1)
        self.widget_spectrometer = SpectrometerPlotWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_spectrometer.sizePolicy().hasHeightForWidth())
        self.widget_spectrometer.setSizePolicy(sizePolicy)
        self.widget_spectrometer.setObjectName("widget_spectrometer")
        self.gridLayout.addWidget(self.widget_spectrometer, 4, 0, 1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 620, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_fit_plots.setText(_translate("MainWindow", "Fit Plots"))
        self.label_state.setText(_translate("MainWindow", "State = "))
        self.pushButton_align_stop_align.setText(_translate("MainWindow", "Align/Stop Align"))
        self.pushButton_start_stop_experiment.setText(_translate("MainWindow", "Start Experiment"))
        self.pushButton_random_number.setText(_translate("MainWindow", "Random Number"))
        self.label_random_number.setText(_translate("MainWindow", "Random Number = "))

from gui_action.plot_spectrometer import SpectrometerPlotWidget

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

