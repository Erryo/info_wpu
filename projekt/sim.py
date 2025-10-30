import raylibpy as rl
import numpy as np
import math

def main():
    rl.init_window(1920, 1080, "3D base")

    # camera
    camera = rl.Camera3D()
    camera.position = rl.Vector3(1,80,0)
    camera.target = rl.Vector3(0,0,0)
    camera.fovy = 45.0
    camera.projection = rl.CAMERA_PERSPECTIVE
    camera.up = rl.Vector3(0, 1, 0)  

    # models

    # cylinder
    mesh_cylinder = rl.gen_mesh_cylinder(0.4,2,20)
    model_cylinder = rl.load_model_from_mesh(mesh_cylinder)

    mesh_cube = rl.gen_mesh_cube(1,1,2)
    model_cube = rl.load_model_from_mesh(mesh_cube)
    model_cube_2 = rl.load_model_from_mesh(mesh_cube)

    delta_angle = 10
    distance_to_target = 20 #cm


    curr_x,curr_y = distance_to_target,distance_to_target
    drone = Drone()

    angle_to_obj = 0
    # move
    pos = rl.Vector3(7,1,-1)
    prev_dx = 0
    prev_dy = 0

    soll_x,soll_y = curr_x,curr_y

    rl.set_target_fps(60)
    while not rl.window_should_close():
        dx_x,dy_y =0,0
        dx_y,dy_x =0,0
        dx,dy =0,0

        if rl.is_key_pressed(rl.KEY_ENTER) or rl.is_key_down(rl.KEY_SPACE):
            angle_to_obj+=delta_angle
            drone.rotate_cntr_clck(delta_angle)
    
            soll_x,soll_y= rotate_vec(distance_to_target,0,angle_to_obj)
    
            dx_circle = soll_x-curr_x
            dy_circle = soll_y-curr_y
    
            dx_x,dy_x = drone.move("forward",dy_circle)
            dx_y,dy_y = drone.move("left",dx_circle)
    
            dx = dx_x+dx_y
            dy = dy_x+dy_y
    
            prev_dx = dx
            prev_dy = dy
    
            curr_x += dx
            curr_y += dy
    


        model_cube.transform = rl.matrix_rotate_y(math.radians(-drone.angle))
        rl.clear_background(rl.WHITE)
        rl.begin_drawing()

        rl.begin_mode3d(camera)

        rl.draw_grid(60,1)
        rl.draw_model(model_cylinder, rl.Vector3(0,0,0),1,rl.YELLOW)
        rl.draw_model(model_cube, rl.Vector3(curr_x,0,curr_y),1,rl.BLUE)
        rl.draw_model(model_cube_2, rl.Vector3(soll_x,0,soll_y),1,rl.GREEN)
        rl.draw_line3d(rl.Vector3(int(soll_x),2,int(soll_y)),rl.Vector3(int(curr_x),2,int(curr_y)),rl.BLUE)

        rl.end_mode3d()

        rl.draw_text("Angle: "+str(drone.angle),10,10,14,rl.RED)
        rl.draw_text("Delta: "+str(prev_dx)+" |--| "+str(prev_dy),10,30,14,rl.RED)
        rl.end_drawing()



    rl.close_window()


class Drone:
    def __init__(self) -> None:
        self.angle = 0

    def rotate_cntr_clck(self,angle):
        self.angle += angle
        self.angle = self.angle%360

    def move(self,direction,distance)->tuple[float,float]:
        if distance <0:
            distance = -distance
        x,y =0,0
        match direction:
            case "left":
                x = -distance
            case "right":
                x = distance
            case "forward":
                y = distance
            case "back":
                y = -distance

        nx,ny= rotate_vec(x,y,self.angle)

        return nx,ny
        



def rotate_vec(x,y,angle)->tuple[float,float]:

    rad = math.radians(angle)


    new_x = x*math.cos(rad)-y*math.sin(rad)
    new_y = x*math.sin(rad)+y*math.cos(rad)

    return new_x,new_y


if __name__ == "__main__":
    main()

