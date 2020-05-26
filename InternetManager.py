from UpdateThread import UpdateThread
import time
import logging
import urllib.request
from subprocess import call

class InternetManager(UpdateThread):

    _online = False

    _wifiConfigFile = "/etc/wpa_supplicant/wpa_supplicant.conf"

    _currentWifiSsid = None
    _newWifiSsid = None

    _currentWifiKey = None
    _newWifiKey = None

    def __init__(self):
        UpdateThread.__init__(self, "INTERNET-Thread")
        self.setSleepDuration(0)

    def update(self):
        self.setSleepDuration(2)
        try:
            with urllib.request.urlopen('https://google.com/'):
                self._online = True            
        except Exception as e:
            print(str(e))
            self._online = False

    def isOnline(self):
        return self._online

    def setWifiSsid(self, ssid):
        self._newWifiSsid = ssid
        self.configureWifi()

    def setWifiKey(self, key):
        self._newWifiKey = key
        self.configureWifi()

    def configureWifi(self):
        if self._newWifiSsid != None and self._newWifiKey != None:
            try:
                if self._currentWifiSsid == None or self._currentWifiKey == None:
                    conf = open(self._wifiConfigFile, "r")
                    try:
                        for line in conf:
                            entry = line.strip()
                            if entry.startswith("ssid="):
                                self._currentWifiSsid = entry.split("\"")[1]
                            if entry.startswith("psk="):
                                self._currentWifiKey = entry.split("\"")[1]
                    finally:
                        conf.close()
                if self._currentWifiSsid != self._newWifiSsid or self._currentWifiKey != self._newWifiKey:
                    print("writing to " + self._wifiConfigFile)
                    conf = open(self._wifiConfigFile, "w")
                    self._currentWifiSsid = self._newWifiSsid
                    self._currentWifiKey = self._newWifiKey
                    try:
                        conf.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                        conf.write("update_config=1\n")
                        conf.write("country=DE\n")
                        conf.write("network={\n")
                        conf.write(" ssid=\"" + self._newWifiSsid + "\"\n")
                        conf.write(" psk=\"" + self._newWifiKey + "\"\n")
                        conf.write("}\n")
                    finally:
                        conf.close()
                    print("restarting wifi")
                    call("sudo wpa_cli -i wlan0 reconfigure", shell=True)
                    call("sudo dhclient -v wlan0", shell=True)
                    print("done")
            except Exception as e:
                print(str(e))
