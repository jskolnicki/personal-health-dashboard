import time
from blinkstick import blinkstick

def color_to_rgb(color):
    color_map = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "purple": (128, 0, 128),
        "cyan": (0, 255, 255),
        "white": (255, 255, 255),
    }
    return color_map.get(color.lower(), (255, 255, 255))  # Default to white if color not found

def set_color(color, brightness=100):
    bstick = blinkstick.find_first()
    if bstick is None:
        print("No BlinkStick found")
        return
    
    r, g, b = color_to_rgb(color)
    
    # Apply brightness
    r = int(r * brightness / 100)
    g = int(g * brightness / 100)
    b = int(b * brightness / 100)
    
    bstick.set_color(red=r, green=g, blue=b)

def indicate_status(status, persist=False):
    if status == "success":
        set_color("green")
    elif status == "error":
        set_color("red")
    elif status == "warning":
        set_color("yellow")
    elif status == "processing":
        blink_processing()
    else:
        print(f"Unknown status: {status}")
    
    if not persist:
        time.sleep(5)
        turn_off()

def blink_processing(duration=10):
    bstick = blinkstick.find_first()
    if bstick is None:
        print("No BlinkStick found")
        return
    
    end_time = time.time() + duration
    while time.time() < end_time:
        set_color("blue")
        time.sleep(0.5)
        turn_off()
        time.sleep(0.5)

def turn_off():
    bstick = blinkstick.find_first()
    if bstick:
        bstick.turn_off()