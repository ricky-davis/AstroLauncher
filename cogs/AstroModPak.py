# pylint: disable=unused-variable
import struct
import zlib
'''
    Parses both compressed and uncompressed PAK files to look for `metadata.json`

    USAGE:

        from AstroModPak import PakParser

        PP = PakParser("000-GoodSample_P.pak")
        print(PP.data)

        PP = PakParser("000-CompressedSample_P.pak")
        print(PP.data)

'''


class PakParser():
    CompressionMethod = {0: "NONE", 1: "ZLIB",
                         2: "BIAS_MEMORY", 3: "BIAS_SPEED"}

    def __init__(self, filepath):
        self.data = None
        with open(filepath, "rb") as f:
            self.data = f.read()
        self.data = PakParser.PakReader().Read(self.data)

    class Block():
        def __init__(self, start, size):
            self.Start = start
            self.Size = size

    class Record():
        def __init__(self):
            self.fileName = None
            self.offset = None
            self.fileSize = None
            self.sizeDecompressed = None
            self.compressionMethod = None
            self.isEncrypted = None
            self.compressionBlocks = []

        def Read(self, data, fileVersion, includesHeader):
            tData = data[:]
            if includesHeader:
                strLen, tData = PakParser.readInt(32, tData, True)
                self.fileName, tData = PakParser.readLen(strLen, tData, True)

            self.offset, tData = PakParser.readInt(64, tData, True)
            self.fileSize, tData = PakParser.readInt(64, tData, True)
            self.sizeDecompressed, tData = PakParser.readInt(64, tData, True)
            self.compressionMethod, tData = PakParser.readInt(32, tData, True)

            if fileVersion <= 1:
                timestamp, tData = PakParser.readInt(64, tData, True)

            sha1hash, tData = PakParser.readLen(20, tData, True)

            if fileVersion >= 3:
                if self.compressionMethod != 0:
                    blockCount, tData = PakParser.readInt(32, tData, True)
                    for _ in range(blockCount):
                        startOffset, tData = PakParser.readInt(64, tData, True)
                        endOffset, tData = PakParser.readInt(64, tData, True)
                        self.compressionBlocks.append(PakParser.Block(
                            startOffset, endOffset - startOffset))

                isEncrypted, tData = PakParser.readInt(8, tData, True)
                self.isEncrypted = isEncrypted > 0
                compressionBlockSize, tData = PakParser.readInt(
                    32, tData, True)
            return tData

    class PakReader():
        def Read(self, data):
            footerData = data[-44:]  # First we head straight to the footer

            rtn, footerData = PakParser.readInt(32, footerData, True)
            assert hex(rtn) == "0x5a6f12e1"

            fileVersion, footerData = PakParser.readInt(32, footerData, True)
            indexOffset, footerData = PakParser.readInt(64, footerData, True)
            indexSize, footerData = PakParser.readInt(64, footerData, True)

            offsetData = data[indexOffset:]
            strLen, offsetData = PakParser.readInt(32, offsetData, True)
            mountPoint, offsetData = PakParser.readLen(
                strLen, offsetData, True)
            recordCount, offsetData = PakParser.readInt(32, offsetData, True)

            for _ in range(recordCount):
                rec = PakParser.Record()
                offsetData = rec.Read(offsetData, fileVersion, True)
                if rec.fileName == "metadata.json":
                    offsetData = data[rec.offset:]
                    # I don't know why there's a second record but there is, so we read it out
                    rec2 = PakParser.Record()
                    offsetData = rec2.Read(offsetData, fileVersion, False)

                    if PakParser.CompressionMethod[rec.compressionMethod] == "NONE":
                        f, offsetData = PakParser.readLen(
                            rec2.fileSize, offsetData, True)
                        return f
                    elif PakParser.CompressionMethod[rec.compressionMethod] == "ZLIB":
                        data_decompressed = []
                        for block in rec2.compressionBlocks:
                            blockOffset = block.Start
                            blockSize = block.Size

                            rData = data[blockOffset:]
                            memstream, rData = PakParser.readLen(
                                blockSize, rData)
                            data_decompressed.append(
                                zlib.decompress(memstream))
                        return b''.join(data_decompressed).decode()
                    else:
                        raise NotImplementedError(
                            "Unimplemented compression method " + PakParser.CompressionMethod[rec.compressionMethod])

            return ""

    @staticmethod
    def readInt(size, data, unsigned=False):
        unsigned = bool(unsigned)
        size = int(size)
        if size == 8:
            bType = b'<B' if unsigned else b'<b'
        if size == 16:
            bType = b'<H'if unsigned else b'<h'
        if size == 32:
            bType = b'<I'if unsigned else b'<i'
        if size == 64:
            bType = b'<Q' if unsigned else b'<q'
        rtnData = int(struct.unpack(
            bType, bytes(data[:int(size/8)]))[0])
        data = data[int(size/8):]
        return rtnData, data

    @staticmethod
    def readLen(length, data, strRtn=False):
        if isinstance(length, bytes):
            length = int.from_bytes(length, 'little')
        rtnData = data[:int(length)]
        data = data[int(length):]
        if strRtn:
            rtnData = rtnData.strip(b"\x00").decode('iso-8859-1')
        return rtnData, data
