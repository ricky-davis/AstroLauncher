import dataclasses
import datetime
import os
import subprocess
import time

import psutil

import cogs.AstroAPI as AstroAPI
import cogs.ValidateSettings as ValidateSettings
from cogs.AstroLogging import AstroLogging
from cogs.AstroRCON import AstroRCON


class AstroDedicatedServer():
    """
        The Dedicated Server Class.
    """
    @dataclasses.dataclass
    class ServerSettings():
        PublicIP: str = None
        Port: str = None
        ServerName: str = None
        ServerPassword: str = None
        MaximumPlayerCount: str = None
        OwnerName: str = None
        OwnerGuid: str = None
        PlayerActivityTimeout: str = None
        bDisableServerTravel: str = None
        DenyUnlistedPlayers: str = None
        VerbosePlayerProperties: str = None
        AutoSaveGameInterval: str = None
        BackupSaveGamesInterval: str = None
        ActiveSaveFileDescriptiveName: str = None
        ServerGuid: str = None
        ServerAdvertisedName: str = None
        bLoadAutoSave: str = None
        MaxServerFramerate: str = None
        MaxServerIdleFramerate: str = None
        bWaitForPlayersBeforeShutdown: str = None
        ConsolePort: str = None
        ExitSemaphore: str = None
        HeartbeatInterval: str = None
        PlayerProperties: list = None

    def __init__(self, astroPath, launcher):
        self.astroPath = astroPath
        self.launcher = launcher
        self.settings = self.ServerSettings()
        self.ipPortCombo = None
        self.process = None
        self.players = {}
        self.onlinePlayers = []
        self.registered = False
        self.LobbyID = None
        self.serverGUID = self.settings.ServerGuid if self.settings.ServerGuid != '' else "REGISTER"
        if self.launcher.launcherConfig.EnableAutoRestart:
            self.syncRestartTime = self.launcher.launcherConfig.AutoRestartSyncTimestamp
            self.nextRestartTime = None
            self.lastRestart = datetime.datetime.now()

            if self.syncRestartTime != "False":
                if self.syncRestartTime == "midnight":
                    self.syncRestartTime = "00:00"
                dt = datetime.datetime.today()
                timestamp = datetime.datetime.strptime(
                    self.syncRestartTime, '%H:%M')
                restartTime = datetime.datetime.combine(dt, datetime.datetime.min.time())+datetime.timedelta(
                    hours=timestamp.hour, minutes=timestamp.minute)
                RestartCooldown = bool(
                    (dt - restartTime).total_seconds() < 300 and (dt - restartTime).total_seconds() > -300)
                if timestamp.hour == 0 and ((dt - restartTime).total_seconds()/60/60) > self.launcher.launcherConfig.AutoRestartEveryHours:
                    restartTime += datetime.timedelta(days=1)
                if dt > restartTime or RestartCooldown:
                    restartTime += \
                        datetime.timedelta(
                            hours=self.launcher.launcherConfig.AutoRestartEveryHours)
                    while dt >= restartTime:
                        restartTime += \
                            datetime.timedelta(
                                hours=self.launcher.launcherConfig.AutoRestartEveryHours)
                self.nextRestartTime = restartTime
            else:
                self.nextRestartTime = self.lastRestart + \
                    datetime.timedelta(
                        hours=self.launcher.launcherConfig.AutoRestartEveryHours)
        self.status = "off"
        self.busy = False
        self.refresh_settings()

    def refresh_settings(self):
        self.settings = dataclasses.replace(
            self.settings, **ValidateSettings.get_current_settings(self.astroPath))
        self.ipPortCombo = f'{self.settings.PublicIP}:{self.settings.Port}'

    def start(self):
        cmd = [os.path.join(self.astroPath, "AstroServer.exe"), '-log']
        self.process = subprocess.Popen(cmd)

    def saveGame(self):
        self.setStatus("saving")
        self.busy = True
        time.sleep(1)
        AstroLogging.logPrint("Saving the current game...")
        AstroRCON.DSSaveGame(self.settings.ConsolePort)
        self.busy = False

    def shutdownServer(self):
        self.setStatus("shutdown")
        self.busy = True
        time.sleep(1)
        AstroRCON.DSServerShutdown(self.settings.ConsolePort)
        AstroLogging.logPrint("Server shutdown.")

    def save_and_shutdown(self):
        self.saveGame()
        self.busy = True
        self.shutdownServer()

    def setStatus(self, status):
        self.status = status
        self.update_webServerQueue()

    def update_webServerQueue(self):
        if not self.launcher.launcherConfig.DisableWebServer:
            # update data(self) in queue for webserver
            self.launcher.webServerQueue.get()
            self.launcher.webServerQueue.put(self)

    def server_loop(self):
        while True:
            if not self.launcher.launcherConfig.DisableBackupRetention:
                self.launcher.backup_retention()

            self.launcher.save_reporting()
            if self.launcher.launcherConfig.EnableAutoRestart:
                if (((datetime.datetime.now() - self.lastRestart).total_seconds() > 60) and ((self.nextRestartTime - datetime.datetime.now()).total_seconds() < 0)):
                    AstroLogging.logPrint("Preparing to shutdown the server.")
                    self.lastRestart = datetime.datetime.now()
                    self.nextRestartTime += datetime.timedelta(
                        hours=self.launcher.launcherConfig.AutoRestartEveryHours)
                    self.save_and_shutdown()

            if self.process.poll() is not None:
                AstroLogging.logPrint("Server was closed. Restarting..")
                return self.launcher.start_server()
            if not self.busy:
                self.setStatus("ready")

            playerList = AstroRCON.DSListPlayers(self.settings.ConsolePort)
            if playerList is not None:
                self.players = playerList
                curPlayers = [x['playerName']
                              for x in self.players['playerInfo'] if x['inGame']]

                if len(curPlayers) > len(self.onlinePlayers):
                    playerDif = list(set(curPlayers) -
                                     set(self.onlinePlayers))[0]
                    self.onlinePlayers = curPlayers
                    AstroLogging.logPrint(f"Player joining: {playerDif}")
                elif len(curPlayers) < len(self.onlinePlayers):
                    playerDif = list(
                        set(self.onlinePlayers) - set(curPlayers))[0]
                    self.onlinePlayers = curPlayers
                    AstroLogging.logPrint(f"Player left: {playerDif}")
            self.update_webServerQueue()
            time.sleep(self.launcher.launcherConfig.ServerStatusFrequency)

    def deregister_all_server(self):
        servers_registered = (AstroAPI.get_server(
            self.ipPortCombo, self.launcher.headers))['data']['Games']

        self.registered = False
        if (len(servers_registered)) > 0:
            AstroLogging.logPrint(
                f"Attemping to deregister all ({len(servers_registered)}) servers as {self.ipPortCombo}")
            # pprint(servers_registered)
            for reg_srvr in servers_registered:
                AstroLogging.logPrint(f"Deregistering {reg_srvr['LobbyID']}..")
                AstroAPI.deregister_server(
                    reg_srvr['LobbyID'], self.launcher.headers)
            AstroLogging.logPrint("All servers deregistered")
            time.sleep(1)
            return [x['LobbyID'] for x in servers_registered]
        return []

    def kill_server(self, reason, save=False):
        AstroLogging.logPrint(f"Kill Server: {reason}")
        self.busy = True
        self.setStatus("shutdown")
        try:
            if save:
                self.saveGame()
                time.sleep(1)
                self.shutdownServer()
        except:
            pass
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
        self.setStatus("off")
        # Kill current process
        try:
            os.kill(os.getpid(), 9)
        except:
            pass
