# ------------------------------------------------------------------
# Trigger Space Metric - Legacy Code
# ------------------------------------------------------------------
# Import BitArray2D 
# import BitArray2D
# from BitArray2D import godel
import numpy

# numpy.set_printoptions(threshold=numpy.inf)

# Used to load device layer bitmap by only analyzing the GDSII layout info
def load_device_layer_bitmap(layout):
	device_layer_bitmap = numpy.zeros(shape=(layout.def_info.num_placement_rows, layout.def_info.num_placement_cols))

	# Loop through the placement sites
	placement_site      = layout.lef.placement_sites[layout.def_info.placement_rows[0].site_name]
	placement_grid_bbox = layout.def_info.placement_grid_bbox

	for device_layer_polys in layout.generate_device_layer_polys():
		# Constrain search region on placement grid
		if device_layer_polys:
			search_region = BBox.from_multiple_polygons(device_layer_polys)
			# print "Search Region: %s" % (search_region.get_bbox_as_list())
			# print "Placement Site Dimensions: X = %d, Y = %d" % (placement_site.dimension.x, placement_site.dimension.y)
			# print "Search Region 1: %s; Placement Grid: %s" % (search_region.get_bbox_as_list(), placement_grid_bbox.get_bbox_as_list())
			if placement_grid_bbox.overlaps_bbox(search_region):
				search_region_ll_x_extended = search_region.ll.x - (search_region.ll.x % placement_site.dimension.x)
				search_region_ll_y_extended = search_region.ll.y - (search_region.ll.y % placement_site.dimension.y)
				search_region_ur_x_extended = search_region.ur.x + (placement_site.dimension.x - (search_region.ur.x % placement_site.dimension.x))
				search_region_ur_y_extended = search_region.ur.y + (placement_site.dimension.y - (search_region.ur.y % placement_site.dimension.y))
				search_region.ll.x = int(((max(placement_grid_bbox.ll.x, search_region_ll_x_extended) - placement_grid_bbox.ll.x) / placement_site.dimension.x) - 1)
				search_region.ll.y = int(((max(placement_grid_bbox.ll.y, search_region_ll_y_extended) - placement_grid_bbox.ll.y) / placement_site.dimension.y) - 1)
				search_region.ur.x = int((min(placement_grid_bbox.ur.x,  search_region_ur_x_extended) - placement_grid_bbox.ll.x) / placement_site.dimension.x)
				search_region.ur.y = int((min(placement_grid_bbox.ur.y,  search_region_ur_y_extended) - placement_grid_bbox.ll.y) / placement_site.dimension.y)
				# print "Search Region 2: %s; Placement Grid: %s" % (search_region.get_bbox_as_list(), placement_grid_bbox.get_bbox_as_list())

				# Set current placement site bbox
				current_site_ll   = Point.from_point_and_offset(layout.def_info.placement_rows[search_region.ll.y].origin, placement_site.dimension.x * search_region.ll.x, 0)
				current_site_ur   = Point.from_point_and_offset(current_site_ll, placement_site.dimension.x, placement_site.dimension.y)
				current_site_bbox = BBox(current_site_ll, current_site_ur)
				for poly in device_layer_polys:
					for row in range(search_region.ll.y, search_region.ur.y):
						for col in range(search_region.ll.x, search_region.ur.x):
							if poly.overlaps_bbox(current_site_bbox):
								device_layer_bitmap[row, col] = 1
							current_site_bbox.ll.x += placement_site.dimension.x
							current_site_bbox.ur.x += placement_site.dimension.x
						# Update Current Site BBox
						current_site_bbox.ll.y += placement_site.dimension.y
						current_site_bbox.ur.y += placement_site.dimension.y
	numpy.save("device_layer_bitmap.npy", device_layer_bitmap)

	# for element in layout.top_gdsii_structure:
	# 	# @TODO: Ignore fill cells
	# 	polys = layout.generate_polys_from_element(element)
	# 	for poly in polys:
	# 		# Polygon coloring algorithm
	# 		color = False
	# 		for row in range(poly.bbox.ll.y, poly.bbox.ur.y):
	# 			for col in range(poly.bbox.ll.x, poly.bbox.ur.x + 1):
	# 				for v_edge in poly.vertical_edges():
	# 					temp_point = Point(col, row + 0.5)
	# 					if v_edge.on_segment(temp_point):
	# 						color = not color
	# 				if color:
	# 					device_layer_bitmap[row, col] = 1
	
	return device_layer_bitmap

