# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Import Graphviz Library
import pygraphviz as pgv

# Other Imports
import pprint
import time

DEBUG_PRINTS = True

def load_critical_nets(critical_nets_fname):
	print "Loading critical nets from .dot file ..."
	start_time = time.time()

	critical_nets = {}

	# Load critical nets .dot file
	critical_nets_graph = pgv.AGraph(critical_nets_fname)

	# Extract graph node full names
	node_full_names = critical_nets_graph.nodes()

	# Extract base names of graph nodes
	for full_name in node_full_names:
		full_name                = full_name.encode('ascii', 'replace')
		full_name_list           = full_name.split('.')
		base_name 	             = full_name_list[-1]
		critical_nets[full_name] = base_name

	# Debug Prints
	if DEBUG_PRINTS:
		print
		print "Critical Nets:"
		pprint.pprint(critical_nets)
		print

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return critical_nets

def load_circuit_paths(gdsii_fname):
	print "Loading circuit paths from GDS2 file ..."
	start_time = time.time()

	circuit_paths = {}

	# Open GDSII File
	with open(gdsii_fname, 'rb') as stream:
	    lib = Library.load(stream)

	# Print mask record
	debug_print_lib_obj(lib)

	# Extract path structures from GDSII file
	for structure in lib:
		# print structure.name
		for element in structure:
			if isinstance(element, Path):
				# print "		Path", element.properties
				path_name = element.properties[0][1]
				if path_name in circuit_paths:
					circuit_paths[path_name].append(element)
				else:
					circuit_paths[path_name] = [element]

	# Close GDSII File
	stream.close()

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return circuit_paths

def extract_critical_paths(circuit_paths, critical_nets):
	print "Extracting critical circuit paths ..."
	start_time = time.time()

	critical_paths = {}

	# Extract/Identify the critical path objects in the GDSII file
	for path_name in circuit_paths.keys():
		path_base_name = path_name.split('/')[-1]
		if path_base_name in critical_nets.values():
			critical_paths[path_name] = circuit_paths[path_name]
			
	# Debug Prints
	if DEBUG_PRINTS:
		print
		print "Critical Paths:"
		pprint.pprint(critical_paths)
		print

	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return critical_paths

def analyze_critical_paths(critical_paths):
	for path_name in critical_paths.keys():
		for path_obj in critical_paths[path_name]:
			debug_print_path_obj(path_obj)

def debug_print_lib_obj(lib_obj):
	print "Lib Object:"
	print "		version:       ", lib_obj.version
	print "		name:          ", lib_obj.name
	print "		physical_unit: ", lib_obj.physical_unit
	print "		logical_unit:  ", lib_obj.logical_unit
	print "		srfname:       ", lib_obj.srfname
	print "		ACLs:          ", lib_obj.acls
	print "		reflibs:       ", lib_obj.reflibs
	print "		fonts:         ", lib_obj.fonts
	print "		attrtable:     ", lib_obj.attrtable
	print "		format:        ", lib_obj.format
	print "		masks:         ", lib_obj.masks
	print

def debug_print_path_obj(path_obj):
	print "Path Object:"
	print "		layer:      ", path_obj.layer
	print "		data_type:  ", path_obj.data_type
	print "		XY:         ", path_obj.xy
	if hasattr(path_obj, 'elflags'):
		print "		elflags:    ", path_obj.elflags
	if hasattr(path_obj, 'plex'):
		print "		plex:       ", path_obj.plex
	if hasattr(path_obj, 'path_type'):
		print "		path_type:  ", path_obj.path_type
	if hasattr(path_obj, 'width'):
		print "		width:      ", path_obj.width
	if hasattr(path_obj, 'bgn_extn'):
		print "		bgn_extn:   ", path_obj.bgn_extn
	if hasattr(path_obj, 'end_extn'):
		print "		end_extn:   ", path_obj.end_extn
	if hasattr(path_obj, 'properties'):
		print "		properties: ", path_obj.properties
	print

def main():
	# Load critical nets
	critical_nets = load_critical_nets('graphs/MAL_TOP_par.supv_2.dot')

	# Load circuit paths
	circuit_paths = load_circuit_paths('gds/MAL_TOP.all.netname.gds')

	# Extract critical circuit paths
	critical_paths = extract_critical_paths(circuit_paths, critical_nets)

	# Analyze security critical paths in GDSII
	analyze_critical_paths(critical_paths)

if __name__ == "__main__":
    main()




