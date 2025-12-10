from djitellopy import Tello
import time

class MissionPadController:
    def __init__(self, search_step=40, delay=0.4, max_attempts=50, forward_step=30):
        self.tello = Tello()
        self.missionpads = []
        self.current_pad = None
        self.search_step = search_step
        self.delay = delay
        self.max_attempts = max_attempts
        self.forward_step = forward_step

    # -------------------------
    # Connect and enable pads
    # -------------------------
    def connect(self):
        self.tello.connect()
        print(self.tello.get_battery())
        self.tello.enable_mission_pads()
        self.tello.set_mission_pad_detection_direction(0)
        print("Connected + Mission Pads enabled.")

    # -------------------------
    # Read pad ID and relative distances
    # -------------------------
    def read_pad(self):
        mid = self.tello.get_mission_pad_id()
        dx = self.tello.get_mission_pad_distance_x()
        dy = self.tello.get_mission_pad_distance_y()
        dz = self.tello.get_mission_pad_distance_z()
        return mid, dx, dy, dz

    # -------------------------
    # Search for a specific pad
    # -------------------------
    def search_pad(self, target_id):
        attempts = 0
        mid, _, _, _ = self.read_pad()
        while mid != target_id and attempts < self.max_attempts:
            self.tello.move_forward(self.search_step)
            time.sleep(self.delay)
            mid, _, _, _ = self.read_pad()
            attempts += 1
        if mid != target_id:
            raise RuntimeError(f"Pad {target_id} not found.")
        return mid

    # -------------------------
    # Detect a new pad different from current
    # -------------------------
    def detect_new_pad(self):
        attempts = 0
        mid, dx, dy, dz = self.read_pad()
        while (mid == -1 or mid == self.current_pad) and attempts < self.max_attempts:
            self.tello.move_forward(self.search_step)
            time.sleep(self.delay)
            mid, dx, dy, dz = self.read_pad()
            attempts += 1
        if mid == -1:
            return -1, None, None, None
        return mid, dx, dy, dz

    # -------------------------
    # Align drone over pad
    # -------------------------
    def align_over_pad(self, dx, dy, dz, mid, alt=50):
        if dx == -1 or dy == -1 or dz == -1:
            print(f"Invalid pad data for pad {mid}, skipping alignment.")
            return
        print(f"Aligning over pad {mid}...")
        try:
            # x = lateral, y = forward, z = vertical; keep constant altitude
            self.tello.go_xyz_speed_mid(-dx, -dy, alt, 40, mid)
        except Exception as e:
            print(e)
            pass

    # -------------------------
    # Fly forward in steps, break if new pad detected
    # -------------------------
    def fly_forward_from_pad(self, mid, distance=120, speed=50):
        print(f"Flying forward from pad {mid}...")
        steps = distance // self.forward_step
        for _ in range(steps):
            try:
                self.tello.go_xyz_speed_mid(self.forward_step, 0, 0, speed, mid)
            except Exception:
                pass
            time.sleep(0.2)
            # Break if a new pad appears early
            next_mid, _, _, _ = self.read_pad()
            if next_mid != -1 and next_mid != mid:
                print(f"New pad {next_mid} detected during flight. Stopping forward move.")
                break

    # -------------------------
    # Main mission loop
    # -------------------------
    def run_mission(self):
        self.connect()
        print("Takeoff.")
        self.tello.takeoff()

        print("Searching for pad 1...")
        try:
            self.current_pad = self.search_pad(1)
        except Exception as e:
            print("Abort:", e)
            self.tello.land()
            return

        mid, dx, dy, dz = self.read_pad()
        self.align_over_pad(dx, dy, dz, mid)
        self.missionpads.append({"id": mid, "dx": dx, "dy": dy, "dz": dz})

        while True:
            print("Looking for next pad...")
            next_mid, dx, dy, dz = self.detect_new_pad()

            if next_mid == -1:
                print("No new pad detected, aborting mission.")
                break

            # Mission complete if Pad 1 is reached again
            if next_mid == 1 and self.current_pad != 1:
                print("Pad 1 detected again. Mission complete.")
                break

            print(f"New pad {next_mid} detected.")
            self.align_over_pad(dx, dy, dz, next_mid)
            self.missionpads.append({"id": next_mid, "dx": dx, "dy": dy, "dz": dz})
            self.fly_forward_from_pad(next_mid)

            self.current_pad = next_mid

        print("Landing.")
        self.tello.land()
        print("Pads recorded:")
        for p in self.missionpads:
            print(p)


# -------------------------
# Run mission
# -------------------------
if __name__ == "__main__":
    MissionPadController().run_mission()
