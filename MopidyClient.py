from UpdateThread import UpdateThread
from mpd import MPDClient
import os.path
import time
import json
import logging
import threading

class MopidyClient(UpdateThread):

    _currentPlaylistId = ""
    _client = None

    def __init__(self):
        UpdateThread.__init__(self, "MOPIDY_CLIENT-Thread")

        self._state = { 'playlistId': '', 'songIdx': 0, 'songTime': 0 }
        self.loadState()
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
        self._client.timeout = 2
        self._client.idletimeout = None
    
    def connect(self, timeout):
        start = time.time()
        while not self._shutdown:
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
                self.saveState()
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
        with self.cv:
            for i in range(2):
                try:
                    self.updateConnection()
                    self._client.clear()
                    self._currentPlaylistId = ""
                    if id == "":
                        self._client.stop()
                        return True
                    else:
                        playlists = self._client.listplaylists()
                        selectedPlaylist = next((p for p in playlists if p["playlist"].find(id) > -1), None)
                        if selectedPlaylist != None:
                            logging.debug(selectedPlaylist["playlist"])
                            self._client.load(selectedPlaylist["playlist"])
                            self._currentPlaylistId = id
                            if self._state['playlistId'] != self._currentPlaylistId:
                                self._client.play(0)
                            else:
                                try:
                                    self._client.play(self._state['songIdx'])
                                    time.sleep(0.1) #hack
                                    self._client.seek(self._state['songIdx'], str(self._state['songTime']))
                                except Exception as e:
                                    logging.warning(str(e))
                                    self._client.play(0)
                            time.sleep(2) #hack
                            return True
                        self._client.stop()
                        return False
                except Exception as e:
                    if i == 0:
                        logging.error(str(e))
                    else:
                        raise e
        return False

    def isStopped(self):
        try:
            return self._client.status()['state'] == 'stop'
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

    def seek(self, deltaInSeconds):
        try:
            with self.cv:
                if self.isStopped():
                    return False
                self.updateConnection()
                if deltaInSeconds > 0:
                    status = self._client.status()
                    if "nextsong" not in status:
                        currentTrack = int(status.get("song", "-1"))
                        if currentTrack > -1:
                            currentTrackTime = int(round(float(status['elapsed'])))
                            currentTrackDuration = int(self._client.playlistinfo()[currentTrack]['time'])
                            if currentTrackTime + deltaInSeconds >= currentTrackDuration - 1:
                                return False
                    self._client.seekcur("+" + str(deltaInSeconds))
                else:
                    self._client.seekcur(str(deltaInSeconds))
            return not self.isStopped()
        except Exception as e:
            logging.error(str(e))
        return False
 
