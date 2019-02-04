# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import matplotlib
# import matplotlib.pyplot as plt

# Other Imports
import sys
import inspect
import pprint
import numpy

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Routing Distance Metric
# ------------------------------------------------------------------
# Calculate center of placement site in manufacturing units
def calculate_placement_site_center(layout, placement_site):
	placement_site_name = layout.def_info.placement_rows[placement_site.y].site_name
	x_trigger_psite     = layout.def_info.placement_rows[placement_site.y].origin.x + (layout.lef.placement_sites[placement_site_name].dimension.x * placement_site.x)
	y_trigger_psite     = layout.def_info.placement_rows[placement_site.y].origin.y
	x_trigger_psite    += (layout.lef.placement_sites[placement_site_name].dimension.x / 2)
	y_trigger_psite    += (layout.lef.placement_sites[placement_site_name].dimension.y / 2)
	
	if x_trigger_psite.is_integer() and y_trigger_psite.is_integer():
		return Point(int(x_trigger_psite), int(y_trigger_psite))
	else:
		print "UNSUPPORTED %s: placement site center is not located on manufacturing grid." % (inspect.stack()[0][3])
		sys.exit(3)

def trim_min_spacing(wire_line, min_spacing):
	if wire_line.is_horizontal():
		wire_line.get_west_endpoint().x += (min_spacing - 1)
		wire_line.get_east_endpoint().x -= (min_spacing - 1)
	elif wire_line.is_vertical():
		wire_line.get_south_endpoint().y += (min_spacing - 1)
		wire_line.get_north_endpoint().y -= (min_spacing - 1)
	else:
		print "UNSUPPORTED %s: wire segment direction." % (inspect.stack()[0][3])
		sys.exit(3)

	return wire_line

def color_ns_bitmap_parallel_window(ns_bitmap, ns_line_anchor_pt, windows, min_spacing):
	for window in windows:
		# 1. Get window center line
		window_line = window.get_window_center_line_segment()

		# 2. Trim window center line spacing
		window_line = trim_min_spacing(window_line, min_spacing)

		if window_line.is_horizontal():
			# 3a. Offset window center line endpoints
			window_line.p1.x -= ns_line_anchor_pt.x
			window_line.p2.x -= ns_line_anchor_pt.x

			# 4a. Color Bitmap
			ns_bitmap[0, window_line.get_west_endpoint().x : window_line.get_east_endpoint().x] = 1
		elif window_line.is_vertical():
			# 3b. Offset window center line endpoints
			window_line.p1.y -= ns_line_anchor_pt.y
			window_line.p2.y -= ns_line_anchor_pt.y
		
			# 4b. Color Bitmap
			ns_bitmap[window_line.get_south_endpoint().y : window_line.get_north_endpoint().y, 0] = 1
		else:
			print "UNSUPPORTED %s: window line orientation." % (inspect.stack()[0][3])
			sys.exit(3)

	return ns_bitmap

def color_ns_bitmap_perpendicular_window(ns_bitmap, net_segment, side):
	# Check if any unblocked windows
	if net_segment.unblocked_windows[side]:
		if   side == 'N':
			ns_bitmap[-1, 0] = 1 # Wire is Vertical
		elif side == 'E':
			ns_bitmap[0, -1] = 1 # Wire is Horizontal
		elif side == 'S' or side == 'W':
			ns_bitmap[0, 0]  = 1 # Wire is Vertical

	return ns_bitmap

