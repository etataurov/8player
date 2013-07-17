#!/usr/bin/env python3

import sys
from PyQt4 import QtCore, QtGui
try:
    from PyQt4.phonon import Phonon
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "Music Player",
            "Your Qt installation does not have Phonon support.",
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
            QtGui.QMessageBox.NoButton)
    sys.exit(1)
import api


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI()
        self.current_track = None
        self.current_mix = None
        self.dialog = LoginForm(self)
        #TODO music buttons
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.mediaObject = Phonon.MediaObject(self)

        self.mediaObject.setTickInterval(1000)

        self.mediaObject.tick.connect(self.tick)
        self.mediaObject.stateChanged.connect(self.stateChanged)

        Phonon.createPath(self.mediaObject, self.audioOutput)

        self.setupActions()
        self.setupUi()

    def stateChanged(self, newState, oldState):
        if newState == Phonon.ErrorState:
            if self.mediaObject.errorType() == Phonon.FatalError:
                QtGui.QMessageBox.warning(self, "Fatal Error",
                        self.mediaObject.errorString())
            else:
                QtGui.QMessageBox.warning(self, "Error",
                        self.mediaObject.errorString())

        elif newState == Phonon.PlayingState:
            self.playAction.setEnabled(False)
            self.pauseAction.setEnabled(True)
            self.stopAction.setEnabled(True)

        elif newState == Phonon.StoppedState:
            self.stopAction.setEnabled(False)
            self.playAction.setEnabled(True)
            self.pauseAction.setEnabled(False)
            self.timeLcd.display("00:00")

        elif newState == Phonon.PausedState:
            self.pauseAction.setEnabled(False)
            self.stopAction.setEnabled(True)
            self.playAction.setEnabled(True)

    def sizeHint(self):
        return QtCore.QSize(500, 300)

    def setupUi(self):
        bar = QtGui.QToolBar()

        bar.addAction(self.playAction)
        bar.addAction(self.pauseAction)
        bar.addAction(self.stopAction)

        self.seekSlider = Phonon.SeekSlider(self)
        self.seekSlider.setMediaObject(self.mediaObject)

        self.volumeSlider = Phonon.VolumeSlider(self)
        self.volumeSlider.setAudioOutput(self.audioOutput)
        self.volumeSlider.setSizePolicy(QtGui.QSizePolicy.Maximum,
                                        QtGui.QSizePolicy.Maximum)

        volumeLabel = QtGui.QLabel()
        volumeLabel.setPixmap(QtGui.QPixmap('images/volume.png'))

        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Light, QtCore.Qt.darkGray)

        self.timeLcd = QtGui.QLCDNumber()
        self.timeLcd.setPalette(palette)

        headers = ("Title", "Description", "Tracks count", "User")

        self.musicTable = QtGui.QTableWidget(0, 4)
        self.musicTable.setHorizontalHeaderLabels(headers)
        self.musicTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.musicTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.musicTable.cellPressed.connect(self.tableClicked)

        seekerLayout = QtGui.QHBoxLayout()
        seekerLayout.addWidget(self.seekSlider)
        seekerLayout.addWidget(self.timeLcd)

        playbackLayout = QtGui.QHBoxLayout()
        playbackLayout.addWidget(bar)
        playbackLayout.addStretch()
        playbackLayout.addWidget(volumeLabel)
        playbackLayout.addWidget(self.volumeSlider)

        self.current_track_label = QtGui.QLabel("Nothing")

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.musicTable)
        mainLayout.addWidget(self.current_track_label)
        mainLayout.addLayout(seekerLayout)
        mainLayout.addLayout(playbackLayout)

        widget = QtGui.QWidget()
        widget.setLayout(mainLayout)

        self.setCentralWidget(widget)

        self.timeLcd.display("00:00")
        self.setWindowTitle("8tracks music player")

    def tick(self, time):
        seconds = (time / 1000) % 60
        # TODO why tick is doubling?
        # TODO report
        displayTime = QtCore.QTime(0, (time / 60000) % 60, seconds)
        self.timeLcd.display(displayTime.toString('mm:ss'))

    def setupActions(self):
        self.playAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaPlay), "Play",
            self, shortcut="Ctrl+P", enabled=False,
            triggered=self.mediaObject.play
        )

        self.pauseAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaPause),
            "Pause", self, shortcut="Ctrl+A", enabled=False,
            triggered=self.mediaObject.pause
        )

        self.stopAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaStop), "Stop",
            self, shortcut="Ctrl+S", enabled=False,
            triggered=self.mediaObject.stop
        )

        self.nextAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaSkipForward),
            "Next", self, shortcut="Ctrl+N"
        )

        self.previousAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaSkipBackward),
            "Previous", self, shortcut="Ctrl+R"
        )

    def addMixToTable(self, mix):
        titleItem = QtGui.QTableWidgetItem(mix.name)
        titleItem.setFlags(titleItem.flags() ^ QtCore.Qt.ItemIsEditable)

        descrItem = QtGui.QTableWidgetItem(mix.description)
        descrItem.setFlags(descrItem.flags() ^ QtCore.Qt.ItemIsEditable)

        countItem = QtGui.QTableWidgetItem(str(mix.tracks_count))
        countItem.setFlags(countItem.flags() ^ QtCore.Qt.ItemIsEditable)

        userItem = QtGui.QTableWidgetItem(mix.user)
        userItem.setFlags(userItem.flags() ^ QtCore.Qt.ItemIsEditable)

        currentRow = self.musicTable.rowCount()
        self.musicTable.insertRow(currentRow)
        self.musicTable.setItem(currentRow, 0, titleItem)
        self.musicTable.setItem(currentRow, 1, descrItem)
        self.musicTable.setItem(currentRow, 2, countItem)
        self.musicTable.setItem(currentRow, 3, userItem)

    def tableClicked(self, row, column):
        mix = self.current_mix = self.mixes[row]
        track = self.current_track = mix.play()
        self.current_track_label.setText(track.get_title())
        source = Phonon.MediaSource(QtCore.QUrl(track.url))
        self.mediaObject.setCurrentSource(source)
        self.mediaObject.play()


    def check_login(self):
        if not self.tracks_api.authenticated:
            self.dialog.show()
        else:
            self.show_mixes()

    def authenticate(self, login, password):
        try:
            self.tracks_api.authenticate(login, password)
        except Exception:
            # TODO handle
            raise
        else:
            self.show_mixes()

    def show_mixes(self):
        self.mixes = self.tracks_api.get_mixes()
        for mix in self.mixes:
            self.addMixToTable(mix)


class LoginForm(QtGui.QDialog):
    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        loginlabel = QtGui.QLabel("Enter login")
        self.loginedit = QtGui.QLineEdit()
        passwordlabel = QtGui.QLabel("Enter password")
        self.passwordedit = QtGui.QLineEdit(echoMode=QtGui.QLineEdit.Password)
        self.loginbutton = QtGui.QPushButton('Login')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(loginlabel)
        layout.addWidget(self.loginedit)
        layout.addWidget(passwordlabel)
        layout.addWidget(self.passwordedit)
        layout.addWidget(self.loginbutton)
        self.setLayout(layout)
        self.loginedit.setFocus()
        self.connect(self.loginedit, QtCore.SIGNAL("returnPressed()"),
                     self.login)
        self.connect(self.passwordedit, QtCore.SIGNAL("returnPressed()"),
                     self.login)
        self.loginbutton.clicked.connect(self.login)
        self.setWindowTitle("Login")

    def login(self):
        login = self.loginedit.text()
        password = self.passwordedit.text()
        self.parent().authenticate(login, password)
        self.hide()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    app.setApplicationName("8tracks Music Player")
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow()
    window.show()
    window.check_login()
    sys.exit(app.exec_())
