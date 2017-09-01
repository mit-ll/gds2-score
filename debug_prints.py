# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Other Imports
import pprint

def debug_print_lib_obj(lib_obj):
	print "Lib Object:"
	print "	version:       ", lib_obj.version
	print "	name:          ", lib_obj.name
	print "	physical_unit: ", lib_obj.physical_unit
	print "	logical_unit:  ", lib_obj.logical_unit
	print "	srfname:       ", lib_obj.srfname
	print "	ACLs:          ", lib_obj.acls
	print "	reflibs:       ", lib_obj.reflibs
	print "	fonts:         ", lib_obj.fonts
	print "	attrtable:     ", lib_obj.attrtable
	print "	format:        ", lib_obj.format
	print "	masks:         ", lib_obj.masks
	print

def debug_print_gdsii_structure(structure_obj):
	print "Structure Object:"
	print "	name:     ", structure_obj.name
	print "	mod_time: ", structure_obj.mod_time
	print "	acc_time: ", structure_obj.acc_time
	print "	strclass: ", structure_obj.strclass
	print

def debug_print_path_obj(path_obj):
	print "Path Object:"
	print "	layer:      ", path_obj.layer
	print "	data_type:  ", path_obj.data_type
	print "	XY:         ", path_obj.xy
	print "	elflags:    ", path_obj.elflags
	print "	plex:       ", path_obj.plex
	print "	path_type:  ", path_obj.path_type
	print "	width:      ", path_obj.width
	print "	bgn_extn:   ", path_obj.bgn_extn
	print "	end_extn:   ", path_obj.end_extn
	print "	properties: ", path_obj.properties
	print

def debug_print_boundary_obj(boundary_obj):
	print "Boundary Object:"
	print "	layer:      ", boundary_obj.layer
	print "	data_type:  ", boundary_obj.data_type
	print "	XY:         ", boundary_obj.xy
	print "	elflags:    ", boundary_obj.elflags
	print "	plex:       ", boundary_obj.plex
	print "	properties: ", boundary_obj.properties
	print

def debug_print_box_obj(box_obj):
	print "Box Object:"
	print "	layer:      ", box_obj.layer
	print "	box_type:   ", box_obj.box_type
	print "	XY:         ", box_obj.xy
	print "	elflags:    ", box_obj.elflags
	print "	plex:       ", box_obj.plex
	print "	properties: ", box_obj.properties
	print

def debug_print_node_obj(node_obj):
	print "Node Object:"
	print "	layer:      ", node_obj.layer
	print "	node_type:  ", node_obj.node_type
	print "	XY:         ", node_obj.xy
	print "	elflags:    ", node_obj.elflags
	print "	plex:       ", node_obj.plex
	print "	properties: ", node_obj.properties
	print

def debug_print_sref_obj(sref_obj):
	print "SRef Object:"
	print "	struct_name: ", sref_obj.struct_name
	print "	XY:          ", sref_obj.xy
	print "	elflags:     ", sref_obj.elflags
	print "	strans:      ", sref_obj.strans
	print "	mag:         ", sref_obj.mag
	print "	angle:       ", sref_obj.angle
	print "	properties:  ", sref_obj.properties
	print

def debug_print_aref_obj(aref_obj):
	print "ARef Object:"
	print "	struct_name: ", aref_obj.struct_name
	print "	cols:        ", aref_obj.cols
	print "	rows:        ", aref_obj.rows
	print "	XY:          ", aref_obj.xy
	print "	elflags:     ", aref_obj.elflags
	print "	plex:        ", aref_obj.plex
	print "	strans:      ", aref_obj.strans
	print "	mag:         ", aref_obj.mag
	print "	angle:       ", aref_obj.angle
	print "	properties:  ", aref_obj.properties
	print

def debug_print_text_obj(text_obj):
	print "Text Object:"
	print "	layer:        ", text_obj.layer
	print "	text_type:    ", text_obj.text_type
	print "	XY:           ", text_obj.xy
	print "	string:       ", text_obj.string
	print "	elflags:      ", text_obj.elflags
	print "	plex:         ", text_obj.plex
	print "	presentation: ", text_obj.presentation
	print "	path_type:    ", text_obj.path_type
	print "	width:        ", text_obj.width
	print "	strans:       ", text_obj.strans
	print "	mag:          ", text_obj.mag
	print "	angle:        ", text_obj.angle 
	print "	properties:   ", text_obj.properties
	print

