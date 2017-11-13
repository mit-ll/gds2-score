# Import Custom Modules
import debug_prints as dbg

# Import Example Metric Modules
from net_blockage  import *
from trigger_space import *
from edit_distance import *

# Other Imports
import time
import sys
import getopt
import copy

# # Import Memory Leak Tool
# from pympler import muppy, summary

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# Global Program Switches
DEBUG_PRINTS  = False
VERBOSE       = False
NET_BLOCKAGE  = False
TRIGGER_SPACE = False

def calculate_and_print_time(start_time, end_time):
	hours, rem       = divmod(end_time - start_time, 3600)
	minutes, seconds = divmod(rem, 60)
	print "Execution Time:", "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)

# ------------------------------------------------------------------
# Usage statement and entry points to metric functions
# ------------------------------------------------------------------
# Print program usage statement
def usage():
	print "Usage: python score.py {-a|-b|-t|-e} [-hv] -g <gdsii> -m <top module> -r <route LEF> -p <placement LEF> -l <layer map> -d <DEF> -n <Nemo .dot> [-s <placement grid .npy>]"
	print "Options:"
	print "	-h, --help	Show this message."
	print "	-b, --blockage	Calculate critical net blockage metric."
	print "	-t, --trigger	Calculate open trigger space metric."
	print "	-e, --edit_distance	Calculate routing edit distance."
	print "	-a, --all	Calculate all metrics."
	print "	-v, --verbose Verbose prints."
	print "	-g, --gds	GDSII input file."
	print "	-m, --top_level_module	Top level module name."
	print "	-r, --route_lef	Routing LEF input file."
	print "	-p, --place_lef	Placement LEF input file."
	print "	-l, --layer_map	Layer map input file."
	print "	-d, --def	DEF input file."
	print "	-n, --nemo_dot	Nemo .dot file."
	print " -s, --place_grid	Placement output file (include .npy extension)."

# Analyze blockage of security critical nets in GDSII
def blockage_metric(layout):
	start_time = time.time()
	print "Starting Net Blockage Analysis:"
	analyze_critical_net_blockage(layout, VERBOSE)
	end_time = time.time()
	print "Done - Net Blockage Analysis."
	calculate_and_print_time(start_time, end_time)
	print "----------------------------------------------"
	return

# Analyze empty space for implanting triggers in GDSII
def trigger_space_metric(layout):
	start_time = time.time()
	print "Starting Trigger Space Analysis:"
	analyze_open_space_for_triggers(layout)
	end_time = time.time()
	print "Done - Trigger Space Analysis."
	calculate_and_print_time(start_time, end_time)
	print "----------------------------------------------"
	return

# Analyze edit distance required for routing
def edit_distance_metric(layout):
	start_time = time.time()
	print "Starting Edit Distance Analysis:"
	analyze_routing_edit_distance(layout)
	end_time = time.time()
	print "Done - Edit Distance Analysis."
	calculate_and_print_time(start_time, end_time)
	print "----------------------------------------------"
	return

