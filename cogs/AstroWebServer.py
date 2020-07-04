
import os
import secrets
import sys
import logging
import hashlib
from threading import Thread

import tornado.web

from cogs.AstroLogging import AstroLogging
from cogs import UIModules
from AstroLauncher import AstroLauncher
# pylint: disable=abstract-method,attribute-defined-outside-init,no-member


class WebServer(tornado.web.Application):
    def __init__(self, launcher):
        logging.getLogger('tornado.access').disabled = True
        self.launcher = launcher
        self.port = self.launcher.launcherConfig.WebServerPort
        curDir = self.launcher.launcherPath
        if self.launcher.isExecutable:
            curDir = sys._MEIPASS
        self.assetDir = os.path.join(curDir, "assets")
        # temp
        # these will later be saved and loaded from/to an .ini
        self.cookieSecret = secrets.token_hex(16).encode()
        self.passwordHash = self.launcher.launcherConfig.WebServerPasswordHash
        cfgOvr = {}

        if len(self.passwordHash) != 64:
            AstroLogging.logPrint(
                "SECURITY ALERT: You must set your Web Server Password!", "warning")
            cfgOvr["WebServerPasswordHash"] = ""
            self.passwordHash = ""

        if cfgOvr != {}:
            self.launcher.overwrite_launcher_config(cfgOvr)
            self.launcher.refresh_launcher_config()

        settings = {
            'debug': True,
            "static_path": self.assetDir,
            "cookie_secret": self.cookieSecret,
            "login_url": "/login",
            "ui_modules": UIModules,
        }
        handlers = [(r'/', MainHandler, dict(path=settings['static_path'], launcher=self.launcher)),
                    (r"/login", LoginHandler,
                     {"path": settings['static_path']}),
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
    def initialize(self, path, launcher):
        self.path = path
        self.launcher = launcher

    # @tornado.web.authenticated
    def get(self):
        s = self.launcher.DedicatedServer.settings
        if not self.application.passwordHash == "":
            self.render(os.path.join(self.path, 'index.html'),
                        isAdmin=self.current_user == b"admin",
                        title=f"Dedicated Server Status for {s.PublicIP}:{s.Port}")
        else:
            self.redirect("/login")


class LoginHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path):
        self.path = path

    def get(self):
        if not self.current_user == b"admin":
            self.render(os.path.join(self.path, 'login.html'),
                        isAdmin=self.current_user == b"admin",
                        hashSet=not self.application.passwordHash == "",
                        title="Dedicated Server Status Login")
        else:
            self.redirect("/")

    def post(self):
        if self.application.passwordHash == "":
            # write hash
            self.application.passwordHash = hashlib.sha256(
                bytes(self.get_argument("password"), 'utf-8')
            ).hexdigest()
            lfcg = AstroLauncher.LauncherConfig(
                WebServerPasswordHash=self.application.passwordHash)
            self.application.launcher.refresh_launcher_config(lfcg)
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
            "stats": dedicatedServer.DSServerStats,
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
            if not self.launcher.DedicatedServer.busy:
                self.launcher.DedicatedServer.busy = True
                t = Thread(
                    target=self.launcher.DedicatedServer.saveGame, args=())
                t.daemon = True
                t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class RebootRequestHandler(BaseHandler):
    def post(self):
        if self.current_user == b"admin":
            if not self.launcher.DedicatedServer.busy:
                self.launcher.DedicatedServer.busy = True
                t = Thread(
                    target=self.launcher.DedicatedServer.save_and_shutdown, args=())
                t.daemon = True
                t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class ShutdownRequestHandler(BaseHandler):
    def post(self):
        if self.current_user == b"admin":
            if not self.launcher.DedicatedServer.busy:
                self.launcher.DedicatedServer.busy = True
                t = Thread(
                    target=self.launcher.DedicatedServer.kill_server, args=("Website Request", True))
                t.daemon = True
                t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})
