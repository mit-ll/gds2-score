# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import BitArray2D 
import BitArray2D
from BitArray2D import godel

# Import matplotlib
import matplotlib.pyplot as plt

# Other Imports
import time
import copy
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
	# device_layer_bitmap = BitArray2D.BitArray2D(rows=40, columns=40)
	device_layer_bitmap = BitArray2D.BitArray2D(rows=layout.def_info.num_placement_rows, columns=layout.def_info.num_placement_cols)

	# # Test of BitArray2D Functions
	# # device_layer_bitmap = BitArray2D( bitstring = "00000\n00000\n00000\n00000\n00000" )
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

	# Loop through the placement sites
	placement_site      = layout.lef.placement_sites[layout.def_info.placement_rows[0].site_name]
	placement_grid_bbox = layout.def_info.placement_grid_bbox

	for device_layer_polys in layout.generate_device_layer_polys():
		# Constrain search region on placement grid
		if device_layer_polys:
			search_region = BBox.from_multiple_polygons(device_layer_polys)
			# print "Search Region: %s" % (search_region.get_bbox_as_list())
			# print "Placement Site Dimensions: X = %d, Y = %d" % (placement_site.dimension.x, placement_site.dimension.y)
			# print "Search Region 1: %s; Placement Grid: %s" % (search_region.get_bbox_as_list(), placement_grid_bbox.get_bbox_as_list())
			if placement_grid_bbox.overlaps_bbox(search_region):
				search_region_ll_x_extended = search_region.ll.x - (search_region.ll.x % placement_site.dimension.x)
				search_region_ll_y_extended = search_region.ll.y - (search_region.ll.y % placement_site.dimension.y)
				search_region_ur_x_extended = search_region.ur.x + (placement_site.dimension.x - (search_region.ur.x % placement_site.dimension.x))
				search_region_ur_y_extended = search_region.ur.y + (placement_site.dimension.y - (search_region.ur.y % placement_site.dimension.y))
				search_region.ll.x = int(((max(placement_grid_bbox.ll.x, search_region_ll_x_extended) - placement_grid_bbox.ll.x) / placement_site.dimension.x) - 1)
				search_region.ll.y = int(((max(placement_grid_bbox.ll.y, search_region_ll_y_extended) - placement_grid_bbox.ll.y) / placement_site.dimension.y) - 1)
				search_region.ur.x = int((min(placement_grid_bbox.ur.x,  search_region_ur_x_extended) - placement_grid_bbox.ll.x) / placement_site.dimension.x)
				search_region.ur.y = int((min(placement_grid_bbox.ur.y,  search_region_ur_y_extended) - placement_grid_bbox.ll.y) / placement_site.dimension.y)
				# print "Search Region 2: %s; Placement Grid: %s" % (search_region.get_bbox_as_list(), placement_grid_bbox.get_bbox_as_list())

				# Set current placement site bbox
				current_site_ll   = Point.from_point_and_offset(layout.def_info.placement_rows[search_region.ll.y].origin, placement_site.dimension.x * search_region.ll.x, 0)
				current_site_ur   = Point.from_point_and_offset(current_site_ll, placement_site.dimension.x, placement_site.dimension.y)
				current_site_bbox = BBox(current_site_ll, current_site_ur)
				for poly in device_layer_polys:
					for row in range(search_region.ll.y, search_region.ur.y):
						for col in range(search_region.ll.x, search_region.ur.x):
							if poly.overlaps_bbox(current_site_bbox):
								device_layer_bitmap[row, col] = 1
							current_site_bbox.ll.x += placement_site.dimension.x
							current_site_bbox.ur.x += placement_site.dimension.x
						# Update Current Site BBox
						current_site_bbox.ll.y += placement_site.dimension.y
						current_site_bbox.ur.y += placement_site.dimension.y
	device_layer_bitmap.write_bit_array_to_char_file("device_layer_bitmap.txt")

	# for element in layout.top_gdsii_structure:
	# 	# @TODO: Ignore fill cells
	# 	polys = layout.generate_polys_from_element(element)
	# 	for poly in polys:
	# 		# Polygon coloring algorithm
	# 		color = False
	# 		for row in range(poly.bbox.ll.y, poly.bbox.ur.y):
	# 			for col in range(poly.bbox.ll.x, poly.bbox.ur.x + 1):
	# 				for v_edge in poly.vertical_edges():
	# 					temp_point = Point(col, row + 0.5)
	# 					if v_edge.on_segment(temp_point):
	# 						color = not color
	# 				if color:
	# 					device_layer_bitmap[row, col] = 1
	
	return device_layer_bitmap

def square_trace_turn_left(current_point, orientation):
	if orientation == "N":
		current_point.x -= 1
		orientation = "W"
	elif orientation == "E":
		current_point.y += 1
		orientation = "N"
	elif orientation == "S":
		current_point.x += 1
		orientation = "E"
	elif orientation == "W":
		current_point.y -= 1
		orientation = "S"
	else:
		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
		sys.exit(1)

	return current_point, orientation

def square_trace_turn_right(current_point, orientation):
	if orientation == "N":
		current_point.x += 1
		orientation = "E"
	elif orientation == "E":
		current_point.y -= 1
		orientation = "S"
	elif orientation == "S":
		current_point.x -= 1
		orientation = "W"
	elif orientation == "W":
		current_point.y += 1
		orientation = "N"
	else:
		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
		sys.exit(1)
		
	return current_point, orientation

# Square Tracing Algorithm
# This algorithm identifies regions of a bitmap
# that are 4-connected. I.e. places where trigger
# circuits could be potentially connected.
def square_trace(device_layer_bitmap):
	connected_points = []
	current_point    = Point(0, 0)
	orientation      = "N"
	max_x_coord      = device_layer_bitmap.columns - 1
	max_y_coord      = device_layer_bitmap.rows - 1	
	bitmap_bbox      = BBox(Point(0,0), Point(max_x_coord, max_y_coord))

	# Find starting point
	for col in range(device_layer_bitmap.columns):
		for row in range(device_layer_bitmap.rows):
			if device_layer_bitmap[ godel(row, col) ] == 1:
				current_point.x = col
				current_point.y = row
				break

	print "Start Point = ", current_point.x, current_point.y
	print device_layer_bitmap[ ]
	# print device_layer_bitmap[ godel(int(current_point.y), int(current_point.x)) : godel(int(current_point.y + 20), int(current_point.x + 20)) ]
	# # Insert the start point in connected_points list and turn left
	# connected_points.append(copy.deepcopy(current_point))
	# current_point, orientation = square_trace_turn_left(current_point, orientation)
	# while not (current_point == connected_points[0] and orientation == "N"):
	# 	# If current point is colored, add to list and turn left
	# 	if bitmap_bbox.is_point_inside_bbox(current_point) and device_layer_bitmap[ godel(current_point.y, current_point.x) ] == 1:
	# 		connected_points.append(copy.deepcopy(current_point))
	# 		current_point, orientation = square_trace_turn_left(current_point, orientation)
	# 	# Otherwise, turn right
	# 	else:
	# 		current_point, orientation = square_trace_turn_right(current_point, orientation)
	
	# # Print connected points
	# print "Connected Points:"
	# for point in connected_points:
	# 	point.print_coords()
	# 	print

	return connected_points

def analyze_open_space_for_triggers():
	device_layer_bitmap = BitArray2D.BitArray2D( filename = "device_layer_bitmap.txt" )
	device_layer_bitmap.read_bit_array_from_char_file()
	# device_layer_bitmap = load_device_layer_bitmap(layout)
	connected_points    = square_trace(device_layer_bitmap)

	return

