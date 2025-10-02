"""
Dieses Programm steuert eine DJI Tello Drohne mit der Tastatur
und zeigt das Kamerabild in einem Fenster an.

Benutzte Bibliotheken:
- pygame: erstellt ein Fenster und erkennt Tastatureingaben
- djitellopy: kommuniziert mit der Tello Drohne
- cv2 (OpenCV): verarbeitet das Kamerabild
- time: für Zeitmessungen
- imgproc: ein eigenes Modul (nicht dabei), um einen Ball zu erkennen
"""

import pygame as pg
from djitellopy import tello
import sys
import time
import cv2

# ----------------- GLOBALE EINSTELLUNGEN -----------------
Speed = 10              # wie schnell die Drohne sich bewegt
Should_quit = False     # wenn True → Programm beendet sich
font = None             # Schriftart für Text im Fenster

# Indizes für Bewegungsrichtungen (zur besseren Übersicht)
X = 1   # vorwärts / rückwärts
Y = 0   # links / rechts
Z = 2   # hoch / runter
R = 3   # drehen (links / rechts)


# ----------------------------------------------------
# Funktion: schreibt Text ins Fenster
# screen → wo der Text erscheinen soll
# text   → die Nachricht
# location → Position x,y
# color  → Textfarbe (Standard: weiß)
def write(screen, text, location, color=(255, 255, 255)):
    global font
    if font is not None:
        screen.blit(font.render(text, True, color), location)


# ----------------------------------------------------
# HAUPTFUNKTION: startet das Drohnenprogramm
def main():
    global font

    # Verbindung zur Drohne versuchen
    drone_conn = True
    drone = tello.Tello()
    print("Versuche, Verbindung zur Drohne aufzubauen...")
    try:
        drone.connect()         # mit Drohne verbinden
        drone.streamon()        # Videostream starten
        # drone.takeoff()       # falls man möchte, dass sie sofort startet
        print("Drohne erfolgreich verbunden!")
    except:
        drone_conn = False
        print("Verbindung zur Drohne fehlgeschlagen.")

    # Fenster für Anzeige erstellen
    pg.init()
    font = pg.font.Font(None, 20)   # Schriftgröße einstellen
    resolution = (960, 720)         # Fenstergröße
    screen = pg.display.set_mode(resolution)
    window_color = (40, 40, 90)     # Hintergrundfarbe (dunkelblau)

    # Variablen für Anzeige
    angle, radius = 0, 0
    start_time = time.time()

    # ----------------- HAUPTSCHLEIFE -----------------
    # Läuft, bis wir beenden
    while not Should_quit:
        screen.fill(window_color)  # Hintergrund neu malen

        # Tastatur-Eingaben holen
        velocities = do_input()

        # Batterie und Temperatur auslesen
        batt = drone.get_battery()
        temp = drone.get_temperature()
            
        # ----------------- BEFEHLZEIT -----------------
        # Die Drohne erwartet einen Befehl nur alle X Sekunden.
        # Wenn wir die Befehle zu schnell senden, kann die Drohne "panisch" reagieren oder unkontrolliert fliegen.
        # Wir prüfen, ob genug Zeit seit dem letzten Befehl vergangen ist:
        if time.time() - start_time >= drone.TIME_BTW_RC_CONTROL_COMMANDS:
            # Sende die Bewegungsbefehle an die Drohne
            drone.send_rc_control(velocities[0], velocities[1], velocities[2], velocities[3])
            # Setze den Timer zurück, um die Zeit für den nächsten Befehl zu messen
            start_time = time.time()
                # Kamerabild von der Drohne holen
            
            
        frame_read = drone.get_frame_read()
        img = frame_read.frame

        if img is not None:  # nur wenn ein Bild da ist
            img = cv2.transpose(img)  # Kamera der Tello ist oft gedreht
            # OpenCV-Bild in pygame umwandeln
            frame_surface = pg.surfarray.make_surface(img)
            screen.blit(frame_surface, (0, 0))  # ins Fenster malen


        # ----------------- TEXT ANZEIGEN -----------------
        write(screen, f"Winkel: {angle}°   Radius: {radius}px", (10, 10))
        write(screen, f"Batterie: {batt}%   Temp: {temp}°C", (10, 40))
        write(screen, f"Geschwindigkeit x:{velocities[X]} y:{velocities[Y]} z:{velocities[Z]} rotation:{velocities[R]}",
              (resolution[0] - 400, 10))

        # Fenster aktualisieren
    pg.display.update()

    # ----------------- AUFRÄUMEN -----------------
    pg.quit()             # Fenster schließen
    if drone_conn:
        drone.land()      # Drohne sicher landen
    sys.exit()            # Programm beenden


# ----------------------------------------------------
# Funktion: verarbeitet Tastatur-Eingaben
# Liest gedrückte Tasten und macht daraus Bewegungen
def do_input():
    global Should_quit, Speed

    # Prüfen, ob X im Fenster angeklickt wurde
    for event in pg.event.get():
        if event.type == pg.QUIT:
            print("Fenster schließen gedrückt")
            Should_quit = True

    # Liste mit Bewegungen [links/rechts, vor/zurück, hoch/runter, drehen]
    velocities = [0, 0, 0, 0]
    # alle Tasten abfragen
    keys = pg.key.get_pressed()

    # Vorwärts / Rückwärts (W / S)
    if keys[pg.K_w]:
        velocities[X] += 10 * Speed
    if keys[pg.K_s]:
        velocities[X] -= 10 * Speed

    # Links / Rechts (A / D)
    if keys[pg.K_a]:
        velocities[Y] -= 10 * Speed
    if keys[pg.K_d]:
        velocities[Y] += 10 * Speed

    # Hoch / Runter (Pfeiltasten hoch/runter)
    if keys[pg.K_UP]:
        velocities[Z] += 10 * Speed
    if keys[pg.K_DOWN]:
        velocities[Z] -= 10 * Speed

    # Drehen (Pfeiltasten links/rechts)
    if keys[pg.K_LEFT]:
        velocities[R] -= 10 * Speed
    if keys[pg.K_RIGHT]:
        velocities[R] += 10 * Speed

    # ESC → Programm beenden
    if keys[pg.K_ESCAPE]:
        print("ESC gedrückt → Programm beenden")
        Should_quit = True

    return velocities


# ----------------------------------------------------
# Hier startet das Programm
if __name__ == "__main__":
    main()

