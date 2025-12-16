from djitellopy import tello 
drone = tello.Tello()        
drone.connect()              
drone.takeoff()


drone.enable_mission_pads()
drone.set_mission_pad_detection_direction(2)

drone.go_xyz_speed_yaw_mid(100,0,0,60,0,4,6)

drone.land()
