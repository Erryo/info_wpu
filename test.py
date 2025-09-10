import cv2
from djitellopy import Tello

tello = Tello()
tello.connect()

tello.streamon()
frame_read = tello.get_frame_read()

tello.takeoff()
if frame_read.frame is not None:
    cv2.imwrite("photos/picture.png", frame_read.frame)

tello.land()



