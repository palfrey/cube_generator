import sdxf
from enum import Enum
import random
import operator
from optparse import OptionParser, OptionValueError
import math

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

		for key in sorted(pairs):
			(first, second) = key
			current = random.choice(key) # pick random starting piece

			#print "fixing", first, second, sorted(pairs[key])

			for (x,y,z) in sorted(pairs[key]):
				self.grid[x][y][z] = [current]
				if current == first:
					current.markNeighbour(second,x,y,z)
					current = second
				else:
					current.markNeighbour(first,x,y,z)
					current = first
				current.deleteCube(x,y,z) # this should be the "other" face

		for x in range(len(self.grid)):
			x2 = x+1
			for y in range(len(self.grid[x])):
				y2 = y+1
				for z in range(len(self.grid[x][y])):
					z2 = z+1

					def pickOwner(x2,y2,z2):
						if x2 <0 or y2<0 or z2<0 or x2>=dimensions[0]*opts.cube_side or y2>=dimensions[1]*opts.cube_side or z2>=dimensions[2]*opts.cube_side:
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

					if len(self.grid[x][y][z]) == 0:
						continue

					owner = self.grid[x][y][z][0]

					if owner.colour.value() not in layers:
						layers[owner.colour.value()] = ("layer-%d"%owner.colour.value()).upper()
						d.layers.append(sdxf.Layer(name=layers[owner.colour.value()], color=owner.colour.value()))

					def doSide(points):
						d.append(sdxf.Face(points=points, layer=layers[owner.colour.value()]))

					doSide([(x,y,z),(x2,y,z),(x2,y2,z),(x,y2,z)])
					doSide([(x,y,z),(x,y2,z),(x,y2,z2),(x,y,z2)])
					doSide([(x,y,z),(x2,y,z),(x2,y,z2),(x,y,z2)])
					 
					doSide([(x2,y2,z2),(x,y2,z2),(x,y,z2),(x2,y,z2)])
					doSide([(x2,y2,z2),(x2,y,z2),(x2,y,z),(x2,y2,z)])
					doSide([(x2,y2,z2),(x,y2,z2),(x,y2,z),(x2,y2,z)])

class DXFColours(Enum):
	Red = 1
	Yellow = 2
	Green = 3
	Cyan = 4
	Blue = 5
	Magenta = 6 
	White = 7

