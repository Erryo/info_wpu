from time import sleep
from djitellopy import tello

drone = tello.Tello(host="127.0.0.1")
drone.connect()


drone.takeoff()

drone.get_height()

drone.rotate_clockwise(90)
drone.rotate_counter_clockwise(60)

while True:
    sleep(0.1)
drone.land()
