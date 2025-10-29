import pygame as pg                                        
from djitellopy import tello                               
import sys                                                 
import numpy as np                                         
import time                                                
import cv2                                                 
                                                           
import imgproc                                             
                                                           
Speed = 10                                                 
Should_quit = False                                        
Track_Ball = False                                         
font = None                                                
                                                           
X = 1                                                      
Y = 0                                                      
Z = 2                                                      
R = 3                                                      
                                                           
# CCF9F8                                                   
def write(screen,text,location,color=(255,255,255)):       
    global font                                            
    if font is not None:                                   
        screen.blit(font.render(text,True,color),location) 
                                                           
                                                           
def main():                                                
                                                           
    global font                                            
    global Track_Ball                                      
                                                           
    drone_conn = True                                      
    drone = tello.Tello()                                  
    print(drone)                                           
    try:                                                   
        drone.connect()                                    
        drone.streamon()                                   
#        drone.takeoff()                                   
    except:                                                
        drone_conn = False                                 
        print("Error",drone,type(drone))                   
