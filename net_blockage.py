# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Other Imports
import time
import sys
import inspect
import copy
import numpy

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Critical Net Blockage Metric
# ------------------------------------------------------------------
# Bits inside the ploygon is set to 1
def color_bitmap(bitmap, offset, poly):	
	for row in range(bitmap.shape[0]):
		for col in range(bitmap.shape[1]):
			if poly.is_point_inside(Point(col + offset.x + 0.5, row + offset.y + 0.5)):
				bitmap[row, col] = 1

# Calculates number of bits in a bitmap that are 1
def bits_colored(bitmap):
	num_bits_colored = 0
	
	for row in range(bitmap.shape[0]):
		for col in range(bitmap.shape[1]):
			if bitmap[row, col] == 1:
				num_bits_colored += 1

	return num_bits_colored

def check_blockage(net_segment, layout, step_size, check_distance):
	same_layer_units_blocked = 0
	diff_layer_units_blocked = 0

	# Scan all 4 perimeter sides to check for blockages
	for direction in ['N', 'E', 'S', 'W', 'T', 'B']:
		if direction == 'N':
			curr_scan_coord  = net_segment.bbox.ll.x
			end_scan_coord   = net_segment.bbox.ur.x
			curr_fixed_coord = net_segment.bbox.ur.y + check_distance
		elif direction == 'E':
			curr_scan_coord  = net_segment.bbox.ll.y
			end_scan_coord   = net_segment.bbox.ur.y
			curr_fixed_coord = net_segment.bbox.ur.x + check_distance
		elif direction == 'S':
			curr_scan_coord  = net_segment.bbox.ll.x
			end_scan_coord   = net_segment.bbox.ur.x
			curr_fixed_coord = net_segment.bbox.ll.y - check_distance
		elif direction == 'W':
			curr_scan_coord  = net_segment.bbox.ll.y
			end_scan_coord   = net_segment.bbox.ur.y
			curr_fixed_coord = net_segment.bbox.ll.x - check_distance
		elif direction != 'T' and direction != 'B':
			print "ERROR %s: unknown scan direction (%s)." % (inspect.stack()[0][3], direction)
			sys.exit(4)
		
		# Analyze blockage along the perimeter of on the same layer
		if direction != 'T' and direction != 'B':
			num_points_to_scan = ((end_scan_coord - curr_scan_coord) / step_size) + 1
			print "		Checking %d units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, check_distance / layout.lef.database_units)
			
			while curr_scan_coord < end_scan_coord:
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord)):
							same_layer_units_blocked += 1
					else:
						if poly.is_point_inside(Point(curr_fixed_coord, curr_scan_coord)):
							same_layer_units_blocked += 1
				curr_scan_coord += step_size
		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			print "		Checking (%d) nearby polygons along %s side (GDSII Layer:) ..." % (len(net_segment.nearby_al_polygons), direction)
			# Create bitmap of net segment
			net_segment_bitmap = numpy.zeros(shape=(net_segment.bbox.get_height(), net_segment.bbox.get_width()))
			
			# Choose nearby polygons to analyze
			if direction == 'T':
				nearby_polys = net_segment.nearby_al_polygons
			else:
				nearby_polys = net_segment.nearby_bl_polygons

			# Color the bitmap
			for poly in nearby_polys:
				clipped_polys = Polygon.from_polygon_clip(poly, net_segment.polygon)
				for clipped_poly in clipped_polys:
					color_bitmap(net_segment_bitmap, net_segment.bbox.ll, clipped_poly)

			# Calculate colored area
			diff_layer_units_blocked += bits_colored(net_segment_bitmap)

	return same_layer_units_blocked, diff_layer_units_blocked
	
