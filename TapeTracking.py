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
    timeout = 0,
    writeTimeout = 0,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False
    )

#Initialize Camera
vs = stream.WebcamVideoStream(src = 0).start()

#HSV Threshholds
greenLower = (70, 100, 50)
greenUpper = (80, 255, 100)
yellowLower = (15,86,6)
yellowUpper = (35,255,255)

threshLower = yellowUpper
threshUpper = yellowLower

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
    if len(cnts) > 1:
        cnts = sorted(cnts, key = cv2.contourArea);
        (x,y,w,h) = cv2.boundingRect(cnts[-1])
        (x2,y2,w2,h2) = cv2.boundingRect(cnts[-2])
        if w*h > 10:
            cv2.rectangle(frame, (int(x),int(y)), (int(w),int(h)), (0,255,255),2)
        if w2*h2 > 100:
            cv2.rectangle(frame, (int(x2),int(y2)), (int(w2),int(h2)), (0,255,255),2)
    else:
        x = 999
    
    #Send/Receive Data
    try:
        ser.flushInput()
        ser.flushOutput()
        ser.write("%+04d" % (int(x-240)) + "\n")
    except serial.SerialTimeoutException:
        print("timed out")
        
    try:
        read = ser.readline()
        if read == "s":
            os.system("sudo shutdown -h now")
        elif read == "q":
            proccessing = False
    except serial.SerialTimeoutException:
        pass
    

    #Display          
    cv2.imshow("Frame",mask)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        proccessing = False
    elif key == ord('l'):
        os.system("v4l2-ctl -c exposure_absolute=25")
    elif key == ord('d'):
        os.system("v4l2-ctl -c exposure_absolute=5")
        
vs.release()
cv2.destroyAllWindows()

