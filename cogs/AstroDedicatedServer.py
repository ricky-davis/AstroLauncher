
import dataclasses
import datetime
import glob
import json
import math
import ntpath
import os
import subprocess
import time

import pathvalidate
import psutil
from PyPAKParser import PakParser

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
        ConsolePassword: str = None
        ExitSemaphore: str = None
        HeartbeatInterval: str = None
        PlayerProperties: list = dataclasses.field(default_factory=list)

    def __init__(self, astroPath, launcher):
        self.astroPath = astroPath
        self.launcher = launcher
        self.settings = self.ServerSettings()
        self.DSServerStats = None
        self.oldServerStats = self.DSServerStats
        self.ipPortCombo = None
        self.process = None
        self.players = {}
        self.pakList = []
        self.stripPlayers = []
        self.onlinePlayers = []
        self.registered = False
        self.serverData = None
        self.lastHeartbeat = None
        self.LobbyID = None
        self.lastXAuth = datetime.datetime.now()
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
        self.DSListGames = ""
        self.busy = False
        self.getPaks()
        self.refresh_settings(ovrIP=True)
        self.AstroRCON = None

    def start_RCON(self):
        rc = AstroRCON(self)
        rc.run()
        return rc

    def refresh_settings(self, ovrIP=False):
        self.settings = dataclasses.replace(
            self.settings, **ValidateSettings.get_current_settings(self.launcher, ovrIP=ovrIP))
        self.ipPortCombo = f'{self.settings.PublicIP}:{self.settings.Port}'

    def start(self):
        if self.launcher.launcherConfig.HideServerConsoleWindow:
            cmd = [ntpath.join(self.astroPath, "AstroServer.exe")]
        else:
            cmd = [ntpath.join(self.astroPath, "AstroServer.exe"), '-log']
        self.process = subprocess.Popen(cmd)

    @staticmethod
    def convert_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    def getPaks(self):
        try:
            pakPath = ntpath.join(self.astroPath, r"Astro\Saved\Paks")
            for f in os.listdir(pakPath):
                try:
                    with open(ntpath.join(pakPath, f), "rb") as pakFile:
                        PP = PakParser(pakFile)
                        mdFile = "metadata.json"
                        md = PP.List(mdFile)
                        if mdFile in md:
                            ppData = PP.Unpack(mdFile).Data.decode()
                            self.pakList.append({ntpath.basename(f): ppData})
                except:
                    pass
        except:
            pass

    def get_save_file_name(self, save):
        saveGamePath = r"Astro\Saved\SaveGames"
        saveGamePath = ntpath.join(
            self.astroPath, saveGamePath)
        fullName = None

        if save['bHasBeenFlaggedAsCreativeModeSave']:
            c = "c"
        else:
            c = ""
        if save['date']:
            date = save['date']
        else:
            date = ""
        saveFileName = (
            glob.glob(saveGamePath + f"/{save['name']}${c}{date}.savegame"))
        if len(saveFileName) > 0:
            fullName = saveFileName[0]
        else:
            saveFileName = (
                glob.glob(saveGamePath + f"/{save['name']}.savegame"))
            if len(saveFileName) > 0:
                fullName = saveFileName[0]
        saveFileName = ntpath.basename(fullName)
        return fullName, saveFileName

    def getSaves(self):
        try:
            if self.AstroRCON is None or not self.AstroRCON.connected:
                return False
            tempSaveGames = {}
            while tempSaveGames == {} and 'activeSaveName' not in tempSaveGames:
                tempSaveGames = self.AstroRCON.DSListGames()
                time.sleep(0.1)
            self.DSListGames = tempSaveGames
            for save in self.DSListGames["gameList"]:
                try:
                    try:
                        sfPath, saveFileName = self.get_save_file_name(save)
                        if saveFileName:
                            save['fileName'] = saveFileName
                        size = AstroDedicatedServer.convert_size(
                            ntpath.getsize(sfPath))
                        save["size"] = size
                    except:
                        pass
                    multipleOfName = False
                    hasDate = False
                    if len([x for x in self.DSListGames["gameList"] if x['name'] == save['name']]) > 1:
                        multipleOfName = True
                        hasDate = save['date'] != ""

                    save['loadable'] = (
                        (multipleOfName and hasDate) or not multipleOfName)

                    if save['name'] == self.DSListGames['activeSaveName'] and ((multipleOfName and hasDate) or not multipleOfName):
                        save['active'] = "Active"
                    else:
                        save['active'] = ""
                except:
                    pass
        except:
            pass

    def saveGame(self, name=None, shutdown=False):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.setStatus("saving")
        self.busy = "Saving"
        AstroLogging.logPrint("Saving the current game...")
        self.AstroRCON.DSSaveGame(name)
        time.sleep(0.5)
        if not shutdown:
            self.getSaves()
        self.busy = False

    def newSaveGame(self):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.setStatus("newsave")
        self.busy = "NewSave"
        # time.sleep(1)
        AstroLogging.logPrint("Starting a new savegame...")
        self.AstroRCON.DSNewGame()
        self.AstroRCON.DSSaveGame()
        self.getSaves()
        self.busy = False

    def loadSaveGame(self, saveData):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.setStatus("loadsave")
        self.busy = "LoadSave"
        name = saveData['name']
        if pathvalidate.is_valid_filename(name):
            # time.sleep(1)
            AstroLogging.logPrint(f"Loading save: {name}")
            self.AstroRCON.DSLoadGame(name)
        self.getSaves()
        self.busy = False

    def deleteSaveGame(self, saveData):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        name = saveData['name']
        if pathvalidate.is_valid_filename(name):
            self.setStatus("delsave")
            self.busy = "DelSave"
            saveGamePath = r"Astro\Saved\SaveGames"
            AstroLogging.logPrint(f"Deleting save: {saveData['fileName']}")
            sfPath = ntpath.join(
                self.astroPath, saveGamePath, saveData['fileName'])
            if ntpath.exists(sfPath):
                os.remove(sfPath)
        self.getSaves()
        self.busy = False

    def renameSaveGame(self, oldSave, newName):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.setStatus("renamesave")
        self.busy = "RenameSave"
        if pathvalidate.is_valid_filename(oldSave['name']) and pathvalidate.is_valid_filename(newName):
            saveGamePath = r"Astro\Saved\SaveGames"
            saveGamePath = ntpath.join(self.astroPath, saveGamePath)
            AstroLogging.logPrint(
                f"Renaming save: {oldSave['name']} to {newName}")
            if oldSave['active']:
                self.saveGame(newName)
                sfPath = ntpath.join(saveGamePath, oldSave['fileName'])
                self.getSaves()
                newSave = [x for x in self.DSListGames['gameList']
                           if x['name'] == newName]
                if newSave:
                    newSave = newSave[0]
                    sfNPath = ntpath.join(saveGamePath, newSave['fileName'])
                    if ntpath.exists(sfNPath) and ntpath.exists(sfPath):
                        os.remove(sfPath)
            else:
                saveFileName = oldSave['fileName']
                sfPath = ntpath.join(saveGamePath, saveFileName)
                newSaveFileName = saveFileName.replace(
                    oldSave['name'], newName)
                sfNPath = ntpath.join(saveGamePath, newSaveFileName)
                # time.sleep(1)
                if ntpath.exists(sfPath) and not ntpath.exists(sfNPath):
                    os.rename(sfPath, sfNPath)

        self.getSaves()
        self.busy = False

    def shutdownServer(self):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.setStatus("shutdown")
        self.busy = "Shutdown"
        # time.sleep(1)
        self.AstroRCON.DSServerShutdown()
        self.DSServerStats = None
        AstroLogging.logPrint("Server shutdown.", ovrDWHL=True)

    def save_and_shutdown(self):
        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        self.saveGame(shutdown=True)
        self.busy = "S&Shutdown"
        self.shutdownServer()

    def setStatus(self, status):
        try:
            self.status = status
        except:
            pass

    def quickToggleWhitelist(self):
        '''Toggling the whitelist is good for forcing the server to put every player who has joined the current save's Guid into the INI'''

        if self.AstroRCON is None or not self.AstroRCON.connected:
            return False
        wLOn = self.settings.DenyUnlistedPlayers
        self.AstroRCON.DSSetDenyUnlisted(not wLOn)
        self.AstroRCON.DSSetDenyUnlisted(wLOn)
        self.refresh_settings()

    def getXauth(self):
        if self.lastXAuth is None or (datetime.datetime.now() - self.lastXAuth).total_seconds() > 3600:
            try:
                gxAuth = None
                while gxAuth is None:
                    try:
                        AstroLogging.logPrint(
                            "Generating new xAuth...", "debug")
                        gxAuth = AstroAPI.generate_XAUTH(
                            self.settings.ServerGuid)
                    except:
                        time.sleep(10)
                self.launcher.headers['X-Authorization'] = gxAuth
                self.lastXAuth = datetime.datetime.now()
            except:
                self.lastXAuth += datetime.timedelta(seconds=20)

    def server_loop(self):
        # AstroLogging.logPrint("Starting server_loop: 2", "debug")
        while True:
            # Ensure RCON is connected
            try:
                if not self.AstroRCON or not self.AstroRCON.connected:
                    self.AstroRCON = self.start_RCON()
                    self.quickToggleWhitelist()
            except:
                pass
            while not self.AstroRCON.connected:
                # AstroLogging.logPrint("Waiting on AstroRCON to connect", "debug")
                time.sleep(0.1)
            ###########################

            # AstroLogging.logPrint("Running through another loop...", "debug")
            now = datetime.datetime.now()

            if not self.launcher.launcherConfig.DisableBackupRetention:
                self.launcher.backup_retention()

            # AstroLogging.logPrint("Server_loop section: 1", "debug")
            self.launcher.save_reporting()

            # AstroLogging.logPrint("Server_loop section: 2", "debug")
            if self.launcher.launcherConfig.EnableAutoRestart:
                if (((now - self.lastRestart).total_seconds() > 60) and ((self.nextRestartTime - now).total_seconds() < 0)):
                    AstroLogging.logPrint(
                        "Preparing to shutdown the server.")
                    self.lastRestart = now
                    self.nextRestartTime += datetime.timedelta(
                        hours=self.launcher.launcherConfig.AutoRestartEveryHours)
                    self.save_and_shutdown()

            # AstroLogging.logPrint("Server_loop section: 3", "debug")
            if self.process.poll() is not None:
                AstroLogging.logPrint(
                    "Server was closed. Restarting..")
                return self.launcher.start_server()

            # AstroLogging.logPrint("Server_loop section: 4", "debug")
            self.getXauth()

            # AstroLogging.logPrint("Server_loop section: 5", "debug")
            # AstroLogging.logPrint(f"self.lastHeartbeat: {self.lastHeartbeat}", "debug")
            # try:
            #     AstroLogging.logPrint(f"total_seconds: {(now - self.lastHeartbeat).total_seconds()}", "debug")
            # except:
            #     pass
            if self.lastHeartbeat is None or (now - self.lastHeartbeat).total_seconds() > 30:

                try:
                    needs_update, latest_version = self.launcher.check_for_server_update(
                        serverStart=True, check_only=True)

                    if needs_update and self.launcher.launcherConfig.AutoUpdateServerSoftware:
                        self.save_and_shutdown()
                        self.launcher.update_server(latest_version)
                        continue
                except:
                    pass

                serverData = []
                try:

                    AstroLogging.logPrint(
                        "Getting Server data for Heartbeat", "debug")
                    serverData = (AstroAPI.get_server(
                        self.ipPortCombo, self.launcher.headers))['data']['Games']
                    if len(serverData) > 0:
                        self.serverData = serverData[0]
                except:
                    pass
                hbServerName = {"customdata": {
                    "ServerName": self.settings.ServerName,
                    "ServerType": ("AstroLauncherEXE" if self.launcher.isExecutable else "AstroLauncherPy") + f" {self.launcher.version}",
                    "ServerPaks": self.pakList
                }}

                AstroLogging.logPrint("Attempting Heartbeat...", "debug")
                hbStatus = AstroAPI.heartbeat_server(
                    self.serverData, self.launcher.headers, {"serverName": json.dumps(hbServerName)})

                hbTryCount = 1
                while hbStatus['status'] != "OK":
                    hbrs = self.launcher.launcherConfig.HeartBeatFailRestartServer
                    if hbrs != 0 and hbTryCount > hbrs:
                        self.kill_server(
                            reason="Server was unable to heartbeat, restarting...",
                            save=True, killLauncher=False)
                        time.sleep(5)
                        return self.launcher.start_server()
                    if hbTryCount > 1:
                        time.sleep(5*hbTryCount)
                    self.getXauth()
                    try:
                        hbStatus = AstroAPI.heartbeat_server(
                            self.serverData, self.launcher.headers, {"serverName": json.dumps(hbServerName)})
                        AstroLogging.logPrint(
                            f"hbStatus: {hbStatus}", "debug")
                        if 'status' in hbStatus and hbStatus['status'] == "Error":
                            raise "HeartBeatError"

                    except:
                        AstroLogging.logPrint(
                            f"Failed to heartbeat server on attempt: {hbTryCount}", msgType="warning")
                    hbTryCount += 1

                if hbTryCount > 1:
                    AstroLogging.logPrint(
                        "Connection reestablished! Successful heartbeat!")

                self.lastHeartbeat = datetime.datetime.now()

            # AstroLogging.logPrint("Server_loop section: 6", "debug")
            if self.launcher.webServer is not None:
                self.setStatus("ready")
                self.busy = "getSavesInLoop"
                self.getSaves()
                self.busy = False

            # AstroLogging.logPrint("Server_loop section: 7", "debug")
            self.setStatus("ready")
            serverStats = self.AstroRCON.DSServerStatistics()
            if serverStats is not None and 'averageFPS' in serverStats:
                self.DSServerStats = serverStats
                if self.launcher.launcherConfig.ShowServerFPSInConsole:
                    FPSJumpRate = (
                        float(self.settings.MaxServerFramerate) / 5)
                    if self.oldServerStats is None or (abs(float(self.DSServerStats['averageFPS']) - float(self.oldServerStats['averageFPS'])) > FPSJumpRate):
                        AstroLogging.logPrint(
                            f"Server FPS: {round(self.DSServerStats['averageFPS'])}")
                self.oldServerStats = self.DSServerStats

            # AstroLogging.logPrint("Server_loop section: 8", "debug")
            self.setStatus("ready")
            playerList = self.AstroRCON.DSListPlayers()
            if playerList is not None and 'playerInfo' in playerList:
                self.players = playerList
                curPlayers = [
                    x for x in self.players['playerInfo'] if x['inGame']]
                curPIDList = [x['playerGuid'] for x in curPlayers]
                onlinePIDList = [x['playerGuid'] for x in self.onlinePlayers]

                if len(curPlayers) > len(self.onlinePlayers):
                    playerDif = list(set(curPIDList) - set(onlinePIDList))
                    AstroLogging.logPrint(
                        f"P. Joining - OnlinePlayers: {onlinePIDList}", "debug")
                    AstroLogging.logPrint(
                        f"P. Joining - CurPlayers: {curPIDList}", "debug")
                    AstroLogging.logPrint(
                        f"P. Joining - dif: {playerDif}", "debug")
                    if len(playerDif) > 0:
                        playerDif = playerDif[0]
                        self.onlinePlayers = curPlayers
                        if playerDif in self.stripPlayers:
                            self.stripPlayers.remove(playerDif)

                        difName = [x for x in self.players['playerInfo']
                                   if x['playerGuid'] == playerDif][0]["playerName"]

                        AstroLogging.logPrint(
                            f"Player joining: {difName}", ovrDWHL=True, dwet="j")

                        # Add player to INI with Unlisted category if not exists or is Pending
                        pp = list(self.settings.PlayerProperties)
                        if len([x for x in pp if playerDif in x and "PlayerCategory=Pending" not in x]) == 0:
                            self.AstroRCON.DSSetPlayerCategoryForPlayerName(
                                playerDif, "Unlisted")
                            self.refresh_settings()

                elif len(curPlayers) < len(self.onlinePlayers):
                    playerDif = list(set(onlinePIDList) - set(curPIDList))
                    AstroLogging.logPrint(
                        f"P. Leaving - OnlinePlayers: {onlinePIDList}", "debug")
                    AstroLogging.logPrint(
                        f"P. Leaving - CurPlayers: {curPIDList}", "debug")
                    AstroLogging.logPrint(
                        f"P. Leaving - dif: {playerDif}", "debug")
                    if len(playerDif) > 0:
                        playerDif = playerDif[0]
                        self.onlinePlayers = curPlayers

                        difName = [x for x in self.players['playerInfo']
                                   if x['playerGuid'] == playerDif][0]["playerName"]
                        AstroLogging.logPrint(
                            f"Player left: {difName}", ovrDWHL=True, dwet="l")

                self.players['playerInfo'] = [
                    x for x in playerList['playerInfo'] if x['playerGuid'] not in self.stripPlayers]

            # AstroLogging.logPrint("Server_loop section: 9", "debug")
            time.sleep(
                self.launcher.launcherConfig.ServerStatusFrequency)

    def deregister_all_server(self):
        servers_registered = (AstroAPI.get_server(
            self.ipPortCombo, self.launcher.headers))['data']['Games']

        self.registered = False
        if (len(servers_registered)) > 0:
            AstroLogging.logPrint(
                f"Attemping to deregister all ({len(servers_registered)}) servers matching self")
            # pprint(servers_registered)
            for counter, reg_srvr in enumerate(servers_registered):
                # reg_srvr['LobbyID']
                AstroLogging.logPrint(
                    f"Deregistering {counter+1}/{len(servers_registered)}...")
                drg_status = AstroAPI.deregister_server(
                    reg_srvr['LobbyID'], self.launcher.headers)
                if 'status' in drg_status and drg_status['status'] == "Error":
                    AstroLogging.logPrint(
                        "Trouble deregistering server. Multiple servers may still be registered.", msgType="warning")
            AstroLogging.logPrint("All servers deregistered")
            time.sleep(1)
            return [x['LobbyID'] for x in servers_registered]
        return []

    def kill_server(self, reason, save=False, killLauncher=True):
        AstroLogging.logPrint(f"Kill Server: {reason}")
        try:
            self.busy = "Kill"
            self.setStatus("shutdown")
        except:
            pass
        try:
            if save:
                self.AstroRCON.lock = False
                self.shutdownServer()
                time.sleep(1)
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
        try:
            self.setStatus("off")
        except:
            pass
        # Kill current process
        try:
            if killLauncher:
                os.kill(os.getpid(), 9)
        except:
            pass
