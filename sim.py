import raylibpy as rl
import ctypes
import numpy as np
import balltracker as bt
import control as ctrl
import cv2


def main():
    rl.init_window(1920, 1080, "3D base")
    
    # camera 
    camera = rl.Camera3D()
    camera.position = rl.Vector3(0,1,0)
    camera.target = rl.Vector3()
    camera.up = rl.Vector3(0,1,0)
    camera.fovy = 45.0
    camera.projection = rl.CAMERA_PERSPECTIVE
    
    # models
    mesh_cube = rl.gen_mesh_cube(0.7,1,1)
    model_cube = rl.load_model_from_mesh(mesh_cube)
    
    # cylinder
    mesh_cylinder = rl.gen_mesh_cylinder(0.4,2,20)
    model_cylinder = rl.load_model_from_mesh(mesh_cylinder)
    

    mesh_sphere = rl.gen_mesh_sphere(0.4,10,29)
    model_sphere = rl.load_model_from_mesh(mesh_sphere)

    ball_tracker = bt.BallTracker(target=(rl.get_screen_width()//2,rl.get_screen_height()//2))
    pid_x = ctrl.PIDControler(rl.get_screen_width()//2,1,0.1,0.05)
   
    # move 
    pos = rl.Vector3(7,1,-15)
    angle = 180
    success = False
    
    rl.set_target_fps(10)
    while not rl.window_should_close():

        output_pid = pid_x.compute(ball_tracker.circle_x)

        output_pid = px_to_angle(output_pid)
        if not pid_x.reached_setpoint(ball_tracker.circle_x):
            angle += output_pid
        else:
            pid_x.plot()

        if rl.is_key_pressed(rl.KEY_A):
            angle += 10
        if rl.is_key_pressed(rl.KEY_D): 
            angle -= 10                 
        camera.target = rotate(angle)
        
        rl.clear_background(rl.WHITE)
        rl.begin_drawing()
        
        rl.begin_mode3d(camera)

        rl.draw_grid(60,1)
        rl.draw_model(model_cylinder, rl.Vector3(10,0,-15),1,rl.YELLOW)
        rl.draw_model(model_cube,rl.Vector3(-7,3,-15),1,rl.BLUE)
        rl.draw_model(model_sphere,pos,1,rl.RED)
        #rl.draw_line3d(rl.Vector3(-4,0,-2),rl.Vector3(5,2,3), rl.BLACK)

        rl.end_mode3d()

        rl.end_drawing()
        image = rl.load_image_from_screen()
        colors = rl.load_image_colors(image)
        size = image.width * image.height
        
        # Tell numpy to read it as (size, 4) uint8 array (RGBA order)
        buf_type = ctypes.c_uint8 * (size * 4)
        buf = ctypes.cast(colors, ctypes.POINTER(buf_type)).contents
        arr = np.frombuffer(buf, dtype=np.uint8).reshape((image.height, image.width, 4))
        frame = frame = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

        success = ball_tracker.calculate(frame)
        if success:
#            print(ball_tracker.circle_x,ball_tracker.circle_y)
            print(ball_tracker.dx)
            rl.draw_circle_lines(int(ball_tracker.circle_x),int(ball_tracker.circle_y),int(ball_tracker.circle_radius),rl.BLUE)
            rl.draw_circle_lines(int(ball_tracker.circle_x+ball_tracker.dx),int(ball_tracker.circle_y+ball_tracker.dy),int(ball_tracker.circle_radius),rl.GREEN)
        
        

    rl.close_window()

def px_to_angle(px):
    return  -px//1000
def rotate(angle) :
    angle = np.deg2rad(angle)
    rotate_x = np.sin(angle) 
    rotate_y = np.cos(angle)
    return rotate_x*10,1,rotate_y*10

if __name__ == "__main__":
    main()