def create_ns_bitmap(layout, net_segment):
	# Get net segment center line
	ns_line = net_segment.get_center_line()

	# Create bitmap of net segment center line
	if   ns_line.is_horizontal():
		ns_line_anchor_pt = ns_line.get_west_endpoint() 
		ns_bitmap         = numpy.zeros(shape=(1, ns_line.get_length()), dtype=bool)	
	elif ns_line.is_vertical():
		ns_line_anchor_pt = ns_line.get_south_endpoint()
		ns_bitmap         = numpy.zeros(shape=(ns_line.get_length(), 1), dtype=bool)
	else:
		print "UNSUPPORTED %s: wire segment direction." % (inspect.stack()[0][3])
		sys.exit(3)

	# Color Bitmap
	for side in net_segment.unblocked_windows.keys():
		if   side == 'N' or side == 'S':
			if ns_bitmap.shape[0] == 1:
				# Bitmap is Horizontal --> Parallel Side
				min_spacing = layout.lef.layers[net_segment.layer_num].min_spacing_db
				ns_bitmap   = color_ns_bitmap_parallel_window(\
								ns_bitmap, \
								ns_line_anchor_pt, \
								net_segment.unblocked_windows[side], \
								min_spacing)

			elif ns_bitmap.shape[1] == 1:
				# Bitmap is Vertical --> Perpendicular Side
				ns_bitmap = color_ns_bitmap_perpendicular_window(\
								ns_bitmap, \
								net_segment, \
								side)

			else: 
				print "UNSUPPORTED %s: wire segment bitmap size (N/S side)." % (inspect.stack()[0][3])
				sys.exit(3)
		elif side == 'W' or side == 'E':
			if ns_bitmap.shape[1] == 1:
				# Bitmap is Vertical --> Parallel Side
				min_spacing = layout.lef.layers[net_segment.layer_num].min_spacing_db
				ns_bitmap   = color_ns_bitmap_parallel_window(\
								ns_bitmap, \
								ns_line_anchor_pt, \
								net_segment.unblocked_windows[side], \
								min_spacing)

			elif ns_bitmap.shape[0] == 1:
				# Bitmap is Horizontal --> Perpendicular Side
				ns_bitmap = color_ns_bitmap_perpendicular_window(\
								ns_bitmap, \
								net_segment, \
								side)
			else:
				print "UNSUPPORTED %s: wire segment bitmap size (W/E side)." % (inspect.stack()[0][3])
				sys.exit(3)
		elif side == 'T':
			# Check if valid routing layer
			if net_segment.layer_num < layout.lef.top_routing_layer_num:
				# Parallel Side
				min_spacing = layout.lef.layers[net_segment.layer_num + 1].min_spacing_db
				ns_bitmap   = color_ns_bitmap_parallel_window(\
								ns_bitmap, \
								ns_line_anchor_pt, \
								net_segment.unblocked_windows[side], \
								min_spacing)
		elif side == 'B':
			# Check if valid routing layer
			if net_segment.layer_num > layout.lef.bottom_routing_layer_num:
				# Parallel Side
				min_spacing = layout.lef.layers[net_segment.layer_num - 1].min_spacing_db
				ns_bitmap   = color_ns_bitmap_parallel_window(\
								ns_bitmap, \
								ns_line_anchor_pt, \
								net_segment.unblocked_windows[side], \
								min_spacing)
		else:
			print "UNSUPPORTED %s: wire segment (%d) unblocked window side (%s)." % (inspect.stack()[0][3], net_segment.num, side)
			sys.exit(3)

	return ns_line, ns_line_anchor_pt, ns_bitmap

def find_closest_open_nsbitmap_pt(ns_bitmap, row, col):
	num_rows = ns_bitmap.shape[0]
	num_cols = ns_bitmap.shape[1]

	# Net Segment is VERTICAL
	if num_cols == 1:
		# Check if row, col is endpoint of bitmap
		if row == 0:
			# print "HERE-1", row, col
			# 1. Closest to SOUTH endpoint
			# Scan rows of bitmap BOTTOM --> UP
			for i in range(row, num_rows):
				if ns_bitmap[i, col]:
					return i, col
		elif row == num_rows:
			# print "HERE-2", row, col
			# 2. Closest to NORTH endpoint
			# Scan rows of bitmap TOP --> DOWN
			for i in range(row - 1, -1, -1):
				if ns_bitmap[i, col]:
					return i, col
		else:
			# 3. Closest to MIDDLE point
			# print "HERE-3", row, col
			i = 0
			while i <= max((num_rows - row - 1), row):
				if (row + i) < num_rows:
					if ns_bitmap[row + i, col]:
						return (row + i), col
				if (row - i) >= 0:
					if ns_bitmap[row - i, col]:
						return (row - i), col
				i += 1

	# Net Segment is HORIZONTAL
	elif num_rows == 1:
		# Check if row, col is endpoint of bitmap
		if col == 0:
			# print "HERE-4", row, col
			# 1. Closest to WEST endpoint
			# Scan rows of bitmap BOTTOM --> UP
			for i in range(col, num_cols):
				if ns_bitmap[row, i]:
					return row, i
		elif col == num_cols:
			# print "HERE-5", row, col
			# 2. Closest to EAST endpoint
			# Scan rows of bitmap TOP --> DOWN
			for i in range(col - 1, -1, -1):
				if ns_bitmap[row, i]:
					return row, i
		else:
			# print "HERE-6", row, col
			# 3. Closest to MIDDLE point
			i = 0
			while i <= max((num_cols - col - 1), col):
				if (col + i) < num_cols:
					if ns_bitmap[row, col + i]:
						return row, (col + i)
				if (col - i) >= 0:
					if ns_bitmap[row, col - i]:
						return row, (col - i)
				i += 1

	# Invalid bitmap shape
	else:
		print "UNSUPPORTED %s: ns_bitmap is not 1-dimensional (# rows = %d; # cols = %d)." % (inspect.stack()[0][3], num_rows, num_cols)
		sys.exit(3) 

	return -1, -1

