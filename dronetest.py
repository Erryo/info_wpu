import datetime
import time 
from djitellopy import tello

drone = tello.Tello(host="127.0.0.1")
drone.connect()


drone.takeoff()


print(drone.get_mission_pad_id())
drone.go_xyz_speed(4,4,0,1)
print(drone.get_mission_pad_id())

#time_start = time.perf_counter()
#print("time_passed:",datetime.timedelta(seconds=time.perf_counter()-time_start))
time.sleep(4)
