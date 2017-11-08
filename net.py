# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from polygon import *

# Other Imports
import inspect
import sys
# from multiprocessing import Lock

class Net():
	def __init__(self, fullname, gdsii_paths, lef, layer_map):
		self.fullname     = fullname
		self.basename     = fullname.split('/')[-1]
		self.num_segments = len(gdsii_paths)
		self.segments     = []

		for path_obj in gdsii_paths:
			self.segments.append(Net_Segment(path_obj, lef, layer_map))

class Net_Segment():
	def __init__(self, gdsii_path, lef, layer_map):
		self.gdsii_path         = gdsii_path
		self.layer_num          = lef.get_layer_num(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.layer_name         = lef.get_layer_name(gdsii_path.layer, gdsii_path.data_type, layer_map)
		self.direction          = self.path_direction()
		self.polygon            = Polygon.from_gdsii_path(gdsii_path)
		self.bbox               = BBox.from_polygon(self.polygon)
		self.nearby_bbox        = BBox.from_bbox_and_extension(self.bbox, (2 * (self.gdsii_path.width + self.bbox.length)))
		self.nearby_sl_polygons = [] # nearby polygons on the same layer
		self.nearby_al_polygons = [] # nearby polygons on above layer
		self.nearby_bl_polygons = [] # nearby polygons on below layer

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

