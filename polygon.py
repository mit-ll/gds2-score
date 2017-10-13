# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
import debug_prints as dbg
from error import *

# Import matplotlib
import matplotlib.pyplot as plt

# Other Imports
import math
import copy
import inspect
import sys
import pprint

# Debug Print Flags
DEBUG_INTERSECTION_CALCS     = False
DEBUG_WA_ALGORITHM_VERBOSE   = False
DEBUG_WA_ALGORITHM_POST_POLY = False
DEBUG_WA_ALGORITHM_POST_CLIP = False

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
			return (self.x == other_point.x and self.y == other_point.y)
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

	def print_coords(self):
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
				x = int(determinant_x / determinant)
				y = int(determinant_y / determinant)
				return Point(x, y)
		return None

	def is_endpoint(self, P):
		if self.p1 == P or self.p2 == P:
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

	def print_segment(self):
		print "P1(x: %d; y: %d) --- P2(x: %d; y: %d)" % (self.p1.x, self.p1.y, self.p2.x, self.p2.y)

class BBox():
	def __init__(self, ll, ur):
		self.ll = ll
		self.ur = ur
		self.length = max((self.ur.x - self.ll.x), (self.ur.y - self.ll.y))

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

class Polygon():
	def __init__(self, coords, gdsii_element=None):
		self.num_coords    = len(coords)
		self.coords        = coords
		self.gdsii_element = gdsii_element
		self.bbox          = BBox.from_polygon(self)
		
	@classmethod
	def from_gdsii_path(cls, path):
		if is_path_type_supported(path):
			point_1    = Point.from_tuple(path.xy[0])
			point_2    = Point.from_tuple(path.xy[1])
			half_width = path.width / 2
			if point_1.x == point_2.x:
				# Path is Vertical
				ll_corner = point_1 if point_1.y < point_2.y else point_2
				ur_corner = point_2 if point_1.y < point_2.y else point_1
				if path.path_type == 0:
					# Square-ended path that ends flush	
					ll_corner.x -= half_width
					ur_corner.x += half_width
			elif point_1.y == point_2.y:
				# Path is Horizontal
				ll_corner = point_1 if point_1.x < point_2.x else point_2
				ur_corner = point_2 if point_1.x < point_2.x else point_1
				if path.path_type == 0:
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
			coords = [ll_corner, lr_corner, ur_corner, ul_corner, ll_corner]

			return cls(coords, path)

	@classmethod
	def from_gdsii_boundary(cls, boundary):
		coords = []
		for coord in boundary.xy:
			coords.append(Point(coord[0], coord[1]))
		return cls(coords, boundary)

	# Weiler-Atherton Algorithm
	# Returns list of polygon objects as a result of a clipping operation
	@classmethod
	def from_polygon_clip(cls, poly, clip_poly):
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
		inside_clip_region = clip_poly.is_point_inside(poly.coords[0])
		for poly_edge in poly.edges():
			intersection_points = set()
			current_point       = poly_edge.p1
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
						intersection_points.add(copy.deepcopy(intersection))
					elif poly_edge.is_endpoint(intersection):
						# Add intersection point to incoming/outgoing set(s)
						if inside_clip_region:
							outgoing_vertices.add(intersection)
						else: 
							incoming_vertices.add(intersection)
						inside_clip_region = not inside_clip_region
					elif clip_edge.is_endpoint(intersection):
						# Add intersection point to incoming/outgoing set(s)
						outgoing_vertices.add(intersection)
						incoming_vertices.add(intersection)
			# Sort intersection points by distance from polgon segment start point.
			# Add the intersection point connections to the graph.
			intersection_points = sorted(intersection_points, key=lambda x:x.distance_from(poly_edge.p1))
			while intersection_points:
				intersection = intersection_points.pop(0)
				# Add intersection point to graph
				if intersection not in wa_graph:
					if DEBUG_WA_ALGORITHM_VERBOSE:
						print "	INT NOT FOUND IN WA_GRAPH: ",
						intersection.print_coords()
						print
					wa_graph[intersection] = [[], []]
					# Add intersection point to incoming/outgoing set(s)
					if inside_clip_region:
						outgoing_vertices.add(intersection)
					else: 
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
			# Add edge connecting last intersection point to 
			# poly edge end-point to wa_graph.
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
			intersection_points = set()
			current_point       = clip_edge.p1
			# Find all intersection point between current clipping polygon
			# and the subject polygon.
			for poly_edge in poly.edges():
				intersection = clip_edge.intersection(poly_edge)
				if intersection:
					if not clip_edge.is_endpoint(intersection):
						intersection_points.add(copy.deepcopy(intersection))
			# Sort intersection points by distance from current node
			# Add the intersection point connections to the graph
			intersection_points = sorted(intersection_points, key=lambda x:x.distance_from(clip_edge.p1))
			while intersection_points:
				intersection = intersection_points.pop(0)
				wa_graph[current_point][1].append(intersection)
				current_point = intersection
			wa_graph[current_point][1].append(clip_edge.p2)

		if DEBUG_WA_ALGORITHM_POST_CLIP:
			print "Post Clip Edge Iteration:"
			dbg.debug_print_wa_graph(wa_graph)
			dbg.debug_print_wa_outgoing_points(outgoing_vertices)
			dbg.debug_print_wa_incoming_points(incoming_vertices)

		# Remove intersection of ingoing/outgoing vertice sets
		outgoing = outgoing_vertices - incoming_vertices
		incoming = incoming_vertices - outgoing_vertices

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
			while curr_vertex != start_vertex:
				# Add vertex to current polygon coords
				new_poly_coords.append(curr_vertex)

				# Change border being walked if needed
				if curr_vertex in incoming or curr_vertex in outgoing:
					walk_edge_index = (walk_edge_index + 1) % 2
					
					# Remove from list of outgoing_vertices if needed
					if curr_vertex in outgoing:
						outgoing.remove(curr_vertex)

				# Update current vertex
				curr_vertex = wa_graph[curr_vertex][walk_edge_index][0]
			new_poly_coords.append(start_vertex)

			# Construct new polygon object
			new_polys.append(Polygon(new_poly_coords))

		return new_polys

	def __eq__(self, other_poly):
		sorted
		if other_point != None:
			return (self.x == other_point.x and self.y == other_point.y)
		else:
			return False

	def __ne__(self, other_point):
		return not(self == other_point)

	def __hash__(self):
		return hash((self.x, self.y))

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
		for i in range(self.num_coords):
			self.coords[i].y *= -1

	def shift_x_y(self, offset_x, offset_y):
		for i in range(self.num_coords):
			self.coords[i].x += offset_x
			self.coords[i].y += offset_y

	def compute_translations(self, offset_x, offset_y, x_reflection, degrees_rotation):
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
