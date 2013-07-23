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
        self.form.show()
        # TODO call check_login automatically
        self.form.check_login()

    def teardown_method(self, method):
        # if we set self.app = None, py.test aborts
        self.form = None

    def test_login_dialog(self):
        assert self.form.isVisible()
        assert self.form.dialog.isVisible()
        assert self.form.dialog.loginedit.text() == ''
        assert self.form.dialog.passwordedit.text() == ''

    def test_success_login(self):
        self.form.dialog.loginedit.setText('user1')
        self.form.dialog.passwordedit.setText('123')
        QTest.mouseClick(self.form.dialog.loginbutton, QtCore.Qt.LeftButton)
        # hack to wait for authentication
        # TODO find more suitable waiter
        QTest.mouseRelease(self.form, QtCore.Qt.LeftButton, delay=1000)
        assert not self.form.dialog.isVisible()

