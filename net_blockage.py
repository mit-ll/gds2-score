# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

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

# Import matplotlib
# import matplotlib.pyplot as plt

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

def bits_colored(bitmap):
	return numpy.count_nonzero(bitmap)

def compute_al_windows_blocked(bitmap, net_segment, al_min_wire_width, al_min_wire_spacing, al_required_open_width):
	windows_scanned = 0
	windows_blocked = 0
	num_rows = bitmap.shape[0]
	num_cols = bitmap.shape[1]

	if net_segment.polygon.bbox.get_width() > net_segment.polygon.bbox.get_height():
		# Horizontal Path or Boundary
		if net_segment.polygon.bbox.get_width() > al_min_wire_width:
			# Wide enough for 1 width of AL wire
			window_width  = al_required_open_width
			window_height = num_rows
			patch_wire_direction = 'H'
		else:
			print "UNSUPPORTED %s: constrained HORIZONTAL adjacent layer net blockage." % (inspect.stack()[0][3], token)
			sys.exit(3)
	elif net_segment.polygon.bbox.get_width() < net_segment.polygon.bbox.get_height():
		# Vertical Path or Boundary
		if net_segment.polygon.bbox.get_height() > al_min_wire_width:
			window_width  = num_cols
			window_height = al_required_open_width
			patch_wire_direction = 'V'
		else:
			print "UNSUPPORTED %s: constrained VERTICAL adjacent layer net blockage." % (inspect.stack()[0][3], token)
			sys.exit(3)
	else:
		print "UNSUPPORTED %s: SQUARE adjacent layer polygon." % (inspect.stack()[0][3], token)
		sys.exit(3)

	# Set window Y dimensions
	window_start_y = 0
	window_end_y   = window_start_y + window_height
	
	# # Keep track of patching points
	# prev_window_blocked = True
	# start_patch_pt      = None
	# patch_points        = []

	# Scan windows
	while window_end_y <= num_rows:
		# Set window X dimensions
		window_start_x = 0
		window_end_x   = window_start_x + window_width
		while window_end_x <= num_cols:
			if bitmap[window_start_y:window_end_y, window_start_x:window_end_x].any():
				windows_blocked += 1
				prev_window_blocked = True

			# 	if start_patch_pt:
			# 		if patch_wire_direction == 'H':
			# 			end_patch_pt = Point(window_end_x - al_min_wire_spacing - 1, net_segment.polygon.bbox.get_height() / 2)
			# 		elif patch_wire_direction == 'V':
			# 			end_patch_pt = Point(net_segment.polygon.bbox.get_height() / 2, window_end_y - al_min_wire_spacing - 1)
			# 		else:
			# 			print "UNSUPPORTED %s: wire patching direction." % (inspect.stack()[0][3], token)
			# 			sys.exit(3)
			# 		patch_points.append((start_patch_pt, end_patch_pt))
			# 		start_patch_pt = None
			# 		end_patch_pt   = None

			# elif prev_window_blocked:
			# 	prev_window_blocked = False
			# 	if patch_wire_direction == 'H':
			# 		start_patch_pt = Point(window_start_x + al_min_wire_spacing + 1, net_segment.polygon.bbox.get_height() / 2)
			# 	elif patch_wire_direction == 'V':
			# 		start_patch_pt = Point(net_segment.polygon.bbox.get_height() / 2, window_start_y + al_min_wire_spacing + 1)
			# 	else:
			# 		print "UNSUPPORTED %s: wire patching direction." % (inspect.stack()[0][3], token)
			# 		sys.exit(3)

			windows_scanned += 1
			window_start_x  += 1
			window_end_x    += 1
		window_start_y += 1
		window_end_y   += 1

	# if not prev_window_blocked and start_patch_pt:
	# 	if patch_wire_direction == 'H':
	# 		end_patch_pt = Point(window_end_x - al_min_wire_spacing - 1, net_segment.polygon.bbox.get_height() / 2)
	# 	elif patch_wire_direction == 'V':
	# 		end_patch_pt = Point(net_segment.polygon.bbox.get_height() / 2, window_end_y - al_min_wire_spacing - 1)
	# 	else:
	# 		print "UNSUPPORTED %s: wire patching direction." % (inspect.stack()[0][3], token)
	# 		sys.exit(3)
	# 	patch_points.append((start_patch_pt, end_patch_pt))

	# print "Patch Points:", patch_points

	# print "			Windows Blocked: %d / %d" % (windows_blocked, windows_scanned)
	return windows_scanned, windows_blocked

