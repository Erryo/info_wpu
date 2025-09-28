# Code modified from github.com/tanat44/PingpongBallTracker

import re
import cv2
import numpy as np
import imutils


class ColorThreshold():

    def __init__(self,h_min1=0, h_max1=10, h_min2=160, h_max2=180, s_min=100, s_max=255, v_min=50, v_max=255):
        # Lower red range
        self.h_min1 = h_min1
        self.h_max1 = h_max1
        # Upper red range
        self.h_min2 = h_min2
        self.h_max2 = h_max2

        self.s_min = s_min
        self.s_max = s_max
        self.v_min = v_min
        self.v_max = v_max

    
    def getLowerRed(self):
        return (self.h_min1, self.s_min, self.v_min), (self.h_max1, self.s_max, self.v_max)

    def getUpperRed(self):
        return (self.h_min2, self.s_min, self.v_min), (self.h_max2, self.s_max, self.v_max)

class BallTracker:
    def __init__(self,target = (0,0)):
        # Two ranges for red (since it wraps in HSV)
        self.lower_red1 = np.array([0, 100, 100])
        self.kernel = np.ones((3, 3), np.uint8)
        self.color_thr = ColorThreshold()
        self.target = target
        self.dx = 0
        self.dy = 0
        self.circle_x = 0 
        self.circle_y = 0 
        self.circle_radius = 0
    def find(self, frame):
        frame = np.copy(frame)
        self.height, self.width, c  = frame.shape

        blurred = cv2.GaussianBlur(frame, (13, 13), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        lower1, upper1 = self.color_thr.getLowerRed()
        lower2, upper2 = self.color_thr.getUpperRed()
        
        lower1 = np.array(lower1, dtype=np.uint8)
        upper1 = np.array(upper1, dtype=np.uint8)
        lower2 = np.array(lower2, dtype=np.uint8)
        upper2 = np.array(upper2, dtype=np.uint8)

        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)

        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.bitwise_or(mask1, mask2)

        mask = cv2.erode(mask, self.kernel, iterations=2)
        mask = cv2.dilate(mask, self.kernel, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = (0,0)
        radius = 0
        

        ball_cnts = []
        if len(cnts) > 0:
            for c in cnts:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                if 20 < radius < 40:
                    ball_cnts.append(c)

        if len(ball_cnts) > 0:
            c = max(ball_cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            self.circle_x = x
            self.circle_y = y
            self.circle_radius = radius
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            cv2.circle(frame, (int(x), int(y)), int(radius),(0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            cv2.putText(frame, f"R: {int(radius)}", 
                (int(x) - 40, int(y) - 10),  # position slightly above the circle
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, (255, 0, 0), 2)  # font scale and color


        # DRAW ROBOT
            
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

        return True, frame, mask
    def calculate(self,frame):
        success,_,_ = self.find(frame)
        if not success:
            return False
        self.dx = self.target[0]-self.circle_x
        self.dy = self.target[1]-self.circle_y
        return True
