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
import gc

# Import matplotlib
# import matplotlib.pyplot as plt

# # Import Memory Leak Tool
# from pympler import muppy, summary

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

def check_blockage_constrained(net_segment, layout, check_distance):
	num_same_layer_units_checked = 0
	same_layer_units_blocked     = 0
	diff_layer_units_blocked     = 0
	sl_temp_units_blocked        = 0
	sl_prev_blocked              = False
	sl_poly_overlap              = False

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
		
		# Analyze blockage along the perimeter on the same layer
		if direction != 'T' and direction != 'B':
			num_points_to_scan = float(end_scan_coord - curr_scan_coord)
			print "		Checking %.2f units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, float(check_distance / layout.lef.database_units))
			# print "		Start Scan Coord = %d; End Scan Coord = %d; Num Points to Scan = %d" % (curr_scan_coord, end_scan_coord, num_points_to_scan)
			while curr_scan_coord < end_scan_coord:
				sl_poly_overlap = False
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord)):
							sl_poly_overlap = True
							break
					else:
						if poly.is_point_inside(Point(curr_fixed_coord, curr_scan_coord)):
							sl_poly_overlap = True
							break
				# Mark start of sub perimeter blockage count			
				if sl_prev_blocked == False and sl_poly_overlap == True:
					sl_prev_blocked = True
					sl_temp_units_blocked += 1
				# Counting sub perimeter blockage
				elif sl_prev_blocked == True and sl_poly_overlap == True:
					sl_temp_units_blocked += 1
				# Mark end of sub perimeter blockage count
				elif sl_prev_blocked == True and sl_poly_overlap == False:
					# Check if num sub units blocked is above threshold
					if sl_temp_units_blocked >= layout.lef.layers[net_segment.layer_name].rogue_wire_width:
						same_layer_units_blocked += sl_temp_units_blocked
					# Reset counter and flag
					sl_temp_units_blocked = 0
					sl_prev_blocked       = False
				num_same_layer_units_checked += 1
				curr_scan_coord              += layout.net_blockage_step
		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			# Create bitmap of net segment
			net_segment_bitmap = numpy.zeros(shape=(net_segment.bbox.get_height(), net_segment.bbox.get_width()))
			
			# Choose nearby polygons to analyze
			if direction == 'T':
				nearby_polys = net_segment.nearby_al_polygons
			else:
				nearby_polys = net_segment.nearby_bl_polygons
			print "		Checking (%d) nearby polygons along %s side (GDSII Layer:) ..." % (len(nearby_polys), direction)

			# Color the bitmap
			for poly in nearby_polys:
				clipped_polys = Polygon.from_polygon_clip(poly, net_segment.polygon)
				# plt.figure(1)
				# plt.plot(poly.get_x_coords(), poly.get_y_coords())
				# plt.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords())
				for clipped_poly in clipped_polys:
					# plt.plot(clipped_poly.get_x_coords(), clipped_poly.get_y_coords())
					if clipped_poly.get_area() > 0:
						color_bitmap(net_segment_bitmap, net_segment.bbox.ll, clipped_poly)
				# plt.grid()
				# plt.show()

			# Calculate colored area
			diff_layer_units_blocked += bits_colored(net_segment_bitmap)

			# Free bitmap memory
			del net_segment_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, diff_layer_units_blocked


