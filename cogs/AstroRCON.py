
import json
import socket
from contextlib import contextmanager


class AstroRCON():

    @staticmethod
    def DSListPlayers(consolePort):
        try:
            with AstroRCON.session_scope(consolePort) as s:
                s.sendall(b"DSListPlayers\n")
                rawdata = AstroRCON.recvall(s)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except:
            return None

    @staticmethod
    @contextmanager
    def session_scope(consolePort: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.settimeout(5)
            s.connect(("127.0.0.1", int(consolePort)))
            yield s
        except:
            pass
        finally:
            s.close()

    @staticmethod
    def recvall(sock):
        try:
            BUFF_SIZE = 4096  # 4 KiB
            data = b''
            while True:
                part = sock.recv(BUFF_SIZE)
                data += part
                if len(part) < BUFF_SIZE:
                    # either 0 or end of data
                    break
            return data
        except ConnectionResetError:
            return None

    @staticmethod
    def parseData(rawdata):
        try:
            data = json.loads(rawdata.decode('utf8'))
            return data
        except:
            return rawdata
