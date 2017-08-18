# Import Custom Modules
import net          as net
import load_files   as load 
import debug_prints as dbg

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import time
import inspect
import sys
import pprint

DEBUG_PRINTS = True

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature

# Returns true if the XY coordinate is inside or
# touching the bounding box provided. BB is formatted as
# [(LL_x, LL_y), (UR_x, UR_y)], and coord is formatted 
# as [X, Y].
def is_inside_bb(bb, coord):
	LL = 0
	UR = 1
	X  = 0
	Y  = 1
	if coord[X] >= bb[LL][X] and coord[X] <= bb[UR][X]:
		if coord[Y] >= bb[LL][Y] and coord[Y] <= bb[UR][Y]:
			return True
	return False

# def check_north_blockage(path_obj, lef_info, gdsii_lib, layer_map):
# 	if is_path_type_supported(path_obj):
# 		path_obj_bb   = compute_path_bb(path_obj)
# 		curr_x_coord  = path_obj_bb[0][0]
# 		north_y_coord = path_obj_bb[1][1]

# 		while curr_x_coord < path_obj_bb[1][0]:
# 			if path_direction(path_obj) == "V":
# 				# Path is Vertical
# 				if lef_info.get_routing_layer_direction(path_obj.layer, path_obj.data_type, layer_map) == "V":
# 					# Routing Direction is Vertical
# 					print "Vertical Path"
# 				else:
# 					# Routing Direction is Horizontal
# 					print "UNSUPPORTED %s: vertical paths on horizontal routing layer not supported." % (inspect.stack()[0][3])
# 					sys.exit(3)
# 			elif path_direction(path_obj) == "H":
# 				# Path is Horizontal
# 				if lef_info.get_routing_layer_direction(path_obj.layer, path_obj.data_type, layer_map) == "H":
# 					# Routing Direction is Horizontal
# 					while curr_x_coord <= path_obj_bb[1][0]
# 				else:
# 					# Routing Direction is Vertical
# 					print "UNSUPPORTED %s: horizontal paths on vertical routing layer not supported." % (inspect.stack()[0][3])
# 					sys.exit(3):

# def analyze_critical_path_connection_points(critical_paths, lef_info, gdsii_lib, layer_map):
# 	# Debug Prints
# 	if DEBUG_PRINTS:
# 		print
# 		print "Critical paths (nets):"
# 		pprint.pprint(critical_paths.keys())
# 		print

# 	for path_name in critical_paths.keys():
# 		print "Analying Critical Net: ", path_name
# 		for path_obj in critical_paths[path_name]:
# 			path_segment_counter = 1
# 			if DEBUG_PRINTS:
# 				dbg.debug_print_path_obj(path_obj)
# 			# Report Path Segment Condition
# 			print "Analyzing path segment ", path_segment_counter
# 			print "	Layer:        ", lef_info.get_layer_num(path_obj.layer, path_obj.data_type, layer_map)
# 			print "	Bounding Box: ", compute_path_bb(path_obj)

# 			# Check NORTH
# 			# check_north_blockage(path_obj, lef_info, gdsii_lib, layer_map)
# 			break
# 			# Check EAST
# 			# Check SOUTH
# 			# Check WEST
# 			# Check ABOVE
# 			# Check BELOW

def main():
	INPUT_LEF_FILE_PATH       = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef'
	INPUT_LAYER_MAP_FILE_PATH = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.map'
	INPUT_GDSII_FILE_PATH 	  = 'gds/MAL_TOP.all.netname.gds'
	INPUT_DOT_FILE_PATH       = 'graphs/MAL_TOP_par.supv_2.dot'

	# Load layout and critical nets
	layout = load.Layout(INPUT_LEF_FILE_PATH, INPUT_LAYER_MAP_FILE_PATH, INPUT_GDSII_FILE_PATH, INPUT_DOT_FILE_PATH)

	# Analyze security critical paths in GDSII
	# analyze_critical_path_connection_points(critical_paths, lef_info, gdsii_lib, layer_map)

if __name__ == "__main__":
    main()



