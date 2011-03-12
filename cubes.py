import sdxf
from enum import Enum
import random
random.seed()

cube_side = 16 # number of unit lengths per cube side. 1 unit length == material depth
sheet_size = (33,1000)
cube_grid = (((True,),),)

dimensions = [None,None,len(cube_grid)]
for plane in cube_grid:
	if dimensions[1] == None:
		dimensions[1] = len(plane)
	else:
		assert dimensions[1] == len(plane)
	for row in plane:
		if dimensions[0] == None:
			dimensions[0] = len(row)
		else:
			assert dimensions[0] == len(row)

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

	def addBox(self, coords, owner):
		assert [a for a in coords if a<0] == [], coords
		try:
			self.grid[coords[0]][coords[1]][coords[2]].append(owner)
		except IndexError:
			print coords
			raise

	def removeBox(self, coords, owner):
		assert [a for a in coords if a<0] == [], coords
		try:
			assert owner in self.grid[coords[0]][coords[1]][coords[2]]
			self.grid[coords[0]][coords[1]][coords[2]].remove(owner)
		except IndexError:
			print coords
			raise

	def fixCubes(self):

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
						if len(possibleOwner)!=1: # can't use it
							return None
						#assert len(possibleOwner) == 1, (possibleOwner, x2,y2,z2,x,y,z)
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
	
	def generateCubes(self,d):
		layers = {}

		for x in range(len(self.grid)):
			x2 = x+1
			for y in range(len(self.grid[x])):
				y2 = y+1
				for z in range(len(self.grid[x][y])):
					z2 = z+1

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
		self.grid = [[True for y in range(height)] for x in range(width)]
		self.direction = direction

		#print "face", origin, width, height, self.colour

		self.forAllCubes(space.addBox, (self,))

	def removeCubes(self):
		self.forAllCubes(space.removeBox, (self,))
	
	def forAllCubes(self, func, args):
		for a in range(self.width):
			for b in range(self.height):
				if self.direction == Direction.POS_X:
					func((self.origin[0], self.origin[1]+a, self.origin[2]+b), *args)
				elif self.direction == Direction.POS_Y:
					func((self.origin[0]+a, self.origin[1], self.origin[2]+b), *args)
				elif self.direction == Direction.POS_Z:
					func((self.origin[0]+a, self.origin[1]+b, self.origin[2]), *args)
				elif self.direction == Direction.NEG_X:
					func((self.origin[0]-1, self.origin[1]-a-1, self.origin[2]-b-1), *args)
				elif self.direction == Direction.NEG_Y:
					func((self.origin[0]-a-1, self.origin[1]-1, self.origin[2]-b-1), *args)
				elif self.direction == Direction.NEG_Z:
					func((self.origin[0]-a-1, self.origin[1]-b-1, self.origin[2]-1), *args)
				else:
					raise Exception, self.direction

	def deleteCube(self, x, y, z):
		#print self.origin, self.direction, (x,y,z)
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

	def _setChar(self, out, x,y, char):
		out[y] = out[y][:x] + char + out[y][x+1:]

	def printFace(self, path = []):
		out = dict([(a, " "*((self.width*2)+1)) for a in range((self.height*2)+1)])
		for x in range(len(self.grid)):
			for y in range(len(self.grid[x])):
				if self.grid[x][y]:
					self._setChar(out, (x*2)+1, (y*2)+1, "T")
				else:
					self._setChar(out, (x*2)+1, (y*2)+1, "F")
		
		if path!=[]:
			for a in range(len(path)-1):
				(x,y) = path[a]
				(x2,y2) = path[a+1]
				if y != y2:
					assert x == x2,(path[a],path[a+1])
					assert abs(y2-y) == 1,(path[a],path[a+1])
					if y2<y:
						y = y2
					for b in range(3):
						self._setChar(out, x*2, (y*2)+b, str(a)[-1])
				else:
					assert abs(x2-x) == 1,(x,x2)
					if x2<x:
						x = x2
					for b in range(3):
						self._setChar(out, (x*2)+b, y*2, str(a)[-1])

		#for y in sorted(out):
		#	print out[y]

	def makeOutline(self, d, place):
		pts = self.makeFaceOutline()
		d.append(sdxf.LwPolyLine(points=[(a+place[0],b+place[1]) for (a,b) in pts]))

	def makeFaceOutline(self):
		#self.printFace()
		x,y = 0,0
		while not self.grid[x][y]:
			#print "initial no good", x,y
			x +=1
		#print "start",x,y,self.grid[x][y]
		pts = []
		while True:
			#print x,y
			if (x,y) in pts:
				pts.append((x,y))
				#print pts
				#self.printFace(pts)
				assert pts[0] == (x,y)
				return pts
			pts.append((x,y))
			try:
				if y<self.height and x<self.width and self.grid[x][y] and (y==0 or not self.grid[x][y-1]):
					x +=1
					#print "move right to", x,y
				elif y<self.height and ((x>0 and x<self.width and not self.grid[x][y] and self.grid[x-1][y]) or (x == self.width and self.grid[x-1][y])):
					y +=1
					#print "move down to", x,y,
					#if x<self.width-1:
					#	print self.grid[x][y-1],self.grid[x-1][y-1]
					#else:
					#	print
				elif x<self.width and ((y!=0 and self.grid[x][y-1] and not self.grid[x-1][y-1]) or (x == 0 and self.grid[x][y-1])):
					y-=1
					#print "move up to", x,y
				elif x>0 and ((y<self.height and not self.grid[x-1][y]) or y == self.height):
					x-=1
					#print "move left to", x,y
				else:
					raise Exception
				if x<0 or y<0:
					raise Exception,(x,y)
			except Exception:
				print pts
				self.printFace(pts)
				raise