def check_blockage_constrained(net_segment, layout):
	num_same_layer_units_checked = 0
	same_layer_units_blocked     = 0
	num_diff_layer_units_checked = 0
	diff_layer_units_blocked     = 0
	sides_unblocked 			 = []
	sl_min_wire_spacing          = layout.lef.layers[net_segment.layer_name].min_spacing_db - 1
	sl_required_open_width       = layout.lef.layers[net_segment.layer_name].rogue_wire_width
	check_distance               = (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width)) * layout.lef.database_units
	print "		Check Distance (uM):", (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width))

	# Scan all 4 perimeter sides to check for blockages
	for direction in ['N', 'E', 'S', 'W', 'T', 'B']:
		if direction == 'N':
			start_scan_coord         = net_segment.polygon.bbox.ll.x - sl_min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.x + sl_min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.y + check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.y + 2
		elif direction == 'E':
			start_scan_coord         = net_segment.polygon.bbox.ll.y - sl_min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.y + sl_min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.x + check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.x + 2
		elif direction == 'S':
			start_scan_coord         = net_segment.polygon.bbox.ll.x - sl_min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.x + sl_min_wire_spacing
			curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.y - check_distance
			curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.y - 2
		elif direction == 'W':
			start_scan_coord         = net_segment.polygon.bbox.ll.y - sl_min_wire_spacing
			end_scan_coord           = net_segment.polygon.bbox.ur.y + sl_min_wire_spacing
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
			sites_blocked = numpy.zeros(shape=(1, end_scan_coord - start_scan_coord))
			sites_ind = 0
			while curr_scan_coord < end_scan_coord:
				sl_poly_overlap = False
				for poly in net_segment.nearby_sl_polygons:
					if direction == 'N' or direction == 'S':
						if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_pitch)) or poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_overlap)):
							for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
								sites_blocked[0, i] = 1
							break
					else:
						if poly.is_point_inside(Point(curr_fixed_coord_pitch, curr_scan_coord)) or poly.is_point_inside(Point(curr_fixed_coord_overlap, curr_scan_coord)):
							for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
								sites_blocked[0, i] = 1
							break
				curr_scan_coord += layout.net_blockage_step
				sites_ind       += layout.net_blockage_step
	
			# Apply sliding window of size (2 * min_spacing * min_wire_width) to calculate wire position blockages
			window_start    = start_scan_coord
			window_end      = window_start + sl_required_open_width
			windows_scanned = 0
			windows_blocked = 0

			while window_end <= end_scan_coord:
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

		# Analyze blockage along the adjacent layers (top and bottom)
		else:
			# Only analyze if top/bottom adjacent layer is routable
			if   direction == 'T' and (net_segment.layer_num < layout.lef.top_routing_layer_num):
				# Get minimum wire width/spacing constraints for the adjacent layer
				al_min_width           = layout.lef.layers[net_segment.layer_num + 1].min_width_db
				al_min_wire_spacing    = layout.lef.layers[net_segment.layer_num + 1].min_spacing_db - 1
				al_required_open_width = layout.lef.layers[net_segment.layer_num + 1].rogue_wire_width

				# Get nearby polygons to analyze
				nearby_polys = net_segment.nearby_al_polygons
			elif direction == 'B' and (net_segment.layer_num > layout.lef.bottom_routing_layer_num):
				# Get minimum wire width/spacing constraints for the adjacent layer
				al_min_width           = layout.lef.layers[net_segment.layer_num - 1].min_width_db
				al_min_wire_spacing    = layout.lef.layers[net_segment.layer_num - 1].min_spacing_db - 1
				al_required_open_width = layout.lef.layers[net_segment.layer_num - 1].rogue_wire_width

				# Get nearby polygons to analyze
				nearby_polys = net_segment.nearby_bl_polygons
			else:
				continue
			
			# Skip iteration if no nearbly polygons
			if not nearby_polys:
				continue

			# Create bitmap
			net_segment_area_poly   = Polygon.from_rect_poly_and_extension(net_segment.polygon, al_min_wire_spacing, al_min_wire_spacing)
			net_segment_area_bitmap = numpy.zeros(shape=(net_segment_area_poly.bbox.get_height(), net_segment_area_poly.bbox.get_width()))
			print "		Checking (%d) nearby polygons along %s side (GDSII Layer:) ..." % (len(nearby_polys), direction)

			# Color the bitmap
			for poly in nearby_polys:
				# First check if bounding boxes overlap
				if net_segment.polygon.bbox.overlaps_bbox(poly.bbox):
					color_bitmap(net_segment_area_bitmap, net_segment.polygon.bbox.ll, poly)
			
			# Calculate windows blocked
			windows_scanned, windows_blocked = compute_al_windows_blocked(net_segment_area_bitmap, net_segment, al_min_width, al_min_wire_spacing, al_required_open_width)
			
			# Updated sides unblocked
			if windows_blocked < windows_scanned:
				sides_unblocked.append(direction)

			# Updated different layer blockage stats
			num_diff_layer_units_checked += windows_scanned
			diff_layer_units_blocked     += windows_blocked

			# Free bitmap memory
			del net_segment_area_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, sides_unblocked, num_diff_layer_units_checked, diff_layer_units_blocked

