

import logging
import os
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
from pprint import pformat


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
    def setup_logging(astroPath):
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-6s %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.INFO)

        console = logging.StreamHandler()
        console.setFormatter(formatter)

        AstroLogging.log_stream = StringIO()
        stringIOLog = logging.StreamHandler(AstroLogging.log_stream)
        stringIOLog.setFormatter(formatter)
        stringIOLog.setLevel(logging.INFO)

        logsPath = os.path.join(astroPath, 'logs\\')
        if not os.path.exists(logsPath):
            os.makedirs(logsPath)
        fileLogHandler = TimedRotatingFileHandler(os.path.join(
            astroPath, 'logs', "server.log"), 'midnight', 1)
        fileLogHandler.setFormatter(formatter)
        fileLogHandler.setLevel(logging.DEBUG)

        rootLogger.addHandler(console)
        rootLogger.addHandler(fileLogHandler)
        rootLogger.addHandler(stringIOLog)
