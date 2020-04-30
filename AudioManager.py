from UpdateThread import UpdateThread
import alsaaudio as audio
import queue
import os
import logging
import json

class AudioManager:

    _maxVolume = 100
    _minVolume = 0

    def __init__(self):
        self._soundsDir = os.path.dirname(__file__) + "/sounds/"

    def playSound(self, fileName):
        try:
            os.system("aplay " + self._soundsDir + fileName)
        except Exception as e:
            logging.error(str(e))

    def setAudioVolume(self, vol):
        try:
            for m in self.getMixer():
                newVol = max(self._minVolume, min(self._maxVolume, vol))
                #print ("volume: {0}".format(newVol))
                m.setvolume(newVol)
        except Exception as e:
            logging.error(str(e))

    def getMixer(self):
        return [ audio.Mixer('Headphone', cardindex = 0), audio.Mixer('Speaker', cardindex = 0) ]