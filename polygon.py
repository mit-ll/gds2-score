# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from error import *

# Import matplotlib
import matplotlib.pyplot as plt

# Other Imports
import inspect
import sys

COMPUTATION_TOLERANCE = 0.001

class Point():
	def __init__(self, x, y):
		self.x = float(x)
		self.y = float(y)

	@classmethod
	def from_tuple(cls, point_tuple):
		return cls(point_tuple[0], point_tuple[1])

	@classmethod
	def from_point_and_offset(cls, point, x_offset, y_offset):
		x = point.x + x_offset
		y = point.y + y_offset
		return cls(x, y)

	def shift(self, x_offset, y_offset):
		self.x += x_offset
		self.y += y_offset

# Line Segment
class LineSegment():
	def __init__(self, p1, p2):
		# End Points
		self.p1 = p1
		self.p2 = p2
		# Standard Form of the Line
		self.a, self.b, self.c = self.get_standard_form_coefs()  

	# Standard Form of a line: ax + by = c,
	# where a, b, and c are coefs
	def get_standard_form_coefs(self):
		a = float(self.p1.y) - float(self.p2.y)
		b = float(self.p2.x) - float(self.p2.x)
		c = (self.p1.x * self.p2.y) - (self.p2.x * self.p1.y)
		return (a, b, c)

	# Returns true if the all point P lies on the line segment
	# NOTE: Assumes all points are colinear.
	def on_segment(self, P):
		if P.x <= max(self.p1.x, self.p2.x) and P.x >= min(self.p1.x, self.p2.x) and \
			P.y <= max(self.p1.y, self.p2.y) and P.y >= min(self.p1.y, self.p2.y):
			return True
		return False

	# Returns the following values according to the 
	# orientation of the points A, B, C:
	# 0 --> p, q and r are colinear
	# 1 --> Clockwise
	# 2 --> Counterclockwise
	def orientation_of_points(self, A, B, C):
		orientation = ((B.y - A.y) * (C.x - B.x)) - ((B.x - A.x) * (C.y - B.y))
		if orientation == 0:
			# Colinear
			return 0
		elif orientation > 0:
			# Clockwise
			return 1
		else:
			# Counterclockwise
			return 2

	# Returns True if the line segments intersect.
	# Returns False otherwise.
	def intersects(self, line):
		orientation_1 = self.orientation_of_points(self.p1, line.p1, self.p2)
		orientation_2 = self.orientation_of_points(self.p1, line.p1, line.p2)
		orientation_3 = self.orientation_of_points(self.p2, line.p2, self.p1)
		orientation_4 = self.orientation_of_points(self.p2, line.p2, line.p1)

		# General Case
		if orientation_1 != orientation_2 and orientation_3 != orientation_4:
			return True

		# Special Cases
		temp_line = LineSegment(self.p1, line.p1)
		if orientation_1 == 0 and temp_line.on_segment(self.p2):
			return True
		if orientation_2 == 0 and temp_line.on_segment(line.p2):
			return True
		temp_line = LineSegment(self.p2, line.p2)
		if orientation_3 == 0 and temp_line.on_segment(self.p1):
			return True
		if orientation_4 == 0 and temp_line.on_segment(line.p1):
			return True

		return False

	# Cramer's Method
	def intersection(self, line):
		if self.intersects(line):
			determinant   = (self.a * line.b) - (line.a * self.b)
			determinant_x = (self.c * line.b) - (line.c * self.b)
			determinant_y = (self.a * line.c) - (line.a * self.c)
			if determinant != 0:
				x = determinant_x / determinant
				y = determinant_y / determinant
				return Point(x, y)
		return None

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
	def from_bbox_and_extension(cls, bbox, extension):
		ll = Point.from_point_and_offset(bbox.ll, extension * -1, extension * -1)
		ur = Point.from_point_and_offset(bbox.ur, extension, extension)
		return cls(ll, ur)

	def get_perimeter(self):
		return (self.ll.x + self.ll.y + self.ur.x + self.ur.y)

	def get_bbox_as_list(self):
		return [(self.ll.x, self.ll.y), (self.ur.x, self.ur.y)]

	def get_bbox_as_list_microns(self, scale_factor):
		return [(self.ll.x * scale_factor, self.ll.y * scale_factor,), (self.ur.x * scale_factor, self.ur.y * scale_factor)]

class Polygon():
	def __init__(self, coords):
		self.num_coords = len(coords)
		self.coords     = coords
		self.bbox       = BBox.from_polygon(self)

	# @TODO: Clean this up
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

			return cls(coords)

	@classmethod
	def from_gdsii_boundary(cls, boundary):
		coords = []
		for coord in boundary.xy:
			coords.append(Point(coord[0], coord[1]))
		return cls(coords)

	# Weiler-Atherton Algorithm
	# @classmethod
	# def from_polygon_clip(cls, poly, clip_poly):
	# 	coords = []
	# 	coords.append(poly.coords[0])
	# 	for i in range(poly.num_coords - 1):
	# 		curr_poly_edge = Line(poly.coords[i], poly.coords[i + 1])
	# 		for j in range(clip_poly.num_coords - 1):
	# 			curr_clip_edge     = Line(clip_poly.coords[i], clip_poly.coords[i + 1])
	# 			intersection_point = curr_clip_edge.intersection(curr_poly_edge)
	# 			if intersection_point != None:
	# 				coords.append(intersection_point)
	# 		coords.append(poly.coords[i + 1])

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
		for i in range(self.num_coords - 1):
			cross_product += ((self.coords[i].x * self.coords[i + 1].y) - (self.coords[i + 1].y * self.coords[i].x))
		return abs(float(cross_product) / 2.0)

	def plot(self):
		plt.plot(self.get_x_coords(), self.get_y_coords())
		plt.show()

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
		if x_reflection == REFLECTION_ABOUT_X_AXIS:
			self.reflect_across_x_axis()
		if degrees_rotation != 0 and degrees_rotation != None:
			self.rotate(degrees_rotation)
		if offset_x != 0 or offset_y != 0:
			self.shift_x_y(offset_x, offset_y)

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

