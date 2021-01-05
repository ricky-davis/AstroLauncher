
import datetime
import hashlib
import logging
import os
import secrets
import sys
import uuid
# from pprint import pprint
from threading import Thread

import pathvalidate
import tornado.web
import tornado.websocket

from AstroLauncher import AstroLauncher
from cogs import UIModules
from cogs.AstroLogging import AstroLogging
from cogs.MultiConfig import MultiConfig

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

        self.connections = {}
        self.iterTimer = None
        self.instanceID = f"{uuid.uuid4().hex}"

        self.cookieSecret = secrets.token_hex(16).encode()
        self.passwordHash = self.launcher.launcherConfig.WebServerPasswordHash
        cfgOvr = {}
        self.baseURL = self.launcher.launcherConfig.WebServerBaseURL.rstrip(
            "/")
        self.baseURL = self.baseURL.replace("\\", "/")
        if self.baseURL != self.launcher.launcherConfig.WebServerBaseURL.rstrip(
                "/"):
            cfgOvr["WebServerBaseURL"] = self.baseURL

        if self.baseURL != "" and not self.baseURL.startswith("/"):
            cfgOvr["WebServerBaseURL"] = "/"
            self.baseURL = ""

        if len(self.passwordHash) != 64:
            cfgOvr["WebServerPasswordHash"] = ""
            self.passwordHash = ""

        if cfgOvr != {}:
            self.launcher.overwrite_launcher_config(cfgOvr)
            self.launcher.refresh_launcher_config()

        settings = {
            'autoreload': True,
            "static_path": self.assetDir,
            "static_url_prefix": self.baseURL+"/static/",
            "cookie_secret": self.cookieSecret,
            "login_url": "/login",
            "ui_modules": UIModules,
            "websocket_ping_interval": 0,
            "default_handler_class": NotFoundHandler
        }

        thandlers = [(r'', MainAltHandler,
                      dict(path=settings['static_path'], launcher=self.launcher)),
                     (r'/', MainHandler,
                      dict(path=settings['static_path'], launcher=self.launcher)),
                     (r"/login", LoginHandler,
                      dict(path=settings['static_path'], launcher=self.launcher)),
                     (r'/logout', LogoutHandler, dict(launcher=self.launcher)),
                     (r"/ws", APIWebSocket, dict(launcher=self.launcher)),
                     (r"/api", APIRequestHandler, dict(launcher=self.launcher)),
                     (r"/api/savegame", SaveRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/savegame/load", LoadSaveRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/savegame/delete", DeleteSaveRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/savegame/rename", RenameSaveRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/reboot", RebootRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/shutdown", ShutdownRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/player", PlayerRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/newsave", NewSaveRequestHandler,
                      dict(launcher=self.launcher)),
                     (r"/api/rodata", RODataRequestHandler,
                      dict(launcher=self.launcher))
                     ]

        handlers = []
        for h in thandlers:
            t = list(h)
            t[0] = self.baseURL + t[0]
            handlers.append(tuple(t))

        super().__init__(handlers, **settings)

    def run(self):
        certFile = None
        keyFile = None
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
            url = f"https://localhost{':'+str(sslPort) if sslPort != 443 else ''}{self.baseURL+'/' if self.baseURL else ''}"
        else:
            self.listen(self.port)
            url = f"http://localhost{':'+str(self.port) if self.port != 80 else ''}{self.baseURL+'/' if self.baseURL else ''}"
        AstroLogging.logPrint(f"Running a web server at {url}")
        if self.passwordHash == "":
            AstroLogging.logPrint(
                f"SECURITY ALERT: Visit {url} to set your password!", "warning")
        tornado.ioloop.IOLoop.instance().start()

    def iterWebSocketConnections(self, force=False):
        try:
            if len(self.connections) > 0:
                if self.iterTimer is None or (datetime.datetime.now() - self.iterTimer).total_seconds() > 1:
                    for _, conn in self.connections.items():
                        try:
                            conn[1].check_data_change(force=force)
                        except:
                            pass
                    self.iterTimer = datetime.datetime.now()
        except:
            pass

    @staticmethod
    def get_client_id(handler):
        client = handler.get_secure_cookie("client")
        cID = f"{uuid.uuid4()}"
        if not isinstance(handler, APIWebSocket):
            if not client:
                handler.set_secure_cookie(
                    "client", bytes(cID, 'utf-8'))
                client = cID
                return client
        else:
            if client:
                return (1, client)
            else:
                return (0, cID)

    @staticmethod
    def gen_api_data(handler, force=False):
        isAdmin = handler.current_user == b"admin"

        dedicatedServer = handler.launcher.DedicatedServer

        logs = AstroLogging.log_stream.getvalue()

        n = 200
        groups = logs.split('\n')
        logs = '\n'.join(groups[-n:])

        s = dedicatedServer.settings
        stats = None
        if dedicatedServer.DSServerStats:
            stats = dedicatedServer.DSServerStats.copy()
            stats['averageFPS'] = round(stats['averageFPS'])
            del stats['secondsInGame']
        res = {
            "forceUpdate": force,
            "viewers": len(handler.WS.connections),
            "instanceID": handler.WS.instanceID,
            "admin": isAdmin,
            "status": dedicatedServer.status,
            "stats": stats,
            "hasUpdate": handler.launcher.hasUpdate,
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
            res['savegames'] = dedicatedServer.DSListGames
        else:
            res["logs"] = ""

        return res


class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self):  # for all methods
        raise tornado.web.HTTPError(
            status_code=404,
            reason="Invalid resource path."
        )


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, launcher):
        self.launcher = launcher
        self.WS = self.launcher.webServer

    def get_current_user(self):
        return self.get_secure_cookie("login")


