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
	print "		elflags:    ", path_obj.elflags
	print "		plex:       ", path_obj.plex
	print "		path_type:  ", path_obj.path_type
	print "		width:      ", path_obj.width
	print "		bgn_extn:   ", path_obj.bgn_extn
	print "		end_extn:   ", path_obj.end_extn
	print "		properties: ", path_obj.properties
	print

def debug_print_boundary_obj(boundary_obj):
	print "Boundary Object:"
	print "		layer:      ", boundary_obj.layer
	print "		data_type:  ", boundary_obj.data_type
	print "		XY:         ", boundary_obj.xy
	print "		elflags:    ", boundary_obj.elflags
	print "		plex:       ", boundary_obj.plex
	print "		properties: ", boundary_obj.properties
	print

# def debug_print_layer_map(layer_map):
# 	print "Layer Map:"
# 	for layer_num in 