# ------------------------------------------------------------------
# Main Entry Point of GDSII-Score
# ------------------------------------------------------------------
def main(argv):
	# dbg.debug_weiler_atherton_algorithm_1()
	# dbg.debug_weiler_atherton_algorithm_2()
	# return
	
	# Global Program Switches
	global DEBUG_PRINTS # currently not set by command args --> set to True to turn on
	global VERBOSE
	global NET_BLOCKAGE
	global TRIGGER_SPACE
	global EDIT_DISTANCE

	# Input Info/File Names 
	TOP_LEVEL_MODULE          = 'MAL_TOP'
	INPUT_MS_LEF_FILE_PATH    = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef'
	INPUT_SC_LEF_FILE_PATH    = 'gds/sc12_base_v31_rvt_soi12s0.lef'
	INPUT_DEF_FILE_PATH       = 'gds/MAL_TOP.def'
	INPUT_LAYER_MAP_FILE_PATH = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.map'
	INPUT_GDSII_FILE_PATH 	  = 'gds/MAL_TOP.merged.gds'
	INPUT_DOT_FILE_PATH       = 'graphs/MAL_TOP_par.supv_2.dot'
	OUTPUT_PGRID              =  None
	# FILL_CELL_NAMES           = []
	FILL_CELL_NAMES           = ["FILLDGCAP8_A12TR", "FILLDGCAP16_A12TR", "FILLDGCAP32_A12TR", "FILLDGCAP64_A12TR"]

	# Load command line arguments
	try:
		opts, args = getopt.getopt(argv, "abtehvg:m:r:p:l:d:n:s:", ["all", "blockage", "trigger", "edit_distance", "help", "verbose", "gds", "top_level_module", "route_lef", "place_lef", "layer_map", "def", "nemo_dot", "place_grid"])
	except getopt.GetoptError:
		usage()
		sys.exit(4)

	# # Enforce correct usage of program
	# opt_flags = zip(*opts)[0]
	# if  ("-b" not in opt_flags and "--blockage"         not in opt_flags  and \
	# 	"-t"  not in opt_flags and "--trigger"          not in opt_flags  and \
	# 	"-e"  not in opt_flags and "--edit_distance"    not in opt_flags  and \
	# 	"-a"  not in opt_flags and "--all"              not in opt_flags) or \
	# 	("-g" not in opt_flags and "--gds"              not in opt_flags) or \
	# 	("-m" not in opt_flags and "--top_level_module" not in opt_flags) or \
	# 	("-r" not in opt_flags and "--route_lef"        not in opt_flags) or \
	# 	("-p" not in opt_flags and "--place_lef"        not in opt_flags) or \
	# 	("-l" not in opt_flags and "--layer_map"        not in opt_flags) or \
	# 	("-d" not in opt_flags and "--def"              not in opt_flags) or \
	# 	("-n" not in opt_flags and "--nemo_dot"         not in opt_flags) or \
	# 	# ("-s" not in opt_flags and "--place_grid"       not in opt_flags):
	# 	usage()
	# 	sys.exit(4)
	
	# Parse command line arguments
	for opt, arg in opts:
		if opt in ("-h", "--help"): 
			usage()                     
			sys.exit(4)
		elif opt in ("-b", "--blockage"):
			NET_BLOCKAGE = True
		elif opt in ("-t", "--trigger"):
			TRIGGER_SPACE = True
		elif opt in ("-e", "--edit_distance"):
			EDIT_DISTANCE = True
		elif opt in ("-a", "--all"):
			NET_BLOCKAGE  = True
			TRIGGER_SPACE = True
			EDIT_DISTANCE = True
		elif opt in ("-v", "--verbose"):
			VERBOSE = True
		elif opt in ("-g", "--gds"):
			INPUT_GDSII_FILE_PATH = copy.copy(arg)
		elif opt in ("-m", "--top_level_module"):
			TOP_LEVEL_MODULE = copy.copy(arg)
		elif opt in ("-r", "--route_lef"):
			INPUT_MS_LEF_FILE_PATH = copy.copy(arg)
		elif opt in ("-p", "--place_lef"):
			INPUT_SC_LEF_FILE_PATH = copy.copy(arg)
		elif opt in ("-l", "--layer_map"):
			INPUT_LAYER_MAP_FILE_PATH = copy.copy(arg)
		elif opt in ("-d", "--def"):
			INPUT_DEF_FILE_PATH = copy.copy(arg)
		elif opt in ("-n", "--nemo_dot"):
			INPUT_DOT_FILE_PATH = copy.copy(arg)
		elif opt in ("-s", "--place_grid"):
			OUTPUT_PGRID = copy.copy(arg)
		else:
			usage()
			sys.exit(4) 
	
	# Start program timer
	overall_start_time = time.time()

	# Load layout and critical nets
	layout = Layout( \
		TOP_LEVEL_MODULE, \
		INPUT_MS_LEF_FILE_PATH, \
		INPUT_SC_LEF_FILE_PATH, \
		INPUT_DEF_FILE_PATH, \
		INPUT_LAYER_MAP_FILE_PATH, \
		INPUT_GDSII_FILE_PATH, \
		INPUT_DOT_FILE_PATH, \
		FILL_CELL_NAMES, \
		OUTPUT_PGRID)

	# # Print memory usage summary
	# summary.print_(summary.summarize(muppy.get_objects()))
	# raw_input("Press key to continue...")

	if DEBUG_PRINTS:
		dbg.debug_print_lib_obj(layout.gdsii_lib)
		print "----------------------------------------------"
		dbg.debug_print_gdsii_stats(layout.gdsii_lib)
		print "----------------------------------------------"
		dbg.debug_print_gdsii_hierarchy(layout.gdsii_lib)
		print "----------------------------------------------"

	# Check if any critical signals found in GDSII
	if not (layout.critical_nets):
		print "WARNING: Could not locate any critical nets in GDSII."
	else:
		# Blockage Metric
		if NET_BLOCKAGE:
			blockage_metric(layout)
		
		# Trigger Space Metric
		if TRIGGER_SPACE:
			trigger_space_metric(layout)

		# Edit Distance Metric
		if EDIT_DISTANCE:
			edit_distance_metric(layout)

	# Calculate and print total execution time
	overall_end_time = time.time()
	print "ICAD Analyses Complete."
	calculate_and_print_time(overall_start_time, overall_end_time)

if __name__ == "__main__":
    main(sys.argv[1:])
