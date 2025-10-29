import pygame as pg
from djitellopy import tello
import sys
import cv2
import math



def main():

    delta_angle = 30
    distance_to_target = 100 #cm
    angle = 0
    x,y = 0,0

    pg.init()
    drone = tello.Tello()
    try:
        drone.connect()
    except:
        print("Error",drone,type(drone))
        sys.exit()

    #die Drohne starten
    drone.streamon()
    drone.takeoff()


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
        img = frame_read.frame
        if img is not None: # sicherstellen, dass das Bild korrekt empfangen wurde
            img = cv2.transpose(img)   # optional, Tello-Feed könnte gedreht sein
            cv2.imwrite("photos/1.jpg",img)

        angle += delta_angle

        if angle > 360:
            should_quit = True
        

        x  = math.sin(math.radians(delta_angle))
        y  = math.cos(math.radians(delta_angle))

        delta_x = distance_to_target - x
        delta_y = y
        drone.move("back",int(delta_x))
        drone.move("left",int(delta_y))


    drone.land()
    # beende das Python-Programm
    sys.exit()



if __name__ == "__main__":
    main()

