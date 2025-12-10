from djitellopy import tello
import time

drone = tello.Tello()


def center_over_pad(pad):
    drone.go_xyz_speed_yaw_mid(0,0,20,20,0,pad,pad)

# --------------------------
#     HAUPTPROGRAMM
# --------------------------

drone.connect()

print("Batterie:", drone.get_battery(), "%")



# Mission Pads aktivieren
drone.enable_mission_pads()
drone.set_mission_pad_detection_direction(2)  # 2 = beide

# Start
drone.takeoff()
time.sleep(1)

print("Warten auf Mission Pad 1 ...")
pad = drone.get_mission_pad_id()
print(f"Pad {pad} erkannt!")

drone.go_xyz_speed_yaw_mid(0,0,20,20,0,pad,pad)

last_pad = pad
print("Starte Vorwärts-Navigation...\n")

# Endlosschleife bis Pad 1 erneut kommt
while True:
    # Schrittweise vorwärts fliegen
    drone.move_forward(20)
    time.sleep(0.5)

    # Aktuelles Pad abfragen
    pad = drone.get_mission_pad_id()
    

    if pad != -1:   # Ein Pad wurde erkannt
        print(f"Mission Pad erkannt: {pad}")

        # Wenn wieder Pad 1 → landen
        if pad == 1 and last_pad != 1:
            print("Pad 1 erneut erreicht → Landen...")
            center_over_pad(pad)
            drone.land()
            break

        # Über dem Pad ausrichten
        center_over_pad(pad)

        last_pad = pad

# Mission Pads deaktivieren (optional)
drone.disable_mission_pads()
drone.end()

