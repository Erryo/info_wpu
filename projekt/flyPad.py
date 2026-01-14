from djitellopy import tello
import time

drone = tello.Tello()

def center_over_pad(pad):
    drone.go_xyz_speed_mid(0,0,20,20,pad)
    yaw = drone.get_yaw()
    drone.rotate_counter_clockwise(yaw)
    #drone.rotate_clockwise(yaw)


def get_pad_position():
    x = drone.get_mission_pad_distance_x()
    y = drone.get_mission_pad_distance_y()
    return x, y




# ChatGPT CODE
def polygon_area_from_vectors(vectors):
    # Reconstruct vertices
    x, y = 0, 0
    vertices = [(x, y)] # die Koordinaten der Ecken des Vieleck

    # Berechne die Ecken
    for dx, dy in vectors:
        x += dx
        y += dy
        vertices.append((x, y))
    print("Vertices:",vertices)

    # Shoelace formula aka. Gaußsche Trapezformel
    # NOTE: Ich verstehe diese Formel nicht, siehe dazu https://de.wikipedia.org/wiki/Gau%C3%9Fsche_Trapezformel
    area = 0
    n = len(vertices)
    for i in range(n - 1):
        x1, y1 = vertices[i]
        x2, y2 = vertices[i + 1]
        area += x1 * y2 - x2 * y1

    return abs(area) / 2


# --------------------------
#     HAUPTPROGRAMM
# --------------------------

drone.connect()

print("Batterie:", drone.get_battery(), "%")



# Start
drone.takeoff()
time.sleep(1)

# Mission Pads aktivieren
drone.enable_mission_pads()
drone.set_mission_pad_detection_direction(0)  # 2 = beide

print("Warten auf Mission Pad 1 ...")
pad = drone.get_mission_pad_id()
print(f"Pad {pad} erkannt!")


center_over_pad(pad)

last_pad = pad

step_2d = (0,0) # speichert die Steigung der Seite
dist_pad = get_pad_position() # Abstand zum Anfang der Seite
print("Starte Vorwärts-Navigation...\n")

side_vectors=[] #  Vektoren, die zu den jeweiligen Seite von der letzte Seite führen
# Endlosschleife bis Pad 1 erneut kommt
while True:
    # Schrittweise vorwärts fliegen
    drone.move_forward(50)
    time.sleep(0.5)

    # Aktuelles Pad abfragen
    pad = drone.get_mission_pad_id()

    # Aktueller Abstand zum Pad
    dist_current_pad = get_pad_position()
    print(dist_current_pad)

    # Hier entsprechen Pads den Ecken des Vieleck

    # Nachdem ein neuer Pad gefunden wurde,
    # speichere die Steigung der neuer Seite
    if dist_pad == (0,0):
        print("Reseting the step_2d")
        step_2d = dist_current_pad

    # Wenn kein Pad gefunden wurde,
    # aktualisiere den Abstand zum Pad
    if pad == -1:
        dist_pad=dist_current_pad

    elif pad != -1:   # Ein Pad wurde erkannt
        print(f"Mission Pad erkannt: {pad}")

        # Man konnte warscheinlich die If-Bedingung weglassen,
        # aber ich bin mir nicht sicher
        # Es konnte ,,Edge-Cases" geben
        if pad != last_pad: # Eine neue Ecke wurde gefunden, damit auch eine neue Seite
            # Da der Abstand nun relativ zum neuen Pad ist,
            # hat man nicht den aktuelsten Abstand zum letzten Pad
            # und muss berechnet werden.
            # + step_2d macht genau das.
            # - dist_current_pad[0] falls die Drohne nicht genau auf dem neuen Pad steht
            dist_pad = dist_pad[0] - dist_current_pad[0]+step_2d[0], dist_pad[1] - dist_current_pad[1]+step_2d[1]
            print("Side done with len:",dist_pad)
            # speichere den neun Vektor
            side_vectors.append(dist_pad)
            dist_pad = (0,0)


        # Wenn wieder Pad 1 → landen
        if pad == 1 and last_pad != 1:
            print("Pad 1 erneut erreicht → Landen...")
            center_over_pad(pad)
            drone.land()
            break

        # Über dem Pad ausrichten
        center_over_pad(pad)

        last_pad = pad

print("\nGot the Following side Vectors:")
print("\t",side_vectors)

print("\n Calculated Area is:\t",polygon_area_from_vectors(side_vectors))
# Mission Pads deaktivieren (optional)
drone.disable_mission_pads()
drone.end()

