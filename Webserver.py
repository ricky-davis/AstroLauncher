import tornado.web


class WebServer(tornado.web.Application):

    def __init__(self, launcher, port):
        self.launcher = launcher
        self.port = port
        handlers = [(r"/test", TestHandler, dict(launcher=self.launcher))]
        settings = {'debug': True}
        super().__init__(handlers, **settings)

    def run(self):
        self.listen(self.port)
        url = f"http://localhost:{self.port}"
        self.launcher.logPrint(f"Running a web server at {url}")
        tornado.ioloop.IOLoop.instance().start()


class TestHandler(tornado.web.RequestHandler):
    def initialize(self, launcher):
        self.launcher = launcher

    def get(self):
        self.write(self.launcher.ipPortCombo)
