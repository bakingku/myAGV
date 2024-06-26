import socket
import struct
import cv2
import pickle
from myagv import MyAgv
import numpy as np


# bot = Rosmaster()   # add
MA = MyAgv('/dev/ttyAMA2', 115200)

# VIDSRC = 'v4l2src device=/dev/video0 ! video/x-raw,width=160,height=120,framerate=20/1 ! videoscale ! videoconvert ! jpegenc ! appsink'
# cap=cv2.VideoCapture(VIDSRC, cv2.CAP_GSTREAMER)
cap = cv2.VideoCapture(0)

HOST = ''
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

server.bind((HOST, PORT))
print('Socket bind complete')

server.listen(10)
print('Socket now listening')

server_cam, addr = server.accept()
print('New Client.')

flag_exit = False

try:

	while True:	

		cmd_byte = server_cam.recv(1)
		cmd = struct.unpack('!B', cmd_byte)
		# print(cmd[0])
		if cmd[0]==12 :	
		
			# capture camera data
			ret,frame=cap.read()
			# print(frame.shape)

			# Serialize frame
			data = pickle.dumps(frame)
			# print(len(data))

			# send sensor + camera data
			data_size = struct.pack("!L", len(data)) 
			server_cam.sendall(data_size + data)
			
except KeyboardInterrupt:
	pass
except ConnectionResetError:
	pass
except BrokenPipeError:
	pass
except:
	pass

flag_exit = True
	
server_cam.close()
server.close()