class APIRequestHandler(BaseHandler):
    def get(self):
        self.WS.get_client_id(self)
        self.write(WebServer.gen_api_data(self))


class APIWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self.launcher = kwargs.pop('launcher')
        self.WS = self.launcher.webServer
        self.isOpen = False
        self.oldData = {}
        # print('initializing websocket')
        super().__init__(*args, **kwargs)

    def get_current_user(self):
        return self.get_secure_cookie("login")
    # pylint: disable=arguments-differ

    def open(self):
        # print("WebSocket opened")

        cType, self.cID = self.WS.get_client_id(self)
        self.isOpen = True
        if cType:
            self.WS.connections[self.cID] = [1, self]
        else:
            self.WS.connections[self.cID] = [0, self]
        # print("open")
        # pprint(self.WS.connections)
        self.check_data_change(force=True)

    def on_message(self, message):
        self.check_data_change()

    def on_close(self):
        self.isOpen = False

        try:
            if self.cID:
                del self.WS.connections[self.cID]
        except:
            pass
        # print("close")
        # pprint(self.WS.connections)
        self.check_data_change(force=True)
        # print("WebSocket closed")

    def check_data_change(self, force=False):
        if force:
            self.oldData = {}
        newData = WebServer.gen_api_data(self, force=force)
        if newData != self.oldData and self.isOpen:
            self.oldData = newData
            self.write_message(newData)


class MainAltHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path, launcher):
        self.path = path
        self.launcher = launcher
        self.WS = self.launcher.webServer

    def get(self):
        self.redirect(self.WS.baseURL+"/")


class MainHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path, launcher):
        self.path = path
        self.launcher = launcher
        self.WS = self.launcher.webServer

    # @tornado.web.authenticated
    def get(self):
        self.WS.get_client_id(self)
        if not self.application.passwordHash == "":
            self.render(os.path.join(self.path, 'index.html'),
                        isAdmin=self.current_user == b"admin",
                        launcher=self.launcher)
        else:
            self.redirect(self.WS.baseURL+"/login")