class Face:
	colours = list(iter(DXFColours))
	last_colour = -1
	last_index = -1

	def __init__(self, direction, width, height, origin, space):
		self.colour = Face.colours[Face.last_colour+1]
		if Face.last_colour +2 >= len(Face.colours):
			Face.last_colour = -1
		else:
			Face.last_colour +=1
		self.index = Face.last_index +1
		Face.last_index +=1
		self.width = width
		self.height = height
		self.origin = list(origin)
		self.grid = [[True for y in range(height)] for x in range(width)]
		self.direction = direction
		self.neighbour = [None for x in range(4)]

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
	
	def _translateLocation(self, x, y, z):
		if self.direction == Direction.POS_X:
			assert self.origin[0] == x,x
			assert y>=self.origin[1] and y<self.origin[1]+self.width,y
			assert z>=self.origin[2] and z<self.origin[2]+self.height,z
			assert self.grid[y-self.origin[1]][z-self.origin[2]]
			return (y-self.origin[1],z-self.origin[2])
		elif self.direction == Direction.POS_Y:
			assert x>=self.origin[0] and x<self.origin[0]+self.width,x
			assert self.origin[1] == y,y
			assert z>=self.origin[2] and z<self.origin[2]+self.height,z
			assert self.grid[x-self.origin[0]][z-self.origin[2]]
			return (x-self.origin[0],z-self.origin[2])
		elif self.direction == Direction.POS_Z:
			assert x>=self.origin[0] and x<self.origin[0]+self.width,x
			assert y>=self.origin[1] and y<self.origin[1]+self.width,y
			assert self.origin[2] == z,z
			assert self.grid[x-self.origin[0]][y-self.origin[1]]
			return (x-self.origin[0],y-self.origin[1])
		elif self.direction == Direction.NEG_X:
			assert self.origin[0]-1 == x,x
			assert y<self.origin[1] and y>self.origin[1]-self.height-1,y
			assert z<self.origin[2] and z>self.origin[2]-self.height-1,z
			assert self.grid[self.origin[1]-y-1][self.origin[2]-z-1]
			return (self.origin[1]-y-1,self.origin[2]-z-1)
		elif self.direction == Direction.NEG_Y:
			assert x<self.origin[0] and x>self.origin[0]-self.width-1,x
			assert self.origin[1]-1 == y,y
			assert z<self.origin[2] and z>self.origin[2]-self.height-1,z
			assert self.grid[self.origin[0]-x-1][self.origin[2]-z-1]
			return (self.origin[0]-x-1,self.origin[2]-z-1)
		elif self.direction == Direction.NEG_Z:
			assert x<self.origin[0] and x>self.origin[0]-self.width-1,x
			assert y<self.origin[1] and y>self.origin[1]-self.height-1,y
			assert self.origin[2]-1 == z,z
			assert self.grid[self.origin[0]-x-1][self.origin[1]-y-1]
			return (self.origin[0]-x-1,self.origin[1]-y-1)
		else:
			raise Exception, self.direction

	def deleteCube(self, x, y, z):
		(x2,y2) = self._translateLocation(x,y,z)
		self.grid[x2][y2] = False

	def markNeighbour(self, other, x, y, z):
		(x2,y2) = self._translateLocation(x,y,z)

		if x2 == 0:
			assert y2>0 and y2<self.height-1, (x2,y2)
			assert self.neighbour[0] in (None, other)
			self.neighbour[0] = other
		elif y2 == 0:
			assert x2>0 and x2<self.width-1, (x2,y2)
			assert self.neighbour[1] in (None, other)
			self.neighbour[1] = other
		elif x2 == self.width-1:
			assert y2>0 and y2<self.height-1, (x2,y2)
			assert self.neighbour[2] in (None, other)
			self.neighbour[2] = other
		elif y2 == self.height-1:
			assert x2>0 and x2<self.width-1, (x2,y2)
			assert self.neighbour[3] in (None, other)
			self.neighbour[3] = other
		else:
			raise Exception, (x2,y2, x,y,z, self.direction)

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

		for y in sorted(out):
			print out[y]

	def drawNumber(self, char, x, y, width, height, layer, reverse = False):
		char = int(char)
		assert char>=0 and char<=9, char
		if char == 1:
			return [sdxf.Line(points=[(x+width/2,y),(x+width/2,y+height)], layer=layer)]
		ret = []
		if char in [0,2,3,5,6,7,8,9]: # top bar
			ret.append(sdxf.Line(points=[(x,y),(x+width,y)], layer=layer))
		if char in [0,1,4,8,9] or (reverse and char in [2,3,7]) or (not reverse and char in [5,6]): # top-right
			ret.append(sdxf.Line(points=[(x+width,y),(x+width,y+height/2)], layer=layer))
		if char in [0,1,6,8] or (reverse and char in [3,4,5,7,9]) or (not reverse and char in [2]): # bottom-right
			ret.append(sdxf.Line(points=[(x+width,y+height/2),(x+width,y+height)], layer=layer))
		if char in [0,2,3,5,6,8,9]: # bottom bar
			ret.append(sdxf.Line(points=[(x+width,y+height),(x,y+height)], layer=layer))
		if char in [0,4,8,9] or (reverse and char in [5,6]) or (not reverse and char in [2,3,7]): # top-left
			ret.append(sdxf.Line(points=[(x,y),(x,y+height/2)], layer=layer))
		if char in [0,6,8] or (reverse and char in [2]) or (not reverse and char in [3,4,5,7,9]): # bottom-left
			ret.append(sdxf.Line(points=[(x,y+height/2),(x,y+height)], layer=layer))
		if char in [2,3,4,5,6,8,9]: # middle bar
			ret.append(sdxf.Line(points=[(x,y+height/2),(x+width,y+height/2)], layer=layer))
		return ret

	def centredText(self, text,x,y,width,height, reverse=False):
		spacing = 0.05
		spacing = (self.width-2.0)/24
		if spacing < 0.25:
			spacing = 0.25

		print "spacing", spacing

		itemWidth = (width-((len(text)+1)*spacing))/len(text)
		ret = []
		if not reverse:
			text = tuple(reversed(text))
		for i in range(len(text)):
			ret.extend(self.drawNumber(text[i], x+(i*(itemWidth+spacing))+spacing,y+spacing,itemWidth,height-(spacing*2),layer="TEXT_LAYER", reverse = reverse))
		return ret

	def makeNumbers(self, reverse):
		outline = []

		# text spacing is 1/4 for the first item, 2/4 for the centre and 1/4 for the last
		horizspace = (self.width-2.0)/3 # unit (i.e 1/4) for horizontal spacing. -2 to cope with notches
		vertspace = (self.height-2.0)/3
		print "width",self.width,horizspace,vertspace

		outline.extend(self.centredText("%d"%self.index, 1+horizspace, 1+vertspace, horizspace, vertspace, reverse))

		assert [x for x in self.neighbour if x==None] == [],self.neighbour
		print self.index,[x.index for x in self.neighbour],self.colour, self.direction, reverse

		outline.extend(self.centredText("%d"%self.neighbour[0].index, 1, 1+vertspace, horizspace, vertspace, reverse))
		outline.extend(self.centredText("%d"%self.neighbour[1].index, 1+horizspace, 1, horizspace, vertspace, reverse))
		outline.extend(self.centredText("%d"%self.neighbour[2].index, 1+(horizspace*2), 1+vertspace, horizspace, vertspace, reverse))
		outline.extend(self.centredText("%d"%self.neighbour[3].index, 1+horizspace, 1+(vertspace*2), horizspace, vertspace, reverse))
		return outline

	def makeOutline(self, invert=False, spacing = 0):
		place = (0,0)
		outline = []

		# These pieces have their directions on the wrong side, so they need flipping
		reverse = self.direction in [Direction.POS_Y, Direction.NEG_Z, Direction.NEG_X]

		if invert:
			reverse = not reverse

		toTest = [place]
		tested = []
		neighbourSet = {place:self}

		while len(toTest)>0:
			point = toTest[0]
			toTest = toTest[1:]
			current = neighbourSet[point]
			(x,y) = point
			for value in range(len(current.neighbour)):
				n = current.neighbour[value]
				if n in tested:
					continue
				if n.direction!=current.direction:
					continue
				print "neighbour", n
				
				if value == 0:
					if reverse:
						newPoint = (x-self.width+1-spacing, y)
					else:
						newPoint = (x+self.width-1+spacing, y)
				elif value == 1:
					newPoint = (x, y+self.height-1+spacing)
				elif value == 2:
					if reverse:
						newPoint = (x+self.width-1+spacing, y)
					else:
						newPoint = (x-self.width+1-spacing, y)
				elif value == 3:
					newPoint = (x, y-self.height+1-spacing)
				neighbourSet[newPoint] = n
				toTest.append(newPoint)
			tested.append(current)

		for point in neighbourSet:
			thisOutline = []
			(x,y) = point
			current = neighbourSet[point]
			pts = current.makeFaceOutline()
			thisOutline.append(sdxf.LwPolyLine(points=pts))
			thisOutline.extend(current.makeNumbers(reverse))
			thisOutline.extend(current.markUnused(reverse))

			# rotate all the items 180 degrees so they're the right way up in QCad
			for item in thisOutline:
				if reverse: # except the reverse ones, which just want flipping
					item.points = [(x+a,y-b+self.height) for (a,b) in item.points]
				else:
					item.points = [(x-a+self.width,y-b+self.height) for (a,b) in item.points]

			outline.extend(thisOutline)

		found = {}
		for item in outline:
			if not isinstance(item, sdxf.LwPolyLine):
				continue
			sequence = [tuple(sorted((item.points[a],item.points[a+1]))) for a in range(len(item.points)-1)]
			for pair in sequence:
				if pair not in found:
					found[pair] = 1
				else:
					found[pair] +=1

		for item in outline:
			if not isinstance(item, sdxf.LwPolyLine):
				continue
			sequence = [(item.points[a],item.points[a+1]) for a in range(len(item.points)-1)]
			sequence = [pair for pair in sequence if found[tuple(sorted(pair))]==1]

			newpts = [[]]
			for a in range(len(sequence)-1):
				if sequence[a][1] == sequence[a+1][0]:
					newpts[-1].append(sequence[a][0])
				else:
					newpts[-1].extend(sequence[a])
					newpts.append([])

			if len(newpts[0])==0:
				continue
			
			try:
				newpts[-1].extend(sequence[-1])
			except IndexError:
				for pts in newpts:
					print "pts",pts
				print "item.points",item.points
				print "sequence",sequence
				raise

			if len(newpts)>1 or newpts[0]!=item.points:
				for pts in newpts:
					print "pts",pts
				print "item.points",item.points
				print "sequence",sequence
				#raise Exception

			item.points = newpts[0]
			for pts in newpts[1:]:
				outline.append(sdxf.LwPolyLine(points=pts))

		smallest = [0,0]
		for item in outline:
			for (x,y) in item.points:
				if x<smallest[0]:
					smallest[0] = x
				if y<smallest[1]:
					smallest[1] = y
		
		offset = [-smallest[a] for a in range(2)]

		size = [0,0]
		for item in outline:
			newpts = [list(p) for p in item.points]
			for p in newpts:
				
				p[0] += offset[0]
				p[1] += offset[1]
				
				for a in range(2):
					size[a] = max(size[a], p[a])
			item.points = newpts

		print "size", size
		return {"faces":neighbourSet.values(), "outline":outline, "size": size}
	
	def markUnused(self, reverse):
		outline = []
		number = "%d"%self.index
		assert len(number)>0
		for x in range(self.width):
			for y in range(self.height):
				if not self.grid[x][y]:
					outline.extend(self.centredText(number,x+0.25,y+0.25,.5,.5,reverse=reverse))
		print self.index, "unused outline",[x.points for x in outline]
		return outline

	def makeFaceOutline(self):
		#self.printFace()
		x,y = 0,0
		while not self.grid[x][y]:
			#print "initial no good", x,y
			x +=1
			if x == self.width:
				raise Exception, "Sanity failure, doesn't look like a valid piece"
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

