# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'powermeter.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(292, 73)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_powermeter = QtWidgets.QGroupBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_powermeter.sizePolicy().hasHeightForWidth())
        self.groupBox_powermeter.setSizePolicy(sizePolicy)
        self.groupBox_powermeter.setObjectName("groupBox_powermeter")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_powermeter)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_integrationtime = QtWidgets.QLabel(self.groupBox_powermeter)
        self.label_integrationtime.setObjectName("label_integrationtime")
        self.horizontalLayout.addWidget(self.label_integrationtime)
        self.doubleSpinBox_integrationtime = QtWidgets.QDoubleSpinBox(self.groupBox_powermeter)
        self.doubleSpinBox_integrationtime.setObjectName("doubleSpinBox_integrationtime")
        self.horizontalLayout.addWidget(self.doubleSpinBox_integrationtime)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_powermeter, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_powermeter.setTitle(_translate("Form", "Powermeter"))
        self.label_integrationtime.setText(_translate("Form", "integration time (ms)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

