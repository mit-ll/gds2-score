# Import Custom Modules
from polygon import *

# Other Imports
import sys
import inspect
import time
import pprint
import copy

class LEF:
	def __init__(self, metal_stack_lef_fname, std_cell_lef_name):
		self.database_units     = 0
		self.manufacturing_grid = 0
		self.layers             = {} # Maps layer name to layer object (only Routing_Layer)
		self.placement_sites    = {} # Maps placement site name to placement site object
		self.standard_cells     = {} # Maps standard cell name to standard cell object
		self.fill_cells         = {} # Maps fill cell name to standard cell object
		self.top_routing_layer_num    = 0
		self.bottom_routing_layer_num = 1
		
		# Load LEF files
		self.load_metal_stack_lef_file(metal_stack_lef_fname)
		self.load_standard_cell_lef_file(std_cell_lef_name)

	def load_metal_stack_lef_file(self, lef_fname):
		print "Loading Metal Stack LEF file ..."
		start_time = time.time()

		self.top_routing_layer_num = 0
		# Open LEF File
		with open(lef_fname, 'rb') as stream:
			for line in stream:
				line = line.rstrip(' ;\n').lstrip()
				# Do not process comment lines
				if (len(line) > 0) and (line[0] != "#"):
					line_list = line.split(' ')
					# Ignore PROPERTYDEFINITIONS ... for now
					if "PROPERTYDEFINITIONS" in line_list:
						line = stream.next().rstrip(' ;\n').lstrip()
						while "END" not in line:
							line = stream.next().rstrip(' ;\n').lstrip()
					# Database units factor
					elif "UNITS" in line_list:
						line = stream.next().rstrip(' ;\n').lstrip()
						while "END" not in line:
							if "DATABASE MICRONS" in line:
								line_list = line.split(' ')
								self.database_units = int(line_list[2])
							line = stream.next().rstrip(' ;\n').lstrip()
					# Manufacturing grid resolution
					elif "MANUFACTURINGGRID" in line_list:
						self.manufacturing_grid = float(line_list[1])
					# Routing/Via Layers
					elif "LAYER" in line_list:
						layer_name = line_list[1].rstrip(' ')
						line = stream.next().rstrip(' ;\n').lstrip()
						if "TYPE" in line:
							line_list  = line.split(' ')
							layer_type = line_list[1].rstrip('; ')
							# Routing Layer
							if "ROUTING" in layer_type:
								direction = None
								pitch     = None
								offset    = None
								min_width = None
								max_width = None
								width     = None 
								area      = None
								spacing   = []

								line = stream.next().rstrip(' ;\n').lstrip()
								while "END" not in line:
									line_list = line.split(' ')
									if "DIRECTION" in line:
										if "VERTICAL" in line:
											direction = "V"
										elif "HORIZONTAL" in line:
											direction = "H"
										else:
											print "ERROR %s: Routing layer direction not recognized." % (inspect.stack()[0][3])
											sys.exit(1)
									elif "PITCH" in line_list:
										pitch = float(line_list[1])
									elif "OFFSET" in line_list:
										offset = float(line_list[1])
									elif "MINWIDTH" in line_list:
										min_width = float(line_list[1])
									elif "MAXWIDTH" in line_list:
										max_width = float(line_list[1])
									elif "WIDTH" in line_list and "MIN" not in line and "MAX" not in line:
										width = float(line_list[1])
									elif "SPACING" in line_list:
										line_list.pop(0)
										space_val = float(line_list.pop(0))
										spacing.append([space_val])
										while len(line_list) != 0:
											token = line_list.pop(0)
											if "RANGE" in token:
												range_min = float(line_list.pop(0))
												range_max = float(line_list.pop(0))
												spacing[-1].append((range_min, range_max))
											else:
												# TODO: Handle additional spacing Rules: http://edi.truevue.org/edi/14.17/lefdefref/LEFSyntax.html#UsingSpacingRules
												print "UNSUPPORTED %s: spacing rules (%s) not supported." % (inspect.stack()[0][3], token)
												sys.exit(3)
									elif "AREA" in line_list:
										area = float(line_list[1])
									line = stream.next().rstrip(' ;\n').lstrip()
								self.top_routing_layer_num += 1
								# Map routing layer NAME to routing layer object
								self.layers[layer_name] = Routing_Layer(layer_name, self.top_routing_layer_num, direction, pitch, offset, min_width, max_width, width, spacing, self.database_units, area)
								# Map logical routing layer NUMBER to routing layer object
								self.layers[self.top_routing_layer_num] = self.layers[layer_name]
								
							# Via Layer
							# elif "CUT" in layer_type:
					# Placement Site Definitions
					elif "SITE" in line_list:
						# Site Values
						name        = None
						site_class  = None
						dimension_x = 0
						dimension_y = 0
						symmetry    = None
						line = line.rstrip(' ;\n').lstrip()
						name = line.split(' ')[-1]
						line = stream.next().rstrip(' ;\n').lstrip()
						while "END" not in line:
							if "CLASS" in line:
								line_list = line.split(' ')
								site_class = line_list[-1]
							elif "SIZE" in line:
								line_list = line.split(' ')
								dimension_x = float(line_list[1]) * self.database_units
								dimension_y = float(line_list[3]) * self.database_units
							elif "SYMMETRY" in line:
								line_list = line.split(' ')
								symmetry  = line_list[-1]
							line = stream.next().rstrip(' ;\n').lstrip()
						self.placement_sites[name] = PlacementSite(name, site_class, Point(dimension_x, dimension_y), symmetry)

		# Close LEF File
		stream.close()

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return

	def load_standard_cell_lef_file(self, lef_fname):
		print "Loading Standard Cell LEF file ..."
		start_time = time.time()

		# Check that metal stack LEF file has already been loaded
		if not self.layers and not self.placement_sites:
			print "ERROR %s: must load metal stack LEF file prior to loading std cell LEF file." % (inspect.stack()[0][3])
			sys.exit(1)

		# Open LEF File
		with open(lef_fname, 'rb') as stream:
			for line in stream:
				line = line.rstrip(' ;\n').lstrip()
				# Do not process comment lines
				if (len(line) > 0) and (line[0] != "#"):
					line_list = line.split(' ')
					# Ignore PROPERTYDEFINITIONS ... for now
					if "MACRO" in line_list:
						std_cell_name = line_list[-1]
						is_fill_cell  = False
						line = stream.next().rstrip(' ;\n').lstrip()
						while not ("END" in line and std_cell_name in line):
							if "CLASS" in line:
								# Check if Fill Cell or Not
								if "SPACER" in line:
									is_fill_cell = True
								else:
									is_fill_cell = False
							if "SIZE" in line:
								size_line_list = line.split(' ')
								if not is_fill_cell and std_cell_name not in self.standard_cells:
									self.standard_cells[std_cell_name] = StandardCell(std_cell_name, float(size_line_list[1]) * self.database_units, float(size_line_list[-1]) * self.database_units)
								elif is_fill_cell and std_cell_name not in self.fill_cells:
									self.fill_cells[std_cell_name] = StandardCell(std_cell_name, float(size_line_list[1]) * self.database_units, float(size_line_list[-1]) * self.database_units)
										
							line = stream.next().rstrip(' ;\n').lstrip()
		
		# Close LEF File
		stream.close()

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return

	# Returns the layer name associated with a given 
	# GDSII layer number and data type.
	def get_layer_name(self, gds_layer_num, gds_data_type, layer_map):
		if gds_layer_num not in layer_map:
			return None
		else:
			if gds_data_type not in layer_map[gds_layer_num]:
				# Just grab an aribitrary layer name
				# TODO: Fix this?
				return layer_map[gds_layer_num].itervalues().next()
			else:
				return layer_map[gds_layer_num][gds_data_type]

	# Returns the logical layer number associated with a given 
	# GDSII layer number and data type. Returns -1 if layer is not
	# a ROUTING layer, i.e. layer is a DEVICE or VIA layer.
	def get_layer_num(self, gds_layer_num, gds_data_type, layer_map):
		layer_name = self.get_layer_name(gds_layer_num, gds_data_type, layer_map)
		if layer_name in self.layers:
			return self.layers[layer_name].layer_num
		else:
			return -1

	# Returns the True if the GDSII layer number is BELOW the 
	# reference GDSII layer number.
	def is_gdsii_layer_below(self, ref_gds_element, gds_element, layer_map):
		# Get Logical Layer Num of Reference Layer
		ref_gds_element_layer_name = self.get_layer_name(ref_gds_element.layer, ref_gds_element.data_type, layer_map)
		# @TODO -- fix this by loading layer map with layer nums from 
		# stdcell GDSII file as well as layer map.
		if ref_gds_element_layer_name == None:
			return False
		ref_layer_num = self.layers[ref_gds_element_layer_name].layer_num 
		
		# Get Logical Layer Num of Layer in Question
		gds_element_layer_name = self.get_layer_name(gds_element.layer, gds_element.data_type, layer_map) 
		# @TODO -- fix this by loading layer map with layer nums from 
		# stdcell GDSII file as well as layer map.
		if gds_element_layer_name == None or gds_element_layer_name not in self.layers:
			return False
		layer_num = self.layers[gds_element_layer_name].layer_num 
		
		if ref_layer_num - layer_num == 1:
			return True
		return False

	# Returns the True if the GDSII layer number is ABOVE the 
	# reference GDSII layer number.
	def is_gdsii_layer_above(self, ref_gds_element, gds_element, layer_map):
		# Get Logical Layer Num of Reference Layer
		ref_gds_element_layer_name = self.get_layer_name(ref_gds_element.layer, ref_gds_element.data_type, layer_map)
		# @TODO -- fix this by loading layer map with layer nums from 
		# stdcell GDSII file as well as layer map.
		if ref_gds_element_layer_name == None:
			return False
		ref_layer_num = self.layers[ref_gds_element_layer_name].layer_num 
		
		# Get Logical Layer Num of Layer in Question
		gds_element_layer_name = self.get_layer_name(gds_element.layer, gds_element.data_type, layer_map) 
		# @TODO -- fix this by loading layer map with layer nums from 
		# stdcell GDSII file as well as layer map.
		if gds_element_layer_name == None or gds_element_layer_name not in self.layers:
			return False
		layer_num = self.layers[gds_element_layer_name].layer_num 
		
		if ref_layer_num - layer_num == -1:
			return True
		return False

	# Returns the preferred routing direction for the GDSII layer number
	# and data type according to what is defined in the intput LEF file.
	def get_routing_layer_direction(self, gds_layer_num, gds_data_type, layer_map):
		layer_name = self.get_layer_name(gds_layer_num, gds_data_type, layer_map)
		return self.layers[layer_name].direction

	def debug_print_attrs(self):
		print "LEF File Definitions:"
		print "	DATABASE UNITS:     %5d"  % (self.database_units)
		print "	MANUFACTURING GRID: %.4f" % (self.manufacturing_grid)
		for layer in sorted(self.layers.values(), key=lambda x:x.layer_num):
			layer.debug_print_attrs()
		return

