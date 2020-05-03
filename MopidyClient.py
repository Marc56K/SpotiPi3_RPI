from UpdateThread import UpdateThread
from mpd import MPDClient
import os.path
import time
import json
import logging
import threading

class MopidyClient(UpdateThread):

    _playlistLock = threading.RLock()
    _requestedPlaylistId = ""
    _currentPlaylistId = ""
    _client = None

    def __init__(self):
        UpdateThread.__init__(self, "MOPIDY_CLIENT-Thread")

        self._state = { 'playlistId': '', 'songIdx': 0, 'songTime': 0 }
        #self.loadState()
        self.resetClient()

    def start(self):
        self.connect(60)
        threading.Thread.start(self)

    def loadState(self):
        for i in range(2):
            fname = 'state{0}.json'.format(i)
            try:
                if os.path.isfile(fname):
                    with open(fname, 'r') as f:
                        self._state = json.load(f)
                        return
            except Exception as e:
                logging.error(str(e))

    def saveState(self):
        for i in range(2):
            try:
                fname = 'state{0}.json'.format(i)
                with open(fname, 'w') as f:
                    json.dump(self._state, f)
            except Exception as e:
                logging.error(str(e))

    def resetClient(self):
        self.cleanup()
        self._client = MPDClient()
        self._client.timeout = 20
        self._client.idletimeout = None
    
    def connect(self, timeout):
        start = time.time()
        while not self.shutdownRequested():
            try:
                self._client.connect("localhost", 6600)
                break
            except Exception as e:
                logging.warning(str(e))
                now = time.time()
                delta = now - start
                if timeout > 0 and delta < timeout:
                    time.sleep(1)
                else:
                    break
    
    def updateConnection(self):
        try:
            self._client.ping()
        except Exception as e:
            logging.warning(str(e))
            self.resetClient()
            self.connect(0)

    def update(self):
        
        self.updateConnection()

        newPlaylistId = ""
        with self._playlistLock:
            if self._requestedPlaylistId != self._currentPlaylistId:
                self._currentPlaylistId = self._requestedPlaylistId
                newPlaylistId = self._currentPlaylistId

        if newPlaylistId != "":
            for i in range(2):
                try:
                    self.updateConnection()
                    self._client.clear()
                    
                    if self._currentPlaylistId == "":
                        self._client.stop()
                    else:
                        playlists = self._client.listplaylists()
                        print(str(playlists))
                        selectedPlaylist = next((p for p in playlists if p["playlist"].find(self._currentPlaylistId) > -1), None)
                        if selectedPlaylist != None:
                            self._client.load(selectedPlaylist["playlist"])
                            self._client.play(0)
                        else:
                            self._client.stop()
                    break
                except Exception as e:
                    if i == 0:
                        logging.error(str(e))

        try:
            status = self._client.status()
            #print (str(status))
            if self._currentPlaylistId != "":
                if 'song' in status and 'elapsed' in status:
                    self._state['playlistId'] = self._currentPlaylistId
                    self._state['songIdx'] = int(status['song'])
                    self._state['songTime'] = int(round(float(status['elapsed'])))
                elif 'state' in status and status['state'] == 'stop':
                    self._state['playlistId'] = ''
                    self._state['songIdx'] = 0
                    self._state['songTime'] = 0
                #self.saveState()
            elif not 'song' in status:
                self._client.stop()

        except Exception as e:
            logging.error(str(e))


    def cleanup(self):
        if self._client != None:
            try:
                self._client.close()
            except Exception as e:
                logging.warning(str(e))
            try:
                self._client.disconnect()
            except Exception as e:
                logging.warning(str(e))


    def setPlaylist(self, id: str) -> bool:
        with self._playlistLock:
            if self._currentPlaylistId == id:
                return
            self._requestedPlaylistId = id

    def isStopped(self):
        try:
            return self._client.status()['state'] == 'stop'
        except Exception as e:
            logging.warning(str(e))
        return True 

    def togglePlayPause(self):
        try:
            state = self._client.status()['state']
            if state == 'play':
                self._client.pause(1)
            if state == 'pause':
                self._client.pause(0)
        except Exception as e:
            logging.warning(str(e))
        return True 

    def skipToNextTrack(self):
        try:
            with self.cv:
                self.updateConnection()
                if self.isStopped() and len(self._client.playlistinfo()) > 0:
                    self._client.play(0)
                    return True
                elif "nextsong" in self._client.status():
                    self._client.next()
                    return not self.isStopped()
                return False
        except Exception as e:
            logging.error(str(e))
        return False

    def skipToPreviousTrack(self):
        try:
            with self.cv:
                self.updateConnection()
                status = self._client.status()
                currentTrack = int(status.get("song", "-1"))
                if currentTrack > 0:
                    self._client.previous()
                elif currentTrack == 0:
                    self._client.play(0)
            return currentTrack > 0 and not self.isStopped()
        except Exception as e:
            logging.error(str(e))
        return False
 
