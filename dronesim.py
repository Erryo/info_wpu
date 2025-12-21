import socket
import raylibpy as rl
import threading
import time
import control as ctrl
import math
import random


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
}

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

def go_point(point):
    print("going point x")
    go_coord(point[0],"x")
    print("going point z")
    go_coord(point[1],"z")

def go_point_diagonal(point):
    pid_x = ctrl.PIDControler(point[0],1/70,0,0,0.001)
    pid_z = ctrl.PIDControler(point[1],1/70,0,0,0.001)

    while (not pid_x.reached_setpoint(drone_state["x"])) or (not pid_z.reached_setpoint(drone_state["z"])):
        if not pid_x.reached_setpoint(drone_state["x"]):
            value = pid_x.compute(drone_state["x"]) 
            variability = random.uniform(0.9,1.1) 
            value *= variability                  
            drone_state["x"] += value             
        if not pid_z.reached_setpoint(drone_state["z"]): 
            value = pid_z.compute(drone_state["z"])      
            variability = random.uniform(0.9,1.1)        
            value *= variability                         
            drone_state["z"] += value                    

        time.sleep(random.uniform(0.003,0.009))



def calc_target(amount):
    x,h,z = drone_state["x"],drone_state["h"],drone_state["z"] 
    i_vector = calc_rotation_vector()                          
    target_delta = [i_vector[0]*amount,i_vector[1]*amount]     
    target = [target_delta[0]+x,target_delta[1]+z]             
    return target
#relative to current yaw(orientation)

def go_front(amount):
    print("going front")
    target = calc_target(amount)
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


def handle_annoying(cmd: str):
    if cmd.startswith("rc"):
        pass
    strs = cmd.split(" ")
    #relative
    x = int(strs[1])
    if strs[0] == "up":
        go_coord_delta(x,"y")
    if strs[0] == "down":
        go_coord_delta(-x,"y")
    if strs[0] == "forward":
        go_front(x)
    if strs[0] == "back":
        go_front(-x)
#        go_coord_delta(x,"x")
    if strs[0] == "cw":
        rotate_pid_delta(x,"yaw")
    if strs[0] == "ccw":
        rotate_pid_delta(-x,"yaw")


def calc_rotation_vector(): # aka. i_vectior
    with state_lock:
        yaw = drone_state['yaw']
        #print("yaw:",yaw)
        yaw = yaw*(math.pi/180)
        #print("yaw rad:",yaw)
    return [math.cos(yaw),math.sin(yaw)]



# --------------------
# Command server thread
# --------------------
def command_server():
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
            with state_lock:
                go_coord(4,'h')
            sock.sendto(b"ok", addr)

        elif cmd == "land":
            with state_lock:
                go_coord(0,'h')
            sock.sendto(b"ok", addr)

        else:
            handle_annoying(cmd)
            sock.sendto(b"ok", addr)

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
                f"agz:{i(drone_state['agz'])};\r\n"
            )

        sock.sendto(state_str.encode(), (CLIENT_IP, STATE_PORT_drone))
        time.sleep(0.1)  # 10 Hz (matches real Tello)


def sim_loop():
    camera = rl.Camera3D()
    camera.position = rl.Vector3(drone_state['x'],drone_state['h'],drone_state['z'])
    camera.target = rl.Vector3(drone_state['x']+1,drone_state['h'],drone_state['z'])
    camera.up = rl.Vector3(0,1,0)
    camera.fovy = 56.6
    camera.projection = rl.CAMERA_PERSPECTIVE


    mesh_drone = rl.gen_mesh_sphere(0.5,4,4)
    model_drone = rl.load_model_from_mesh(mesh_drone)
    
    mesh_cube = rl.gen_mesh_cube(0.7,1,1)
    model_cube = rl.load_model_from_mesh(mesh_cube)

    pov = "drone"

    while not rl.window_should_close():
        if rl.is_key_pressed(rl.KEY_ENTER) and not rl.is_key_pressed_repeat(rl.KEY_ENTER):
            print("enter pressed")
            if pov == "drone":
                pov = "top"
            elif pov == "top":
                pov = "drone"


        with state_lock:
            x,h,z = drone_state['x'],drone_state['h'],drone_state['z']

        if pov == "top":
            camera.position = rl.Vector3(1,25,1)
            camera.target = rl.Vector3(0,0,0)
        if pov == "drone":
            rot_v = calc_rotation_vector()
            camera.position = rl.Vector3(x,h,z)
            camera.target = rl.Vector3(x+rot_v[0],h,z+rot_v[1])

        t = calc_target(2)


        rl.clear_background(rl.WHITE)
        rl.begin_drawing()

        rl.begin_mode3d(camera)

        rl.draw_grid(60,1)
        rl.draw_model(model_drone,rl.Vector3(x,h,z),1,rl.BLUE)

        rl.draw_line3d(rl.Vector3(x,h,z),rl.Vector3(t[0],h,t[1]),rl.RED)
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
