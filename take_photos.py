from time import sleep
from djitellopy import tello
import sys
import cv2


if True:
    drone = tello.Tello()
    
    
    drone.connect()
    drone.streamon()

photos_per_sec = 3

args = sys.argv
if len(args) > 1:
    photos_per_sec = args[1]

try:
    photos_per_sec = int(photos_per_sec)
except:
    photos_per_sec= 3


if photos_per_sec > 120:
    photos_per_sec = 3


index = 0
while True:
    fr_read = drone.get_frame_read()
    frame =fr_read.frame
    
    
    
    if frame is not None:
        cv2.imwrite("photos/"+str(index)+".png",frame)

    index +=1
    sleep(60/photos_per_sec)


