from UpdateThread import UpdateThread
import alsaaudio as audio
import queue
import os
import logging
import json
import math

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
                newVol = 0
                if vol > 0:
                    newVol = 19.87266007 * math.log(vol) + 7.893804667
                newVol = max(self._minVolume, min(self._maxVolume, round(newVol)))
                m.setvolume(int(newVol))
        except Exception as e:
            logging.error(str(e))

    def getMixer(self):
        return [ audio.Mixer('Headphone', cardindex = 0), audio.Mixer('Speaker', cardindex = 0) ]