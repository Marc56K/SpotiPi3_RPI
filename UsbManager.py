from UpdateThread import UpdateThread
import time
import os
import glob
import usb1

class UsbManager(UpdateThread):

    _m3uRootDir = "/var/lib/mopidy/m3u/"
    _usbRootMountDir = "/media/"
    _usbPrefix = "[USB] "
    _usbCtx = None
    _scanRepeats = 0

    def __init__(self):
        UpdateThread.__init__(self, "USB-Thread")
        self.setSleepDuration(0)

    def hotplug_callback(self, context, device, event):
        self._scanRepeats = 30

    def startup(self):
        try:
            self._usbCtx = usb1.USBContext()
            self._usbCtx.hotplugRegisterCallback(self.hotplug_callback)
            self.scanUsbDrives()
        except Exception as e:
            print("ERROR: " + str(e))

    def update(self):
        if self._usbCtx != None:
            self._usbCtx.handleEventsTimeout(1)
        if self._scanRepeats > 0:
            self._scanRepeats = self._scanRepeats - 1
            self.scanUsbDrives()

    def cleanup(self):
        try:
            if self._usbCtx != None:
                self._usbCtx.close()
                self._usbCtx = None
        except Exception as e:
            print("ERROR: " + str(e))

    def getAudioFilesInDirectory(self, dirPath):
        result = []
        for root, _, files in os.walk(dirPath):
            for fileName in files:
                if fileName.lower().endswith(".mp3"):
                    filePath = os.path.join(root, fileName)
                    result.append(filePath)
        result.sort()
        return result

    def scanUsbDrive(self, usbRootDir, playlists):
        try:
            if os.path.isdir(usbRootDir):
                #print("scanning: " + str(usbRootDir))
                for dirName in os.listdir(usbRootDir):
                    dirPath = os.path.join(usbRootDir, dirName)
                    if os.path.isdir(dirPath):
                        #print("found: " + str(dirPath))
                        audioFiles = self.getAudioFilesInDirectory(dirPath)
                        if len(audioFiles) > 0:
                            playlists[dirName] = '\n'.join(audioFiles)
        except Exception as e:
            print("ERROR: " + str(e))
    
    def scanUsbDrives(self):
        try:
            #print("scanning usb drives ...")
            playlists = {}
            for i in range(8):
                self.scanUsbDrive(self._usbRootMountDir + "usb" + str(i), playlists)

            for playlist in playlists:                
                self.wirtePlaylist(playlist, playlists[playlist])
            #print("scanning usb drives finished!")

            #print("cleanup playlists ...")
            for usbPlaylistFile in glob.glob(os.path.join(self._m3uRootDir, "*.m3u8")):
                usbPlaylistName = os.path.basename(usbPlaylistFile)
                if usbPlaylistName.startswith(self._usbPrefix):
                    usbPlaylistName = usbPlaylistName.replace(self._usbPrefix, "").replace(".m3u8", "")                
                    if not (usbPlaylistName in playlists):
                        print("DELETE USB-PLAYLIST: " + usbPlaylistName)
                        os.remove(usbPlaylistFile)

            for partFile in glob.glob(os.path.join(self._m3uRootDir, "*.part")):
                os.remove(partFile)
            #print("cleanup playlists finished!")

        except Exception as e:
            print("ERROR: " + str(e))

    def wirtePlaylist(self, playlistName, content):
        try:
            filePath = os.path.join(self._m3uRootDir, self._usbPrefix + playlistName + ".m3u8")
            if os.path.exists(filePath):
                f = open(filePath, "r")
                if f.read() == content:
                    #print(playlistName + " already up-to-date")
                    return
                f.close()
            print("NEW USB-PLAYLIST: " + playlistName)
            f = open(filePath + ".part", "w")
            f.write(content)
            f.close()
            os.rename(filePath + ".part", filePath)
        except Exception as e:
            print("ERROR: " + str(e))

if __name__ == '__main__':
    usbMgr = UsbManager()
    print("starting...")
    usbMgr.start()
    input("Press Enter to exit...")
    print("stopping...")
    usbMgr.stop()
    print("done")