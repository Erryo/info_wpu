from djitellopy import tello
import cv2

drone = tello.Tello()
drone.connect()
response = drone.send_command_with_return("command")
print(response)  

drone.streamon()

try:
    drone.takeoff()
except Exception as e:
    print(f"Takeoff failed: {e}")

temp = drone.get_temperature() 
print(temp)
batt = drone.get_battery()
print(batt)



for i in range(4): 
    frame = drone.get_frame_read()
    if frame.frame  is not None:
        cv2.imwrite(f"photos/Drone{i}.png", frame.frame)
        cv2.imshow("DroneCapture",frame.frame)

drone.land()
