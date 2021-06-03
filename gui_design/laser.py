# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'laser.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(299, 131)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_laser = QtWidgets.QGroupBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_laser.sizePolicy().hasHeightForWidth())
        self.groupBox_laser.setSizePolicy(sizePolicy)
        self.groupBox_laser.setObjectName("groupBox_laser")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_laser)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_start = QtWidgets.QLabel(self.groupBox_laser)
        self.label_start.setObjectName("label_start")
        self.horizontalLayout_3.addWidget(self.label_start)
        self.doubleSpinBox_start = QtWidgets.QDoubleSpinBox(self.groupBox_laser)
        self.doubleSpinBox_start.setObjectName("doubleSpinBox_start")
        self.horizontalLayout_3.addWidget(self.doubleSpinBox_start)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_stop = QtWidgets.QLabel(self.groupBox_laser)
        self.label_stop.setObjectName("label_stop")
        self.horizontalLayout_2.addWidget(self.label_stop)
        self.doubleSpinBox_stop = QtWidgets.QDoubleSpinBox(self.groupBox_laser)
        self.doubleSpinBox_stop.setObjectName("doubleSpinBox_stop")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_stop)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_step = QtWidgets.QLabel(self.groupBox_laser)
        self.label_step.setObjectName("label_step")
        self.horizontalLayout.addWidget(self.label_step)
        self.doubleSpinBox_step = QtWidgets.QDoubleSpinBox(self.groupBox_laser)
        self.doubleSpinBox_step.setObjectName("doubleSpinBox_step")
        self.horizontalLayout.addWidget(self.doubleSpinBox_step)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_laser, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_laser.setTitle(_translate("Form", "Laser Wavelength"))
        self.label_start.setText(_translate("Form", "start (nm)"))
        self.label_stop.setText(_translate("Form", "stop (nm) "))
        self.label_step.setText(_translate("Form", "step (nm) "))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

