
import chardet
import configparser
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
import collections.abc


def get_public_ip():
    url = "https://api.ipify.org?format=json"
    x = (requests.get(url)).json()
    return x['ip']


def updateDict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = updateDict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def read_config(configPath):
    config = configparser.ConfigParser(strict=False)
    pathname = os.path.dirname(configPath)
    if not os.path.exists(pathname):
        os.makedirs(pathname)
    rawdata = open(configPath, 'ab+').read()
    result = chardet.detect(rawdata)
    charenc = result['encoding']
    config.read(configPath, encoding=charenc)
    return config


def convert_to_dict(config):
    config_dict = defaultdict(dict)
    for section in config.sections():
        for key, value in config.items(section):
            config_dict[section][key] = value

    return config_dict


def make_config_baseline(configPath, baseDict):
    config = read_config(configPath)
    dictConfig = dict(convert_to_dict(config))
    newConfig = updateDict(baseDict, dictConfig)
    config = configparser.ConfigParser(strict=False)
    config.read_dict(newConfig)
    if newConfig != dictConfig:
        with open(configPath, 'w') as configfile:
            config.write(configfile)
    return config


def get_current_settings(curPath):
    baseConfig = {
        "/Script/Astro.AstroServerSettings": {
            "bloadautosave": "True",
            "maxserverframerate": "30.000000",
            "maxserveridleframerate": "3.000000",
            "bwaitforplayersbeforeshutdown": "False",
            "publicip": get_public_ip(),
            "servername": "Astroneer Dedicated Server",
            "maximumplayercount": "12",
            "ownername": "",
            "ownerguid": "",
            "playeractivitytimeout": "0",
            "serverpassword": "",
            "bdisableservertravel": "False",
            "denyunlistedplayers": "False",
            "verboseplayerproperties": "False",
            "autosavegameinterval": "900",
            "backupsavegamesinterval": "7200",
            "serverguid": uuid.uuid4().hex,
            "activesavefiledescriptivename": "SAVE_1",
            "serveradvertisedname": "",
            "consoleport": "1234"
        }
    }
    config = make_config_baseline(os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\AstroServerSettings.ini"), baseConfig)

    settings = config._sections['/Script/Astro.AstroServerSettings']

    baseConfig = {
        "URL": {
            "port": "8777"
        }
    }
    config = make_config_baseline(os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\Engine.ini"), baseConfig)

    settings.update(config._sections['URL'])

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


@contextmanager
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
