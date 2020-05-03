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
        self._readBuffer = []
        self._readDataSize = -1

    def startup(self):
        self._serial = serial.Serial(
            port = '/dev/serial0',
            baudrate = 115200,
            parity = serial.PARITY_EVEN,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1)

    def write(self, dict):
        with self.callbackCv:
            msg = json.dumps(dict)
            encodedData = base64.b64encode(msg.encode("utf-8"))
            encodedDataSize = int(len(encodedData)).to_bytes(4, byteorder="little", signed=True)
            encodedHeader = base64.b64encode(encodedDataSize)

            self._serial.write(struct.pack("B", self.STX))
            self._serial.write(encodedHeader)
            self._serial.write(encodedData)            
            self._serial.write(struct.pack("B", self.ETX))

    def update(self):
        while self._serial.inWaiting() > 0 and not self.shutdownRequested():
            numBytes = min(self._serial.inWaiting(), 128)
            rawBytes = self._serial.read(numBytes)
            for i in range(numBytes):
                b = struct.unpack_from("B", rawBytes, i)[0]
                if b == self.STX or b == self.ETX:
                    self._readStarted = b == self.STX
                    self._readBuffer = []
                    self._readDataSize = -1
                elif self._readStarted:
                    if self._readDataSize < 0:
                        self._readBuffer.append(b)
                        if len(self._readBuffer) == 8:
                            encodedBytes = bytearray(self._readBuffer)
                            decodedBytes = base64.b64decode(encodedBytes)
                            self._readDataSize = int.from_bytes(decodedBytes, byteorder='little', signed=True)
                            #print(str(self._readDataSize))
                            self._readBuffer = []
                    else:
                        if len(self._readBuffer) < self._readDataSize:
                            self._readBuffer.append(b)
                        if len(self._readBuffer) == self._readDataSize:
                            encodedBytes = bytearray(self._readBuffer)
                            decodedBytes = base64.b64decode(encodedBytes)
                            #print(str(decodedBytes))
                            msg = json.loads(decodedBytes)
                            self._readStarted = False
                            self.eventMessageReceived(msg)

    def eventMessageReceived(self, msg):
        with self.callbackCv:
            if callable(self.onMessageReceived):
                self.onMessageReceived(msg)