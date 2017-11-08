# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Import matplotlib
# import matplotlib.pyplot as plt

# Import custom modules
from polygon import *
from trigger_space import *

# Other Imports
import time
import pprint
import copy
import numpy

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

def get_num_element_coords_floats(element):
	num_float_coords = 0
	num_int_coords   = 0
	for coord in element.xy:
		if isinstance(coord[0], int) and isinstance(coord[1], int):
			num_int_coords += 1
		elif isinstance(coord[0], float) and isinstance(coord[1], float):
			num_float_coords += 1
		elif isinstance(coord[0], int) and isinstance(coord[1], float) or isinstance(coord[0], float) and isinstance(coord[1], int):
			print "PARTIAL",
			print coord
			num_int_coords   += 1
			num_float_coords += 1
		else:
			print "UNKOWN COORD TYPE",
			print coord

	if num_float_coords > 0:
		print element.xy
	return num_int_coords, num_float_coords

def debug_print_gdsii_stats(gdsii_lib):
	# Compute number/type of elements in GDSII
	# Structures
	num_structures   = 0
	# Elements
	num_paths 	     = 0
	num_boundaries   = 0
 	num_nodes 	     = 0
	num_boxes 	     = 0
	num_srefs 	     = 0
	num_arefs 	     = 0
	num_texts 	     = 0
	path_coords      = {}
	boundary_coords  = {}
	max_boundary     = None
	min_boundary     = None
	num_float_coords = 0
	num_int_coords   = 0
	for structure in gdsii_lib:
		num_structures += 1
		for element in structure:
			if isinstance(element, Path):
				num_paths += 1
				# coord_type_counts = get_num_element_coords_floats(element)
				# num_int_coords    += coord_type_counts[0]
				# num_float_coords  += coord_type_counts[1]
				# if len(element.xy) not in path_coords:
				# 	path_coords[len(element.xy)] = 1
				# else:
				# 	path_coords[len(element.xy)] += 1
			elif isinstance(element, Boundary):
				num_boundaries += 1
				# coord_type_counts = get_num_element_coords_floats(element)
				# num_int_coords    += coord_type_counts[0]
				# num_float_coords  += coord_type_counts[1]
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
				# coord_type_counts = get_num_element_coords_floats(element)
				# num_int_coords    += coord_type_counts[0]
				# num_float_coords  += coord_type_counts[1]
			elif isinstance(element, ARef):
				num_arefs += 1
				# coord_type_counts = get_num_element_coords_floats(element)
				# num_int_coords    += coord_type_counts[0]
				# num_float_coords  += coord_type_counts[1]
			elif isinstance(element, Text):
				num_texts += 1
				# coord_type_counts = get_num_element_coords_floats(element)
				# num_int_coords    += coord_type_counts[0]
				# num_float_coords  += coord_type_counts[1]

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
	# print "---------------------"
	# print "Number of Int Coords:  ", num_int_coords
	# print "Number of Float Coords:", num_float_coords
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
		print "Key:", point, " = ",
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
		print "Key:", point, " = ",
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

def debug_polygon_vertical_edge_generator(poly):
	for v_edge in poly.vertical_edges():
		v_edge.print_segment()

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

def debug_plot_polygons(polys):
	plt.figure(1)
	for poly in polys:
		poly.plot()
	plt.grid()
	plt.show()

def debug_plot_x_reflected_polygons(polys):
	plt.figure(1)
	for poly in polys:
		poly.reflect_across_x_axis()
		poly.plot()
	plt.grid()
	plt.show()

def debug_polygon_translations():
	# Create polygon 1
	r1 = Point(0, 0)
	r2 = Point(4, 0)
	r3 = Point(4, 4)
	r4 = Point(0, 4)
	poly_1 = Polygon([r1, r2, r3, r4, copy.deepcopy(r1)])

	# Create polygon 2
	p1 = Point(1, -2)
	p2 = Point(5, -2)
	p3 = Point(5, 5)
	p4 = Point(1, 5)
	p5 = Point(1, 3)
	p6 = Point(2, 3)
	p7 = Point(2, 2)
	p8 = Point(1, 2)
	poly_2 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, copy.deepcopy(p1)])

	# Plot both polygons
	plt.figure(1)
	plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	plt.plot(poly_2.get_x_coords(), poly_2.get_y_coords())

	# Reflect accross X-Axis
	before_x_coords = poly_2.get_x_coords()
	before_y_coords = poly_2.get_y_coords()
	poly_2.compute_translations(0, 0, 32768, 0)
	after_x_coords = poly_2.get_x_coords()
	after_y_coords = poly_2.get_y_coords()

	print "Before X-Coords:", before_x_coords
	print "After  X-Coords:", after_x_coords
	print
	print "Before Y-Coords:", before_y_coords
	print "After  Y-Coords:", after_y_coords

	# Replot
	plt.plot(poly_2.get_x_coords(), poly_2.get_y_coords())

	# Rotate 90 degrees CCW
	before_x_coords = poly_2.get_x_coords()
	before_y_coords = poly_2.get_y_coords()
	poly_2.compute_translations(0, 0, 0, 90)
	after_x_coords = poly_2.get_x_coords()
	after_y_coords = poly_2.get_y_coords()

	print "Before X-Coords:", before_x_coords
	print "After  X-Coords:", after_x_coords
	print
	print "Before Y-Coords:", before_y_coords
	print "After  Y-Coords:", after_y_coords

	# Replot
	plt.plot(poly_2.get_x_coords(), poly_2.get_y_coords())
	plt.grid()
	plt.show()

