import cv2
import numpy as np
import threading
import time
from pymycobot.myagv import MyAgv

agv = MyAgv("/dev/ttyAMA2", 115200)

class CameraThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cap = cv2.VideoCapture(0)
        self.stopped = False

    def run(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                print("Camera error")
                break

            result = process_frame(frame)
            if result:
                print(result)
                if result == "LEFT":
                    agv.counterclockwise_rotation(4)
                elif result == "FORWARD":
                    agv.go_ahead(10)
                elif result == "RIGHT":
                    agv.clockwise_rotation(4)
                elif result == "PURPLE":
                    agv.pan_left(7)
                # elif result == "BLUE":
                #     agv.pan_right(7)
                elif result == "RED":
                    agv.stop()
                    time.sleep(1)
                    print("Exiting script...")
                    exit(0)
                else:
                    agv.counterclockwise_rotation(1)

            cv2.imshow("Frame", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def stop(self):
        self.stopped = True
        self.cap.release()
        cv2.destroyAllWindows()

def process_frame(frame):
    height, width, _ = frame.shape
    section_width = int(width / 5)  # Calculate the width of each section
    section_height = int(height / 6)
    roi_top = height - section_height
    crop_img = frame[roi_top:, :]

    # Draw vertical lines to divide the ROI into five sections
    for i in range(1, 6):
        cv2.line(crop_img, (section_width * i, 0), (section_width * i, section_height), (0, 255, 0), 2)

    hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([0,0,200], dtype=np.uint8)
    upper_yellow = np.array([255,30,255], dtype=np.uint8)

    lower_red = np.array([0,101,139], dtype=np.uint8)
    upper_red = np.array([5,210,244], dtype=np.uint8)

    lower_purple = np.array([103,79,75], dtype=np.uint8)
    upper_purple = np.array([124,173,161], dtype=np.uint8)

    # lower_blue = np.array([45,26,0], dtype=np.uint8)
    # upper_blue = np.array([77,75,135], dtype=np.uint8)

    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    red_mask = cv2.inRange(hsv, lower_red, upper_red)
    purple_mask = cv2.inRange(hsv, lower_purple, upper_purple)
    # blue_mask = cv2.inRange(hsv, lower_blue, upper_purple)
    
    # Convert to grayscale and apply thresholding
    # gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_red, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_purple, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # contours_blue, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(crop_img, contours_red, -1, (128, 0, 128), 2)
    cv2.drawContours(crop_img, contours_purple, -1, (128, 0, 128), 2)
    # cv2.drawContours(crop_img, contours_blue, -1, (128, 0, 128), 2)

    total_area1 = total_area2 = total_area3 = 0

    

    if len(contours_purple) > 0:
        total_area1 = sum(cv2.contourArea(cnt) for cnt in contours_purple)
        print(total_area1)

    if len(contours_red) > 0:
        total_area2 = sum(cv2.contourArea(cnt) for cnt in contours_red)
        print(total_area2)

    # if len(contours_blue) > 0:
    #     total_area3 = sum(cv2.contourArea(cnt) for cnt in contours_blue)
    #     print(total_area3)

        # if total_area >= 1000:
        #     perform_route_action()
        #     return "PURPLE"
    

    # Contour detection and processing
    if total_area1 >= 3000 and total_area1 >= total_area2 and total_area1 >= total_area3:
       return "PURPLE"
    elif total_area2 >= 3000 and total_area2 >= total_area1 and total_area2 >= total_area3:
       return "RED"
    # elif total_area3 >= 10000 and total_area3 >= total_area1 and total_area3 >= total_area2:
    #    return "BLUE"
    elif len(contours) >= 1:
        max_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(crop_img, [max_contour], -1, (0, 255, 0), 2)

        # Calculate the center of the object
        M = cv2.moments(max_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])

            center_lines = [section_width * (2 * i + 1) // 2 for i in range(5)]  # Calculate center lines for each section
            if 0 <= cx < section_width:
                return "LEFT"
            elif section_width <= cx < 4 * section_width:
                return "FORWARD"
            elif 4 * section_width <= cx < width:
                return "RIGHT"
            
    return None


camera_thread = CameraThread()
camera_thread.start()

# Wait for the camera thread to finish
camera_thread.join()

# Release resources
camera_thread.stop()