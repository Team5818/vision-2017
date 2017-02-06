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

threshLower = greenLower
threshUpper = greenUpper

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
        cnts = sorted(cnts, key = cv2.contourArea);
        (x,y,w,h) = cv2.boundingRect(cnts[-1])
        if len(cnts) < 2:
            (x2,y2,w2,h2) = (0,0,0,0)
        else:
            (x2,y2,w2,h2) = cv2.boundingRect(cnts[-2])
        if w*h > 100 and w2*h2 > 100:
            cv2.rectangle(frame, (int(min(x,x2)),int(max(y,y2))),
                          (int(max(x+w, x2+w2)),int(min(y+h, y2 + h2))), (0,0,255),2)
            x_center = int((min(x,x2)+max(x+w, x2+w2))/2)
            y_center = int((min(y,y2)+max(y+h, y2+h2))/2)
            cv2.circle(frame, (x_center, y_center), 3, (0,0,255),2)
        elif max(w*h,w2*h2) > 100:
            cv2.rectangle(frame, (int(x),int(y)), (int(x+w),int(y+h)),(0,0,255),2)
            x_center = int(x + w/2)
            y_center = int(y + h/2)
            cv2.circle(frame, (x_center, y_center), 3, (0,0,255),2)
    else:
        x_center = 999

    #Send Data
    try:
        ser.flushInput()
        ser.flushOutput()
        ser.write("%+04d" % (int(x_center-240)) + "\n")
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
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        proccessing = False

vs.release()
cv2.destroyAllWindows()

