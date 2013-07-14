import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, World!")

    def post(self):
        self.set_header("Content-Type", "application/json")
        login = self.get_argument('login')
        password = self.get_argument('password')
        if login != 'user1' or password != '123':
            self.set_status(403)
        self.write(b'{"current_user":{"id":902671,"login":"tataurov","popup_prefs":"ask","next_mix_prefs":"ask","slug":"tataurov","bio_html":"<p></p>","location":"Yekaterinburg, Sverdlovskaya obl., Russian Federation","path":"/tataurov","avatar_urls":{"sq56":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&w=56&h=56&fit=crop","sq72":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&w=72&h=72&fit=crop","sq100":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&w=100&h=100&fit=crop","max200":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&w=200&h=200&fit=max","max250w":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&w=250&h=250&fit=max","original":"http://8tracks.imgix.net/avatars/000/902/671/32908.original.jpg?fm=jpg&q=65&sharp=15&vib=10&"},"subscribed":false,"followed_by_current_user":false,"follows_count":6,"web_safe_browse":false,"mobile_safe_browse":true},"auth_token":"902671;ca11f318586b05f1fc31b41ed17866e20512ed19","user_token":"902671;ca11f318586b05f1fc31b41ed17866e20512ed19","status":"200 OK","errors":null,"notices":"You are now logged in as tataurov","logged_in":true,"api_warning":["You didn\'t pass an API version, defaulting to api_version=2."],"api_version":2}')
        print("successfully send")

application = tornado.web.Application([
    (r"/sessions.json", MainHandler),
])

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
