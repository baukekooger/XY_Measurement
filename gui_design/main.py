# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(929, 705)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page_intro = QtWidgets.QWidget()
        self.page_intro.setObjectName("page_intro")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.page_intro)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_intro = QtWidgets.QGridLayout()
        self.gridLayout_intro.setObjectName("gridLayout_intro")
        self.label_intro_text = QtWidgets.QLabel(self.page_intro)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_intro_text.sizePolicy().hasHeightForWidth())
        self.label_intro_text.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label_intro_text.setFont(font)
        self.label_intro_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_intro_text.setObjectName("label_intro_text")
        self.gridLayout_intro.addWidget(self.label_intro_text, 0, 0, 1, 1)
        self.pushButton_transmission = QtWidgets.QPushButton(self.page_intro)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_transmission.sizePolicy().hasHeightForWidth())
        self.pushButton_transmission.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.pushButton_transmission.setFont(font)
        self.pushButton_transmission.setObjectName("pushButton_transmission")
        self.gridLayout_intro.addWidget(self.pushButton_transmission, 1, 0, 1, 1)
        self.pushButton_excitation_emission = QtWidgets.QPushButton(self.page_intro)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_excitation_emission.sizePolicy().hasHeightForWidth())
        self.pushButton_excitation_emission.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.pushButton_excitation_emission.setFont(font)
        self.pushButton_excitation_emission.setObjectName("pushButton_excitation_emission")
        self.gridLayout_intro.addWidget(self.pushButton_excitation_emission, 2, 0, 1, 1)
        self.pushButton_decay = QtWidgets.QPushButton(self.page_intro)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_decay.sizePolicy().hasHeightForWidth())
        self.pushButton_decay.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.pushButton_decay.setFont(font)
        self.pushButton_decay.setObjectName("pushButton_decay")
        self.gridLayout_intro.addWidget(self.pushButton_decay, 3, 0, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_intro, 0, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_intro)
        self.page_experiment = QtWidgets.QWidget()
        self.page_experiment.setObjectName("page_experiment")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.page_experiment)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.stackedWidget_experiment = QtWidgets.QStackedWidget(self.page_experiment)
        self.stackedWidget_experiment.setObjectName("stackedWidget_experiment")
        self.page_transmission = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.page_transmission.sizePolicy().hasHeightForWidth())
        self.page_transmission.setSizePolicy(sizePolicy)
        self.page_transmission.setObjectName("page_transmission")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.page_transmission)
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.splitter_transmission_vertical = QtWidgets.QSplitter(self.page_transmission)
        self.splitter_transmission_vertical.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_transmission_vertical.setObjectName("splitter_transmission_vertical")
        self.widget_spectrometerplot_transmission = SpectrometerPlotWidget(self.splitter_transmission_vertical)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_spectrometerplot_transmission.sizePolicy().hasHeightForWidth())
        self.widget_spectrometerplot_transmission.setSizePolicy(sizePolicy)
        self.widget_spectrometerplot_transmission.setObjectName("widget_spectrometerplot_transmission")
        self.scrollArea_transmission = QtWidgets.QScrollArea(self.splitter_transmission_vertical)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_transmission.sizePolicy().hasHeightForWidth())
        self.scrollArea_transmission.setSizePolicy(sizePolicy)
        self.scrollArea_transmission.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea_transmission.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea_transmission.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.scrollArea_transmission.setWidgetResizable(True)
        self.scrollArea_transmission.setObjectName("scrollArea_transmission")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 322, 420))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.widget_xystage_transmission = XYStageWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_xystage_transmission.sizePolicy().hasHeightForWidth())
        self.widget_xystage_transmission.setSizePolicy(sizePolicy)
        self.widget_xystage_transmission.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_xystage_transmission.setObjectName("widget_xystage_transmission")
        self.gridLayout_7.addWidget(self.widget_xystage_transmission, 1, 0, 1, 1)
        self.widget_file_transmission = FileWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_file_transmission.sizePolicy().hasHeightForWidth())
        self.widget_file_transmission.setSizePolicy(sizePolicy)
        self.widget_file_transmission.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_file_transmission.setObjectName("widget_file_transmission")
        self.gridLayout_7.addWidget(self.widget_file_transmission, 0, 0, 1, 1)
        self.widget_spectrometer_transmission = SpectrometerWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_spectrometer_transmission.sizePolicy().hasHeightForWidth())
        self.widget_spectrometer_transmission.setSizePolicy(sizePolicy)
        self.widget_spectrometer_transmission.setObjectName("widget_spectrometer_transmission")
        self.gridLayout_7.addWidget(self.widget_spectrometer_transmission, 5, 0, 1, 1)
        self.widget_xystageplot_transmission = XYStagePlotWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_xystageplot_transmission.sizePolicy().hasHeightForWidth())
        self.widget_xystageplot_transmission.setSizePolicy(sizePolicy)
        self.widget_xystageplot_transmission.setMinimumSize(QtCore.QSize(300, 300))
        self.widget_xystageplot_transmission.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.widget_xystageplot_transmission.setObjectName("widget_xystageplot_transmission")
        self.gridLayout_7.addWidget(self.widget_xystageplot_transmission, 2, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.gridLayout_7.addItem(spacerItem, 7, 0, 1, 1)
        self.scrollArea_transmission.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_6.addWidget(self.splitter_transmission_vertical, 0, 0, 1, 1)
        self.stackedWidget_experiment.addWidget(self.page_transmission)
        self.page_excitation_emission = QtWidgets.QWidget()
        self.page_excitation_emission.setObjectName("page_excitation_emission")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.page_excitation_emission)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.splitter_excitation_emission_vertical = QtWidgets.QSplitter(self.page_excitation_emission)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter_excitation_emission_vertical.sizePolicy().hasHeightForWidth())
        self.splitter_excitation_emission_vertical.setSizePolicy(sizePolicy)
        self.splitter_excitation_emission_vertical.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_excitation_emission_vertical.setObjectName("splitter_excitation_emission_vertical")
        self.splitter_excitation_emission_horizontal = QtWidgets.QSplitter(self.splitter_excitation_emission_vertical)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter_excitation_emission_horizontal.sizePolicy().hasHeightForWidth())
        self.splitter_excitation_emission_horizontal.setSizePolicy(sizePolicy)
        self.splitter_excitation_emission_horizontal.setOrientation(QtCore.Qt.Vertical)
        self.splitter_excitation_emission_horizontal.setObjectName("splitter_excitation_emission_horizontal")
        self.widget_spectrometerplot_excitation_emission = SpectrometerPlotWidget(self.splitter_excitation_emission_horizontal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_spectrometerplot_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_spectrometerplot_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_spectrometerplot_excitation_emission.setMinimumSize(QtCore.QSize(100, 100))
        self.widget_spectrometerplot_excitation_emission.setObjectName("widget_spectrometerplot_excitation_emission")
        self.widget_powermeterplot_excitation_emission = PowerMeterPlotWidget(self.splitter_excitation_emission_horizontal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_powermeterplot_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_powermeterplot_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_powermeterplot_excitation_emission.setMinimumSize(QtCore.QSize(200, 100))
        self.widget_powermeterplot_excitation_emission.setObjectName("widget_powermeterplot_excitation_emission")
        self.scrollArea_excitation_emission = QtWidgets.QScrollArea(self.splitter_excitation_emission_vertical)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_excitation_emission.sizePolicy().hasHeightForWidth())
        self.scrollArea_excitation_emission.setSizePolicy(sizePolicy)
        self.scrollArea_excitation_emission.setWidgetResizable(True)
        self.scrollArea_excitation_emission.setObjectName("scrollArea_excitation_emission")
        self.scrollAreaWidgetContents_4 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_4.setGeometry(QtCore.QRect(0, 0, 656, 537))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_4.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_4.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents_4.setObjectName("scrollAreaWidgetContents_4")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents_4)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.widget_file_excitation_emission = FileWidget(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_file_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_file_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_file_excitation_emission.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_file_excitation_emission.setObjectName("widget_file_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_file_excitation_emission, 0, 0, 1, 2)
        self.widget_xystage_excitation_emission = XYStageWidget(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_xystage_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_xystage_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_xystage_excitation_emission.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_xystage_excitation_emission.setObjectName("widget_xystage_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_xystage_excitation_emission, 1, 0, 1, 2)
        self.widget_xystageplot_excitation_emission = XYStagePlotWidget(self.scrollAreaWidgetContents_4)
        self.widget_xystageplot_excitation_emission.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_xystageplot_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_xystageplot_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_xystageplot_excitation_emission.setMinimumSize(QtCore.QSize(300, 300))
        self.widget_xystageplot_excitation_emission.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.widget_xystageplot_excitation_emission.setObjectName("widget_xystageplot_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_xystageplot_excitation_emission, 2, 0, 1, 2)
        self.widget_spectrometer_excitation_emission = SpectrometerWidget(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_spectrometer_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_spectrometer_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_spectrometer_excitation_emission.setObjectName("widget_spectrometer_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_spectrometer_excitation_emission, 3, 0, 1, 2)
        self.widget_powermeter_excitation_emission = PowerMeterWidget(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_powermeter_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_powermeter_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_powermeter_excitation_emission.setObjectName("widget_powermeter_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_powermeter_excitation_emission, 4, 0, 1, 2)
        self.widget_laser_excitation_emission = LaserWidget(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_laser_excitation_emission.sizePolicy().hasHeightForWidth())
        self.widget_laser_excitation_emission.setSizePolicy(sizePolicy)
        self.widget_laser_excitation_emission.setObjectName("widget_laser_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_laser_excitation_emission, 5, 0, 1, 2)
        self.groupBox_calibration_beamsplitter = QtWidgets.QGroupBox(self.scrollAreaWidgetContents_4)
        self.groupBox_calibration_beamsplitter.setObjectName("groupBox_calibration_beamsplitter")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_calibration_beamsplitter)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.pushButton_beamsplitter_calibration = QtWidgets.QPushButton(self.groupBox_calibration_beamsplitter)
        self.pushButton_beamsplitter_calibration.setObjectName("pushButton_beamsplitter_calibration")
        self.gridLayout_8.addWidget(self.pushButton_beamsplitter_calibration, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_beamsplitter_calibration = QtWidgets.QLabel(self.groupBox_calibration_beamsplitter)
        self.label_beamsplitter_calibration.setObjectName("label_beamsplitter_calibration")
        self.horizontalLayout_2.addWidget(self.label_beamsplitter_calibration)
        self.lineEdit_beamsplitter_calibration_file = QtWidgets.QLineEdit(self.groupBox_calibration_beamsplitter)
        self.lineEdit_beamsplitter_calibration_file.setObjectName("lineEdit_beamsplitter_calibration_file")
        self.horizontalLayout_2.addWidget(self.lineEdit_beamsplitter_calibration_file)
        self.toolButton_beamsplitter_calibration_file = QtWidgets.QToolButton(self.groupBox_calibration_beamsplitter)
        self.toolButton_beamsplitter_calibration_file.setObjectName("toolButton_beamsplitter_calibration_file")
        self.horizontalLayout_2.addWidget(self.toolButton_beamsplitter_calibration_file)
        self.gridLayout_8.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.gridLayout_9.addWidget(self.groupBox_calibration_beamsplitter, 6, 0, 1, 2)
        self.widget_shuttercontrol_excitation_emission = ShutterControlWidget(self.scrollAreaWidgetContents_4)
        self.widget_shuttercontrol_excitation_emission.setObjectName("widget_shuttercontrol_excitation_emission")
        self.gridLayout_9.addWidget(self.widget_shuttercontrol_excitation_emission, 7, 0, 1, 2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_9.addItem(spacerItem1, 9, 1, 1, 1)
        self.scrollArea_excitation_emission.setWidget(self.scrollAreaWidgetContents_4)
        self.gridLayout_5.addWidget(self.splitter_excitation_emission_vertical, 0, 0, 1, 1)
        self.stackedWidget_experiment.addWidget(self.page_excitation_emission)
        self.page_decay = QtWidgets.QWidget()
        self.page_decay.setObjectName("page_decay")
        self.gridLayout = QtWidgets.QGridLayout(self.page_decay)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter_decay_vertical = QtWidgets.QSplitter(self.page_decay)
        self.splitter_decay_vertical.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_decay_vertical.setObjectName("splitter_decay_vertical")
        self.layoutWidget = QtWidgets.QWidget(self.splitter_decay_vertical)
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout_plot_decay = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout_plot_decay.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_plot_decay.setObjectName("gridLayout_plot_decay")
        self.widget_digitizerplot_decay = DigitizerPlotWidget(self.layoutWidget)
        self.widget_digitizerplot_decay.setMinimumSize(QtCore.QSize(200, 100))
        self.widget_digitizerplot_decay.setObjectName("widget_digitizerplot_decay")
        self.gridLayout_plot_decay.addWidget(self.widget_digitizerplot_decay, 0, 0, 1, 1)
        self.scrollArea_decay = QtWidgets.QScrollArea(self.splitter_decay_vertical)
        self.scrollArea_decay.setWidgetResizable(True)
        self.scrollArea_decay.setObjectName("scrollArea_decay")
        self.scrollAreaWidgetContents_5 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 322, 414))
        self.scrollAreaWidgetContents_5.setObjectName("scrollAreaWidgetContents_5")
        self.gridLayout_10 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents_5)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.widget_shuttercontrol_decay = ShutterControlWidget(self.scrollAreaWidgetContents_5)
        self.widget_shuttercontrol_decay.setObjectName("widget_shuttercontrol_decay")
        self.gridLayout_10.addWidget(self.widget_shuttercontrol_decay, 5, 0, 1, 1)
        self.widget_digitizer_decay = DigitizerWidget(self.scrollAreaWidgetContents_5)
        self.widget_digitizer_decay.setObjectName("widget_digitizer_decay")
        self.gridLayout_10.addWidget(self.widget_digitizer_decay, 4, 0, 1, 1)
        self.widget_file_decay = FileWidget(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_file_decay.sizePolicy().hasHeightForWidth())
        self.widget_file_decay.setSizePolicy(sizePolicy)
        self.widget_file_decay.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_file_decay.setObjectName("widget_file_decay")
        self.gridLayout_10.addWidget(self.widget_file_decay, 0, 0, 1, 1)
        self.widget_laser_decay = LaserWidget(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_laser_decay.sizePolicy().hasHeightForWidth())
        self.widget_laser_decay.setSizePolicy(sizePolicy)
        self.widget_laser_decay.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_laser_decay.setObjectName("widget_laser_decay")
        self.gridLayout_10.addWidget(self.widget_laser_decay, 3, 0, 1, 1)
        self.widget_xystage_decay = XYStageWidget(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_xystage_decay.sizePolicy().hasHeightForWidth())
        self.widget_xystage_decay.setSizePolicy(sizePolicy)
        self.widget_xystage_decay.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_xystage_decay.setObjectName("widget_xystage_decay")
        self.gridLayout_10.addWidget(self.widget_xystage_decay, 1, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_10.addItem(spacerItem2, 6, 0, 1, 1)
        self.widget_xystageplot_decay = XYStagePlotWidget(self.scrollAreaWidgetContents_5)
        self.widget_xystageplot_decay.setMinimumSize(QtCore.QSize(300, 300))
        self.widget_xystageplot_decay.setObjectName("widget_xystageplot_decay")
        self.gridLayout_10.addWidget(self.widget_xystageplot_decay, 2, 0, 1, 1)
        self.scrollArea_decay.setWidget(self.scrollAreaWidgetContents_5)
        self.gridLayout.addWidget(self.splitter_decay_vertical, 0, 0, 1, 1)
        self.stackedWidget_experiment.addWidget(self.page_decay)
        self.gridLayout_2.addWidget(self.stackedWidget_experiment, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_fit_plots_to_screen = QtWidgets.QPushButton(self.page_experiment)
        self.pushButton_fit_plots_to_screen.setObjectName("pushButton_fit_plots_to_screen")
        self.horizontalLayout.addWidget(self.pushButton_fit_plots_to_screen)
        self.label_completion_time = QtWidgets.QLabel(self.page_experiment)
        self.label_completion_time.setMinimumSize(QtCore.QSize(300, 0))
        self.label_completion_time.setObjectName("label_completion_time")
        self.horizontalLayout.addWidget(self.label_completion_time)
        self.progressBar = QtWidgets.QProgressBar(self.page_experiment)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout.addWidget(self.progressBar)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.horizontalLayout_buttons = QtWidgets.QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName("horizontalLayout_buttons")
        self.pushButton_return = QtWidgets.QPushButton(self.page_experiment)
        self.pushButton_return.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.pushButton_return.setFont(font)
        self.pushButton_return.setObjectName("pushButton_return")
        self.horizontalLayout_buttons.addWidget(self.pushButton_return)
        self.pushButton_alignment_experiment = QtWidgets.QPushButton(self.page_experiment)
        self.pushButton_alignment_experiment.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.pushButton_alignment_experiment.setFont(font)
        self.pushButton_alignment_experiment.setObjectName("pushButton_alignment_experiment")
        self.horizontalLayout_buttons.addWidget(self.pushButton_alignment_experiment)
        self.pushButton_start_experiment = QtWidgets.QPushButton(self.page_experiment)
        self.pushButton_start_experiment.setMinimumSize(QtCore.QSize(0, 50))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.pushButton_start_experiment.setFont(font)
        self.pushButton_start_experiment.setObjectName("pushButton_start_experiment")
        self.horizontalLayout_buttons.addWidget(self.pushButton_start_experiment)
        self.gridLayout_2.addLayout(self.horizontalLayout_buttons, 2, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_experiment)
        self.gridLayout_3.addWidget(self.stackedWidget, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 929, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        self.stackedWidget_experiment.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "XY Setup"))
        self.label_intro_text.setText(_translate("MainWindow", "Choose an experiment type:"))
        self.pushButton_transmission.setText(_translate("MainWindow", "Transmission"))
        self.pushButton_excitation_emission.setText(_translate("MainWindow", "Excitation Emission"))
        self.pushButton_decay.setText(_translate("MainWindow", "Decay"))
        self.groupBox_calibration_beamsplitter.setTitle(_translate("MainWindow", "beamsplitter calibration"))
        self.pushButton_beamsplitter_calibration.setText(_translate("MainWindow", "new beamsplitter calibration (go to set experiment) "))
        self.label_beamsplitter_calibration.setText(_translate("MainWindow", "current calibration file"))
        self.toolButton_beamsplitter_calibration_file.setText(_translate("MainWindow", "..."))
        self.pushButton_fit_plots_to_screen.setText(_translate("MainWindow", "Fit Plots to Screen"))
        self.label_completion_time.setText(_translate("MainWindow", "Estimated completion time: 00:00:00"))
        self.pushButton_return.setText(_translate("MainWindow", "Return"))
        self.pushButton_alignment_experiment.setText(_translate("MainWindow", "Set Experiment"))
        self.pushButton_start_experiment.setText(_translate("MainWindow", "Start"))

from gui_action.plot_digitizer import DigitizerPlotWidget
from gui_action.plot_powermeter import PowerMeterPlotWidget
from gui_action.plot_spectrometer import SpectrometerPlotWidget
from gui_action.plot_xystage import XYStagePlotWidget
from gui_action.widget_digitizer  import DigitizerWidget
from gui_action.widget_file import FileWidget
from gui_action.widget_laser import LaserWidget
from gui_action.widget_powermeter import PowerMeterWidget
from gui_action.widget_shuttercontrol import ShutterControlWidget
from gui_action.widget_spectrometer import SpectrometerWidget
from gui_action.widget_xystage import XYStageWidget

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

