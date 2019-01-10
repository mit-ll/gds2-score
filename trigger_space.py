# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import matplotlib
# import matplotlib.pyplot as plt

# Other Imports
import numpy
import pprint
import time
import copy
import sys
import os
import inspect

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Open Trigger Space Metric
# ------------------------------------------------------------------
def find_empty_placement_site(device_layer_bitmap):
	num_rows = device_layer_bitmap.shape[0]
	num_cols = device_layer_bitmap.shape[1]

	for col in range(num_cols):
		for row in range(num_rows):
			if device_layer_bitmap[row, col] == 0:
				return Point(col, row)
	return None

# Takes 2D numpy array bitmap that represents the placement grid
# on a circuit layout and determines which cells are open.
def find_4_connected_regions(device_layer_bitmap):
	trigger_spaces = {}
	num_open_sites = 0
	num_rows       = device_layer_bitmap.shape[0]
	num_cols       = device_layer_bitmap.shape[1]
	bitmap_bbox    = BBox(Point(0,0), Point(num_cols - 1, num_rows - 1))
	start_point    = find_empty_placement_site(device_layer_bitmap)

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
		if len(connected_points) not in trigger_spaces:
			trigger_spaces[len(connected_points)] = TriggerSpaces(len(connected_points))
			trigger_spaces[len(connected_points)].spaces.append(connected_points)
			trigger_spaces[len(connected_points)].freq += 1
		else:
			trigger_spaces[len(connected_points)].spaces.append(connected_points)
			trigger_spaces[len(connected_points)].freq += 1

		# Update start point
		start_point = find_empty_placement_site(device_layer_bitmap)

	return num_open_sites, trigger_spaces

def analyze_open_space_for_triggers(layout, print_to_stdio=False, print_histogram=False):
	# Find open placement sites in the placement grid
	num_open_sites, trigger_spaces = find_4_connected_regions(copy.deepcopy(layout.def_info.placement_grid))

	# Get width of terminal for printing of the histogram
	if print_to_stdio:
		terminal_rows, terminal_columns = map(int, os.popen('stty size', 'r').read().split())
	else:
		terminal_columns = 80

	# Print calculations
	print "Open/Total Placement Sites: %d / %d" % (num_open_sites, (layout.def_info.num_placement_rows * layout.def_info.num_placement_cols))
	print "Total Trigger Spaces:       %d" % (sum(ts.freq for ts in trigger_spaces.values()))
	print "Summary of Adjacent Placement Sites:"
	print "size  : freq"
	for space_size in sorted(trigger_spaces):
		# Create histogram bar from ASCII characters
		if print_histogram:
			if trigger_spaces[space_size].freq > (terminal_columns - 16):
				histogram_bar = ((unichr(0x2588) * (terminal_columns - 16)) + '*').encode('utf-8')
			else:
				histogram_bar = (unichr(0x2588) * trigger_spaces[space_size].freq).encode('utf-8')

		# Print histogram row
		if print_histogram:
			print "%6d:%5d |%s" % (space_size, trigger_spaces[space_size].freq, histogram_bar)
		else:
			print "%6d:%5d" % (space_size, trigger_spaces[space_size].freq)
	print "----------------------------------------------"

	# Set completed flag and save histogram
	layout.trigger_spaces     = trigger_spaces
	layout.trigger_space_done = True 
