

import gzip
import logging
import os
import random
import shutil
import sys
from io import StringIO
from logging.handlers import TimedRotatingFileHandler as _TRFH
from pprint import pformat
from queue import Queue
from threading import Thread

from colorlog import ColoredFormatter

from cogs.utils import AstroRequests

from cogs.utils import ALVERSION


class TimedRotatingFileHandler(_TRFH):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def doRollover(self):
        super(TimedRotatingFileHandler, self).doRollover()
        log_dir = os.path.dirname(self.baseFilename)
        to_compress = [
            os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith(
                os.path.basename(os.path.splitext(self.baseFilename)[0])
            ) and not f.endswith((".gz", ".log"))
        ]
        for f in to_compress:
            try:
                if os.path.exists(f):
                    with open(f, "rb") as _old, gzip.open(f + ".gz", "wb") as _new:
                        shutil.copyfileobj(_old, _new)
                    os.remove(f)
            except:
                pass


class AstroLogging():
    log_stream = None
    discordWebhookURL = None
    discordWebhookLevel = "chat"
    discordWebhookAvatarDict = {}
    discordWebhookQueue = Queue()
    discordWebhookHeaders = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': f"AstroLauncherWebhooks ( https://github.com/ricky-davis/AstroLauncher/releases/latest , {ALVERSION} )"
    }
    # print(discordWebhookHeaders)
    avatarThemes = [
        "frogideas",
        "sugarsweets",
        "heatwave",
        "daisygarden",
        "seascape",
        "summerwarmth",
        "bythepool",
        "duskfalling",
        "berrypie"
    ]
    discordWebhookEmoji = {
        "j": ":wave:",
        "l": ":x:",
        "s": ":floppy_disk:",
        "b": ":recycle:",
        "c": ":speech_balloon:"
    }

    @staticmethod
    def logPrint(message, msgType="info", playerName=None, printTraceback=False, ovrDWHL=False, printToDiscord=None, dwet=None):
        ptd = True
        if msgType == "debug":
            ptd = False
            logging.debug(pformat(message), exc_info=printTraceback)
        if msgType == "info":
            logging.info(pformat(message), exc_info=printTraceback)
        if msgType == "chat":
            msg = f"{playerName}: {message}"
            logging.chat(pformat(msg), exc_info=printTraceback)
        if msgType == "cmd":
            msg = f"{playerName}: /{message}"
            logging.cmd(pformat(msg), exc_info=printTraceback)
        if msgType == "warning":
            logging.warning(pformat(message), exc_info=printTraceback)
        if msgType == "error":
            logging.error(pformat(message), exc_info=printTraceback)
        if msgType == "critical":
            if printTraceback:
                ermsg = ('Error on line {}'.format(
                    sys.exc_info()[-1].tb_lineno), type(message).__name__, message)
                logging.critical(pformat(ermsg))
            logging.critical(pformat(message), exc_info=printTraceback)

        if printToDiscord is not None:
            ptd = printToDiscord

        if AstroLogging.discordWebhookURL and ptd:
            lvl = AstroLogging.discordWebhookLevel
            if dwet:
                message = f"{AstroLogging.discordWebhookEmoji[dwet]} {message}"
            requestObj = {
                "content": message,
                "avatar_url": "https://cdn.discordapp.com/attachments/778327974071238676/778334487208525844/AstroLauncherTransparent.png",
                "allowed_mentions": {
                    "parse": []
                }
            }
            if msgType in ("chat", "cmd"):
                if msgType == "cmd":
                    if lvl != "cmd" and lvl != "all":
                        return
                    message = "/"+message
                requestObj["content"] = message
                requestObj['username'] = playerName
                if playerName not in AstroLogging.discordWebhookAvatarDict.keys():
                    random.seed(playerName)
                    playerNameTheme = random.choice(AstroLogging.avatarThemes)
                    avatarURL = f"https://www.tinygraphs.com/squares/{playerName}?theme={playerNameTheme}&numcolors=4&size=220&fmt=png"
                    AstroLogging.discordWebhookAvatarDict[playerName] = avatarURL
                requestObj['avatar_url'] = AstroLogging.discordWebhookAvatarDict[playerName]
            else:
                if lvl != "all" and not ovrDWHL:
                    return

            AstroLogging.discordWebhookQueue.put(requestObj)

    # pylint: disable=unused-argument
    @classmethod
    def sendDiscordReqLoop(cls):
        def sendDiscordReq(queueMsg):
            try:
                _ = (AstroRequests.post(cls.discordWebhookURL,
                                        headers=cls.discordWebhookHeaders, jsonD=queueMsg))
            except Exception as err:
                ermsg = ('FINAL Error on line {}'.format(
                    sys.exc_info()[-1].tb_lineno), type(err).__name__, err)
                AstroLogging.logPrint(
                    f"Failed to send log msg to discord. {ermsg}", msgType="warning", printToDiscord=False, printTraceback=True)
        while True:
            t = Thread(target=sendDiscordReq, args=(
                cls.discordWebhookQueue.get(),))
            t.daemon = True
            t.start()

    @staticmethod
    def cmd(msg, *args, **kwargs):
        if logging.getLogger().isEnabledFor(21):
            logging.log(21, msg)

    logging.addLevelName(21, "CMD")
    logging.cmd = cmd.__func__
    logging.Logger.cmd = cmd.__func__

    @staticmethod
    def chat(msg, *args, **kwargs):
        if logging.getLogger().isEnabledFor(21):
            logging.log(22, msg)

    logging.addLevelName(22, "CHAT")
    logging.chat = chat.__func__
    logging.Logger.chat = chat.__func__

    @staticmethod
    def setup_logging():
        LOGFORMAT = '%(asctime)s - %(levelname)-6s %(message)s'
        CLOGFORMAT = '%(asctime)s - %(log_color)s%(levelname)-6s%(reset)s %(message)s'
        DATEFMT = "%H:%M:%S"
        LOGCOLORS = {
            'DEBUG':    'cyan',
            'INFO':     'green',
            'CMD':      'blue',
            'CHAT':     'cyan',
            'WARNING':  'red',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
        formatter = logging.Formatter(LOGFORMAT, datefmt=DATEFMT)
        colorformatter = ColoredFormatter(
            CLOGFORMAT, datefmt=DATEFMT, log_colors=LOGCOLORS)
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setFormatter(colorformatter)
        console.setLevel(logging.INFO)

        AstroLogging.log_stream = StringIO()
        stringIOLog = logging.StreamHandler(AstroLogging.log_stream)
        stringIOLog.setFormatter(formatter)
        stringIOLog.setLevel(logging.INFO)

        rootLogger.addHandler(console)
        rootLogger.addHandler(stringIOLog)

    @ staticmethod
    def setup_loggingPath(astroPath, logRetention=0):
        LOGFORMAT = '%(asctime)s - %(levelname)-6s %(message)s'
        DATEFMT = "%H:%M:%S"
        formatter = logging.Formatter(LOGFORMAT, datefmt=DATEFMT)

        rootLogger = logging.getLogger()

        logsPath = os.path.join(astroPath, 'logs\\')
        if not os.path.exists(logsPath):
            os.makedirs(logsPath)
        fileLogHandler = TimedRotatingFileHandler(os.path.join(
            astroPath, 'logs', "server.log"), 'midnight', 1, int(logRetention))
        fileLogHandler.setFormatter(formatter)
        fileLogHandler.setLevel(logging.INFO)

        debugLogHandler = TimedRotatingFileHandler(os.path.join(
            astroPath, 'logs', "debug.log"), 'midnight', 1, 3)
        debugLogHandler.setFormatter(formatter)
        debugLogHandler.setLevel(logging.DEBUG)

        rootLogger.addHandler(fileLogHandler)
        rootLogger.addHandler(debugLogHandler)
