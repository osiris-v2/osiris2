def f():
    print("THIS FILE USE COMMON MODULE")


    
    
class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


def print_color(text, color,end=""):
    return color + text + Color.ENDC + end
