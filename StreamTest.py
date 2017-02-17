import socket
import cv2

cam = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cam.bind((socket.gethostname(), 1180))
vs = cv2.VideoCapture(0)
cam.listen(5)
magic_num = bytearray()
magic_num.append(0x01)
magic_num.append(0x00)
magic_num.append(0x00)
magic_num.append(0x00)


while True:
    (grabbed, frame) = vs.read()
    jpeg_frame = cv2.imencode(".jpeg", frame)
    (clientsock,address) = cam.accept()
    clientsocket.send(magic_num)
    clientsocket.send(len(jpeg_frame))
    clientsocket.send(jpeg_frame)
    clinesocket.flush()
    

