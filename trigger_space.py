# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import BitArray2D 
# import BitArray2D
# from BitArray2D import godel

# Import matplotlib
import matplotlib.pyplot as plt

# Other Imports
import numpy
import pprint
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
	device_layer_bitmap = numpy.zeros(shape=(layout.def_info.num_placement_rows, layout.def_info.num_placement_cols))

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
	numpy.save("device_layer_bitmap.npy", device_layer_bitmap)

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

# def square_trace_turn_left(current_point, orientation):
# 	if orientation == "N":
# 		current_point.x -= 1
# 		orientation = "W"
# 	elif orientation == "E":
# 		current_point.y += 1
# 		orientation = "N"
# 	elif orientation == "S":
# 		current_point.x += 1
# 		orientation = "E"
# 	elif orientation == "W":
# 		current_point.y -= 1
# 		orientation = "S"
# 	else:
# 		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
# 		sys.exit(1)

# 	return current_point, orientation

# def square_trace_turn_right(current_point, orientation):
# 	if orientation == "N":
# 		current_point.x += 1
# 		orientation = "E"
# 	elif orientation == "E":
# 		current_point.y -= 1
# 		orientation = "S"
# 	elif orientation == "S":
# 		current_point.x -= 1
# 		orientation = "W"
# 	elif orientation == "W":
# 		current_point.y += 1
# 		orientation = "N"
# 	else:
# 		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
# 		sys.exit(1)
		
# 	return current_point, orientation

# # Square Tracing Algorithm
# # This algorithm identifies regions of a bitmap
# # that are 4-connected. I.e. places where trigger
# # circuits could be potentially connected.
# def square_trace(device_layer_bitmap):
# 	connected_points = set()
# 	num_rows         = device_layer_bitmap.shape[0]
# 	num_cols         = device_layer_bitmap.shape[1]
# 	bitmap_bbox      = BBox(Point(0,0), Point(num_rows - 1, num_cols - 1))
# 	start_point      = get_contour_trace_start_point(device_layer_bitmap)
# 	orientation      = "N"

# 	print "Num Rows:", num_rows
# 	print "Num Cols:", num_cols
# 	print
# 	print "Start Point = (R, C)", start_point.y, start_point.x
# 	print
# 	numpy.set_printoptions(threshold=numpy.inf)
# 	print device_layer_bitmap
# 	print
# 	print bitmap_bbox.get_bbox_as_list()
# 	print

# 	# Insert the start point in connected_points list and turn left
# 	current_point = copy.deepcopy(start_point)
# 	connected_points.add(copy.deepcopy(current_point))
# 	current_point, orientation = square_trace_turn_left(current_point, orientation)
# 	dbg.debug_print_square_trace_step(device_layer_bitmap, current_point, orientation, connected_points)

# 	while not (current_point == start_point and orientation == "N"):
# 		# If current point is colored, add to list and turn left
# 		print bitmap_bbox.is_point_inside_bbox(current_point), (device_layer_bitmap[current_point.y, current_point.x] == 1), device_layer_bitmap[current_point.y, current_point.x]
# 		if bitmap_bbox.is_point_inside_bbox(current_point) and device_layer_bitmap[current_point.y, current_point.x] == 1:
# 			print "adding current point"
# 			connected_points.add(copy.deepcopy(current_point))
# 			current_point, orientation = square_trace_turn_left(current_point, orientation)
# 		# Otherwise, turn right
# 		else:
# 			current_point, orientation = square_trace_turn_right(current_point, orientation)
# 		dbg.debug_print_square_trace_step(device_layer_bitmap, current_point, orientation, connected_points)

# 	# Print connected points
# 	print "Num Connected Points:", len(connected_points)
# 	print "Connected Points:"
# 	for point in list(connected_points):
# 		point.print_coords()
# 		print

# 	return connected_points

def get_contour_trace_start_point(device_layer_bitmap):
	num_rows = device_layer_bitmap.shape[0]
	num_cols = device_layer_bitmap.shape[1]

	for col in range(num_cols):
		for row in range(num_rows):
			if device_layer_bitmap[row, col] == 0:
				return Point(col, row)
	return None

def find_4_connected_regions(device_layer_bitmap):
	tigger_space_histogram = {}
	num_open_sites         = 0
	num_rows               = device_layer_bitmap.shape[0]
	num_cols               = device_layer_bitmap.shape[1]
	bitmap_bbox            = BBox(Point(0,0), Point(num_cols - 1, num_rows - 1))
	start_point            = get_contour_trace_start_point(device_layer_bitmap)

	while start_point != None:
		connected_points  = set()
		points_to_explore = set()
		
		# Add start point to unexplored set
		points_to_explore.add(copy.copy(start_point))

		while points_to_explore:
			current_point = points_to_explore.pop()
			
			# add point to connected points
			connected_points.add(copy.copy(current_point))
			num_open_sites += 1

			# mark point as colored
			device_layer_bitmap[current_point.y, current_point.x] = 1
			
			# Check North
			if bitmap_bbox.are_coords_inside_bbox(current_point.x, current_point.y + 1) and device_layer_bitmap[current_point.y + 1, current_point.x] == 0:
				new_point = Point(current_point.x, current_point.y + 1)
				if new_point not in connected_points:
					points_to_explore.add(copy.copy(new_point))

			# Check East
			if bitmap_bbox.are_coords_inside_bbox(current_point.x + 1, current_point.y) and device_layer_bitmap[current_point.y, current_point.x + 1] == 0:
				new_point = Point(current_point.x + 1, current_point.y)
				if new_point not in connected_points:
					points_to_explore.add(copy.copy(new_point))

			# Check South
			if bitmap_bbox.are_coords_inside_bbox(current_point.x, current_point.y - 1) and device_layer_bitmap[current_point.y - 1, current_point.x] == 0:
				new_point = Point(current_point.x, current_point.y - 1)
				if new_point not in connected_points:
					points_to_explore.add(copy.copy(new_point))

			# Check West
			if bitmap_bbox.are_coords_inside_bbox(current_point.x - 1, current_point.y) and device_layer_bitmap[current_point.y, current_point.x - 1] == 0:
				new_point = Point(current_point.x - 1, current_point.y)
				if new_point not in connected_points:
					points_to_explore.add(copy.copy(new_point))

		# Update trigger space histogram
		if len(connected_points) not in tigger_space_histogram:
			tigger_space_histogram[len(connected_points)] = 1
		else:
			tigger_space_histogram[len(connected_points)] += 1

		# Update start point
		start_point = get_contour_trace_start_point(device_layer_bitmap)

	return num_open_sites, tigger_space_histogram

def analyze_open_space_for_triggers(layout):
	# device_layer_bitmap = load_device_layer_bitmap(layout)
	device_layer_bitmap = numpy.load("device_layer_bitmap.npy")

	# # Create random bitmap for testing/debugging
	# device_layer_bitmap = dbg.debug_create_bitmap(10, 10)
	# print device_layer_bitmap

	num_open_sites, tigger_space_histogram = find_4_connected_regions(device_layer_bitmap)
	return num_open_sites, tigger_space_histogram

