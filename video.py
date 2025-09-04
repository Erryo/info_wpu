import pygame as pg
from djitellopy import tello
import sys
import time
import cv2


Should_quit = False


def main():
    drone = tello.Tello()
    drone.connect()
    drone.streamon()

    drone.takeoff()

    # initialize
    pg.init()
    resolution = 960,720
    screen = pg.display.set_mode(resolution)
    wincolor = 40, 40, 90
    keys = [False,False,False,False,False,False,False,False,False,False]

    while not Should_quit:
        time.sleep(0.1)
        screen.fill(wincolor)
        vel,keys = do_input(keys)
        print(vel)
        drone.send_rc_control(vel[0],vel[1],vel[2],vel[3]) 

        frame_read = drone.get_frame_read()
        if frame_read.frame is not None:
            frame_rgb = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.transpose(frame_rgb)   # optional, Tello feed may be rotated
            frame_surface = pg.surfarray.make_surface(frame_rgb)
            screen.blit(frame_surface, (0, 0))
        pg.display.update()

    pg.quit()
    drone.land()
    sys.exit()


def do_input(keys):
    global Should_quit
    for event in pg.event.get():
            if event.type == pg.QUIT:
                Should_quit = True

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    keys[0] = True
                if event.key == pg.K_s:
                    keys[1] = True
                if event.key == pg.K_d:
                    keys[2] = True
                if event.key == pg.K_a:
                    keys[3] = True
                if event.key == pg.K_q:
                    keys[4] = True
                if event.key == pg.K_e:
                    keys[5] = True
                if event.key == pg.K_UP:
                    keys[6] = True
                if event.key == pg.K_DOWN:
                    keys[7] = True
                if event.key == pg.K_ESCAPE:
                    Should_quit = True
            if event.type == pg.KEYUP:
                if event.key == pg.K_w:
                    keys[0] = False
                if event.key == pg.K_s:
                    keys[1] = False
                if event.key == pg.K_d:
                    keys[2] = False
                if event.key == pg.K_a:
                    keys[3] = False
                if event.key == pg.K_q:
                    keys[4] = False
                if event.key == pg.K_e:
                    keys[5] = False
                if event.key == pg.K_UP:   
                    keys[6] = False         
                if event.key == pg.K_DOWN: 
                    keys[7] = False
    vels = [0,0,0,0]

    if keys[0]:
        vels[0] += 10
    if keys[1]:
        vels[0] -= 10

    if keys[2]:
        vels[1] += 10
    if keys[3]:
        vels[1] -= 10

    if keys[4]:
        vels[3] += 10
    if keys[5]:
        vels[3] -= 10

    if keys[6]:       
        vels[2] += 10 
    if keys[7]:       
        vels[2] -= 10 

    return vels,keys


if __name__ == "__main__":
    main()
