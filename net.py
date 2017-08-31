# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from bbox import *

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
		self.gdsii_path = None
		self.layer_num  = 0
		self.layer_name = None
		self.direction  = None
		self.ll_x_coord = 0
		self.ll_y_coord = 0
		self.ur_x_coord = 0
		self.ur_y_coord = 0

	def __init__(self, gdsii_path, lef, layer_map):
		self.gdsii_path = gdsii_path
		self.layer_num  = lef.get_layer_num(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.layer_name = lef.get_layer_name(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.direction  = self.path_direction()
		self.ll_x_coord = compute_gdsii_path_bbox(gdsii_path).ll_x_coord
		self.ll_y_coord = compute_gdsii_path_bbox(gdsii_path).ll_y_coord
		self.ur_x_coord = compute_gdsii_path_bbox(gdsii_path).ur_x_coord
		self.ur_y_coord = compute_gdsii_path_bbox(gdsii_path).ur_y_coord

	def get_bbox(self):
		return [(self.ll_x_coord, self.ll_y_coord), (self.ur_x_coord, self.ur_y_coord)]

	def get_width(self):
		return self.gdsii_path.width

	# Returns the direction of the path object. Returns "V" for 
	# a Vertical path and "H" for a horizontal path. Script exits
	# with error code 3 if path direction is unknown.
	def path_direction(self):
		coord_1 = self.gdsii_path.xy[0]
		coord_2 = self.gdsii_path.xy[1]

		if coord_1[0] == coord_2[0]:
			return "V"
		elif coord_1[1] == coord_2[1]:
			return "H"
		else:
			print "UNSUPPORTED %s: non-straight paths not supported." % (inspect.stack()[1][3])
			sys.exit(3)

