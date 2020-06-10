
import AstroAPI
import ValidateSettings

import argparse
import atexit
import ctypes
import json
import logging
import os
import psutil
import requests
import signal
import socket
import subprocess
import sys
import time

from collections import OrderedDict
from contextlib import contextmanager
from logging.handlers import TimedRotatingFileHandler
from pprint import pprint, pformat

'''

'''


class AstroLauncher():
    """ Starts a new instance of the Server Launcher"""

    def __init__(self, astropath, disable_auto_update=False):
        self.astropath = astropath
        self.version = "v1.2.3"
        self.latestURL = "https://github.com/ricky-davis/AstroLauncher/releases/latest"
        self.isExecutable = os.path.samefile(sys.executable, sys.argv[0])
        self.disable_auto_update = disable_auto_update

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-6s %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.INFO)

        console = logging.StreamHandler()
        console.setFormatter(formatter)

        logsPath = os.path.join(astropath, 'logs\\')
        if not os.path.exists(logsPath):
            os.makedirs(logsPath)
        fileLogHandler = TimedRotatingFileHandler(os.path.join(
            astropath, 'logs', "server.log"),  'midnight', 1)
        fileLogHandler.setFormatter(formatter)

        rootLogger.addHandler(console)
        rootLogger.addHandler(fileLogHandler)

        self.logPrint(f"Astroneer Dedicated Server Launcher {self.version}")
        latestVersion = AstroLauncher.check_for_update()
        if latestVersion != self.version:
            self.logPrint(
                f"UPDATE: There is a newer version of the launcher out! {latestVersion}")
            self.logPrint(f"Download it at {self.latestURL}")
            if self.isExecutable and not self.disable_auto_update:
                self.autoupdate()
        self.logPrint("Starting a new session")
        self.settings = ValidateSettings.get_current_settings(astropath)

        self.logPrint("Checking the network configuration..")

        networkCorrect = ValidateSettings.test_network(
            self.settings['PublicIP'], int(self.settings['Port']))
        if networkCorrect:
            self.logPrint("Server network configuration good!")
        else:
            self.logPrint(
                "I can't seem to validate your network settings..", "warning")
            self.logPrint(
                "Make sure to Port Forward and enable NAT Loopback", "warning")
            self.logPrint(
                "If nobody can connect, Port Forward.", "warning")
            self.logPrint(
                "If others are able to connect, but you aren't, enable NAT Loopback.", "warning")

        rconNetworkCorrect = not (ValidateSettings.test_network(
            self.settings['PublicIP'], int(self.settings['ConsolePort'])))
        if rconNetworkCorrect:
            self.logPrint("Remote Console network configuration good!")
        else:
            self.logPrint(
                f"SECURITY ALERT: Your console port ({self.settings['ConsolePort']}) is Port Forwarded!", "warning")
            self.logPrint(
                "SECURITY ALERT: This allows anybody to control your server.", "warning")
            self.logPrint(
                "SECURITY ALERT: Disable this ASAP to prevent issues.", "warning")
            time.sleep(5)

        self.headers = AstroAPI.base_headers
        self.activePlayers = []
        self.ipPortCombo = f'{self.settings["PublicIP"]}:{self.settings["Port"]}'
        serverguid = self.settings['ServerGuid'] if self.settings['ServerGuid'] != '' else "REGISTER"
        self.headers['X-Authorization'] = AstroAPI.generate_XAUTH(
            self.settings['ServerGuid'])

        atexit.register(self.kill_server, "Launcher shutting down")
        self.start_server()

    def logPrint(self, message, type="info"):
        if type == "info":
            logging.info(pformat(message))
        if type == "warning":
            logging.warning(pformat(message))

    def kill_server(self, reason):
        self.logPrint(f"Kill Server: {reason}")
        try:
            self.deregister_all_server()
        except:
            pass
        # Kill all child processes
        try:
            for child in psutil.Process(self.process.pid).children():
                child.kill()
        except:
            pass
        # Kill current process
        try:
            os.kill(os.getpid(), 9)
        except:
            pass

    def start_server(self):
        oldLobbyIDs = self.deregister_all_server()
        self.logPrint("Starting Server process...")
        time.sleep(3)
        startTime = time.time()
        cmd = [os.path.join(self.astropath, "AstroServer.exe"), '-log']
        self.process = subprocess.Popen(cmd)

        if self.isExecutable:
            daemonCMD = [sys.executable, '--daemon', '-l',
                         str(os.getpid()), '-c', str(self.process.pid)]
        else:
            daemonCMD = [sys.executable, sys.argv[0], '--daemon',
                         '-l', str(os.getpid()), '-c', str(self.process.pid)]
        # print(' '.join(daemonCMD))

        self.watchDogProcess = subprocess.Popen(
            daemonCMD, shell=False, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

        # Wait for server to finish registering...
        registered = False
        apiRateLimit = 2
        while registered == False:
            try:
                serverData = (AstroAPI.get_server(
                    self.ipPortCombo, self.headers))
                # pprint(serverData)
                serverData = serverData['data']['Games']
                lobbyIDs = [x['LobbyID'] for x in serverData]
                if len(set(lobbyIDs) - set(oldLobbyIDs)) == 0:
                    time.sleep(apiRateLimit)
                else:
                    registered = True
                    del oldLobbyIDs
                    self.LobbyID = serverData[0]['LobbyID']

                if self.process.poll() != None:
                    self.logPrint(
                        "Server was forcefully closed before registration. Exiting....")
                    return False
            except Exception as e:
                self.logPrint(
                    "Failed to check server. Probably hit rate limit. Backing off and trying again...")
                apiRateLimit += 1
                time.sleep(apiRateLimit)

        doneTime = time.time()
        elapsed = doneTime - startTime
        self.logPrint(
            f"Server ready with ID {self.LobbyID}. Took {round(elapsed,2)} seconds to register.")

        self.server_loop()

    def server_loop(self):
        while(True):
            if self.process.poll() != None:
                self.logPrint("Server was closed. Restarting..")
                return self.start_server()
            curPlayers = self.DSListPlayers()
            if curPlayers is not None:
                if len(curPlayers) > len(self.activePlayers):
                    playerDif = list(set(curPlayers) -
                                     set(self.activePlayers))[0]
                    self.activePlayers = curPlayers
                    self.logPrint(f"Player joining: {playerDif}")
                elif len(curPlayers) < len(self.activePlayers):
                    playerDif = list(
                        set(self.activePlayers) - set(curPlayers))[0]
                    self.activePlayers = curPlayers
                    self.logPrint(f"Player left: {playerDif}")

            time.sleep(2)

    def DSListPlayers(self):
        with AstroLauncher.session_scope(self.settings['ConsolePort']) as s:
            s.sendall(b"DSListPlayers\n")
            rawdata = AstroLauncher.recvall(s)
            parsedData = AstroLauncher.parseData(rawdata)
            # pprint(parsedData)
            try:
                return [x['playerName'] for x in parsedData['playerInfo'] if x['inGame'] == True]
            except:
                return None

    def deregister_all_server(self):
        servers_registered = (AstroAPI.get_server(
            self.ipPortCombo, self.headers))['data']['Games']
        if (len(servers_registered)) > 0:
            self.logPrint(
                f"Attemping to deregister all ({len(servers_registered)}) servers as {self.ipPortCombo}")
            # pprint(servers_registered)
            for reg_srvr in servers_registered:
                self.logPrint(f"Deregistering {reg_srvr['LobbyID']}..")
                AstroAPI.deregister_server(reg_srvr['LobbyID'], self.headers)
            self.logPrint("All servers deregistered")
            time.sleep(1)
            return [x['LobbyID'] for x in servers_registered]
        return []

    def autoupdate(self):
        url = "https://api.github.com/repos/ricky-davis/AstroLauncher/releases/latest"
        x = (requests.get(url)).json()
        downloadFolder = os.path.dirname(sys.executable)
        for fileObj in x['assets']:
            downloadURL = fileObj['browser_download_url']
            downloadPath = os.path.join(downloadFolder, fileObj['name'])
            downloadCMD = ["powershell", '-executionpolicy', 'bypass', '-command',
                           'Write-Host "Starting download of latest AstroLauncher.exe..";', 'wait-process', str(
                               os.getpid()), ';',
                           'Invoke-WebRequest', downloadURL, "-OutFile", downloadPath,
                           ';', 'Start-Process', '-NoNewWindow', downloadPath]
            print(' '.join(downloadCMD))
            subprocess.Popen(downloadCMD, shell=True, creationflags=subprocess.DETACHED_PROCESS |
                             subprocess.CREATE_NEW_PROCESS_GROUP)
        time.sleep(2)
        self.kill_server("Auto-Update")

    @staticmethod
    def check_for_update():
        url = "https://api.github.com/repos/ricky-davis/AstroLauncher/releases/latest"

        x = (requests.get(url)).json()
        return x['tag_name']

    @staticmethod
    @contextmanager
    def session_scope(consolePort: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.settimeout(5)
            s.connect(("127.0.0.1", int(consolePort)))
            yield s
        except:
            raise
        finally:
            s.close()

    @staticmethod
    def recvall(sock):
        try:
            BUFF_SIZE = 4096  # 4 KiB
            data = b''
            while True:
                part = sock.recv(BUFF_SIZE)
                data += part
                if len(part) < BUFF_SIZE:
                    # either 0 or end of data
                    break
            return data
        except ConnectionResetError:
            return None

    @staticmethod
    def parseData(rawdata):
        try:
            data = json.loads(rawdata.decode('utf8'))
            return data
        except:
            return rawdata


def watchDog(laucherPID, consolePID):
    while(psutil.pid_exists(int(laucherPID)) and psutil.pid_exists(int(consolePID))):
        time.sleep(0.5)
    try:
        for child in psutil.Process(int(consolePID)).children():
            os.kill(child.pid, signal.CTRL_C_EVENT)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-p", "--path", help="Set the server folder path", type=str.lower)
        parser.add_argument("-d", "--daemon", dest="daemon",
                            help="Set the launcher to run as a Daemon", action='store_true')
        parser.add_argument("-U", "--noupdate", dest="noautoupdate",
                            help="Disable autoupdate if running as exe", action='store_true')

        parser.add_argument(
            "-c", "--consolepid", help="Set the consolePID for the Daemon", type=str.lower)
        parser.add_argument(
            "-l", "--launcherpid", help="Set the launcherPID for the Daemon", type=str.lower)
        args = parser.parse_args()
        if args.daemon:
            if args.consolepid and args.launcherpid:
                kernel32 = ctypes.WinDLL('kernel32')
                user32 = ctypes.WinDLL('user32')
                SW_HIDE = 0
                hWnd = kernel32.GetConsoleWindow()
                if hWnd:
                    user32.ShowWindow(hWnd, SW_HIDE)
                watchDog(args.launcherpid, args.consolepid)
            else:
                print("Insufficient launch options!")
        elif args.path:
            AstroLauncher(args.path, disable_auto_update=args.noautoupdate)
        else:
            AstroLauncher(os.getcwd(), disable_auto_update=args.noautoupdate)
    except KeyboardInterrupt:
        pass