# Used in Square Trace - Contour Tracing Algorithm
def get_contour_trace_start_point(device_layer_bitmap):
	num_rows = device_layer_bitmap.shape[0]
	num_cols = device_layer_bitmap.shape[1]

	for col in range(num_cols):
		for row in range(num_rows):
			if device_layer_bitmap[row, col] == 0:
				return Point(col, row)
	return None

# Used in Square Trace - Contour Tracing Algorithm
def square_trace_turn_left(current_point, orientation):
	if orientation == "N":
		current_point.x -= 1
		orientation = "W"
	elif orientation == "E":
		current_point.y += 1
		orientation = "N"
	elif orientation == "S":
		current_point.x += 1
		orientation = "E"
	elif orientation == "W":
		current_point.y -= 1
		orientation = "S"
	else:
		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
		sys.exit(1)

	return current_point, orientation

# Used in Square Trace - Contour Tracing Algorithm
def square_trace_turn_right(current_point, orientation):
	if orientation == "N":
		current_point.x += 1
		orientation = "E"
	elif orientation == "E":
		current_point.y -= 1
		orientation = "S"
	elif orientation == "S":
		current_point.x -= 1
		orientation = "W"
	elif orientation == "W":
		current_point.y += 1
		orientation = "N"
	else:
		print "ERROR %s: Unknown orientation %s." % (inspect.stack()[0][3], orientation)
		sys.exit(1)
		
	return current_point, orientation

# Square Tracing Algorithm
# This algorithm identifies regions of a bitmap
# that are 4-connected. I.e. places where trigger
# circuits could be potentially connected.
def square_trace(device_layer_bitmap):
	connected_points = set()
	num_rows         = device_layer_bitmap.shape[0]
	num_cols         = device_layer_bitmap.shape[1]
	bitmap_bbox      = BBox(Point(0,0), Point(num_rows - 1, num_cols - 1))
	start_point      = get_contour_trace_start_point(device_layer_bitmap)
	orientation      = "N"

	print "Num Rows:", num_rows
	print "Num Cols:", num_cols
	print
	print "Start Point = (R, C)", start_point.y, start_point.x
	print
	numpy.set_printoptions(threshold=numpy.inf)
	print device_layer_bitmap
	print
	print bitmap_bbox.get_bbox_as_list()
	print

	# Insert the start point in connected_points list and turn left
	current_point = copy.deepcopy(start_point)
	connected_points.add(copy.deepcopy(current_point))
	current_point, orientation = square_trace_turn_left(current_point, orientation)
	dbg.debug_print_square_trace_step(device_layer_bitmap, current_point, orientation, connected_points)

	while not (current_point == start_point and orientation == "N"):
		# If current point is colored, add to list and turn left
		print bitmap_bbox.is_point_inside_bbox(current_point), (device_layer_bitmap[current_point.y, current_point.x] == 1), device_layer_bitmap[current_point.y, current_point.x]
		if bitmap_bbox.is_point_inside_bbox(current_point) and device_layer_bitmap[current_point.y, current_point.x] == 1:
			print "adding current point"
			connected_points.add(copy.deepcopy(current_point))
			current_point, orientation = square_trace_turn_left(current_point, orientation)
		# Otherwise, turn right
		else:
			current_point, orientation = square_trace_turn_right(current_point, orientation)
		dbg.debug_print_square_trace_step(device_layer_bitmap, current_point, orientation, connected_points)

	# Print connected points
	print "Num Connected Points:", len(connected_points)
	print "Connected Points:"
	for point in list(connected_points):
		point.print_coords()
		print

	return connected_points

