from MopidyClient import MopidyClient
from InternetManager import InternetManager
from AudioManager import AudioManager
from SerialInterface import SerialInterface
from subprocess import call
import threading
import time
import signal
import logging
import os

class MainApp:
    shutdownRequested = False
    lastStateUpdate = 0

    inetMgr = InternetManager()
    audioMgr = AudioManager()
    mpdClient = MopidyClient()
    serialIf = SerialInterface()

    def __init__(self):
        pass

    def handleShutdownRequest(self, signal, frame):
        self.shutdownRequested = True

    def run(self):
        signal.signal(signal.SIGINT, self.handleShutdownRequest)
        signal.signal(signal.SIGTERM, self.handleShutdownRequest)

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

    def loop(self):
        try:
            messages = self.serialIf.read()
            for msg in messages:
                print(str(msg))
                for (k, v) in msg.items():
                    if k == "volume":
                        self.audioMgr.setAudioVolume(v)
                    elif k == "playlist":
                        self.mpdClient.loadPlaylist(v)
                    elif k == "togglePlayPause":
                        self.mpdClient.togglePlayPause()
                    elif k == "skipPrevious":
                        self.mpdClient.skipToPreviousTrack(v)
                    elif k == "skipNext":
                        self.mpdClient.skipToNextTrack(v)
                    elif k == "skipToStart":
                        self.mpdClient.skipToStart()
                    elif k == "shutdown":
                        call("sudo shutdown 0", shell=True)
        except Exception as e:
            print(str(e))

        if time.time() - self.lastStateUpdate > 0.9:
            self.lastStateUpdate = time.time()
            try:
                dict = {}
                dict["online"] = self.inetMgr.isConnected()
                dict.update(self.mpdClient.getStatus())
                self.serialIf.write(dict)
            except Exception as e:
                print(str(e))

        self.mpdClient.disconnect()

if __name__ == '__main__':
    try:
        os.nice(19)
        time.sleep(5)
        MainApp().run()        
    except Exception as e:
        print(str(e))
        exit(1)

    exit(0)
