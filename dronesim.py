import socket
from cv2.typing import Point
import raylibpy as rl
import threading
import ctypes
import time
import control as ctrl
from fractions import Fraction
import math
import random
import numpy as np
import av
import cv2
import copy

import datetime

# --------------------
# Configuration
# --------------------
COMMAND_PORT = 8889
STATE_PORT = 8890

VS_PORT = 11111
CMD_PORT_drone = 8000
STATE_PORT_drone = 8001
HOST = "0.0.0.0"

# Where to send state (DJITelloPy listens locally)
CLIENT_IP = "127.0.0.1"
TIME_OUT=15 #s


DRONE_SIZE = 0.5



video_frame = None
video_lock = threading.Lock()
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

    def __init__(self,origin: Point3D,vector:Point3D,id) -> None:
        self.origin = origin
        self.vector = vector
        self.id = id
    def calc_target_point(self,origin=None)->Point3D:
        if origin is None:
            return Point3D(x=self.origin.x+self.vector.x,
                           y=self.origin.y+self.vector.y,
                           z=self.origin.z+self.vector.z)
        
        return Point3D(x=origin.x+self.vector.x, 
                       y=origin.y+self.vector.y, 
                       z=origin.z+self.vector.z) 
        

class SimState :
    def __init__(self) -> None:
        self.mesh_drone = rl.gen_mesh_sphere(DRONE_SIZE/2,4,4)
        self.model_drone = rl.load_model_from_mesh(self.mesh_drone)

        self.mesh_cube = rl.gen_mesh_cube(0.7,1,1)
        self.model_cube = rl.load_model_from_mesh(self.mesh_cube)

        self.mesh_mission_pad = rl.gen_mesh_cube(DRONE_SIZE,0.1,0.5)
        self.model_mp = rl.load_model_from_mesh(self.mesh_mission_pad)
        self.frame = []

in_air = False
stream_state = False

mp_0 = MissionPad(Point3D(100,100,100,),vector=Point3D(1,0,0),id=0)
mp_1 = MissionPad(Point3D(0,0,0,),vector=Point3D(1,0,0),id=1)
mp_2 = MissionPad(Point3D(20,0,0,),vector=Point3D(0,0,1),id=2)
mp_3 = MissionPad(Point3D(20,0,20,),vector=Point3D(-1,0,0),id=3)
mp_4 = MissionPad(Point3D(0,0,20,),vector=Point3D(0,0,-1),id=4)

mission_pads = [mp_0,mp_1,mp_2,mp_3,mp_4]
mission_pads_on = False
mission_pads_detection = 0
default_speed = 1




state_lock = threading.Lock()

def rc_dir(velocity:float,key:str):
    distance = velocity * 0.001
    target = drone_state[key]+distance
    while True:
        with state_lock:
            current_val = drone_state[key]
            if not reached_coord(current_val,target,0.06):
                drone_state[key] += distance/10
            else:
                return

def rc_normal_2D(velocity: float,offset:int = 0):
    #TIME_BTW_RC_CONTROL_COMMANDS = 0.001  # in seconds
    # top speed: 100cm/s
    # t = 0.001 s
    # d = 100cm/s * 0.001s = 0.1 cm
    #
    # 0.001s -?> 0.06 frames
    # 60 fps v = f/s
    # f = v * s = 60 fps * 0.001s = 0.06 frames
    # v = 1.667 cm/frame

    distance = velocity * 0.001
    target = calc_target_yaw(distance,offset)
    x_done = False
    y_done = False
    z_done = False
    while not ( x_done and y_done and z_done) :
        with state_lock:
            if not reached_coord(drone_state['h'],target.y,0.06):
                drone_state['h'] += distance/10
            else:
                y_done= True

            if not reached_coord(drone_state['x'],target.x,0.06):
                drone_state['x'] += distance/10
            else:
                x_done= True

            if not reached_coord(drone_state['z'],target.z,0.06):
                drone_state['z'] += distance/10
            else:
                z_done= True


def reached_coord(p:float,t:float,margin:float) -> bool:
    if p == t:
        return True
    return p < t + margin and p > t - margin



#absolute
def go_coord(target,key,speed = default_speed):
    pid = ctrl.PIDControler(target,1/70,0,0,0.001)

    while not pid.reached_setpoint(drone_state[key]):
        with state_lock:
            value = pid.compute(drone_state[key])
            variability = random.uniform(0.9,1.1)
            value *= variability*speed
            drone_state[key] += value
        time.sleep(random.uniform(0.003,0.009))


