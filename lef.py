# Other Imports
import sys
import time
import pprint

class LEF:
	def __init__(self, lef_fname):
		self.database_units     = 0
		self.manufacturing_grid = 0
		self.layers             = {}
		self.load_lef_file(lef_fname)

	def load_lef_file(self, lef_fname):
		print "Loading LEF file ..."
		start_time = time.time()

		layer_index = 1
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
											print "ERROR <LEF.load_lef_file>: Routing layer direction not recognized."
											sys.exit(1)
									elif "PITCH" in line_list:
										pitch = float(line_list[1])
									elif "OFFSET" in line_list:
										offset = float(line_list[1])
									elif "MINWIDTH" in line_list:
										min_width = float(line_list[1])
									elif "MAXWIDTH" in line_list:
										max_width = float(line_list[1])
									elif "WIDTH" in line_list:
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
									line = stream.next().rstrip(' ;\n').lstrip()
								self.layers[layer_name] = Routing_Layer(layer_name, layer_index, direction, pitch, offset, min_width, max_width, width, spacing)
								layer_index += 1
							# Via Layer
							# elif "CUT" in layer_type:

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
				return None
			else:
				return layer_map[gds_layer_num][gds_data_type]

	# Returns the logical layer number associated with a given 
	# GDSII layer number and data type.
	def get_layer_num(self, gds_layer_num, gds_data_type, layer_map):
		layer_name = self.get_layer_name(gds_layer_num, gds_data_type, layer_map)
		return self.layers[layer_name].layer_num

	# Returns the True if the GDSII layer number is ABOVE the 
	# reference GDSII layer number.
	def is_gdsii_layer_above_below(self, ref_gds_element, gds_element, layer_map):
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
		
		if abs(ref_layer_num - layer_num) == 1:
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
	def __init__(self, name, num, direction, pitch, offset, min_width, max_width, width, spacing):
		self.name      = name
		self.layer_num = num
		self.direction = direction
		self.pitch     = pitch
		self.offset    = offset
		self.min_width = min_width
		self.max_width = max_width
		self.width     = width
		self.spacing   = spacing
		# self.area
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