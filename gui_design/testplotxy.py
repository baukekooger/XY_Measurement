# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'testplotxy.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(445, 404)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_plot = XYStagePlotWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_plot.sizePolicy().hasHeightForWidth())
        self.widget_plot.setSizePolicy(sizePolicy)
        self.widget_plot.setObjectName("widget_plot")
        self.verticalLayout.addWidget(self.widget_plot)
        self.pushButton_home = QtWidgets.QPushButton(Form)
        self.pushButton_home.setObjectName("pushButton_home")
        self.verticalLayout.addWidget(self.pushButton_home)
        self.pushButton_move = QtWidgets.QPushButton(Form)
        self.pushButton_move.setObjectName("pushButton_move")
        self.verticalLayout.addWidget(self.pushButton_move)
        self.pushButton_plot = QtWidgets.QPushButton(Form)
        self.pushButton_plot.setObjectName("pushButton_plot")
        self.verticalLayout.addWidget(self.pushButton_plot)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(Form)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(Form)
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        self.horizontalLayout.addWidget(self.doubleSpinBox_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_home.setText(_translate("Form", "Home "))
        self.pushButton_move.setText(_translate("Form", "Move"))
        self.pushButton_plot.setText(_translate("Form", "Test Plot"))
        self.label.setText(_translate("Form", "x"))
        self.label_2.setText(_translate("Form", "y"))

from gui_action.plot_xystage import XYStagePlotWidget

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