def go_point_diagonal(point: Point3D,speed=default_speed):
    pid_x = ctrl.PIDControler(point.x,1/70,0,0,0.1)
    pid_h = ctrl.PIDControler(point.y,1/70,0,0,0.1)
    pid_z = ctrl.PIDControler(point.z,1/70,0,0,0.1)

    numb_pids_done = 0
    x_done = False
    y_done = False
    z_done = False
    while numb_pids_done <3:
        with state_lock:
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

def go_point_mid(p: Point3D,id: int,speed: int = default_speed):
    mp = MissionPad(Point3D(0,0,0),Point3D(1,0,0),0)
    for pad in mission_pads:
        if pad.id == id :
            mp = pad

    x,h,z = mp.origin.x,mp.origin.y,mp.origin.z
    target = Point3D(x=p.x+x,y=p.y+h,z=p.z+z)
    print("target is x:",target.x," y:",target.y," z:",target.z)
    go_point_diagonal(target,speed)


# Relative to drone
def go_point_diagonal_delta(p: Point3D,speed=default_speed):
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

def go_normal_2D(amount,yaw_offset=0,speed=default_speed):
    print("going normal:",yaw_offset+drone_state["yaw"])
    target = calc_target_yaw(amount,yaw_offset)
    go_point_diagonal(target,speed=default_speed)


def rotate_pid(target,key,speed=default_speed):
    pid = ctrl.PIDControler(target,1/70,1/10000,0,0.01)
    while not pid.reached_setpoint(drone_state[key]):
        with state_lock:
            value = pid.compute(drone_state[key])
            variability = random.uniform(0.98,1.02)
            value *= variability*speed
            drone_state[key] += value
        time.sleep(random.uniform(0.003,0.009))

def rotate_pid_delta(target,key):
    target = drone_state[key]+target
    rotate_pid(target=target,key=key)

#absolute
def go_coord_delta(target,key: str):
    target = drone_state[key]+target
    go_coord(target=target,key=key)
def calc_vector_angle(a: Point3D, b: Point3D) -> float:
    magnitude_a = calc_magnitude(a)
    magnitude_b = calc_magnitude(b)

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Cannot compute angle with zero-length vector")

    dot_prod = calc_dot_product(a, b)
    cos_angle = dot_prod / (magnitude_a * magnitude_b)

    # Clamp due to floating-point precision
    cos_angle = max(-1.0, min(1.0, cos_angle))

    return math.degrees(math.acos(cos_angle))

def calc_dot_product(a:Point3D,b:Point3D) -> float :
    return (a.x*b.x +
        a.y*b.y +
        a.z*b.z)

def calc_magnitude(v:Point3D) -> float:
    return math.sqrt(v.x**2+v.y**2+v.z**2)

def calc_yaw_point(yaw=drone_state["yaw"]):
    yaw = yaw*(math.pi/180) # convert to rad
    return Point3D(x=math.cos(yaw),y=0,z=math.sin(yaw))

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


def handle_variable(cmd: str):
    global mission_pads_detection,default_speed
    if not in_air:
        return b"error not in air"
    strs = cmd.split(" ")
    #relative
    x = int(strs[1])
    match strs[0]:
        case "mdirection":
            with state_lock:
                mission_pads_detection = x
        case "speed":
            with state_lock:
                default_speed = x
        case "up":
            go_coord_delta(x,"h")
        case "down":
            go_coord_delta(-x,"h")
        case "forward":
            go_normal_2D(x)
        case "back":
            go_normal_2D(-x)
        case "right":
            go_normal_2D(x,90)
        case "left":
            go_normal_2D(-x,90)
        case "cw":
            rotate_pid_delta(x,"yaw")
        case "ccw":
            rotate_pid_delta(-x,"yaw")
        case "rc":
                left_right= int(strs[1])
                forward_back= int(strs[2])
                up_down= int(strs[3])
                yaw= int(strs[4])

                if yaw != 0:
                    rc_dir(yaw*10,"yaw")
