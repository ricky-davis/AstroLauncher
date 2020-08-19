

import os
import secrets
import socket
import threading
import time
import uuid
from contextlib import contextmanager

import requests
from IPy import IP

from cogs.AstroLogging import AstroLogging
from cogs.MultiConfig import MultiConfig


def get_public_ip():
    url = "https://api.ipify.org?format=json"
    x = (requests.get(url)).json()
    return x['ip']


def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False


def get_current_settings(launcher, ovrIP=False):
    curPath = launcher.astroPath

    confPath = os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\AstroServerSettings.ini")
    ovrConfig = {
        "/Script/Astro.AstroServerSettings": {
            "VerbosePlayerProperties": "True",
            "HeartbeatInterval": "0"
        }
    }
    try:
        tConfig = MultiConfig().baseline(confPath, {})
        bIP = tConfig.getdict()[
            '/Script/Astro.AstroServerSettings'].get("PublicIP")
        validIP = valid_ip(bIP)
        if validIP and IP(bIP).iptype() != 'PUBLIC':
            validIP = False
            AstroLogging.logPrint(
                "PublicIP field (AstroServerSettings.ini) contained a Private IP!", "warning")
            AstroLogging.logPrint(
                "This will be automatically fixed..", "warning")
    except:
        validIP = False

    try:
        if ovrIP:
            if launcher.launcherConfig.OverwritePublicIP or not validIP:
                ovrConfig["/Script/Astro.AstroServerSettings"]["PublicIP"] = get_public_ip()
    except:
        t = "warning"
        if not validIP:
            t = "error"
        AstroLogging.logPrint("Could not update PublicIP!", t)

    try:
        MultiConfig().overwrite_with(confPath, ovrConfig)

        baseConfig = {
            "/Script/Astro.AstroServerSettings": {
                "bLoadAutoSave": "True",
                "MaxServerFramerate": "30.000000",
                "MaxServerIdleFramerate": "3.000000",
                "bWaitForPlayersBeforeShutdown": "False",
                "PublicIP": "",
                "ServerName": "Astroneer Dedicated Server",
                "MaximumPlayerCount": "12",
                "OwnerName": "",
                "OwnerGuid": "",
                "PlayerActivityTimeout": "0",
                "ServerPassword": "",
                "bDisableServerTravel": "False",
                "DenyUnlistedPlayers": "False",
                "VerbosePlayerProperties": "True",
                "AutoSaveGameInterval": "900",
                "BackupSaveGamesInterval": "7200",
                "ServerGuid": uuid.uuid4().hex,
                "ActiveSaveFileDescriptiveName": "SAVE_1",
                "ServerAdvertisedName": "",
                "ConsolePort": "1234",
                "ConsolePassword": uuid.uuid4().hex,
                "HeartbeatInterval": "0"
            }
        }
        config = MultiConfig().baseline(confPath, baseConfig)

        settings = config.getdict()['/Script/Astro.AstroServerSettings']

        baseConfig = {
            "URL": {
                "Port": "7777"
            },
            "/Script/OnlineSubsystemUtils.IpNetDriver": {
                "MaxClientRate": "1000000",
                "MaxInternetClientRate": "1000000"
            }
        }
        config = MultiConfig().baseline(os.path.join(
            curPath, r"Astro\Saved\Config\WindowsServer\Engine.ini"), baseConfig)
        # print(settings)
        settings.update(config.getdict()['URL'])
        # print(settings)
        return settings
    except:
        AstroLogging.logPrint("Could not retrieve INI settings!", "critical")
        AstroLogging.logPrint(
            "Please ensure everything is correctly formatted...", "critical")
        AstroLogging.logPrint(
            "or delete the INI and allow the launcher to recreate it!", "critical")
        try:
            launcher.DedicatedServer.kill_server()
        except:
            try:
                launcher.kill_launcher()
            except:
                pass


def socket_server(port, secret, tcp):
    try:
        if tcp:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.settimeout(10)
        # bind the socket to a public host,
        # and a well-known port
        serversocket.bind(("0.0.0.0", port))
        # become a server socket
        if tcp:
            serversocket.listen(1)
        while 1:
            # accept connections from outside
            connection = None
            if tcp:
                connection, _client_address = serversocket.accept()
            while True:
                if tcp:
                    data = connection.recv(32)
                else:
                    data = serversocket.recv(32)

                if data == secret:
                    if tcp:
                        connection.close()
                    else:
                        serversocket.close()
                    return True
                else:
                    return False
    except:
        return False


def socket_client(ip, port, secret, tcp):
    try:
        if tcp:
            with session_scope(ip, port) as s:
                s.sendall(secret)
        else:
            time.sleep(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(secret, (ip, port))
    except:
        pass


@contextmanager
def session_scope(ip, consolePort: int):
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, int(consolePort)))
        yield s
    except:
        pass
    finally:
        s.close()


def test_network(ip, port, tcp):
    secretPhrase = secrets.token_hex(16).encode()
    x = threading.Thread(target=socket_client,
                         args=(ip, port, secretPhrase, tcp))
    x.start()
    return socket_server(port, secretPhrase, tcp)
