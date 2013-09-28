#!/usr/bin/env python3

import sys
import logging
from PyQt4 import QtCore, QtGui, QtWebKit
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
from . import eightplayer_rc

log = logging.getLogger(__name__)


class BrowserWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(BrowserWidget, self).__init__(parent=parent)
        self.mainWindow = parent  # do it because in click, parent() returns some QStackedWidget object
        self.web_load_finished = False
        self.mixes = {}  # tag -> mixes
        self.mixes_dict = {}  # mix_id -> mix
        self.current_tag = 'Hot'  # TODO do it another way
        self.webView = QtWebKit.QWebView()
        self.webView.setUrl(QtCore.QUrl('qrc:/resources/mixes.html'))
        self.webView.loadFinished.connect(self.finishLoading)
        self.webView.page().mainFrame().javaScriptWindowObjectCleared.connect(
                self.populateJavaScriptWindowObject)
        self.webView.setMinimumSize(QtCore.QSize(500, 270))
        self.mainWindow.api_thread.mixes_ready.connect(self.mixes_loaded)

        if self.mainWindow.show_inspector:
            self.webView.page().settings().setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
            self.inspector = QtWebKit.QWebInspector()
            self.inspector.setPage(self.webView.page())
            self.inspector.setVisible(True)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.webView)
        self.setLayout(mainLayout)

    def populateJavaScriptWindowObject(self):
        self.webView.page().mainFrame().addToJavaScriptWindowObject(
                'GUIPlayer', self)

    def finishLoading(self):
        self.web_load_finished = True
        if self.mixes:
            self.show_mixes()

    def mixes_loaded(self, mixes):
        # TODO scroll to beginning
        self.mixes[self.current_tag] = mixes  # attention: race possibility
        self.mixes_dict.update({mix.id: mix for mix in mixes})
        if self.web_load_finished:
            self.show_mixes()

    def show_mixes(self):
        self.clear_mixes()
        mainFrame = self.webView.page().mainFrame()
        for i, mix in enumerate(self.mixes[self.current_tag]):  # attention: race possibility
            mainFrame.evaluateJavaScript("""this.addMixToList('%s', %d)""" % (mix.as_json(), i))

    def clear_mixes(self):
        mainFrame = self.webView.page().mainFrame()
        mainFrame.evaluateJavaScript("""this.clearMixes()""")

    def update_mixes(self, tag):
        if tag == self.current_tag:
            return
        if tag in self.mixes:
            self.current_tag = tag
            self.show_mixes()
            return
        self.mainWindow.api_thread.request_mixes(tag=tag)
        self.current_tag = tag

    @QtCore.pyqtSlot(int)
    def click(self, mix_id):
        self.mainWindow.mediaObject.stop()
        self.mainWindow.mediaObject.clearQueue()
        mix = self.mainWindow.current_mix = self.mixes_dict.get(mix_id)
        self.mainWindow.next_track = None
        log.info("Selected: {}".format(mix))
        mix.play()


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None, config_filename=None, inspector=False):
        super(MainWindow, self).__init__(parent)
        self.api_thread = TracksAPIThread(config_filename=config_filename)
        self.show_inspector = inspector
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

        self.api_thread.authenticated.connect(self.on_authenticated)
        self.api_thread.authentication_fail.connect(self.dialog.show_error)
        self.api_thread.track_ready.connect(self.play_track)
        self.api_thread.next_track_ready.connect(self.enqueue_track)
        self.api_thread.next_track_after_skip_ready.connect(self.play_next_track)
        self.api_thread.tags_ready.connect(self.update_combobox)

        # TODO change icon
        self.tray_icon = QtGui.QSystemTrayIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaVolume), self)
        self.setupSysTrayMenu()
        self.tray_icon.show()

        self.setupActions()
        self.setupUi()
        self.api_thread.request_tags()

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
            self.trayPlayAction.setEnabled(False)
            self.pauseAction.setEnabled(True)
            self.trayPauseAction.setEnabled(True)
            self.skipAction.setEnabled(True)

        elif newState == Phonon.StoppedState:
            self.playAction.setEnabled(True)
            self.pauseAction.setEnabled(False)

        elif newState == Phonon.PausedState:
            self.pauseAction.setEnabled(False)
            self.trayPauseAction.setEnabled(False)
            self.playAction.setEnabled(True)
            self.trayPlayAction.setEnabled(True)

    def sourceChanged(self, source):
        if self.next_track is not None:
            self.current_track = self.next_track
            self.next_track = None
        self.current_track_label.setText(self.current_track.get_title())
        # we going to preload next track url right here
        self.current_mix.next()

    def sizeHint(self):
        return QtCore.QSize(600, 300)

    def setupSysTrayMenu(self):
        menu = QtGui.QMenu(self)
        trayExitAction = QtGui.QAction("Exit",
            self, triggered=self.close
        )
        self.trayPlayAction = QtGui.QAction("Play",
            self, enabled=False, triggered=self.mediaObject.play
        )
        self.trayPauseAction = QtGui.QAction("Pause",
            self, enabled=False, triggered=self.mediaObject.pause
        )
        menu.addAction(self.trayPlayAction)
        menu.addAction(self.trayPauseAction)
        menu.addAction(trayExitAction)
        self.tray_icon.setContextMenu(menu)

    def setupUi(self):
        bar = QtGui.QToolBar()

        bar.addAction(self.playAction)
        bar.addAction(self.pauseAction)
        bar.addAction(self.skipAction)

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

        seekerLayout = QtGui.QHBoxLayout()
        seekerLayout.addWidget(self.seekSlider)

        playbackLayout = QtGui.QHBoxLayout()
        playbackLayout.addWidget(bar)
        playbackLayout.addStretch()
        playbackLayout.addWidget(volumeLabel)
        playbackLayout.addWidget(self.volumeSlider)

        self.current_track_label = QtGui.QLabel("Nothing")

        self.browserWidget = BrowserWidget(self)

        self.modeCombobox = QtGui.QComboBox()
        self.modeCombobox.addItem('Hot')
        self.modeCombobox.insertSeparator(1)
        self.modeCombobox.activated[str].connect(self.browserWidget.update_mixes)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.modeCombobox)
        mainLayout.addWidget(self.browserWidget)
        mainLayout.addWidget(self.current_track_label)
        mainLayout.addLayout(seekerLayout)
        mainLayout.addLayout(playbackLayout)

        widget = QtGui.QWidget()
        widget.setLayout(mainLayout)

        self.setCentralWidget(widget)

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

        self.skipAction = QtGui.QAction(
            self.style().standardIcon(QtGui.QStyle.SP_MediaSkipForward),
            "Skip", self, shortcut="Ctrl+N", enabled=False,
            triggered=self.skip_track
        )

    def skip_track(self):
        self.current_mix.skip()

    def update_combobox(self, tags):
        sorted_tags = [tag.name for tag in sorted(tags, key=lambda x: x.count, reverse=True)]
        self.modeCombobox.addItems(sorted_tags)

    def play_track(self, track):
        log.info("Start playing track: {}".format(track))
        self.current_track = track
        source = Phonon.MediaSource(QtCore.QUrl(track.url))
        self.mediaObject.setCurrentSource(source)
        self.mediaObject.play()

    def enqueue_track(self, track):
        log.info("Enqueue next track: {}".format(track))
        self.next_track = track
        source = Phonon.MediaSource(QtCore.QUrl(track.url))
        self.mediaObject.enqueue(source)

    def play_next_track(self, track):
        self.mediaObject.stop()
        self.mediaObject.clearQueue()
        self.next_track = None
        self.play_track(track)

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

    def closeEvent(self, event):
        self.parent().close()
        event.accept()

    def login(self):
        login = self.loginedit.text()
        password = self.passwordedit.text()
        self.parent().authenticate(login, password)

    def show_error(self):
        log.info("Wrong username/password")
        self.errorlabel.show()


def main(config_filename="config.json", inspector=False):
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("8tracks Music Player")
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow(config_filename=config_filename, inspector=inspector)
    window.show()
    window.check_login()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