#                    rotate_pid_delta(yaw,"yaw")
                #forward
                if forward_back != 0:
                    rc_normal_2D(forward_back)
                    #go_normal_2D(forward_back)
                #lr
                if left_right != 0:
                    rc_normal_2D(left_right,90)
                    #go_normal_2D(left_right,90)
                if up_down != 0:
                    rc_dir(up_down,"h")
                    #go_coord_delta(up_down,"h")


        case "go":
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
        case "jump":
            x= int(strs[1]) #x in tello coord
            z= int(strs[2]) #y 
            h= int(strs[3]) #z
            print("jumping:x",x," y",h," z:",z)
            speed= int(strs[4])
            yaw = int(strs[5])
            mid_1=int(strs[6].removeprefix("m"))
            mid_2=int(strs[7].removeprefix("m"))
            print("mid is:",mid_1)
            print("mid Target is:",mid_2)
            go_point_mid(Point3D(x=x,y=h,z=z),mid_1,speed)
            go_point_mid(Point3D(x=0,y=h,z=0),mid_2,speed)
            yaw_point= calc_yaw_point(drone_state["yaw"])     
            mp = mission_pads[mid_2]             
                                                              
            angle_diff=calc_vector_angle(yaw_point,mp.vector) 
            rotate_pid_delta(angle_diff,"yaw")
            



    return b"ok"







# --------------------
# Command server thread
# --------------------
def command_server():
    global in_air,last_keep_alive,mission_pads_on,stream_state
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, COMMAND_PORT))

    print("Command server listening on UDP 8889")

    while True:
        data, addr = sock.recvfrom(1024)
        cmd = data.decode("utf-8").strip()
#        print(f"[CMD] {addr}: {cmd}")


        match (cmd):
            case "command":
                sock.sendto(b"ok", addr)
            case "takeoff":
                if in_air:
                    sock.sendto(b"error", addr)
                    return
                go_coord(4,'h')
                with state_lock:
                    in_air = True
                sock.sendto(b"ok", addr)

            case "keepalive":
                with state_lock:
                    last_keep_alive = time.perf_counter()
                sock.sendto(b"ok", addr)
            case "mon":
                with state_lock:
                    mission_pads_on = True
                sock.sendto(b"ok", addr)
            case "moff":
                with state_lock:
                    mission_pads_on = False
                sock.sendto(b"ok", addr)
            case "streamoff":
                with state_lock:
                    stream_state = False
                sock.sendto(b"ok", addr)
            case "streamon":
                with state_lock:
                    stream_state = True
                sock.sendto(b"ok", addr)
            case "land" | "emergency":
                if not in_air:
                      sock.sendto(b"error", addr)
                      return
                go_coord(0,'h')
                with state_lock:
                    in_air = False
                sock.sendto(b"ok", addr)
            case _:
                res = handle_variable(cmd)
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

def draw_world(state:SimState):
        x,h,z = drone_state['x'],drone_state['h'],drone_state['z']
        t = calc_target_yaw(2)
        rl.draw_grid(60,1)
        rl.draw_model(state.model_drone,rl.Vector3(x,h,z),1,rl.BLUE)

        rl.draw_line3d(rl.Vector3(x,h,z),rl.Vector3(t.x,h,t.z),rl.RED)

        for mp in mission_pads:
            rl.draw_model(state.model_mp,mp.origin.to_vector(),1,rl.RED)
            origin = copy.copy(mp.origin)
            origin.y += 0.2
            rl.draw_line3d(origin.to_vector(),mp.calc_target_point(origin).to_vector(),rl.BLUE)

        rl.draw_model(state.model_cube,rl.Vector3(10,1,0),1,rl.RED)
        rl.draw_model(state.model_cube,rl.Vector3(-10,1,0),1,rl.BLUE)
        rl.draw_model(state.model_cube,rl.Vector3(0,1,10),1,rl.ORANGE)
        rl.draw_model(state.model_cube,rl.Vector3(0,1,-10),1,rl.GREEN)

def sim_loop(state: SimState):
    global in_air,mission_pads,mission_pads_on,video_frame
    drone_cam = rl.Camera3D()
    top_cam = rl.Camera3D()

    drone_cam.up = rl.Vector3(0,1,0)
    drone_cam.fovy = 56.6
    drone_cam.projection = rl.CAMERA_PERSPECTIVE

    top_cam.up = rl.Vector3(0,1,0)
    top_cam.fovy = 56.6
    top_cam.projection = rl.CAMERA_PERSPECTIVE


    pov = drone_cam
    drone_rt = rl.load_render_texture(960, 720)


    while not rl.window_should_close():

        ## drone Logic:

