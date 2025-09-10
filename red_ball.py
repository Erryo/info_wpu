import pygame as pg
from djitellopy import tello
import sys
import numpy as np
import cv2

import imgproc

Should_quit = False
font = None

X = 0
Y = 1
Z = 2 
R = 3

def write(screen,text,location,color=(255,255,255)):
    global font
    if font is not None:
        screen.blit(font.render(text,True,color),location)


def main():

    global font

    drone_conn = True
    drone = tello.Tello()
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

    while not Should_quit:
        #time.sleep(0.1)
        screen.fill(wincolor)

        #vel,keys = do_input(keys)
        vel = test_input()
        if drone_conn:
            batt = drone.get_battery()
            temp = drone.get_temperature()

            #NOTE: maybe req a timer
            print("Time between RC CTRL CMD:",drone.TIME_BTW_RC_CONTROL_COMMANDS)
            drone.send_rc_control(vel[0],vel[1],vel[2],vel[3])
            frame_read = drone.get_frame_read()

            if frame_read.frame is not None:
                angle,radius = imgproc.get_angle(frame_read.frame)

                frame_rgb = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.transpose(frame_rgb)   # optional, Tello feed may be rotated
                frame_surface = pg.surfarray.make_surface(frame_rgb)

                screen.blit(frame_surface, (0, 0))
        else:
            angle,radius = imgproc.get_angle(np.zeros((960,720,3),dtype=np.uint8))
            batt = 10000
            temp = -1000
        write(screen,f"Angle:{angle}*   Radius:{radius}px",(0,10))
        write(screen,f"Batt:{batt}%   T:{temp}*C",(0,40))
        write(screen,f"Velocity x:{vel[X]} y:{vel[Y]} z:{vel[Z]} rot:{vel[R]}",(resolution[0]-200,10))
        pg.display.update()

    pg.quit()
    if drone_conn:
        drone.land()
    sys.exit()



def test_input():
    global Should_quit
    for event in pg.event.get():      
            if event.type == pg.QUIT: 
                print("PRESSED QUIT") 
                Should_quit = True    

    vels = [0,0,0,0]
    keys = pg.key.get_pressed()
    if keys[pg.K_w]:
        vels[X] -= 10
    if keys[pg.K_s]:
        vels[X] += 10

    if keys[pg.K_a]:  
        vels[Y] -= 10 
    if keys[pg.K_d]:  
         vels[Y] += 10 

    if keys[pg.K_DOWN]:  
        vels[Z] -= 10 
    if keys[pg.K_UP]:  
        vels[Z] += 10 

    if keys[pg.K_LEFT]:  
        vels[R] -= 10 
    if keys[pg.K_RIGHT]:  
        vels[R] += 10 

    if keys[pg.K_ESCAPE]:
        Should_quit = True

    return vels
    


if __name__ == "__main__":
    main()
