#!BPY

"""
Name: 'Cube import'
Blender: 249
Group: 'Import'
Tooltip: 'Import for cube data.'
"""
import Blender
import sys
sys.path.append("/usr/share/blender/scripts/blender/")

import import_dxf

from Blender import Draw

EVENT_IMPORT = 1 

def draw_UI():
	Draw.BeginAlign()
	Draw.PushButton('Import', EVENT_IMPORT, 30, 0, 100, 20, 'import')
	Draw.EndAlign()

def bevent(evt):
	if evt==EVENT_IMPORT:
		SCENE = Blender.Scene.New("hello world")
		SCENE.makeCurrent()
		import_dxf.SCENE = SCENE
		import_dxf.main("hello_world.dxf")

def event(evt, val):
	if evt in (Draw.QKEY, Draw.ESCKEY) and not val:
		Draw.Exit()

Draw.Register(draw_UI, event, bevent)

