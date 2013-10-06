import tornado.ioloop
import tornado.web
import os
import datetime
import stagger

MUSIC_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'test_music')
PLAY_TOKEN = '12345'

# TODO check api_key and user token in every request


def tracks_iterator():
    while True:
        for filename in os.listdir(MUSIC_DIR):
            if os.path.isfile(os.path.join(MUSIC_DIR, filename)):
                yield filename

TRACKS = tracks_iterator()


def real_file_path(filename):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), filename)


class MainHandler(tornado.web.RequestHandler):
    def get(self, filename):
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        if filename in ('next.json', 'skip.json'):
            filename = 'play.json'
        with open(real_file_path(filename)) as json_file:
            data = json_file.read()
            if filename == 'play.json':
                data = data % self.next_track()
            self.finish(data)

    def post(self, filename):
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        login = self.get_argument('login')
        password = self.get_argument('password')
        if login != 'user1' or password != '123':
            self.set_status(403)
        with open(real_file_path('sessions.json')) as sessions:
            self.finish(sessions.read())

    def next_track(self):
        filename = next(TRACKS)
        track = stagger.read_tag(os.path.join(MUSIC_DIR, filename))
        return {'filename': filename, 'title': track.title, 'artist': track.artist}


class SetsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""{"status": "200 OK", "errors": null, "api_version": 2, "api_warning": ["You didn't pass an API version, defaulting to api_version=2."], "notices": null, "play_token": "%s"}""" % PLAY_TOKEN)
        self.finish()


class ReportHandler(tornado.web.RequestHandler):
    def get(self):
        mix_id = self.get_argument('mix_id')
        self.finish({'status': "200 OK"})


class FileHandler(tornado.web.RequestHandler):
    def get(self, object_name):
        path = os.path.join(MUSIC_DIR, object_name)
        if not os.path.isfile(path):
            raise tornado.web.HTTPError(404)
        info = os.stat(path)
        self.set_header("Content-Type", "application/unknown")
        self.set_header("Last-Modified", datetime.datetime.utcfromtimestamp(
            info.st_mtime))
        object_file = open(path, "rb")
        try:
            self.finish(object_file.read())
        finally:
            object_file.close()


application = tornado.web.Application([
    (r"/(\w+.json)", MainHandler),
    (r"/sets/new.json", SetsHandler),
    (r"/sets/%s/report.json" % PLAY_TOKEN, ReportHandler),
    (r"/sets/%s/(\w+.json)" % PLAY_TOKEN, MainHandler),
    (r"/(.+)", FileHandler),

], debug=True)

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
