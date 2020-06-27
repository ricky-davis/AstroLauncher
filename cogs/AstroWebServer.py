
import os
import secrets
import sys
import logging

import tornado.web

from cogs.AstroLogging import AstroLogging

# pylint: disable=abstract-method,attribute-defined-outside-init,no-member


class WebServer(tornado.web.Application):
    def __init__(self, launcher):
        logging.getLogger('tornado.access').disabled = True
        self.launcher = launcher
        self.port = self.launcher.launcherConfig.WebServerPort
        curDir = self.launcher.launcherPath
        if self.launcher.isExecutable:
            curDir = sys._MEIPASS

        settings = {
            'debug': True,
            "static_path": os.path.join(curDir, "assets"),
            "cookie_secret": secrets.token_hex(16).encode(),
            "login_url": "/login"
        }
        handlers = [(r'/', MainHandler, {"path": settings['static_path']}),
                    (r"/login", LoginHandler, dict(launcher=self.launcher)),
                    (r"/api", APIRequestHandler, dict(launcher=self.launcher)),
                    (r"/api/savegame", SaveRequestHandler,
                     dict(launcher=self.launcher)),
                    (r"/api/reboot", RebootRequestHandler,
                     dict(launcher=self.launcher)),
                    (r"/api/shutdown", ShutdownRequestHandler,
                     dict(launcher=self.launcher)),
                    ]
        super().__init__(handlers, **settings)

    def run(self):
        self.listen(self.port)
        url = f"http://localhost:{self.port}"
        AstroLogging.logPrint(f"Running a web server at {url}")
        tornado.ioloop.IOLoop.instance().start()


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, launcher):
        self.launcher = launcher
        self.WS = self.launcher.webServer

    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path):
        self.path = path

    # @tornado.web.authenticated
    def get(self):
        self.render(os.path.join(self.path, 'index.html'))


class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")


class APIRequestHandler(BaseHandler):
    def get(self):
        # api
        dedicatedServer = self.launcher.DedicatedServer

        logs = AstroLogging.log_stream.getvalue()

        n = 200
        groups = logs.split('\n')
        logs = '\n'.join(groups[-n:])

        s = dedicatedServer.settings
        res = {
            "status": dedicatedServer.status,
            "settings": {
                "MaxServerFramerate": s.MaxServerFramerate,
                "PublicIP": s.PublicIP,
                "ServerName": s.ServerName,
                "MaximumPlayerCount": s.MaximumPlayerCount,
                "OwnerName": s.OwnerName,
                "OwnerGuid": s.OwnerGuid,
                "DenyUnlistedPlayers": s.DenyUnlistedPlayers,
                "VerbosePlayerProperties": s.VerbosePlayerProperties,
                "AutoSaveGameInterval": s.AutoSaveGameInterval,
                "BackupSaveGamesInterval": s.BackupSaveGamesInterval,
                "ServerGuid": s.ServerGuid,
                "ActiveSaveFileDescriptiveName": s.ActiveSaveFileDescriptiveName,
                "ServerAdvertisedName": s.ServerAdvertisedName,
                "Port": s.Port
            },
            "players": dedicatedServer.players,
            "logs": logs
        }
        self.write(res)


class SaveRequestHandler(BaseHandler):
    def post(self):
        self.launcher.DedicatedServer.busy = True
        self.launcher.DedicatedServer.saveGame()
        self.write({"message": "Success"})


class RebootRequestHandler(BaseHandler):
    def post(self):
        self.launcher.DedicatedServer.busy = True
        self.launcher.DedicatedServer.save_and_shutdown()
        self.write({"message": "Success"})


class ShutdownRequestHandler(BaseHandler):
    def post(self):
        self.launcher.DedicatedServer.busy = True
        self.launcher.DedicatedServer.kill_server(
            "Website Request", save=True)
        self.write({"message": "Success"})