#        duration =time.perf_counter()-last_keep_alive
#        if duration > TIME_OUT and in_air:
#            print("LANDING TIMEOUT:",duration,"____",TIME_OUT)
#            with state_lock:
#                go_coord(0,"h")
#                in_air = False
#
        if mission_pads_on:
            detect_mission_pad_underneath()

        ## Sim log:wic
        if rl.is_key_pressed(rl.KEY_ENTER) and not rl.is_key_pressed_repeat(rl.KEY_ENTER):
            print("enter pressed")
            if pov == drone_cam:
                pov = top_cam
            elif pov == top_cam:
                pov = drone_cam


        x,h,z = drone_state['x'],drone_state['h'],drone_state['z']
        rot_v = calc_rotation_vector(drone_state["yaw"])

        drone_cam.position = rl.Vector3(x, h, z)
        drone_cam.target   = rl.Vector3(x + rot_v[0], h, z + rot_v[1])

        top_cam.position = rl.Vector3(x+1, h+30, z+1)
        top_cam.target   = rl.Vector3(x, h,z)



        rl.begin_texture_mode(drone_rt)
        rl.clear_background(rl.WHITE)

        rl.begin_mode3d(drone_cam)
        draw_world(state)
        rl.end_mode3d()

        rl.end_texture_mode()

        image = rl.load_image_from_texture(drone_rt.texture)
        rl.image_flip_vertical(image)  # IMPORTANT
        colors = rl.load_image_colors(image)
        size = image.width * image.height

        # Tell numpy to read it as (size, 4) uint8 array (RGBA order)
        buf_type = ctypes.c_uint8 * (size * 4)
        buf = ctypes.cast(colors, ctypes.POINTER(buf_type)).contents
        arr = np.frombuffer(buf, dtype=np.uint8).reshape((image.height, image.width, 4))
        frame = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

        #print(f"Generated frame: {frame.shape}, dtype: {frame.dtype}")
        with video_lock:
            video_frame = frame.copy()

        rl.unload_image_colors(colors)
        rl.unload_image(image)


        rl.clear_background(rl.WHITE)
        rl.begin_drawing()

        rl.begin_mode3d(pov)

        draw_world(state)

        rl.end_mode3d()

        yaw_point= calc_yaw_point(drone_state["yaw"])
        mp = mission_pads[drone_state["mid"]]

        angle_diff=calc_vector_angle(yaw_point,mp.vector)
        rl.draw_text(f"x:{round(drone_state['x'],3)};h:{round(drone_state['h'],3)};z:{round(drone_state['z'],3)};yaw:{round(drone_state['yaw'],3)};diff:{round(angle_diff,3)}",0,0,24,rl.RED) 
        rl.draw_text(f"mid:{drone_state['mid']}",0,30,24,rl.RED) 
#        rl.draw_text(f"mp_1.v: x:{round(mp.vector.x,3)}; y: {round(mp.vector.y,3)}; z: {round(mp.vector.z,3)}",0,30,24,rl.RED) 
#        rl.draw_text(f"yaw.v: x:{round(yaw_point.x,3)}; y: {round(yaw_point.y,3)}; z: {round(yaw_point.z,3)}",0,70,24,rl.RED) 
        rl.end_drawing()
    rl.close_window()

def video_stream_server(): # Thanks ClaudeAI!!!!!!!!!!!!!    :)))))))))))
    global stream_state, video_frame, video_lock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (CLIENT_IP, VS_PORT)

    print("Video stream server started on UDP 11111")

    frame_count = 0
    codec = None
    last_keyframe = 0

    while True:
        if not stream_state:
            if codec is not None:
                try:
                    # Flush encoder
                    packets = codec.encode(None)
                    for packet in packets:
                        sock.sendto(bytes(packet), addr)
                except:
                    pass
                codec = None
                frame_count = 0
                last_keyframe = 0
            time.sleep(0.05)
            continue

        # Initialize codec when stream starts
        if codec is None:
            codec = av.CodecContext.create("libx264", "w")
            codec.width = 960
            codec.height = 720
            codec.framerate = Fraction(30, 1)
            codec.time_base = Fraction(1, 90000)  # Standard H.264 timebase
            codec.pix_fmt = "yuv420p"
            codec.bit_rate = 2000000  # 2 Mbps
            codec.options = {
                "preset": "ultrafast",
                "tune": "zerolatency",
                "profile": "baseline",
                "level": "3.0",
                "g": "30",  # Keyframe every 30 frames (1 second)
                "bf": "0",  # No B-frames for low latency
            }
            try:
                codec.open()
                frame_count = 0
                last_keyframe = 0
                print("Video codec initialized and opened")
            except Exception as e:
                print(f"Failed to open codec: {e}")
                codec = None
                time.sleep(1)
                continue

        # Get frame
        with video_lock:
            if video_frame is None:
                time.sleep(0.01)
                continue
            frame = video_frame.copy()

        try:
            # Convert BGR to VideoFrame
            av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
            av_frame = av_frame.reformat(codec.width, codec.height, codec.pix_fmt)

            # Set PTS with proper timebase
            av_frame.pts = frame_count * 3000  # 90000/30 = 3000 per frame

            # Force keyframe every 30 frames
            if frame_count - last_keyframe >= 30:
                av_frame.pict_type = av.video.frame.PictureType.I
                last_keyframe = frame_count

            frame_count += 1

            # Encode
            packets = codec.encode(av_frame)

            # Add after encoding in video_stream_server:
            if packets:
                total_bytes = sum(len(bytes(p)) for p in packets)
                #print(f"Frame {frame_count}: {len(packets)} packets, {total_bytes} bytes")

            # Send all packets
            for packet in packets:
                data = bytes(packet)
                if len(data) > 0:
                    # UDP packet size limit
                    MAX_DGRAM = 60000
                    if len(data) <= MAX_DGRAM:
                        sock.sendto(data, addr)
                    else:
                        # Split large packets (shouldn't happen with ultrafast preset)
                        print(f"Warning: Packet too large ({len(data)} bytes), splitting")
                        for i in range(0, len(data), MAX_DGRAM):
                            sock.sendto(data[i:i+MAX_DGRAM], addr)

        except Exception as e:
            print(f"Video encoding error: {e}")
            import traceback
            traceback.print_exc()
            codec = None
            continue

        time.sleep(1 / 30)
