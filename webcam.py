import  sys
import cv2
import balltracker as bt

vc = cv2.VideoCapture(0)

frame = None
if vc.isOpened(): # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

if frame is None:
    sys.exit()

ball_tracker = bt.BallTracker()

while rval:
    if frame is None:
        break
    frame = cv2.flip(frame,1)
    success, processed_frame, mask = ball_tracker.calculate(frame)

    cv2.imshow("Processed Frame", processed_frame)
    cv2.imshow("Mask", mask)
    
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    
vc.release()
cv2.destroyAllWindows()
