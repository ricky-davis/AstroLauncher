
import json
import socket

from cogs.AstroLogging import AstroLogging


class AstroRCON():

    def __init__(self, DedicatedServer):
        self.DS = DedicatedServer
        self.connected = False
        self.socket = None

    def run(self):
        # pylint: disable=protected-access
        if self.socket is None or self.socket._closed:
            self.socket = self.getSocket()
        if not self.connected:
            try:
                self.socket.send(b"u up?")
            except:  # Exception as e:
                self.connected = False
                #print("no response, reconnecting..")
                try:
                    self.connectSocket()
                except:  # Exception as er:
                    pass
                #print(f"3 {e}")

    def connectSocket(self):
        if not self.connected:
            # print("Connecting...")
            self.socket.connect(
                ("127.0.0.1", int(self.DS.settings.ConsolePort)))
            self.connected = True
            AstroLogging.logPrint("Connected to RCON Console!")

    def getSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return s

    def DSListPlayers(self):
        try:
            self.socket.sendall(b"DSListPlayers\n")
            rawdata = AstroRCON.recvall(self.socket)
            parsedData = AstroRCON.parseData(rawdata)
            # pprint(parsedData)
            return parsedData
        except Exception as e:
            print(f"Error retrieving player list: {e}")
            return None

    def DSServerStatistics(self):
        try:
            self.socket.sendall(b"DSServerStatistics\n")
            rawdata = AstroRCON.recvall(self.socket)
            parsedData = AstroRCON.parseData(rawdata)
            # pprint(parsedData)
            return parsedData
        except Exception as e:
            print(f"Error retrieving server statistics: {e}")
            return None

    def DSSaveGame(self):
        try:
            self.socket.sendall(b"DSSaveGame\n")
            rawdata = AstroRCON.recvall(self.socket)
            parsedData = AstroRCON.parseData(rawdata)
            # pprint(parsedData)
            return parsedData
        except:  # Exception as e:
            # print(e)
            return None

    def DSServerShutdown(self):
        try:
            self.socket.sendall(b"DSServerShutdown\n")
            rawdata = AstroRCON.recvall(self.socket)
            parsedData = AstroRCON.parseData(rawdata)
            # pprint(parsedData)
            return parsedData
        except:  # Exception as e:
            # print(e)
            return None

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
        except:  # ConnectionResetError as e:
            #print(f"recvall Error {e}")
            return None

    @staticmethod
    def parseData(rawdata):
        try:
            if rawdata != b"":
                rawdata = rawdata.rstrip()
                data = json.loads(rawdata.decode())
                return data
            return None
        except:  # Exception as e:
            #print(f"RCON Parse Error {e}")
            return rawdata
