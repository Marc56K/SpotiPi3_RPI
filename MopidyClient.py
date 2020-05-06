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

    def getStatus(self):
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
                result["album"] = curr["album"]
                result["artist"] = curr["artist"]
                result["title"] = curr["title"]

        except Exception as e:
            print(str(e))
            result["error"] = str(e)
        return result
 

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
                    self._client.play(0)
        except Exception as e:
            print(str(e))

