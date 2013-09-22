from queue import Queue
from PyQt4 import QtCore
import logging
try:
    import simplejson as json
except ImportError:
    import json
from . import api

STOP = object()

log = logging.getLogger(__name__)


class Mix:
    def __init__(self, params, api_thread):
        self.api_thread = api_thread
        self.params = params
        self.id = params.get('id')
        self.name = params.get('name')
        self.description = params.get('description')
        self.params.pop('description')  # hacky way to fix showing mixes TODO handle json
        self.tracks_count = params.get('tracks_count')
        self.user = params.get('user').get('login')

    def __str__(self):
        return "Mix({}): {}".format(self.id, self.name)

    def play(self):
        self.api_thread.play_mix(self.id)

    def next(self):
        self.api_thread.next_track(self.id)

    def skip(self):
        """
        also checks that skip is possible
        """
        pass

    def as_json(self):
        return json.dumps(self.params).replace("'", "\\'")


class Track:
    def __init__(self, params, api_thread):
        self.api_thread = api_thread
        self.id = params.get('id')
        self.url = params.get('url')
        self.performer = params.get('performer')
        self.name = params.get('name')
        self.reported = False

    def __str__(self):
        return self.get_title()

    def get_title(self):
        return "{} - {}".format(self.performer, self.name)

    def report(self, mix_id):
        if not self.reported:
            log.info("30 sec reporting")
            self.api_thread.report_track(self, mix_id)
            # TODO we should be sure that we are reported
            self.reported = True


class Tag:
    def __init__(self, params):
        self.name = params['name']
        cool_taggings_count = params['cool_taggings_count'].replace(',', '')
        self.count = int(cool_taggings_count[:-1]) if cool_taggings_count.endswith('+') else int(cool_taggings_count)


class TracksAPIThread(QtCore.QThread):
    mixes_ready = QtCore.pyqtSignal(list)
    tags_ready = QtCore.pyqtSignal(list)
    track_ready = QtCore.pyqtSignal(Track)
    next_track_ready = QtCore.pyqtSignal(Track)
    authenticated = QtCore.pyqtSignal()
    authentication_fail = QtCore.pyqtSignal()

    def __init__(self, parent=None, config_filename=None):
        super(TracksAPIThread, self).__init__(parent)
        self.tracks_api = api.EightTracksAPI(config_filename)
        self.request_queue = Queue()

    def __del__(self):
        self.request_queue.put(STOP)
        self.wait()

    def request_mixes(self, **kwargs):
        def callback(params):
            mixes = [Mix(x, self) for x in params]
            self.mixes_ready.emit(mixes)

        self.request_queue.put((self.tracks_api.get_mixes, [kwargs], callback))

    def request_tags(self):
        def callback(params):
            tags = [Tag(x) for x in params]
            self.tags_ready.emit(tags)

        self.request_queue.put((self.tracks_api.get_tags, [], callback))

    def authenticate(self, login, password):
        self.request_queue.put(
            (
                self.tracks_api.authenticate,
                [login, password],
                (self.authenticated, self.authentication_fail)
            )
        )

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
                errback = None
                func, args, action = data
                if isinstance(action, tuple):
                    action, errback = action
                try:
                    resp = func(*args)
                except Exception:
                    if errback is not None:
                        errback.emit()
                        continue
                    # TODO handle any exception
                    raise
                if isinstance(action, QtCore.pyqtBoundSignal):
                    if resp is None:
                        action.emit()
                    else:
                        action.emit(resp)
                elif action is not None:
                    action(resp)
