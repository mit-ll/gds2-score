# Import Custom Modules
import load_files   as load 
import lef          as lef
import debug_prints as dbg

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import time
import sys
import pprint

DEBUG_PRINTS = True

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature

def extract_critical_paths(gdsii_lib, critical_nets):
	print "Extracting critical GDSII paths (nets)..."
	start_time = time.time()

	critical_paths = {}

	# Extract path structures from GDSII file
	for structure in gdsii_lib:
		for element in structure:
			if isinstance(element, Path):
				path_name = element.properties[0][1] # property 1 of Path element is the net name
				if path_name in critical_paths:
					critical_paths[path_name].append(element)
				else:
					# Check if path is critical or not
					path_basename = path_name.split('/')[-1]
					if path_basename in critical_nets.values():
						critical_paths[path_name] = [element]

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return critical_paths

def gds_layer_2_logical_layer(element_obj, lef_info, layer_map):
	layer_name = layer_map[element_obj.layer][element_obj.data_type]
	return lef_info.layers[layer_name].layer_num

def compute_bb(element_obj):
	if isinstance(element_obj, Path):
		if element_obj.path_type == 0:
			print "ERROR <compute_bb>: Path object path_type 0 not handled."
			sys.exit(3)
		elif element_obj.path_type == 1:
			continue
		elif element_obj.path_type == 2:
		elif element_obj.path_type == 4:
		else:
			print "ERROR <compute_bb>: unknown Path object path_type."
			sys.exit(2)

def analyze_critical_path_connection_points(critical_paths, lef_info, gdsii_lib, layer_map):
	# Debug Prints
	if DEBUG_PRINTS:
		print
		print "Critical paths (nets):"
		pprint.pprint(critical_paths.keys())
		print

	for path_name in critical_paths.keys():
		print "Analying Critical Net: ", path_name
		for path_obj in critical_paths[path_name]:
			path_segment_counter = 1
			if DEBUG_PRINTS:
				dbg.debug_print_path_obj(path_obj)
			# Report Path Segment Condition
			print "Analyzing path segment ", path_segment_counter
			print "	Layer: ", gds_layer_2_logical_layer(path_obj, lef_info, layer_map)
			print "	Layer: ", gds_layer_2_logical_layer(path_obj, lef_info, layer_map)
			# Check NORTH
			# Check EAST
			# Check SOUTH
			# Check WEST
			# Check ABOVE
			# Check BELOW

def main():
	# Load critical nets
	critical_nets  = load.load_dot_file('graphs/MAL_TOP_par.supv_2.dot')

	# Load GDSII layout
	# gdsii_lib      = load.load_gdsii_library('gds/MAL_TOP.all.netname.gds')

	# Load layer map
	layer_map 	   = load.load_layer_map('gds/tech_nominal_25c_3_20_20_00_00_02_LB.map')

	# Load LEF file
	lef_info 	   = lef.LEF('gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef')

	# Extract critical circuit paths
	critical_paths = extract_critical_paths(gdsii_lib, critical_nets)

	# Analyze security critical paths in GDSII
	analyze_critical_paths(critical_paths, lef_info, gdsii_lib, layer_map)

if __name__ == "__main__":
    main()



