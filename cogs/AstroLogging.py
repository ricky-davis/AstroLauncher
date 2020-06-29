

import logging
import os
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
from pprint import pformat
from colorlog import ColoredFormatter


class AstroLogging():
    log_stream = None

    @staticmethod
    def logPrint(message, msgType="info"):
        if msgType == "debug":
            logging.debug(pformat(message))
        if msgType == "info":
            logging.info(pformat(message))
        if msgType == "warning":
            logging.warning(pformat(message))
        if msgType == "error":
            logging.error(pformat(message))
        if msgType == "critical":
            logging.critical(pformat(message))

    @staticmethod
    def setup_logging():
        LOGFORMAT = '%(asctime)s - %(levelname)-6s %(message)s'
        CLOGFORMAT = '%(asctime)s - %(log_color)s%(levelname)-6s%(reset)s %(message)s'
        DATEFMT = "%Y-%m-%d %H:%M:%S"
        LOGCOLORS = {
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'red',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
        formatter = logging.Formatter(LOGFORMAT, datefmt=DATEFMT)
        colorformatter = ColoredFormatter(
            CLOGFORMAT, datefmt=DATEFMT, log_colors=LOGCOLORS)
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.INFO)

        console = logging.StreamHandler()
        console.setFormatter(colorformatter)

        AstroLogging.log_stream = StringIO()
        stringIOLog = logging.StreamHandler(AstroLogging.log_stream)
        stringIOLog.setFormatter(formatter)
        stringIOLog.setLevel(logging.INFO)

        rootLogger.addHandler(console)
        rootLogger.addHandler(stringIOLog)

    @staticmethod
    def setup_loggingPath(astroPath):
        LOGFORMAT = '%(asctime)s - %(levelname)-6s %(message)s'
        DATEFMT = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(LOGFORMAT, datefmt=DATEFMT)

        rootLogger = logging.getLogger()

        logsPath = os.path.join(astroPath, 'logs\\')
        if not os.path.exists(logsPath):
            os.makedirs(logsPath)
        fileLogHandler = TimedRotatingFileHandler(os.path.join(
            astroPath, 'logs', "server.log"), 'midnight', 1)
        fileLogHandler.setFormatter(formatter)
        fileLogHandler.setLevel(logging.DEBUG)

        rootLogger.addHandler(fileLogHandler)
