# Import Custom Modules
import debug_prints as dbg
from net    import *
from layout import *

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import time
import inspect
import sys

DEBUG_PRINTS = True

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

def check_blockage(net_segment, layout, direction, step_size, check_distance):
	num_units_blocked = 0

	# Scan all 4 perimeter sides to check for blockages
	for direction in ['N', 'E', 'S', 'W']:
		if direction == 'N':
			curr_scan_coord  = net_segment.ll_x_coord
			end_scan_coord   = net_segment.ur_x_coord
			curr_fixed_coord = net_segment.ur_y_coord + check_distance
		elif direction == 'E':
			curr_scan_coord  = net_segment.ll_y_coord
			end_scan_coord   = net_segment.ur_y_coord
			curr_fixed_coord = net_segment.ur_x_coord + check_distance
		elif direction == 'S':
			curr_scan_coord  = net_segment.ll_x_coord
			end_scan_coord   = net_segment.ur_x_coord
			curr_fixed_coord = net_segment.ll_y_coord - check_distance
		elif direction == 'W':
			curr_scan_coord  = net_segment.ll_y_coord
			end_scan_coord   = net_segment.ur_y_coord
			curr_fixed_coord = net_segment.ll_x_coord - check_distance
		else:
			print "ERROR %s: unknown scan direction (%s)." % (inspect.stack()[0][3], direction)
			sys.exit(4)
		
		num_points_to_scan = ((end_scan_coord - curr_scan_coord) / step_size) + 1
		print "		Checking %d units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, check_distance / layout.lef.database_units)
		
		while curr_scan_coord < end_scan_coord:
			if direction == 'N' or direction == 'S':
				if layout.is_point_blocked(curr_scan_coord, curr_fixed_coord, net_segment.gdsii_path.layer):
					num_units_blocked += 1
			else:
				if layout.is_point_blocked(curr_fixed_coord, curr_scan_coord, net_segment.gdsii_path.layer):
					num_units_blocked += 1
			curr_scan_coord += step_size
	
	return num_units_blocked
	
def analyze_critical_nets(layout):
	# Debug Prints
	if DEBUG_PRINTS:
		print
		print "Critical paths (nets):"
		for net in layout.critical_nets:
			print net.fullname
		print

	for net in layout.critical_nets:
		print "Analying Net: ", net.fullname
		for net_segment in net.segments:
			path_segment_counter = 1
			top_bottom_perimeter = net_segment.ur_x_coord - net_segment.ll_x_coord
			left_right_perimeter = net_segment.ur_y_coord - net_segment.ll_y_coord
			perimeter            = (2 * top_bottom_perimeter) + (2 * left_right_perimeter) 
			if DEBUG_PRINTS:
				dbg.debug_print_path_obj(net_segment.gdsii_path)

			# Report Path Segment Condition
			print "	Analyzing Net Segment ", path_segment_counter
			print "		Layer:         ", net_segment.layer_num
			print "		Bounding Box:  ", net_segment.get_bbox()
			print "		Perimeter:     ", perimeter
			print "		Klayout Query: " 
			print "			paths on layer %d/%d of cell MAL_TOP where" % (net_segment.gdsii_path.layer, net_segment.gdsii_path.data_type)
			print "			shape.path.bbox.left==%d &&"  % (net_segment.ll_x_coord)
			print "			shape.path.bbox.right==%d &&" % (net_segment.ur_x_coord)
			print "			shape.path.bbox.top==%d &&"   % (net_segment.ur_y_coord)
			print "			shape.path.bbox.bottom==%d"   % (net_segment.ll_y_coord)

			# check_path_blockage() Parameters
			step_size       = 100
			check_distance  = layout.lef.layers[net_segment.layer_name].pitch * layout.lef.database_units

			# Check NORTH
			start_time = time.time()
			north_perimeter_blocked = check_blockage(net_segment, layout, 'N', step_size, check_distance)
			print "		N-Perimeter Blocked: ", north_perimeter_blocked
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"

			# Check EAST
			start_time = time.time()
			east_perimeter_blocked = check_blockage(net_segment, layout, 'E', step_size, check_distance)
			print "		E-Perimeter Blocked: ", east_perimeter_blocked
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"

			# Check SOUTH
			start_time = time.time()
			south_perimeter_blocked = check_blockage(net_segment, layout, 'S', step_size, check_distance)
			print "		S-Perimeter Blocked: ", south_perimeter_blocked
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"

			# Check WEST
			start_time = time.time()
			west_perimeter_blocked = check_blockage(net_segment, layout, 'W', step_size, check_distance)
			print "		W-Perimeter Blocked: ", west_perimeter_blocked
			print "		Done - Time Elapsed:", (time.time() - start_time), "seconds."
			print "		----------------------------------------------"
			
			# Check ABOVE
			# Check BELOW

def main():
	TOP_LEVEL_MODULE          = 'MAL_TOP'
	INPUT_LEF_FILE_PATH       = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef'
	INPUT_LAYER_MAP_FILE_PATH = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.map'
	INPUT_GDSII_FILE_PATH 	  = 'gds/MAL_TOP.merged.gds'
	INPUT_DOT_FILE_PATH       = 'graphs/MAL_TOP_par.supv_2.dot'

	# Load layout and critical nets
	layout = Layout( \
		TOP_LEVEL_MODULE, \
		INPUT_LEF_FILE_PATH, \
		INPUT_LAYER_MAP_FILE_PATH, \
		INPUT_GDSII_FILE_PATH, \
		INPUT_DOT_FILE_PATH)

	if DEBUG_PRINTS:
		dbg.debug_print_lib_obj(layout.gdsii_lib)
		dbg.debug_print_gdsii_stats(layout.gdsii_lib)
		# dbg.debug_print_gdsii_hierarchy(layout.gdsii_lib)
		# dbg.debug_print_gdsii_sref_strans_stats(layout.gdsii_lib)
		# dbg.debug_print_gdsii_aref_strans_stats(layout.gdsii_lib)
		
	# Analyze security critical paths in GDSII
	start_time = time.time()
	print "Starting Blockage Analysis:"
	analyze_critical_nets(layout)
	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"

if __name__ == "__main__":
    main()

# Example search query for Klayout GDSII viewer:
#
# paths on layer 17/0 of cell MAL_TOP where 
# shape.path.bbox.left==535150 && 
# shape.path.bbox.right==535990 && 
# shape.path.bbox.top==545370 && 
# shape.path.bbox.bottom==545230 