# ------------------------------------------------------------------
# Ray Casting Algorithm - Legacy Code
# ------------------------------------------------------------------
def ray_intersects_segment(self, x, y, point_1, point_2):
	# NOTE: Point 1 is MUST BE below Point 2 for this function to work
	if point_1.y > point_2.y:
		print "ERROR %s: point_1 must be below point_2." % (inspect.stack()[1][3])
		sys.exit(4)

	if y < point_1.y or y > point_2.y:
		return False
	elif x > max(point_1.x, point_2.x):
		return False
	else:
		if x < max(point_1.x, point_2.x):
			return True
		else:
			if point_1.x != point_2.x:
				slope_a = (point_2.y - point_1.y) / (point_2.x - point_1.x)
			else:
				slope_a = sys.float_info.max
			if point_1.x != x:
				slope_b = (y - point_1.y) / (x - point_1.x)
			else:
				slope_b = sys.float_info.max
			# Compare slopes (i.e. angles)
			if slope_b >= slope_a:
				return True
			else:
				return False

def is_point_a_vertext(self, x, y):
	for coord in self.coords:
		if x == coord.x and y == coord.y:
			return True
	return False

# Ray Casting Algorithm 
# @TODO Clean-up checking if point on an edge
def is_point_inside(self, x, y):
	# Check if the point lies on a vertex
	if self.is_point_a_vertext(x, y):
		return True

	# Check if the point lies on an edge
	for i in range(self.num_coords - 1):
		curr_line_seg = LineSegment(self.coords[i], self.coords[i + 1])
		if curr_line_seg.orientation_of_points(self.coords[i], Point(x, y), self.coords[i + 1]) == 0 and curr_line_seg.on_segment(Point (x, y)):
			return True

	# Check if point lies inside the polygon
	intersect_count = 0
	for i in range(self.num_coords - 1):
		if self.coords[i].y <= self.coords[i + 1].y:
			if self.ray_intersects_segment(x, y, self.coords[i], self.coords[i + 1]):
				intersect_count += 1
		else:
			if self.ray_intersects_segment(x, y, self.coords[i + 1], self.coords[i]):
				intersect_count += 1

	# If intersect_count is odd, return TRUE
	if intersect_count % 2 == 1:
		return True
	else:
		return False

				# # Apply the inclusion principle from set theory to calculate blockage
				# for i in range(1, len(overlapping_bot_polys) + 1):
				# 	for bot_poly_combo in itertools.combinations(overlapping_bot_polys, i):
				# 		# Calculate area of overlap between polys in poly combo
				# 		poly_combo_intersection_area = 0
				# 		if len(bot_poly_combo) == 1:
				# 			poly_combo_intersection_area = bot_poly_combo[0].get_area()
				# 		else:

						# for j in range(1, len(top_poly_combo)):
						# 	if not intersection_polys:
						# 		intersection_polys.extend(Polygon.from_polygon_clip(top_poly_combo[0], top_poly_combo[j])
						# 	else:
						# 		for intersection_poly in inintersection_polys:
						# 			intersection_polys.extend(Polygon.from_polygon_clip(intersection_poly, top_poly_combo[j])
							

						# 	poly_combo_intersection_area += top_poly_combo[0].
						# top_area_blocked += ((-1)**(len(poly_combo + 1))) * 

# ------------------------------------------------------------------
# Pickling/Unpickling an Object
# ------------------------------------------------------------------
import pickle

layout_file = open("layout.bin", "wb")
pickle.dump(layout, layout_file, -1)
layout_file.close()
return

print "Loading pickled layout object ..."
load_layout_start_time = time.time()
layout_file = open("layout.bin", "rb")
layout = pickle.load(layout_file)
layout_file.close()
print "Done - Time Elapsed:", (time.time() - load_layout_start_time), "seconds."
print "----------------------------------------------"

# ------------------------------------------------------------------
# Edit Distance Debug Code
# ------------------------------------------------------------------
print "Size:", trigger_spaces.size
print "Freq:", trigger_spaces.freq
print "net_segment_2_sites:"
pprint.pprint(trigger_spaces.net_segment_2_sites)

print len(trigger_spaces.net_segment_2_sites[net_segment])
print "Index:",              trigger_spaces.net_segment_2_sites[net_segment][i].spaces_index
print "Centers:",            trigger_spaces.net_segment_2_sites[net_segment][i].centers
print "Edit Distance:",      trigger_spaces.net_segment_2_sites[net_segment][i].edit_distances
print "Manhattan Distance:", trigger_spaces.net_segment_2_sites[net_segment][i].manhattan_distance
print [ ts.spaces_index for ts in trigger_spaces.net_segment_2_sites[net_segment] ]

