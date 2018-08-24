# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
import debug_prints as dbg

# Other Imports
import inspect
import sys

# Possible ERROR Codes:
# 1 = Error loading input load_files
# 2 = Unknown GDSII object attributes/attribute types
# 3 = Unhandled feature
# 4 = Usage Error

# GDSII Spec. Constants
REFLECTION_ABOUT_X_AXIS = 32768

# Returns True if the Path type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle more than two coordinate pairs
# @TODO: Handle more path_types than just type 2 and 0
def is_path_type_supported(path):
	if len(path.xy) == 2 and path.path_type == 0 or path.path_type == 2 or path.path_type == None or path.path_type == 4:
		return True
	else:
		if len(path.xy) != 2:
			print "UNSUPPORTED %s: number of coordinates (%d) for path object not supported." % (inspect.stack()[1][3], len(path.xy))
		if path.path_type != 0 and path.path_type != 2 and path.path_type != 4:
			print "UNSUPPORTED %s: path type (%d) not supported" % (inspect.stack()[1][3], path.path_type)
		sys.exit(3)

# Returns True if the SRef type is currently supported by 
# this tool. Else, script exits with error code 3.
# @TODO: Handle SRef magnitude and any angle transformations.
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
# @TODO: Handle ARef magnitude and any angle transformations.
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
