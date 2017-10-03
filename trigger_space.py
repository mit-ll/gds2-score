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
	device_layer_bitmap = BitArray2D(rows=50, columns=50)

	# device_layer_bitmap = BitArray2D( bitstring = "10101\n11001\n10011\n01011" )
	# print device_layer_bitmap
	# print
	# replacement = ~device_layer_bitmap[godel(0,2) : godel(3,5)]
	# print replacement
	# print
	# print replacement.rows, replacement.columns
	# print
	# # device_layer_bitmap[godel(0, 3) : godel(2, 5)] = BitArray2D( bitstring = "111\n111\n111" )
	# device_layer_bitmap[godel(0, 3) : godel(2, 5)] = replacement
	# print
	# print device_layer_bitmap

	for element in layout.top_gdsii_structure:
		polys = layout.generate_polys_from_element(element)
		for poly in polys:
			# Check if polygon is rectangular
			if poly.num_coords == 5:
				fill_ba = ~device_layer_bitmap[godel(poly.bbox.ll.y, poly.bbox.ll.x) : godel(poly.bbox.ur.y, poly.bbox.ur.x)]
				device_layer_bitmap[ godel(poly.bbox.ll.y, poly.bbox.ur.y) : godel(poly.bbox.ll.x, poly.bbox.ur.x) ] = fill_ba

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