print "	<route_distance>"
print "		Num Trigger Spaces:", len(trigger_spaces.spaces)
print "		Size:              ", trigger_spaces.size
print "		Freq:              ", trigger_spaces.freq

class TriggerSpaces():
	def __init__(self, size):
		self.size    = size # Number of 4-connected placement sites
		self.freq    = 0    # Frequency of same size trigger spaces
		self.spaces  = []   # List of sets of Point objects comprising a single trigger space
		self.net_segment_2_sites = {} # maps net segments to list of closest trigger space sites

class TriggerSpace():
	def __init__(self, i, coords, md):
		self.spaces_index       = i      # Index into parent object TriggerSpace.spaces_index list 
		self.centers            = coords # Coords of center of placement site (manufacturing units)
		self.edit_distances     = []
		self.manhattan_distance = md

class WireStats():
	def __init__(self, n_mean, n_stdv, c_mean, c_stdv):
		self.net_sigma        = n_mean
		self.net_mean         = n_stdv
		self.connection_sigma = c_mean
		self.connection_mean  = c_stdv

# ------------------------------------------------------------------
# Old (non-working) Weiler Atherton implementation
# ------------------------------------------------------------------
DEBUG_WA_ALGORITHM_POST_POLY = False
DEBUG_WA_ALGORITHM_POST_CLIP = False
# Returns list of polygon objects as a result of a clipping operation
@classmethod
def from_polygon_clip_old(cls, poly, clip_poly, print_polys=False):
	wa_graph, outgoing, incoming = cls.build_wa_graph_old(poly, clip_poly)

	new_polys = []
	
	# If no outgoing points --> check if subject polygon
	# is completely contained inside the clip polygon
	if not outgoing:
		contained_inside = True
		for vertex in poly.coords:
			if not clip_poly.is_point_inside(vertex):
				contained_inside = False
		if contained_inside:
			new_polys.append(poly)

	# Start at exit intersection, walk graph to create clipped polygon(s)
	while outgoing:
		walk_edge_index = 1
		start_vertex    = outgoing.pop()
		new_poly_coords = [start_vertex]

		# Construct polygon coords
		curr_vertex = wa_graph[start_vertex][walk_edge_index][0]
		iter_num = 1
		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "Interation", iter_num
			print "curr_vertex: ",
			curr_vertex.print_coords()
			print
			print "start_vertex: ",
			start_vertex.print_coords()
			print
			print
		while curr_vertex != start_vertex:
			# Add vertex to current polygon coords
			new_poly_coords.append(curr_vertex)

			# Change border being walked if needed
			if (curr_vertex in incoming and walk_edge_index == 1) or (curr_vertex in outgoing and walk_edge_index == 0):
				walk_edge_index = (walk_edge_index + 1) % 2
				
				# Remove from list of outgoing_vertices if needed
				if curr_vertex in outgoing:
					outgoing.remove(curr_vertex)
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "Removing vertex from outgoing:",
						curr_vertex.print_coords()
						print
						dbg.debug_print_wa_outgoing_points(outgoing)

			# Update current vertex
			curr_vertex = wa_graph[curr_vertex][walk_edge_index][0]
			iter_num += 1
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "Interation", iter_num
				print "curr_vertex: ",
				curr_vertex.print_coords()
				print
				print "start_vertex: ",
				start_vertex.print_coords()
				print
				print
		new_poly_coords.append(start_vertex)

		# Construct new polygon object
		new_polys.append(Polygon(new_poly_coords))

	return new_polys

