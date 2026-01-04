from numpy import ma
import pygame as pg
from djitellopy import tello
import sys
import balltracker as bt
import cv2



# speichere die Standardschriftart, die zum Zeichnen des Textes verwendet wird
font = None


# Text an einer bestimmten Position auf dem Bildschirm zeichnen
def write(screen,text,location,color=(255,255,255)):
    global font
    if font is not None:
        screen.blit(font.render(text,True,color),location)


def main():
    global font

    drone = tello.Tello()
    print(drone)
    try:
        drone.connect()
    except:
        print("Error",drone,type(drone))
        sys.exit()

    #die Drohne starten
    drone.streamon()

    # Starte pygame
    # pygame ist eine Python-Bibliothek, die für Spiele verwendet wird,
    # aber sie kann auch außerhalb von Spielen genutzt werden
    pg.init()
    resolution = 960,720
    screen = pg.display.set_mode(resolution)

    # Standardschriftart festlegen
    font=pg.font.Font(None,20)

    window_color = 40, 40, 90

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
        screen.fill(window_color)

        # Akku-Prozentsatz und aktuelle Temperatur der Drohne abrufen
        batt = drone.get_battery()
        temp = drone.get_temperature()

        ball_tracker = bt.BallTracker(min_r=10,max_r=50)
        # Ein Objekt mit dem Bild und Details der Drohne abrufen
        frame_read = drone.get_frame_read()
        # auf das Bild zugreifen
        img = frame_read.frame
        if img is not None: # sicherstellen, dass das Bild korrekt empfangen wurde
            img = cv2.flip(img,1)
            img = cv2.transpose(img)   # optional, Tello feed may be rotated
            success, processed_frame, mask = ball_tracker.find(img)

            # optional, Tello und Pygame könnten unterschiedliche Formate nutzen
            #frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            keys = pg.key.get_pressed() 
            if keys[pg.K_a]:            
                img = mask
            if keys[pg.K_d]:            
                img =processed_frame

            frame_surface = pg.surfarray.make_surface(img)

            # zeichne das Bild an Position 0,0 auf den Bildschirm
            screen.blit(frame_surface, (0, 0))
        else: # falls ein Fehler aufgetreten ist
            batt = 10000
            temp = -1000

        # Zeichne verschiedene Informationen über die Drohne auf den Bildschirm
        write(screen,f"Batt:{batt}%   T:{temp}*C",(0,0))
        pg.display.update()

    # schließe das Fenster, das wir für den Kamerastream genutzt haben
    pg.quit()
    # lande die Drohne, nachdem wir die Schleife beendet haben
    # beende das Python-Programm
    sys.exit()



if __name__ == "__main__":
    main()
