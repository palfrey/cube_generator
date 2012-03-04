from cubes import *
import random
random.seed(9)

(height, depth, width) = (25, 4, 31)
#(height, depth, width) = (8, 4, 12)

space = Space([height, depth, width],[1,1,1])

grid = find_empty_cubes([[[1]]])

print grid

cube_side = 8
topleft = (0,0,0)
(x,y,z) = topleft
(x2,y2,z2) = bottomright = (height, depth, width)

assert x<x2,(x,x2)
assert y<y2,(y,y2)
assert z<z2,(z,z2)

faces = []

faces.append(Face(Direction.POS_Z,x2-x,y2-y,topleft,space))
faces.append(Face(Direction.POS_X,y2-y,z2-z,topleft,space))
#faces.append(Face(Direction.POS_Y,3,z2-z,topleft,space))
faces.append(Face(Direction.POS_Y,x2-x-4,2,topleft,space))
faces.append(Face(Direction.POS_Y,x2-x-4,2,(0,0,width-2),space))

faces.append(Face(Direction.NEG_Z,x2-x,y2-y,bottomright,space))
#faces.append(Face(Direction.NEG_X,y2-y,z2-z,bottomright,space))
faces.append(Face(Direction.NEG_Y,x2-x,z2-z,bottomright,space))

blender = sdxf.Drawing()
space.fixCubes(cube_side)
space.generateCubes(blender)
blender.saveas('holder-3d.dxf')

# reindex all of the faces as there's a few missing after the hidden-face removal
for newindex,face in enumerate(sorted(faces, key=operator.attrgetter("index"))):
	face.index = newindex

plans = Plans((100,200), 'holder-plans-%d.dxf')

facesDone = []

for face in sorted(faces, key=operator.attrgetter("index")):
	#print face, face.colour
	if face in facesDone:
		continue
	data = face.makeOutline(True)
	plans.place(data["outline"], data["size"])

	facesDone.extend(data["faces"])
plans.finished()
