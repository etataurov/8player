import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtTest import QTest
from eightplayer.gui import MainWindow

class TestTrackGUI:
    def setup_method(self, method):
        self.app = QtGui.QApplication(sys.argv)
        self.app.setApplicationName("Test 8tracks Music Player")
        # TODO test config
        self.form = MainWindow(config_filename='config.json')
        self.form.show()
        # TODO call check_login automatically
        self.form.check_login()

    def test_login(self):
        assert self.form.isVisible()
        assert self.form.dialog.isVisible()
        assert self.form.dialog.loginedit.text() == ''
        assert self.form.dialog.passwordedit.text() == ''
        self.form.dialog.loginedit.setText('user1')
        self.form.dialog.passwordedit.setText('123')
        QTest.mouseClick(self.form.dialog.loginbutton, QtCore.Qt.LeftButton)
        assert not self.form.dialog.isVisible()

