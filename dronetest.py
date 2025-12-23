import time
import cv2
from djitellopy import tello

drone = tello.Tello(host="127.0.0.1")
drone.connect()

drone.takeoff()
drone.streamon()

# Give stream time to start
time.sleep(1)

frame_read = drone.get_frame_read()

def clamp(value, min_val, max_val):          
    """Clamp value between min and max"""    
    return max(min_val, min(max_val, value)) 

                                                           
def rotate_clockwise_no_wait(drone: tello.Tello, x: int):  
    x = int(clamp(x, 1, 360))                              
    drone.send_command_without_return("cw {}".format(x))   

# Show video continuously
print("Starting video display...")
start_time = time.time()

while time.time() - start_time < 30:  # Show for 10 seconds
    frame = frame_read.frame
    
    if frame is not None and frame.size > 0:
        cv2.imshow("Tello Video", frame)
        print(f"Frame shape: {frame.shape}")
    else:
        print("No frame yet...")
    
#    drone.rotate_clockwise(10)
    rotate_clockwise_no_wait(drone,10)

    # CRITICAL: waitKey is required for imshow to work!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    time.sleep(0.03)  # ~30 FPS

print(f"Mission pad: {drone.get_mission_pad_id()}")

# Do your movements
drone.go_xyz_speed(4, 4, 0, 1)
time.sleep(3)

print(f"Mission pad: {drone.get_mission_pad_id()}")

# Keep showing video during flight
for _ in range(100):
    frame = frame_read.frame
    if frame is not None:
        cv2.imshow("Tello Video", frame)
    cv2.waitKey(1)

drone.land()
cv2.destroyAllWindows()




