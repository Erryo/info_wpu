import socket
import raylibpy as rl
import threading
import time
import control as ctrl
import math
import random

import datetime

# --------------------
# Configuration
# --------------------
COMMAND_PORT = 8889
STATE_PORT = 8890

CMD_PORT_drone = 8000
STATE_PORT_drone = 8001
HOST = "0.0.0.0"

DEFAULT_SPEED = 10
# Where to send state (DJITelloPy listens locally)
CLIENT_IP = "127.0.0.1"
TIME_OUT=15 #s


DRONE_SIZE = 0.5



last_keep_alive = time.perf_counter()

# --------------------
# Shared drone state
# --------------------
drone_state = {
    "x": 0,
    "h": 0,
    "z": 0,
    "pitch": 0,
    "roll": 0,
    "yaw": 0,
    "vgx": 0,
    "vgy": 0,
    "vgz": 0,
    "templ": 70,
    "temph": 75,
    "tof": 10,
    "bat": 100,
    "baro": 0.0,
    "time": 0,
    "agx": 0.0,
    "agy": 0.0,
    "agz": 0.0,
    "mid": -1,
}



class Point3D:
    x: float
    y: float
    z: float
    def __init__(self,x:float,y:float,z:float) -> None:
        self.x = x
        self.y = y
        self.z = z
    def to_vector(self):
        return rl.Vector3(self.x,self.y,self.z)

class MissionPad :
    origin: Point3D
    vector: Point3D# Vector from origin(of Pad) to Point3D
    id: int
    
    def __init__(self,x,y,z,id) -> None:
        self.origin = Point3D(x,y,z)
        self.id = id


in_air = False

mp_1 = MissionPad(0,0,0,1)      
mp_2 = MissionPad(4,0,4,2)      
                                
mission_pads = [mp_1,mp_2]      
state_lock = threading.Lock()

#absolute
def go_coord(target,key):
    pid = ctrl.PIDControler(target,1/70,0,0,0.001)

    while not pid.reached_setpoint(drone_state[key]):
        value = pid.compute(drone_state[key])
        variability = random.uniform(0.9,1.1)
        value *= variability
        drone_state[key] += value
        time.sleep(random.uniform(0.003,0.009))


def go_point_diagonal(point: Point3D,speed=1):
    pid_x = ctrl.PIDControler(point.x,1/70,0,0,0.001)
    pid_h = ctrl.PIDControler(point.y,1/70,0,0,0.001)
    pid_z = ctrl.PIDControler(point.z,1/70,0,0,0.001)

    numb_pids_done = 0
    x_done = False
    y_done = False
    z_done = False
    while numb_pids_done <3:
        if not pid_x.reached_setpoint(drone_state["x"]):
            value = pid_x.compute(drone_state["x"])
            variability = random.uniform(0.9,1.1)
            value *= variability*speed
            drone_state["x"] += value
        elif not x_done:
            numb_pids_done += 1
            x_done = True

        if not pid_h.reached_setpoint(drone_state["h"]):
            value = pid_h.compute(drone_state["h"])
            variability = random.uniform(0.9,1.1)
            value *= variability*speed
            drone_state["h"] += value
        elif not y_done:
            numb_pids_done += 1
            y_done = True

        if not pid_z.reached_setpoint(drone_state["z"]):
            value = pid_z.compute(drone_state["z"])
            variability = random.uniform(0.9,1.1)
            value *= variability*speed
            drone_state["z"] += value
        elif not z_done:
            numb_pids_done += 1

        time.sleep(random.uniform(0.003,0.009))

    print("x:",drone_state["x"]," y:",drone_state["h"]," z:",drone_state["z"])

def go_point_mid(p: Point3D,id: int,speed: int = 1):
    mp = MissionPad(0,0,0,0)
    for pad in mission_pads:
        if pad.id == id :
            mp = pad

    x,h,z = mp.origin.x,mp.origin.y,mp.origin.z
    target = Point3D(x=p.x+x,y=p.y+h,z=p.z+z)                    
    print("target is x:",target.x," y:",target.y," z:",target.z) 
    go_point_diagonal(target,speed)                              


# Relative to drone
def go_point_diagonal_delta(p: Point3D,speed=1):
    x,h,z = drone_state["x"],drone_state["h"],drone_state["z"]
    target = Point3D(x=p.x+x,y=p.y+h,z=p.z+z)
    print("target is x:",target.x," y:",target.y," z:",target.z)
    go_point_diagonal(target,speed)



