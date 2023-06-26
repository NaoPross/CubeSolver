from . import graphics
from . import cube
from . import vision


# Initial setup
cube_view = graphics.RubikCube()

# Code that runs in a loop forever (until the window is closed)

def update():
	print("Hello")

graphics.loop(update, cube_view.render)
