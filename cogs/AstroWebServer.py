import http.server
import json
import os
import socketserver
import sys
import threading

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
            self.webServer.launcher.DedicatedServer.save_and_shutdown()
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

                self.wfile.write(
                    bytes(json.dumps(res, separators=(',', ':')), "utf8"))

            elif self.path in self.webServer.routes:
                # static files
                self.send_response(200)
                self.send_header(
                    'Content-type', self.webServer.routes[self.path]['type'])
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

    def getListOfFiles(self, dirName):
        # create a list of file and sub directories
        # names in the given directory
        listOfFile = os.listdir(dirName)
        allFiles = list()
        # Iterate over all the entries
        for entry in listOfFile:
            # Create full path
            fullPath = os.path.join(dirName, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(fullPath):
                allFiles = allFiles + self.getListOfFiles(fullPath)
            else:
                allFiles.append(fullPath)

        return allFiles

    def run(self):

        # load content from files to be served
        # pylint: disable=no-member, protected-access
        curDir = ""
        if self.launcher.isExecutable:
            curDir = sys._MEIPASS
        self.routes = {
            "/": {"path": "assets/index.html", "type": "text/html"}}
        fileNames = self.getListOfFiles(os.path.join(curDir, "assets"))
        fileNames = [os.path.relpath(x, curDir) for x in fileNames]
        # print(fileNames)
        assets = f"assets{os.sep}"
        for f in fileNames:
            ext = f.split(".")[-1]
            ctype = "text/html"
            if ext == "ico":
                ctype = "image/x-icon"
            if ext == "png":
                ctype = "image/png"
            if ext == "ttf":
                ctype = "font/ttf"
            self.routes[f"/{f.replace(assets , '').replace(os.sep , '/')}"] = {
                "path": f"{f}", "type": ctype}
        # print(self.routes)
        for key in self.routes:
            # pylint: disable=no-member, protected-access
            with open(os.path.join(curDir, self.routes[key]['path']), 'rb') as contentFile:
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