def calc_target_yaw(amount,yaw_offset=0):
    x,h,z = drone_state["x"],drone_state["h"],drone_state["z"]
    i_vector = calc_rotation_vector(drone_state["yaw"]+yaw_offset)
    target_delta = Point3D(i_vector[0]*amount,y=h,z=i_vector[1]*amount)
    target = Point3D(target_delta.x+x,h,target_delta.z+z)
    return target
#relative to current yaw(orientation)

def go_normal_2D(amount,yaw_offset=0):
    print("going normal:",yaw_offset+drone_state["yaw"])
    target = calc_target_yaw(amount,yaw_offset)
    go_point_diagonal(target)


def rotate_pid(target,key):
    pid = ctrl.PIDControler(target,1/70,1/10000,0,0.01)
    while not pid.reached_setpoint(drone_state[key]):
        value = pid.compute(drone_state[key])
        variability = random.uniform(0.98,1.02)
        value *= variability
        drone_state[key] += value
        time.sleep(random.uniform(0.003,0.009))

def rotate_pid_delta(target,key):
    target = drone_state[key]+target
    rotate_pid(target=target,key=key)

#absolute
def go_coord_delta(target,key: str):
    target = drone_state[key]+target
    go_coord(target=target,key=key)

def calc_rotation_vector(yaw=drone_state["yaw"]): # aka. i_vectior
    yaw = yaw*(math.pi/180)
    return [math.cos(yaw),math.sin(yaw)]

def detect_mission_pad_underneath() :
    drone_state["mid"] = -1
    for pad in mission_pads:
        if aabb_2d_check(pad):
            drone_state["mid"] = pad.id

def aabb_2d_check(
    pad: MissionPad,
) -> bool:
    """
    2D AABB collision check on X-Z plane.
    Height (Y) is ignored.
    """
    drone_pos = Point3D(drone_state["x"],
                        drone_state["h"],
                        drone_state["z"],
    )


    dx = abs(drone_pos.x - pad.origin.x)
    dz = abs(drone_pos.z - pad.origin.z)

    return (
        dx <= (DRONE_SIZE/2 + DRONE_SIZE) and
        dz <= (DRONE_SIZE/2 + DRONE_SIZE)
    )


def handle_annoying(cmd: str):
    if not in_air:
        return b"error not in air"
    strs = cmd.split(" ")
    #relative
    x = int(strs[1])
    if strs[0] == "up":
        go_coord_delta(x,"y")
    if strs[0] == "down":
        go_coord_delta(-x,"y")
    if strs[0] == "forward":
        go_normal_2D(x)
    if strs[0] == "back":
        go_normal_2D(-x)
    if strs[0] == "right":
        go_normal_2D(x,90)
    if strs[0] == "left":
        go_normal_2D(-x,90)
    if strs[0] == "cw":
        rotate_pid_delta(x,"yaw")
    if strs[0] == "ccw":
        rotate_pid_delta(-x,"yaw")
    if strs[0] == "go":
        if len(strs) == 5:
            x= int(strs[1])
            z= int(strs[2])
            h= int(strs[3])
            print("Going:x",x," y",h," z:",z)
            speed= int(strs[4])
            go_point_diagonal_delta(Point3D(x=x,y=h,z=z),speed)
        if len(strs) == 6:                                      
            x= int(strs[1])                                     
            z= int(strs[2])                                     
            h= int(strs[3])                                     
            print("Going:x",x," y",h," z:",z)                   
            speed= int(strs[4])                                 
            mid=int(strs[5].removeprefix("m"))                          
            print("mid is:",mid)
            go_point_mid(Point3D(x=x,y=h,z=z),mid,speed)
     

    return b"ok"







# --------------------
# Command server thread
# --------------------
def command_server():
    global in_air,last_keep_alive
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, COMMAND_PORT))

    print("Command server listening on UDP 8889")

    while True:
        data, addr = sock.recvfrom(1024)
        cmd = data.decode("utf-8").strip()
        print(f"[CMD] {addr}: {cmd}")

        # Basic command handling
        if cmd == "command":
            sock.sendto(b"ok", addr)

        elif cmd == "takeoff":
            if in_air:
                sock.sendto(b"error", addr)
                return
            with state_lock:
                go_coord(4,'h')
                in_air = True
            sock.sendto(b"ok", addr)

        elif cmd == "keepalive":
            last_keep_alive = time.perf_counter()
        elif cmd == "land" or cmd == "emergency":
            if not in_air:
                sock.sendto(b"error", addr)
                return
            with state_lock:
                go_coord(0,'h')
                in_air = False
            sock.sendto(b"ok", addr)

        else:
            with state_lock:
                res = handle_annoying(cmd)
            sock.sendto(res, addr)

def i(v):
    return int(round(v))