def video_stream_server_reduced():
    global stream_state, video_frame, video_lock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (CLIENT_IP, VS_PORT)

    print("Video stream server started on UDP 11111")

    frame_count = 0
    codec = None
    last_keyframe = 0

    while True:
        if not stream_state:
            if codec is not None:
                try:
                    packets = codec.encode(None)
                    for packet in packets:
                        sock.sendto(bytes(packet), addr)
                except:
                    pass
                codec = None
                frame_count = 0
                last_keyframe = 0
            time.sleep(0.05)
            continue

        if codec is None:
            codec = av.CodecContext.create("libx264", "w")
            codec.width = 960
            codec.height = 720
            codec.framerate = Fraction(30, 1)
            codec.time_base = Fraction(1, 90000)
            codec.pix_fmt = "yuv420p"
            codec.bit_rate = 500000  # Reduced from 2Mbps to 500kbps
            codec.options = {
                "preset": "ultrafast",
                "tune": "zerolatency",
                "profile": "baseline",
                "level": "3.0",
                "g": "30",
                "bf": "0",
                "crf": "28",  # Higher = more compression (0-51, 23 is default)
            }
            try:
                codec.open()
                frame_count = 0
                last_keyframe = 0
                print("Video codec initialized and opened")
            except Exception as e:
                print(f"Failed to open codec: {e}")
                codec = None
                time.sleep(1)
                continue

        with video_lock:
            if video_frame is None:
                time.sleep(0.01)
                continue
            frame = video_frame.copy()

        try:
            av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
            av_frame = av_frame.reformat(codec.width, codec.height, codec.pix_fmt)
            av_frame.pts = frame_count * 3000

            if frame_count - last_keyframe >= 30:
                av_frame.pict_type = av.video.frame.PictureType.I
                last_keyframe = frame_count

            frame_count += 1
            packets = codec.encode(av_frame)

            for packet in packets:
                data = bytes(packet)
                if len(data) > 0:
                    # Real Tello uses ~1400 byte chunks for reliability
                    MAX_DGRAM = 1400
                    if len(data) <= MAX_DGRAM:
                        sock.sendto(data, addr)
                    else:
                        # Fragment into small packets
                        for i in range(0, len(data), MAX_DGRAM):
                            sock.sendto(data[i:i+MAX_DGRAM], addr)

        except Exception as e:
            print(f"Video encoding error: {e}")
            codec = None
            continue

        time.sleep(1 / 30)
# --------------------
# Main
# --------------------
if __name__ == "__main__":
    rl.init_window(920, 720, "3D base")
    rl.set_trace_log_level(rl.TraceLogLevel.LOG_ERROR)

    state = SimState()
    cmd_thread = threading.Thread(target=command_server, daemon=True)
    state_thread = threading.Thread(target=state_server, daemon=True)
    video_thread = threading.Thread(
        target=video_stream_server_reduced,
        daemon=True
    )

    cmd_thread.start()
    state_thread.start()
    video_thread.start()

    print("Fake Tello simulator running")


    sim_loop(state)
