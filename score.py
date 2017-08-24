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

def check_north_blockage(net_segment, layout):
	curr_x_coord      = net_segment.ll_x_coord
	north_y_coord     = net_segment.ur_y_coord
	print "NORTH-Y: ", north_y_coord
	routing_direction = layout.lef.layers[net_segment.layer_name].direction 
	num_units_blocked = 0

	print "		Checking %d units along NORTH edge..." % (net_segment.ur_x_coord - curr_x_coord)
	if net_segment.direction == "V":
		# Path is Vertical
		if routing_direction == "V":
			# Routing Direction is Vertical
			print "Routing V"
			while curr_x_coord < net_segment.ur_x_coord:
				check_distance = layout.lef.layers[net_segment.layer_name].pitch * layout.lef.database_units
				if layout.is_point_blocked(curr_x_coord, north_y_coord + check_distance, net_segment.gdsii_path.layer):
					num_units_blocked += 1
				return num_units_blocked
				curr_x_coord += 1
		else:
			# Routing Direction is Horizontal
			print "UNSUPPORTED %s: vertical paths on horizontal routing layer not supported." % (inspect.stack()[0][3])
			sys.exit(3)
	else:
		# Path is Horizontal
		if routing_direction == "H":
			# Routing Direction is Horizontal
			while curr_x_coord < net_segment.ur_x_coord:
				check_distance = layout.lef.layers[net_segment.layer_name].pitch * layout.lef.database_units
				if layout.is_point_blocked(curr_x_coord, north_y_coord + check_distance, net_segment.gdsii_path.layer):
					num_units_blocked += 1
				return num_units_blocked
				curr_x_coord += 1
		else:
			# Routing Direction is Vertical
			print "UNSUPPORTED %s: horizontal paths on vertical routing layer not supported." % (inspect.stack()[0][3])
			sys.exit(3)
	print "Done."
	return num_units_blocked
	
def analyze_critical_path_connection_points(layout):
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
			print "		Layer:        ", net_segment.layer_num
			print "		Bounding Box: ", net_segment.get_bbox()
			print "		Perimeter:    ", perimeter

			# Check NORTH
			north_perimeter_blocked = check_north_blockage(net_segment, layout)
			print "		N-Perimeter Blocked: ", north_perimeter_blocked
			break
			# Check EAST
			# Check SOUTH
			# Check WEST
			# Check ABOVE
			# Check BELOW

def main():
	INPUT_LEF_FILE_PATH       = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef'
	INPUT_LAYER_MAP_FILE_PATH = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.map'
	INPUT_GDSII_FILE_PATH 	  = 'gds/MAL_TOP.all.netname.gds'
	INPUT_DOT_FILE_PATH       = 'graphs/MAL_TOP_par.supv_2.dot'

	# Load layout and critical nets
	layout = Layout(INPUT_LEF_FILE_PATH, \
		INPUT_LAYER_MAP_FILE_PATH, \
		INPUT_GDSII_FILE_PATH, \
		INPUT_DOT_FILE_PATH)

	if DEBUG_PRINTS:
		dbg.debug_print_lib_obj(layout.gdsii_lib)
		dbg.debug_print_gdsii_stats(layout.gdsii_lib)
		dbg.debug_print_gdsii_hierarchy(layout.gdsii_lib)

	# Analyze security critical paths in GDSII
	analyze_critical_path_connection_points(layout)

if __name__ == "__main__":
    main()

# Example search query for Klayout GDSII viewer:
#
# paths on layer 17/0 of cell MAL_TOP where 
# shape.path.bbox.left==535150 && 
# shape.path.bbox.right==535990 && 
# shape.path.bbox.top==545370 && 
# shape.path.bbox.bottom==545230 

