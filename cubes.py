import sdxf
from enum import Enum
import random
random.seed()

d = sdxf.Drawing()

#d.layers.append(sdxf.Layer(name="textlayer",color=3))

dimensions = (1,1,1) # cube count in x/y/z
cube_side = 6 # number of unit lengths per cube side. 1 unit length == material depth

cube_size = (cube_side, cube_side, cube_side)

class Direction(Enum):
	POS_X = 1
	POS_Y = 2
	POS_Z = 3
	NEG_X = 4
	NEG_Y = 5
	NEG_Z = 6

class Space:
	def __init__(self, size):
		assert len(size) == 3, size
		self.grid = [[[[] for z in range(size[2])] for y in range(size[1])] for x in range(size[0])]

	def addBox(self, owner, coords):
		assert [a for a in coords if a<0] == [], coords
		try:
			self.grid[coords[0]][coords[1]][coords[2]].append(owner)
		except IndexError:
			print coords
			raise

	def generateCubes(self, d):
		layers = {}

		pairs = {}

		# pairs first
		for x in range(len(self.grid)):
			for y in range(len(self.grid[x])):
				for z in range(len(self.grid[x][y])):
					if len(self.grid[x][y][z]) == 2:
						key = tuple(sorted(self.grid[x][y][z]))
						if key not in pairs:
							pairs[key] = []
						pairs[key].append((x,y,z))

		for key in pairs:
			(first, second) = key
			current = random.choice(key) # pick random starting piece

			#print "fixing", first, second, sorted(pairs[key])

			for (x,y,z) in sorted(pairs[key]):
				self.grid[x][y][z] = [current]
				if current == first:
					current = second
				else:
					current = first
				current.deleteCube(x,y,z) # this should be the "other" face

		for x in range(len(self.grid)):
			x2 = x+1
			for y in range(len(self.grid[x])):
				y2 = y+1
				for z in range(len(self.grid[x][y])):
					z2 = z+1

					def pickOwner(x2,y2,z2):
						if x2 <0 or y2<0 or z2<0 or x2>=dimensions[0]*cube_side or y2>=dimensions[1]*cube_side or z2>=dimensions[2]*cube_side:
							return None
						possibleOwner = self.grid[x2][y2][z2]
						if len(possibleOwner) == 0: # nothing there
							return None
						assert len(possibleOwner) == 1, (possibleOwner, x2,y2,z2,x,y,z)
						possibleOwner = possibleOwner[0]
						if possibleOwner in self.grid[x][y][z]:
							return possibleOwner
						else:
							return None

					if len(self.grid[x][y][z])>1:
						axes = range(3)
						random.shuffle(axes)
						for axe in axes:
							if axe == 0: # X
								poss = pickOwner(x-1,y,z)
								if poss:
									break
								poss = pickOwner(x+1,y,z)
								if poss:
									break
							elif axe == 1: # Y
								poss = pickOwner(x,y-1,z)
								if poss:
									break
								poss = pickOwner(x,y+1,z)
								if poss:
									break
							elif axe == 2: # Z
								poss = pickOwner(x,y,z-1)
								if poss:
									break
								poss = pickOwner(x,y,z+1)
								if poss:
									break
							else:
								raise Exception, axe # shouldn't happen
						assert poss != None
						for owner in self.grid[x][y][z]:
							if owner == poss:
								continue
							owner.deleteCube(x,y,z)
						self.grid[x][y][z] = [poss]

					for owner in self.grid[x][y][z]:
						if owner.colour not in layers:
							layers[owner.colour] = ("layer-%d"%owner.colour).upper()
							d.layers.append(sdxf.Layer(name=layers[owner.colour], color=owner.colour))

						d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y2,z),(x,y2,z)], layer=layers[owner.colour]))
						d.append(sdxf.Face(points=[(x,y,z),(x,y2,z),(x,y2,z2),(x,y,z2)], layer=layers[owner.colour]))
						d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y,z2),(x,y,z2)], layer=layers[owner.colour]))
						 
						d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y,z2),(x2,y,z2)], layer=layers[owner.colour]))
						d.append(sdxf.Face(points=[(x2,y2,z2),(x2,y,z2),(x2,y,z),(x2,y2,z)], layer=layers[owner.colour]))
						d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y2,z),(x2,y2,z)], layer=layers[owner.colour]))
