from djitellopy import tello
drone_conn = True                    
drone = tello.Tello()                
print(drone)                         
try:                                 
    drone.connect()                  
except:                              
    drone_conn = False               
    print("Error",drone,type(drone)) 

print(drone.get_battery())
