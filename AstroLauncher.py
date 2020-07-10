import argparse
import asyncio
import atexit
import ctypes
import dataclasses
import os
import shutil
import subprocess
import sys
import time
from threading import Thread

import psutil
import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import cogs.AstroAPI as AstroAPI
import cogs.AstroWebServer as AstroWebServer
import cogs.ValidateSettings as ValidateSettings
from cogs.AstroDaemon import AstroDaemon
from cogs.AstroDedicatedServer import AstroDedicatedServer
from cogs.AstroLogging import AstroLogging
from cogs.MultiConfig import MultiConfig


"""
Build:
pyinstaller AstroLauncher.py -F --add-data "assets;./assets" --icon=assets/astrolauncherlogo.ico
or
python BuildEXE.py
"""


class AstroLauncher():
    """ Starts a new instance of the Server Launcher"""

    @dataclasses.dataclass
    class LauncherConfig():
        DisableAutoUpdate: bool = False
        UpdateOnServerRestart: bool = True
        HideServerConsoleWindow: bool = False
        HideLauncherConsoleWindow: bool = False
        ServerStatusFrequency: float = 2
        PlayfabAPIFrequency: float = 2
        DisableBackupRetention: bool = False
        BackupRetentionPeriodHours: float = 72
        BackupRetentionFolderLocation: str = r"Astro\Saved\Backup\LauncherBackups"
        EnableAutoRestart: bool = False
        AutoRestartEveryHours: float = 24
        AutoRestartSyncTimestamp: str = "00:00"
        DisableNetworkCheck: bool = False
        OverwritePublicIP: bool = False
        ShowServerFPSInConsole: bool = True

        DisableWebServer: bool = False
        WebServerPort: int = 5000
        WebServerPasswordHash: str = ""

        EnableWebServerSSL: bool = False
        SSLPort: int = 443
        SSLCertFile: str = ""
        SSLKeyFile: str = ""

        CPUAffinity: str = ""

        def __post_init__(self):
            # pylint: disable=no-member
            hasError = False
            for field, data in self.__dataclass_fields__.items():
                try:
                    self.__dict__[field] = data.type(self.__dict__[field])
                except ValueError:
                    hasError = True
                    AstroLogging.logPrint(
                        f"INI error: {field} must be of type {data.type.__name__}", "critical")
            if hasError:
                AstroLogging.logPrint(
                    "Fix your launcher config file!", "critical")
                sys.exit()

    class SaveHandler(FileSystemEventHandler):
        def __init__(self, launcher):
            self.launcher = launcher
            self.astroPath = self.launcher.astroPath
            self.moveToPath = self.launcher.launcherConfig.BackupRetentionFolderLocation
            super().__init__()

        def on_created(self, event):
            # print(event)
            # time.sleep(1)
            try:
                time.sleep(0.5)
                dirName = os.path.dirname(event.src_path)
                fileNames = [os.path.join(dirName, f) for f in os.listdir(
                    dirName) if os.path.isfile(os.path.join(dirName, f))]
                # print(fileNames)
                fileName = sorted(
                    fileNames, key=os.path.getmtime, reverse=True)[0]
                AstroLogging.logPrint(
                    f"Server saved. {os.path.basename(fileName)}")
            except:
                pass
            # self.launcher.saveObserver.stop()

    class BackupHandler(FileSystemEventHandler):
        def __init__(self, launcher):
            self.launcher = launcher
            self.astroPath = self.launcher.astroPath
            self.moveToPath = self.launcher.launcherConfig.BackupRetentionFolderLocation
            self.retentionPeriodHours = self.launcher.launcherConfig.BackupRetentionPeriodHours
            self.pendingFiles = []
            super().__init__()

        def handle_files(self):
            #print(f"first: {self.pendingFiles}")
            time.sleep(2)
            #print(f"second: {self.pendingFiles}")

            path = os.path.join(self.astroPath, self.moveToPath)
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
            except Exception as e:
                AstroLogging.logPrint(e, "error")
            now = time.time()
            try:
                for f in os.listdir(path):
                    fpath = os.path.join(path, f)
                    if os.stat(fpath).st_mtime < (now - (self.retentionPeriodHours * 60 * 60)):
                        os.remove(fpath)
            except Exception as e:
                AstroLogging.logPrint(e, "error")

            AstroLogging.logPrint("Copying backup(s) to retention folder.")
            # time.sleep(1)
            try:

                dirName = os.path.dirname(self.pendingFiles[0])
                fileNames = [os.path.join(dirName, f) for f in os.listdir(
                    dirName) if os.path.isfile(os.path.join(dirName, f))]
                for cFile in fileNames:
                    # AstroLogging.logPrint(newFile, "debug")
                    # print(cFile)
                    shutil.copy2(cFile, path)
                    # AstroLogging.logPrint(copiedFile, "debug")
            except FileNotFoundError as e:
                AstroLogging.logPrint(e, "error")
            except Exception as e:
                AstroLogging.logPrint(e, "error")

            self.launcher.backupObserver.stop()
            self.launcher.backup_retention()

        def on_modified(self, event):
            # print(event)
            # AstroLogging.logPrint("File in save directory changed")
            try:
                self.pendingFiles.append(event.src_path)
                if len(self.pendingFiles) == 1:
                    t = Thread(target=self.handle_files, args=())
                    t.daemon = True
                    t.start()
            except:
                pass

    def __init__(self, astroPath, launcherINI="Launcher.ini", disable_auto_update=None):
        AstroLogging.setup_logging()

        # check if path specified
        if astroPath is not None:
            if os.path.exists(os.path.join(astroPath, "AstroServer.exe")):
                self.astroPath = astroPath
            else:
                AstroLogging.logPrint(
                    "Specified path does not contain the server executable! (AstroServer.exe)", "critical")
                time.sleep(5)
                return

        # check if executable in current directory
        elif os.path.exists(os.path.join(os.getcwd(), "AstroServer.exe")):
            self.astroPath = os.getcwd()

        # fallback to automatic detection (experimental, do NOT rely on it)
        else:
            try:
                autoPath = AstroAPI.getInstallPath()
                if os.path.exists(os.path.join(autoPath, "AstroServer.exe")):
                    self.astroPath = autoPath
            except:
                AstroLogging.logPrint(
                    "Unable to find server executable anywhere! (AstroServer.exe)", "critical")
                time.sleep(5)
                return

        AstroLogging.setup_loggingPath(self.astroPath)
        self.launcherINI = launcherINI
        self.launcherConfig = self.LauncherConfig()
        self.launcherPath = os.getcwd()
        self.refresh_launcher_config()
        if disable_auto_update is not None:
            self.launcherConfig.DisableAutoUpdate = disable_auto_update
        self.version = "v1.5.3"
        AstroLogging.logPrint(
            f"AstroLauncher - Unofficial Dedicated Server Launcher {self.version}")
        AstroLogging.logPrint(
            "If you encounter any bugs please open a new issue at:")
        AstroLogging.logPrint(
            "https://github.com/ricky-davis/AstroLauncher/issues")
        AstroLogging.logPrint(
            "To safely stop the launcher and server press CTRL+C")
        self.latestURL = "https://github.com/ricky-davis/AstroLauncher/releases/latest"
        self.isExecutable = os.path.samefile(sys.executable, sys.argv[0])
        self.headers = AstroAPI.base_headers
        self.DaemonProcess = None
        self.saveObserver = None
        self.backupObserver = None
        self.hasUpdate = False
        self.affinity = self.launcherConfig.CPUAffinity
        try:
            if self.affinity != "":
                affinityList = [int(x.strip())
                                for x in self.affinity.split(',')]
                p = psutil.Process()
                p.cpu_affinity(affinityList)
        except ValueError as e:
            AstroLogging.logPrint(f"CPU Affinity Error: {e}", "critical")
            AstroLogging.logPrint(
                "Please correct this in your launcher config", "critical")
            return

        self.DedicatedServer = AstroDedicatedServer(
            self.astroPath, self)

        self.check_for_update()

        AstroLogging.logPrint("Starting a new session")

        if not self.launcherConfig.DisableNetworkCheck:
            AstroLogging.logPrint("Checking the network configuration..")
            self.check_network_config()

        self.save_reporting()

        if not self.launcherConfig.DisableBackupRetention:
            self.backup_retention()
            AstroLogging.logPrint("Backup retention started")
        # setup queue for data exchange
        if not self.launcherConfig.DisableWebServer:
            # start http server
            self.webServer = self.start_WebServer()
            # AstroLogging.logPrint(
            #    f"HTTP Server started at 127.0.0.1:{self.launcherConfig.WebServerPort}")

        if self.launcherConfig.HideLauncherConsoleWindow:
            # hide window
            AstroLogging.logPrint(
                "HideLauncherConsoleWindow enabled, Hiding window in 5 seconds...")
            time.sleep(5)
            # pylint: disable=redefined-outer-name
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')

            hWnd = kernel32.GetConsoleWindow()
            user32.ShowWindow(hWnd, 0)

        self.start_server(firstLaunch=True)

    def save_reporting(self):
        if self.saveObserver:
            if not self.saveObserver.is_alive():
                self.saveObserver = None
                self.save_reporting()
        else:
            self.saveObserver = Observer()
            saveGamePath = r"Astro\Saved\SaveGames"
            watchPath = os.path.join(
                self.astroPath, saveGamePath)
            try:
                if not os.path.exists(watchPath):
                    os.makedirs(watchPath)
            except Exception as e:
                AstroLogging.logPrint(e)
            self.saveObserver.schedule(
                self.SaveHandler(self), watchPath)
            self.saveObserver.start()

    def backup_retention(self):
        if self.backupObserver:
            if not self.backupObserver.is_alive():
                self.backupObserver = None
                self.backup_retention()
        else:
            self.backupObserver = Observer()
            backupSaveGamePath = r"Astro\Saved\Backup\SaveGames"
            watchPath = os.path.join(
                self.astroPath, backupSaveGamePath)
            try:
                if not os.path.exists(watchPath):
                    os.makedirs(watchPath)
            except Exception as e:
                AstroLogging.logPrint(e)
            self.backupObserver.daemon = True

            self.backupObserver.schedule(
                self.BackupHandler(self), watchPath)
            self.backupObserver.start()

    def refresh_launcher_config(self, lcfg=None):
        field_names = set(
            f.name for f in dataclasses.fields(self.LauncherConfig))
        cleaned_config = {k: v for k,
                          v in self.get_launcher_config(lcfg).items() if k in field_names}
        self.launcherConfig = dataclasses.replace(
            self.launcherConfig, **cleaned_config)

        config = MultiConfig()
        config.read_dict({"AstroLauncher": cleaned_config})
        with open(self.launcherINI, 'w') as configfile:
            config.write(configfile)

    def overwrite_launcher_config(self, ovrDict):
        ovrConfig = {
            "AstroLauncher": ovrDict
        }
        MultiConfig().overwrite_with(self.launcherINI, ovrConfig)

    def get_launcher_config(self, lfcg=None):
        if not lfcg:
            lfcg = self.LauncherConfig()
        baseConfig = {
            "AstroLauncher": dataclasses.asdict(lfcg)
        }
        config = MultiConfig().baseline(self.launcherINI, baseConfig)
        # print(settings)
        settings = config.getdict()['AstroLauncher']
        return settings

    def check_for_update(self, serverStart=False):
        try:
            url = "https://api.github.com/repos/ricky-davis/AstroLauncher/releases/latest"
            data = ((requests.get(url)).json())
            latestVersion = data['tag_name']
            if latestVersion != self.version:
                self.hasUpdate = latestVersion
                AstroLogging.logPrint(
                    f"UPDATE: There is a newer version of the launcher out! {latestVersion}")
                AstroLogging.logPrint(f"Download it at {self.latestURL}")
                aupdate = not self.launcherConfig.DisableAutoUpdate
                if not self.launcherConfig.UpdateOnServerRestart and serverStart:
                    return

                if self.isExecutable and aupdate:
                    self.autoupdate(data)
        except:
            pass

    def autoupdate(self, data):
        x = data
        downloadFolder = os.path.dirname(sys.executable)
        for fileObj in x['assets']:
            downloadURL = fileObj['browser_download_url']
            fileName = (os.path.splitext(fileObj['name'])[0])
            downloadPath = os.path.join(downloadFolder, fileName)

            downloadCMD = ["powershell", '-executionpolicy', 'bypass', '-command',
                           'Write-Host "Downloading latest AstroLauncher.exe..";', 'wait-process', str(
                               os.getpid()), ';',
                           '[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;',
                           "$ProgressPreference = 'SilentlyContinue';",
                           'Invoke-WebRequest', f"'{downloadURL}'", "-OutFile", f"'{downloadPath + '_new.exe'}'", ';',
                           "Move-Item", "-path", f"'{downloadPath + '_new.exe'}'", "-destination", f"'{downloadPath + '.exe'}'", "-Force;",
                           'Write-Host "Download complete!";',
                           'Start-Process', f"'{downloadPath + '.exe'}'"]
            # print(' '.join(downloadCMD))
            subprocess.Popen(downloadCMD, shell=True,
                             creationflags=subprocess.DETACHED_PROCESS)
        time.sleep(2)
        self.DedicatedServer.kill_server("Auto-Update")

    def start_server(self, firstLaunch=False):
        """
            Starts the Dedicated Server process and waits for it to be registered
        """
        if firstLaunch:
            atexit.register(self.DedicatedServer.kill_server,
                            reason="Launcher shutting down",
                            save=True)
        else:
            self.check_for_update(serverStart=True)
            self.DedicatedServer = AstroDedicatedServer(
                self.astroPath, self)

        self.DedicatedServer.status = "starting"
        self.DedicatedServer.busy = False
        self.headers['X-Authorization'] = AstroAPI.generate_XAUTH(
            self.DedicatedServer.settings.ServerGuid)
        oldLobbyIDs = self.DedicatedServer.deregister_all_server()
        AstroLogging.logPrint("Starting Server process...")
        if self.launcherConfig.EnableAutoRestart:
            AstroLogging.logPrint(
                f"Next restart is at {self.DedicatedServer.nextRestartTime}")
        # time.sleep(5)
        startTime = time.time()
        self.DedicatedServer.start()
        self.DaemonProcess = AstroDaemon.launch(
            executable=self.isExecutable, consolePID=self.DedicatedServer.process.pid)

        # Wait for server to finish registering...
        while not self.DedicatedServer.registered:
            try:
                serverData = (AstroAPI.get_server(
                    self.DedicatedServer.ipPortCombo, self.headers))
                serverData = serverData['data']['Games']
                lobbyIDs = [x['LobbyID'] for x in serverData]
                if len(set(lobbyIDs) - set(oldLobbyIDs)) == 0:
                    time.sleep(self.launcherConfig.PlayfabAPIFrequency)
                else:
                    now = time.time()
                    if now - startTime > 15:
                        self.DedicatedServer.registered = True
                        del oldLobbyIDs
                        self.DedicatedServer.LobbyID = serverData[0]['LobbyID']

                if self.DedicatedServer.process.poll() is not None:
                    AstroLogging.logPrint(
                        "Server was forcefully closed before registration. Exiting....")
                    return False
            except KeyboardInterrupt:
                self.DedicatedServer.kill_server("Launcher shutting down")
            except:
                AstroLogging.logPrint(
                    "Failed to check server. Probably hit rate limit. Backing off and trying again...")
                self.launcherConfig.PlayfabAPIFrequency += 1
                time.sleep(self.launcherConfig.PlayfabAPIFrequency)

        doneTime = time.time()
        elapsed = doneTime - startTime
        AstroLogging.logPrint(
            f"Server ready! Took {round(elapsed,2)} seconds to register.")  # {self.DedicatedServer.LobbyID}
        self.DedicatedServer.status = "ready"
        self.DedicatedServer.server_loop()

    def check_network_config(self):
        networkCorrect = ValidateSettings.test_network(
            self.DedicatedServer.settings.PublicIP, int(self.DedicatedServer.settings.Port), False)
        if networkCorrect:
            AstroLogging.logPrint("Server network configuration good!")
        else:
            AstroLogging.logPrint(
                "I can't seem to validate your network settings..", "warning")
            AstroLogging.logPrint(
                f"Make sure to Port Forward ({self.DedicatedServer.settings.Port} UDP) and enable NAT Loopback", "warning")
            AstroLogging.logPrint(
                "If nobody can connect, Port Forward.", "warning")
            AstroLogging.logPrint(
                "If others are able to connect, but you aren't, enable NAT Loopback.", "warning")

        rconNetworkCorrect = not (ValidateSettings.test_network(
            self.DedicatedServer.settings.PublicIP, int(self.DedicatedServer.settings.ConsolePort), True))
        if rconNetworkCorrect:
            AstroLogging.logPrint("Remote Console network configuration good!")
        else:
            AstroLogging.logPrint(
                f"SECURITY ALERT: Your console port ({self.DedicatedServer.settings.ConsolePort}) is Port Forwarded!", "warning")
            AstroLogging.logPrint(
                "SECURITY ALERT: This allows anybody to control your server.", "warning")
            AstroLogging.logPrint(
                "SECURITY ALERT: Disable this ASAP to prevent issues.", "warning")
            time.sleep(5)

    def start_WebServer(self):
        ws = AstroWebServer.WebServer(self)

        def start_WebServerThread():
            if sys.version_info.minor > 7:
                asyncio.set_event_loop_policy(
                    asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.set_event_loop(asyncio.new_event_loop())
            ws.run()

        t = Thread(target=start_WebServerThread, args=())
        t.daemon = True
        t.start()
        return ws


if __name__ == "__main__":
    try:
        os.system("title AstroLauncher - Unofficial Dedicated Server Launcher")
    except:
        pass
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--daemon", dest="daemon",
                            help="Set the launcher to run as a Daemon", action='store_true')
        parser.add_argument(
            "-c", "--consolepid", help="Set the consolePID for the Daemon", type=str.lower)
        parser.add_argument(
            "-l", "--launcherpid", help="Set the launcherPID for the Daemon", type=str.lower)

        parser.add_argument(
            "-p", "--path", help="Set the server folder path", type=str.lower)
        parser.add_argument("-U", "--noupdate", dest="noautoupdate", default=None,
                            help="Disable autoupdate if running as exe", action='store_true')
        parser.add_argument("-i", "--ini", dest="launcherINI", default="Launcher.ini",
                            help="Set the location of the Launcher INI")

        args = parser.parse_args()
        if args.daemon:
            if args.consolepid and args.launcherpid:
                kernel32 = ctypes.WinDLL('kernel32')
                user32 = ctypes.WinDLL('user32')
                SW_HIDE = 0
                hWnd = kernel32.GetConsoleWindow()
                if hWnd:
                    user32.ShowWindow(hWnd, SW_HIDE)

                AstroDaemon().daemon(args.launcherpid, args.consolepid)
            else:
                print("Insufficient launch options!")
        else:
            AstroLauncher(
                args.path, disable_auto_update=args.noautoupdate, launcherINI=args.launcherINI)
    except KeyboardInterrupt:
        pass
    except Exception as err:
        AstroLogging.logPrint(err, "critical", True)
