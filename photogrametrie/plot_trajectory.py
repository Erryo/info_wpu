import sys
import math
import matplotlib.pyplot as plt




def main():

    photo_dir =  "Test1/images/"
    delta_angle = 30
    distance_to_target = 50 #cm
    angle = 0
    x,y = 0,0

    index = 0
    coords = []

    # Starte eine Schleife, die läuft, bis wir sie stoppen
    should_quit = False
    while not should_quit:
        # Gehe alle Tasten durch, die der Benutzer gedrückt hat
        #
        index += 1
        angle += delta_angle
        if angle > 720 :
            break



        x  = math.cos(math.radians(angle)) * distance_to_target
        y  = math.sin(math.radians(angle)) * distance_to_target
        coords.append((x,y))

        print("Going to:",int(x),int(y))

    draw_points(coords)
                                                                                  
    # beende das Python-Programm
    sys.exit()


def draw_points(coords):
    """Draw a list of 2D points (x, y) on a Cartesian plane."""
    if not coords:
        print("No coordinates to plot.")
        return

    # Split list of tuples into two lists: xs and ys
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]

    plt.figure(figsize=(8, 8))
    plt.scatter(xs, ys, s=40)        # draw points
    plt.plot(xs, ys, linestyle='-')  # connect them if desired

    plt.axhline(0, color='black', linewidth=1)  # x-axis
    plt.axvline(0, color='black', linewidth=1)  # y-axis

    plt.title("2D Point Plot")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')  # equal scaling
    plt.show()


if __name__ == "__main__":
    main()

