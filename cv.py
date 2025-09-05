import cv2
import sys
import numpy as np
import math
import random


def main():
    
    #img = cv2.imread("unnamed.png")
    #img = np.zeros((960,720,3),dtype='uint8')
    #cv2.rectangle(img,(100,50),(150,100),(128,52,178),thickness=cv2.FILLED)
    #cv2.rectangle(img,(500,550),(450,510),(128,52,198),thickness=cv2.FILLED)

    #cv2.circle(img,(100,180),radius,(0,0,220),cv2.FILLED)

    z = 54*50  # distance in meters * focal length(mm) 

    #radius = random.randint(5,20)
    img = cv2.imread("render_x.png")
    if img is None:
        return
    img = resize(img,1)
    screen_h,screen_w,_ = img.shape
    print("Img resized",screen_w,screen_h)

    backg = np.copy(img)
    #c_x = random.randint(0,screen_w-radius)
    #c_y = random.randint(0,screen_h-radius)

    #cv2.circle(img,(c_x,c_y),radius,(0,0,255),cv2.FILLED)
    
    if img is None:
        sys.exit()
    
    img = cv2.GaussianBlur(img, (17, 17), 0)
    b, g, r = cv2.split(img)
    _, r_thresh = cv2.threshold(r, 150, 255, cv2.THRESH_BINARY)
    _, g_thresh = cv2.threshold(g, 100, 255, cv2.THRESH_BINARY)
    _, b_thresh = cv2.threshold(b, 100, 255, cv2.THRESH_BINARY)
    
    
    not_b = cv2.bitwise_not(b_thresh)
    not_g = cv2.bitwise_not(g_thresh)
    
    r_and_not_b = cv2.bitwise_and(r_thresh, not_b)
    r_and_not_g = cv2.bitwise_and(r_thresh, not_g)
    
    only_red = cv2.bitwise_and(r_and_not_b, r_and_not_g)
    contours, _ = cv2.findContours(only_red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    x,y,contour = get_coords(contours)
    if contour is not None:
        cv2.drawContours(img,[contour],0,(0,255,0),2)
    print("Contour x,y:",x,y)
    

    delta_x = (screen_w//2)-x
    delta_y = (screen_h//2)-y

    angle_rads = math.atan((delta_x/z))
    angle_degs = angle_rads*(180/math.pi)
    new_x = x+delta_x
    new_y = y+delta_y

    radius = cv2.arcLength(contour,True)/(2*math.pi)
    print("Radius:",radius)

    cv2.circle(backg,(new_x,new_y),int(radius),(0,0,255),cv2.FILLED)
    
    cv2.imshow("Img", img)
    cv2.imshow("r_and_nb_ng", only_red)
    cv2.imshow("back", backg)

    print("Angle:",angle_degs)
    print("Dx,dy:",delta_x,delta_y)

    cv2.waitKey(0)
    
def get_coords(contours):
    print(len(contours))
    if len(contours) <= 0:
        return -1,-1,None
    greatest_area = 0
    largest_contour = contours[-1]
    x, y = 0, 0
    for _, contour in enumerate(contours):
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)

        # Detect shape
        sides = len(approx)
        if sides > 10:
            print(sides)
            area = cv2.contourArea(contour)
            if area > greatest_area:
                greatest_area = area
                largest_contour = contour


    M = cv2.moments(largest_contour)
    if M["m00"] != 0:
        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])

    return x,y,largest_contour

def resize(frame, scale=0.75):
    w = int(frame.shape[1] * scale)
    h = int(frame.shape[0] * scale)
    dim = (w,h)
    print("DIM  Resize:",dim)

    return cv2.resize(frame,dim,interpolation=cv2.INTER_AREA)
if __name__ == "__main__": 
    main()                 
