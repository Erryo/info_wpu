from time import sleep
import raylibpy as rl
import ctypes
import numpy as np
import balltracker as bt
import control as ctrl
import cv2

XBOX_ALIAS_1 = "xbox"
XBOX_ALIAS_2 = "x-box"

def main():
    rl.init_window(920, 720, "3D base")

    # camera
    camera = rl.Camera3D()
    camera.position = rl.Vector3(0,1,0)
    camera.target = rl.Vector3()
    camera.up = rl.Vector3(0,1,0)
    camera.fovy =56.6
    camera.projection = rl.CAMERA_PERSPECTIVE

    # models
    mesh_cube = rl.gen_mesh_cube(0.7,1,1)
    model_cube = rl.load_model_from_mesh(mesh_cube)

    # cylinder
    mesh_cylinder = rl.gen_mesh_cylinder(0.4,2,20)
    model_cylinder = rl.load_model_from_mesh(mesh_cylinder)


    mesh_sphere = rl.gen_mesh_sphere(0.4,10,29)
    model_sphere = rl.load_model_from_mesh(mesh_sphere)

    ball_tracker = bt.BallTracker(target=(rl.get_screen_width()//2,rl.get_screen_height()//2),min_r=0,max_r=100)
    # ball has to be center of screen in x achsis, tolerance 20px
    pid_x = ctrl.PIDControler(rl.get_screen_width()//2,0.0001,0.02,0.001,24)
    # ball has to be center of screen in y achsis,tolerance 20px
    pid_y = ctrl.PIDControler(rl.get_screen_height()//2,1,0.01,0.1,24)
    # radius has to be 30, tolerance 1px
    pid_z = ctrl.PIDControler(30,1,0.01,0.1,4)
    pid_z.logging = True
    pid_x.logging = True
    pid_y.logging = True


    # move
    pos = rl.Vector3(7,1,-1)
    angle = 0
    height = 1
    depth = -1
    success = False

    overlay_w = 920 
    overlay_h = 720 
    
    overlay_tex = rl.load_texture_from_image(
        rl.gen_image_color(overlay_w, overlay_h, rl.BLANK)
    )

    found_once = False
    centered = False
    rl.set_target_fps(60)
    while not rl.window_should_close():
                                              
        if rl.is_key_pressed(rl.KEY_A):
            pid_x.plot()
#        pos.z += vels[0]*10 * rl.get_frame_time()
#        pos.x -= vels[1]*10 * rl.get_frame_time()
#        pos.y -= vels[3]*10 * rl.get_frame_time() 
#

        if not found_once:
            angle -=10
        elif not centered:
            output_pid_x = pid_x.compute(ball_tracker.circle_x)                                                      
            print(output_pid_x)                                                                                      
            if not pid_x.reached_setpoint(ball_tracker.circle_x):                                                   
                angle += output_pid_x                                                                                
            else:                                                                                                    
                centered = True
                pid_x.plot()
                pid_x.reset()                                                                                        
            

        camera.target = rotate(angle)
        camera.target = (camera.target[0],height,camera.target[2])
        camera.position.y = height
        camera.position.x = depth


        rl.clear_background(rl.WHITE)
        rl.begin_drawing()

        rl.begin_mode3d(camera)

        rl.draw_grid(60,1)
        rl.draw_model(model_cylinder, rl.Vector3(10,0,-15),1,rl.YELLOW)
        rl.draw_model(model_cube,rl.Vector3(-7,3,-15),1,rl.BLUE)
        rl.draw_model(model_sphere,pos,1,rl.RED)
        #rl.draw_line3d(rl.Vector3(-4,0,-2),rl.Vector3(5,2,3), rl.BLACK)

        rl.end_mode3d()
        rl.draw_text("dRadius:"+str(ball_tracker.delta_radius),0,0,16,rl.BLACK)
        rl.draw_text("Radius:"+str(ball_tracker.circle_radius),0,30,16,rl.BLACK)
        image = rl.load_image_from_screen()


        scale = 0.35
        rl.draw_texture_ex(
            overlay_tex,
            rl.Vector2(10, 10),
            0.0,
            scale,
            rl.WHITE
        )

        rl.end_drawing()
        colors = rl.load_image_colors(image)
        size = image.width * image.height

        # Tell numpy to read it as (size, 4) uint8 array (RGBA order)
        buf_type = ctypes.c_uint8 * (size * 4)
        buf = ctypes.cast(colors, ctypes.POINTER(buf_type)).contents
        arr = np.frombuffer(buf, dtype=np.uint8).reshape((image.height, image.width, 4))
        frame = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        cv2.imwrite("save.png",frame)
        rl.unload_image_colors(colors)
        rl.unload_image(image)

        success = ball_tracker.calculate(frame)
        if success:
            if ball_tracker.circle_x != 0 :
                found_once = True
            print("found bal",ball_tracker.circle_x)
            rl.draw_circle_lines(int(ball_tracker.circle_x),int(ball_tracker.circle_y),int(ball_tracker.circle_radius)+4,rl.BLUE)
            rl.draw_circle_lines(int(ball_tracker.circle_x+ball_tracker.dx),int(ball_tracker.circle_y+ball_tracker.dy),int(pid_z.setpoint),rl.GREEN)
        else:
            pass
          #  ball_tracker.circle_x = pid_x.past_variables[-1]
          #  ball_tracker.circle_y = pid_y.past_variables[-1]
          #  ball_tracker.circle_radius= pid_z.past_variables[-1]

        if ball_tracker.mask is None:
            continue
#        rgb = cv2.cvtColor(ball_tracker.mask, cv2.COLOR_RGB2)   
 ##       rgba = cv2.cvtColor(rgb, cv2.COLOR_RGB2RGBA)   
        rgba = cv2.cvtColor(ball_tracker.mask, cv2.COLOR_RGB2RGBA)   
        rl.update_texture(overlay_tex, rgba.ctypes.data) 


    rl.close_window()

def rotate(angle) :
    angle = np.deg2rad(angle)
    rotate_x = np.sin(angle)
    rotate_y = np.cos(angle)
    return rotate_x*10,1,rotate_y*10

def do_joy_input(gamepad=0):
    rl.draw_text(f"GP{gamepad}: {rl.get_gamepad_name(gamepad)}", 10, 10, 10, rl.BLACK)
    velocities = [0.0,0.0,0.0,0.0]
    if rl.is_key_down(rl.KEY_A):
        velocities[0] =30
    if rl.is_key_down(rl.KEY_D):
        velocities[0] = -30

    if rl.is_gamepad_available(gamepad):
        # Axis values
        leftStickX = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_LEFT_X)
        leftStickY = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_LEFT_Y)
        rightStickX = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_RIGHT_X)
        rightStickY = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_RIGHT_Y)
#        leftTrigger = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_LEFT_TRIGGER)
#        rightTrigger = rl.get_gamepad_axis_movement(gamepad, rl.GAMEPAD_AXIS_RIGHT_TRIGGER)
        velocities = [leftStickX,leftStickY,rightStickX,rightStickY]
    return velocities


if __name__ == "__main__":
    main()

