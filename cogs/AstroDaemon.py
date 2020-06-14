import os
import signal
import subprocess
import sys
import time

import psutil


class AstroDaemon():
    """
        Daemon process to watch the Launcher and Dedicated Server
    """

    @staticmethod
    def launch(executable, consolePID):
        if executable:
            daemonCMD = [sys.executable, '--daemon', '-l',
                         str(os.getpid()), '-c', str(consolePID)]
        else:
            daemonCMD = [sys.executable, sys.argv[0], '--daemon',
                         '-l', str(os.getpid()), '-c', str(consolePID)]
        return subprocess.Popen(daemonCMD, shell=False, creationflags=subprocess.DETACHED_PROCESS |
                                subprocess.CREATE_NEW_PROCESS_GROUP)

    @staticmethod
    def daemon(laucherPID, consolePID):
        while(psutil.pid_exists(int(laucherPID)) and psutil.pid_exists(int(consolePID))):
            time.sleep(0.5)
        try:
            for child in psutil.Process(int(consolePID)).children():
                os.kill(child.pid, signal.CTRL_C_EVENT)
        except KeyboardInterrupt as e:
            print(e)
