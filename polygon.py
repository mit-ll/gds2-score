# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
import debug_prints as dbg
from error import *

# Import matplotlib
# import matplotlib.pyplot as plt

# Other Imports
import math
import copy
import inspect
import sys
import pprint

# Debug Print Flags
DEBUG_INTERSECTION_CALCS   = False
DEBUG_WA_ALGORITHM_VERBOSE = False

class Point():
	def __init__(self, x, y):
		self.x = x
		self.y = y

	@classmethod
	def from_tuple(cls, tup):
		return cls(tup[0], tup[1])

	@classmethod
	def from_point_and_offset(cls, point, x_offset, y_offset):
		x = point.x + x_offset
		y = point.y + y_offset
		return cls(x, y)

	def __eq__(self, other_point):
		if other_point != None:
			return ((self.x == other_point.x) and (self.y == other_point.y))
		else:
			return False

	def __ne__(self, other_point):
		return not(self == other_point)

	def __hash__(self):
		return hash((self.x, self.y))

	def shift(self, x_offset, y_offset):
		self.x += x_offset
		self.y += y_offset

	# Computes the eulcidean distance_from itself to point P
	def distance_from(self, P):
		return math.sqrt((P.x - self.x)**2 + (P.y - self.y)**2)

	def print_coords(self, convert_to_microns=False, scale_factor=1):
		if convert_to_microns:
			print "(x: %.3f; y: %.3f)" % (self.x * scale_factor, self.y * scale_factor),
		else:
			# print "(x: %5d; y: %5d)" % (self.x, self.y),
			print "(x: %d; y: %d)" % (self.x, self.y),

