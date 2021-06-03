# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(503, 426)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_file = QtWidgets.QGroupBox(Form)
        self.groupBox_file.setObjectName("groupBox_file")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_file)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_filename = QtWidgets.QLabel(self.groupBox_file)
        self.label_filename.setMinimumSize(QtCore.QSize(50, 0))
        self.label_filename.setObjectName("label_filename")
        self.horizontalLayout_3.addWidget(self.label_filename)
        self.lineEdit_filename = QtWidgets.QLineEdit(self.groupBox_file)
        self.lineEdit_filename.setObjectName("lineEdit_filename")
        self.horizontalLayout_3.addWidget(self.lineEdit_filename)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_comments = QtWidgets.QLabel(self.groupBox_file)
        self.label_comments.setMinimumSize(QtCore.QSize(50, 0))
        self.label_comments.setObjectName("label_comments")
        self.horizontalLayout_2.addWidget(self.label_comments)
        self.plainTextEdit_comments = QtWidgets.QPlainTextEdit(self.groupBox_file)
        self.plainTextEdit_comments.setObjectName("plainTextEdit_comments")
        self.horizontalLayout_2.addWidget(self.plainTextEdit_comments)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_directory = QtWidgets.QLabel(self.groupBox_file)
        self.label_directory.setMinimumSize(QtCore.QSize(50, 0))
        self.label_directory.setObjectName("label_directory")
        self.horizontalLayout.addWidget(self.label_directory)
        self.lineEdit_directory = QtWidgets.QLineEdit(self.groupBox_file)
        self.lineEdit_directory.setObjectName("lineEdit_directory")
        self.horizontalLayout.addWidget(self.lineEdit_directory)
        self.toolButton = QtWidgets.QToolButton(self.groupBox_file)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_file, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_file.setTitle(_translate("Form", "General information"))
        self.label_filename.setText(_translate("Form", "filename"))
        self.label_comments.setText(_translate("Form", "comments"))
        self.label_directory.setText(_translate("Form", "directory"))
        self.toolButton.setText(_translate("Form", "..."))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

