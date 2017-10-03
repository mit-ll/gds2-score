# Import Custom Modules
import debug_prints as dbg
from polygon import *
from net     import *
from layout  import *

# Other Imports
import time
import sys
import inspect
# import itertools

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# ------------------------------------------------------------------
# Critical Net Blockage Metric
# ------------------------------------------------------------------
def check_blockage(net_segment, layout, step_size, check_distance):
	num_units_blocked = 0

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
		
		if direction != 'T' and direction != 'B':
			num_points_to_scan = ((end_scan_coord - curr_scan_coord) / step_size) + 1
			print "		Checking %d units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, check_distance / layout.lef.database_units)
			
			while curr_scan_coord < end_scan_coord:
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord)):
							num_units_blocked += 1
					else:
						if poly.is_point_inside(Point(curr_fixed_coord, curr_scan_coord)):
							num_units_blocked += 1
				curr_scan_coord += step_size
		else:
			print "		Checking (%d) nearby polygons along %s side ..." % (len(net_segment.nearby_al_polygons), direction)
			# Calculate areas of intersection of nearby polygons
			# Calculate all clipped polygons
			overlapping_polys  = []
			total_overlap_area = 0
			for poly in net_segment.nearby_al_polygons:
				clipped_polys = Polygon.from_polygon_clip(poly, net_segment.polygon)
				if clipped_polys:
					overlapping_polys.extend(clipped_polys)
					for clipped_poly in clipped_polys:
						total_overlap_area += clipped_poly.get_area()
			# Calculate Overlap Area to Subtract Out
			# @TODO
			# a = [1,2,3,4]
			# for i in range(1, len(a) + 1):
			# 	for value in itertools.combinations(a, i):
			# 		print value
				
	return (num_units_blocked + total_overlap_area)
	
def analyze_critical_net_blockage(layout, verbose):
	total_area      = 0
	total_blockage  = 0 

	# Extract all GDSII elements near security-critical nets
	layout.extract_nearby_polygons()
	# layout.extract_nearby_polygons_parallel()

	for net in layout.critical_nets:
		print "Analying Net: ", net.fullname
		path_segment_counter = 1
		for net_segment in net.segments:
			total_area += net_segment.bbox.get_perimeter() + (net_segment.polygon.get_area() * 2)
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
			start_time     = time.time()
			units_blocked  = check_blockage(net_segment, layout, step_size, check_distance)
			total_blockage += units_blocked
			print "		Area Blocked:       ", units_blocked
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"
			path_segment_counter += 1

	return ((float(total_blockage) / float(total_area)) * 100.0)