# Line Segment
class LineSegment():
	def __init__(self, p1, p2):
		# End Points
		self.p1 = p1
		self.p2 = p2
		if p1.x != p2.x:
			self.slope       = (p2.y - p1.y) / (p2.x - p1.x)
			self.y_intercept = p1.y - (self.slope * p1.x)
		else:
			self.slope       = None
			self.y_intercept = None
		# Standard Form of the Line
		self.a, self.b, self.c = self.get_standard_form_coefs()

	# Standard Form of a line: ax + by = c,
	# where a, b, and c are coefs
	def get_standard_form_coefs(self):
		a = float(self.p1.y) - float(self.p2.y)
		b = float(self.p2.x) - float(self.p1.x)
		c = -1.0 * ((self.p1.x * self.p2.y) - (self.p2.x * self.p1.y))
		return (a, b, c)

	# Returns the following values according to the orientation 
	# of the segment's points p1 and p2 with the provided point R:
	# 0 --> p1, p2 and R are colinear
	# 1 --> Clockwise
	# 2 --> Counterclockwise
	def get_orientation_of_points(self, R):
		orientation = ((self.p2.y - self.p1.y) * (R.x - self.p2.x)) - ((self.p2.x - self.p1.x) * (R.y - self.p2.y))
		if orientation == 0:
			# Colinear
			return 0
		elif orientation > 0:
			# Clockwise
			return 1
		else:
			# Counterclockwise
			return 2

	# Returns true if the point P lies on the line segment
	def on_segment(self, P):
		if self.get_orientation_of_points(P) == 0:
			if P.x <= max(self.p1.x, self.p2.x) and P.x >= min(self.p1.x, self.p2.x):
				if P.y <= max(self.p1.y, self.p2.y) and P.y >= min(self.p1.y, self.p2.y):
					# Debug Prints
					if DEBUG_INTERSECTION_CALCS:
						print "			ON SEGMENT: ", 
						P.print_coords()
						self.print_segment()
					return True
		return False

	# Returns True if the line segments intersect.
	# Returns False otherwise.
	def intersects(self, line):
		orientation_1 = self.get_orientation_of_points(line.p1)
		orientation_2 = self.get_orientation_of_points(line.p2)
		orientation_3 = line.get_orientation_of_points(self.p1)
		orientation_4 = line.get_orientation_of_points(self.p2)

		# Debug Prints
		if DEBUG_INTERSECTION_CALCS:
			print "		Orientations: ", orientation_1, orientation_2, orientation_3, orientation_4

		# General Case
		if orientation_1 != orientation_2 and orientation_3 != orientation_4:
			return True

		# Special Cases
		temp_line = LineSegment(self.p1, self.p2)
		if temp_line.on_segment(line.p1):
			return True
		if temp_line.on_segment(line.p2):
			return True
		temp_line = LineSegment(line.p1, line.p2)
		if temp_line.on_segment(self.p1):
			return True
		if temp_line.on_segment(self.p2):
			return True
		return False

	# Cramer's Method
	def intersection(self, line):
		if self.intersects(line):
			determinant   = (self.a * line.b) - (line.a * self.b)
			determinant_x = (self.c * line.b) - (line.c * self.b)
			determinant_y = (self.a * line.c) - (line.a * self.c)
			if DEBUG_INTERSECTION_CALCS:
				print "		Checking intersection of "
				print "		P1(x: %5d; y: %5d) --- P2(x: %5d; y: %5d)" % (self.p1.x, self.p1.y, self.p2.x, self.p2.y)
				print "			AND"
				print "		P1(x: %5d; y: %5d) --- P2(x: %5d; y: %5d)" % (line.p1.x, line.p1.y, line.p2.x, line.p2.y)
				print "		Determinants:", determinant, determinant_x, determinant_y
				print
			if determinant != 0:
				x = float(determinant_x / determinant)
				y = float(determinant_y / determinant)
				return Point(x, y)
		return None

	def get_south_endpoint(self):
		if not self.is_horizontal():
			if self.p1.y < self.p2.y:
				return self.p1
			else:
				return self.p2
		return None

	def get_north_endpoint(self):
		if not self.is_horizontal():
			if self.p2.y > self.p1.y:
				return self.p2
			else:
				return self.p1
		return None

	def get_east_endpoint(self):
		if not self.is_vertical():
			if self.p2.x > self.p1.x:
				return self.p2
			else:
				return self.p1
		return None

	def get_west_endpoint(self):
		if not self.is_vertical():
			if self.p1.x < self.p2.x:
				return self.p1
			else:
				return self.p2
		return None

	def get_length(self):
		if   self.is_vertical():
			return (self.get_north_endpoint().y - self.get_south_endpoint().y)
		elif self.is_horizontal():
			return (self.get_east_endpoint().x - self.get_west_endpoint().x)
		else:
			return self.p1.distance_from(self.p2)

	def is_endpoint(self, P):
		if (self.p1 == P) or (self.p2 == P):
			return True
		return False

	def is_vertical(self):
		if self.p1.x == self.p2.x:
			return True
		return False

	def is_horizontal(self):
		if self.p1.y == self.p2.y:
			return True
		return False
	
	def print_segment(self, convert_to_microns=False, scale_factor=1):
		if convert_to_microns:
			print "P1(x: %.3f; y: %.3f) --- P2(x: %.3f; y: %.3f)" % (self.p1.x * scale_factor, self.p1.y * scale_factor, self.p2.x * scale_factor, self.p2.y * scale_factor)
		else:
			print "P1(x: %d; y: %d) --- P2(x: %d; y: %d)" % (self.p1.x, self.p1.y, self.p2.x, self.p2.y)

