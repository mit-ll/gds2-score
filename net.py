# Import GDSII Library
from gdsii.elements import *

# Other Imports
import inspect
import sys

class Net():
	def __init__(self):
		self.fullname     = None
		self.basename     = None
		self.num_segments = 0
		self.segments     = []

	def __init__(self, fullname, gdsii_paths, lef, layer_map):
		self.fullname     = fullname
		self.basename     = fullname.split('/')[-1]
		self.num_segments = len(gdsii_paths)
		self.segments     = []

		for path_obj in gdsii_paths:
			self.segments.append(Net_Segment(path_obj, lef, layer_map))

class Net_Segment():
	def __init__(self):
		self.layer_num  = 0
		self.layer_name = None
		self.direction  = None
		self.ll_x_coord = 0
		self.ll_y_coord = 0
		self.ur_x_coord = 0
		self.ur_y_coord = 0
		self.gdsii_path = None

	def __init__(self, gdsii_path, lef, layer_map):
		self.layer_num  = lef.get_layer_num(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.layer_name = lef.get_layer_name(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.direction  = self.path_direction(gdsii_path)
		self.ll_x_coord = self.compute_gdsii_path_bb(gdsii_path)[0][0]
		self.ll_y_coord = self.compute_gdsii_path_bb(gdsii_path)[0][1]
		self.ur_x_coord = self.compute_gdsii_path_bb(gdsii_path)[1][0]
		self.ur_y_coord = self.compute_gdsii_path_bb(gdsii_path)[1][1]
		self.gdsii_path = gdsii_path

	def get_width(self):
		return self.gdsii_path.width

	# Returns True if the Path type is currently supported by 
	# this tool. Else, script exits with error code 3.
	# @TODO: Handle more than two coordinate pairs
	# @TODO: Handle more path_types than just type 2
	def is_path_type_supported(self, gdsii_path):
		if len(gdsii_path.xy) == 2 and gdsii_path.path_type == 2:
			return True
		else:
			if len(gdsii_path.xy) != 2:
				print "UNSUPPORTED %s: number of coordinates (%d) for path object not supported." % (inspect.stack()[1][3], len(gdsii_path.xy))
			if gdsii_path.path_type != 2:
				print "UNSUPPORTED %s: path type (%d) not supported" % (inspect.stack()[1][3], gdsii_path.path_type)
			sys.exit(3)

	# Computes the bounding box of a GDSII path object. Returns
	# the bounding box in the form of a LL and UR pair of coordinates
	# formatted as follows: [(LL_x, LL_y), (UR_x, UR_y)]. 
	def compute_gdsii_path_bb(self, gdsii_path):
		# Coordinate Indexes
		X = 0
		Y = 1

		if self.is_path_type_supported(gdsii_path):
			coord_1 = gdsii_path.xy[X]
			coord_2 = gdsii_path.xy[Y]
			
			# @TODO: Handle non-straight paths
			if self.path_direction(gdsii_path) == "V":
				# Path is Vertical
				ll_corner = (coord_1[X], coord_1[Y]) if coord_1[Y] < coord_2[Y] else (coord_2[X], coord_2[Y])
				ur_corner = (coord_2[X], coord_2[Y]) if coord_1[Y] < coord_2[Y] else (coord_1[X], coord_1[Y])
			else:
				# Path is Horizontal
				ll_corner = (coord_1[X], coord_1[Y]) if coord_1[X] < coord_2[X] else (coord_2[X], coord_2[Y])
				ur_corner = (coord_2[X], coord_2[Y]) if coord_1[X] < coord_2[X] else (coord_1[X], coord_1[Y])
			
			# Adjust LL and UR Coords for path type
			half_width = gdsii_path.width / 2
			ll_corner = (ll_corner[X] - half_width, ll_corner[Y] - half_width)
			ur_corner = (ur_corner[X] + half_width, ur_corner[Y] + half_width)
		
		return [ll_corner, ur_corner]

	# Returns the direction of the path object. Returns "V" for 
	# a Vertical path and "H" for a horizontal path. Script exits
	# with error code 3 if path direction is unknown.
	def path_direction(self, gdsii_path):
		coord_1 = gdsii_path.xy[0]
		coord_2 = gdsii_path.xy[1]

		if coord_1[0] == coord_2[0]:
			return "V"
		elif coord_1[1] == coord_2[1]:
			return "H"
		else:
			print "UNSUPPORTED %s: non-straight paths not supported." % (inspect.stack()[1][3])
			sys.exit(3)