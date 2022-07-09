
import json
import ntpath
import os
import chardet

_default_dict = dict


class MultiConfig():
    """ Apparently nobody has a use-case for an ini file with duplicate keys, go figure. Somebody please make this better.
    """
    # Possible boolean values in the configuration.
    BOOLEAN_STATES = {'yes': True, 'true': True, 'on': True,
                      'no': False, 'false': False, 'off': False}

    def getdict(self):
        return self.__dict__

    def read_dict(self, configDict):
        self.__dict__ = json.loads(json.dumps(
            configDict), parse_int=str, parse_float=str)

    def read(self, configPath):
        encoding = MultiConfig.get_encoding(configPath)
        with open(configPath, "r", encoding=encoding) as f:
            lines = [l.strip() for l in f.read().split("\n")]
            section = None
            properties = [x.split("=", 1) for x in lines]
            for p in properties:
                key = p[0].strip()
                if isinstance(p, list) and len(p) > 1:
                    value = p[1].strip()
                    if value != "":
                        if value.lower() in self.BOOLEAN_STATES:
                            value = self._convert_to_boolean(value)
                        if key in self.__dict__[section]:
                            if isinstance(self.__dict__[section][key], str):
                                self.__dict__[section][key] = [
                                    self.__dict__[section][key], value]
                            else:
                                self.__dict__[section][key].append(value)
                        else:
                            self.__dict__[section][key] = value
                else:
                    if len(key) > 0:
                        section = key[1: len(key)-1]
                        self.__dict__[section] = {}

    def write(self, configFile):
        for section in self.__dict__.keys():
            configFile.write(f"[{section}]\n")
            properties = self.__dict__[section]
            for p, v in properties.items():
                if isinstance(v, list):
                    for item in v:
                        configFile.write(f"{p}={item}\n")
                else:
                    configFile.write(f"{p}={v}\n")

    def update(self, updateWithDict):
        config = MultiConfig()
        config.read_dict(self._update(self.getdict(), updateWithDict))
        return config

    def _update(self, baseDict, updateWithDict):
        tDict = {}
        for key, value in baseDict.items():
            tDict[key] = value
            if key in updateWithDict.keys():
                if isinstance(value, dict):
                    tDict[key] = self._update(
                        value, updateWithDict[key])
                else:
                    tDict[key] = updateWithDict[key]

        tDict.update({k: v for k, v in updateWithDict.items()
                      if k not in tDict.keys()})
        return tDict

    def overwrite_with(self, filePath, overwriteDict):
        fileConfig = MultiConfig()
        fileConfig.read(filePath)
        ovrConfig = MultiConfig()
        ovrConfig.read_dict(overwriteDict)
        newConfig = fileConfig.update(ovrConfig.getdict())

        encoding = MultiConfig.get_encoding(filePath)
        with open(filePath, 'w', encoding=encoding) as configfile:
            newConfig.write(configfile)
        return newConfig

    def baseline(self, filePath, dictBaseline):
        baseConfig = MultiConfig()
        baseConfig.read_dict(dictBaseline)
        fileConfig = MultiConfig()
        fileConfig.read(filePath)
        newConfig = baseConfig.update(fileConfig.getdict())

        encoding = MultiConfig.get_encoding(filePath)
        with open(filePath, 'w', encoding=encoding) as configfile:
            newConfig.write(configfile)
        return newConfig

    def _convert_to_boolean(self, value):
        """Return a boolean value translating from other types if necessary.
        """
        if value.lower() not in self.BOOLEAN_STATES:
            raise ValueError('Not a boolean: %s' % value)
        return self.BOOLEAN_STATES[value.lower()]

    @staticmethod
    def get_encoding(filePath):
        pathname = ntpath.dirname(filePath)
        if pathname and not ntpath.exists(pathname):
            os.makedirs(pathname)
        with open(filePath, 'a+', encoding="utf_8"):
            pass
        with open(filePath, 'rb') as fP:
            rawdata = fP.read()
        result = chardet.detect(rawdata)
        charenc = result['encoding']
        return charenc
