import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class EightTracksAPI:
    CONFIG_PATH = 'config.json'

    def __init__(self):
        self.play_token = None #maybe also have in config?
        with open(self.CONFIG_PATH) as conf:
            self.config = json.load(conf)

    def _request(self, filename, params=None, method='GET'):
        if params is None:
            params = {}
        url = '{}{}'.format(self.config.get('service_url'), filename)
        request_params = {'api_key': self.config.get('api_key')}
        if self.authenticated:
            request_params['user_token'] = self.config.get('user_token')
        if method == 'POST':
            request_dict = dict(params=request_params, data=params)
        else:
            request_params.update(params)
            request_dict = dict(params=request_params)
        response = requests.request(method, url, **request_dict)
        response.raise_for_status()
        response_data = json.loads(response.text)
        log.debug(response_data)
        return response_data

    def authenticate(self, login, password):
        data = {'login': login, 'password': password}
        response_data = self._request('sessions.json', data, method='POST')
        self.config['user_token'] = response_data.get('user_token')
        with open(self.CONFIG_PATH, 'w') as conf:
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
        return [Mix(x, self) for x in self._get_mixes()]

    def play_mix(self, mix_id):
        params = {'mix_id': mix_id}
        response_data = self._request('sets/{}/play.json'.format(self.play_token), params)
        return response_data.get('set').get('track')


class Mix:
    def __init__(self, params, api):
        self.api = api
        self.id = params.get('id')
        self.name = params.get('name')
        self.description = params.get('description')
        self.tracks_count = params.get('tracks_count')
        self.user = params.get('user').get('login')

    def play(self):
        track = Track(self.api.play_mix(self.id))
        return track


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