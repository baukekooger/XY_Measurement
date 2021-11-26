# Import necessary modules
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, \
    QPushButton, QVBoxLayout, QInputDialog, QWidget, QFileDialog


# Define class to to display an informational message
class MessageWindow(QMainWindow):
    def __init__(self):
        # Call the parent constructor
        super().__init__()
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)
        # Create the display and the buttons

        self.btnmessage = QPushButton('open messagebox')
        self.btninput = QPushButton('open inputbox')
        self.btndirec = QPushButton('choose directory')
        self.btnfile = QPushButton('choose file')

        self.generalLayout.addWidget(self.btnmessage)
        self.generalLayout.addWidget(self.btninput)
        self.generalLayout.addWidget(self.btndirec)
        self.generalLayout.addWidget(self.btnfile)

        self.btnmessage.clicked.connect(self._messagebox)
        self.btninput.clicked.connect(self._inputbox)
        self.btndirec.clicked.connect(self._choosedirec)
        self.btnfile.clicked.connect(self._choosefile)

        self.returnvalue = None

    def _messagebox(self):
        msgbox = QMessageBox(self)
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setText(f'are these settings correct?')
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        msgbox.setWindowTitle('check beamsplitter calibration settings')
        answer = msgbox.exec_()
        if answer == QMessageBox.Yes:
            return True
        if answer == QMessageBox.No:
            return False

    # def _inputbox(self):
    #     text, ok = QInputDialog.getText(self, 'filename', 'which beamsplitter?:')
    #     if ok:
    #         print(text)
    #     else:
    #         return

    def _inputbox(self):
        items = ['BS20WA', 'DiCrhoic Boiii', 'Split yo bitch in half']
        item, ok = QInputDialog.getItem(self, 'beamsplitter', 'please choose beamsplitter type '
                                                              'or edit if type not available', items)
        if ok:
            print(item)

    def _choosedirec(self):
        filedir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        print(filedir)
        if not filedir:
            print('no directory chosen')

    def _choosefile(self):
        filename = QFileDialog.getOpenFileName(self, 'Select Directory', '*.csv')[0]
        print(filename)
        print(type(filename))
        if not filename:
            print('no file chosen')


# Create app object and run the app
app = QApplication(sys.argv)
Win = MessageWindow()
Win.show()
app.exec_()
