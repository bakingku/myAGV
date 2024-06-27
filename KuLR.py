import cv2
import numpy as np
from pymycobot.myagv import MyAgv
import threading
import time

agv = MyAgv("/dev/ttyAMA2", 115200)
cs, ps, gs, mt = 5, 2, 3, 1

def process_frame(frame):
    height, width, _ = frame.shape
    greenOn = 1

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

    yellow_roi_height = int(height * 0.1)
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

    gray_yellow = cv2.cvtColor(yellow_area, cv2.COLOR_BGR2GRAY)
    _, binary_image_yellow = cv2.threshold(gray_yellow, 128, 255, cv2.THRESH_BINARY)

    yellow_contours, _ = cv2.findContours(binary_image_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    try:
        if len(white_contours) >= 1 and greenOn == 1:
            max_white_contour = max(white_contours, key=cv2.contourArea)
            cv2.drawContours(white_roi, [max_white_contour], -1, (0, 255, 0), 2)

            whiteM = cv2.moments(max_white_contour)
            if whiteM["m00"] != 0:
                wcx = int(whiteM["m10"] / whiteM["m00"])
                wcy = int(whiteM["m01"] / whiteM["m00"])

                cv2.circle(white_roi, (wcx, wcy), 5, (0, 0, 0), -1)

                center_line = width // 2
                bias, straight = 100, 50

                if center_line - straight <= wcx <= center_line + straight:
                    print("FORWARD, wcx:",wcx, ", wcy:",wcy)
                    return "FORWARD"
                elif wcx <= center_line - bias:
                    print("LEFT, wcx:", wcx, ", wcy:", wcy)
                    return "LEFT"
                elif wcx >= center_line + bias:
                    print("RIGHT, wcx:", wcx, ", wcy:", wcy)
                    return "RIGHT"
                elif center_line - bias < wcx < center_line - straight:
                    print("PAN_LEFT, wcx:", wcx, ", wcy:", wcy)
                    return "PAN_LEFT"
                elif center_line + straight < wcx < center_line + bias:
                    print("PAN_RIGHT, wcx:", wcx, ", wcy:", wcy)
                    return "PAN_RIGHT"
        elif cv2.countNonZero(red_mask) > 0:
            print("Red detected!")
            greenOn = 0
            return "STOP"
        elif cv2.countNonZero(green_mask) > 0:
            print("Green detected!")
            greenOn = 1
            return "REBOOT"
        '''
        elif len(yellow_contours) >= 1 and greenOn == 1 and len(white_contours) == None:
            max_yellow_contour = max(yellow_contours, key=cv2.contourArea)
            cv2.drawContours(yellow_roi, [max_yellow_contour], -1, (0, 255, 0), 2)

            yellowM = cv2.moments(max_yellow_contour)
            if whiteM["m00"] != 0:
                ycx = int(yellowM["m10"] / yellowM["m00"])
                ycy = int(yellowM["m01"] / yellowM["m00"])

                cv2.circle(white_roi, (ycx, ycy), 5, (0, 255, 0), -1)

                center_line = width // 2

                if 200 <= ycx:
                    print("Yellow detected!")
                    greenOn = 0
                    return "STOP"
        '''
    except:
        if greenOn == 1:
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
                time.sleep(1)
                #agv.go_vector(1,0,70)
            elif result == "PAN_LEFT":
                agv.pan_left(ps,1)
                time.sleep(1)
            elif result == "RIGHT":
                agv.clockwise_rotation(cs)
                time.sleep(1)
                #agv.go_vector(1,0,-70)
            elif result == "PAN_RIGHT":
                agv.pan_right(ps)
                time.sleep(1)
            elif result == "FORWARD":
                agv.go_ahead(gs)
                time.sleep(1)
            elif result == "BACK":
                agv.retreat(1)
            elif result == "STOP":
                agv.stop()
            elif result == "REBOOT":
                agv.restore()
            elif result == "SLOW":
                agv.go_ahead(gs-1)
                time.sleep(1)

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