def debug_print_closest_attack_pt(layout, net_segment, ns_bitmap, attack_pt, ts_pt):
	print "Net Segment (%s): %d" % (net_segment.net_basename, net_segment.num)
	print "		Klayout Query:       " 
	print "			paths on layer %d/%d of cell %s where" % (net_segment.polygon.gdsii_element.layer, net_segment.polygon.gdsii_element.data_type, layout.top_level_name)
	print "			shape.path.bbox.left==%d &&"  % (net_segment.polygon.bbox.ll.x)
	print "			shape.path.bbox.right==%d &&" % (net_segment.polygon.bbox.ur.x)
	print "			shape.path.bbox.top==%d &&"   % (net_segment.polygon.bbox.ur.y)
	print "			shape.path.bbox.bottom==%d"   % (net_segment.polygon.bbox.ll.y)
	print "Net Segment Center Line:"
	net_segment.get_center_line().print_segment()
	print "Attack Point:"
	attack_pt.print_coords()
	print
	print "Trigger Space Point:"
	ts_pt.print_coords()
	print
	print "Net Segment Bitmap:"
	numpy.set_printoptions(threshold=numpy.nan)
	print numpy.array2string(ns_bitmap.astype(int).flatten())
	print

# Computes the closest point on the net segment
# (that is NOT blocked) to the given point
def compute_closet_pt_on_net_segment(layout, net_segment, point):
	# Create bitmap with open windows
	ns_line, ns_line_anchor_pt, ns_bitmap = create_ns_bitmap(layout, net_segment)	

	# # Find closest open attack point on net segment
	# closest_point    = None
	# closest_distance = 0

	# for row in range(ns_bitmap.shape[0]):
	# 	for col in range(ns_bitmap.shape[1]):

	# 		# Compute locations of unblocked attack points on net segment
	# 		if ns_bitmap[row][col]:
	# 			ns_line_attack_pt = Point.from_point_and_offset(ns_line_anchor_pt, col, row)
	# 			route_distance    = point.distance_from(ns_line_attack_pt)
	# 			if (not closest_point) or (route_distance < closest_distance):
	# 				closest_point    = ns_line_attack_pt
	# 				closest_distance = route_distance

	# return closest_point

	# Net Segment is VERTICAL
	if ns_line.is_vertical():
		# print "ns_line is VERTICAL"
		if point.y >= min(ns_line.p1.y, ns_line.p2.y) and \
		   point.y <= max(ns_line.p1.y, ns_line.p2.y):
			# Point lies within vertical range of line -->
			# point on line that is perpendicular to Point is the closest
			# print "IN BETWEEN"
			row, col = find_closest_open_nsbitmap_pt(ns_bitmap, point.y - ns_line_anchor_pt.y, 0)
		elif point.y < min(ns_line.p1.y, ns_line.p2.y):
			# Point lies south of vertical range of line -->
			# south endpoint of line is the closest
			# print "BELOW"
			row, col =  find_closest_open_nsbitmap_pt(ns_bitmap, 0, 0)
		else:
			# Point lies north of vertical range of line -->
			# north endpoint of line is the closest
			# print "ABOVE"
			row, col = find_closest_open_nsbitmap_pt(ns_bitmap, ns_bitmap.shape[0], 0)

	# Net Segment is HORIZONTAL
	elif ns_line.is_horizontal():
		# print "ns_line is HORIZONTAL"
		if point.x >= min(ns_line.p1.x, ns_line.p2.x) and \
		   point.x <= max(ns_line.p1.x, ns_line.p2.x):
			# Point lies within horizontal range of line -->
			# point on line that is perpendicular to Point is the closest
			# print "IN BETWEEN"
			row, col = find_closest_open_nsbitmap_pt(ns_bitmap, 0, point.x - ns_line_anchor_pt.x)
		elif point.x < min(ns_line.p1.x, ns_line.p2.x):
			# Point lies west of horizontal range of line -->
			# west endpoint of line is the closest
			# print "LEFT"
			row, col = find_closest_open_nsbitmap_pt(ns_bitmap, 0, 0)
		else:
			# Point lies east of horizontal range of line -->
			# east endpoint of line is the closest
			# print "RIGHT"
			row, col = find_closest_open_nsbitmap_pt(ns_bitmap, 0, ns_bitmap.shape[1])
	else:
		print "ERROR %s: not possible to reach here."  % (inspect.stack()[0][3])
		sys.exit(4)

	if row != -1 and col != -1 and ns_bitmap[row][col]:
		return Point.from_point_and_offset(ns_line_anchor_pt, col, row)
	else:
		print "Number of Attack Points: %d" % (numpy.count_nonzero(ns_bitmap))
		debug_print_closest_attack_pt(layout, net_segment, ns_bitmap, Point(col,row), point)
		print "ERROR %s: invalid attack point on net segment (row = %d; col = %d; segment num = %d)."  % (inspect.stack()[0][3], row, col, net_segment.num)
		sys.exit(4)

