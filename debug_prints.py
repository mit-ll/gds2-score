# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Import matplotlib
import matplotlib.pyplot as plt

# Import custom modules
from polygon import *

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
	max_boundary    = None
	min_boundary    = None
	for structure in gdsii_lib:
		num_structures += 1
		for element in structure:
			if isinstance(element, Path):
				num_paths += 1
				# if len(element.xy) not in path_coords:
				# 	path_coords[len(element.xy)] = 1
				# else:
				# 	path_coords[len(element.xy)] += 1
			elif isinstance(element, Boundary):
				num_boundaries += 1
				# if len(element.xy) not in boundary_coords:
				# 	boundary_coords[len(element.xy)] = 1
				# else:
				# 	boundary_coords[len(element.xy)] += 1
				# # Update Max Coord Boundary
				# if max_boundary == None:
				# 	max_boundary = element
				# elif sorted(element.xy, key=lambda x:(x[0], x[1]))[-1] > sorted(max_boundary.xy, key=lambda x:(x[0], x[1]))[-1]:
				# 	max_boundary = element
				# # Update Min Coord Boundary
				# if min_boundary == None:
				# 	min_boundary = element
				# elif sorted(element.xy, key=lambda x:(x[0], x[1]))[0] < sorted(min_boundary.xy, key=lambda x:(x[0], x[1]))[0]:
				# 	min_boundary = element
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
	# print "Max Boundary:"
	# print "---------------------"
	# debug_print_boundary_obj(max_boundary)
	# print
	# print "Min Boundary:"
	# print "---------------------"
	# debug_print_boundary_obj(min_boundary)
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

def debug_print_wa_graph(wa_graph):
	# Print Polygon Edges
	print "Polygon Edges:"
	for point in wa_graph.keys():
		point.print_coords()
		print ":",
		for connection_point in wa_graph[point][0]:
			print "-->", 
			connection_point.print_coords()
		print
	print 

	# Print Polygon Clip Edges
	print "Polygon Clip Edges:"
	for point in wa_graph.keys():
		point.print_coords()
		print ":",
		for connection_point in wa_graph[point][1]:
			print "-->", 
			connection_point.print_coords()
		print
	print

def debug_polygon_edge_generator(poly):
	for edge in poly.edges():
		edge.print_segment()

def debug_print_wa_outgoing_points(outgoing_points):
	print "Outgoing Points: "
	debug_print_points(outgoing_points)
	print 

def debug_print_wa_incoming_points(incoming_points):
	print "Incoming Points: "
	debug_print_points(incoming_points)
	print 

def debug_print_points(points):
	for point in points:
		point.print_coords()
		print

def debug_weiler_atherton_algorithm():
	# Create polygon 1
	r1 = Point(0, 0)
	r2 = Point(4, 0)
	r3 = Point(4, 4)
	r4 = Point(0, 4)
	poly_1 = Polygon([r1, r2, r3, r4, r1])

	# Create polygon 2
	p1 = Point(1, -2)
	p2 = Point(5, -2)
	p3 = Point(5, 5)
	p4 = Point(1, 5)
	p5 = Point(1, 3)
	p6 = Point(2, 3)
	p7 = Point(2, 2)
	p8 = Point(1, 2)
	poly_2 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, p1])

	# Create polygon 3 from clipping 2 with 1
	poly_3 = Polygon.from_polygon_clip(poly_2, poly_1)[0]

	# # Plot both polygons
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_2.get_x_coords(), poly_2.get_y_coords())
	# plt.plot(poly_3.get_x_coords(), poly_3.get_y_coords())
	# plt.grid()
	# plt.show()

	# Create polygon 4
	p1 = Point(-1, 1)
	p2 = Point(1, 1)
	p3 = Point(2, -1)
	p4 = Point(3, 1)
	p5 = Point(3, 3)
	p6 = Point(2, 5)
	p7 = Point(-1, 3)
	poly_4 = Polygon([p1, p2, p3, p4, p5, p6, p7, p1])

	# Create polygon 5 from clipping 4 with 1
	poly_5 = Polygon.from_polygon_clip(poly_4, poly_1)[0]

	# # Plot both polygons
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_4.get_x_coords(), poly_4.get_y_coords())
	# plt.plot(poly_5.get_x_coords(), poly_5.get_y_coords())
	# plt.grid()
	# plt.show()

	# Create polygon 6
	p1 = Point(1, -2)
	p2 = Point(3, -2)
	p3 = Point(3, 1)
	p4 = Point(6, 1)
	p5 = Point(6, 5)
	p6 = Point(1, 5)
	poly_6 = Polygon([p1, p2, p3, p4, p5, p6, p1])

	# Create polygon 7 from clipping 6 with 1
	poly_7 = Polygon.from_polygon_clip(poly_6, poly_1)[0]

	# # Plot both polygons
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_6.get_x_coords(), poly_6.get_y_coords())
	# plt.plot(poly_7.get_x_coords(), poly_7.get_y_coords())
	# plt.grid()
	# plt.show()

	# Create polygon 8
	p1 = Point(-1, 1)
	p2 = Point(1, 1)
	p3 = Point(2, 0)
	p4 = Point(3, 1)
	p5 = Point(5, 1)
	p6 = Point(5, 3)
	p7 = Point(3, 3)
	p8 = Point(1, 5)
	p9 = Point(-1, 3)
	poly_8 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, p9, p1])

	# Create polygon 9 from clipping 8 with 1
	poly_9 = Polygon.from_polygon_clip(poly_8, poly_1)[0]

	# Plot both polygons
	plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	plt.plot(poly_8.get_x_coords(), poly_8.get_y_coords())
	plt.plot(poly_9.get_x_coords(), poly_9.get_y_coords())
	plt.grid()
	plt.show()

