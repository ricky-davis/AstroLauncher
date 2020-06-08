import argparse
import os
import signal
import psutil
import time

def watchDog(laucherPID, consolePID):
    while(psutil.pid_exists(int(laucherPID)) and psutil.pid_exists(int(consolePID))):
        time.sleep(0.5)
    try:
        for child in psutil.Process(int(consolePID)).children():
            os.kill(child.pid, signal.CTRL_C_EVENT)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--consolepid", type=str.lower)
        parser.add_argument("-l", "--launcherpid", type=str.lower)
        args = parser.parse_args() 
        if args.consolepid and args.launcherpid:
            watchDog(args.launcherpid, args.consolepid)
        else:
            print("Insufficient launch options!")

    except KeyboardInterrupt:
        pass
