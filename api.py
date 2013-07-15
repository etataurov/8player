import requests
import json


class EightTracksAPI:
    CONFIG_PATH = 'config.json'

    def __init__(self):
        self.play_token = None #maybe also have in config?
        with open(self.CONFIG_PATH) as conf:
            self.config = json.load(conf)

    def authenticate(self, login, password):
        params = {'login': login, 'password': password, 'api_key': self.config.get('api_key')}
        response = requests.post('{}sessions.json'.format(self.config.get('service_url')), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        self.config['user_token'] = response_data.get('user_token')
        with open(self.CONFIG_PATH, 'w') as conf:
            json.dump(self.config, conf, indent=4)
        print(response_data)

    @property
    def authenticated(self):
        # what if we want to logout?
        return 'user_token' in self.config

    def _get_mixes(self):
        params = {'user_token': self.config.get('user_token'), 'api_key': self.config.get('api_key')}
        response = requests.get('{}mixes.json'.format(self.config.get('service_url')), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        return response_data['mixes']

    def _get_play_token(self):
        params = {'user_token': self.config.get('user_token'), 'api_key': self.config.get('api_key')}
        response = requests.get('{}sets/new.json'.format(self.config.get('service_url')), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        self.play_token = response_data.get('play_token')

    def get_mixes(self):
        self._get_play_token()
        return [Mix(x, self) for x in self._get_mixes()]

    def play_mix(self, mix_id):
        params = {'user_token': self.config.get('user_token'), 'api_key': self.config.get('api_key'), 'mix_id': mix_id}
        response = requests.get('{}sets/{}/play.json'.format(self.config.get('service_url'), self.play_token), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        return response_data.get('set').get('track').get('url')


class Mix:
    def __init__(self, params, api):
        self.api = api
        self.id = params.get('id')
        self.name = params.get('name')
        self.description = params.get('description')
        self.tracks_count = params.get('tracks_count')
        self.user = params.get('user').get('login')

    def play(self):
        """
        Should return just url to first track
        + some meta-info
        """
        return self.api.play_mix(self.id)


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