# --------------------
# State sender thread
# --------------------
def state_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    print("State server sending on UDP 8890")

    while True:
        with state_lock:
            state_str = (
                f"x:{i(drone_state['x'])};"
                f"h:{i(drone_state['h'])};"
                f"z:{i(drone_state['z'])};"
                f"pitch:{i(drone_state['pitch'])};"
                f"roll:{i(drone_state['roll'])};"
                f"yaw:{i(drone_state['yaw'])};"
                f"vgx:{i(drone_state['vgx'])};"
                f"vgy:{i(drone_state['vgy'])};"
                f"vgz:{i(drone_state['vgz'])};"
                f"templ:{i(drone_state['templ'])};"
                f"temph:{i(drone_state['temph'])};"
                f"tof:{i(drone_state['tof'])};"
                f"bat:{i(drone_state['bat'])};"
                f"baro:{i(drone_state['baro'])};"
                f"time:{i(drone_state['time'])};"
                f"agx:{i(drone_state['agx'])};"
                f"agy:{i(drone_state['agy'])};"
                f"mid:{i(drone_state['mid'])};"
                f"agz:{i(drone_state['agz'])};\r\n"
            )

        sock.sendto(state_str.encode(), (CLIENT_IP, STATE_PORT_drone))
        time.sleep(0.1)  # 10 Hz (matches real Tello)


def sim_loop():
    global in_air,mission_pads
    camera = rl.Camera3D()
    camera.position = rl.Vector3(drone_state['x'],drone_state['h'],drone_state['z'])
    camera.target = rl.Vector3(drone_state['x']+1,drone_state['h'],drone_state['z'])
    camera.up = rl.Vector3(0,1,0)
    camera.fovy = 56.6
    camera.projection = rl.CAMERA_PERSPECTIVE


    mesh_drone = rl.gen_mesh_sphere(DRONE_SIZE/2,4,4)
    model_drone = rl.load_model_from_mesh(mesh_drone)

    mesh_cube = rl.gen_mesh_cube(0.7,1,1)
    model_cube = rl.load_model_from_mesh(mesh_cube)

    mesh_mission_pad = rl.gen_mesh_cube(DRONE_SIZE,0.1,0.5)
    model_mp = rl.load_model_from_mesh(mesh_mission_pad)
    pov = "drone"


    while not rl.window_should_close():

        ## drone Logic:

        duration =time.perf_counter()-last_keep_alive
        if duration > TIME_OUT and in_air:
            print("LANDING TIMEOUT:",duration,"____",TIME_OUT)
            with state_lock:
                go_coord(0,"h")
                in_air = False

        detect_mission_pad_underneath()

        ## Sim log:wic
        if rl.is_key_pressed(rl.KEY_ENTER) and not rl.is_key_pressed_repeat(rl.KEY_ENTER):
            print("enter pressed")
            if pov == "drone":
                pov = "top"
            elif pov == "top":
                pov = "drone"


        x,h,z = drone_state['x'],drone_state['h'],drone_state['z']

        if pov == "top":
            camera.position = rl.Vector3(1,25,1)
            camera.target = rl.Vector3(0,0,0)
        if pov == "drone":
            rot_v = calc_rotation_vector(drone_state["yaw"])
            camera.position = rl.Vector3(x,h,z)
            camera.target = rl.Vector3(x+rot_v[0],h,z+rot_v[1])

        t = calc_target_yaw(2)


        rl.clear_background(rl.WHITE)
        rl.begin_drawing()

        rl.begin_mode3d(camera)

        rl.draw_grid(60,1)
        rl.draw_model(model_drone,rl.Vector3(x,h,z),1,rl.BLUE)

        rl.draw_line3d(rl.Vector3(x,h,z),rl.Vector3(t.x,h,t.z),rl.RED)

        for mp in mission_pads:
            rl.draw_model(model_mp,mp.origin.to_vector(),1,rl.RED)

        rl.draw_model(model_cube,rl.Vector3(10,1,0),1,rl.RED)
        rl.draw_model(model_cube,rl.Vector3(-10,1,0),1,rl.BLUE)
        rl.draw_model(model_cube,rl.Vector3(0,1,10),1,rl.ORANGE)
        rl.draw_model(model_cube,rl.Vector3(0,1,-10),1,rl.GREEN)

        rl.end_mode3d()
        rl.end_drawing()
    rl.close_window()

# --------------------
# Main
# --------------------
if __name__ == "__main__":
    rl.init_window(920, 720, "3D base")

    cmd_thread = threading.Thread(target=command_server, daemon=True)
    state_thread = threading.Thread(target=state_server, daemon=True)

    cmd_thread.start()
    state_thread.start()

    print("Fake Tello simulator running")


    sim_loop()