class LoginHandler(BaseHandler):
    # pylint: disable=arguments-differ
    def initialize(self, path, launcher):
        self.path = path
        self.launcher = launcher
        self.WS = self.launcher.webServer

    def get(self):
        self.WS.get_client_id(self)
        if not self.current_user == b"admin":
            self.render(os.path.join(self.path, 'login.html'),
                        isAdmin=self.current_user == b"admin",
                        hashSet=not self.application.passwordHash == "",
                        launcher=self.launcher)
        else:
            self.redirect(self.WS.baseURL+"/")

    def post(self):
        self.WS.get_client_id(self)
        if self.application.passwordHash == "":
            # write hash
            self.application.passwordHash = hashlib.sha256(
                bytes(self.get_argument("password"), 'utf-8')
            ).hexdigest()
            lfcg = AstroLauncher.LauncherConfig(
                WebServerPasswordHash=self.application.passwordHash)
            self.application.launcher.refresh_launcher_config(lfcg)
            self.redirect(self.WS.baseURL+"/login")
        else:
            # check hash
            sendHash = hashlib.sha256(
                bytes(self.get_argument("password"), 'utf-8')
            ).hexdigest()
            if sendHash == self.application.passwordHash:
                self.set_secure_cookie("login", bytes(
                    "admin", 'utf-8'))
                self.redirect(self.WS.baseURL+"/")
            else:
                self.redirect(self.WS.baseURL+"/login")


class LogoutHandler(BaseHandler):
    def get(self):
        self.WS.get_client_id(self)
        self.clear_cookie('login')
        self.redirect(self.WS.baseURL+"/")


class RODataRequestHandler(BaseHandler):
    def get(self):
        ip = self.request.headers.get("X-Real-IP") or \
            self.request.headers.get("X-Forwarded-For") or \
            self.request.remote_ip
        if ip == "::1":
            evt = self.get_argument('evt')
            msg = self.get_argument('msg')
            name = self.get_argument('name')
            if evt == "chat" or evt == "cmd":
                AstroLogging.logPrint(msg, msgType=evt, playerName=name)
            self.write({"message": "Success"})
        else:
            print(f"{ip} Tried to send fake chat message")
            self.write({"message": "Error"})


class SaveRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            t = Thread(
                target=self.launcher.DedicatedServer.saveGame, args=())
            t.daemon = True
            t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class NewSaveRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            t = Thread(
                target=self.launcher.DedicatedServer.newSaveGame, args=())
            t.daemon = True
            t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class LoadSaveRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            data = tornado.escape.json_decode(self.request.body)
            if "save" in data and data["save"] is not None:
                saveData = data["save"]
                GL = self.launcher.DedicatedServer.DSListGames
                if saveData['name'] != GL['activeSaveName']:
                    t = Thread(
                        target=self.launcher.DedicatedServer.loadSaveGame, args=(saveData,))
                    t.daemon = True
                    t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class DeleteSaveRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            data = tornado.escape.json_decode(self.request.body)
            if "save" in data and data["save"] is not None:
                saveData = data["save"]
                t = Thread(
                    target=self.launcher.DedicatedServer.deleteSaveGame, args=(saveData,))
                t.daemon = True
                t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class RenameSaveRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        fData = False
        if self.current_user == b"admin":
            data = tornado.escape.json_decode(self.request.body)
            if "nName" in data and data["nName"] is not None and "save" in data and data["save"] is not None:
                oldSave = data["save"]
                newSaveName = data["nName"]

                if pathvalidate.is_valid_filename(oldSave['name']) and pathvalidate.is_valid_filename(newSaveName):
                    GL = self.launcher.DedicatedServer.DSListGames
                    if newSaveName not in [x['name'] for x in GL['gameList']]:
                        t = Thread(
                            target=self.launcher.DedicatedServer.renameSaveGame, args=(oldSave, newSaveName))
                        t.daemon = True
                        t.start()
                    else:
                        fData = True
                else:
                    fData = True
            else:
                fData = True
            self.write({"message": "Success"})
        else:
            fData = True
            self.write({"message": "Not Authenticated"})

        if fData:
            cID = self.WS.get_client_id(self)
            self.WS.connections[cID].check_data_change(
                force=True)


class RebootRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            t = Thread(
                target=self.launcher.DedicatedServer.save_and_shutdown, args=())
            t.daemon = True
            t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class ShutdownRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        if self.current_user == b"admin":
            t = Thread(
                target=self.launcher.DedicatedServer.kill_server, args=("Website Request", True))
            t.daemon = True
            t.start()
            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})


