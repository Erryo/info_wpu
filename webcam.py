import  sys
import cv2
import numpy as np

import imgproc
cv2.namedWindow("mine")
cv2.namedWindow("only_red")
vc = cv2.VideoCapture(0)

frame = None
if vc.isOpened(): # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

if frame is None:
    sys.exit()

greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)

while rval:
    if frame is None:
        break

    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
         cv2.CHAIN_APPROX_SIMPLE)
    center = None
    # only proceed if at least one contour was found
    if len(cnts) > 0:
    	# find the largest contour in the mask, then use
    	# it to compute the minimum enclosing circle and
    	# centroid
    	c = max(cnts, key=cv2.contourArea)
    	((x, y), radius) = cv2.minEnclosingCircle(c)
    	M = cv2.moments(c)
    	center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    	# only proceed if the radius meets a minimum size
    	if radius > 10:
    		# draw the circle and centroid on the frame,
    		# then update the list of tracked points
    		cv2.circle(frame, (int(x), int(y)), int(radius),
    			(0, 255, 255), 2)
    		cv2.circle(frame, center, 5, (0, 0, 255), -1)
    
    cv2.imshow("Mash",mask)
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    
vc.release()
cv2.destroyAllWindows()