class Routing_Layer:
	def __init__(self, name, num, direction, pitch, offset, min_width, max_width, width, spacing, db_units, area):
		self.name        = name
		self.layer_num   = num
		self.direction   = direction
		self.pitch       = pitch
		self.offset      = offset
		self.min_width   = min_width
		self.max_width   = max_width
		self.width       = width
		self.spacing     = spacing
		self.area        = area
		self.min_spacing_db = spacing[0][0] * db_units # Database units
		if min_width:
			self.min_width_db   = min_width * db_units     # Database units
		else:
			self.min_width_db   = width * db_units     # Database units
		if self.min_spacing_db.is_integer() and self.min_width_db.is_integer():
			self.min_spacing_db = int(self.min_spacing_db)
			self.min_width_db   = int(self.min_width_db)
		else:
			print "Min Spacing DB",   self.min_spacing_db,   self.min_spacing_db.is_integer()
			print "Min Width DB",     self.min_width_db,     self.min_width_db.is_integer()
			print "ERROR %s: spacing and/or widths not integer multiple of DB units." % (inspect.stack()[0][3])
			sys.exit(1)
		self.rogue_wire_width = int(self.min_width_db + (2 * self.spacing[0][0] * db_units)) - 2 # Database units
		# self.min_enclosed_area
		# self.min_density
		# self.max_density
		# self.density_check_window
		# self.density_check_step
		# self.min_cut

	def debug_print_attrs(self):
		print "	ROUTING Layer:"
		print "		NAME:      ", self.name
		print "		NUMBER:    ", self.layer_num
		print "		DIRECTION: ", self.direction
		if self.pitch:
			print "		PITCH:      %.4f" % (self.pitch)
		if self.offset:
			print "		OFFSET:     %.4f" % (self.offset)
		if self.min_width:
			print "		MINWIDTH:   %.4f" % (self.min_width)
		if self.max_width:
			print "		MAXWIDTH:   %.4f" % (self.max_width)
		if self.width:
			print "		WIDTH:      %.4f" % (self.width)
		for spacing_val in self.spacing:
			print "		SPACING:    %.4f" % (spacing_val[0]),
			for range_val in spacing_val[1:-1]:
				print "RANGE %.4f %.4f" % (range_val[0], range_val[1])

class Via_Layer:
	def __init__(self, spacing):
		self.spacing = spacing

	def debug_print_attrs(self):
		return

# Placement site as defined in the metal stack LEF file.
class PlacementSite():
	def __init__(self, name, site_class, dim, symmetry):
		self.name       = name
		self.site_class = site_class
		self.dimension  = dim # Point object in database units
		self.symmetry   = symmetry

	def debug_print_attrs(self):
		print "	NAME:", self.name
		print "		CLASE:   ", self.site_class
		print "		SYMMETRY:", self.symmetry
		print "		WIDTH:   ", self.dimension.x
		print "		HEIGHT:  ", self.dimension.y

# Standard cell site as defined in the standard cell LEF file.
class StandardCell():
	def __init__(self, name, width, height):
		self.name         = name
		self.width        = width  # in database units
		self.height       = height # in database units

	def debug_print_attrs(self):
		print "	NAME:", self.name
		print "		WIDTH: ", self.width
		print "		HEIGHT:", self.height
