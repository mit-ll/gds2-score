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
	sides_unblocked 			 = []
	min_wire_spacing    = layout.lef.layers[net_segment.layer_name].min_spacing_db - 1
	required_open_width = layout.lef.layers[net_segment.layer_name].rogue_wire_width

	# Scan all 4 perimeter sides to check for blockages
	for direction in ['N', 'E', 'S', 'W', 'T', 'B']:
		if direction == 'N':
			start_scan_coord         = net_segment.polygon.bbox.ll.x - min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.x + min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.y + check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.y + 2
		elif direction == 'E':
			start_scan_coord         = net_segment.polygon.bbox.ll.y - min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.y + min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.x + check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.x + 2
		elif direction == 'S':
			start_scan_coord         = net_segment.polygon.bbox.ll.x - min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.x + min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.y - check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.y - 2
		elif direction == 'W':
			start_scan_coord         = net_segment.polygon.bbox.ll.y - min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.y + min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.x - check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.x - 2
		elif direction != 'T' and direction != 'B':
			print "ERROR %s: unknown scan direction (%s)." % (inspect.stack()[0][3], direction)
			sys.exit(4)
		
		# Analyze blockage along the perimeter on the same layer
		if direction != 'T' and direction != 'B':
			curr_scan_coord = start_scan_coord
			num_points_to_scan = (float(end_scan_coord - curr_scan_coord) / float(layout.net_blockage_step))
			print "		Checking %.2f units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, float(check_distance / layout.lef.database_units))
			# print "		Start Scan Coord = %d; End Scan Coord = %d; Num Points to Scan = %d" % (curr_scan_coord, end_scan_coord, num_points_to_scan)
			
			# Create Sites Blocked Bitmap 
			# colors  = ['g']*(end_scan_coord - start_scan_coord)
			# markers = ['.']*(end_scan_coord - start_scan_coord)
			sites_blocked = numpy.zeros(shape=(1, end_scan_coord - start_scan_coord))
			sites_ind = 0
			while curr_scan_coord < end_scan_coord:
				sl_poly_overlap = False
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_pitch)) or poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_overlap)):
							for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
								sites_blocked[0, i] = 1
								# colors[i]  = 'r'
								# markers[i] = 'x'
							break
					else:
						if poly.is_point_inside(Point(curr_fixed_coord_pitch, curr_scan_coord)) or poly.is_point_inside(Point(curr_fixed_coord_overlap, curr_scan_coord)):
							for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
								sites_blocked[0, i] = 1
								# colors[i]  = 'r'
								# markers[i] = 'x'
							break
				curr_scan_coord += layout.net_blockage_step
				sites_ind       += layout.net_blockage_step
	
			# Apply sliding window of size (2 * min_spacing * min_wire_width) to calculate wire position blockages
			window_start    = start_scan_coord
			window_end      = window_start + required_open_width
			windows_scanned = 0
			windows_blocked = 0

			# # plt.ion()
			# fig = plt.figure(1)
			# ax = fig.add_subplot(111)
			# net_segment_plot = ax.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords())
			# if direction == 'N' or direction == 'S':
			# 	blocked_line  = ax.scatter(range(start_scan_coord, end_scan_coord), [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord)), color=colors)
			# 	scan_line,    = ax.plot([window_start, window_end-1], [curr_fixed_coord_pitch+10]*2, 'k')
			# else:
			# 	blocked_line  = ax.scatter([curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord)), range(start_scan_coord, end_scan_coord), color=colors)
			# 	scan_line,    = ax.plot([curr_fixed_coord_pitch+10]*2, [window_start, window_end-1], 'k')
			# ax.grid()
			# plt.show()

			while window_end <= end_scan_coord:
				# print "Window Start", window_start
				# print "Window End", window_end
				# print "Length of Sites Blocked", len(sites_blocked)
				# print
				# if direction == 'N' or direction == 'S':
				# 	scan_line.set_xdata([window_start, window_end-1])
				# else:
				# 	scan_line.set_ydata([window_start, window_end-1])
				# fig.canvas.draw()
				# raw_input("		Hit any key to continue...")

				for window_curr in range(window_start, window_end):
					if sites_blocked[0, window_curr-start_scan_coord] == 1:
						# Mark wire position as blocked
						same_layer_units_blocked += 1
						windows_blocked += 1
						break

				window_start                 += 1
				window_end                   += 1
				windows_scanned              += 1
				num_same_layer_units_checked += 1

			if windows_blocked < windows_scanned:
				sides_unblocked.append(direction)
			# print "		Windows blocked %d/%d on %s edge" % (windows_blocked, windows_scanned, direction)

			# fig = plt.figure(1)
			# ax = fig.add_subplot(111)
			# for poly in net_segment.nearby_sl_polygons:
			# 	ax.plot(poly.get_x_coords(), poly.get_y_coords(), color='k')
			# net_segment_plot = ax.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords(), color='b', linewidth=3)
			# if direction == 'N' or direction == 'S':
			# 	x = range(start_scan_coord, end_scan_coord)
			# 	y = [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord))
			# else:
			# 	x = [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord))
			# 	y = range(start_scan_coord, end_scan_coord)
			# for xp, yp, c, m in zip(x, y, colors, markers):
			# 	ax.scatter([xp],[yp], color=c, marker=m)
			# ax.grid()
			# plt.show()

		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			# Create bitmap of net segment
			net_segment_bitmap = numpy.zeros(shape=(net_segment.polygon.bbox.get_height(), net_segment.polygon.bbox.get_width()))
			
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
						color_bitmap(net_segment_bitmap, net_segment.polygon.bbox.ll, clipped_poly)
				# plt.grid()
				# plt.show()

			# Calculate colored area
			diff_layer_units_blocked += bits_colored(net_segment_bitmap)

			# Free bitmap memory
			del net_segment_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, sides_unblocked, diff_layer_units_blocked

