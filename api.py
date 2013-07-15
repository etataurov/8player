import requests
import json


class EightTracksAPI:
    CONFIG_PATH = 'config.json'
    def __init__(self):
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
        return 'user_token' in self.config

    def _get_mixes(self):
        params = {'user_token': self.config.get('user_token'), 'api_key': self.config.get('api_key')}
        response = requests.get('{}mixes.json'.format(self.config.get('service_url')), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        return response_data['mixes']

    def get_mixes(self):
        return [Mix(x) for x in self._get_mixes()]


class Mix:
    def __init__(self, params):
        self.name = params.get('name')
        self.description = params.get('description')
        self.id = params.get('id')