class Plans(sdxf.Drawing):
	def __init__(self, sheet_size):
		sdxf.Drawing.__init__(self)
		self.sheet_size = sheet_size
		self.used = [[False for y in range(sheet_size[1])] for x in range(sheet_size[0])]

	def place(self, items, size):
		x,y = 0,0
		while True:
			assert y + size[1] < self.sheet_size[1], "Design can't fit on one sheet"
			for x2 in range(x, x+size[0]+1):
				for y2 in range(y, y+size[1]+1):
					if self.used[x2][y2]:
						x = x2+1
						if self.sheet_size[0] < x+size[0]+1:
							x = 0
							y +=1
						break
				else:
					continue # if no break in inner loop, can continue
				break
			else:
				print "occupied", x,y, size
				# found a space
				for x2 in range(x, x+size[0]+1):
					for y2 in range(y, y+size[1]+1):
						self.used[x2][y2] = True
				for item in items:
					newpts = [list(p) for p in item.points]
					for p in newpts:
						p[0] += x
						p[1] += y
					item.points = newpts
				self.extend(items)
				break

if __name__ == "__main__":

	parser = OptionParser()
	parser.add_option("-c","--cube-side",default=6,type="int",dest="cube_side",help="Number of unit lengths per cube side")

	def size_callback(option, opt_str, value, parser):
		items = value.split(",")
		if len(items)!=2:
			raise OptionValueError, "%s is an invalid sheet size"%value
		
		try:
			value = [int(x) for x in items]
		except ValueError:
			raise OptionValueError, "%s is an invalid sheet size"%value

		setattr(parser.values, option.dest, value)

	parser.add_option("-s","--sheet-size", default=(100,200),action="callback", callback=size_callback, nargs=1, dest="sheet_size",type="string")
	parser.add_option("-r","--random-seed",default=None, dest="seed")
	parser.add_option("-i","--invert-pieces",action="store_true",default=False,dest="invert",help="Generate pieces with instructions on the outside")
	parser.add_option("--spacing",default=0,type="int", dest="spacing")

	(opts,args) = parser.parse_args()

	if opts.cube_side < 4:
		parser.error("Cube sides must be at least 4")

	if len(args)!=1:
		parser.error("Need a specification file")

	try:
		data = file(args[0])
	except IOError:
		parser.error("Can't open '%s'"%args[0])
	cube_grid = []
	plane = []
	for line in data.readlines():
		line = line.strip()
		if len(line)==0:
			cube_grid.append(plane)
			plane = []
		else:
			if [x for x in line if x not in ('*', '-')]!=[]:
				parser.error("'%s' is an invalid row!"%line)
			row = [x == '*' for x in line]
			plane.append(row)

	if plane!=[]:
		cube_grid.append(plane)

	random.seed(opts.seed)

	if opts.sheet_size[0]<opts.cube_side:
		parser.error("Sheet is less wide than the cube size!")
	if opts.sheet_size[1]<opts.cube_side:
		parser.error("Sheet is less long than the cube size!")

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

	space = Space([a*opts.cube_side for a in dimensions])
	faces = []

	grid = find_empty_cubes(cube_grid)

	print grid

	for z in range(len(cube_grid)):
		for y in range(len(cube_grid[z])):
			for x in range(len(cube_grid[z][y])):
				if cube_grid[z][y][x]:
					newfaces = cube_faces(space, (x*(opts.cube_side-1),y*(opts.cube_side-1),z*(opts.cube_side-1)), opts.cube_side)
					for face in newfaces:
						print face, face.index, face.direction
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
	blender.saveas(args[0]+'-3d.dxf')

	# reindex all of the faces as there's a few missing after the hidden-face removal
	for newindex,face in enumerate(sorted(faces, key=operator.attrgetter("index"))):
		face.index = newindex

	plans = Plans(opts.sheet_size)

	for layer in plans.layers:
		if layer.name == "TEXT_LAYER":
			break
	else:
		plans.layers.append(sdxf.Layer(name="TEXT_LAYER", color=DXFColours.Blue.value()))

	facesDone = []

	for face in sorted(faces, key=operator.attrgetter("index")):
		#print face, face.colour
		if face in facesDone:
			continue
		data = face.makeOutline(opts.invert, opts.spacing)
		plans.place(data["outline"], data["size"])
		facesDone.extend(data["faces"])
	plans.saveas(args[0]+'-plans.dxf')