def cube_faces(space, topleft, cube_side):
	(x,y,z) = topleft
	(x2,y2,z2) = bottomright = (x+cube_side, y+cube_side, z+cube_side)

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

class CubeType(Enum):
	Filled = 1
	Empty = 2 # can be seen by an edge cube
	HiddenEmpty = 3 # can't been seen by edge

def find_nonhidden_cubes(grid, x,y,z):
	ret = []
	if x>0 and grid[z][y][x-1] == CubeType.HiddenEmpty:
		ret.append((x-1,y,z))
	if x<len(grid[z][y])-1 and grid[z][y][x+1] == CubeType.HiddenEmpty:
		ret.append((x+1,y,z))
	if y>0 and grid[z][y-1] == CubeType.HiddenEmpty:
		ret.append((x,y-1,z))
	if y<len(grid[z])-1 and grid[z][y+1][x] == CubeType.HiddenEmpty:
		ret.append((x,y+1,z))
	if z>0 and grid[z-1][y][x] == CubeType.HiddenEmpty:
		ret.append((x,y,z-1))
	if z<len(grid)-1 and grid[z+1][y][x] == CubeType.HiddenEmpty:
		ret.append((x,y,z+1))
	return ret

def find_empty_cubes(cube_grid):
	tocheck = []

	ret = []
	for z in range(len(cube_grid)):
		plane = []
		for y in range(len(cube_grid[z])):
			row = []
			for x in range(len(cube_grid[z][y])):
				if cube_grid[z][y][x]:
					row.append(CubeType.Filled)
				elif x == 0 or x == len(cube_grid[z][y])-1 or y == 0 or y == len(cube_grid[z])-1 or z == 0 or z == len(cube_grid)-1:
					row.append(CubeType.Empty)
					tocheck.append((x,y,z))
				else:
					row.append(CubeType.HiddenEmpty)
			plane.append(row)
		ret.append(plane)

	while len(tocheck)>0:
		(x,y,z) = tocheck[0]
		tocheck = tocheck[1:]
		newempty = find_nonhidden_cubes(ret, x,y,z)
		tocheck.extend(newempty)
		for (x,y,z) in newempty:
			ret[z][y][x] = CubeType.Empty

	return ret

if __name__ == "__main__":
	assert sheet_size[0]>cube_side and sheet_size[1]>cube_side, (sheet_size, cube_side)

	space = Space([a*cube_side for a in dimensions])
	faces = []

	grid = find_empty_cubes(cube_grid)

	print grid

	for z in range(len(cube_grid)):
		for y in range(len(cube_grid[z])):
			for x in range(len(cube_grid[z][y])):
				if cube_grid[z][y][x]:
					newfaces = cube_faces(space, (x*(cube_side-1),y*(cube_side-1),z*(cube_side-1)), cube_side)
					for face in newfaces:
						print face, face.direction
						if face.direction == Direction.NEG_X and (x == len(cube_grid[z][y])-1 or grid[z][y][x+1] == CubeType.Empty):
							faces.append(face)
						elif face.direction == Direction.NEG_Y and (y == len(cube_grid[z])-1 or grid[z][y+1][x] == CubeType.Empty):
							faces.append(face)
						elif face.direction == Direction.NEG_Z and (z == len(cube_grid)-1 or grid[z+1][y][x] == CubeType.Empty):
							faces.append(face)
						elif face.direction == Direction.POS_X and (x == 0 or grid[z][y][x-1] == CubeType.Empty):
							faces.append(face)
						elif face.direction == Direction.POS_Y and (y == 0 or grid[z][y-1][x] == CubeType.Empty):
							faces.append(face)
						elif face.direction == Direction.POS_Z and (z == 0 or grid[z-1][y][x] == CubeType.Empty):
							faces.append(face)
						else:
							print "skipping", face, face.direction
							face.removeCubes()

	blender = sdxf.Drawing()
	space.fixCubes()
	space.generateCubes(blender)
	blender.saveas('hello_world.dxf')

	plans = sdxf.Drawing()
	x,y = 0,0
	for face in sorted(faces):
		#print face, face.colour
		face.makeOutline(plans, (x,y))
		x += cube_side+1
		if x + cube_side > sheet_size[0]:
			x = 0
			y += cube_side +1
			assert y + cube_side < sheet_size[1]
	plans.saveas('plans.dxf')
