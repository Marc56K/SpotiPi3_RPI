from MopidyClient import MopidyClient
from InternetManager import InternetManager
from SerialInterface import SerialInterface
import threading
import time
import signal
import logging

class MainApp:
    criticalError = 0
    shutdownRequested = False
    shutdownCv = threading.Condition()

    mpdClient = MopidyClient()
    inetMgr = InternetManager()
    serialIf = SerialInterface()

    def __init__(self):
        pass

    def run(self):
        signal.signal(signal.SIGINT, self.handleShutdownRequest)
        signal.signal(signal.SIGTERM, self.handleShutdownRequest)

        self.serialIf.onMessageReceived = self.handleSerialMessage

        self.inetMgr.start()
        self.mpdClient.start()
        self.serialIf.start()

        with self.shutdownCv:
            while not self.shutdownRequested:
                self.shutdownCv.wait()
        
        self.serialIf.stop()
        self.mpdClient.stop()
        self.inetMgr.stop()

    def handleSerialMessage(self, msg):
        print(str(msg))

    def handleShutdownRequest(self, signal, frame):
        with self.shutdownCv:
            self.shutdownRequested = True
            self.shutdownCv.notify_all()

    def handleCriticalError(self, error):
        logging.critical(error)
        self.criticalError = time.time()

if __name__ == '__main__':

    try:
        logging.basicConfig(level=logging.INFO)
        #fh = logging.FileHandler('log.log')
        #fh.setLevel(logging.DEBUG)
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #fh.setFormatter(formatter)
        #logging.getLogger().addHandler(fh)
        #logging.getLogger("mpd.base").addHandler(fh)

        MainApp().run()        
    except Exception as e:
        logging.error(str(e))
        exit(1)
    finally:
        #GPIO.cleanup()
        pass

    exit(0)
