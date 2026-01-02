import pygame as pg
from djitellopy import tello
import sys
import numpy as np
import time
import cv2

import imgproc

Speed = 10
Should_quit = False
Track_Ball = False
font = None

X = 1
Y = 0
Z = 2 
R = 3

# CCF9F8
def write(screen,text,location,color=(255,255,255)):
    global font
    if font is not None:
        screen.blit(font.render(text,True,color),location)


def main():

    global font
    global Track_Ball

    drone_conn = True
    drone = tello.Tello(host="127.0.0.1")
    print(drone)
    try:
        drone.connect()
        drone.streamon()
        drone.takeoff()
    except:
        drone_conn = False
        print("Error",drone,type(drone))
    # initialize
    pg.init()
    font=pg.font.Font(None,20)
    resolution = 960,720
    screen = pg.display.set_mode(resolution)

    wincolor = 40, 40, 90
    #keys = [False,False,False,False,False,False,False,False,False,False]
    angle,radius = 0,0
    start_time = time.time()
    drone.enable_mission_pads()

    while not Should_quit:
        #time.sleep(0.1)
        screen.fill(wincolor)

        #vel,keys = do_input(keys)
        vel = do_input()
        if drone_conn:
            batt = drone.get_battery()
            temp = drone.get_temperature()

            #NOTE: maybe req a timer
            # print("Time between RC CTRL CMD:",drone.TIME_BTW_RC_CONTROL_COMMANDS, "seconds ")
            if time.time() - start_time >= drone.TIME_BTW_RC_CONTROL_COMMANDS:
                drone.send_rc_control(vel[0],vel[1],vel[2],vel[3])
                start_time = time.time()
            frame_read = drone.get_frame_read()

            img = frame_read.frame
            if img is not None:
                img = cv2.transpose(img)   # optional, Tello feed may be rotated
                if Track_Ball:
                    img = cv2.GaussianBlur(img, (17, 17), 0)
                    r,g,b = cv2.split(img)
                    angle,radius,contour = imgproc.get_angle(r,g,b)
                    # cv2.imwrite("photos/g.png",g)
                    # cv2.imwrite("photos/b.png",b)
                    cv2.drawContours(src=img,contours=[contour],contourIdx=-1,color=(0,255,0),thickness=2)

                    img =imgproc.detect_circle_1(img)
                    #img = imgproc.filter_col(150,100,r,g,b)
                    #img = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)

                #frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                frame_surface = pg.surfarray.make_surface(img)

                screen.blit(frame_surface, (0, 0))
        else:
            batt = 10000
            temp = -1000
        write(screen,f"Winkel:{angle}*   Radius:{radius}px",(0,10))
        write(screen,f"Batt:{batt}%   T:{temp}*C",(0,40))
        write(screen,f"Geschwidigkeit x:{vel[X]} y:{vel[Y]} z:{vel[Z]} rot:{vel[R]}",(resolution[0]-230,10))
        pg.display.update()

    pg.quit()
    if drone_conn:
        drone.land()
    sys.exit()



def do_input():
    global Should_quit,Track_Ball,Speed
    for event in pg.event.get():      
            if event.type == pg.QUIT: 
                print("PRESSED QUIT") 
                Should_quit = True    

    vels = [0,0,0,0]
    keys = pg.key.get_pressed()
    if keys[pg.K_w]:
        vels[X] += 10*Speed
    if keys[pg.K_s]:
        vels[X] -= 10*Speed

    if keys[pg.K_a]:  
        vels[Y] -= 10*Speed 
    if keys[pg.K_d]:  
         vels[Y] += 10 *Speed

    if keys[pg.K_DOWN]:  
        vels[Z] -= 10 *Speed
    if keys[pg.K_UP]:  
        vels[Z] += 10 *Speed

    if keys[pg.K_LEFT]:  
        vels[R] -= 10 *Speed
    if keys[pg.K_RIGHT]:  
        vels[R] += 10 * Speed

    if keys[pg.K_CAPSLOCK]:
        Track_Ball = not Track_Ball
        print("Track_Ball is", Track_Ball)

    if keys[pg.K_ESCAPE]:
        print("Should_quit")
        Should_quit = True

    return vels
    


if __name__ == "__main__":
    main()
