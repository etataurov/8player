import json
from PyQt4.QtTest import QTest
from eightplayer.wrapper import TracksAPIThread, Track, Mix

TEST_CONFIG = {'api_key': '654321', 'service_url': 'http://127.0.0.1:8888/'}
TEST_CONFIG_WITH_TOKEN = dict(TEST_CONFIG, user_token='902671;ca11f318586b05f1fc31b41ed17866e20512ed19')
TEST_CONFIG_PATH = 'tests/test_config.json'


class BasicTestWrapper:
    config = TEST_CONFIG

    def setup_method(self, method):
        with open(TEST_CONFIG_PATH, 'w') as conf:
            json.dump(self.config, conf, indent=4)
        self.api_thread = TracksAPIThread(config_filename=TEST_CONFIG_PATH)
        self.api_thread.start()

    def teardown_method(self, method):
        self.api_thread.quit()


class TestTracWrapperAuth(BasicTestWrapper):
    def setup_method(self, method):
        super().setup_method(method)
        self.auth_success = False
        self.auth_failure = False
        self.api_thread.authenticated.connect(self.authenticated)
        self.api_thread.authentication_fail.connect(self.authenticated_fail)

    def authenticated(self):
        self.auth_success = True

    def authenticated_fail(self):
        self.auth_failure = True

    def test_authenticate_success(self):
        self.api_thread.authenticate('user1', '123')
        QTest.qWait(300)
        assert self.auth_success
        assert not self.auth_failure

    def test_authenticate_failure(self):
        self.api_thread.authenticate('user1', '999999')
        QTest.qWait(300)
        assert self.auth_failure
        assert not self.auth_success


class TestTracWrapperMixes(BasicTestWrapper):
    config = TEST_CONFIG_WITH_TOKEN

    def setup_method(self, method):
        super().setup_method(method)
        self.mixes = None
        self.track = None
        self.next_track = None
        self.api_thread.mixes_ready.connect(self.mixes_ready)
        self.api_thread.track_ready.connect(self.track_ready)
        self.api_thread.next_track_ready.connect(self.next_track_ready)
        self.api_thread.next_track_after_skip_ready.connect(self.next_track_after_skip_ready)

    def mixes_ready(self, mixes):
        self.mixes = mixes

    def track_ready(self, track):
        self.track = track

    def next_track_ready(self, track):
        self.next_track = track

    def next_track_after_skip_ready(self, track):
        self.next_track_after_skip = track

    def test_request_mixes(self):
        self.api_thread.request_mixes()
        QTest.qWait(500)
        assert self.mixes
        assert len(self.mixes) == 12
        assert isinstance(self.mixes[0], Mix)

    def test_play_mix(self):
        self.api_thread.tracks_api._get_play_token()
        self.api_thread.play_mix(12345)
        QTest.qWait(500)
        assert self.track
        assert isinstance(self.track, Track)

    def test_next_track(self):
        self.api_thread.tracks_api._get_play_token()
        self.api_thread.next_track(12345)
        QTest.qWait(500)
        assert self.next_track
        assert isinstance(self.next_track, Track)

    def test_skip_track(self):
        self.api_thread.tracks_api._get_play_token()
        self.api_thread.skip_track(12345)
        QTest.qWait(500)
        assert self.next_track_after_skip
        assert isinstance(self.next_track_after_skip, Track)