def check_blockage(net_segment, layout, check_distance):
	num_same_layer_units_checked = 0
	same_layer_units_blocked     = 0
	diff_layer_units_blocked     = 0
	sides_unblocked 			 = []

	# Scan all 4 perimeter sides to check for blockages
	for direction in ['N', 'E', 'S', 'W', 'T', 'B']:
		if direction == 'N':
			curr_scan_coord          = net_segment.polygon.bbox.ll.x
			end_scan_coord           = net_segment.polygon.bbox.ur.x
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.y + 1
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.y + check_distance
		elif direction == 'E':
			curr_scan_coord          = net_segment.polygon.bbox.ll.y
			end_scan_coord           = net_segment.polygon.bbox.ur.y
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.x + 1
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.x + check_distance
		elif direction == 'S':
			curr_scan_coord          = net_segment.polygon.bbox.ll.x
			end_scan_coord           = net_segment.polygon.bbox.ur.x
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.y - 1
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.y - check_distance
		elif direction == 'W':
			curr_scan_coord          = net_segment.polygon.bbox.ll.y
			end_scan_coord           = net_segment.polygon.bbox.ur.y
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.x - 1
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.x - check_distance
		elif direction != 'T' and direction != 'B':
			print "ERROR %s: unknown scan direction (%s)." % (inspect.stack()[0][3], direction)
			sys.exit(4)
		
		# Analyze blockage along the perimeter on the same layer
		if direction != 'T' and direction != 'B':
			num_points_to_scan      = (float(end_scan_coord - curr_scan_coord) / float(layout.net_blockage_step))
			same_side_units_blocked = 0
			print "		Checking %.2f units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, float(check_distance / layout.lef.database_units))
			# print "		Start Scan Coord = %d; End Scan Coord = %d; Num Points to Scan = %d" % (curr_scan_coord, end_scan_coord, num_points_to_scan)
			while curr_scan_coord < end_scan_coord:
				for poly in net_segment.polygon.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_pitch)) or poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_overlap)):
							same_layer_units_blocked += 1
							same_side_units_blocked  += 1
							break
					else:
						if poly.is_point_inside(Point(curr_fixed_coord_pitch, curr_scan_coord)) or poly.is_point_inside(Point(curr_fixed_coord_overlap, curr_scan_coord)):
							same_layer_units_blocked += 1
							same_side_units_blocked  += 1
							break
				num_same_layer_units_checked += 1
				curr_scan_coord              += layout.net_blockage_step
				if same_side_units_blocked < num_points_to_scan:
					sides_unblocked.append(direction)

		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			# Create bitmap of net segment
			net_segment_bitmap = numpy.zeros(shape=(net_segment.polygon.bbox.get_height(), net_segment.polygon.bbox.get_width()))
			
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
						color_bitmap(net_segment_bitmap, net_segment.polygon.bbox.ll, clipped_poly)
				# plt.grid()
				# plt.show()

			# Calculate colored area
			diff_layer_units_blocked += bits_colored(net_segment_bitmap)

			# Free bitmap memory
			del net_segment_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, sides_unblocked, diff_layer_units_blocked
	
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
			# Get GDSII element type
			if isinstance(net_segment.polygon.gdsii_element, Path):
				gdsii_element_type = "Path"
			elif isinstance(net_segment.polygon.gdsii_element, Boundary):
				gdsii_element_type = "Boundary"
			else:
				gdsii_element_type = "Unknown"
			# Report Path Segment Condition
			if verbose:
				print "	Analyzing Net Segment", path_segment_counter
				print "		Layer:                ", net_segment.layer_num
				print "		GDSII Element:        ", gdsii_element_type
				print "		Perimeter:            ", net_segment.polygon.bbox.get_perimeter()
				print "		Step Size:            ", layout.net_blockage_step
				print "		Pitch:                ", layout.lef.layers[net_segment.layer_name].pitch 
				print "		Default Width:        ", layout.lef.layers[net_segment.layer_name].width 
				# print "		Real Width:           ", (float(net_segment.polygon.bbox.get_width()) / float(layout.lef.database_units))
				# print "		Real Height:          ", (float(net_segment.polygon.bbox.get_height()) / float(layout.lef.database_units))
				print "		Top and Bottom Area:  ", (net_segment.polygon.get_area() * 2)
				print "		BBox (M-Units):       ", net_segment.polygon.bbox.get_bbox_as_list()
				print "		BBox (Microns):       ", net_segment.polygon.bbox.get_bbox_as_list_microns(1.0 / layout.lef.database_units)
				print "		Nearby BBox (M-Units):", net_segment.nearby_bbox.get_bbox_as_list()
				print "		Nearby BBox (Microns):", net_segment.nearby_bbox.get_bbox_as_list_microns(1.0 / layout.lef.database_units)
				print "		Nearby Polygons:      ", len(net_segment.nearby_al_polygons) + len(net_segment.nearby_sl_polygons)
				if gdsii_element_type == "Path":
					print "		Klayout Query: " 
					print "			paths on layer %d/%d of cell MAL_TOP where" % (net_segment.polygon.gdsii_element.layer, net_segment.polygon.gdsii_element.data_type)
					print "			shape.path.bbox.left==%d &&"  % (net_segment.polygon.bbox.ll.x)
					print "			shape.path.bbox.right==%d &&" % (net_segment.polygon.bbox.ur.x)
					print "			shape.path.bbox.top==%d &&"   % (net_segment.polygon.bbox.ur.y)
					print "			shape.path.bbox.bottom==%d"   % (net_segment.polygon.bbox.ll.y)
				elif gdsii_element_type == "Boundary":
					print "		Klayout Query: " 
					print "			boxes on layer %d/%d of cell MAL_TOP where" % (net_segment.polygon.gdsii_element.layer, net_segment.polygon.gdsii_element.data_type)
					print "			shape.box.left==%d &&"  % (net_segment.polygon.bbox.ll.x)
					print "			shape.box.right==%d &&" % (net_segment.polygon.bbox.ur.x)
					print "			shape.box.top==%d &&"   % (net_segment.polygon.bbox.ur.y)
					print "			shape.box.bottom==%d"   % (net_segment.polygon.bbox.ll.y)

			# check_path_blockage() Parameters
			check_distance = (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width)) * layout.lef.database_units
			print "		Check Distance (uM):  ", (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width))

			# Check N, E, S, W, T, B
			start_time = time.time()
			if layout.net_blockage_type == 1:
				num_same_layer_units_checked, same_layer_blockage, sides_unblocked, diff_layer_blockage = check_blockage_constrained(net_segment, layout, check_distance)
			else:
				num_same_layer_units_checked, same_layer_blockage, sides_unblocked, diff_layer_blockage = check_blockage(net_segment, layout, check_distance)
			net_segment.same_layer_blockage = same_layer_blockage
			net_segment.diff_layer_blockage = diff_layer_blockage 
			total_same_layer_blockage      += same_layer_blockage
			total_diff_layer_blockage      += diff_layer_blockage
			total_perimeter_units          += num_same_layer_units_checked
			total_top_bottom_area          += (net_segment.polygon.get_area() * 2)

			if sides_unblocked:
				print "		Sides Unblocked:", sides_unblocked
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
	perimeter_blockage_percentage  = (float(total_same_layer_blockage) / float(total_perimeter_units)) * 100.0
	top_bottom_blockage_percentage = (float(total_diff_layer_blockage) / float(total_top_bottom_area)) * 100.0
	raw_blockage_percentage        = (float(total_same_layer_blockage + total_diff_layer_blockage) / float(total_perimeter_units + total_top_bottom_area)) * 100.0
	weighted_blockage_percentage   = (((float(total_same_layer_blockage) / float(total_perimeter_units)) * float(4.0/6.0)) + ((float(total_diff_layer_blockage) / float(total_top_bottom_area)) * float(2.0/6.0))) * 100.0

	# Print calculations
	print "Perimeter Blockage Percentage:  %4.2f%%" % (perimeter_blockage_percentage) 
	print "Top/Bottom Blockage Percentage: %4.2f%%" % (top_bottom_blockage_percentage) 
	print "Raw Blockage Percentage:        %4.2f%%" % (raw_blockage_percentage) 
	print "Weighted Blockage Percentage:   %4.2f%%" % (weighted_blockage_percentage)

	# Set completed flag
	layout.net_blockage_done = True
