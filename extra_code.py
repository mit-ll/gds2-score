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
				