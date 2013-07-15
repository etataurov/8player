#!/usr/bin/env python3

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import api


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI()
        loginlabel = QLabel("Enter login")
        self.loginedit = QLineEdit()
        passwordlabel = QLabel("Enter password")
        self.passwordedit = QLineEdit(echoMode=QLineEdit.Password)
        self.pushButton = QPushButton('Login')
        layout = QVBoxLayout()
        layout.addWidget(loginlabel)
        layout.addWidget(self.loginedit)
        layout.addWidget(passwordlabel)
        layout.addWidget(self.passwordedit)
        layout.addWidget(self.pushButton)
        self.setLayout(layout)
        self.loginedit.setFocus()
        self.connect(self.loginedit, SIGNAL("returnPressed()"),
                     self.authenticate)
        self.connect(self.passwordedit, SIGNAL("returnPressed()"),
                     self.authenticate)
        self.connect(self.pushButton, SIGNAL("clicked()"),
                     self.authenticate)
        self.setWindowTitle("8tracks")

    def authenticate(self):
        login = self.loginedit.text()
        password = self.passwordedit.text()
        self.tracks_api.authenticate(login, password)



app = QApplication(sys.argv)
form = Form()
form.show()
app.exec_()
