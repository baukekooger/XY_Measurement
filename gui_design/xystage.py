# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'xystage.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(494, 394)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(0, 0))
        self.gridLayout_5 = QtWidgets.QGridLayout(Form)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.stackedWidget = QtWidgets.QStackedWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page_experiment = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.page_experiment.sizePolicy().hasHeightForWidth())
        self.page_experiment.setSizePolicy(sizePolicy)
        self.page_experiment.setObjectName("page_experiment")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.page_experiment)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_experiment = QtWidgets.QGroupBox(self.page_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_experiment.sizePolicy().hasHeightForWidth())
        self.groupBox_experiment.setSizePolicy(sizePolicy)
        self.groupBox_experiment.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox_experiment.setObjectName("groupBox_experiment")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_experiment)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_x_num = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_x_num.sizePolicy().hasHeightForWidth())
        self.label_x_num.setSizePolicy(sizePolicy)
        self.label_x_num.setMinimumSize(QtCore.QSize(120, 0))
        self.label_x_num.setObjectName("label_x_num")
        self.horizontalLayout_4.addWidget(self.label_x_num)
        self.spinBox_x_num = QtWidgets.QSpinBox(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_x_num.sizePolicy().hasHeightForWidth())
        self.spinBox_x_num.setSizePolicy(sizePolicy)
        self.spinBox_x_num.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_x_num.setMinimum(1)
        self.spinBox_x_num.setMaximum(100)
        self.spinBox_x_num.setObjectName("spinBox_x_num")
        self.horizontalLayout_4.addWidget(self.spinBox_x_num)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_y_num = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_y_num.sizePolicy().hasHeightForWidth())
        self.label_y_num.setSizePolicy(sizePolicy)
        self.label_y_num.setMinimumSize(QtCore.QSize(120, 0))
        self.label_y_num.setObjectName("label_y_num")
        self.horizontalLayout_7.addWidget(self.label_y_num)
        self.spinBox_y_num = QtWidgets.QSpinBox(self.groupBox_experiment)
        self.spinBox_y_num.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_y_num.setMinimum(1)
        self.spinBox_y_num.setMaximum(100)
        self.spinBox_y_num.setObjectName("spinBox_y_num")
        self.horizontalLayout_7.addWidget(self.spinBox_y_num)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_x_off_left = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_x_off_left.sizePolicy().hasHeightForWidth())
        self.label_x_off_left.setSizePolicy(sizePolicy)
        self.label_x_off_left.setMinimumSize(QtCore.QSize(120, 0))
        self.label_x_off_left.setObjectName("label_x_off_left")
        self.horizontalLayout_8.addWidget(self.label_x_off_left)
        self.spinBox_x_off_left = QtWidgets.QSpinBox(self.groupBox_experiment)
        self.spinBox_x_off_left.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_x_off_left.setMinimum(-100)
        self.spinBox_x_off_left.setMaximum(100)
        self.spinBox_x_off_left.setProperty("value", 0)
        self.spinBox_x_off_left.setObjectName("spinBox_x_off_left")
        self.horizontalLayout_8.addWidget(self.spinBox_x_off_left)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_x_off_right = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_x_off_right.sizePolicy().hasHeightForWidth())
        self.label_x_off_right.setSizePolicy(sizePolicy)
        self.label_x_off_right.setMinimumSize(QtCore.QSize(120, 0))
        self.label_x_off_right.setObjectName("label_x_off_right")
        self.horizontalLayout_3.addWidget(self.label_x_off_right)
        self.spinBox_x_off_right = QtWidgets.QSpinBox(self.groupBox_experiment)
        self.spinBox_x_off_right.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_x_off_right.setMinimum(-100)
        self.spinBox_x_off_right.setMaximum(100)
        self.spinBox_x_off_right.setProperty("value", 0)
        self.spinBox_x_off_right.setObjectName("spinBox_x_off_right")
        self.horizontalLayout_3.addWidget(self.spinBox_x_off_right)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_11.setSpacing(6)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_y_off_bottom = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_y_off_bottom.sizePolicy().hasHeightForWidth())
        self.label_y_off_bottom.setSizePolicy(sizePolicy)
        self.label_y_off_bottom.setMinimumSize(QtCore.QSize(120, 0))
        self.label_y_off_bottom.setObjectName("label_y_off_bottom")
        self.horizontalLayout_11.addWidget(self.label_y_off_bottom)
        self.spinBox_y_off_bottom = QtWidgets.QSpinBox(self.groupBox_experiment)
        self.spinBox_y_off_bottom.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_y_off_bottom.setMinimum(-100)
        self.spinBox_y_off_bottom.setMaximum(100)
        self.spinBox_y_off_bottom.setProperty("value", 0)
        self.spinBox_y_off_bottom.setObjectName("spinBox_y_off_bottom")
        self.horizontalLayout_11.addWidget(self.spinBox_y_off_bottom)
        self.verticalLayout.addLayout(self.horizontalLayout_11)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_y_off_top = QtWidgets.QLabel(self.groupBox_experiment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_y_off_top.sizePolicy().hasHeightForWidth())
        self.label_y_off_top.setSizePolicy(sizePolicy)
        self.label_y_off_top.setMinimumSize(QtCore.QSize(120, 0))
        self.label_y_off_top.setObjectName("label_y_off_top")
        self.horizontalLayout.addWidget(self.label_y_off_top)
        self.spinBox_y_off_top = QtWidgets.QSpinBox(self.groupBox_experiment)
        self.spinBox_y_off_top.setMinimumSize(QtCore.QSize(60, 0))
        self.spinBox_y_off_top.setMinimum(-100)
        self.spinBox_y_off_top.setMaximum(100)
        self.spinBox_y_off_top.setProperty("value", 0)
        self.spinBox_y_off_top.setObjectName("spinBox_y_off_top")
        self.horizontalLayout.addWidget(self.spinBox_y_off_top)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_experiment, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_experiment)
        self.page_alignment = QtWidgets.QWidget()
        self.page_alignment.setObjectName("page_alignment")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.page_alignment)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setSpacing(0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox_alignment = QtWidgets.QGroupBox(self.page_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_alignment.sizePolicy().hasHeightForWidth())
        self.groupBox_alignment.setSizePolicy(sizePolicy)
        self.groupBox_alignment.setObjectName("groupBox_alignment")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_alignment)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_x = QtWidgets.QLabel(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_x.sizePolicy().hasHeightForWidth())
        self.label_x.setSizePolicy(sizePolicy)
        self.label_x.setMinimumSize(QtCore.QSize(35, 0))
        self.label_x.setObjectName("label_x")
        self.horizontalLayout_9.addWidget(self.label_x)
        self.doubleSpinBox_x = QtWidgets.QDoubleSpinBox(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_x.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_x.setSizePolicy(sizePolicy)
        self.doubleSpinBox_x.setAccessibleDescription("")
        self.doubleSpinBox_x.setFrame(True)
        self.doubleSpinBox_x.setPrefix("")
        self.doubleSpinBox_x.setMaximum(100.0)
        self.doubleSpinBox_x.setProperty("value", 100.0)
        self.doubleSpinBox_x.setObjectName("doubleSpinBox_x")
        self.horizontalLayout_9.addWidget(self.doubleSpinBox_x)
        self.label_x_value = QtWidgets.QLabel(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_x_value.sizePolicy().hasHeightForWidth())
        self.label_x_value.setSizePolicy(sizePolicy)
        self.label_x_value.setMinimumSize(QtCore.QSize(75, 0))
        self.label_x_value.setAlignment(QtCore.Qt.AlignCenter)
        self.label_x_value.setObjectName("label_x_value")
        self.horizontalLayout_9.addWidget(self.label_x_value)
        self.checkBox_homed_x = QtWidgets.QCheckBox(self.groupBox_alignment)
        self.checkBox_homed_x.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_homed_x.sizePolicy().hasHeightForWidth())
        self.checkBox_homed_x.setSizePolicy(sizePolicy)
        self.checkBox_homed_x.setMinimumSize(QtCore.QSize(65, 0))
        self.checkBox_homed_x.setStyleSheet("QCheckBox::indicator:checked\n"
"{\n"
"background-color: rgb(0, 198, 6)\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked\n"
"{\n"
"background-color: rgb(202, 0, 3);\n"
"}")
        self.checkBox_homed_x.setChecked(False)
        self.checkBox_homed_x.setTristate(False)
        self.checkBox_homed_x.setObjectName("checkBox_homed_x")
        self.horizontalLayout_9.addWidget(self.checkBox_homed_x)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_y = QtWidgets.QLabel(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_y.sizePolicy().hasHeightForWidth())
        self.label_y.setSizePolicy(sizePolicy)
        self.label_y.setMinimumSize(QtCore.QSize(35, 0))
        self.label_y.setObjectName("label_y")
        self.horizontalLayout_2.addWidget(self.label_y)
        self.doubleSpinBox_y = QtWidgets.QDoubleSpinBox(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_y.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_y.setSizePolicy(sizePolicy)
        self.doubleSpinBox_y.setMaximum(100.0)
        self.doubleSpinBox_y.setProperty("value", 100.0)
        self.doubleSpinBox_y.setObjectName("doubleSpinBox_y")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_y)
        self.label_y_value = QtWidgets.QLabel(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_y_value.sizePolicy().hasHeightForWidth())
        self.label_y_value.setSizePolicy(sizePolicy)
        self.label_y_value.setMinimumSize(QtCore.QSize(75, 0))
        self.label_y_value.setAlignment(QtCore.Qt.AlignCenter)
        self.label_y_value.setObjectName("label_y_value")
        self.horizontalLayout_2.addWidget(self.label_y_value)
        self.checkBox_homed_y = QtWidgets.QCheckBox(self.groupBox_alignment)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_homed_y.sizePolicy().hasHeightForWidth())
        self.checkBox_homed_y.setSizePolicy(sizePolicy)
        self.checkBox_homed_y.setMinimumSize(QtCore.QSize(65, 0))
        self.checkBox_homed_y.setStyleSheet("QCheckBox::indicator:checked\n"
"{\n"
"background-color: rgb(0, 198, 6)\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked\n"
"{\n"
"background-color: rgb(202, 0, 3);\n"
"}")
        self.checkBox_homed_y.setObjectName("checkBox_homed_y")
        self.horizontalLayout_2.addWidget(self.checkBox_homed_y)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.pushButton_home_motors = QtWidgets.QPushButton(self.groupBox_alignment)
        self.pushButton_home_motors.setObjectName("pushButton_home_motors")
        self.verticalLayout_2.addWidget(self.pushButton_home_motors)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_alignment, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_alignment)
        self.gridLayout_5.addWidget(self.stackedWidget, 0, 0, 1, 1)

        self.retranslateUi(Form)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_experiment.setTitle(_translate("Form", "XY Stages"))
        self.label_x_num.setText(_translate("Form", "x num (#)"))
        self.label_y_num.setText(_translate("Form", "y num (#)"))
        self.label_x_off_left.setText(_translate("Form", "x off left (0-100)"))
        self.label_x_off_right.setText(_translate("Form", "x off right (0-100)"))
        self.label_y_off_bottom.setText(_translate("Form", "y off bottom (0-100)"))
        self.label_y_off_top.setText(_translate("Form", "y off top (0-100)"))
        self.groupBox_alignment.setTitle(_translate("Form", "XY Stages"))
        self.label_x.setText(_translate("Form", "x (mm)"))
        self.label_x_value.setText(_translate("Form", "0.00 mm"))
        self.checkBox_homed_x.setText(_translate("Form", "homed"))
        self.label_y.setText(_translate("Form", "y (mm)"))
        self.label_y_value.setText(_translate("Form", "0.00 mm"))
        self.checkBox_homed_y.setText(_translate("Form", "homed"))
        self.pushButton_home_motors.setText(_translate("Form", "home motors"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

