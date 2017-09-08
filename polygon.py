# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from error import *

# Import matplotlib
import matplotlib.pyplot as plt

# Other Imports
import inspect
import sys

class BBox():
	def __init__(self, ll_x, ll_y, ur_x, ur_y):
		self.ll_x   = ll_x
		self.ll_y   = ll_y
		self.ur_x   = ur_x
		self.ur_y   = ur_y
		self.length = max((self.ur_x - self.ll_x), (self.ur_y - self.ll_y))

	@classmethod
	def from_polygon(cls, poly):
		ll_x = min(poly.x_coords)
		ll_y = min(poly.y_coords)
		ur_x = max(poly.x_coords)
		ur_y = max(poly.y_coords)
		return cls(ll_x, ll_y, ur_x, ur_y)
		
	@classmethod
	def from_bbox_and_extension(cls, bbox, extension):
		ll_x = bbox.ll_x - extension
		ll_y = bbox.ll_y - extension
		ur_x = bbox.ur_x + extension
		ur_y = bbox.ur_y + extension
		return cls(ll_x, ll_y, ur_x, ur_y)

	def get_perimeter(self):
		return (self.ll_x + self.ll_y + self.ur_x + self.ur_y)

	def get_bbox_as_list(self):
		return [(self.ll_x, self.ll_y), (self.ur_x, self.ur_y)]

	def get_bbox_as_list_microns(self, scale_factor):
		return [(self.ll_x * scale_factor, self.ll_y * scale_factor,), (self.ur_x * scale_factor, self.ur_y * scale_factor)]

class Polygon():
	def __init__(self, num_coords, x_coords, y_coords):
		self.num_coords = num_coords
		self.x_coords   = x_coords
		self.y_coords   = y_coords
		self.bbox       = BBox.from_polygon(self)

	# @TODO: Clean this up
	@classmethod
	def from_gdsii_path(cls, path):
		# Coordinate Indexes
		X = 0
		Y = 1

		if is_path_type_supported(path):
			coord_1 = path.xy[0]
			coord_2 = path.xy[1]

			if coord_1[X] == coord_2[X]:
				# Path is Vertical
				ll_corner  = (coord_1[X], coord_1[Y]) if coord_1[Y] < coord_2[Y] else (coord_2[X], coord_2[Y])
				ur_corner  = (coord_2[X], coord_2[Y]) if coord_1[Y] < coord_2[Y] else (coord_1[X], coord_1[Y])
				half_width = path.width / 2
				if path.path_type == 2:
					# Square-ended path that extends past endpoints
					ll_corner  = (ll_corner[X] - half_width, ll_corner[Y] - half_width)
					ur_corner  = (ur_corner[X] + half_width, ur_corner[Y] + half_width)
				elif path.path_type == 0:
					# Square-ended path that ends flush	
					ll_corner  = (ll_corner[X] - half_width, ll_corner[Y])
					ur_corner  = (ur_corner[X] + half_width, ur_corner[Y])
			elif coord_1[Y] == coord_2[Y]:
				# Path is Horizontal
				ll_corner  = (coord_1[X], coord_1[Y]) if coord_1[X] < coord_2[X] else (coord_2[X], coord_2[Y])
				ur_corner  = (coord_2[X], coord_2[Y]) if coord_1[X] < coord_2[X] else (coord_1[X], coord_1[Y])
				half_width = path.width / 2
				if path.path_type == 2:
					# Square-ended path that extends past endpoints
					ll_corner  = (ll_corner[X] - half_width, ll_corner[Y] - half_width)
					ur_corner  = (ur_corner[X] + half_width, ur_corner[Y] + half_width)
				elif path.path_type == 0:
					# Square-ended path that ends flush
					ll_corner  = (ll_corner[X], ll_corner[Y] - half_width)
					ur_corner  = (ur_corner[X], ur_corner[Y] + half_width)

			# List of Coords -- 5 coords total -- first and last are the same
			x_coords = [ll_corner[X], ur_corner[X], ur_corner[X], ll_corner[X], ll_corner[X]]
			y_coords = [ll_corner[Y], ll_corner[Y], ur_corner[Y], ur_corner[Y], ll_corner[Y]]

			return cls(5, x_coords, y_coords)

	@classmethod
	def from_gdsii_boundary(cls, boundary):
		# Coordinate Indexes
		X = 0
		Y = 1

		# X and Y coords
		x_coords = []
		y_coords = []

		for coord in boundary.xy:
			x_coords.append(coord[X])
			y_coords.append(coord[Y])

		return cls(len(boundary.xy), x_coords, y_coords)

	def plot(self):
		plt.plot(self.x_coords, self.y_coords)
		plt.show()

	def rotate(self, degrees):
		if degrees == 90:
			# 1. Switch X and Y values
			# 2. Multiply the new X values by -1
			for i in range(self.num_coords):
				self.x_coords[i], self.y_coords[i] = self.y_coords[i], self.x_coords[i]
				self.x_coords[i] *= -1
		elif degrees == 180:
			# 1. Multiply X and Y values by -1
			for i in range(self.num_coords):
				self.x_coords[i] *= -1
				self.y_coords[i] *= -1
		elif degrees == 270:
			# 1. Switch X and Y values
			# 2. Multiply the new Y values by -1
			for i in range(self.num_coords):
				self.x_coords[i], self.y_coords[i] = self.y_coords[i], self.x_coords[i]
				self.y_coords[i] *= -1
		else:
			print "UNSUPPORTED %s: rotation of %d degrees not supported." % (inspect.stack()[1][3], degrees)
			sys.exit(3)

	def reflect_across_x_axis(self):
		# 1. Multiply Y values by -1
		for i in range(self.num_coords):
			self.y_coords[i] *= -1

	def shift_x_y(self, offset_x, offset_y):
		for i in range(self.num_coords):
			self.x_coords[i] += offset_x
			self.y_coords[i] += offset_y

	def compute_translations(self, offset_x, offset_y, x_reflection, degrees_rotation):
		if x_reflection == REFLECTION_ABOUT_X_AXIS:
			self.reflect_across_x_axis()
		if degrees_rotation != 0 and degrees_rotation != None:
			self.rotate(degrees_rotation)
		if offset_x != 0 or offset_y != 0:
			self.shift_x_y(offset_x, offset_y)

	def is_point_inside(self, x, y):
		inside    = False
		point_1_x = self.x_coords[0]
		point_1_y = self.y_coords[0]
		for i in range(1, self.num_coords):
			point_2_x = self.x_coords[i]
			point_2_y = self.y_coords[i]
			if y > min(point_1_y, point_2_y) and y <= max(point_1_y, point_2_y):
				if x <= max(point_1_x, point_2_x):
					if point_1_y != point_2_y:
						x_intersection = (y - point_1_y) * (point_2_x - point_1_x) / (point_2_y - point_1_y) + point_1_x
					if point_1_x == point_2_x or x <= x_intersection:
						inside = not inside
			point_1_x, point_1_y = point_2_x, point_2_y
		return inside

	# Returns True if the provided bounding box overlaps the bounding
	# box of the polygon. Otherwise, returns False.
	def overlaps(self, bbox):
		# Check if one box is to the left of another box
		if self.bbox.ur_x < bbox.ll_x or bbox.ur_x < self.bbox.ll_x:
			return False
		# Check if one box is above the other box
		if self.bbox.ur_y < bbox.ll_y or bbox.ur_y < self.bbox.ll_y:
			return False
		return True

