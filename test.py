import cubes
import sdxf

space = cubes.Space((8,8,8))
d = sdxf.Drawing()

f = cubes.Face(cubes.Direction.POS_X, 8,8, (0,0,0), space)
f.makeOutline(d, (0,0))

blender = sdxf.Drawing()
space.fixCubes()
space.generateCubes(blender)
blender.saveas("hello_world.dxf")

f.grid[0][1] = False
f.makeOutline(d, (8,0))

f.grid[7][1] = False
f.makeOutline(d, (16,0))

f.grid[0][7] = False
f.makeOutline(d, (24,0))

f.grid[1][7] = False
f.makeOutline(d, (32,0))

d.saveas('test.dxf')

