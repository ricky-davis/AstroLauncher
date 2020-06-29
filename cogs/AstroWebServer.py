
import os
import secrets
import sys
import logging
import hashlib

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

        # temp
        # these will later be saved and loaded from/to an .ini
        self.cookieSecret = secrets.token_hex(16).encode()
        self.passwordHash = ""

        settings = {
            'debug': True,
            "static_path": os.path.join(curDir, "assets"),
            "cookie_secret": self.cookieSecret,
            "login_url": "/login"
        }
        handlers = [(r'/', MainHandler, {"path": settings['static_path']}),
                    (r"/login", LoginHandler, {"path": settings['static_path']}),
                    (r'/logout', LogoutHandler, dict(launcher=self.launcher)),
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
        return self.get_secure_cookie("login")


class MainHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path):
        self.path = path

    # @tornado.web.authenticated
    def get(self):
        self.render(os.path.join(self.path, 'index.html'),
                    isAdmin=self.current_user == b"admin")


class LoginHandler(BaseHandler):
    def initialize(self, path):
        self.path = path

    def get(self):
        self.render(os.path.join(self.path, 'login.html'),
                    isAdmin=self.current_user == b"admin",
                    hashSet=not self.application.passwordHash == "")

    def post(self):
        if self.application.passwordHash == "":
            # write hash
            self.application.passwordHash = hashlib.sha256(
                bytes(self.get_argument("password"), 'utf-8')
            ).hexdigest()
            self.redirect("/login")
        else:
            # check hash
            sendHash = hashlib.sha256(
                bytes(self.get_argument("password"), 'utf-8')
            ).hexdigest()
            if sendHash == self.application.passwordHash:
                self.set_secure_cookie("login", bytes(
                    "admin", 'utf-8'))
                self.redirect("/")
            else:
                self.redirect("/login")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('login')
        self.redirect('/')


class APIRequestHandler(BaseHandler):
    def get(self):

        isAdmin = self.current_user == b"admin"

        dedicatedServer = self.launcher.DedicatedServer

        logs = AstroLogging.log_stream.getvalue()

        n = 200
        groups = logs.split('\n')
        logs = '\n'.join(groups[-n:])

        s = dedicatedServer.settings
        res = {
            "admin": isAdmin,
            "status": dedicatedServer.status,
            "version": self.launcher.DSServerVersion,
            "settings": {
                "MaxServerFramerate": s.MaxServerFramerate,
                "PublicIP": s.PublicIP,
                "ServerName": s.ServerName,
                "MaximumPlayerCount": s.MaximumPlayerCount,
                "OwnerName": s.OwnerName,
                "Port": s.Port
            },
            "players": dedicatedServer.players,
        }

        # only send full logs if admin
        if isAdmin:
            res["logs"] = logs
        else:
            res["logs"] = ""

        self.write(res)


class SaveRequestHandler(BaseHandler):
    def post(self):
        if self.current_user == b"admin":
            self.launcher.DedicatedServer.busy = True
            self.launcher.DedicatedServer.saveGame()
            self.write({"message": "Success"})


class RebootRequestHandler(BaseHandler):
    def post(self):
        if self.current_user == b"admin":
            self.launcher.DedicatedServer.busy = True
            self.launcher.DedicatedServer.save_and_shutdown()
            self.write({"message": "Success"})


class ShutdownRequestHandler(BaseHandler):
    def post(self):
        if self.current_user == b"admin":
            self.launcher.DedicatedServer.busy = True
            self.launcher.DedicatedServer.kill_server(
                "Website Request", save=True)
            self.write({"message": "Success"})