class BBox():
	def __init__(self, ll, ur):
		self.ll     = ll
		self.ur     = ur
		self.height = self.ur.y - self.ll.y
		self.width  = self.ur.x - self.ll.x

	def __eq__(self, other_bbox):
		if other_bbox != None:
			return ((self.ll == other_bbox.ll) and (self.ur == other_bbox.ur))
		else:
			return False

	def __ne__(self, other_bbox):
		return not(self == other_bbox)

	def __hash__(self):
		return hash((self.ll.x, self.ll.y, self.ur.x, self.ur.y))

	@classmethod
	def from_polygon(cls, poly):
		x_coords = poly.get_x_coords()
		y_coords = poly.get_y_coords()
		ll       = Point(min(x_coords), min(y_coords))
		ur       = Point(max(x_coords), max(y_coords))
		return cls(ll, ur)

	@classmethod
	def from_multiple_polygons(cls, polys):
		# Create list of all X and Y coords
		all_x_coords = []
		all_y_coords = []
		for poly in polys:
			all_x_coords.extend(copy.copy(poly.get_x_coords()))
			all_y_coords.extend(copy.copy(poly.get_y_coords()))
		
		# Extract min/max values
		ll = Point(min(all_x_coords), min(all_y_coords))
		ur = Point(max(all_x_coords), max(all_y_coords))

		return cls(ll, ur)
		
	@classmethod
	def from_bbox_and_extension(cls, bbox, extension):
		ll = Point.from_point_and_offset(bbox.ll, extension * -1, extension * -1)
		ur = Point.from_point_and_offset(bbox.ur, extension, extension)
		return cls(ll, ur)

	def get_width(self):
		return (self.ur.x - self.ll.x)

	def get_height(self):
		return (self.ur.y - self.ll.y)

	def get_perimeter(self):
		return ((2 * self.get_width()) + (2 * self.get_height()))

	def get_center(self):
		return Point(self.ll.x + (self.get_width() / 2), self.ll.y + (self.get_height() / 2))

	def get_bbox_as_list(self):
		return [(self.ll.x, self.ll.y), (self.ur.x, self.ur.y)]

	def get_bbox_as_list_microns(self, scale_factor):
		return [(self.ll.x * scale_factor, self.ll.y * scale_factor,), (self.ur.x * scale_factor, self.ur.y * scale_factor)]

	# Returns True if the provided coords are inside the 
	# bounding box. Otherwise, returns False.
	def are_coords_inside_bbox(self, x, y):
		if x >= self.ll.x and x <= self.ur.x:
			if y >= self.ll.y and y <= self.ur.y:
				return True
		return False

	# Returns True if the provided point is inside the 
	# bounding box. Otherwise, returns False.
	def is_point_inside_bbox(self, point):
		if point.x >= self.ll.x and point.x <= self.ur.x:
			if point.y >= self.ll.y and point.y <= self.ur.y:
				return True
		return False

	# Returns True if the provided bounding box overlaps the bounding
	# box of the polygon. Otherwise, returns False.
	def overlaps_bbox(self, bbox):
		# Check if one box is to the left of another box
		if self.ur.x < bbox.ll.x or bbox.ur.x < self.ll.x:
			return False
		# Check if one box is above the other box
		if self.ur.y < bbox.ll.y or bbox.ur.y < self.ll.y:
			return False
		return True

	def plot(self):
		x_coords = [self.ll.x, self.ur.x, self.ur.x, self.ll.x, self.ll.x]
		y_coords = [self.ll.y, self.ll.y, self.ur.y, self.ur.y, self.ll.y]
		plt.plot(x_coords, y_coords)

