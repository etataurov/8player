import tornado.ioloop
import tornado.web
import os
import datetime
import stagger

MUSIC_DIR = 'test_music'
PLAY_TOKEN = '12345'

# TODO check api_key and user token in every request


def tracks_iterator():
    while True:
        for filename in os.listdir(MUSIC_DIR):
            if os.path.isfile(os.path.join(MUSIC_DIR, filename)):
                yield filename

TRACKS = tracks_iterator()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # TODO get filename param
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        with open('mixes.json') as mixes:
            self.finish(mixes.read())

    def post(self):
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        login = self.get_argument('login')
        password = self.get_argument('password')
        if login != 'user1' or password != '123':
            self.set_status(403)
        with open('sessions.json') as sessions:
            self.finish(sessions.read())
        print("successfully send")


class TagsHandler(tornado.web.RequestHandler):
    def get(self):
        # TODO get filename param
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        with open('tags.json') as mixes:
            self.finish(mixes.read())


class SetsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""{"status": "200 OK", "errors": null, "api_version": 2, "api_warning": ["You didn't pass an API version, defaulting to api_version=2."], "notices": null, "play_token": "%s"}""" % PLAY_TOKEN)
        self.finish()


class PlayHandler(tornado.web.RequestHandler):
    def next_track(self):
        filename = next(TRACKS)
        track = stagger.read_tag(os.path.join(MUSIC_DIR, filename))
        return {'filename': filename, 'title': track.title, 'artist': track.artist}

    def get(self):
        mix_id = self.get_argument('mix_id')
        self.set_header("Content-Type", 'application/json; charset=utf-8')
        with open('play.json') as play:
            self.finish(play.read() % self.next_track())


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
    (r"/sessions.json", MainHandler),
    (r"/mixes.json", MainHandler),
    (r"/tags.json", TagsHandler),
    (r"/sets/new.json", SetsHandler),
    (r"/sets/%s/play.json" % PLAY_TOKEN, PlayHandler),
    (r"/sets/%s/next.json" % PLAY_TOKEN, PlayHandler),
    (r"/sets/%s/report.json" % PLAY_TOKEN, ReportHandler),
    (r"/(.+)", FileHandler),

], debug=True)

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
