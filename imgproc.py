from re import split
import cv2
import sys
from cv2.typing import MatLike
import numpy as np
import math


def main():
    img = cv2.imread("photos/render.png")
    if img is None:
        sys.exit()

    img = resize(img,0.4) 
    b,g,r = cv2.split(img)
    only_red = filter_col(150,110,r,g,b)
    contours, _ = cv2.findContours(only_red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    angle,radius,contour = get_angle(r,g,b)
    cnt = filter_contours(contours)


    img = cv2.drawContours(img,[contour],0,(255,0,0),3)
    img = cv2.drawContours(img,cnt,-1,(255,0,0),3)

    cv2.imshow("aoeu" ,only_red)
    cv2.imshow("img" ,img)


   # cv2.imshow("r_and_nb_ng", only_red)
   # cv2.imshow("back", backg)
   #
   # print("Angle:",angle_degs)
   # print("Dx,dy:",delta_x,delta_y)



    cv2.waitKey(0)

def detect_circle_1(img) :
    params = cv2.SimpleBlobDetector_Params()
    
    # Set Area filtering parameters
    params.filterByArea = True
    params.minArea = 10
    
    # Set Circularity filtering parameters
    params.filterByCircularity = True 
    params.minCircularity = 0.9
    
    # Set Convexity filtering parameters
    params.filterByConvexity = True
    params.minConvexity = 0.2
        
    # Set inertia filtering parameters
    
    # Create a detector with the parameters
    detector = cv2.SimpleBlobDetector_create(params)
        
    # Detect blobs
    keypoints = detector.detect(img)
    
    # Draw blobs on our image as red circles
    blank = np.zeros((1, 1)) 
    blobs = cv2.drawKeypoints(img, keypoints, blank, (0, 0, 255),
                              cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    return blobs

def do_and_draw_hough(img,ch):
    hough_circles = get_circles_hough(ch)
    if hough_circles is None:
        print("NONNE")

    if hough_circles is not None:                                 
        hough_circles = np.uint16(np.around(hough_circles))       
        for i in hough_circles[0,:]:                              
            cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2) 
    return img
    
def filter_col(keep_threshhold,remvo_threshold,ch_keep,ch_rm1,ch_rm2):

    _, keep_thr_ch = cv2.threshold(ch_keep, keep_threshhold, 255, cv2.THRESH_BINARY)
    _, rm_thr_1 = cv2.threshold(ch_rm1, remvo_threshold, 255, cv2.THRESH_BINARY)
    _, rm_thr_2 = cv2.threshold(ch_rm2, remvo_threshold, 255, cv2.THRESH_BINARY)


    not_b = cv2.bitwise_not(rm_thr_1)
    not_g = cv2.bitwise_not(rm_thr_2)

    r_and_not_b = cv2.bitwise_and(keep_thr_ch, not_b)
    r_and_not_g = cv2.bitwise_and(keep_thr_ch, not_g)

    return cv2.bitwise_and(r_and_not_b, r_and_not_g)



def filter_contours(contours):
    res = []
    for cnt in contours:
        perim = cv2.arcLength(cnt,closed=True)
        area = cv2.contourArea(cnt)                                           
        approx = cv2.approxPolyDP(cnt, 0.01 * perim, True) 

        radius_p = perim/(2*math.pi)
        radius_area = math.sqrt(area/math.pi)
        area_prediction = radius_p*radius_p*math.pi

        delta_area = area_prediction-area
        delta_radius = radius_area-radius_p
        ((x, y), radius) = cv2.minEnclosincountgCircle(cnt)
        print("Enclosing:",x,y,radius, radius_area,radius_area,radius_p)
        
        if len(approx) > 10 and len(approx) < 16:
            if delta_area < 200:
                if delta_radius < 1.0:
                    res.append(cnt)

    return res

def get_circles_hough(channel) -> MatLike:
    
#    blurred = cv2.medianBlur(channel, 25) #cv2.bilateralFilter(gray,10,50,50)
    blurred = channel
    
    minDist = 100
    param1 = 30 #500
    param2 = 50 #200 #smaller value-> more false circles
    minRadius = 0 
    maxRadius = 0 #10
    
    # docstring of HoughCircles: HoughCircles(image, method, dp, minDist[, circles[, param1[, param2[, minRadius[, maxRadius]]]]]) -> circles
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, minDist, param1=param1, param2=param2, minRadius=minRadius, maxRadius=maxRadius)
    print("Circles in fn:", circles)# prints :  Circles: [[387 231]]
    return circles



def get_angle(r,g,b):

    z = 54*50  # distance in meters * focal length(mm)

    _,screen_w = r.shape

    only_red = filter_col(150,100,r,g,b)

    contours, _ = cv2.findContours(only_red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    x,y,contour = get_coords(contours)

    if contour is  None:
        return -255,-255, contour
    print("Circle Contour found at x,y:",x,y)
    #print("With No fo sides:",len(cv2.approxPolyDP(contour, 0.04* cv2.arcLength(contour,True),True)))


    delta_x = (screen_w//2)-x

    angle_rads = math.atan((delta_x/z))
    angle_degs = angle_rads*(180/math.pi)

    radius = cv2.arcLength(contour,True)/(2*math.pi)
    return angle_degs,radius,contour


def get_coords(contours):
    print(len(contours))
    if len(contours) <= 0:
        return -1,-1,None
    greatest_area = 0
    largest_contour = contours[-1]
    x, y = 0, 0
    for _, contour in enumerate(contours):
       approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
       sides = len(approx)
       if sides > 10:
           area = cv2.contourArea(contour)
           if area > greatest_area:
               greatest_area = area
               largest_contour = contour


    M = cv2.moments(largest_contour[0])
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
