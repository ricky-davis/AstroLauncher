
import chardet
import configparser
import json
import os
import requests
import time
import uuid


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

    # 2CE7C559471397697B5627AC9FFE7A89
    baseConfig = {
        "URL": {
            "port": "8777"
        }
    }
    config = make_config_baseline(os.path.join(
        curPath, r"Astro\Saved\Config\WindowsServer\Engine.ini"), baseConfig)

    settings.update(config._sections['URL'])

    return settings


if __name__ == "__main__":
    get_current_settings(r"path")
