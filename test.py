import cubes

space = cubes.Space((8,8,8))
d = None

f = cubes.Face(cubes.Direction.POS_X, 8,8, (0,0,0), space)
f.makeOutline(d, space)

f.grid[0][1] = False
f.makeOutline(d, space)

f.grid[7][1] = False
f.makeOutline(d, space)

f.grid[0][7] = False
f.makeOutline(d, space)

f.grid[1][7] = False
f.makeOutline(d, space)

