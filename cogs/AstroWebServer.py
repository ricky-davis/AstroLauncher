import threading
import http.server
import socketserver
import sys
import os
import json
import time

from cogs.AstroLogging import AstroLogging


class ServerHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    webServer = None
    dedicatedServer = None

    # pylint: disable=redefined-builtin
    def log_message(self, format, *args):
        return

    def do_POST(self):
        self.webServer = ServerHttpRequestHandler.webServer
        success = False
        if self.path == '/api/savegame':
            self.webServer.launcher.DedicatedServer.busy = True
            self.webServer.launcher.DedicatedServer.saveGame()
            success = True
        if self.path == '/api/reboot':
            self.webServer.launcher.DedicatedServer.busy = True
            self.webServer.launcher.DedicatedServer.saveGame()
            self.webServer.launcher.DedicatedServer.busy = True
            time.sleep(1)
            self.webServer.launcher.DedicatedServer.busy = True
            self.webServer.launcher.DedicatedServer.shutdownServer()
            success = True
        if self.path == '/api/shutdown':
            self.webServer.launcher.DedicatedServer.busy = True
            self.webServer.launcher.DedicatedServer.kill_server(
                "Website Request", save=True)
            success = True

        if success:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(
                bytes(json.dumps({"message": "Success"}), "utf8"))
        return

    def do_GET(self):
        try:
            self.webServer = ServerHttpRequestHandler.webServer
            if self.path == '/api':
                # api
                queue = self.webServer.queue
                dedicatedServer = queue.get()
                queue.put(dedicatedServer)

                self.send_response(200)

                self.send_header("Content-type", "application/json")
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                logs = AstroLogging.log_stream.getvalue()

                n = 21
                groups = logs.split('\n')
                logs = '\n'.join(groups[-n:])

                s = dedicatedServer.settings
                res = {
                    "status": dedicatedServer.status,
                    "busy": dedicatedServer.busy,
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

                self.wfile.write(
                    bytes(json.dumps(res, separators=(',', ':')), "utf8"))

            elif self.path in self.webServer.routes:
                # static files
                self.send_response(200)
                if self.webServer.routes[self.path]['type'] == "text":
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(
                        self.webServer.routes[self.path]['content'])
                elif self.webServer.routes[self.path]['type'] == "image":
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(
                        self.webServer.routes[self.path]['content'])

            else:
                # 404
                self.send_response(404)

                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(bytes(
                    "<html><head><title>Not Found</title></head><body>Not Found</body></html>", 'utf8'))

            return
        except:
            pass


class AstroWebServer(threading.Thread):
    def __init__(self, queue, launcher):
        threading.Thread.__init__(self)
        self.launcher = launcher
        self.queue = queue
        ServerHttpRequestHandler.webServer = self
        self.handler = ServerHttpRequestHandler
        self.routes = None

    def run(self):
        # assign queue inside the thread

        # load content from files to be served
        self.routes = {
            "/": {
                "path": "index.html",
                "type": "text"
            },
            "/script.js": {
                "path": "script.js",
                "type": "text"
            },
            "/bootstrap.bundle.min.js": {
                "path": "bootstrap.bundle.min.js",
                "type": "text"
            },
            "/bootstrap.min.css": {
                "path": "bootstrap.min.css",
                "type": "text"
            },
            "/jquery-3.5.1.min.js": {
                "path": "jquery-3.5.1.min.js",
                "type": "text"
            },
            "/style.css": {
                "path": "style.css",
                "type": "text"
            },
            "/astrolauncherlogo.ico": {
                "path": "astrolauncherlogo.ico",
                "type": "image"
            }
        }

        for key in self.routes:
            # pylint: disable=no-member, protected-access
            with open(os.path.join(sys._MEIPASS, self.routes[key]['path']), 'rb') as contentFile:
                self.routes[key]['content'] = contentFile.read()

        with socketserver.TCPServer(("", self.launcher.launcherConfig.WebServerPort), self.handler) as httpd:
            httpd.serve_forever()


def startWebServer(exchangeQueue, launcher):
    try:
        server = AstroWebServer(exchangeQueue, launcher)
        server.daemon = True
        server.start()
    except Exception as e:
        print("ERROR: %s" % e)
