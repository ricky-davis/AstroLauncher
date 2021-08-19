import json
import time

from cogs.AstroLogging import AstroLogging
from cogs.utils import AstroRequests

base_headers = {'Content-Type': 'application/json; charset=utf-8',
                "X-PlayFabSDK": "UE4MKPL-1.49.201027",
                "User-Agent": "Astro/++UE4+Release-4.23-CL-0 Windows/10.0.19042.1.256.64bit",
                }
# pylint: disable=no-member


def generate_XAUTH(serverGUID):
    url = f"https://5EA1.playfabapi.com/Client/LoginWithCustomID?sdk={base_headers['X-PlayFabSDK']}"
    requestObj = {
        "CreateAccount": False,
        "CustomId": serverGUID,
        "TitleId": "5EA1"
    }
    AstroLogging.logPrint(requestObj, "debug")
    x = json.load(AstroRequests.post(
        url, headers=base_headers, jsonD=requestObj))

    if x['code'] == 400 and x['error'] == "AccountNotFound":
        time.sleep(0.2)
        requestObj["CreateAccount"] = True
        x = json.load(AstroRequests.post(
            url, headers=base_headers, jsonD=requestObj))
    AstroLogging.logPrint(x, "debug")
    return x['data']['SessionTicket']


def get_server(ipPortCombo, headers):
    try:
        url = f"https://5EA1.playfabapi.com/Client/GetCurrentGames?sdk={base_headers['X-PlayFabSDK']}"
        requestObj = {
            "TagFilter": {
                "Includes": [
                    {"Data": {"gameId": ipPortCombo}}
                ]
            }
        }
        AstroLogging.logPrint(requestObj, "debug")
        x = json.load(AstroRequests.post(url, headers=headers,
                                         jsonD=requestObj))
        AstroLogging.logPrint(x, "debug")
        return x
    except:
        return {"status": "Error"}


def deregister_server(lobbyID, headers):
    try:
        url = f"https://5EA1.playfabapi.com/Client/ExecuteCloudScript?sdk={base_headers['X-PlayFabSDK']}"
        requestObj = {
            "FunctionName": "deregisterDedicatedServer",
            "FunctionParameter":
            {
                "lobbyId": lobbyID
            },
            "GeneratePlayStreamEvent": True
        }

        AstroLogging.logPrint(requestObj, "debug")
        x = json.load(AstroRequests.post(
            url, headers=headers, jsonD=requestObj))
        AstroLogging.logPrint(x, "debug")
        return x
    except:
        return {"status": "Error"}


def heartbeat_server(serverData, headers, dataToChange=None):
    try:
        url = f"https://5EA1.playfabapi.com/Client/ExecuteCloudScript?sdk={base_headers['X-PlayFabSDK']}"

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

        AstroLogging.logPrint(requestObj, "debug")
        x = json.load(AstroRequests.post(url, headers=headers,
                                         jsonD=requestObj))
        AstroLogging.logPrint(x, "debug")
        return x
    except:
        return {"status": "Error"}


# def getInstallPath():
#     # query steam install path from registry
#     key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'Software\\Valve\\Steam')
#     steamPath = winreg.QueryValueEx(key, "InstallPath")[0]

#     with open(os.path.join(steamPath + "/steamapps/libraryfolders.vdf")) as libraryFile:

#         # get install directory of games
#         lf = libraryFile.read()
#         lf = lf.replace("\\\\", "\\")
#         # pylint: disable=anomalous-backslash-in-string
#         gamePath = re.findall('^\s*"\d*"\s*"([^"]*)"', lf, re.MULTILINE)[0]

#         return os.path.join(gamePath, "steamapps", "common", "ASTRONEER Dedicated Server")
