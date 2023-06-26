# Python standard library
import sys
import enum

# Graphics stuff
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from .clifford import Vec3


class Face(Vec3):
	# Along z axis
	NORTH = Vec3(0, 0, 1)
	SOUTH = Vec3(0, 0, -1)
	# Along y axis
	EAST = Vec3(0, 1, 0)
	WEST = Vec3(0, -1, 0)
	# Along x axis
	FRONT = Vec3(1, 0, 0)
	BACK  = Vec3(-1, 0, 0)

	def __init__(self, *coords):
		super().__init__(coords)

	@staticmethod
	def faces():
		return [Face.NORTH, Face.SOUTH, Face.EAST,
			Face.WEST, Face.FRONT, Face.BACK]


class Color(enum.Enum):
	WHITE  = (255, 255, 255)
	RED    = (183, 18, 52)
	YELLOW = (255, 213, 0)
	BLUE   = (0, 70, 173)
	ORANGE = (255, 88, 0)
	GREEN  = (0, 155, 72)
	BLACK  = (0, 0, 0)


class Cubie:
	def __init__(self, position=(0, 0, 0), size=1, faces={}):
		# Save cube parameters
		self.position = position
		self.rotation = None
		self.size = size
		self.faces = faces

		# print(f"New cubie at {self.position}, size {self.size}, and with faces {self.faces}")

		# Create cube verticies and quads
		F = Face
		self.verticies = (
			F.NORTH + F.EAST, F.NORTH + F.WEST,
			F.NORTH + F.FRONT, F.NORTH + F.BACK,
			F.BACK + F.EAST, F.BACK + F.WEST,
			F.BACK + F.FRONT, F.BACK + F.BACK
		)

		self.quads = {
			F.NORTH: (
				F.NORTH + F.EAST + F.BACK,
				F.NORTH + F.WEST + F.BACK,
				F.NORTH + F.WEST + F.FRONT,
				F.NORTH + F.EAST + F.FRONT,
			),
			F.SOUTH: (
				F.SOUTH + F.EAST + F.BACK,
				F.SOUTH + F.EAST + F.FRONT,
				F.SOUTH + F.WEST + F.FRONT,
				F.SOUTH + F.WEST + F.BACK,
			),
			F.EAST: (
				F.NORTH + F.EAST + F.BACK,
				F.NORTH + F.EAST + F.FRONT,
				F.SOUTH + F.EAST + F.FRONT,
				F.SOUTH + F.EAST + F.BACK,
			),
			F.WEST: (
				F.NORTH + F.WEST + F.BACK,
				F.SOUTH + F.WEST + F.BACK,
				F.SOUTH + F.WEST + F.FRONT,
				F.NORTH + F.WEST + F.FRONT,
			),
			F.FRONT: (
				F.NORTH + F.EAST + F.FRONT,
				F.NORTH + F.WEST + F.FRONT,
				F.SOUTH + F.WEST + F.FRONT,
				F.SOUTH + F.EAST + F.FRONT,
			),
			F.BACK: (
				F.NORTH + F.EAST + F.BACK,
				F.NORTH + F.WEST + F.BACK,
				F.SOUTH + F.WEST + F.BACK,
				F.SOUTH + F.EAST + F.BACK,
			),
		}

	def render(self):
		glPushMatrix()
		glTranslatef(*self.position)
		glScalef(self.size / 2., self.size / 2., self.size / 2.)

		# Draw the face of the cubie
		glBegin(GL_QUADS)
		for face in Face.faces():
			color = self.faces.get(face, Color.BLACK)
			glColor3ub(*color.value)
			for vertex in self.quads[face]:
				glVertex3f(*vertex)
		glEnd()

		# Draw a black wireframe
		glLineWidth(GLfloat(2.))
		glColor3ub(*Color.BLACK.value)
		for face in Face.faces():
			glBegin(GL_LINE_LOOP)
			for vertex in self.quads[face]:
				glVertex3f(*vertex)
			glEnd()
		glPopMatrix()