def debug_generate_polys():
	# Create polygon 1
	r1 = Point(0, 0)
	r2 = Point(4, 0)
	r3 = Point(4, 4)
	r4 = Point(0, 4)
	poly_1 = Polygon([r1, r2, r3, r4, copy.deepcopy(r1)])

	# Create polygon 2
	p1 = Point(10, 14)
	p2 = Point(16, 14)
	p3 = Point(16, 20)
	p4 = Point(14, 20)
	p5 = Point(14, 22)
	p6 = Point(16, 22)
	p7 = Point(16, 24)
	p8 = Point(10, 24)
	poly_2 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, copy.deepcopy(p1)])

	# Create polygon 3
	q1 = Point(0, 14)
	q2 = Point(6, 14)
	q3 = Point(6, 20)
	q4 = Point(8, 20)
	q5 = Point(8, 22)
	q6 = Point(6, 22)
	q7 = Point(6, 24)
	q8 = Point(0, 24)
	poly_3 = Polygon([q1, q2, q3, q4, q5, q6, q7, q8, copy.deepcopy(q1)])
	poly_3.compute_translations(50, 20, None, 90)
	
	return [poly_1, poly_2, poly_3]

def debug_weiler_atherton_algorithm():
	# # Create polygon 1
	# r1 = Point(0, 0)
	# r2 = Point(4, 0)
	# r3 = Point(4, 4)
	# r4 = Point(0, 4)
	# poly_1 = Polygon([r1, r2, r3, r4, r1])

	# # Create polygon 2
	# p1 = Point(1, -2)
	# p2 = Point(5, -2)
	# p3 = Point(5, 5)
	# p4 = Point(1, 5)
	# p5 = Point(1, 3)
	# p6 = Point(2, 3)
	# p7 = Point(2, 2)
	# p8 = Point(1, 2)
	# poly_2 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, p1])

	# # Create polygon 3 from clipping 2 with 1
	# poly_3 = Polygon.from_polygon_clip(poly_2, poly_1)[0]

	# # Plot both polygons
	# plt.figure(1)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_2.get_x_coords(), poly_2.get_y_coords())
	# plt.plot(poly_3.get_x_coords(), poly_3.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Create polygon 4
	# p1 = Point(-1, 1)
	# p2 = Point(1, 1)
	# p3 = Point(2, -1)
	# p4 = Point(3, 1)
	# p5 = Point(3, 3)
	# p6 = Point(2, 5)
	# p7 = Point(-1, 3)
	# poly_4 = Polygon([p1, p2, p3, p4, p5, p6, p7, p1])

	# # Create polygon 5 from clipping 4 with 1
	# poly_5 = Polygon.from_polygon_clip(poly_4, poly_1)[0]

	# # Plot both polygons
	# plt.figure(2)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_4.get_x_coords(), poly_4.get_y_coords())
	# plt.plot(poly_5.get_x_coords(), poly_5.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Create polygon 6
	# p1 = Point(1, -2)
	# p2 = Point(3, -2)
	# p3 = Point(3, 1)
	# p4 = Point(6, 1)
	# p5 = Point(6, 5)
	# p6 = Point(1, 5)
	# poly_6 = Polygon([p1, p2, p3, p4, p5, p6, p1])

	# # Create polygon 7 from clipping 6 with 1
	# poly_7 = Polygon.from_polygon_clip(poly_6, poly_1)[0]

	# # Plot both polygons
	# plt.figure(3)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_6.get_x_coords(), poly_6.get_y_coords())
	# plt.plot(poly_7.get_x_coords(), poly_7.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Create polygon 8
	# p1 = Point(-1, 1)
	# p2 = Point(1, 1)
	# p3 = Point(2, 0)
	# p4 = Point(3, 1)
	# p5 = Point(5, 1)
	# p6 = Point(5, 3)
	# p7 = Point(3, 3)
	# p8 = Point(1, 5)
	# p9 = Point(-1, 3)
	# poly_8 = Polygon([p1, p2, p3, p4, p5, p6, p7, p8, p9, p1])

	# # Create polygon 9 from clipping 8 with 1
	# poly_9 = Polygon.from_polygon_clip(poly_8, poly_1)[0]

	# # Plot both polygons
	# plt.figure(4)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_8.get_x_coords(), poly_8.get_y_coords())
	# plt.plot(poly_9.get_x_coords(), poly_9.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Create polygon 10
	# p1 = Point(0, 3)
	# p2 = Point(4, 3)
	# p3 = Point(4, 5)
	# p4 = Point(0, 5)
	# poly_10 = Polygon([p1, p2, p3, p4, p1])

	# # Create polygon 11 from clipping 10 with 1
	# poly_11 = Polygon.from_polygon_clip(poly_10, poly_1)[0]

	# # Plot both polygons
	# plt.figure(5)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_10.get_x_coords(), poly_10.get_y_coords())
	# plt.plot(poly_11.get_x_coords(), poly_11.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Polygons below does not overlap clip ploygon
	# # Create polygon 12
	# p1 = Point(5, 0)
	# p2 = Point(9, 0)
	# p3 = Point(9, 4)
	# p4 = Point(5, 4)
	# poly_12 = Polygon([p1, p2, p3, p4, p1])

	# # Try to create a polygon from clipping 12 with 1
	# assert len(Polygon.from_polygon_clip(poly_12, poly_1)) == 0

	# # Plot both polygons
	# plt.figure(6)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_12.get_x_coords(), poly_12.get_y_coords())
	# plt.grid()
	# plt.show()

	# # Polygons below is completely contained inside the clip polygon
	# # Create polygon 13
	# p1 = Point(1, 1)
	# p2 = Point(3, 1)
	# p3 = Point(3, 3)
	# p4 = Point(1, 3)
	# poly_13 = Polygon([p1, p2, p3, p4, p1])

	# # Try to create a polygon from clipping 13 with 1
	# poly_14 = Polygon.from_polygon_clip(poly_13, poly_1)[0]

	# # Plot both polygons
	# plt.figure(7)
	# plt.plot(poly_1.get_x_coords(), poly_1.get_y_coords())
	# plt.plot(poly_13.get_x_coords(), poly_13.get_y_coords())
	# plt.plot(poly_14.get_x_coords(), poly_14.get_y_coords())
	# plt.grid()
	# plt.show()

	# Polygons clip are same length and overlap
	# Create polygon 15
	p1 = Point(535150.00, 539070.00)
	p2 = Point(535290.00, 539070.00)
	p3 = Point(535290.00, 545090.00)
	p4 = Point(535150.00, 545090.00)
	poly_15 = Polygon([p1, p2, p3, p4, p1])

	# Create polygon 16
	p1 = Point(535150.00, 544950.00)
	p2 = Point(535290.00, 544950.00)
	p3 = Point(535290.00, 545370.00)
	p4 = Point(535150.00, 545370.00)
	poly_16 = Polygon([p1, p2, p3, p4, p1])

	# Try to create a polygon from clipping 15 with 16
	poly_17 = Polygon.from_polygon_clip(poly_15, poly_16)[0]

	# Plot both polygons
	plt.figure(8)
	plt.plot(poly_15.get_x_coords(), poly_15.get_y_coords())
	plt.plot(poly_16.get_x_coords(), poly_16.get_y_coords())
	plt.plot(poly_17.get_x_coords(), poly_17.get_y_coords())
	plt.grid()
	plt.show()

