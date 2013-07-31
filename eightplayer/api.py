import requests
try:
    import simplejson as json
except ImportError:
    import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_VERSION = 2


class EightTracksAPI:
    def __init__(self, config_filename):
        self.play_token = None #maybe also have in config?
        self.config_filename = config_filename
        self.session = requests.Session()
        with open(self.config_filename) as conf:
            self.config = json.load(conf)

    def _request(self, filename, params=None, method='GET'):
        if params is None:
            params = {}
        url = '{}{}'.format(self.config.get('service_url'), filename)
        request_params = {'api_key': self.config.get('api_key'), 'api_version': API_VERSION}
        if self.authenticated:
            request_params['user_token'] = self.config.get('user_token')
        if method == 'POST':
            request_dict = dict(params=request_params, data=params)
        else:
            request_params.update(params)
            request_dict = dict(params=request_params)
        response = self.session.request(method, url, **request_dict)
        response.raise_for_status()
        response_data = json.loads(response.text)
        log.debug(json.dumps(response_data, indent=2))
        return response_data

    def authenticate(self, login, password):
        data = {'login': login, 'password': password}
        response_data = self._request('sessions.json', data, method='POST')
        self.config['user_token'] = response_data.get('user_token')
        with open(self.config_filename, 'w') as conf:
            json.dump(self.config, conf, indent=4)

    @property
    def authenticated(self):
        # what if we want to logout?
        return 'user_token' in self.config

    def _get_mixes(self):
        response_data = self._request('mixes.json')
        return response_data['mixes']

    def _get_play_token(self):
        response_data = self._request('sets/new.json')
        self.play_token = response_data.get('play_token')

    def get_mixes(self):
        self._get_play_token()
        return self._get_mixes()

    def play_mix(self, mix_id):
        params = {'mix_id': mix_id}
        response_data = self._request('sets/{}/play.json'.format(self.play_token), params)
        return response_data.get('set').get('track')

    def next_track(self, mix_id):
        params = {'mix_id': mix_id}
        response_data = self._request('sets/{}/next.json'.format(self.play_token), params)
        return response_data.get('set').get('track')

    def report_track(self, track_id, mix_id):
        params = {'track_id': track_id, 'mix_id': mix_id}
        self._request('sets/{}/report.json'.format(self.play_token), params)
