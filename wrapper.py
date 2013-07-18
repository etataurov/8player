from queue import Queue
from PyQt4 import QtCore
import api

STOP = object()


class Mix:
    def __init__(self, params, api_thread):
        self.api_thread = api_thread
        self.id = params.get('id')
        self.name = params.get('name')
        self.description = params.get('description')
        self.tracks_count = params.get('tracks_count')
        self.user = params.get('user').get('login')

    def play(self):
        self.api_thread.play_mix(self.id)

    def next(self):
        """
        same as play
        maybe dont separate them
        """
        pass

    def skip(self):
        """
        also checks that skip is possible
        """
        pass

    def send_30_sec(self):
        pass


class Track:
    def __init__(self, params):
        self.id = params.get('id')
        self.url = params.get('url')
        self.performer = params.get('performer')
        self.name = params.get('name')

    def get_title(self):
        return "{} - {}".format(self.performer, self.name)


class TracksAPIThread(QtCore.QThread):
    mixes_ready = QtCore.pyqtSignal(list)
    track_ready = QtCore.pyqtSignal(Track)
    authenticated = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TracksAPIThread, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI()
        self.request_queue = Queue()

    def __del__(self):
        self.request_queue.put(STOP)
        self.wait()

    def request_mixes(self):
        def callback(params):
            mixes = [Mix(x, self) for x in params]
            self.mixes_ready.emit(mixes)

        self.request_queue.put((self.tracks_api.get_mixes, [], callback))

    def authenticate(self, login, password):
        self.request_queue.put((self.tracks_api.authenticate, [login, password], self.authenticated))

    def play_mix(self, mix_id):
        def callback(params):
            track = Track(params)
            self.track_ready.emit(track)

        self.request_queue.put((self.tracks_api.play_mix, [mix_id], callback))

    def is_authenticated(self):
        return self.tracks_api.authenticated

    def run(self):
        while True:
            data = self.request_queue.get()
            if data is STOP:
                return
            else:
                func, args, action = data
                resp = func(*args)
                if isinstance(action, QtCore.pyqtBoundSignal):
                    if resp is None:
                        action.emit()
                    else:
                        action.emit(resp)
                else:
                    action(resp)