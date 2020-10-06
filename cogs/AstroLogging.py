

import logging
import os
import sys
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
from pprint import pformat

from colorlog import ColoredFormatter


class AstroLogging():
    log_stream = None

    @staticmethod
    def logPrint(message, msgType="info", printTraceback=False):
        if msgType == "debug":
            logging.debug(pformat(message), exc_info=printTraceback)
        if msgType == "info":
            logging.info(pformat(message), exc_info=printTraceback)
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

    @staticmethod
    def setup_logging(debugLogging=False):
        LOGFORMAT = '%(asctime)s - %(levelname)-6s %(message)s'
        CLOGFORMAT = '%(asctime)s - %(log_color)s%(levelname)-6s%(reset)s %(message)s'
        DATEFMT = "%H:%M:%S"
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
        logLevel = logging.DEBUG if debugLogging else logging.INFO
        rootLogger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setFormatter(colorformatter)
        console.setLevel(logLevel)

        AstroLogging.log_stream = StringIO()
        stringIOLog = logging.StreamHandler(AstroLogging.log_stream)
        stringIOLog.setFormatter(formatter)
        stringIOLog.setLevel(logging.INFO)

        rootLogger.addHandler(console)
        rootLogger.addHandler(stringIOLog)

    @staticmethod
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
        fileLogHandler.setLevel(logging.DEBUG)

        rootLogger.addHandler(fileLogHandler)