def check_blockage(net_segment, layout):
	num_same_layer_units_checked = 0
	same_layer_units_blocked     = 0
	num_diff_layer_units_checked = 0
	diff_layer_units_blocked     = 0
	sides_unblocked 			 = []
	check_distance               = (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width)) * layout.lef.database_units
	print "		Check Distance (uM):", (layout.lef.layers[net_segment.layer_name].pitch - (0.5 * layout.lef.layers[net_segment.layer_name].width))

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
			if direction == 'T' and (net_segment.layer_num < layout.lef.top_routing_layer_num):
				nearby_polys = net_segment.nearby_al_polygons
				print "		Checking (%d) nearby polygons along %s side (Layer: %d) ..." % (len(nearby_polys), direction, net_segment.layer_num + 1)
			elif direction == 'B' and (net_segment.layer_num > layout.lef.bottom_routing_layer_num):
				nearby_polys = net_segment.nearby_bl_polygons
				print "		Checking (%d) nearby polygons along %s side (Layer: %d) ..." % (len(nearby_polys), direction, net_segment.layer_num - 1)
			else:
				continue

			# Color the bitmap
			for poly in nearby_polys:
				# First check if bounding boxes overlap
				if net_segment.polygon.bbox.overlaps_bbox(poly.bbox):
					color_bitmap(net_segment_bitmap, net_segment.polygon.bbox.ll, poly)

			# Calculate colored area
			diff_layer_units_blocked     += bits_colored(net_segment_bitmap)
			num_diff_layer_units_checked += net_segment.polygon.get_area()

			# Free bitmap memory
			del net_segment_bitmap

	return num_same_layer_units_checked, same_layer_units_blocked, sides_unblocked, num_diff_layer_units_checked, diff_layer_units_blocked
	