@classmethod
def build_wa_graph_old(cls, poly, clip_poly):
	# Construct graph with three groups of vertices:
	# 1. polygon vertices
	# 2. clipping region
	# 3. intersection vertices

	wa_graph          = {}
	outgoing_vertices = set()
	incoming_vertices = set()

	# Add all poly and clip_poly nodes to graph
	for vertex in poly.coords:
		if vertex not in wa_graph:
			wa_graph[vertex] = [[], []]
	for vertex in clip_poly.coords:
		if vertex not in wa_graph:
			wa_graph[vertex] = [[], []]

	if DEBUG_WA_ALGORITHM_VERBOSE:
		print "Initiated wa_graph."
		dbg.debug_print_wa_graph(wa_graph)

	# Add edges between poly vertices and intersection points, 
	# keeping track of direction entering(False)/exiting(True) 
	# of intersection points with curr_location.
	inside_clip_region  = clip_poly.is_point_inside(poly.coords[0])
	intersection_points = set()
	for poly_edge in poly.edges():
		intersection_points.clear()
		current_point = poly_edge.p1
		
		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "Poly Edge: ", 
			poly_edge.print_segment()
		
		# Find intections between polygon edges and clip polygon edges
		for clip_edge in clip_poly.edges():
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "	Clip Edge: ", 
				clip_edge.print_segment()
			intersection = poly_edge.intersection(clip_edge)
			if intersection:
				if not poly_edge.is_endpoint(intersection):
					# Intersection does NOT lie on an endpoint of the polygon segment
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		FOUND INTS: ",
						intersection.print_coords()
						print
					intersection_points.add(intersection)
				elif poly_edge.is_endpoint(intersection):
					# Add intersection point to incoming/outgoing set(s)
					if inside_clip_region:
						if DEBUG_WA_ALGORITHM_VERBOSE:
							print "		POLY END - ADDED INT to OUTGOING"
						outgoing_vertices.add(intersection)
					else: 
						incoming_vertices.add(intersection)
						if DEBUG_WA_ALGORITHM_VERBOSE:
							print "		POLY END - ADDED INT to INCOMING"
					inside_clip_region = not inside_clip_region
		
		# Sort intersection points by distance from polgon segment start point.
		# Add the intersection point connections to the graph.
		sorted_intersection_points = sorted(intersection_points, key=lambda x:x.distance_from(poly_edge.p1))
		while sorted_intersection_points:
			intersection = sorted_intersection_points.pop(0)
			
			# Add intersection point to graph
			if intersection not in wa_graph:
				if DEBUG_WA_ALGORITHM_VERBOSE:
					print "	INT NOT FOUND IN WA_GRAPH: ",
					intersection.print_coords()
					print
				wa_graph[intersection] = [[], []]
				
				# Add intersection point to incoming/outgoing set(s)
				if inside_clip_region:
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		ADDED INT to OUTGOING"
					outgoing_vertices.add(intersection)
				else: 
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		ADDED INT to INCOMING"
				 	incoming_vertices.add(intersection)
				inside_clip_region = not inside_clip_region	
			
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "	ADD INTS: ",
				current_point.print_coords()
				print "-->",
				intersection.print_coords()
				print
			
			# Add edges to/from intersection point
			wa_graph[current_point][0].append(intersection)
			current_point = intersection
		
		# Delete list of sorted intersection points
		del sorted_intersection_points
		
		# Add edge connecting last intersection point to 
		# poly edge end-point to wa_graph.
		if current_point != poly_edge.p2:
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "	ADD ENDPOINT: ",
				current_point.print_coords() 
				print "-->",
				poly_edge.p2.print_coords()
				print
			wa_graph[current_point][0].append(poly_edge.p2)

	if DEBUG_WA_ALGORITHM_POST_POLY:
		print "Post Poly Edge Iteration:"
		dbg.debug_print_wa_graph(wa_graph)
		dbg.debug_print_wa_outgoing_points(outgoing_vertices)
		dbg.debug_print_wa_incoming_points(incoming_vertices)

	# Add all clip_poly vertices to graph.
	# Add edges between clip_poly vertices and intersection points
	for clip_edge in clip_poly.edges():
		intersection_points.clear()
		current_point = clip_edge.p1

		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "Clip Edge: ", 
			clip_edge.print_segment()
		
		# Find all intersection point between current clipping polygon
		# and the subject polygon.
		for poly_edge in poly.edges():
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "	Poly Edge: ", 
				poly_edge.print_segment()
			intersection = clip_edge.intersection(poly_edge)
			if intersection and not clip_edge.is_endpoint(intersection):
				if DEBUG_WA_ALGORITHM_VERBOSE:
					print "		FOUND INTS: ",
					intersection.print_coords()
					print
				intersection_points.add(intersection)
		
		# Sort intersection points by distance from current node
		# Add the intersection point connections to the graph
		sorted_intersection_points = sorted(intersection_points, key=lambda x:x.distance_from(clip_edge.p1))
		while sorted_intersection_points:
			intersection = sorted_intersection_points.pop(0)
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "	ADD INTS: ",
				current_point.print_coords()
				print "-->",
				intersection.print_coords()
				print
			wa_graph[current_point][1].append(intersection)
			current_point = intersection
		
		# Delete list of sorted intersection points
		del sorted_intersection_points

		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "	ADD ENDPOINT: ",
			current_point.print_coords()
			print "-->",
			clip_edge.p2.print_coords()
			print
		wa_graph[current_point][1].append(clip_edge.p2)

	if DEBUG_WA_ALGORITHM_POST_CLIP:
		print "Post Clip Edge Iteration:"
		dbg.debug_print_wa_graph(wa_graph)
		dbg.debug_print_wa_outgoing_points(outgoing_vertices)
		dbg.debug_print_wa_incoming_points(incoming_vertices)

	# Remove intersection of ingoing/outgoing vertice sets
	outgoing = outgoing_vertices - incoming_vertices
	incoming = incoming_vertices - outgoing_vertices

	if DEBUG_WA_ALGORITHM_POST_CLIP:
		print "Post Set Overlap Adjustment:"
		print "Size of outgoing set:", len(outgoing)
		print "Size of incoming set:", len(incoming)
		dbg.debug_print_wa_outgoing_points(outgoing)
		dbg.debug_print_wa_incoming_points(incoming)

	return wa_graph, outgoing, incoming

