
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

while rval:
    b,g,r = cv2.split(frame)
    only_red = imgproc.filter_col(120,100,r,g,b)

    sobelx = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(frame, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = cv2.magnitude(sobelx, sobely)
    gradient_magnitude = cv2.convertScaleAbs(gradient_magnitude)

    cv2.imshow("only_red",gradient_magnitude)
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break

vc.release()
cv2.destroyAllWindows()