def analyze_critical_net_blockage(layout, verbose):
	total_perimeter_units     = 0
	total_top_bottom_area     = 0
	total_same_layer_blockage = 0 
	total_diff_layer_blockage = 0

	# Extract all GDSII elements near security-critical nets
	layout.extract_nearby_polygons()
	# layout.extract_nearby_polygons_parallel()

	for net in layout.critical_nets:
		print "Analyzing Net: ", net.fullname
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
				print "		Layer:                    ", net_segment.layer_num
				print "		GDSII Element:            ", gdsii_element_type
				print "		Perimeter (dbu):          ", net_segment.polygon.bbox.get_perimeter()
				print "		Step Size (dbu):          ", layout.net_blockage_step
				print "		Pitch (uM):               ", layout.lef.layers[net_segment.layer_name].pitch 
				print "		Default Width (uM):       ", layout.lef.layers[net_segment.layer_name].width 
				print "		Min SL Width (uM):        ", layout.lef.layers[net_segment.layer_num].min_width
				if net_segment.layer_num < layout.lef.top_routing_layer_num:
					print "		Min TL Width (uM):        ", layout.lef.layers[net_segment.layer_num + 1].min_width 
				if net_segment.layer_num > layout.lef.bottom_routing_layer_num:
					print "		Min BL Width (uM):        ", layout.lef.layers[net_segment.layer_num - 1].min_width 
				print "		Top and Bottom Area (dbu):", (net_segment.polygon.get_area() * 2)
				print "		BBox (M-Units):           ", net_segment.polygon.bbox.get_bbox_as_list()
				print "		Nearby SL BBox (M-Units): ", net_segment.nearby_sl_bbox.get_bbox_as_list()
				if net_segment.layer_num < layout.lef.top_routing_layer_num:
					print "		Nearby TL BBox (M-Units): ", net_segment.nearby_al_bbox.get_bbox_as_list()
				if net_segment.layer_num > layout.lef.bottom_routing_layer_num:
					print "		Nearby BL BBox (M-Units): ", net_segment.nearby_bl_bbox.get_bbox_as_list()
				print "		Num. Nearby Polygons:     ", len(net_segment.nearby_al_polygons) + len(net_segment.nearby_bl_polygons) + len(net_segment.nearby_sl_polygons)
				if gdsii_element_type == "Path":
					print "		Klayout Query:       " 
					print "			paths on layer %d/%d of cell MAL_TOP where" % (net_segment.polygon.gdsii_element.layer, net_segment.polygon.gdsii_element.data_type)
					print "			shape.path.bbox.left==%d &&"  % (net_segment.polygon.bbox.ll.x)
					print "			shape.path.bbox.right==%d &&" % (net_segment.polygon.bbox.ur.x)
					print "			shape.path.bbox.top==%d &&"   % (net_segment.polygon.bbox.ur.y)
					print "			shape.path.bbox.bottom==%d"   % (net_segment.polygon.bbox.ll.y)
				elif gdsii_element_type == "Boundary":
					print "		Klayout Query:       " 
					print "			boxes on layer %d/%d of cell MAL_TOP where" % (net_segment.polygon.gdsii_element.layer, net_segment.polygon.gdsii_element.data_type)
					print "			shape.box.left==%d &&"  % (net_segment.polygon.bbox.ll.x)
					print "			shape.box.right==%d &&" % (net_segment.polygon.bbox.ur.x)
					print "			shape.box.top==%d &&"   % (net_segment.polygon.bbox.ur.y)
					print "			shape.box.bottom==%d"   % (net_segment.polygon.bbox.ll.y)

			# Check N, E, S, W, T, B
			start_time = time.time()
			if layout.net_blockage_type == 1:
				num_same_layer_units_checked, same_layer_blockage, sides_unblocked, num_diff_layer_units_checked, diff_layer_blockage = check_blockage_constrained(net_segment, layout)
			else:
				num_same_layer_units_checked, same_layer_blockage, sides_unblocked, num_diff_layer_units_checked, diff_layer_blockage = check_blockage(net_segment, layout)
			net_segment.same_layer_units_blocked = same_layer_blockage
			net_segment.diff_layer_units_blocked = diff_layer_blockage 
			net_segment.same_layer_units_checked = num_same_layer_units_checked
			net_segment.diff_layer_units_checked = num_diff_layer_units_checked 
			net_segment.sides_unblocked          = sides_unblocked
			total_same_layer_blockage            += same_layer_blockage
			total_diff_layer_blockage            += diff_layer_blockage
			total_perimeter_units                += num_same_layer_units_checked
			total_top_bottom_area                += num_diff_layer_units_checked

			if sides_unblocked:
				print "		Sides Unblocked:", sides_unblocked
			print "		Perimeter Units Blocked:  %d / %d" % (same_layer_blockage, num_same_layer_units_checked)
			print "		Top/Bottom Units Blocked: %d / %d" % (diff_layer_blockage, num_diff_layer_units_checked)
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"
			
			path_segment_counter += 1

	# Calculate raw and weighted blockage percentages.
	# Weighted accounts for area vs. perimeter blockage
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
