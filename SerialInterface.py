from UpdateThread import UpdateThread
import os.path
import time
import json
import logging
import threading
import serial

class SerialInterface(UpdateThread):

    def __init__(self):
        UpdateThread.__init__(self, "SERIAL_INTERFACE-Thread")       
        self._readBuffer = "" 
        self.setSleepDuration(0.001)

    def startup(self):
        self._serial = serial.Serial(
            port = '/dev/serial0',
            baudrate = 115200,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1)

    def update(self):
        commands = []
        while self._serial.inWaiting() > 0 and not self.shutdownRequested() and len(commands) < 8:
            self._readBuffer = self._readBuffer + self._serial.read(1).decode('utf-8')
            try:
                commands.append(json.loads(self._readBuffer))
                self._readBuffer = ""
            except ValueError:
                pass
        for cmd in commands:
            print("SERIAL-IN: " + str(cmd))
        