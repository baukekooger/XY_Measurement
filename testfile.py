from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread
from gui_design.main import Ui_MainWindow
from yaml import safe_load, dump

import collections
# from experiments.statemachine import StateMachine

import time


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.b = {}

        with open('config_main.yaml') as f:
            self.config = safe_load(f)

    def loopdict(self):
        for key, value in self.config['widgets']['transmission'].items():
            print(key)
            print(value)

    def loopwidget(self):
        with open('settings_ui.yaml') as f:
            settings = safe_load(f)
        experiment = 'excitation_emission'
        settings[experiment] = {}
        for widget_inst in self.config['widgets'][experiment].keys():
            if 'plot' not in widget_inst:
                settings[experiment][widget_inst] = {}
                widget = getattr(self.ui, widget_inst)
                d = widget.ui.__dict__
                for key, widget_value in d.items():
                    if isinstance(widget_value, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                        widgethandle = getattr(widget.ui, key)
                        settings[experiment][widget_inst][key] = widgethandle.value()
                    elif isinstance(widget_value, QtWidgets.QLineEdit):
                        widgethandle = getattr(widget.ui, key)
                        settings[experiment][widget_inst][key] = widgethandle.text()
                    elif isinstance(widget_value, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
                        widgethandle = getattr(widget.ui, key)
                        settings[experiment][widget_inst][key] = widgethandle.toPlainText()
                    elif isinstance(widget_value, QtWidgets.QCheckBox):
                        widgethandle = getattr(widget.ui, key)
                        settings[experiment][widget_inst][key] = widgethandle.isChecked()
        with open('settings_ui.yaml', 'w') as f:
            dump(settings, f)


window = MainWindow()