# ------------------------------------------------------------------
# T/B Layer net blockage WA-Algo debug code (constrained and non)
# ------------------------------------------------------------------
# Color the bitmap
for poly in nearby_polys:
	clipped_polys = Polygon.from_polygon_clip(poly, net_segment_area_poly)
	# plt.figure(1)
	# plt.plot(poly.get_x_coords(), poly.get_y_coords())
	# plt.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords())
	for clipped_poly in clipped_polys:
		# plt.plot(clipped_poly.get_x_coords(), clipped_poly.get_y_coords())
		if clipped_poly.get_area() > 0:
			color_bitmap(net_segment_bitmap, net_segment_area_poly.bbox.ll, clipped_poly)
	# plt.grid()
	# plt.show()

# ------------------------------------------------------------------
# Same Layer (constrained) net blockage sliding window debug code
# ------------------------------------------------------------------
# Scan all 4 perimeter sides to check for blockages
for direction in ['N', 'E', 'S', 'W', 'T', 'B']:
	if direction == 'N':
		start_scan_coord         = net_segment.polygon.bbox.ll.x - sl_min_wire_spacing
		end_scan_coord           = net_segment.polygon.bbox.ur.x + sl_min_wire_spacing
		curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.y + check_distance
		curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.y + 2
	elif direction == 'E':
		start_scan_coord         = net_segment.polygon.bbox.ll.y - sl_min_wire_spacing
		end_scan_coord           = net_segment.polygon.bbox.ur.y + sl_min_wire_spacing
		curr_fixed_coord_pitch   = net_segment.polygon.bbox.ur.x + check_distance
		curr_fixed_coord_overlap = net_segment.polygon.bbox.ur.x + 2
	elif direction == 'S':
		start_scan_coord         = net_segment.polygon.bbox.ll.x - sl_min_wire_spacing
		end_scan_coord           = net_segment.polygon.bbox.ur.x + sl_min_wire_spacing
		curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.y - check_distance
		curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.y - 2
	elif direction == 'W':
		start_scan_coord         = net_segment.polygon.bbox.ll.y - sl_min_wire_spacing
		end_scan_coord           = net_segment.polygon.bbox.ur.y + sl_min_wire_spacing
		curr_fixed_coord_pitch   = net_segment.polygon.bbox.ll.x - check_distance
		curr_fixed_coord_overlap = net_segment.polygon.bbox.ll.x - 2
	elif direction != 'T' and direction != 'B':
		print "ERROR %s: unknown scan direction (%s)." % (inspect.stack()[0][3], direction)
		sys.exit(4)
	
	# Analyze blockage along the perimeter on the same layer
	if direction != 'T' and direction != 'B':
		curr_scan_coord = start_scan_coord
		num_points_to_scan = (float(end_scan_coord - curr_scan_coord) / float(layout.net_blockage_step))
		print "		Checking %.2f units along %s edge (%d/%f units/microns away)..." % (num_points_to_scan, direction, check_distance, float(check_distance / layout.lef.database_units))
		# print "		Start Scan Coord = %d; End Scan Coord = %d; Num Points to Scan = %d" % (curr_scan_coord, end_scan_coord, num_points_to_scan)
		
		# Create Sites Blocked Bitmap 
		# colors  = ['g']*(end_scan_coord - start_scan_coord)
		# markers = ['.']*(end_scan_coord - start_scan_coord)
		sites_blocked = numpy.zeros(shape=(1, end_scan_coord - start_scan_coord))
		sites_ind = 0
		while curr_scan_coord < end_scan_coord:
			sl_poly_overlap = False
			for poly in net_segment.nearby_sl_polygons:
				if direction == 'N' or direction == 'S':
					if poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_pitch)) or poly.is_point_inside(Point(curr_scan_coord, curr_fixed_coord_overlap)):
						for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
							sites_blocked[0, i] = 1
							# colors[i]  = 'r'
							# markers[i] = 'x'
						break
				else:
					if poly.is_point_inside(Point(curr_fixed_coord_pitch, curr_scan_coord)) or poly.is_point_inside(Point(curr_fixed_coord_overlap, curr_scan_coord)):
						for i in range(sites_ind, min(sites_ind + layout.net_blockage_step, sites_ind + (end_scan_coord - curr_scan_coord))):
							sites_blocked[0, i] = 1
							# colors[i]  = 'r'
							# markers[i] = 'x'
						break
			curr_scan_coord += layout.net_blockage_step
			sites_ind       += layout.net_blockage_step

		# Apply sliding window of size (2 * min_spacing * min_wire_width) to calculate wire position blockages
		window_start    = start_scan_coord
		window_end      = window_start + sl_required_open_width
		windows_scanned = 0
		windows_blocked = 0

		# # plt.ion()
		# fig = plt.figure(1)
		# ax = fig.add_subplot(111)
		# net_segment_plot = ax.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords())
		# if direction == 'N' or direction == 'S':
		# 	blocked_line  = ax.scatter(range(start_scan_coord, end_scan_coord), [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord)), color=colors)
		# 	scan_line,    = ax.plot([window_start, window_end-1], [curr_fixed_coord_pitch+10]*2, 'k')
		# else:
		# 	blocked_line  = ax.scatter([curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord)), range(start_scan_coord, end_scan_coord), color=colors)
		# 	scan_line,    = ax.plot([curr_fixed_coord_pitch+10]*2, [window_start, window_end-1], 'k')
		# ax.grid()
		# plt.show()

		while window_end <= end_scan_coord:
			# print "Window Start", window_start
			# print "Window End", window_end
			# print "Length of Sites Blocked", len(sites_blocked)
			# print
			# if direction == 'N' or direction == 'S':
			# 	scan_line.set_xdata([window_start, window_end-1])
			# else:
			# 	scan_line.set_ydata([window_start, window_end-1])
			# fig.canvas.draw()
			# raw_input("		Hit any key to continue...")

			for window_curr in range(window_start, window_end):
				if sites_blocked[0, window_curr-start_scan_coord] == 1:
					# Mark wire position as blocked
					same_layer_units_blocked += 1
					windows_blocked += 1
					break

			window_start                 += 1
			window_end                   += 1
			windows_scanned              += 1
			num_same_layer_units_checked += 1

		if windows_blocked < windows_scanned:
			sides_unblocked.append(direction)
		# print "		Windows blocked %d/%d on %s edge" % (windows_blocked, windows_scanned, direction)

		# fig = plt.figure(1)
		# ax = fig.add_subplot(111)
		# for poly in net_segment.nearby_sl_polygons:
		# 	ax.plot(poly.get_x_coords(), poly.get_y_coords(), color='k')
		# net_segment_plot = ax.plot(net_segment.polygon.get_x_coords(), net_segment.polygon.get_y_coords(), color='b', linewidth=3)
		# if direction == 'N' or direction == 'S':
		# 	x = range(start_scan_coord, end_scan_coord)
		# 	y = [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord))
		# else:
		# 	x = [curr_fixed_coord_pitch]*len(range(start_scan_coord, end_scan_coord))
		# 	y = range(start_scan_coord, end_scan_coord)
		# for xp, yp, c, m in zip(x, y, colors, markers):
		# 	ax.scatter([xp],[yp], color=c, marker=m)
		# ax.grid()
		# plt.show()

