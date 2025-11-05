from time import sleep
from djitellopy import tello
import sys
import cv2
import pygame as pg


pg.init()
if True:
    drone = tello.Tello()
    
    
    drone.connect()
    drone.streamon()

print(drone.get_battery())
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
    
    print(index)
    if frame is not None:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite("photos/t"+str(index)+".png",frame)
        cv2.imshow("photo",frame)

    index +=1
    sleep(1/photos_per_sec)

