from subprocess import call

class MopidyConfig:

    _params = { 
        "username": [-1, None, None], 
        "password": [-1, None, None], 
        "client_id": [-1, None, None], 
        "client_secret": [-1, None, None] }
    _configFile = "/etc/mopidy/mopidy.conf"
    _configLines = None

    def __init__(self):
        pass

    def setSpotifyUser(self, value):
        self._params["username"][2] = value
        self.updateConfig()

    def setSpotifyPassword(self, value):
        self._params["password"][2] = value
        self.updateConfig()

    def setSpotifyClientId(self, value):
        self._params["client_id"][2] = value
        self.updateConfig()

    def setSpotifyClientSecret(self, value):
        self._params["client_secret"][2] = value
        self.updateConfig()

    def updateConfig(self):
        for (k, v) in self._params.items():
            if v[2] == None:
                return # missing new value

        if self._configLines == None:
            try:
                with open(self._configFile, "r") as conf:
                    self._configLines = conf.readlines()

                spotifySection = False
                lineIdx = 0
                for line in self._configLines:
                    if line.startswith("["):
                        spotifySection = line.startswith("[spotify]")
                    elif spotifySection:
                        for (k, v) in self._params.items():
                            if line.startswith(k):
                                v[0] = lineIdx
                                v[1] = line.split("=", 1)[1].strip()

                    lineIdx = lineIdx + 1

                configValid = True
                for (k, v) in self._params.items():
                    if v[0] < 0:
                        configValid = False

                if not configValid:
                    self._configLines.append("\n")
                    self._configLines.append("[spotify]\n")
                    lineIdx = lineIdx + 2
                    for (k, v) in self._params.items():
                        v[0] = lineIdx
                        v[1] = ""
                        self._configLines.append("\n")
                        lineIdx = lineIdx + 1
            except Exception as e:
                print(str(e))
        
        writeConfig = False
        for (k, v) in self._params.items():
            if v[1] != v[2]:
                writeConfig = True
                break

        if writeConfig:
            try:
                for (k, v) in self._params.items():
                    v[1] = v[2]
                    self._configLines[v[0]] = k + " = " + v[2] + "\n"

                print("writing to " + self._configFile)
                with open(self._configFile, "w") as conf:
                    for line in self._configLines:
                        conf.write(line)

                print("restarting mopidy")
                call("sudo systemctl restart mopidy", shell=True)                
            except Exception as e:
                print(str(e))