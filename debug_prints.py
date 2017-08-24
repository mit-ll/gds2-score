# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

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
	num_structures = 0
	# Elements
	num_paths 	   = 0
	num_boundaries = 0
 	num_nodes 	   = 0
	num_boxes 	   = 0
	num_srefs 	   = 0
	num_arefs 	   = 0
	num_texts 	   = 0
	for structure in gdsii_lib:
		num_structures += 1
		for element in structure:
			if isinstance(element, Path):
				num_paths += 1
			elif isinstance(element, Boundary):
				num_boundaries += 1
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


