from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from gui_design.file import Ui_Form
import logging


class FileWidget(QtWidgets.QWidget):
    """
    PyQt Widget for entering file information data. Also selects the file directory.
    Check the corresponding design file in pyqt Designer for detailed information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.file')
        self.logger_widget.info('init filewidget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.filename = None

    def connect_signals_slots(self):
        """ Connect the file widget signals. """
        self.logger_widget.info('Connecting filewidget signal')
        self.ui.toolButton_directory.clicked.connect(self.select_filedir)

    def disconnect_signals_slots(self):
        """ Disconnect the file widget signals. """
        self.logger_widget.info('Disconnecting filewidget signal')
        self.ui.toolButton_directory.clicked.disconnect(self.select_filedir)

    def select_filedir(self):
        """ Select the file directory for storing the output file. """
        self.logger_widget.info('selecting file directory')
        filedir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.ui.lineEdit_directory.setText(filedir)


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # setup pyqt app
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = FileWidget()
    window.show()
    sys.exit(app.exec_())

