
from time import sleep
import pygame as pg
from djitellopy import tello
import sys
import cv2
import control as ctrl


(major_ver, minor_ver, subminor_ver) = cv2.__version__.split('.')

Speed = 10
Should_quit = False
Track_Ball = False
Abort = False
Set_Radius = False
Set_BBOX = False
font = None

def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

# CCF9F8
def write(screen,text,location,color=(255,255,255)):
    global font
    if font is not None:
        screen.blit(font.render(text,True,color),location)


def main():

    global font
    global Should_quit,Track_Ball,Abort,Set_Radius,Set_BBOX

    drone_conn = True
    drone = tello.Tello()

    try:
        drone.connect()
    except Exception as e:
        drone_conn = False
        print(e)
        sys.exit()
        print("Error starting drone",drone,type(drone))
    drone.streamon()
    drone.takeoff()
    # initialize
    pg.init()
    font=pg.font.Font(None,20)
    resolution = 960,720
    screen = pg.display.set_mode(resolution)

    wincolor = 40, 40, 90

    width, height = screen.get_size()

    # ball has to be center of screen in x achsis, tolerance 20px
    pid_x = ctrl.PIDControler(width//2,1,0.1,0.0,40)
    # ball has to be center of screen in y achsis,tolerance 20px
    pid_y = ctrl.PIDControler(height//2,1,0.1,0.0,20)
    # radius has to be 30, tolerance 1px
    pid_z = ctrl.PIDControler(30,1,0.1,0.0,1)

    tracker_types = [                                                
        'BOOSTING', 'MIL', 'KCF', 'TLD',                             
        'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT'                      
    ]                                                                
                                                                     
    tracker_type = tracker_types[2]                                  
    tracker = None
                                                                     
    print(cv2.__version__)                                           
                                                                     
    if int(minor_ver) < 3:                                           
        tracker = cv2.Tracker_create(tracker_type)                   
    else:                                                            
        if tracker_type == 'BOOSTING':                               
            tracker = cv2.TrackerBoosting_create()                   
        elif tracker_type == 'MIL':                                  
            tracker = cv2.TrackerMIL_create()                        
        elif tracker_type == 'KCF':                                  
            tracker = cv2.TrackerKCF_create()                        
        elif tracker_type == 'TLD':                                  
            tracker = cv2.TrackerTLD_create()                        
        elif tracker_type == 'MEDIANFLOW':                           
            tracker = cv2.TrackerMedianFlow_create()                 
        elif tracker_type == 'GOTURN':                               
            tracker = cv2.TrackerGOTURN_create()                     
        elif tracker_type == 'MOSSE':                                
            tracker = cv2.TrackerMOSSE_create()                      
        elif tracker_type == 'CSRT':                                 
            tracker = cv2.TrackerCSRT_create()                       
        else:
            return
                                                                     

    # move
    angle = 0
    height = 20
    circle_center= (0,0)

    bbox = (287, 23, 86, 320)                                       
    output_pid_x = 0

    while not Should_quit:
        #time.sleep(0.1)
        screen.fill(wincolor)

        do_input()
 #       print("ABort:",Abort,"Quit:",Should_quit)
        if Abort:
            drone.emergency()
            sys.exit()
        if drone_conn:
            batt = drone.get_battery()
            temp = drone.get_temperature()
#            print( "Batt:",batt)

            frame_read = drone.get_frame_read()

            img = frame_read.frame
            if img is not None:
                img = cv2.transpose(img)   # optional, Tello feed may be rotated
                if not Track_Ball:
                    rotate_clockwise_no_wait(drone,10)
                    sleep(0.1)
                else:
                    img = cv2.GaussianBlur(img, (17, 17), 0)
                    output_pid_x = pid_x.compute(circle_center[0])
                    print(output_pid_x)


                    if not pid_x.reached_setpoint(circle_center[0]):
                        angle += output_pid_x
                    else:
                        pid_x.reset()
                    print(output_pid_x)

                    if output_pid_x > 0:
                        rotate_clockwise_no_wait(drone,output_pid_x)
                    else:
                        rotate_counter_clockwise_no_wait(drone,-output_pid_x)


                    
                    #if ball_tracker.frame is not None:
                    #    img=ball_tracker.frame
                    ok,bbox = tracker.update(img)

                    if ok:                                                       
                        p1 = (int(bbox[0]), int(bbox[1]))                        
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))    
                        circle_center = (int(bbox[0]+bbox[2])/2,int(bbox[1]+bbox[3])/2)
                        cv2.rectangle(img, p1, p2, (255, 0, 0), 2, 1)          
                        cv2.circle(img,(int(circle_center[0]),int(circle_center[1])),4,(255,0,0),2)
                    else:                                                        
                        cv2.putText(                                             
                            img,                                               
                            "Tracking failure detected",                         
                            (100, 80),                                           
                            cv2.FONT_HERSHEY_SIMPLEX,                            
                            0.75,                                                
                            (0, 0, 255),                                         
                            2                                                    
                        )                                                        
                if Set_BBOX:
                    bbox = cv2.selectROI(img,False)
                    ok = tracker.init(img, bbox)                                  
                    Set_BBOX = False


                frame_surface = pg.surfarray.make_surface(img)

                screen.blit(frame_surface, (0, 0))

        else:
            batt = 10000
            temp = -1000
        write(
            screen,
            tracker_type + " Tracker",                                 
            (100, 20),                                                 
        )
        write(screen,f"Akku:{batt}%   T:{temp}*C",(0,40))
        write(screen,f"setpoint Radius:{pid_z.setpoint}",(width-200,0))
        write(screen,f"output_pid_x:{pid_x.past_variables[-1]}",(width-200,40))

        pg.display.update()

    pg.quit()
    if drone_conn:
        drone.land()
    sys.exit()


def px_to_angle(anngl):
    return anngl/10

def do_input():
    global Should_quit,Track_Ball,Abort,Set_Radius,Set_BBOX
    for event in pg.event.get():
            if event.type == pg.QUIT:
                Should_quit = True

    keys = pg.key.get_pressed()
    if keys[pg.K_a]:
        Set_Radius = True
    if keys[pg.K_SPACE]:
        Track_Ball = not Track_Ball
    if keys[pg.K_s]:
        Set_BBOX = True


    if keys[pg.K_KP_ENTER]:
        Abort = True 
    if keys[pg.K_ESCAPE]:
        Should_quit = True




# Eigene Funktionen benutzen, um nicht auf eine Antwort zu wartet:
def rotate_clockwise_no_wait(drone: tello.Tello, x: int):
    x = int(clamp(x, 1, 360)) 
    drone.send_command_without_return("cw {}".format(x))

def rotate_counter_clockwise_no_wait(drone: tello.Tello, x: int):
    x = int(clamp(x, 1, 360)) 
    drone.send_command_without_return("ccw {}".format(x))

if __name__ == "__main__":
    main()
