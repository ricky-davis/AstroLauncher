
import json
import socket
import time
from contextlib import contextmanager

from cogs.AstroLogging import AstroLogging


class AstroRCON():

    def __init__(self, DedicatedServer):
        self.DS = DedicatedServer
        self.connected = False
        self.socket = None
        self.lock = False

    @contextmanager
    def lockRcon(self):
        try:
            while self.lock:
                pass
            self.lock = True
            yield self
        except:
            self.lock = False
        finally:
            self.lock = False

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
            with self.lockRcon() as s:
                # Send console password
                s.socket.sendall(
                    f"{self.DS.settings.ConsolePassword}\n".encode())
                # print(f"{self.DS.settings.ConsolePassword}\n".encode())
            self.connected = True
            AstroLogging.logPrint("Connected to RCON Console!")

    def getSocket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return s

    def DSListPlayers(self):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(b"DSListPlayers\n")
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except Exception as e:
            print(f"Error retrieving player list: {e}")
            return None

    def DSKickPlayerGuid(self, playerGuid):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(
                    f'DSKickPlayerGuid {playerGuid}\n'.encode())
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except Exception as e:
            print(f"Error kicking player: {e}")
            return None

    def DSSetPlayerCategoryForPlayerName(self, playerName, category):
        try:
            escapedName = playerName.replace('"', '\\"')
            with self.lockRcon() as s:
                s.socket.sendall(
                    f'DSSetPlayerCategoryForPlayerName "{escapedName}" {category}\n'.encode())
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except:  # Exception as e:
            # print(e)
            return None

    def DSServerStatistics(self):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(b"DSServerStatistics\n")
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except Exception as e:
            print(f"Error retrieving server statistics: {e}")
            return None

    def DSSaveGame(self, name=None):
        try:
            with self.lockRcon() as s:
                if name is not None:
                    s.socket.sendall(f"DSSaveGame {name}\n".encode())
                else:
                    s.socket.sendall(b"DSSaveGame\n")
                #rawdata = AstroRCON.recvall(s.socket)
                #parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                
                time.sleep(1.1)
                return  # parsedData
        except:  # Exception as e:
            # print(e)
            return None

    def DSSetDenyUnlisted(self, state):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(
                    f'DSSetDenyUnlisted {state}\n'.encode())
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except:  # Exception as e:
            # print(e)
            return None

    def DSServerShutdown(self):
        try:
            self.socket.sendall(b"DSServerShutdown\n")
            #rawdata = AstroRCON.recvall(self.socket)
            #parsedData = AstroRCON.parseData(rawdata)
            # pprint(parsedData)
            return  # parsedData
        except:  # Exception as e:
            # print(e)
            return None

    def DSListGames(self):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(b"DSListGames\n")
                rawdata = AstroRCON.recvall(s.socket)
                parsedData = AstroRCON.parseData(rawdata)
                # pprint(parsedData)
                return parsedData
        except Exception as e:
            print(f"Error retrieving savegame list: {e}")
            return None

    def DSNewGame(self):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(b"DSNewGame\n")
            # pprint(parsedData)
            return True
        except:  # Exception as e:
            # print(e)
            return None

    def DSLoadGame(self, name):
        try:
            with self.lockRcon() as s:
                s.socket.sendall(f'DSLoadGame {name}\n'.encode())
                rawdata = AstroRCON.recvall(s.socket)
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
