import sys
import json
from PyQt4 import QtGui, QtCore
from PyQt4.QtTest import QTest
from PyQt4.phonon import Phonon
from eightplayer.gui import MainWindow

TEST_CONFIG = {'api_key': '654321', 'service_url': 'http://127.0.0.1:8888/'}
TEST_CONFIG_PATH = 'tests/test_config.json'


class TestTrackGUI:
    def setup_method(self, method):
        self.app = QtGui.QApplication(sys.argv)
        self.app.setApplicationName("Test 8tracks Music Player")
        with open(TEST_CONFIG_PATH, 'w') as conf:
            json.dump(TEST_CONFIG, conf, indent=4)
        self.form = MainWindow(config_filename=TEST_CONFIG_PATH)
        # TODO call check_login automatically
        self.form.check_login()

    def teardown_method(self, method):
        self.form.dialog.close()
        self.form.tray_icon.hide()
        self.form.close()

    def test_login_dialog(self):
        assert self.form.dialog.isVisible()
        assert self.form.dialog.loginedit.text() == ''
        assert self.form.dialog.passwordedit.text() == ''

    def test_login_success(self):
        self.form.dialog.loginedit.setText('user1')
        self.form.dialog.passwordedit.setText('123')
        QTest.mouseClick(self.form.dialog.loginbutton, QtCore.Qt.LeftButton)
        QTest.qWait(1000)
        assert not self.form.dialog.isVisible()
        assert self.form.api_thread.is_authenticated()

    def test_login_fail(self):
        self.form.dialog.loginedit.setText('user1')
        self.form.dialog.passwordedit.setText('999999')
        QTest.mouseClick(self.form.dialog.loginbutton, QtCore.Qt.LeftButton)
        QTest.qWait(1000)
        assert self.form.dialog.isVisible()
        assert self.form.dialog.errorlabel.isVisible()

    def test_login_window_closes_main(self):
        self.form.show()
        self.form.dialog.close()
        assert not self.form.isVisible()

    def test_tray_icon(self):
        assert isinstance(self.form.tray_icon, QtGui.QSystemTrayIcon)
        assert self.form.tray_icon.isVisible()

    def test_tray_icon_menu(self):
        assert isinstance(self.form.tray_icon.contextMenu(), QtGui.QMenu)
        assert len(self.form.tray_icon.contextMenu().actions()) == 3

    def test_tray_icon_menu_exit(self):
        exit_action = self.form.tray_icon.contextMenu().actions()[2]
        assert exit_action.isVisible()
        assert exit_action.text() == 'Exit'  # TODO i18n
        self.form.show()
        exit_action.trigger()
        assert not self.form.isVisible()

    def test_tray_icon_menu_play(self):
        play_action = self.form.tray_icon.contextMenu().actions()[0]
        assert play_action.isVisible()
        assert play_action.text() == 'Play'  # TODO i18n
        assert not play_action.isEnabled()

    # TODO test actions should not working without authentication, do some separation

    def test_tray_icon_menu_play_action(self):
        play_action = self.form.tray_icon.contextMenu().actions()[0]
        self.play_mix()
        assert not play_action.isEnabled()
        self.form.mediaObject.pause()
        assert play_action.isEnabled()
        play_action.trigger()
        assert self.form.mediaObject.state() == Phonon.PlayingState

    def test_tray_icon_menu_pause(self):
        pause_action = self.form.tray_icon.contextMenu().actions()[1]
        assert pause_action.isVisible()
        assert pause_action.text() == 'Pause'  # TODO i18n
        assert not pause_action.isEnabled()

    def test_tray_icon_menu_pause_action(self):
        pause_action = self.form.tray_icon.contextMenu().actions()[1]
        self.play_mix()
        assert pause_action.isEnabled()
        pause_action.trigger()
        assert not pause_action.isEnabled()
        assert self.form.mediaObject.state() == Phonon.PausedState

    def test_tags_list(self):
        assert self.form.modeCombobox.itemText(0) == 'Hot'
        QTest.qWait(2000)
        assert self.form.modeCombobox.count() == 28  # Hot, separator and 26 tags

    def test_tags_change(self):
        self.form.api_thread.request_mixes()
        QTest.qWait(100)  # wait for mixes
        assert 'Hot' in self.form.browserWidget.mixes
        self.form.browserWidget.update_mixes('sex')
        QTest.qWait(2000)
        assert self.form.browserWidget.current_tag == 'sex'
        assert 'sex' in self.form.browserWidget.mixes
        self.form.browserWidget.update_mixes('Hot')

    def test_mixes_count(self):
        self.form.api_thread.request_mixes()
        QTest.qWait(2000)  # wait for mixes
        mainFrame = self.form.browserWidget.webView.page().mainFrame()
        assert mainFrame.evaluateJavaScript("""$('div.mix').size()""") == 12

    def test_skip_track(self):
        assert isinstance(self.form.skipAction, QtGui.QAction)
        assert not self.form.skipAction.isEnabled()
        self.play_mix()
        assert self.form.skipAction.isEnabled()
        track = self.form.current_track
        self.form.skipAction.trigger()
        QTest.qWait(2000)
        assert track != self.form.current_track
        assert self.form.mediaObject.state() == Phonon.PlayingState

    # helpers

    def play_mix(self):
        self.form.api_thread.request_mixes()
        QTest.qWait(2000)
        self.form.browserWidget.click(2025587)  # mix_id from mixes.json
        QTest.qWait(2000)