# -----------------------------------------------------------------------
# Adjacent Layer (constrained) net blockage bitmap creation optimization
# -----------------------------------------------------------------------
# Create bitmap
nearby_polys_bbox       = BBox.from_multiple_polygons(nearby_polys)
net_segment_area_bitmap = numpy.zeros(shape=(nearby_polys_bbox.get_height(), nearby_polys_bbox.get_width()), dtype=bool)
print "		Checking (%d) nearby polygons along %s side (GDSII Layer:) ..." % (len(nearby_polys), direction)

# Color the bitmap
for poly in nearby_polys:
	# Create bitmap of nearby polygon -- TODO: Fix this
	nearby_poly_bitmap = numpy.ones(shape=(poly.bbox.get_height(), poly.bbox.get_width()), dtype=bool)

	# Compute offsets
	offset_x = poly.bbox.ll.x - nearby_polys_bbox.ll.x
	offset_y = poly.bbox.ll.y - nearby_polys_bbox.ll.y
	nearby_poly_width  = nearby_poly_bitmap.shape[1]
	nearby_poly_height = nearby_poly_bitmap.shape[0]

	# Color main polygon
	net_segment_area_bitmap[offset_y : nearby_poly_height, offset_x : nearby_poly_width] |= nearby_poly_bitmap

