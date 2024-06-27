import cv2
import numpy as np
from pymycobot.myagv import MyAgv
import threading
import time

agv = MyAgv("/dev/ttyAMA2", 115200)
agv.stop()
agv.restore()