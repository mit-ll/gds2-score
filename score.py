# Import Custom Modules
import load_files   as load 
import lef          as lef
import debug_prints as dbg

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import time
import pprint

DEBUG_PRINTS = True

# ---------------------------------------------
# Technology Specific Layers
# THIS MUST BE HAND DEFINED BY USER ... for now
# ---------------------------------------------
tech_net_layers = {
	1  : "m1",
	2  : "m2",
	3  : "m3",
	4  : "c1",
	5  : "c2",
	6  : "b1",
	7  : "b2",
	8  : "ua",
	9  : "ub",
	10 : "lb"
}

tech_via_layers = {
	1  : "v1",
	2  : "v2",
	3  : "ay",
	4  : "a1",
	5  : "w0",
	6  : "w1",
	7  : "ta",
	8  : "ga",
	9  : "vv"
}
# ---------------------------------------------

# def gdsii_layer_num_2_logical_num(layer_map, tech_net_layers):

# def is_via_layer():

# def is_net_layer():

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
			# elif isinstance(element, Boundary):
			# 	dbg.debug_print_boundary_obj(element)
			
	# Debug Prints
	if DEBUG_PRINTS:
		print
		print "Critical paths (nets):"
		pprint.pprint(critical_paths.keys())
		print

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return critical_paths

def analyze_critical_paths(critical_paths):
	for path_name in critical_paths.keys():
		for path_obj in critical_paths[path_name]:
			dbg.debug_print_path_obj(path_obj)

def main():
	# Load critical nets
	critical_nets  = load.load_dot_file('graphs/MAL_TOP_par.supv_2.dot')

	# Load GDSII layout
	gdsii_lib      = load.load_gdsii_library('gds/MAL_TOP.all.netname.gds')

	# Load layer map
	layer_map 	   = load.load_layer_map('gds/tech_nominal_25c_3_20_20_00_00_02_LB.map')

	# Load LEF file
	lef_info 	   = lef.LEF('gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef')

	# Extract critical circuit paths
	critical_paths = extract_critical_paths(gdsii_lib, critical_nets)

	# Analyze security critical paths in GDSII
	analyze_critical_paths(critical_paths)

if __name__ == "__main__":
    main()



