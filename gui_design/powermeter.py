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
        Form.resize(231, 230)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.gridLayout_4 = QtWidgets.QGridLayout(Form)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.stackedWidget = QtWidgets.QStackedWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page_experiment = QtWidgets.QWidget()
        self.page_experiment.setObjectName("page_experiment")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.page_experiment)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.stackedWidget.addWidget(self.page_experiment)
        self.page_alignment = QtWidgets.QWidget()
        self.page_alignment.setObjectName("page_alignment")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.page_alignment)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox_powermeter_alignment = QtWidgets.QGroupBox(self.page_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_powermeter_alignment.sizePolicy().hasHeightForWidth())
        self.groupBox_powermeter_alignment.setSizePolicy(sizePolicy)
        self.groupBox_powermeter_alignment.setObjectName("groupBox_powermeter_alignment")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_powermeter_alignment)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_power_title = QtWidgets.QLabel(self.groupBox_powermeter_alignment)
        self.label_power_title.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.label_power_title.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_power_title.setObjectName("label_power_title")
        self.horizontalLayout_3.addWidget(self.label_power_title)
        self.label_power_value_unit = QtWidgets.QLabel(self.groupBox_powermeter_alignment)
        self.label_power_value_unit.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_power_value_unit.setObjectName("label_power_value_unit")
        self.horizontalLayout_3.addWidget(self.label_power_value_unit)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.pushButton_zero = QtWidgets.QPushButton(self.groupBox_powermeter_alignment)
        self.pushButton_zero.setObjectName("pushButton_zero")
        self.gridLayout.addWidget(self.pushButton_zero, 1, 0, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_powermeter_alignment, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_alignment)
        self.gridLayout_4.addWidget(self.stackedWidget, 0, 0, 1, 1)

        self.retranslateUi(Form)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_powermeter_alignment.setTitle(_translate("Form", "Powermeter"))
        self.label_power_title.setText(_translate("Form", "power "))
        self.label_power_value_unit.setText(_translate("Form", "300 uW"))
        self.pushButton_zero.setText(_translate("Form", "Zero Measurement"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

