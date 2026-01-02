from time import sleep
from djitellopy import tello          
                                      
drone = tello.Tello(host="127.0.0.1") 
drone.connect()                       
                                      
drone.takeoff()                       


drone.enable_mission_pads()
drone.go_xyz_speed_yaw_mid(0,0,3,40,0,1,2)

sleep(1)

drone.land()
