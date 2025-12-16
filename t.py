import time
from djitellopy import tello
drone = tello.Tello()
drone.connect()
drone.initiate_throw_takeoff()
time.sleep(1)
drone.land()
