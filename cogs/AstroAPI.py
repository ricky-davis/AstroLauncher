
import os
import re
import winreg

import requests

base_headers = {'Content-Type': 'application/json; charset=utf-8',
                'X-PlayFabSDK': 'UE4MKPL-1.19.190610',
                'User-Agent': 'game=Astro, engine=UE4, version=4.18.2-0+++UE4+Release-4.18, platform=Windows, osver=6.2.9200.1.256.64bit'
                }


def generate_XAUTH(serverGUID):
    url = "https://5EA1.playfabapi.com/Client/LoginWithCustomID?sdk=UE4MKPL-1.19.190610"
    requestObj = {
        "CreateAccount": True,
        "CustomId": serverGUID,
        "TitleId": "5EA1"
    }
    x = (requests.post(url, headers=base_headers, json=requestObj)).json()
    return x['data']['SessionTicket']


def get_server(ipPortCombo, headers):
    url = 'https://5EA1.playfabapi.com/Client/GetCurrentGames?sdk=UE4MKPL-1.19.190610'
    requestObj = {
        "TagFilter": {
            "Includes": [
                {"Data": {"gameId": ipPortCombo}}
            ]
        }
    }
    x = (requests.post(url, headers=headers, json=requestObj)).json()
    return x


def deregister_server(lobbyID, headers):
    url = 'https://5EA1.playfabapi.com/Client/ExecuteCloudScript?sdk=UE4MKPL-1.19.190610'
    jsonRequest = {
        "FunctionName": "deregisterDedicatedServer",
        "FunctionParameter":
        {
            "lobbyId": lobbyID
        },
        "GeneratePlayStreamEvent": True
    }

    x = (requests.post(url, headers=headers, json=jsonRequest)).json()
    return x


def heartbeat_server(serverData, headers, dataToChange=None):
    url = (
        "https://5EA1.playfabapi.com/Client/ExecuteCloudScript?sdk=UE4MKPL-1.19.190610"
    )
    requestObj = {
        "FunctionName": "heartbeatDedicatedServer",
        "FunctionParameter": {
            "serverName": serverData['Tags']['serverName'],
            "buildVersion": serverData['Tags']['gameBuild'],
            "gameMode": serverData['GameMode'],
            "ipAddress": serverData['ServerIPV4Address'],
            "port": serverData['ServerPort'],
            "matchmakerBuild": serverData['BuildVersion'],
            "maxPlayers": serverData['Tags']['maxPlayers'],
            "numPlayers": str(len(serverData['PlayerUserIds'])),
            "lobbyId": serverData['LobbyID'],
            "publicSigningKey": serverData['Tags']['publicSigningKey'],
            "requiresPassword": serverData['Tags']['requiresPassword']
        },
        "GeneratePlayStreamEvent": True
    }
    if dataToChange is not None:
        requestObj['FunctionParameter'].update(dataToChange)

    x = (requests.post(url, headers=headers, json=requestObj)).json()
    return x


def getInstallPath():

    # query steam install path from registry
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'Software\\Valve\\Steam')
    steamPath = winreg.QueryValueEx(key, "InstallPath")[0]

    with open(os.path.join(steamPath + "/steamapps/libraryfolders.vdf")) as libraryFile:

        # get install directory of games
        lf = libraryFile.read()
        lf = lf.replace("\\\\", "\\")
        # pylint: disable=anomalous-backslash-in-string
        gamePath = re.findall('^\s*"\d*"\s*"([^"]*)"', lf, re.MULTILINE)[0]

        return os.path.join(gamePath, "steamapps", "common", "ASTRONEER Dedicated Server")
