import time 
from djitellopy import tello

drone = tello.Tello(host="127.0.0.1")
drone.connect()


drone.takeoff()

drone.get_height()

drone.rotate_clockwise(45)

time.sleep(2)
drone.move_forward(2)
time.sleep(2)
drone.move_forward(2)
time.sleep(2)
drone.move_back(2)
time.sleep(2)
drone.move_back(2)

time.sleep(4)