class Face:
	colours = tuple(range(1,8))
	last_colour = -1

	def __init__(self, direction, width, height, origin, space):
		self.colour = Face.colours[Face.last_colour+1]
		if Face.last_colour +2 > len(Face.colours):
			Face.last_colour = -1
		else:
			Face.last_colour +=1
		assert width>=3, width
		assert height>=3, height
		self.width = width
		self.height = height
		self.origin = list(origin)
		self.grid = [[True for x in range(height)] for y in range(width)]
		self.direction = direction

		print "face", origin, width, height, self.colour

		for a in range(width):
			for b in range(height):
				if self.direction == Direction.POS_X:
					space.addBox(self, (origin[0], origin[1]+a, origin[2]+b))
				elif self.direction == Direction.POS_Y:
					space.addBox(self, (origin[0]+a, origin[1], origin[2]+b))
				elif self.direction == Direction.POS_Z:
					space.addBox(self, (origin[0]+a, origin[1]+b, origin[2]))
				elif self.direction == Direction.NEG_X:
					space.addBox(self, (origin[0]-1, origin[1]-a-1, origin[2]-b-1))
				elif self.direction == Direction.NEG_Y:
					space.addBox(self, (origin[0]-a-1, origin[1]-1, origin[2]-b-1))
				elif self.direction == Direction.NEG_Z:
					space.addBox(self, (origin[0]-a-1, origin[1]-b-1, origin[2]-1))
				else:
					raise Exception, self.direction

	def deleteCube(self, x, y, z):
		print self.origin, self.direction, (x,y,z)
		if self.direction == Direction.POS_X:
			assert self.origin[0] == x,x
			assert y>=self.origin[1] and y<self.origin[1]+self.width,y
			assert z>=self.origin[2] and z<self.origin[2]+self.height,z
			#(origin[0], origin[1]+a, origin[2]+b))
			assert self.grid[y-self.origin[1]][z-self.origin[2]]
			self.grid[y-self.origin[1]][z-self.origin[2]] = False
		elif self.direction == Direction.POS_Y:
			assert x>=self.origin[0] and x<self.origin[0]+self.width,x
			assert self.origin[1] == y,y
			assert z>=self.origin[2] and z<self.origin[2]+self.height,z
			#(origin[0]+a, origin[1], origin[2]+b))
			assert self.grid[x-self.origin[0]][z-self.origin[2]]
			self.grid[x-self.origin[0]][z-self.origin[2]] = False
		elif self.direction == Direction.POS_Z:
			assert x>=self.origin[0] and x<self.origin[0]+self.width,x
			assert y>=self.origin[1] and y<self.origin[1]+self.width,y
			assert self.origin[2] == z,z
			# (origin[0]+a, origin[1]+b, origin[2]))
			assert self.grid[x-self.origin[0]][y-self.origin[1]]
			self.grid[x-self.origin[0]][y-self.origin[1]] = False
		elif self.direction == Direction.NEG_X:
			assert self.origin[0]-1 == x,x
			assert y<self.origin[1] and y>self.origin[1]-self.height-1,y
			assert z<self.origin[2] and z>self.origin[2]-self.height-1,z
			#space.addBox(self, (origin[0]-1, origin[1]-a-1, origin[2]-b-1))
			assert self.grid[y-self.origin[1]][z-self.origin[2]]
			self.grid[y-self.origin[1]][z-self.origin[2]] = False
		elif self.direction == Direction.NEG_Y:
			assert x<self.origin[0] and x>self.origin[0]-self.width-1,x
			assert self.origin[1]-1 == y,y
			assert z<self.origin[2] and z>self.origin[2]-self.height-1,z
			#space.addBox(self, (origin[0]-a-1, origin[1]-1, origin[2]-b-1))
			assert self.grid[self.origin[0]-x-1][self.origin[2]-z-1]
			self.grid[self.origin[0]-x-1][self.origin[2]-z-1] = False
		elif self.direction == Direction.NEG_Z:
			assert x<self.origin[0] and x>self.origin[0]-self.width-1,x
			assert y<self.origin[1] and y>self.origin[1]-self.height-1,y
			assert self.origin[2]-1 == z,z
			#space.addBox(self, (origin[0]-a-1, origin[1]-b-1, origin[2]-1))
			assert self.grid[self.origin[0]-x-1][self.origin[1]-y-1]
			self.grid[self.origin[0]-x-1][self.origin[1]-y-1] = False
		else:
			raise Exception, self.direction

def cuboid(space, topleft, bottomright):
	ret = []


def cube_faces(space, topleft, bottomright):
	if topleft > bottomright:
		temp = topleft
		topleft = bottomright
		bottomright = temp

	(x,y,z) = topleft
	(x2,y2,z2) = bottomright

	assert x<x2,(x,x2)
	assert y<y2,(y,y2)
	assert z<z2,(z,z2)

	ret = []

	ret.append(Face(Direction.POS_Z,x2-x,y2-y,topleft,space))
	ret.append(Face(Direction.POS_X,y2-y,z2-z,topleft,space))
	ret.append(Face(Direction.POS_Y,x2-x,z2-z,topleft,space))

	ret.append(Face(Direction.NEG_Z,x2-x,y2-y,bottomright,space))
	ret.append(Face(Direction.NEG_X,y2-y,z2-z,bottomright,space))
	ret.append(Face(Direction.NEG_Y,x2-x,z2-z,bottomright,space))

	return ret

space = Space([a*cube_side for a in dimensions])
cubes = cube_faces(space, (0,0,0), cube_size)

space.generateCubes(d)

d.saveas('hello_world.dxf')