# Coords = list of Point objects, starting and ending with first point
class Polygon():
	def __init__(self, coords, gdsii_element=None):
		self.num_coords    = len(coords)
		self.coords        = coords
		self.gdsii_element = gdsii_element
		self.bbox          = BBox.from_polygon(self)

	def __eq__(self, other_poly):
		if other_poly != None:
			return ((self.num_coords == other_poly.num_coords) and (set(self.coords) == set(other_poly.coords)) and (self.bbox == other_poly.bbox))
		else:
			return False

	def __ne__(self, other_poly):
		return not(self == other_poly)

	def __hash__(self):
		poly_info = []
		poly_info.append(self.num_coords)
		poly_info.extend(self.coords)
		poly_info.append(self.bbox.ll)
		poly_info.append(self.bbox.ur)
		poly_info = tuple(poly_info)
		return hash(poly_info)

	@classmethod
	def from_gdsii_path(cls, path):
		if is_path_type_supported(path):
			point_1    = Point.from_tuple(path.xy[0])
			point_2    = Point.from_tuple(path.xy[1])
			half_width = path.width / 2
			if point_1.x == point_2.x:
				# Path is Vertical
				# # Custom Extensions
				# if path.path_type == 4:
				# 	point_1.y += path.bgn_extn 
				# 	point_2.y += path.end_extn 
				ll_corner = point_1 if point_1.y < point_2.y else point_2
				ur_corner = point_2 if point_1.y < point_2.y else point_1
				if path.path_type == 0 or path.path_type == None or path.path_type == 4:
					# Square-ended path that ends flush	
					ll_corner.x -= half_width
					ur_corner.x += half_width
			elif point_1.y == point_2.y:
				# Path is Horizontal
				# # Custom Extensions
				# if path.path_type == 4:
				# 	point_1.x += path.bgn_extn 
				# 	point_2.x += path.end_extn 
				ll_corner = point_1 if point_1.x < point_2.x else point_2
				ur_corner = point_2 if point_1.x < point_2.x else point_1
				if path.path_type == 0 or path.path_type == None or path.path_type == 4:
					# Square-ended path that ends flush
					ll_corner.y -= half_width
					ur_corner.y += half_width
			else:
				print "UNSUPPORTED %s: path object is neither Vertical nor Horizontal." % (inspect.stack()[0][3])
				sys.exit(3)

			if path.path_type == 2:
				# Square-ended path that extends past endpoints
				ll_corner.x -= half_width
				ll_corner.y -= half_width
				ur_corner.x += half_width
				ur_corner.y += half_width

			# Calculate coords for remaining corners
			lr_corner = Point.from_point_and_offset(ll_corner, (ur_corner.x - ll_corner.x), 0)
			ul_corner = Point.from_point_and_offset(ur_corner, (ll_corner.x - ur_corner.x), 0)
			
			# List of Coords -- 5 coords total -- first and last are the same
			coords = [ll_corner, lr_corner, ur_corner, ul_corner, copy.deepcopy(ll_corner)]

			return cls(coords, path)

	@classmethod
	def from_gdsii_boundary(cls, boundary):
		coords = []
		for coord in boundary.xy:
			coords.append(Point(coord[0], coord[1]))
		return cls(coords, boundary)

	@classmethod
	def from_rect_poly_and_extension(cls, rect_poly, height_extension, width_extension):
		# Verify rect_poly is a rectangle, i.e. has exactly 5 coords (1st and last coord are the same)
		if rect_poly.num_coords != 5:
			print "Num coords:", rect_poly.num_coords
			print "ERROR %s: polygon is not a rectangle." % (inspect.stack()[0][3])
			sys.exit(4)

		ll_corner = Point(rect_poly.bbox.ll.x - width_extension, rect_poly.bbox.ll.y - height_extension)
		lr_corner = Point(rect_poly.bbox.ur.x + width_extension, rect_poly.bbox.ll.y - height_extension)
		ur_corner = Point(rect_poly.bbox.ur.x + width_extension, rect_poly.bbox.ur.y + height_extension)
		ul_corner = Point(rect_poly.bbox.ll.x - width_extension, rect_poly.bbox.ur.y + height_extension)
		coords    = [ll_corner, lr_corner, ur_corner, ul_corner, copy.deepcopy(ll_corner)] 
		
		return cls(coords)

	# Weiler-Atherton Algorithm
	@classmethod
	def intersection_is_vertex(cls, poly_edge, clip_edge, intersection):
		if poly_edge.is_endpoint(intersection) or clip_edge.is_endpoint(intersection):
			return True
		return False

	@classmethod
	def from_polygon_clip(cls, poly, clip_poly):
		# plt.figure(1)
		# plt.plot(poly.get_x_coords(), poly.get_y_coords())
		# plt.plot(clip_poly.get_x_coords(), clip_poly.get_y_coords())
		# plt.grid()
		# plt.show()
		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "Start - Poly Vertices:",
			dbg.debug_print_wa_vertices(poly.coords, set())
			print "Start - Clip Vertices:", 
			dbg.debug_print_wa_vertices(clip_poly.coords, set())
			print

		poly_vertices, clip_vertices, incoming, intersections = cls.build_wa_graph(poly, clip_poly)

		new_polys = []
		
		# Set maximum number of algorithm iterations before killing the program
		max_iterations = (len(poly_vertices) + len(clip_vertices)) * 2

		# If no outgoing points --> check two cases:
		# 1. subject polygon is completely contained inside the clip polygon --> return subject polygon
		# 2. clip polygon is completely contained inside the subject polygon --> return clip polygon
		if not incoming:
			poly_contained_inside = True
			clip_contained_inside = True
			
			# Check case 1
			for vertex in poly.coords:
				if not clip_poly.is_point_inside(vertex):
					poly_contained_inside = False
					break
			
			# Check case 2
			for vertex in clip_poly.coords:
				if not poly.is_point_inside(vertex):
					clip_contained_inside = False
					break
			
			# Case 1
			if poly_contained_inside:
				new_polys.append(poly)
			# Case 2
			elif clip_contained_inside:
				new_polys.append(clip_poly)

		# Start at exit intersection, walk graph to create clipped polygon(s)
		while incoming:
			walk_edge_index = 1
			start_vertex    = incoming.pop()
			new_poly_coords = [start_vertex]

			# Construct polygon coords
			curr_vertex = poly_vertices[(poly_vertices.index(start_vertex) + 1) % len(poly_vertices)]
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

				if iter_num > max_iterations:
					print "ERROR %s: exceeded maximum iterations of Weiler-Atherton algorithm." % (inspect.stack()[0][3])
					sys.exit(3)

				# Change border being walked if needed
				if curr_vertex in intersections:
					walk_edge_index = (walk_edge_index + 1) % 2
					if curr_vertex in incoming:
						incoming.remove(curr_vertex)

				# Update current vertex
				if walk_edge_index:
					curr_vertex = poly_vertices[(poly_vertices.index(curr_vertex) + 1) % len(poly_vertices)]
				else:
					curr_vertex = clip_vertices[(clip_vertices.index(curr_vertex) + 1) % len(clip_vertices)]

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
			if len(new_poly_coords) > 3:
				new_polys.append(Polygon(new_poly_coords))

		return new_polys

	@classmethod
	def build_wa_graph(cls, poly, clip_poly):
		# Construct graph with three groups of vertices:
		# 1. polygon vertices
		# 2. clipping region
		# 3. intersection vertices

		incoming      = set()
		intersections = set()
		poly_vertices = []
		clip_vertices = []

		# Add all poly and clip_poly nodes to graph
		for vertex in poly.coords:
			poly_vertices.append(vertex)
		for vertex in clip_poly.coords:
			clip_vertices.append(vertex)

		# Add intersection points to poly_coords, keeping 
		# track of entering of intersection points.
		inside_clip_region = False
		prev_intersection  = None 
		poly_ind = 0
		for poly_edge in poly.edges():
			if DEBUG_WA_ALGORITHM_VERBOSE:
				print "Current poly_edge:",
				poly_edge.print_segment()
			temp_intersections = set()
			for clip_edge in clip_poly.edges():
				possible_intersection = poly_edge.intersection(clip_edge)
				if possible_intersection:
					temp_intersections.add((possible_intersection, clip_vertices[1:].index(clip_edge.p2) + 1, clip_edge))
			sorted_intersection_points = sorted(temp_intersections, key=lambda x:x[0].distance_from(poly_edge.p1))
			for i in range(len(sorted_intersection_points)):
				intersection = sorted_intersection_points[i][0]
				# clip_ind     = sorted_intersection_points[i][1]
				clip_edge    = sorted_intersection_points[i][2]
				clip_ind     = clip_vertices[1:].index(clip_edge.p2) + 1
				poly_ind     = poly_vertices[1:].index(poly_edge.p2) + 1
				if DEBUG_WA_ALGORITHM_VERBOSE:
					print "	Potential intersection:", 
					intersection.print_coords()
					print
					print "	Current clip_edge:",
					clip_edge.print_segment()
				# Intersection is NOT at a poly or clip vertex
				if not cls.intersection_is_vertex(poly_edge, clip_edge, intersection):
					# Add to intersections set
					intersections.add(intersection)

					# Add intersection poly list
					poly_vertices.insert(poly_ind, intersection)
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		Inserting into poly_vertices:", 
						intersection.print_coords()
						print poly_ind
						dbg.debug_print_wa_vertices(poly_vertices, intersections)

					# Add intersection to clip_poly list
					clip_vertices.insert(clip_ind, intersection)
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		Inserting into clip_vertices:", 
						intersection.print_coords()
						print clip_ind
						dbg.debug_print_wa_vertices(clip_vertices, intersections)
					
					# Add intersection to incoming vertices
					if not inside_clip_region:
						if DEBUG_WA_ALGORITHM_VERBOSE:
							print "		Adding to incoming..."
						incoming.add(intersection)
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "Incoming:"
						dbg.debug_print_points(incoming)
					inside_clip_region = not inside_clip_region
					prev_intersection  = intersection
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print
				# Intersection IS at a poly or clip vertex
				else:
					# Determine intersection insertion indices
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		Intersection is a vertex..."
					insert_in_clip_vertices = False
					insert_in_poly_vertices = False
					# Intersection is at a poly vertex OR a poly and clip vertex
					if poly_edge.is_endpoint(intersection):
						# Intersection at poly p2
						if intersection == poly_edge.p2:
							poly_ind_before = poly_vertices[1:].index(poly_edge.p2)
							poly_ind_after  = (poly_ind_before + 2) % len(poly_vertices)
						# Intersection at poly p1
						else:
							poly_ind_before = (poly_vertices[:-1].index(poly_edge.p1) - 1)
							poly_ind_after  = (poly_ind_before + 2) % len(poly_vertices)
						# If intersection is NOT on clip vertex --> must insert into clip vertices
						if not clip_edge.is_endpoint(intersection):
							insert_in_clip_vertices = True
					# Intersection is at only a clip vertex
					elif clip_edge.is_endpoint(intersection):
						poly_ind_before         = poly_vertices.index(poly_edge.p1)
						poly_ind_after          = poly_ind_before + 1
						insert_in_poly_vertices = True

					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "		Poly Ind Before Int:  ", poly_ind_before
						print "		Poly Ind After Int:   ", poly_ind_after
						if prev_intersection:
							print "		Previous Intersection:", 
							prev_intersection.print_coords()
						else:
							print "		Previous Intersection: None", 
						print

					# Add intersections nodes
					# Previous poly vertices was an intersection point --> base decision 
					# off previous classification of in/out of clip region.
					if poly_vertices[poly_ind_before] == prev_intersection:

						# Next poly/clip vertex will also be an intersection point --> this
						# means that it will always been "inside the clip" region since it
						# must fall on the clip boundary to be an intersection.
						if (i + 1) < len(sorted_intersection_points):
							if not inside_clip_region:
								# Out-In
								incoming.add(intersection)
								intersections.add(intersection)
								inside_clip_region = True
								prev_intersection  = intersection
								if insert_in_clip_vertices:
									clip_vertices.insert(clip_ind, intersection)
								if insert_in_poly_vertices:
									poly_vertices.insert(poly_ind, intersection)
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Adding to intersections... (Out-In) - based on next int"
							else:
								# In-In
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (In-In) - based on next int"
								prev_intersection = intersection
						# Next poly/clip vertex is NOT an intersection point,
						# use normal method to check whether inside or outside.
						else:
							if not inside_clip_region and clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
								# Out-In
								incoming.add(intersection)
								intersections.add(intersection)
								inside_clip_region = True
								prev_intersection  = intersection
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (Out-In) - based on prev int"
								if insert_in_clip_vertices:
									clip_vertices.insert(clip_ind, intersection)
								if insert_in_poly_vertices:
									poly_vertices.insert(poly_ind, intersection)
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Adding to intersections... (Out-In) - based on prev int"
							elif inside_clip_region and not clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
								# In-Out
								intersections.add(intersection)
								inside_clip_region = False
								prev_intersection  = intersection
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (In-Out) - based on prev int"
								if insert_in_clip_vertices:
									clip_vertices.insert(clip_ind, intersection)
								if insert_in_poly_vertices:
									poly_vertices.insert(poly_ind, intersection)
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Adding to intersections... (In-Out) - based on prev int"
							elif not inside_clip_region and not clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
								# Out-Out
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (Out-Out) - based on prev int"
								prev_intersection = intersection
							elif inside_clip_region and clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
								# In-In
								if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (In-In) - based on prev int"
								prev_intersection = intersection
					# Previous poly vertex was NOT an intersection point
					else:
						if (not clip_poly.is_point_inside(poly_vertices[poly_ind_before]) or not inside_clip_region) and clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
							# Out-In
							incoming.add(intersection)
							intersections.add(intersection)
							inside_clip_region = True
							prev_intersection  = intersection
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (Out-In)"
							if insert_in_clip_vertices:
								clip_vertices.insert(clip_ind, intersection)
							if insert_in_poly_vertices:
								poly_vertices.insert(poly_ind, intersection)
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Adding to intersections... (Out-In)"
						elif (clip_poly.is_point_inside(poly_vertices[poly_ind_before]) or inside_clip_region) and not clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
							# In-Out
							intersections.add(intersection)
							inside_clip_region = False
							prev_intersection  = intersection
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (In-Out)"
							if insert_in_clip_vertices:
								clip_vertices.insert(clip_ind, intersection)
							if insert_in_poly_vertices:
								poly_vertices.insert(poly_ind, intersection)
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Adding to intersections... (In-Out)"
						elif (not clip_poly.is_point_inside(poly_vertices[poly_ind_before]) or not inside_clip_region) and not clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
							# Out-Out
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (Out-Out)"
							prev_intersection = intersection
						elif (clip_poly.is_point_inside(poly_vertices[poly_ind_before]) or inside_clip_region) and clip_poly.is_point_inside(poly_vertices[poly_ind_after]):
							# In-In
							if DEBUG_WA_ALGORITHM_VERBOSE: print "		Updating prev_intersection... (In-In)"
							prev_intersection = intersection

					if DEBUG_WA_ALGORITHM_VERBOSE:
						dbg.debug_print_wa_vertices(poly_vertices, intersections)
						dbg.debug_print_wa_vertices(clip_vertices, intersections)
						print "Incoming:"
						dbg.debug_print_points(incoming)
						print

		# Fix order of poly vertices
		ordered_poly_vertices = []
		ordered_poly_vertices.append(poly.coords[0])
		for poly_edge in poly.edges():
			start = False
			for i in range(len(poly_vertices)):
				curr_vertex = poly_vertices[i]
				if not start:
					if curr_vertex == poly_edge.p1:
						start = True
						temp_vertices = []
				else:
					if curr_vertex == poly_edge.p2:
						start = False
						temp_vertices = sorted(temp_vertices, key=lambda x:x.distance_from(poly_edge.p1))
						ordered_poly_vertices.extend(temp_vertices)
						ordered_poly_vertices.append(poly_edge.p2)
					else:
						temp_vertices.append(curr_vertex)

		# Fix order of clip vertices
		ordered_clip_vertices = []
		ordered_clip_vertices.append(clip_poly.coords[0])
		for clip_edge in clip_poly.edges():
			start = False
			for i in range(len(clip_vertices)):
				curr_vertex = clip_vertices[i]
				if not start:
					if curr_vertex == clip_edge.p1:
						start = True
						temp_vertices = []
				else:
					if curr_vertex == clip_edge.p2:
						start = False
						temp_vertices = sorted(temp_vertices, key=lambda x:x.distance_from(clip_edge.p1))
						ordered_clip_vertices.extend(temp_vertices)
						ordered_clip_vertices.append(clip_edge.p2)
					else:
						temp_vertices.append(curr_vertex)

		if DEBUG_WA_ALGORITHM_VERBOSE:
			print "Ordered Poly Vertices:" 
			dbg.debug_print_wa_vertices(ordered_poly_vertices, intersections)
			print
			print "Ordered Clip Vertices:"
			dbg.debug_print_wa_vertices(ordered_clip_vertices, intersections)
			print
			print "Incoming Vertices:"
			dbg.debug_print_points(incoming)
			print

		return ordered_poly_vertices, ordered_clip_vertices, incoming, intersections

	# Generator that yields edges of the polygon
	# as LineSegment objects.
	def edges(self):
		for i in range(self.num_coords - 1):
			yield LineSegment(self.coords[i], self.coords[i + 1])

	# Generator that yields only the vertical edges of 
	# the polygon as LineSegment objects.
	def vertical_edges(self):
		for i in range(self.num_coords - 1):
			segment = LineSegment(self.coords[i], self.coords[i + 1])
			if segment.is_vertical():
				yield segment
			else:
				continue

	def get_x_coords(self):
		x_coords = []
		for coord in self.coords:
			x_coords.append(coord.x)
		return x_coords

	def get_y_coords(self):
		y_coords = []
		for coord in self.coords:
			y_coords.append(coord.y)
		return y_coords

	def get_area(self):
		cross_product = 0.0
		for edge in self.edges():
			cross_product += ((edge.p1.x * edge.p2.y) - (edge.p1.y * edge.p2.x))
		return abs(float(cross_product) / 2.0)

	def update_bbox(self):
		x_coords     = self.get_x_coords()
		y_coords     = self.get_y_coords()
		self.bbox.ll = Point(min(x_coords), min(y_coords))
		self.bbox.ur = Point(max(x_coords), max(y_coords))

	def plot(self):
		plt.plot(self.get_x_coords(), self.get_y_coords())

	def print_vertices(self):
		print "	Num. Vertices:", self.num_coords
		for coord in self.coords:
			print "	", coord, "-",
			coord.print_coords()
			print
		print

	def rotate(self, degrees):
		if degrees == 90:
			# 1. Switch X and Y values
			# 2. Multiply the new X values by -1
			for i in range(self.num_coords):
				self.coords[i].x, self.coords[i].y = self.coords[i].y, self.coords[i].x
				self.coords[i].x *= -1
		elif degrees == 180:
			# 1. Multiply X and Y values by -1
			for i in range(self.num_coords):
				self.coords[i].x *= -1
				self.coords[i].y *= -1
		elif degrees == 270:
			# 1. Switch X and Y values
			# 2. Multiply the new Y values by -1
			for i in range(self.num_coords):
				self.coords[i].x, self.coords[i].y = self.coords[i].y, self.coords[i].x
				self.coords[i].y *= -1
		else:
			print "UNSUPPORTED %s: rotation of %d degrees not supported." % (inspect.stack()[1][3], degrees)
			sys.exit(3)

	def reflect_across_x_axis(self):
		# 1. Multiply Y values by -1
		# ***NOTE***: must reverse vertices to ensure they are still
		# listed in CCW order. This is necessary for the WA algorithm.
		for i in range(self.num_coords):
			self.coords[i].y *= -1
		# Reverse coords list
		self.coords.reverse()

	def shift_x_y(self, offset_x, offset_y):
		for i in range(self.num_coords):
			self.coords[i].x += offset_x
			self.coords[i].y += offset_y

	def compute_translations(self, offset_x, offset_y, x_reflection, degrees_rotation, verbose=False):
		translation_computed = False
		# Reflections are computed FIRST
		if x_reflection == REFLECTION_ABOUT_X_AXIS:
			self.reflect_across_x_axis()
			translation_computed = True
		# Rotations are computed SECOND
		if degrees_rotation != 0 and degrees_rotation != None:
			self.rotate(degrees_rotation)
			translation_computed = True
		# Offsets are computed LAST
		if offset_x != 0 or offset_y != 0:
			self.shift_x_y(offset_x, offset_y)
			translation_computed = True

		# Update the bounding box if a translation is computed
		if translation_computed:
			self.update_bbox()

	def is_point_inside(self, P):
		# First check if polygon is a rectangle
		if self.num_coords == 5:
			return self.bbox.is_point_inside_bbox(P)
		else:
			# Check if point is inside bbox first
			if self.bbox.is_point_inside_bbox(P):
				# Ray Casting Algorithm 
				inside = False
				for edge in self.edges():
					if edge.on_segment(P):
						return True
					elif P.y > min(edge.p1.y, edge.p2.y) and P.y <= max(edge.p1.y, edge.p2.y):
						if P.x <= max(edge.p1.x, edge.p2.x):
							if edge.p1.y != edge.p2.y:
								x_intersection = ((P.y - edge.p1.y) * ((edge.p2.x - edge.p1.x) / (edge.p2.y - edge.p1.y))) + edge.p1.x
							if edge.p1.x == edge.p2.x or P.x <= x_intersection:
									inside = not inside
				return inside
			else:
				return False

	# Returns True if the provided bounding box overlaps the bounding
	# box of the polygon. Otherwise, returns False.
	def overlaps_bbox(self, bbox):
		# Check if one box is to the left of another box
		if self.bbox.ur.x < bbox.ll.x or bbox.ur.x < self.bbox.ll.x:
			return False
		# Check if one box is above the other box
		if self.bbox.ur.y < bbox.ll.y or bbox.ur.y < self.bbox.ll.y:
			return False
		return True
