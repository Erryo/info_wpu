
import pygame as pg
from djitellopy import tello
import sys
import cv2
from raylibpy import KEY_ENTER
import balltracker as bt
import control as ctrl


Speed = 10
Should_quit = False
Track_Ball = False
Abort = False
Set_Radius = False
font = None


# CCF9F8
def write(screen,text,location,color=(255,255,255)):
    global font
    if font is not None:
        screen.blit(font.render(text,True,color),location)


def main():

    global font
    global Should_quit,Track_Ball,Abort,Set_Radius

    drone_conn = True
    drone = tello.Tello()
    try:
        drone.connect()
        drone.streamon()
        drone.takeoff()
    except Exeption as e:
        drone_conn = False
        print("Error starting drone",drone,type(drone),e)
    # initialize
    pg.init()
    font=pg.font.Font(None,20)
    resolution = 960,720
    screen = pg.display.set_mode(resolution)

    wincolor = 40, 40, 90

    width, height = screen.get_size()

    ball_tracker = bt.BallTracker(target=(width//2,height//2),min_r=0,max_r=100)
    # ball has to be center of screen in x achsis, tolerance 20px
    pid_x = ctrl.PIDControler(width//2,1,0.1,0.05,20)
    # ball has to be center of screen in y achsis,tolerance 20px
    pid_y = ctrl.PIDControler(height//2,1,0.1,0.05,20)
    # radius has to be 30, tolerance 1px
    pid_z = ctrl.PIDControler(30,1,0.1,0.05,1)


    # move
    pos = (0,0,0)
    angle = 0
    height = 20
    depth = 0
    success = False


    while not Should_quit:
        #time.sleep(0.1)
        screen.fill(wincolor)

        do_input()
        if Abort:
            drone.emergency()
            sys.exit()
        if drone_conn:
            batt = drone.get_battery()
            temp = drone.get_temperature()

            frame_read = drone.get_frame_read()

            img = frame_read.frame
            if img is not None:
                img = cv2.transpose(img)   # optional, Tello feed may be rotated
                if Track_Ball:
                    img = cv2.GaussianBlur(img, (17, 17), 0)
                    output_pid_x = pid_x.compute(ball_tracker.circle_x)
                    output_pid_x = px_to_angle(output_pid_x)

                    if not pid_x.reached_setpoint(ball_tracker.circle_x):
                        pass
                        angle += output_pid_x
                    else:
                        pid_x.reset()
                    if output_pid_x > 0:
                        drone.rotate_clockwise(output_pid_x)
                    else:
                        drone.rotate_counter_clockwise(-output_pid_x)


                    success = ball_tracker.calculate(img)
                    if Set_Radius:
                        print("setting radius:",ball_tracker.circle_radius)
                        pid_z.setpoint = int(ball_tracker.circle_radius)
                        Set_Radius = False
                    if success:
                        cv2.circle(img=img,center=(int(ball_tracker.circle_x),int(ball_tracker.circle_y)),radius=int(ball_tracker.circle_radius),color=(255,0,0),thickness=2)


                frame_surface = pg.surfarray.make_surface(img)

                screen.blit(frame_surface, (0, 0))

        else:
            batt = 10000
            temp = -1000
        write(screen,f"Winkel:{angle}*   Radius:{ball_tracker.circle_radius}px",(0,10))
        write(screen,f"Akku:{batt}%   T:{temp}*C",(0,40))
        write(screen,f"setpoint Radius:{pid_z.setpoint}",(width-200,0))
        write(screen,f"output_pid_x:{pid_x.past_variables[-1]}",(width-200,40))

        pg.display.update()

    pg.quit()
    if drone_conn:
        drone.land()
    sys.exit()


def px_to_angle(anngl):
    return anngl/1000

def do_input():
    global Should_quit,Track_Ball,Abort,Set_Radius
    for event in pg.event.get():
            if event.type == pg.QUIT:
                Should_quit = True

    keys = pg.key.get_pressed()
    if keys[pg.K_a]:
        Set_Radius = True
    if keys[pg.K_SPACE]:
        Track_Ball = not Track_Ball

    if keys[pg.K_KP_ENTER]:
        Abort = True 
    if keys[pg.K_ESCAPE]:
        Should_quit = True



if __name__ == "__main__":
    main()
