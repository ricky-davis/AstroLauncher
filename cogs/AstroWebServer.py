
import hashlib
import logging
import os
import secrets
import sys
from threading import Thread

import tornado.web

from AstroLauncher import AstroLauncher
from cogs import UIModules
from cogs.AstroLogging import AstroLogging

# pylint: disable=abstract-method,attribute-defined-outside-init,no-member


class WebServer(tornado.web.Application):
    def __init__(self, launcher):
        logging.getLogger('tornado.access').disabled = True
        self.launcher = launcher
        self.port = self.launcher.launcherConfig.WebServerPort
        self.ssl = False
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
            "ui_modules": UIModules
        }

        handlers = [(r'/', MainHandler, dict(path=settings['static_path'], launcher=self.launcher)),
                    (r"/login", LoginHandler,
                     dict(path=settings['static_path'], launcher=self.launcher)),
                    (r'/logout', LogoutHandler, dict(launcher=self.launcher)),
                    (r"/api", APIRequestHandler, dict(launcher=self.launcher)),
                    (r"/api/savegame", SaveRequestHandler,
                     dict(launcher=self.launcher)),
                    (r"/api/reboot", RebootRequestHandler,
                     dict(launcher=self.launcher)),
                    (r"/api/shutdown", ShutdownRequestHandler,
                     dict(launcher=self.launcher)),
                    (r"/api/player", PlayerRequestHandler,
                     dict(launcher=self.launcher)),
                    ]
        super().__init__(handlers, **settings)

    def run(self):
        if self.launcher.launcherConfig.EnableWebServerSSL:
            certFile = self.launcher.launcherConfig.SSLCertFile
            keyFile = self.launcher.launcherConfig.SSLKeyFile
            if os.path.exists(keyFile) and os.path.exists(certFile):
                self.ssl = True
            else:
                AstroLogging.logPrint(
                    "No SSL Certificates specified. Defaulting to HTTP", "warning")
        if self.ssl:
            sslPort = self.launcher.launcherConfig.SSLPort
            ssl_options = {
                "certfile": os.path.join(self.launcher.launcherPath, certFile),
                "keyfile": os.path.join(self.launcher.launcherPath, keyFile),
            }
            self.listen(sslPort, ssl_options=ssl_options)
            url = f"https://localhost{':'+str(sslPort) if sslPort != 443 else ''}"
        else:
            self.listen(self.port)
            url = f"http://localhost{':'+str(self.port) if self.port != 80 else ''}"
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
        if not self.application.passwordHash == "":
            self.render(os.path.join(self.path, 'index.html'),
                        isAdmin=self.current_user == b"admin",
                        launcher=self.launcher)
        else:
            self.redirect("/login")


class LoginHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path, launcher):
        self.path = path
        self.launcher = launcher

    def get(self):
        if not self.current_user == b"admin":
            self.render(os.path.join(self.path, 'login.html'),
                        isAdmin=self.current_user == b"admin",
                        hashSet=not self.application.passwordHash == "",
                        launcher=self.launcher)
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
            "hasUpdate": self.launcher.hasUpdate,
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
                t = Thread(
                    target=self.launcher.DedicatedServer.kill_server, args=("Website Request", True))
                t.daemon = True
                t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class PlayerRequestHandler(BaseHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        players = self.launcher.DedicatedServer.players['playerInfo']
        playerGUID = data["guid"]
        player = [x for x in players if x['playerGuid']
                  == playerGUID and x["playerName"] != ""][0]
        playerName = player["playerName"]
        action = data['action']
        if player["playerCategory"] == "Owner":
            self.write({"message": "Cannot touch the Owner!"})
            return
        if self.current_user == b"admin":
            if action == "kick":
                self.launcher.DedicatedServer.AstroRCON.DSKickPlayerGuid(
                    playerGUID)
                AstroLogging.logPrint(f"Kicking player: {playerName}")

            if action == "ban":
                if len([x for x in players if x["playerName"] == playerName and x["inGame"]]) > 0:
                    self.launcher.DedicatedServer.AstroRCON.DSKickPlayerGuid(
                        playerGUID)
                self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                    playerName, "Blacklisted")
                self.launcher.DedicatedServer.refresh_settings()
                AstroLogging.logPrint(f"Banning player: {playerName}")

            if action == "WL":
                self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                    playerName, "Whitelisted")
                self.launcher.DedicatedServer.refresh_settings()
                AstroLogging.logPrint(f"Whitelisting player: {playerName}")

            if action == "admin":
                self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                    playerName, "Admin")
                self.launcher.DedicatedServer.refresh_settings()
                AstroLogging.logPrint(f"Setting player as Admin: {playerName}")

            if action == "reset":
                self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                    playerName, "Unlisted")
                self.launcher.DedicatedServer.refresh_settings()
                AstroLogging.logPrint(
                    f"Resetting perms for player: {playerName}")

            playerList = self.launcher.DedicatedServer.AstroRCON.DSListPlayers()
            if playerList is not None:
                self.launcher.DedicatedServer.players = playerList

            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})
