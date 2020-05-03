from UpdateThread import UpdateThread
import RPi.GPIO as gpio
import alsaaudio as audio
import queue
import os
import logging
import json
import math

class AudioManager(UpdateThread):

    _volume = 0
    _maxVolume = 100
    _minVolume = 0
    _cardIdx = 0

    def __init__(self):
        UpdateThread.__init__(self, "AUDIO-Thread")
        self.setSleepDuration(0.5)
        self._soundsDir = os.path.dirname(__file__) + "/sounds/"
        self._cardIdx = audio.cards().index('wm8960soundcard')
        gpio.setmode(gpio.BCM)
        gpio.setup(4, gpio.IN)

    def update(self):
        try:
            if self.headphoneDetected():                
                self.getSpeakerMixer().setvolume(0)
            else:
                self.getSpeakerMixer().setvolume(self._volume)
            self.getHeadphoneMixer().setvolume(self._volume)
        except Exception as e:
            logging.error(str(e))

    def headphoneDetected(self):
        return not gpio.input(4)

    def getSpeakerMixer(self):
        return audio.Mixer('Speaker', cardindex = self._cardIdx)

    def getHeadphoneMixer(self):
        return audio.Mixer('Headphone', cardindex = self._cardIdx)

    def playSound(self, fileName):
        try:
            os.system("aplay " + self._soundsDir + fileName)
        except Exception as e:
            logging.error(str(e))

    def setAudioVolume(self, vol):
        with self.cv:        
            newVol = 0
            if vol > 0:
                newVol = 19.87266007 * math.log(vol) + 7.893804667
            newVol = max(self._minVolume, min(self._maxVolume, round(newVol)))
            self._volume = newVol
            self.cv.notify_all()
