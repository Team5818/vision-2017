import time
import serial

ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    writeTimeout = 1,
    xonxoff = False,
    rtscts = False,
    dsrdtr = False
    )

x = 0
while True:
    try:
        ser.flushInput()
        ser.flushOutput()
        ser.write("%06d \n" % (x))
        time.sleep(.016)
        x = x+1
    except serial.SerialTimeoutException:
        print("timed out")
    
    
                             
