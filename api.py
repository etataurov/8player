import requests
import json


class EightTracksAPI:
    def __init__(self):
        self.user_token = None
        with open('config.json') as conf:
            self.config = json.load(conf)

    def authenticate(self, login, password):
        params = {'login': login, 'password': password, 'api_key': self.config.get('api_key')}
        response = requests.post('{}sessions.json'.format(self.config.get('service_url')), params=params)
        response.raise_for_status()
        response_data = json.loads(response.text)
        self.user_token = response_data.get('user_token')
        print(response_data)
