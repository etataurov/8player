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
        self.api_thread.next_track(self.id)

    def skip(self):
        """
        also checks that skip is possible
        """
        pass


class Track:
    def __init__(self, params, api_thread):
        self.api_thread = api_thread
        self.id = params.get('id')
        self.url = params.get('url')
        self.performer = params.get('performer')
        self.name = params.get('name')
        self.reported = False

    def get_title(self):
        return "{} - {}".format(self.performer, self.name)

    def report(self, mix_id):
        if not self.reported:
            self.api_thread.report_track(self, mix_id)
            # TODO we should be sure that we are reported
            self.reported = True


class TracksAPIThread(QtCore.QThread):
    mixes_ready = QtCore.pyqtSignal(list)
    track_ready = QtCore.pyqtSignal(Track)
    next_track_ready = QtCore.pyqtSignal(Track)
    authenticated = QtCore.pyqtSignal()

    def __init__(self, parent=None, config_filename=None):
        super(TracksAPIThread, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI(config_filename)
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
            track = Track(params, self)
            self.track_ready.emit(track)

        self.request_queue.put((self.tracks_api.play_mix, [mix_id], callback))

    def next_track(self, mix_id):
        def callback(params):
            track = Track(params, self)
            self.next_track_ready.emit(track)

        self.request_queue.put((self.tracks_api.next_track, [mix_id], callback))

    def report_track(self, track, mix_id):
        self.request_queue.put((self.tracks_api.report_track, [track.id, mix_id], None))

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
                elif action is not None:
                    action(resp)
