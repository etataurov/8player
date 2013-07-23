#!/usr/bin/env python3

import sys
import argparse
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
from .wrapper import TracksAPIThread


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None, config_filename=None):
        super(MainWindow, self).__init__(parent)
        self.api_thread = TracksAPIThread(config_filename=config_filename)
        self.api_thread.start()
        self.current_track = None
        self.next_track = None
        self.current_mix = None
        self.dialog = LoginForm(self)

        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.mediaObject = Phonon.MediaObject(self)

        # this tick interval somehow dont working
        # it ticks more than once in a second
        self.mediaObject.setTickInterval(1000)
        self.mediaObject.tick.connect(self.tick)
        self.mediaObject.stateChanged.connect(self.stateChanged)
        self.mediaObject.currentSourceChanged.connect(self.sourceChanged)

        Phonon.createPath(self.mediaObject, self.audioOutput)

        self.api_thread.mixes_ready.connect(self.show_mixes)
        self.api_thread.authenticated.connect(self.on_authenticated)
        self.api_thread.authentication_fail.connect(self.dialog.show_error)
        self.api_thread.track_ready.connect(self.play_track)
        self.api_thread.next_track_ready.connect(self.enqueue_track)

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

        elif newState == Phonon.StoppedState:
            self.playAction.setEnabled(True)
            self.pauseAction.setEnabled(False)
            self.timeLcd.display("00:00")

        elif newState == Phonon.PausedState:
            self.pauseAction.setEnabled(False)
            self.playAction.setEnabled(True)

    def sourceChanged(self, source):
        if self.next_track is not None:
            self.current_track = self.next_track
            self.next_track = None
        self.current_track_label.setText(self.current_track.get_title())
        self.timeLcd.display('00:00')
        # we going to preload next track url right here
        self.current_mix.next()

    def sizeHint(self):
        return QtCore.QSize(500, 300)

    def setupUi(self):
        bar = QtGui.QToolBar()

        bar.addAction(self.playAction)
        bar.addAction(self.pauseAction)

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
        # TODO seconds may be 30 more than once!
        # really its done now because we report only once
        # make it more explicit
        if int(seconds) == 30:
            # with phonon-backend-vlc tick is doubling
            # so it maybe called more than once
            self.current_track.report(self.current_mix.id)
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
        self.mediaObject.stop()
        self.mediaObject.clearQueue()
        mix = self.current_mix = self.mixes[row]
        mix.play()

    def play_track(self, track):
        self.current_track = track
        source = Phonon.MediaSource(QtCore.QUrl(track.url))
        self.mediaObject.setCurrentSource(source)
        self.mediaObject.play()

    def enqueue_track(self, track):
        self.next_track = track
        source = Phonon.MediaSource(QtCore.QUrl(track.url))
        self.mediaObject.enqueue(source)

    def check_login(self):
        if not self.api_thread.is_authenticated():
            self.dialog.show()
        else:
            self.api_thread.request_mixes()

    def authenticate(self, login, password):
        #TODO handle auth errors
        self.api_thread.authenticate(login, password)

    def on_authenticated(self):
        self.dialog.hide()
        self.api_thread.request_mixes()

    def show_mixes(self, mixes):
        self.mixes = mixes
        for mix in self.mixes:
            self.addMixToTable(mix)


class LoginForm(QtGui.QDialog):
    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.errorlabel = QtGui.QLabel("ERROR: Wrong credentials")
        self.errorlabel.hide()
        loginlabel = QtGui.QLabel("Enter login")
        self.loginedit = QtGui.QLineEdit()
        passwordlabel = QtGui.QLabel("Enter password")
        self.passwordedit = QtGui.QLineEdit(echoMode=QtGui.QLineEdit.Password)
        self.loginbutton = QtGui.QPushButton('Login')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.errorlabel)
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

    def show_error(self):
        self.errorlabel.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json", help="path to config file")
    args = parser.parse_args()

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("8tracks Music Player")
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow(config_filename=args.config)
    window.show()
    window.check_login()
    sys.exit(app.exec_())