def debug_print_gdsii_stats(gdsii_lib):
	# Compute number/type of elements in GDSII
	# Structures
	num_structures  = 0
	# Elements
	num_paths 	    = 0
	num_boundaries  = 0
 	num_nodes 	    = 0
	num_boxes 	    = 0
	num_srefs 	    = 0
	num_arefs 	    = 0
	num_texts 	    = 0
	path_coords     = {}
	boundary_coords = {}
	for structure in gdsii_lib:
		num_structures += 1
		for element in structure:
			if isinstance(element, Path):
				num_paths += 1
				if len(element.xy) not in path_coords:
					path_coords[len(element.xy)] = 1
				else:
					path_coords[len(element.xy)] += 1
			elif isinstance(element, Boundary):
				num_boundaries += 1
				if len(element.xy) not in boundary_coords:
					boundary_coords[len(element.xy)] = 1
				else:
					boundary_coords[len(element.xy)] += 1
			elif isinstance(element, Box):
				num_boxes += 1
			elif isinstance(element, Node):
				num_nodes += 1
			elif isinstance(element, SRef):
				num_srefs += 1
			elif isinstance(element, ARef):
				num_arefs += 1
			elif isinstance(element, Text):
				num_texts += 1

	# Print stats
	print "GDSII Stats:"
	print "---------------------"
	print " Structures: ", num_structures
	print "---------------------"
	print " Paths:      ", num_paths
	print " Boundaries: ", num_boundaries
	print " Boxes:      ", num_boxes
	print " Nodes:      ", num_nodes
	print " SRefs:      ", num_srefs
	print " ARefs:      ", num_arefs
	print " Texts:      ", num_texts
	print
	# print "Path Coords:"
	# print "---------------------"
	# pprint.pprint(path_coords)
	# print
	# print "Boundary Coords:"
	# print "---------------------"
	# pprint.pprint(boundary_coords)
	# print

def debug_print_gdsii_sref_strans_stats(gdsii_lib):
	# Compute number/type of elements in GDSII
	strans_vals = {}
	for structure in gdsii_lib:
		for element in structure:
			if isinstance(element, SRef):
				if element.strans != 0 and element.strans != None:
					print "---------------------"
					debug_print_gdsii_structure(structure)
					debug_print_sref_obj(element)
					print "---------------------"
				if element.strans == None:
					if "None" in strans_vals:
						strans_vals["None"] += 1
					else:
						strans_vals["None"] = 1
				else:
					if bin(element.strans) in strans_vals:
						strans_vals[bin(element.strans)] += 1
					else:
						strans_vals[bin(element.strans)] = 1
	print "SRef.strans Stats:"
	pprint.pprint(strans_vals)
	print 

def debug_print_gdsii_aref_strans_stats(gdsii_lib):
	# Compute number/type of elements in GDSII
	strans_vals = {}
	for structure in gdsii_lib:
		for element in structure:
			if isinstance(element, ARef):
				if element.strans != 0 and element.strans != None:
					print "---------------------"
					debug_print_gdsii_structure(structure)
					debug_print_aref_obj(element)
					print "---------------------"
				if element.strans == None:
					if "None" in strans_vals:
						strans_vals["None"] += 1
					else:
						strans_vals["None"] = 1
				else:
					if bin(element.strans) in strans_vals:
						strans_vals[bin(element.strans)] += 1
					else:
						strans_vals[bin(element.strans)] = 1
	print "ARef.strans Stats:"
	pprint.pprint(strans_vals)
	print 

def debug_print_gdsii_hierarchy(gdsii_lib):
	print "GDSII Hierarchy:"
	for structure in gdsii_lib:
		print "Structure: ", structure.name
		for element in structure:
			if isinstance(element, Path):
				print "	Path"
			elif isinstance(element, Boundary):
				print "	Boundary"
			elif isinstance(element, Box):
				print "	Box"
			elif isinstance(element, Node):
				print "	Node"
			elif isinstance(element, SRef):
				print "	SRef"
			elif isinstance(element, ARef):
				print "	ARef"
			elif isinstance(element, Text):
				print "	Text"

def debug_print_gdsii_element(element):
	if isinstance(element, Path):
		debug_print_path_obj(element)
	elif isinstance(element, Boundary):
		debug_print_boundary_obj(element)
	elif isinstance(element, Box):
		debug_print_box_obj(element)
	elif isinstance(element, Node):
		debug_print_node_obj(element)
	elif isinstance(element, SRef):
		debug_print_sref_obj(element)
	elif isinstance(element, ARef):
		debug_print_aref_obj(element)
	elif isinstance(element, Text):
		debug_print_text_obj(element)

def debug_print_gdsii_structure_and_elements(structure_obj):
	debug_print_gdsii_structure(structure_obj)
	for element in structure_obj:
		debug_print_gdsii_element(element)
