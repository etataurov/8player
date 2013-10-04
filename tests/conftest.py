from PyQt4 import QtGui


def pytest_configure(config):
    qt_app_instance = QtGui.QApplication([])
    qt_app_instance.setApplicationName("Test 8tracks Music Player")

    def exit_qapp():
        qt_app_instance.exit()

    config._cleanup.append(exit_qapp)
