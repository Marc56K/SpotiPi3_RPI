from UpdateThread import UpdateThread
import os.path
import time
import json
import logging
import threading
import serial
import struct
import base64

class SerialInterface:

    STX = int(2) # ASCII: Start of Text
    ETX = int(3) # ASCII: End of Text

    def __init__(self):
        self._readStarted = False
        self._readBuffer = []
        self._readDataSize = -1
        self._serial = serial.Serial(
            port = '/dev/serial0',
            baudrate = 115200,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1)

    def write(self, dict):
        msg = json.dumps(dict, ensure_ascii = False)
        encodedData = base64.b64encode(msg.encode("utf-8"))
        encodedDataSize = int(len(encodedData)).to_bytes(4, byteorder="little", signed=True)
        encodedHeader = base64.b64encode(encodedDataSize)

        self._serial.write(struct.pack("B", self.STX))
        self._serial.write(encodedHeader)
        self._serial.write(encodedData)            
        self._serial.write(struct.pack("B", self.ETX))

    def read(self) -> []:
        result = []
        while self._serial.inWaiting() > 0:
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
                            self._readStarted = False
                            encodedBytes = bytearray(self._readBuffer)
                            decodedBytes = base64.b64decode(encodedBytes)
                            #print(str(decodedBytes))
                            msg = json.loads(decodedBytes)
                            result.append(msg)
        #print(str(result))                        
        return result