# Computes a 3D manhattan distance between the closest 
# placement site in the open trigger space and the closest
# attackable point of the net segment (GDSII path/boundary object).
def route_distance(layout, trigger_spaces, net_segment):
	tspaces = []

	# Calculate net segment center
	net_segment_center = net_segment.polygon.bbox.get_center()
	
	# Determine placement site(s) in trigger space(s) of a given size that are closest to the net segment
	ind = 0
	for trigger_space in trigger_spaces.spaces:
		min_manhattan_distance      = 0
		min_placement_sites_centers = []
		placement_site_ind          = 0
		
		for placement_site in trigger_space:
			# Calculate placement site center
			placement_site_center = calculate_placement_site_center(layout, placement_site)

			# Calculate closest point on net segment to placement site center
			net_segment_pt = compute_closet_pt_on_net_segment(layout, net_segment, placement_site_center)

			# Calculate Manhattan Distance
			x_distance = abs(net_segment_pt.x  - placement_site_center.x)
			y_distance = abs(net_segment_pt.y  - placement_site_center.y)
			# z_distance = abs(net_segment.layer_num - 0)
			curr_manhattan_distance = x_distance + y_distance #+ z_distance

			if placement_site_ind == 0:
				min_manhattan_distance = curr_manhattan_distance

			# Update minimum distance
			if curr_manhattan_distance < min_manhattan_distance:
				min_manhattan_distance      = curr_manhattan_distance
				min_placement_sites_centers = [placement_site_center]
			elif curr_manhattan_distance == min_manhattan_distance:
				min_placement_sites_centers.append(placement_site_center)

			placement_site_ind += 1

		ind += 1

		# Pair placement site(s) with trigger spaces
		tspaces.append(TriggerSpace(ind - 1, min_placement_sites_centers, float(min_manhattan_distance) / float(layout.lef.database_units)))

	return tspaces

def analyze_routing_distance(layout, target_trigger_size=4, max_blockage=100.0):
	# Verify net blockage and trigger space metrics have been computed
	if not layout.net_blockage_done or not layout.trigger_space_done:
		print "ERROR %s: net blockage and trigger space metrics not computed." % (inspect.stack()[0][3])
		sys.exit(4)

	# Sort Critical Net Segments
	sorted_net_segments = []
	for net in layout.critical_nets:
		for net_segment in net.segments:
			weighted_blockage = net_segment.get_weighted_blockage_percentage()
			if weighted_blockage < max_blockage:
				sorted_net_segments.append(net_segment)

	# Filter/Map trigger spaces to critical net segments based on size and 3D manhattan distance
	for trigger_size in sorted(layout.trigger_spaces):
		# Filter only trigger spaces that are large enough for the target trigger circuit
		if trigger_size >= target_trigger_size:
			trigger_spaces = layout.trigger_spaces[trigger_size]
			for net_segment in sorted_net_segments:
				# Map possible trigger spaces to net segments
				if net_segment not in trigger_spaces.net_segment_2_sites:
					trigger_spaces.net_segment_2_sites[net_segment] = route_distance(layout, trigger_spaces, net_segment)
				else:
					print "ERROR <analyze_routing_distance>: not possible to reach here."
					sys.exit(3)
				
	# Print Report
	for trigger_size in sorted(layout.trigger_spaces):
		# Filter only trigger spaces that are large enough for the target trigger circuit
		if trigger_size >= target_trigger_size:
			trigger_spaces  = layout.trigger_spaces[trigger_size]
			trigger_counter = 0
			for i in range(len(trigger_spaces.spaces)):
				print "Trigger %d (Size: %d):" % (trigger_counter, trigger_size)
				for net_segment in sorted_net_segments:
					curr_trigger_space_ind = [ ts.spaces_index for ts in trigger_spaces.net_segment_2_sites[net_segment] ].index(i) 
					curr_trigger_space     = trigger_spaces.net_segment_2_sites[net_segment][curr_trigger_space_ind]
					net_std_from_mean      = (float(curr_trigger_space.manhattan_distance) - float(layout.wire_stats.net_mean)) / float(layout.wire_stats.net_sigma)
					conn_std_from_mean     = (float(curr_trigger_space.manhattan_distance) - float(layout.wire_stats.connection_mean)) / float(layout.wire_stats.connection_sigma)
					print "	Net Basename: %s, Segment #: %d, Est. MD: %d (microns), Net Length: %.2f, Conn. Length: %.2f" % (net_segment.net_basename, net_segment.num, curr_trigger_space.manhattan_distance, net_std_from_mean, conn_std_from_mean)
				trigger_counter += 1

	# Set completed flag
	layout.route_distance_done = True
