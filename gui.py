#!/usr/bin/env python3

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import api


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI()
        self.dialog = LoginForm(self)
        self.setWindowTitle("8tracks")

    def check_login(self):
        self.dialog.show()

    def authenticate(self, login, password):
        self.tracks_api.authenticate(login, password)


class LoginForm(QDialog):
    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        loginlabel = QLabel("Enter login")
        self.loginedit = QLineEdit()
        passwordlabel = QLabel("Enter password")
        self.passwordedit = QLineEdit(echoMode=QLineEdit.Password)
        self.loginbutton = QPushButton('Login')
        layout = QVBoxLayout()
        layout.addWidget(loginlabel)
        layout.addWidget(self.loginedit)
        layout.addWidget(passwordlabel)
        layout.addWidget(self.passwordedit)
        layout.addWidget(self.loginbutton)
        self.setLayout(layout)
        self.loginedit.setFocus()
        self.connect(self.loginedit, SIGNAL("returnPressed()"),
                     self.login)
        self.connect(self.passwordedit, SIGNAL("returnPressed()"),
                     self.login)
        self.loginbutton.clicked.connect(self.login)
        self.setWindowTitle("Login")

    def login(self):
        login = self.loginedit.text()
        password = self.passwordedit.text()
        self.parent().authenticate(login, password)
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.check_login()
    sys.exit(app.exec_())
