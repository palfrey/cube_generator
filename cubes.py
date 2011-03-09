import sdxf

d = sdxf.Drawing()

#d.layers.append(sdxf.Layer(name="textlayer",color=3))

dimensions = (1,1,1) # cube count in x/y/z
cube_size = 8 # number of unit lengths per cube size. 1 unit length == material depth

cube_size = (cube_size, cube_size, cube_size)

def cuboid(d, topleft, bottomright):
	(x,y,z) = topleft
	(x2,y2,z2) = bottomright
	d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y2,z),(x,y2,z)]))
	d.append(sdxf.Face(points=[(x,y,z),(x,y2,z),(x,y2,z2),(x,y,z2)]))
	d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y,z2),(x,y,z2)]))

	d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y,z2),(x2,y,z2)]))
	d.append(sdxf.Face(points=[(x2,y2,z2),(x2,y,z2),(x2,y,z),(x2,y2,z)]))
	d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y2,z),(x2,y2,z)]))

def cube_faces(d, topleft, bottomright):
	(x,y,z) = topleft
	(x2,y2,z2) = bottomright

	cuboid(d, (x,y,z), (x2,y2,z+1))
	cuboid(d, (x,y,z), (x2,y+1,z2))
	cuboid(d, (x,y,z), (x+1,y2,z2))

	cuboid(d, (x2,y2,z2), (x,y,z2-1))
	cuboid(d, (x2,y2,z2), (x,y2-1,z))
	cuboid(d, (x2,y2,z2), (x2-1,y,z))

cube_faces(d, (0,0,0), cube_size)

d.saveas('hello_world.dxf')
