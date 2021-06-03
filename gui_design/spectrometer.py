# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'spectrometer.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(436, 101)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_integrationtime = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_integrationtime.sizePolicy().hasHeightForWidth())
        self.label_integrationtime.setSizePolicy(sizePolicy)
        self.label_integrationtime.setMinimumSize(QtCore.QSize(150, 0))
        self.label_integrationtime.setObjectName("label_integrationtime")
        self.horizontalLayout.addWidget(self.label_integrationtime)
        self.doubleSpinBox_integrationtime = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.doubleSpinBox_integrationtime.setObjectName("doubleSpinBox_integrationtime")
        self.horizontalLayout.addWidget(self.doubleSpinBox_integrationtime)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_averagemeasurements = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_averagemeasurements.sizePolicy().hasHeightForWidth())
        self.label_averagemeasurements.setSizePolicy(sizePolicy)
        self.label_averagemeasurements.setMinimumSize(QtCore.QSize(150, 0))
        self.label_averagemeasurements.setObjectName("label_averagemeasurements")
        self.horizontalLayout_2.addWidget(self.label_averagemeasurements)
        self.doubleSpinBox_averagemeasurements = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.doubleSpinBox_averagemeasurements.setObjectName("doubleSpinBox_averagemeasurements")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_averagemeasurements)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox.setTitle(_translate("Form", "Spectrometer"))
        self.label_integrationtime.setText(_translate("Form", "integration time (ms)"))
        self.label_averagemeasurements.setText(_translate("Form", "average measurements (#)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

