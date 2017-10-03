# Import Custom Modules
import debug_prints as dbg

# Import Example Metric Modules
from net_blockage  import *
from trigger_space import *

# Other Imports
import time
import sys
import getopt

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

# ------------------------------------------------------------------
# Usage statement and entry points to metric functions
# ------------------------------------------------------------------
# Print program usage statement
def usage():
	print "Usage: python score.py {-a|-b|-t} [-hdv]"
	print "Options:"
	print "	-h, --help	Show this message."
	print "	-b, --blockage	Calculate critical net blockage metric."
	print "	-t, --trigger	Calculate open trigger space metric."
	print "	-a, --all	Calculate all metrics."
	print "	-d, --debug	Debug prints."
	print "	-v, --verbose Verbose prints."

# Analyze blockage of security critical nets in GDSII
def blockage_metric(layout):
	start_time = time.time()
	print "Starting Blockage Analysis:"
	blockage_percentage = analyze_critical_net_blockage(layout, VERBOSE)
	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "Blockage Percentage: %4.2f%%" % (blockage_percentage) 
	print "----------------------------------------------"
	return

# Analyze empty space for implanting triggers in GDSII
def trigger_space_metric(layout):
	start_time = time.time()
	print "Starting Trigger Space Analysis:"
	analyze_open_space_for_triggers(layout)
	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return

# ------------------------------------------------------------------
# Main Entry Point of GDSII-Score
# ------------------------------------------------------------------
def main(argv):
	# Global Program Switches
	global DEBUG_PRINTS
	global VERBOSE
	global NET_BLOCKAGE
	global TRIGGER_SPACE

	trigger_space_metric(None)
	return

	# Input Filenames
	TOP_LEVEL_MODULE          = 'MAL_TOP'
	INPUT_LEF_FILE_PATH       = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.lef'
	INPUT_LAYER_MAP_FILE_PATH = 'gds/tech_nominal_25c_3_20_20_00_00_02_LB.map'
	INPUT_GDSII_FILE_PATH 	  = 'gds/MAL_TOP.merged.gds'
	INPUT_DOT_FILE_PATH       = 'graphs/MAL_TOP_par.supv_2.dot'
	# INPUT_DEF_FILE_PATH       = '.def'

	# Load command line arguments
	try:
		opts, args = getopt.getopt(argv, "abthdv", ["all", "blockage", "trigger", "help", "debug", "verbose"])
	except getopt.GetoptError:
		usage()

	# Enforce correct usage of program
	opt_flags = zip(*opts)[0]
	if "-b" not in opt_flags and \
		"-t" not in opt_flags and \
		"-a" not in opt_flags and \
		"--blockage" not in opt_flags and \
		"--trigger" not in opt_flags and \
		"--all" not in opt_flags:
		usage()
		sys.exit(4)
	
	# Parse command line arguments
	for opt, arg in opts:
		if opt in ("-h", "--help"): 
			usage()                     
			sys.exit(4)
		elif opt in ("-b", "--blockage"):
			NET_BLOCKAGE = True
		elif opt in ("-t", "--trigger"):
			TRIGGER_SPACE = True
		elif opt in ("-a", "--all"):
			NET_BLOCKAGE = True
			TRIGGER_SPACE = True
		elif opt in ("-d", "--debug"):
			DEBUG_PRINTS = True
		elif opt in ("-v", "--verbose"):
			VERBOSE = True
		else:
			usage()
			sys.exit(4) 
	
	# Start program timer
	overall_start_time = time.time()

	# Load layout and critical nets
	layout = Layout( \
		TOP_LEVEL_MODULE, \
		INPUT_LEF_FILE_PATH, \
		INPUT_LAYER_MAP_FILE_PATH, \
		INPUT_GDSII_FILE_PATH, \
		INPUT_DOT_FILE_PATH)

	if DEBUG_PRINTS:
		dbg.debug_print_lib_obj(layout.gdsii_lib)
		print "----------------------------------------------"
		dbg.debug_print_gdsii_stats(layout.gdsii_lib)
		print "----------------------------------------------"
		dbg.debug_print_gdsii_hierarchy(layout.gdsii_lib)
		print "----------------------------------------------"

	# Blockage Metric
	if NET_BLOCKAGE:
		blockage_metric(layout)
	
	# Trigger Space Metric
	if TRIGGER_SPACE:
		trigger_space_metric(layout)

	# Calculate and print total execution time
	overall_end_time = time.time()
	hours, rem       = divmod(overall_end_time - overall_start_time, 3600)
	minutes, seconds = divmod(rem, 60)
	print "Total Execution Time: ", "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)

if __name__ == "__main__":
    main(sys.argv[1:])
