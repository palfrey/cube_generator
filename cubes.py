import sdxf

d=sdxf.Drawing()

d.layers.append(sdxf.Layer(name="textlayer",color=3))

def cuboid(d, topleft, bottomright):
	(x,y,z) = topleft
	(x2,y2,z2) = bottomright
	d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y2,z),(x,y2,z)]))
	d.append(sdxf.Face(points=[(x,y,z),(x,y2,z),(x,y2,z2),(x,y,z2)]))
	d.append(sdxf.Face(points=[(x,y,z),(x2,y,z),(x2,y,z2),(x,y,z2)]))

	d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y,z2),(x2,y,z2)]))
	d.append(sdxf.Face(points=[(x2,y2,z2),(x2,y,z2),(x2,y,z),(x2,y2,z)]))
	d.append(sdxf.Face(points=[(x2,y2,z2),(x,y2,z2),(x,y2,z),(x2,y2,z)]))

cuboid(d, (0,0,0), (1,1,1))

d.saveas('hello_world.dxf')
