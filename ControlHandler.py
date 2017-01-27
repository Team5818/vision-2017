from threading import Thread
import cv2
import serial
import os

class ControlHandler:
    def __init__(self, ser):
        self.ser = ser
        self.stopped = False
        self.quitTracking = True

    def start(self):
        Thread(target = self.update, args = ()).start()
        return self

    def update(self):
        while True:      
            try:
                read = self.ser.readline()
                if read == "s":
                    os.system("sudo shutdown -h now")
                elif read == "q":
                    self.quitTracking = False
            except serial.SerialTimeoutException:
                pass
                
    def getQuitTracking(self):
        return self.quitTracking
    
    def stop(self):
        self.stopped = True
 
