# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import BitArray2D 
from BitArray2D import *

# Other Imports
import time
import sys
import inspect

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Open Trigger Space Metric
# ------------------------------------------------------------------
def load_device_layer_bitmap(layout):
	# device_layer_bitmap = BitArray2D(rows=layout.bbox.ur.y, columns=layout.bbox.ur.x)
	device_layer_bitmap = BitArray2D(rows=100, columns=100)

	# # Test of BitArray2D Functions
	# device_layer_bitmap = BitArray2D( bitstring = "00000\n00000\n00000\n00000\n00000" )
	# print device_layer_bitmap
	# print
	# ll_x = 0
	# ll_y = 2
	# ur_x = 4
	# ur_y = 4
	# # replacement = ~device_layer_bitmap[godel(ll_y, ll_x) : godel(ur_y, ur_x)]
	# replacement = device_layer_bitmap[godel(ll_y, ll_x) : godel(ur_y, ur_x)]
	# print replacement
	# print
	# print replacement.rows, replacement.columns
	# print device_layer_bitmap[godel(ll_y, ll_x) : godel(ur_y, ur_x)].rows, device_layer_bitmap[godel(ll_y, ll_x) : godel(ur_y, ur_x)].columns 
	# print
	# # device_layer_bitmap[godel(ll_y, ur_y) : godel(ll_x, ur_x)] = replacement
	# for row in range(replacement.rows):
	# 	for col in range(replacement.columns):
	# 		device_layer_bitmap[ll_y + row, ll_x + col] = 1	
	# print device_layer_bitmap

	for element in layout.top_gdsii_structure:
		polys = layout.generate_polys_from_element(element)
		for poly in polys:
			# Polygon coloring algorithm
			color = False
			for row in range(poly.bbox.ll.y, poly.bbox.ur.y):
				for col in range(poly.bbox.ll.x, poly.bbox.ur.x + 1):
					for v_edge in poly.vertical_edges():
						temp_point = Point(col, row + 0.5)
						if v_edge.on_segment(temp_point):
							color = not color
					if color:
						device_layer_bitmap[row, col] = 1
	return device_layer_bitmap

def analyze_open_space_for_triggers(layout, def_fname=None):
	# Calculate total area of layout withouth the DEF file
	# if def_fname == None:
	# 	layout.compute_layout_bbox()
	# else:
	# 	layout.load_bbox(def_fname)

	device_layer_bitmap = load_device_layer_bitmap(layout)

	# print "Check MEM"
	# while True:
	# 	continue

	return