def debug_trigger_space_metric():
	start_time = time.time()
	print "Starting Trigger Space Analysis:"
	analyze_open_space_for_triggers()
	print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
	print "----------------------------------------------"
	return

def debug_create_bitmap(rows, cols):
	return numpy.random.choice([0, 1], size=(rows, cols), p=[1./2, 1./2])

def debug_print_square_trace_step(device_layer_bitmap, current_point, orientation, connected_points):
	temp_bitmap = copy.deepcopy(device_layer_bitmap)
	temp_bitmap[current_point.y, current_point.x] = 8

	# print bitmap
	print "Current Point:",
	current_point.print_coords()
	print orientation
	print "Num Connected Points:", len(connected_points)
	for i in reversed(range(device_layer_bitmap.shape[0])):
		print temp_bitmap[i], "	", device_layer_bitmap[i]
	print

	# Hit any key to continue
	x = raw_input()

def debug_print_lef_std_cells(lef_info):
	print "Standard Cells:"
	for std_cell_name in lef_info.standard_cells:
		lef_info.standard_cells[std_cell_name].debug_print_attrs()
		# print "	# Sites High: %f" % (lef_info.standard_cells[std_cell_name].height / lef_info.placement_sites.values()[0].dimension.y)
		# print "	# Sites Wide: %f" % (lef_info.standard_cells[std_cell_name].width / lef_info.placement_sites.values()[0].dimension.x)
	print

def debug_print_lef_placement_sites(lef_info):
	print "Placement Sites:"
	for place_site_name in lef_info.placement_sites:
		lef_info.placement_sites[place_site_name].debug_print_attrs()
	print

def debug_plot_bitmap(placement_grid):
	plt.imshow(placement_grid)
	plt.grid()
	plt.show()

def debug_plot_bitmap_scaled(placement_grid):
	adjusted_aspect_ratio = (float(placement_grid.shape[1]) / float(placement_grid.shape[0]))
	plt.imshow(placement_grid)
	plt.axes().set_aspect(adjusted_aspect_ratio)
	plt.grid()
	plt.show()

