import threading
import http.server
import socketserver
import sys
import os
import json


class ServerHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    webServer = None

    def do_GET(self):
        self.webServer = ServerHttpRequestHandler.webServer
        if self.path == '/api':
            # api
            queue = self.webServer.queue
            dedicatedServer = queue.get()
            queue.put(dedicatedServer)

            self.send_response(200)

            self.send_header("Content-type", "text/json")
            self.end_headers()

            s = dedicatedServer.settings
            res = {
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
                "players": dedicatedServer.players
            }

            self.wfile.write(
                bytes(json.dumps(res, separators=(',', ':')), "utf8"))

        elif self.path in self.webServer.routes:
            # static files
            self.send_response(200)
            if self.webServer.routes[self.path]['type'] == "text":
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.webServer.routes[self.path]['content'])
            elif self.webServer.routes[self.path]['type'] == "image":
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(self.webServer.routes[self.path]['content'])

        else:
            # 404
            self.send_response(404)

            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(bytes(
                "<html><head><title>Not Found</title></head><body>Not Found</body></html>", 'utf8'))

        return


class AstroWebServer(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
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

        with socketserver.TCPServer(("", 80), self.handler) as httpd:
            httpd.serve_forever()


def startWebServer(exchangeQueue):
    try:
        server = AstroWebServer(exchangeQueue)
        server.daemon = True
        server.start()
    except Exception as e:
        print("ERROR: %s" % e)
