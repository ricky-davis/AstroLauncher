
import chardet
import json
import os
import requests
import secrets
import socket
import threading
import time
import uuid

from contextlib import contextmanager
from collections import OrderedDict, defaultdict
from pprint import pprint


def get_public_ip():
    url = "https://api.ipify.org?format=json"
    x = (requests.get(url)).json()
    return x['ip']


class CustomConfig(defaultdict):
    """ Apparently nobody has a use-case for an ini file with duplicate keys, go figure. Somebody please make this better.
    """

    def getdict(self):
        return self.__dict__

    def read_dict(self, configDict):
        self.__dict__ = configDict

    def read(self, configPath):
        encoding = CustomConfig.get_encoding(configPath)
        with open(configPath, "r", encoding=encoding) as f:
            lines = [l.strip() for l in f.read().split("\n")]
            section = None
            properties = [x.split("=", 1) for x in lines]
            for p in properties:
                key = p[0].strip()
                if isinstance(p, list) and len(p) > 1:
                    value = p[1].strip()
                    if key in self.__dict__[section]:
                        if isinstance(self.__dict__[section][key], str):
                            self.__dict__[section][key] = [
                                self.__dict__[section][key], value]
                        else:
                            self.__dict__[section][key].append(value)
                    else:
                        self.__dict__[section][key] = value
                else:
                    if len(key) > 0:
                        section = key[1: len(key)-1]
                        self.__dict__[section] = {}

    def write(self, configFile):
        for section in self.__dict__.keys():
            configFile.write(f"[{section}]\n")
            properties = self.__dict__[section]
            for p, v in properties.items():
                if isinstance(v, list):
                    for item in v:
                        configFile.write(f"{p}={item}\n")
                else:
                    configFile.write(f"{p}={v}\n")

    @staticmethod
    def get_encoding(filePath):
        pathname = os.path.dirname(filePath)
        if not os.path.exists(pathname):
            os.makedirs(pathname)
        with open(filePath, 'a+'):
            pass
        rawdata = open(filePath, 'rb').read()
        result = chardet.detect(rawdata)
        charenc = result['encoding']
        return charenc

    @staticmethod
    def updateTo(baseDict, updateWithDict):
        tDict = {}
        for key, value in baseDict.items():
            tDict[key] = value
            if key in updateWithDict.keys():
                if isinstance(value, dict):
                    tDict[key] = CustomConfig.updateTo(
                        value, updateWithDict[key])
                else:
                    tDict[key] = updateWithDict[key]

        tDict.update({k: v for k, v in updateWithDict.items()
                      if k not in tDict.keys()})
        return tDict


def make_config_baseline(configPath, baseDict):
    config = CustomConfig()
    config.read(configPath)
    baseConfig = CustomConfig()
    baseConfig.read_dict(baseDict)
    newConfig = CustomConfig()
    newConfig.read_dict(CustomConfig.updateTo(
        baseConfig.getdict(), config.getdict()))
    with open(configPath, 'w') as configfile:
        newConfig.write(configfile)
    return newConfig.getdict()


def get_current_settings(curPath):
    baseConfig = {
        "/Script/Astro.AstroServerSettings": {
            "bLoadAutoSave": "True",
            "MaxServerFramerate": "30.000000",
            "MaxServerIdleFramerate": "3.000000",
            "bWaitForPlayersBeforeShutdown": "False",
            "PublicIP": get_public_ip(),
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
            "ConsolePort": "1234"
        }
    }
    config = make_config_baseline(os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\AstroServerSettings.ini"), baseConfig)

    settings = config['/Script/Astro.AstroServerSettings']

    baseConfig = {
        "URL": {
            "Port": "8777"
        }
    }
    config = make_config_baseline(os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\Engine.ini"), baseConfig)
    # print(settings)
    settings.update(config['URL'])
    # print(settings)
    return settings


def socket_server(port, secret):
    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.settimeout(5)
        # bind the socket to a public host,
        # and a well-known port
        serversocket.bind((socket.gethostname(), port))
        # become a server socket
        serversocket.listen(1)
        while 1:
            # accept connections from outside
            connection, client_address = serversocket.accept()
            while True:
                data = connection.recv(32)
                # print(data)
                if data == secret:
                    connection.close()
                    return True
                else:
                    return False
    except:
        return False


def socket_client(ip, port, secret):
    try:
        with session_scope(ip, port) as s:
            s.sendall(secret)
    except:
        pass


@ contextmanager
def session_scope(ip, consolePort: int):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, int(consolePort)))
        yield s
    except:
        pass
    finally:
        s.close()


def test_network(ip, port):
    secretPhrase = secrets.token_hex(16).encode()
    x = threading.Thread(target=socket_client, args=(ip, port, secretPhrase))
    x.start()
    return socket_server(port, secretPhrase)
