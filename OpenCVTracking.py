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
vsgears = stream.WebcamVideoStream(src = 0).start()
vstape = stream.WebcamVideoStream(src = 1).start()


#HSV Threshholds
greenLower = (70, 100, 100)
greenUpper = (90, 255, 255)

yellowLower = (20, 100,100)
yellowUpper = (35,255,255)

gears = True
proccessing = True

#Proccessing Loop
try:
    while proccessing:
        if gears:
            vs = vsgears
            threshLower = yellowLower
            threshUpper = yellowUpper
        else:
            vs = vstape
            threshLower = greenLower
            threshUpper = greenUpper
        #Grab frame
        frame = vs.read().copy()
        (width, height, c) = frame.shape
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        #Remove Small Particles
        mask = cv2.inRange(hsv, threshLower, threshUpper)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]
        if not gears:
            if len(cnts) > 0:
                x_center = 999
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
        else:
             if len(cnts) > 0:
                x_center = 999
                c = max(cnts, key = cv2.contourArea)
                if len(c) > 5:
                    rect = cv2.minAreaRect(c)
                    ((x,y),(w,h), ang) = rect
                    if w*h > 100:
                        cv2.ellipse(frame, rect, (0,255,255),2)
                        cv2.circle(frame,(int(x),int(y)), 3, (0,255,0),2)
                        x_center = x
             else:
                 x_center = 0
                 
        #Send Data
        try:
            ser.flushOutput()
            ser.write("%+04d" % (int(x_center-160)) + "\n")
        except serial.SerialTimeoutException:
            print("timed out")
        try:
            if ser.inWaiting() > 0:
                read = str(ser.read(1))
                ser.flushInput()
                if "s" in read:
                    os.system("sudo shutdown -h now")
                elif "q" in read:
                    proccessing = False
                elif "w" in read:
                    gears = not gears
                elif "l" in read:
                    os.system("v4l2-ctl -d /dev/video1 -c exposure_absolute=5")
                elif "h" in read:
                    os.system("v4l2-ctl -d /dev/video1 -c exposure_absolute=156")
                print(read)
        except serial.SerialTimeoutException:
            pass
        
        #Display          
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            proccessing = False
        if key == ord('x'):
            gears = not gears
        elif key == ord('l'):
            os.system("v4l2-ctl -d /dev/video1 -c exposure_auto=1 -c exposure_absolute=5")
        elif key == ord('h'):
            os.system("v4l2-ctl -d /dev/video1 -c exposure_auto=1 -c exposure_absolute=156")
finally:
    vstape.release()
    vsgears.release()
    cv2.destroyAllWindows()



