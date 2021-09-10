# Import necessary modules
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton, QVBoxLayout


# Define class to to display an informational message
class MessageWindow(QMainWindow):
    def __init__(self):
        # Call the parent constructor
        super().__init__()
        self.btn = QPushButton('open msbox')
        self.setCentralWidget(self.btn)
        self.btn.clicked.connect(self.box)
        self.returnvalue = None

    def box(self):
        # Create the messagebox object
        msgQuestion = QMessageBox(self)
        # Set the Warning icon
        msgQuestion.setIcon(QMessageBox.Question)
        # Set the main message
        msgQuestion.setText("Do you want to continue?")
        # Set two buttons for the message box
        msgQuestion.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msgQuestion.setEscapeButton(QMessageBox.Close)

        msgQuestion.setDefaultButton(QMessageBox.No)
        # Call the custom method on button clicked
        # msgQuestion.buttonClicked.connect(self.msgButton)
        # Set the title of the window
        msgQuestion.setWindowTitle("Asking Question to user")
        # Display the message box
        # msgQuestion.show()
        result = msgQuestion.exec_()
        if result == QMessageBox.Yes:
            print('yes pressed')
        elif result == QMessageBox.Cancel:
            print('cancel pressed')
        else:
            print(result)



# Create app object and run the app
app = QApplication(sys.argv)
Win = MessageWindow()
Win.show()
app.exec_()
