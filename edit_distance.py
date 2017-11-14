# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Import matplotlib
# import matplotlib.pyplot as plt

# Other Imports
import time
import sys
import os
import inspect

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Routing Edit Distance Metric
# ------------------------------------------------------------------
def perimeter_blockage(net_segment, step_size):
	return ((float(net_segment.same_layer_blockage) / (float(net_segment.bbox.get_perimeter()) / float(step_size))) * 100.0)

def top_bottom_blockage(net_segment):
	return ((float(net_segment.diff_layer_blockage) / float(net_segment.polygon.get_area() * 2)) * 100.0)

def raw_blockage(net_segment):
	return ((float(net_segment.same_layer_blockage + net_segment.diff_layer_blockage) / float((float(net_segment.bbox.get_perimeter()) / float(step_size)) + (net_segment.polygon.get_area() * 2))) * 100.0)

def weighted_blockage(net_segment, ):
	return ((perimeter_blockage(net_segment, step_size) * float(4.0/6.0)) + (top_bottom_blockage(net_segment) * float(2.0/6.0)))

# Calculate center of placement site in manufacturing units
def calculate_placement_site_center(layout, placement_site):
	placement_site_name = layout.placement_rows[placement_site.y].site_name
	x_trigger_psite = layout.def_info.placement_rows[placement_site.y].origin.x + (layout.def_info.placement_rows[placement_site.y].spacing * placement_site.x)
	y_trigger_psite = layout.def_info.placement_rows[placement_site.y].origin.y
	x_trigger_psite += (layout.def_info.placement_rows[placement_site.y].spacing / 2)
	y_trigger_psite += (layout.lef_info.standard_cells[placement_site_name].height / 2)
	
	return Point(x_trigger_psite, y_trigger_psite)

def calculate_edit_distance(start, end):
	return

# Computes a 3D manhattan distance between the closest 
# placement site in the open trigger space and the centroid
# of the net segment (GDSII path object) bounding box.
def route_distance(trigger_spaces, net_segment):
	trigger_space_sites = []

	# Calculate net segment center
	net_segment_center = net_segment.bbox.get_center()
	
	# Determine placement sites in trigger spaces that are closest to the net segment
	for i in range(len(trigger_space.spaces)):
		min_manhattan_distance      = 0
		min_placement_sites_centers = []

		for placement_site in trigger_space.spaces[i]:
			# Calculate placement site center
			placement_site_center = calculate_placement_site_center(layout, placement_site)

			# Calculate Manhattan Distance
			x_distance = abs(net_segment_center.x  - placement_site_center.x)
			y_distance = abs(net_segment_center.y  - placement_site_center.y)
			z_distance = abs(net_segment.layer_num - 0)
			curr_manhattan_distance = x_distance + y_distance + z_distance

			# Update minimum distance
			if curr_manhattan_distance < min_manhattan_distance:
				min_manhattan_distance      = curr_manhattan_distance
				min_placement_sites_centers = [placement_site_center]
			elif curr_manhattan_distance == min_manhattan_distance:
				min_placement_sites_centers.append(placement_site_center)

		# Pair placement site(s) with trigger spaces
		trigger_space_sites.append(TriggerSite(i, min_placement_sites_centers, min_manhattan_distance))

	return trigger_space_sites

# class TriggerSpace():
# 	def __init__(self, size):
# 		self.size    = size # Number of 4-connected placement sites
# 		self.freq    = 0    # Frequency of same size trigger spaces
# 		self.spaces  = []   # List of sets of Point objects comprising a single trigger space
# 		self.net_segment_2_sites = {} # maps net segments to closest trigger space sites

# class TriggerSite():
# 	def __init__(self, i, coords, md):
# 		self.sites_index        = i      # Index into parent object TriggerSpace.sites list 
# 		self.centers            = coords # Coords of center of placement site (manufacturing units)
#		self.edit_distances     = 0
# 		self.manhattan_distance = md

def analyze_routing_edit_distance(layout, target_trigger_size, max_target_wires):
	# Verify net blockage and trigger space metrics have been computed
	if not layout.net_blockage_done or not layout.trigger_space_done:
		print "ERROR %s: net blockage and trigger space metrics not computed." % (inspect.stack()[0][3])
		sys.exit(4)

	# Sort Critical Net Segments
	sorted_net_segments = []
	for net in layout.critical_nets:
		sorted_net_segments.extend(net.net_segments)
	sorted_net_segments = sorted(sorted_net_segments, key=lambda x:weighted_blockage(x))

	# Adjust max_target_wires
	if max_target_wires > len(sorted_net_segments):
		max_target_wires = len(sorted_net_segments)

	# Filter/Map trigger spaces to critical net segments based on size and 3D manhattan distance
	for trigger_size in layout.trigger_spaces.keys():
		# Filter only trigger spaces that are large enough for the target trigger circuit
		if trigger_size >= target_trigger_size:
			trigger_spaces = layout.trigger_spaces[trigger_size]
			for net_segment in sorted_net_segments[:max_target_wires]:
				# Map possible trigger spaces to net segments
				if net_segment not in trigger_spaces.net_segment_2_sites:
					trigger_spaces.net_segment_2_sites[net_segment] = route_distance(trigger_spaces, net_segment)
				else:
					print "ERROR <analyze_routing_edit_distance>: not possible to reach here."
					sys.exit(3)
				# 
				
	# Print Report
	# for trigger_size in layout.trigger_spaces.keys():
	# 	# Filter only trigger spaces that are large enough for the target trigger circuit
	# 	if trigger_size >= target_trigger_size:


	return