# Clip bitmap to min spacing region surrounding net segment projection
offset_x = nearby_bbox.ll.x - nearby_polys_bbox.ll.x
width    = nearby_bbox.get_width()
offset_y = nearby_bbox.ll.y - nearby_polys_bbox.ll.y
height   = nearby_bbox.get_height()
net_segment_area_bitmap = net_segment_area_bitmap[offset_y : height, offset_x : width]


# -----------------------------------------------------------------------
# Adjacent Layer (constrained) net blockage debugging code
# -----------------------------------------------------------------------
			if direction == 'B':
				counter = 0
				poly_layers     = {}
				poly_data_types = {}
				polys           = {}
				poly_shapes     = {'path':0, 'boundary':0, 'other':0}
				# net_segment.polygon.plot()
				for poly in nearby_polys:
				# 	poly.plot()
				# 	if counter == 5:
				# 		break
				# 	counter += 1
			# 	plt.show()
					if poly.gdsii_element.layer in poly_layers:
						poly_layers[poly.gdsii_element.layer] += 1
					else:
						poly_layers[poly.gdsii_element.layer] = 1

					if poly in polys:
						polys[poly] += 1
					else:
						polys[poly] = 1

					if poly.gdsii_element.data_type in poly_data_types:
						poly_data_types[poly.gdsii_element.data_type] += 1
					else:
						poly_data_types[poly.gdsii_element.data_type] = 1

					if isinstance(poly.gdsii_element, Path):
						poly_shapes['path'] += 1
					elif isinstance(poly.gdsii_element, Boundary):
						poly_shapes['boundary'] += 1
					else:
						poly_shapes['other'] += 1

				# print "Poly Layers:"
				# print poly_layers
				# print
				# print "Num. Unique Polys:", len(polys.keys())
				# print 
				# print "Poly Data Types:", poly_data_types
				# print 
				# print "Poly Shapes:", poly_shapes
				# print
					print "Layer:", poly.gdsii_element.layer
					if isinstance(poly.gdsii_element, Path):
						dbg.debug_print_path_obj(poly.gdsii_element)
					elif isinstance(poly.gdsii_element, Boundary):
						dbg.debug_print_boundary_obj(poly.gdsii_element)
					poly.print_vertices()
					print
					counter += 1
					if counter == 5:
						sys.exit(0)