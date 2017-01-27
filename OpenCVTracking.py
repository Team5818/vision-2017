import VideoSteamClass as stream
import ControlHandler as controls
import numpy as np
import cv2
import time
import serial
import os

ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = .01,
    writeTimeout = .01,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False
    )

#Initialize Camera
vs = stream.WebcamVideoStream(src = 0).start()
cont = controls.ControlHandler(ser).start()

#HSV Threshholds
greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)
yellowLower = (15,86,6)
yellowUpper = (35,255,255)

threshLower = yellowLower
threshUpper = yellowUpper

proccessing = True

#Proccessing Loop
while proccessing:
    #Grab frame
    frame = vs.read()
    (width, height, c) = frame.shape
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    #Remove Small Particles
    mask = cv2.inRange(hsv, threshLower, threshUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    if len(cnts) > 0:
        c = max(cnts, key = cv2.contourArea)
        ((x,y),radius) = cv2.minEnclosingCircle(c)
        if radius > 10:
            cv2.circle(frame, (int(x),int(y)), int(radius), (0,255,255),2)
    else:
        x = 999
    
    #Send Data
    try:
        ser.flushInput()
        ser.flushOutput()
        ser.write("%+04d" % (int(x-240)) + "\n")
    except serial.SerialTimeoutException:
        print("timed out")

    #Display          
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    proccessing = cont.getQuitTracking()
    if key == ord('q'):
        proccessing = False

vs.release()
cv2.destroyAllWindows()

