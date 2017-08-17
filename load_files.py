# Import Graphviz Library
import pygraphviz as pgv

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import time
import sys

# Loads nets from a Graphviz dot file.
# Returns a dictionary of net names in the format:
# Key<net fullname> --> Value<net basename>
def load_dot_file(dot_fname):
	print "Loading nets from .dot file ..."
	start_time = time.time()

	nets = {}

	# Load critical nets .dot file
	nets_graph = pgv.AGraph(dot_fname)

	# Extract graph node full names
	net_full_names = nets_graph.nodes()

	# Extract base names of graph nodes
	for full_name in net_full_names:
		full_name       = full_name.encode('ascii', 'replace')
		full_name_list  = full_name.split('.')
		base_name 	    = full_name_list[-1]
		nets[full_name] = base_name

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return nets

# Loads entire circuit layout from GDSII file. 
# Returns a GDSII library object.
def load_gdsii_library(gdsii_fname):
	print "Loading GDSII file ..."
	start_time = time.time()

	# Open GDSII File
	with open(gdsii_fname, 'rb') as stream:
	    lib = Library.load(stream)

	# Close GDSII File
	stream.close()  

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return lib

# Loads entire layer map file for technology node. 
# Returns a dictionary of the following format:
# Key<layer number> --> Value< Key<data type> --> Value <layer name> >
def load_layer_map(map_fname):
	print "Loading layer map file ..."
	start_time = time.time()

	layer_map = {}

	# Open GDSII File
	with open(map_fname, 'rb') as stream:
	    for line in stream:
	    	# Do not process comment lines
	    	if (len(line) > 0) and (line[0] != "#"):
		    	line = line.rstrip()
		    	line_list = line.split(' ')

		    	# Check if layer map file is the correct format
		    	# Correct Line Format: <Cadence Layer Name> | <layer purpose> | <layer number> | <data type>
		    	if len(line_list) != 4:
		    		print "ERROR <load_layer_map>: layer map file format not recognized."
		    		sys.exit(1)
		    	cad_layer_name = line_list[0]
		    	layer_num 	   = int(line_list[2])
		    	data_type      = int(line_list[3])
		    	if layer_num not in layer_map:
		    		layer_map[layer_num] = {data_type: cad_layer_name}
		    	else:
		    		if data_type not in layer_map[layer_num]:
		    			layer_map[layer_num][data_type] = cad_layer_name
	    	
	# Close GDSII File
	stream.close()  

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return layer_map