def analyze_critical_net_blockage(layout, verbose):
	total_perimeter_units     = 0
	total_top_bottom_area     = 0
	total_same_layer_blockage = 0 
	total_diff_layer_blockage = 0

	# Extract all GDSII elements near security-critical nets
	layout.extract_nearby_polygons()
	# layout.extract_nearby_polygons_parallel()

	for net in layout.critical_nets:
		print "Analying Net: ", net.fullname
		path_segment_counter = 1
		for net_segment in net.segments:
			total_perimeter_units += net_segment.bbox.get_perimeter()
			total_top_bottom_area += (net_segment.polygon.get_area() * 2)

			# Report Path Segment Condition
			if verbose:
				print "	Analyzing Net Segment", path_segment_counter
				print "		Layer:                ", net_segment.layer_num
				print "		Perimeter:            ", net_segment.bbox.get_perimeter()
				print "		Top and Bottom Area:  ", (net_segment.polygon.get_area() * 2)
				print "		BBox (M-Units):       ", net_segment.bbox.get_bbox_as_list()
				print "		BBox (Microns):       ", net_segment.bbox.get_bbox_as_list_microns(1.0 / layout.lef.database_units)
				print "		Nearby BBox (M-Units):", net_segment.nearby_bbox.get_bbox_as_list()
				print "		Nearby BBox (Microns):", net_segment.nearby_bbox.get_bbox_as_list_microns(1.0 / layout.lef.database_units)
				print "		Nearby Polygons:      ", len(net_segment.nearby_al_polygons) + len(net_segment.nearby_sl_polygons)
				print "		Klayout Query: " 
				print "			paths on layer %d/%d of cell MAL_TOP where" % (net_segment.gdsii_path.layer, net_segment.gdsii_path.data_type)
				print "			shape.path.bbox.left==%d &&"  % (net_segment.bbox.ll.x)
				print "			shape.path.bbox.right==%d &&" % (net_segment.bbox.ur.x)
				print "			shape.path.bbox.top==%d &&"   % (net_segment.bbox.ur.y)
				print "			shape.path.bbox.bottom==%d"   % (net_segment.bbox.ll.y)

			# check_path_blockage() Parameters
			step_size      = 1
			check_distance = layout.lef.layers[net_segment.layer_name].pitch * layout.lef.database_units
			
			# Check N, E, S, W, T, B
			start_time = time.time()
			same_layer_blockage, diff_layer_blockage = check_blockage(net_segment, layout, step_size, check_distance)
			total_same_layer_blockage += same_layer_blockage
			total_diff_layer_blockage += diff_layer_blockage

			print "		Perimeter Units Blocked:  %d / %d" % (same_layer_blockage, net_segment.bbox.get_perimeter())
			print "		Top/Bottom Units Blocked: %d / %d" % (diff_layer_blockage, (net_segment.polygon.get_area() * 2))
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"

			path_segment_counter += 1

	# Calculate raw and weighted blockage percentages.
	# Weighted acounts for area vs. perimeter blockage
	perimeter_blockage_percentage  = (float(total_same_layer_blockage) / float(total_perimeter_units)) * 100.0
	top_bottom_blockage_percentage = (float(total_diff_layer_blockage) / float(total_top_bottom_area)) * 100.0
	raw_blockage_percentage        = (float(total_same_layer_blockage + total_diff_layer_blockage) / float(total_perimeter_units + total_top_bottom_area)) * 100.0
	weighted_blockage_percentage   = (((float(total_same_layer_blockage) / float(total_perimeter_units)) * (float(4.0/6.0)) + (float(total_diff_layer_blockage) / float(total_top_bottom_area)) * float(2.0/6.0))) * 100.0

	# Print calculations
	print "Perimeter Blockage Percentage:  %4.2f%%" % (perimeter_blockage_percentage) 
	print "Top/Bottom Blockage Percentage: %4.2f%%" % (top_bottom_blockage_percentage) 
	print "Raw Blockage Percentage:        %4.2f%%" % (raw_blockage_percentage) 
	print "Weighted Blockage Percentage:   %4.2f%%" % (weighted_blockage_percentage) 
