from MopidyClient import MopidyClient
from InternetManager import InternetManager
from AudioManager import AudioManager
from UsbManager import UsbManager
from SerialInterface import SerialInterface
from subprocess import call
import threading
import time
import signal
import logging
import os

class MainApp:
    hdmiActive = True
    shutdownRequested = False
    lastStateUpdate = 0

    inetMgr = InternetManager()
    audioMgr = AudioManager()
    usbManager = UsbManager()
    mpdClient = MopidyClient()
    serialIf = SerialInterface()

    def __init__(self):
        pass

    def handleShutdownRequest(self, signal, frame):
        self.shutdownRequested = True

    def run(self):
        signal.signal(signal.SIGINT, self.handleShutdownRequest)
        signal.signal(signal.SIGTERM, self.handleShutdownRequest)

        self.usbManager.start()
        self.inetMgr.start()
        self.audioMgr.start()

        while not self.shutdownRequested:      
            start = time.time()      
            self.loop()
            end = time.time()
            delta = end - start 
            time.sleep(max(0, 0.3 - delta))

        self.audioMgr.stop()
        self.inetMgr.stop()
        self.usbManager.stop()

    def shutdownHdmi(self):
        if self.inetMgr.isOnline() and self.hdmiActive:
            self.hdmiActive = False
            call("/usr/bin/tvservice -o", shell=True)        

    def loop(self):
        try:
            messages = self.serialIf.read()
            for msg in messages:
                #print(str(msg))
                for (k, v) in msg.items():
                    if k == "volume":
                        self.audioMgr.setAudioVolume(v)
                    elif k == "playlist":
                        self.mpdClient.loadPlaylist(v)
                    elif k == "stop":
                        self.mpdClient.stop()
                    elif k == "togglePlayPause":
                        self.mpdClient.togglePlayPause()
                    elif k == "skipPrevious":
                        self.mpdClient.skipToPreviousTrack(v)
                    elif k == "skipNext":
                        self.mpdClient.skipToNextTrack(v)
                    elif k == "skipToStart":
                        self.mpdClient.skipToStart()
                    elif k == "skipTo":
                        self.mpdClient.skipToTrack(v)
                    elif k == "seek":
                        self.mpdClient.seek(v)
                    elif k == "shutdown":
                        self.mpdClient.stop()
                        call("sudo shutdown 0", shell=True)
                    elif k == "reboot":
                        self.mpdClient.stop()
                        call("sudo reboot 0", shell=True)
                    elif k == "wifiSsid":
                        self.inetMgr.setWifiSsid(v)
                    elif k == "wifiKey":
                        self.inetMgr.setWifiKey(v)
                    elif k == "spotifyUser":
                        self.mpdClient.setSpotifyUser(v)
                    elif k == "spotifyPassword":
                        self.mpdClient.setSpotifyPassword(v)
                    elif k == "spotifyClientId":
                        self.mpdClient.setSpotifyClientId(v)
                    elif k == "spotifyClientSecret":
                        self.mpdClient.setSpotifyClientSecret(v)
        except Exception as e:
            print(str(e))

        if time.time() - self.lastStateUpdate > 0.9:
            self.lastStateUpdate = time.time()
            try:
                dict = {}
                dict["online"] = self.inetMgr.isOnline()
                dict.update(self.mpdClient.updateStatus())
                self.serialIf.write(dict)
                self.shutdownHdmi()
            except Exception as e:
                print(str(e))

        self.mpdClient.disconnect()

if __name__ == '__main__':
    try:
        os.nice(19)
        MainApp().run()
    except Exception as e:
        print(str(e))
        exit(1)

    exit(0)