class PlayerRequestHandler(BaseHandler):
    def post(self):
        self.WS.get_client_id(self)
        data = tornado.escape.json_decode(self.request.body)
        try:
            players = self.launcher.DedicatedServer.players['playerInfo']
        except:
            return
        playerGUID = None
        playerName = None
        player = None
        if "guid" in data and data["guid"] is not None:
            playerGUID = data["guid"]

        if playerGUID:
            player = [x for x in players if x['playerGuid']
                      == playerGUID][0]
            playerName = player["playerName"]
            if playerName == "":
                playerName = None
        if "name" in data:
            playerName = data["name"]
            try:
                player = [x for x in players if x['playerName']
                          == playerName][0]
            except:
                pass
        if playerGUID is None and playerName is None:
            self.write({"message": "Missing variable! (name or guid)"})
            return

        if player and player["playerCategory"] == "Owner":
            self.write({"message": "Cannot touch the Owner!"})
            return
        if playerName in self.launcher.DedicatedServer.stripPlayers:
            self.launcher.DedicatedServer.stripPlayers.remove(
                playerName)
        action = data['action']
        if self.current_user == b"admin":
            if playerGUID:
                if action == "kick":
                    self.launcher.DedicatedServer.AstroRCON.DSKickPlayerGuid(
                        playerGUID)
                    AstroLogging.logPrint(f"Kicking player: {playerName}")

            if action == "ban":
                if playerGUID:
                    if len([x for x in players if x["playerName"] == playerName and x["inGame"]]) > 0:
                        self.launcher.DedicatedServer.AstroRCON.DSKickPlayerGuid(
                            playerGUID)
                if playerName:
                    self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                        playerName, "Blacklisted")
                    self.launcher.DedicatedServer.refresh_settings()
                    AstroLogging.logPrint(f"Banning player: {playerName}")

            if action == "WL":
                if playerName:
                    self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                        playerName, "Whitelisted")
                    self.launcher.DedicatedServer.refresh_settings()
                    AstroLogging.logPrint(f"Whitelisting player: {playerName}")

            if action == "admin":
                if playerName:
                    self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                        playerName, "Admin")
                    self.launcher.DedicatedServer.refresh_settings()
                    AstroLogging.logPrint(
                        f"Setting player as Admin: {playerName}")

            if action == "reset":
                if playerName:
                    self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                        playerName, "Unlisted")
                    self.launcher.DedicatedServer.refresh_settings()
                    AstroLogging.logPrint(
                        f"Resetting perms for player: {playerName}")

            if action == "remove":
                self.launcher.DedicatedServer.AstroRCON.DSSetPlayerCategoryForPlayerName(
                    playerName, "Unlisted")
                pp = list(
                    self.launcher.DedicatedServer.settings.PlayerProperties)

                pp = [
                    x for x in pp if not (((f'PlayerFirstJoinName="{playerName}"' in x
                                            and 'PlayerRecentJoinName=""' in x) or
                                           ('PlayerFirstJoinName=""' in x
                                            and f'PlayerRecentJoinName="{playerName}"' in x))
                                          or f'PlayerGuid="{playerGUID}"' in x)]

                confPath = os.path.join(
                    self.launcher.astroPath, r"Astro\Saved\Config\WindowsServer\AstroServerSettings.ini")

                ovrConfig = {
                    "/Script/Astro.AstroServerSettings": {
                        "PlayerProperties": pp
                    }
                }
                MultiConfig().overwrite_with(confPath, ovrConfig)
                self.launcher.DedicatedServer.stripPlayers.append(playerName)
                self.launcher.DedicatedServer.players['playerInfo'] = [
                    x for x in self.launcher.DedicatedServer.players['playerInfo']
                    if x['playerName'] not in self.launcher.DedicatedServer.stripPlayers]
                self.launcher.DedicatedServer.refresh_settings()
                AstroLogging.logPrint(
                    f"Removing player data: {playerName}")

            playerList = self.launcher.DedicatedServer.AstroRCON.DSListPlayers()
            if playerList is not None:
                self.launcher.DedicatedServer.players = playerList

            self.write({"message": "Success"})
        else:
            self.write({"message": "Not Authenticated"})
