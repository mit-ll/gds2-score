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

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Routing Distance Metric
# ------------------------------------------------------------------
# Calculate center of placement site in manufacturing units
def calculate_closest_placement_site_center(layout, placement_site):
	placement_site_name = layout.def_info.placement_rows[placement_site.y].site_name
	x_trigger_psite     = layout.def_info.placement_rows[placement_site.y].origin.x + (layout.lef.placement_sites[placement_site_name].dimension.x * placement_site.x)
	y_trigger_psite     = layout.def_info.placement_rows[placement_site.y].origin.y
	x_trigger_psite    += (layout.lef.placement_sites[placement_site_name].dimension.x / 2)
	y_trigger_psite    += (layout.lef.placement_sites[placement_site_name].dimension.y / 2)
	
	return Point(x_trigger_psite, y_trigger_psite)

# Computes a 3D manhattan distance between the closest 
# placement site in the open trigger space and the centroid
# of the net segment (GDSII path object) bounding box.
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
			placement_site_center = calculate_closest_placement_site_center(layout, placement_site)

			# Calculate Manhattan Distance
			x_distance = abs(net_segment_center.x  - placement_site_center.x)
			y_distance = abs(net_segment_center.y  - placement_site_center.y)
			z_distance = abs(net_segment.layer_num - 0)
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

