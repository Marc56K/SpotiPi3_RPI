from UpdateThread import UpdateThread
import os.path
import time
import json
import logging
import threading
import serial
import struct
import base64

class SerialInterface(UpdateThread):

    STX = int(2) # ASCII: Start of Text
    ETX = int(3) # ASCII: End of Text

    callbackCv = threading.Condition()

    def __init__(self):
        UpdateThread.__init__(self, "SERIAL_INTERFACE-Thread")
        self.onMessageReceived = None   
        self.setSleepDuration(0.01)
        self._readStarted = False
        self._readHeaderBuffer = []
        self._readDataBuffer = []
        self._readDataSize = -1

    def startup(self):
        self._serial = serial.Serial(
            port = '/dev/serial0',
            baudrate = 115200,
            parity = serial.PARITY_EVEN,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1)

    def update(self):        
        while self._serial.inWaiting() > 0 and not self.shutdownRequested():
            rawByte = self._serial.read()
            b = struct.unpack("B", rawByte)[0]
            if b == self.STX or b == self.ETX:
                self._readStarted = b == self.STX                
                self._readHeaderBuffer = []
                self._readDataBuffer = [] 
                self._readDataSize = -1
            elif self._readStarted:
                if self._readDataSize < 0:
                    self._readHeaderBuffer.append(b)
                    if len(self._readHeaderBuffer) == 8:
                        encodedBytes = bytearray(self._readHeaderBuffer)
                        decodedBytes = base64.b64decode(encodedBytes)
                        self._readDataSize = int.from_bytes(decodedBytes, byteorder='little', signed=False)
                        print(str(self._readDataSize))
                else:
                    if len(self._readDataBuffer) < self._readDataSize:
                        self._readDataBuffer.append(b)
                    if len(self._readDataBuffer) == self._readDataSize:
                        encodedBytes = bytearray(self._readDataBuffer)
                        decodedBytes = base64.b64decode(encodedBytes)
                        msg = json.loads(decodedBytes)
                        self.eventMessageReceived(msg)

    def eventMessageReceived(self, msg):
        with self.callbackCv:
            if callable(self.onMessageReceived):
                self.onMessageReceived(msg)