class RubikCube:
	def __init__(self, position=(0, 0, 0), size=1):
		# To keep track of rotations
		self.turning = None
		self.angle = 0
		self.turn_speed = 5

		# Define the structure of the Rubik cube
		F = Face
		C = Color
		cube_structure = {
			# Front corner pieces
			F.NORTH + F.EAST + F.FRONT: {
				F.NORTH: C.ORANGE,
				F.EAST: C.BLUE,
				F.FRONT: C.WHITE
			},
			F.NORTH + F.WEST + F.FRONT: {
				F.NORTH: C.ORANGE,
				F.WEST: C.GREEN,
				F.FRONT: C.WHITE
			},
			F.SOUTH + F.WEST + F.FRONT: {
				F.SOUTH: C.RED,
				F.WEST: C.GREEN,
				F.FRONT: C.WHITE,
			},
			F.SOUTH + F.EAST + F.FRONT: {
				F.SOUTH: C.RED,
				F.EAST: C.BLUE,
				F.FRONT: C.WHITE
			},
			# Back corner pieces
			F.NORTH + F.EAST + F.BACK: {
				F.BACK: C.YELLOW,
				F.NORTH: C.ORANGE,
				F.EAST: C.BLUE,
			},
			F.NORTH + F.WEST + F.BACK: {
				F.BACK: C.YELLOW,
				F.NORTH: C.ORANGE,
				F.WEST: C.GREEN,
			},
			F.SOUTH + F.WEST + F.BACK: {
				F.BACK: C.YELLOW,
				F.SOUTH: C.RED,
				F.WEST: C.GREEN,
			},
			F.SOUTH + F.EAST + F.BACK: {
				F.BACK: C.YELLOW,
				F.SOUTH: C.RED,
				F.EAST: C.BLUE,
			},
			# Front edges
			F.NORTH + F.FRONT: { F.FRONT: C.WHITE, F.NORTH: C.ORANGE, },
			F.EAST + F.FRONT: { F.FRONT: C.WHITE, F.EAST: C.BLUE, },
			F.WEST + F.FRONT: { F.FRONT: C.WHITE, F.WEST: C.GREEN, },
			F.SOUTH + F.FRONT: { F.FRONT: C.WHITE, F.SOUTH: C.RED, },
			# Middle edges
			F.NORTH + F.EAST: { F.NORTH: C.ORANGE, F.EAST: C.BLUE, },
			F.NORTH + F.WEST: { F.NORTH: C.ORANGE, F.WEST: C.GREEN, },
			F.SOUTH + F.EAST: { F.SOUTH: C.RED, F.EAST: C.BLUE, },
			F.SOUTH+ F.WEST: { F.SOUTH: C.RED, F.WEST: C.GREEN, },
			# Back edges
			F.NORTH + F.BACK: { F.BACK: C.YELLOW, F.NORTH: C.ORANGE, },
			F.EAST + F.BACK: { F.BACK: C.YELLOW, F.EAST: C.BLUE, },
			F.WEST + F.BACK: { F.BACK: C.YELLOW, F.WEST: C.GREEN, },
			F.SOUTH + F.BACK: { F.BACK: C.YELLOW, F.SOUTH: C.RED, },
			# Middle pieces
			F.FRONT: { F.FRONT: C.WHITE },
			F.BACK: { F.BACK: C.YELLOW },
			F.NORTH: { F.NORTH: C.ORANGE },
			F.SOUTH: { F.SOUTH: C.RED },
			F.EAST: { F.EAST: C.BLUE },
			F.WEST: { F.WEST: C.GREEN },
		}

		self.cubies = []
		for pos, faces in cube_structure.items():
			pos = (size * 1.1) * pos
			c = Cubie(pos, size, faces)
			self.cubies.append(c)

	def turn(self, face, angle=90):
		self.turning = face
		self.angle = 90

	def render(self):
		for cubie in self.cubies:
			cubie.render()


def loop(update, render):
	# We want a framerate of 60 FPS, dt is in milliseconds
	dt = int(1e3/60)
	display = (800, 600)

	# Initialize graphics, create window
	pygame.init()
	pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
	pygame.display.set_caption("Rubik Cube Solver")

	# Enable the painter's algorithm and setup nicer rendering
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_LINE_SMOOTH)
	glEnable(GL_POLYGON_SMOOTH)
	# glEnable(GL_BLEND)
	# glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	# Setup and move camera
	camera = (0, 0, -15)
	aspect_ratio = display[0] / display[1]
	gluPerspective(45, aspect_ratio, 0.1, 50)
	glTranslatef(*camera)

	# Setup background
	glClearColor(1., 1., 1., 1.)

	# Start inifinite loop
	while True:
		# Process events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_SPACE:
					# Update logic
					update()

		# Clear screen and render new stuff
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glRotatef(.8, -1, 1, 1)
		render()

		pygame.display.flip()

		# Wait
		pygame.time.wait(dt);
