from UpdateThread import UpdateThread
import logging
import urllib.request

class InternetManager(UpdateThread):

    _connected = True

    def __init__(self):
        UpdateThread.__init__(self, "INTERNET-Thread")
        self.setSleepDuration(0)

    def update(self):
        self.setSleepDuration(2)
        try:
            with urllib.request.urlopen('https://google.com/'):
                self._connected = True            
        except Exception as e:
            logging.error(str(e))
            self._connected = False

    def isConnected(self):
        return self._connected
