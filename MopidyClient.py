from mpd import MPDClient
from MopidyConfig import MopidyConfig
import RPi.GPIO as gpio
import os.path
import time
import json
import logging
import threading

RED = [True, False, False]
GREEN = [False, True, False]
BLUE = [False, False, True]
YELLOW = [True, True, False]
WHITE = [True, True, True]

class MopidyClient(MopidyConfig):

    _red_led = 25
    _green_led = 23
    _blue_led = 24

    def __init__(self):
        self._client = None
        self._currentPlaylistId = ""
        self._currentPlaylistName = ""
        self._stateFileContent = { 'playlistId': '', 'track': 0, 'time': 0 }        
        self.initRgbLed()
        self.loadStateFile()

    def initRgbLed(self):
        gpio.setmode(gpio.BCM)
        gpio.setup(self._red_led, gpio.OUT)        
        gpio.setup(self._green_led, gpio.OUT)        
        gpio.setup(self._blue_led, gpio.OUT)
        gpio.output(self._red_led, gpio.LOW)
        gpio.output(self._green_led, gpio.LOW)
        gpio.output(self._blue_led, gpio.LOW)

    def led_on(self, color):
        if color[0]:
            gpio.output(self._red_led, gpio.HIGH)
        if color[1]:
            gpio.output(self._green_led, gpio.HIGH)
        if color[2]:
            gpio.output(self._blue_led, gpio.HIGH)
    
    def led_off(self):
        gpio.output(self._red_led, gpio.LOW)
        gpio.output(self._green_led, gpio.LOW)
        gpio.output(self._blue_led, gpio.LOW)

    def connect(self):
        try:
            if self._client == None:
                self._client = MPDClient()
                self._client.timeout = 60
                self._client.idletimeout = None
                self._client.connect("localhost", 6600)
        except Exception as e:
            print("ERROR1: " + str(e))

    def disconnect(self):
        try:
            if self._client != None:
                self._client.close()
                self._client.disconnect()
        except Exception as e:
            print("ERROR2: " + str(e))
        self._client = None

    def updateStatus(self):
        result = {}
        try:
            self.connect()            

            result["playlistId"] = self._currentPlaylistId
            result["playlistName"] = self._currentPlaylistName.replace("[USB] ", "")

            status = self._client.status()
            
            result["tracks"] = int(status["playlistlength"])
            result["state"] = status["state"]

            if "song" in status:
                result["track"] = int(status["song"])
                result["time"] = float(status.get('elapsed', 0.0))                
                curr = self._client.currentsong()
                result["duration"] = float(curr["time"]) 
                result["album"] = curr.get("album", "").strip()
                result["artist"] = curr.get("artist", "").strip()
                result["title"] = curr.get("title", "").strip()
                if (result["track"] == result["tracks"] - 1) and (result["duration"] - result["time"] < 5):
                    self.updateStateFileContent(self._currentPlaylistId, 0, 0)
                else:
                    self.updateStateFileContent(self._currentPlaylistId, int(status["song"]), float(status.get('elapsed', 0.0)))            

        except Exception as e:
            print("ERROR3: " + str(e))
            result["error"] = str(e)
        return result
 
    def stop(self):
        try:
            self.connect()
            state = self._client.status()['state']
            if state == 'play' or state == 'pause':
                self._client.stop()
        except Exception as e:
            print("ERROR4: " + str(e))

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
            print("ERROR5: " + str(e))

    def skipToTrack(self, track):
        try:
            self.connect()
            status = self._client.status()
            tracks = int(status["playlistlength"])
            if tracks > 0:                
                track = max(0, min(track, tracks - 1))
                self._client.play(track)
        except Exception as e:
            print("ERROR6: " + str(e))

    def skipToNextTrack(self, count):
        try:
            if count <= 0:
                return
            self.connect()
            status = self._client.status()
            if "nextsong" in status and "song" in status:
                tracks = int(status["playlistlength"])
                track = int(status["song"]) + count
                track = min(track, tracks - 1)
                self._client.play(track)
            else:
                self.seek(count * 60)
        except Exception as e:
            print("ERROR7: " + str(e))

    def skipToPreviousTrack(self, count):
        try:
            if count <= 0:
                return
            self.connect()
            status = self._client.status()
            currentTrack = int(status.get("song", "-1"))
            if currentTrack > 0:
                track = max(0, currentTrack - count)
                self._client.play(track)
            else:
                self.seek(count * -60)
        except Exception as e:
            print("ERROR8: " + str(e))

    def skipToStart(self):
        try:
            self.connect()
            status = self._client.status()
            if int(status["playlistlength"]) > 0:
                self._client.play(0)
        except Exception as e:
            print("ERROR9: " + str(e))

    def seek(self, deltaInSeconds):
        try:
            self.connect()
            if self._client.status()['state'] == 'stop':
                return
            if deltaInSeconds > 0:
                status = self._client.status()
                if "nextsong" not in status:
                    currentTrack = int(status.get("song", "-1"))
                    if currentTrack > -1:
                        currentTrackTime = int(round(float(status.get('elapsed', 0.0))))
                        currentTrackDuration = int(self._client.playlistinfo()[currentTrack]['time'])
                        if currentTrackTime + deltaInSeconds >= currentTrackDuration - 1:
                            return
                self._client.seekcur("+" + str(deltaInSeconds))
            else:
                self._client.seekcur(str(deltaInSeconds))
        except Exception as e:
            print("ERROR10: " + str(e))

    def loadPlaylist(self, id):
        if self._currentPlaylistId == id and (id == "" or self._currentPlaylistName != ""):
            return
        newId = self._currentPlaylistId != id and self._currentPlaylistId != ""
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
                    self.led_on(GREEN)
                    self._currentPlaylistName = selectedPlaylist["playlist"]
                    self._client.clear()
                    self._client.load(selectedPlaylist["playlist"])
                    if self._stateFileContent.get("playlistId", "") == id:
                        track = self._stateFileContent.get("track", 0)
                        self._client.play(track)
                        if float(self._stateFileContent.get("time", 0)) > 5:
                            self._client.pause(1)
                            time.sleep(1) #hack
                            self._client.seek(track, str(self._stateFileContent.get("time", 0)))
                            self._client.pause(0)
                    else:
                        self._client.play(0)
                elif newId:
                    self.led_on(RED)
        except Exception as e:
            print("ERROR11: " + str(e))
            self.led_on(YELLOW)

        time.sleep(1)    
        self.led_off()

    def loadStateFile(self):
        for i in range(2):
            fname = 'state{0}.json'.format(i)
            try:
                if os.path.isfile(fname):
                    with open(fname, 'r') as f:
                        self._stateFileContent = json.load(f)
                        return
            except Exception as e:
                print("ERROR12: " + str(e))

    def updateStateFileContent(self, playlistId, track, time):
        if playlistId == "" or playlistId == None:
            return
        trackChanged = playlistId != self._stateFileContent.get("playlistId", "") or track != self._stateFileContent.get("track", 0)
        timeChanged = time != self._stateFileContent["time"]
        if trackChanged or int(time) % 5 == 0:
            self._stateFileContent["playlistId"] = playlistId
            self._stateFileContent["track"] = track
            self._stateFileContent["time"] = time
        if trackChanged or (timeChanged and int(time) % 60 == 0):
            self.saveStateFile()

    def saveStateFile(self):
        for i in range(2):
            try:
                fname = 'state{0}.json'.format(i)
                with open(fname, 'w') as f:
                    json.dump(self._stateFileContent, f)
            except Exception as e:
                print("ERROR13: " + str(e))
