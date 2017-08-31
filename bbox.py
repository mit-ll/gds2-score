# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
import debug_prints as dbg

# Other Imports
import inspect
import sys

# GDSII Spec. Constants
REFLECTION_ABOUT_X_AXIS = 32768

class BBox():
	def __init__(self):
		self.ll_x_coord = None
		self.ll_y_coord = None
		self.ur_x_coord = None
		self.ur_y_coord = None

	def __init__(self, ll_x_coord, ll_y_coord, ur_x_coord, ur_y_coord):
		self.ll_x_coord = ll_x_coord
		self.ll_y_coord = ll_y_coord
		self.ur_x_coord = ur_x_coord
		self.ur_y_coord = ur_y_coord

# ------------------------------
# GDSII Element BB Functions
# ------------------------------

# Returns True if the Path type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle more than two coordinate pairs
# @TODO: Handle more path_types than just type 2
def is_path_type_supported(path):
	if len(path.xy) == 2 and path.path_type == 0 or path.path_type == 2 or path.path_type == 4:
		return True
	else:
		if len(path.xy) != 2:
			print "UNSUPPORTED %s: number of coordinates (%d) for path object not supported." % (inspect.stack()[1][3], len(path.xy))
		if path.path_type != 0 and path.path_type != 2 and path.path_type != 4:
			print "UNSUPPORTED %s: path type (%d) not supported" % (inspect.stack()[1][3], path.path_type)
		sys.exit(3)

# Returns True if the Boundary type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle more than five coordinate pairs
def is_boundary_type_supported(boundary):
	if len(boundary.xy) == 5:
		return True
	else:
		print "UNSUPPORTED %s: number of coordinates (%d) for boundary object not supported." % (inspect.stack()[1][3], len(boundary.xy))
		sys.exit(3)

# Returns True if the SRef type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle SRef magnitude and angle transformations.
def is_sref_type_supported(sref, structure):
	supported_strans = [ None, 0, REFLECTION_ABOUT_X_AXIS ]
	supported_angles = [ None, 0, 90, 180, 270 ]
	supported_mags   = [ None ]
	if sref.strans in supported_strans and sref.angle in supported_angles and sref.mag in supported_mags:
		return True
	else:
		dbg.debug_print_sref_obj(sref)
		# dbg.debug_print_gdsii_structure_and_elements(structure)
		print "UNSUPPORTED %s: transformations of SRef object not supported." % (inspect.stack()[1][3])
		sys.exit(3)

# Returns True if the ARef type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle ARef magnitude and angle transformations.
def is_aref_type_supported(aref, structure):
	supported_strans = [ None, 0, REFLECTION_ABOUT_X_AXIS ]
	supported_angles = [ None, 0, 90, 180, 270 ]
	supported_mags   = [ None ]
	if aref.strans in supported_strans and aref.angle in supported_angles and aref.mag in supported_mags:
		return True
	else:
		dbg.debug_print_aref_obj(aref)
		# dbg.debug_print_gdsii_structure_and_elements(structure)
		print "UNSUPPORTED %s: transformations of SRef object not supported." % (inspect.stack()[1][3])
		sys.exit(3)

def compute_gdsii_path_bbox(path):
	# Coordinate Indexes
	X = 0
	Y = 1
	if is_path_type_supported(path):
		coord_1 = path.xy[0]
		coord_2 = path.xy[1]
		
		# @TODO: Handle non-straight paths
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
			elif path.path_type == 4:
				# Custom-ended square-ended path
				ll_corner  = (ll_corner[X] - half_width, ll_corner[Y] - half_width)
				ur_corner  = (ur_corner[X] + half_width, ur_corner[Y] + half_width)
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
			elif path.path_type == 4:
				# Custom-ended square-ended path
				ll_corner  = (ll_corner[X] - half_width, ll_corner[Y] - half_width)
				ur_corner  = (ur_corner[X] + half_width, ur_corner[Y] + half_width)
		
		return BBox(ll_corner[X], ll_corner[Y], ur_corner[X], ur_corner[Y])

def compute_gdsii_boundary_bbox(boundary):
	if is_boundary_type_supported(boundary):
		sorted_coords = sorted(boundary.xy, key=lambda x: (x[0], x[1]))
		return BBox(sorted_coords[0][0], sorted_coords[0][1], sorted_coords[2][0], sorted_coords[2][1])

def reflect_bbox_across_x_axis(bb):
	temp_ur_y_coord = bb.ur_y_coord
	bb.ur_y_coord   = bb.ll_y_coord * -1
	bb.ll_y_coord   = temp_ur_y_coord * -1
	return bb

# Performs counter clockwise rotation of BBox
def rotate_bbox(bb, rotation):
	temp_ll_x = bb.ll_x_coord
	temp_ll_y = bb.ll_y_coord
	temp_ur_x = bb.ur_x_coord
	temp_ur_y = bb.ur_y_coord

	if rotation == 90:
		bb.ll_x_coord = temp_ur_y * -1
		bb.ur_x_coord = temp_ll_y * -1
		bb.ll_y_coord = temp_ll_x
		bb.ur_y_coord = temp_ur_x
	elif rotation == 180:
		bb.ll_x_coord = temp_ur_x * -1
		bb.ll_y_coord = temp_ur_y * -1
		bb.ur_x_coord = temp_ll_x * -1
		bb.ur_y_coord = temp_ll_y * -1
	elif rotation == 270:
		bb.ll_x_coord = temp_ll_y
		bb.ur_x_coord = temp_ur_y
		bb.ll_y_coord = temp_ur_x * -1
		bb.ur_y_coord = temp_ll_x * -1
	else:
		print "UNSUPPORTED %s: rotation of %d degrees not supported." % (inspect.stack()[1][3], rotation)
		sys.exit(3)
	return bb
