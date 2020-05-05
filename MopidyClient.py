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
        self._currentPlaylistId = None
        self._currentPlaylistName = ""

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

    def skipToNextTrack(self, count):
        try:
            self.connect()
            for _ in range(count):
                if "nextsong" in self._client.status():
                    self._client.next()
        except Exception as e:
            print(str(e))

    def skipToPreviousTrack(self, count):
        try:
            self.connect()
            for _ in range(count):
                status = self._client.status()
                currentTrack = int(status.get("song", "-1"))
                if currentTrack > 0:
                    self._client.previous()
        except Exception as e:
            print(str(e))

    def skipToStart(self):
        try:
            self.connect()
            self._client.play(0)
        except Exception as e:
            print(str(e))

    def loadPlaylist(self, id):
        if id != "" and self._currentPlaylistId == id and self._currentPlaylistName != "":
            return
        if id == "" and self._currentPlaylistId == id:
            return
        self._currentPlaylistId = id
        self._currentPlaylistName = ""
        try:
            self.connect()  
            self._client.clear()
            if self._currentPlaylistId != "":
                playlists = self._client.listplaylists()
                selectedPlaylist = next((p for p in playlists if p["playlist"].find(id) > -1), None)
                if selectedPlaylist != None:
                    self._currentPlaylistName = selectedPlaylist["playlist"]
                    self._client.load(selectedPlaylist["playlist"])
                    self._client.play(0)
        except Exception as e:
            print(str(e))
    
    def getStatus(self):
        try:
            self.connect()
            result = {}

            result["playlist"] = self._currentPlaylistName

            stat = self._client.status()
            
            result["tracks"] = int(stat["playlistlength"])            
            result["state"] = stat["state"]

            if "song" in stat:
                result["track"] = int(stat["song"])
                result["time"] = float(stat["elapsed"])
                curr = self._client.currentsong()
                result["album"] = curr["album"]
                result["artist"] = curr["artist"]
                result["title"] = curr["title"]
            else:
                result["track"] = -1
                result["time"] = 0
                result["album"] = ""
                result["artist"] = ""
                result["title"] = ""       

            return result
        except Exception as e:
            print(str(e))
        return ""
 
