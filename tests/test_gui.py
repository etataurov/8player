import sys
import json
from PyQt4 import QtGui, QtCore
from PyQt4.QtTest import QTest
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
        #TODO icon

    def test_tray_icon_menu(self):
        assert isinstance(self.form.tray_icon.contextMenu(), QtGui.QMenu)
        assert len(self.form.tray_icon.contextMenu().actions()) == 1  # will be more soon

    def test_tray_icon_menu_exit(self):
        exit_action = self.form.tray_icon.contextMenu().actions()[0]
        assert exit_action.isVisible()
        assert exit_action.text() == 'Exit'  # TODO i18n
        self.form.show()
        exit_action.trigger()
        assert not self.form.isVisible()