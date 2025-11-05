from threading import currentThread
from time import sleep
import pygame as pg
from djitellopy import tello
import sys
import cv2
import math



def main():

    photo_dir =  "Test1/images/" 
    delta_angle = 40
    distance_to_target = 50 #cm
    angle = 0
    x,y = 0,0

    pg.init()
    drone = tello.Tello()
    try:
        drone.connect()
    except:
        print("Error",drone,type(drone))
        sys.exit()

    batt = drone.get_battery()
    print(batt)
    #die Drohne starten
    drone.streamon()
    drone.takeoff()


    drone.enable_mission_pads()
    drone.set_mission_pad_detection_direction(2)
    missionPadId = drone.get_mission_pad_id()
    print(missionPadId)
    index = 0

    current_x = 0
    current_y = 0
    current_y = 30
    # Starte eine Schleife, die läuft, bis wir sie stoppen
    should_quit = False
    while not should_quit:
        # Gehe alle Tasten durch, die der Benutzer gedrückt hat
        for event in pg.event.get():
                # wenn der Benutzer das X-Symbol oben im Fenster klickt, Schleife beenden
                if event.type == pg.QUIT:
                    should_quit = True



        # lösche, was im vorherigen Frame gezeichnet wurde
        # und setze die Hintergrundfarbe auf Blau

        # Akku-Prozentsatz und aktuelle Temperatur der Drohne abrufen
        batt = drone.get_battery()
        print(batt)

        # Ein Objekt mit dem Bild und Details der Drohne abrufen
        frame_read = drone.get_frame_read()
        # auf das Bild zugreifen
        #
        index += 1
        img = frame_read.frame
        if img is not None: # sicherstellen, dass das Bild korrekt empfangen wurde

            cv2.imwrite(photo_dir+"t"+str(index)+".png",img)

        angle += delta_angle

        

        x  = math.cos(math.radians(delta_angle)) * distance_to_target
        y  = math.sin(math.radians(delta_angle)) * distance_to_target

        print("Going to:",int(x)-current_x,int(y)-current_y)
#        drone.go_xyz_speed(int(x)-current_x, 0, int(y)-current_y, 60)
        drone.go_xyz_speed_mid(int(x), 100, int(y), 60,3)


    drone.land()
    # beende das Python-Programm
    sys.exit()



if __name__ == "__main__":
    main()

