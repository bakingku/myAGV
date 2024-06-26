import cv2
import numpy as np
from pymycobot.myagv import MyAgv
import threading
import time

agv = MyAgv("/dev/ttyAMA2", 115200)
cs, ps, gs, mt = 5, 2, 3, 1

def process_frame(frame):
    height, width, _ = frame.shape
    blueOn, current = 0, 0
    
    # ROI (Region of Interest) 
    RGB_roi_height = int(height * 0.4)
    RGB_roi_top = height - RGB_roi_height
    RGB_roi = frame[RGB_roi_top:, :]
    hsv_RGB = cv2.cvtColor(RGB_roi, cv2.COLOR_BGR2HSV)

    lower_red = np.array([160, 120, 100], dtype=np.uint8)
    upper_red = np.array([200, 255, 255], dtype=np.uint8)
    lower_green = np.array([50, 120, 100], dtype=np.uint8)
    upper_green = np.array([60, 255, 255], dtype=np.uint8)
    lower_blue = np.array([100, 120, 100], dtype=np.uint8)
    upper_blue = np.array([130, 255, 255], dtype=np.uint8)
    red_mask = cv2.inRange(hsv_RGB, lower_red, upper_red)
    green_mask = cv2.inRange(hsv_RGB, lower_green, upper_green) 
    blue_mask = cv2.inRange(hsv_RGB, lower_blue, upper_blue) 
   
    # rectangle around RGB detection zone 표시
    cv2.rectangle(RGB_roi, (0, 0), (width, RGB_roi_top), (255, 255, 255), 3)
    cv2.putText(RGB_roi, 'RGB Detection Zone', (10, RGB_roi_height-160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


    white_roi_height = int(height * 0.13)
    white_roi_top = height - white_roi_height
    white_roi = frame[white_roi_top:, :]

    cv2.line(white_roi, (width // 2, 0), (width // 2, white_roi_height), (0, 125, 125), 2)

    hsv_white = cv2.cvtColor(white_roi, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 200], dtype=np.uint8)
    upper_white = np.array([255, 30, 255], dtype=np.uint8)
    white_mask = cv2.inRange(hsv_white, lower_white, upper_white)

    kernel = np.ones((5,5),np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

    white_area = cv2.bitwise_and(white_roi, white_roi, mask=white_mask)

    gray = cv2.cvtColor(white_area, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    white_contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    yellow_roi_height = int(height * 0.13)
    yellow_roi_top = height - yellow_roi_height
    yellow_roi = frame[yellow_roi_top:, :]

    cv2.line(yellow_roi, (width // 2, 0), (width // 2, yellow_roi_height), (0, 125, 125), 2)

    hsv_yellow = cv2.cvtColor(yellow_roi, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([20, 120, 100], dtype=np.uint8)
    upper_yellow = np.array([40, 255, 255], dtype=np.uint8)
    yellow_mask = cv2.inRange(hsv_yellow, lower_yellow, upper_yellow)

    kernel = np.ones((5,5),np.uint8)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)

    yellow_area = cv2.bitwise_and(yellow_roi, yellow_roi, mask=yellow_mask)

    gray = cv2.cvtColor(yellow_area, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    yellow_contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    try:
        if len(white_contours) >= 1 and blueOn == 1:
            max_white_contour = max(white_contours, key=cv2.contourArea)
            cv2.drawContours(white_roi, [max_white_contour], -1, (0, 255, 0), 2)

            whiteM = cv2.moments(max_white_contour)
            if whiteM["m00"] != 0:
                ycx = int(whiteM["m10"] / whiteM["m00"])
                ycy = int(whiteM["m01"] / whiteM["m00"])

                cv2.circle(white_roi, (wcx, wcy), 5, (0, 0, 255), -1)

                center_line = width // 2
                bias, straight = 180, 150
                
                if center_line - straight <= ycx <= center_line + straight:
                    print("FORWARD, ycx:",ycx, ", ycy:",ycy)
                    current = 1
                    return "FORWARD"
                elif ycx <= center_line - bias:
                    print("LEFT, ycx:", ycx, ", ycy:", ycy)
                    current = 2
                    return "LEFT"
                elif ycx >= center_line + bias:
                    print("RIGHT, ycx:", ycx, ", ycy:", ycy)
                    current = 3
                    return "RIGHT"
                elif center_line - bias < ycx < center_line - straight:
                    print("PAN_LEFT, ycx:", ycx, ", ycy:", ycy)
                    current = 4
                    return "PAN_LEFT"
                elif center_line + straight < ycx < center_line + bias:
                    print("PAN_RIGHT, ycx:", ycx, ", ycy:", ycy)
                    current = 5
                    return "PAN_RIGHT"
        elif cv2.countNonZero(red_mask) > 0:
            print("Red detected!")
            blueOn = 0
            return "STOP"
        elif cv2.countNonZero(green_mask) > 0 and current == 1:
            print("Green detected!")
            return "SLOW"
        elif cv2.countNonZero(blue_mask) > 0:
            print("Blue detected!")
            blueOn = 1
            return "REBOOT" 
    except:
        if blueOn == 1:
            print("None Color")
            return "BACK"
    

def camera_thread():
    cap = cv2.VideoCapture(0) 
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera error")
            break
        
        result = process_frame(frame)
        if result:
            if result == "LEFT":
                agv.counterclockwise_rotation(cs)
            elif result == "PAN_LEFT":
                agv.pan_left(ps)
            elif result == "RIGHT":
                agv.clockwise_rotation(cs)
            elif result == "PAN_RIGHT":
                agv.pan_right(ps)
            elif result == "FORWARD":
                agv.go_ahead(gs)
            elif result == "BACK":
                agv.retreat(1)
            elif result == "STOP":
                agv.stop()
            elif result == "REBOOT":
                agv.restore()
            elif result == "SLOW":
                agv.go_ahead(gs-1)
                
        cv2.imshow("Frame", frame)
        
        key = cv2.waitKey(1)
        if  key & 0xFF == ord('q'):
            agv.stop()
            break
        elif key == ord('r'):
            agv.restore()

        '''
        # 배터리 정보 읽기
        try:
            battery_info = agv.get_battery_info()
            print("Battery Data:", battery_info[0])
        except Exception:
            print("Failed to get battery information:", Exception)
        '''
            
    cap.release()
    cv2.destroyAllWindows()

# camera thread start
camera_thread = threading.Thread(target=camera_thread)
camera_thread.start()
# Wait until the camera thread is terminated. 
camera_thread.join()
