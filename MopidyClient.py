from mpd import MPDClient
from MopidyConfig import MopidyConfig
import os.path
import time
import json
import logging
import threading

class MopidyClient(MopidyConfig):

    def __init__(self):
        self._client = None
        self._currentPlaylistId = ""
        self._currentPlaylistName = ""
        self._stateFileContent = { 'playlistId': '', 'track': 0 }
        self.loadStateFile()

    def connect(self):
        try:
            if self._client == None:
                self._client = MPDClient()
                self._client.timeout = 60
                self._client.idletimeout = None
                self._client.connect("localhost", 6600)
        except Exception as e:
            print(str(e))

    def disconnect(self):
        try:
            if self._client != None:
                self._client.close()
                self._client.disconnect()
        except Exception as e:
            print(str(e))
        self._client = None

    def updateStatus(self):
        result = {}
        try:
            self.connect()            

            result["playlistId"] = self._currentPlaylistId
            result["playlistName"] = self._currentPlaylistName

            status = self._client.status()
            
            result["tracks"] = int(status["playlistlength"])
            result["state"] = status["state"]

            if "song" in status:
                result["track"] = int(status["song"])
                result["time"] = float(status["elapsed"])                
                curr = self._client.currentsong()
                result["duration"] = float(curr["time"]) 
                result["album"] = curr["album"]
                result["artist"] = curr["artist"]
                result["title"] = curr["title"]
                if (result["track"] == result["tracks"] - 1) and (result["duration"] - result["time"] < 5):
                    self.saveStateFile(self._currentPlaylistId, 0)
                else:
                    self.saveStateFile(self._currentPlaylistId, int(status["song"]))            

        except Exception as e:
            print(str(e))
            result["error"] = str(e)
        return result
 
    def stop(self):
        try:
            self.connect()
            state = self._client.status()['state']
            if state == 'play' or state == 'pause':
                self._client.stop()
        except Exception as e:
            print(str(e))

    def togglePlayPause(self):
        try:
            self.connect()
            state = self._client.status()['state']
            if state == 'play':
                self._client.pause(1)
            elif state == 'pause':
                self._client.pause(0)
            else:
                self._client.play(0)
        except Exception as e:
            print(str(e))

    def skipToTrack(self, track):
        try:
            self.connect()
            status = self._client.status()
            tracks = int(status["playlistlength"])
            if tracks > 0:                
                track = max(0, min(track, tracks - 1))
                self._client.play(track)
        except Exception as e:
            print(str(e))

    def skipToNextTrack(self, count):
        try:
            self.connect()
            status = self._client.status()
            if count > 0 and "nextsong" in status and "song" in status:
                tracks = int(status["playlistlength"])
                track = int(status["song"]) + count
                track = min(track, tracks - 1)
                self._client.play(track)
        except Exception as e:
            print(str(e))

    def skipToPreviousTrack(self, count):
        try:
            self.connect()
            status = self._client.status()
            currentTrack = int(status.get("song", "-1"))
            if count > 0 and currentTrack > 0:
                track = max(0, currentTrack - count)
                self._client.play(track)
        except Exception as e:
            print(str(e))

    def skipToStart(self):
        try:
            self.connect()
            status = self._client.status()
            if int(status["playlistlength"]) > 0:
                self._client.play(0)
        except Exception as e:
            print(str(e))

    def loadPlaylist(self, id):
        if self._currentPlaylistId == id and (id == "" or self._currentPlaylistName != ""):
            return

        self._currentPlaylistId = id
        prevPlaylistName = self._currentPlaylistName
        self._currentPlaylistName = ""
        try:
            self.connect()
            if prevPlaylistName != "":
                self._client.clear()
            if id != "":
                playlists = self._client.listplaylists()
                selectedPlaylist = next((p for p in playlists if p["playlist"].find(id) > -1), None)
                if selectedPlaylist != None:
                    self._currentPlaylistName = selectedPlaylist["playlist"]
                    self._client.clear()
                    self._client.load(selectedPlaylist["playlist"])
                    if self._stateFileContent.get("playlistId", "") == id:
                        self._client.play(self._stateFileContent.get("track", 0))
                    else:
                        self._client.play(0)
        except Exception as e:
            print(str(e))

    def loadStateFile(self):
        for i in range(2):
            fname = 'state{0}.json'.format(i)
            try:
                if os.path.isfile(fname):
                    with open(fname, 'r') as f:
                        self._stateFileContent = json.load(f)
                        return
            except Exception as e:
                print(str(e))

    def saveStateFile(self, playlistId, track):
        if playlistId == "" or playlistId == None:
            return
        if playlistId != self._stateFileContent.get("playlistId", "") or track != self._stateFileContent.get("track", 0):
            self._stateFileContent["playlistId"] = playlistId
            self._stateFileContent["track"] = track
            for i in range(2):
                try:
                    fname = 'state{0}.json'.format(i)
                    with open(fname, 'w') as f:
                        json.dump(self._stateFileContent, f)
                except Exception as e:
                    print(str(e))