def check_blockage(net_segment, layout, check_distance):
	num_same_layer_units_checked = 0
	same_layer_units_blocked     = 0
	diff_layer_units_blocked     = 0

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
		
		# Analyze blockage along the perimeter on the same layer
		if direction != 'T' and direction != 'B':
			num_points_to_scan = (float(end_scan_coord - curr_scan_coord) / float(layout.net_blockage_step))
			print "		Checking %.2f units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, float(check_distance / layout.lef.database_units))
			# print "		Start Scan Coord = %d; End Scan Coord = %d; Num Points to Scan = %d" % (curr_scan_coord, end_scan_coord, num_points_to_scan)
			while curr_scan_coord < end_scan_coord:
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord)):
							same_layer_units_blocked += 1
							break
					else:
						if poly.is_point_inside(Point(curr_fixed_coord, curr_scan_coord)):
							same_layer_units_blocked += 1
							break
				num_same_layer_units_checked += 1
				curr_scan_coord              += layout.net_blockage_step
		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			# Create bitmap of net segment
			net_segment_bitmap = numpy.zeros(shape=(net_segment.bbox.get_height(), net_segment.bbox.get_width()))
			
			# Choose nearby polygons to analyze
			if direction == 'T':
				nearby_polys = net_segment.nearby_al_polygons
			else:
				nearby_polys = net_segment.nearby_bl_polygons
			print "		Checking (%d) nearby polygons along %s side (GDSII Layer:) ..." % (len(nearby_polys), direction)

			# Color the bitmap
			for poly in nearby_polys:
				clipped_polys = Polygon.from_polygon_clip(poly, net_segment.polygon)
				# plt.figure(1)
				# plt.plot(poly.get_x_coords(), poly.get_y_coords())
				# plt.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords())
				for clipped_poly in clipped_polys:
					# plt.plot(clipped_poly.get_x_coords(), clipped_poly.get_y_coords())
					if clipped_poly.get_area() > 0:
						color_bitmap(net_segment_bitmap, net_segment.bbox.ll, clipped_poly)
				# plt.grid()
				# plt.show()

			# Calculate colored area
			diff_layer_units_blocked += bits_colored(net_segment_bitmap)

			# Free bitmap memory
			del net_segment_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, diff_layer_units_blocked
	
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
				print "		Step Size:            ", layout.net_blockage_step
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
			check_distance = layout.lef.layers[net_segment.layer_name].pitch * layout.lef.database_units
			
			# Check N, E, S, W, T, B
			start_time = time.time()
			if layout.net_blockage_type == 1:
				num_same_layer_units_checked, same_layer_blockage, diff_layer_blockage = check_blockage_constrained(net_segment, layout, check_distance)
			else:
				num_same_layer_units_checked, same_layer_blockage, diff_layer_blockage = check_blockage(net_segment, layout, check_distance)
			net_segment.same_layer_blockage = same_layer_blockage
			net_segment.diff_layer_blockage = diff_layer_blockage 
			total_same_layer_blockage      += same_layer_blockage
			total_diff_layer_blockage      += diff_layer_blockage

			print "		Perimeter Units Blocked:  %d / %d" % (same_layer_blockage, float(num_same_layer_units_checked))
			print "		Top/Bottom Units Blocked: %d / %d" % (diff_layer_blockage, (net_segment.polygon.get_area() * 2))
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"

			path_segment_counter += 1

		# gc.collect()

		# # Print memory usage summary
		# summary.print_(summary.summarize(muppy.get_objects()))
		# raw_input("Press key to continue...")

	# Calculate raw and weighted blockage percentages.
	# Weighted acounts for area vs. perimeter blockage
	# print "Total Same Layer Blockage:", total_same_layer_blockage
	# print "Total Perimeter Units    :", total_perimeter_units
	# print "Total Diff Layer Blockage:", total_diff_layer_blockage
	# print "Total Top/Bottom Area    :", total_top_bottom_area
	perimeter_blockage_percentage  = (float(total_same_layer_blockage) / (float(total_perimeter_units) / float(layout.net_blockage_step))) * 100.0
	top_bottom_blockage_percentage = (float(total_diff_layer_blockage) / float(total_top_bottom_area)) * 100.0
	raw_blockage_percentage        = (float(total_same_layer_blockage + total_diff_layer_blockage) / float((float(total_perimeter_units) / float(layout.net_blockage_step)) + total_top_bottom_area)) * 100.0
	weighted_blockage_percentage   = (((float(total_same_layer_blockage) / (float(total_perimeter_units) / float(layout.net_blockage_step))) * (float(4.0/6.0)) + (float(total_diff_layer_blockage) / float(total_top_bottom_area)) * float(2.0/6.0))) * 100.0

	# Print calculations
	print "Perimeter Blockage Percentage:  %4.2f%%" % (perimeter_blockage_percentage) 
	print "Top/Bottom Blockage Percentage: %4.2f%%" % (top_bottom_blockage_percentage) 
	print "Raw Blockage Percentage:        %4.2f%%" % (raw_blockage_percentage) 
	print "Weighted Blockage Percentage:   %4.2f%%" % (weighted_blockage_percentage)

	# Set completed flag
	layout.net_blockage_done = True
