# Import Graphviz Library
import pygraphviz as pgv

# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Import Custom Modules
from polygon import *
import lef
import net

# Other Imports
import copy
import time
import sys
import pprint

class Layout():
	def __init__(self):
		self.top_level_name      = None  
		self.lef                 = None
		self.layer_map           = None
		self.gdsii_lib           = None
		self.gdsii_structures    = {}
		self.top_gdsii_structure = None
		self.critical_nets       = None

	def __init__(self, top_name, lef_fname, layer_map_fname, gdsii_fname, dot_fname):
		self.top_level_name      = top_name 
		self.lef                 = lef.LEF(lef_fname)
		self.layer_map           = self.load_layer_map(layer_map_fname)
		self.gdsii_lib           = self.load_gdsii_library(gdsii_fname)
		self.gdsii_structures    = self.index_gdsii_structures_by_name()
		self.top_gdsii_structure = self.gdsii_structures[top_name]
		self.critical_nets       = self.extract_critical_nets_from_gdsii(self.load_dot_file(dot_fname))

	def is_element_nearby(self, element, x_coord, y_coord, threshold_distance, gdsii_layer, offset_x, offset_y, x_reflection, degrees):
		nearby_polygons = []

		if isinstance(element, Path):
			if gdsii_layer == element.layer:
				poly = init_polygon_from_path(element)
				
				# Compute translations if any
				poly.compute_translations(offset_x, offset_y, x_reflection, degrees)
				
				# Check if polygon is nearby
				if poly.is_nearby(x_coord, y_coord, threshold_distance):
					nearby_polygons.append(copy.deepcopy(poly))
		elif isinstance(element, Boundary):
			if gdsii_layer == element.layer:
				poly = init_polygon_from_boundary(element)

				# Compute translations if any
				poly.compute_translations(offset_x, offset_y, x_reflection, degrees)

				# Check if polygon is nearby
				if poly.is_nearby(x_coord, y_coord, threshold_distance):
					nearby_polygons.append(copy.deepcopy(poly))
		elif isinstance(element, SRef):
			# Check if SRef properties are supported by this tool
			# and that the structure pointed to exists.
			if element.struct_name in self.gdsii_structures:
				is_sref_type_supported(element, self.gdsii_structures[element.struct_name])
			else:
				print "ERROR %s: SRef points to unkown structure %s." % (inspect.stack()[1][3], element.struct_name)
				sys.exit(1)

			# Iterate over elements of referenced structure
			for sub_element in self.gdsii_structures[element.struct_name]:
				nearby_polygons.extend(self.is_element_nearby(sub_element, x_coord, y_coord, threshold_distance, gdsii_layer, element.xy[0][0], element.xy[0][1], element.strans, element.angle))
		elif isinstance(element, ARef):
			# Check if SRef properties are supported by this tool
			# and that the structure pointed to exists.
			if element.struct_name in self.gdsii_structures:
				is_aref_type_supported(element, self.gdsii_structures[element.struct_name])
			else:
				print "ERROR %s: ARef points to unkown structure %s." % (inspect.stack()[1][3], element.struct_name)
				sys.exit(1)

			# Retrieve row and column spacing
			curr_x_offset = element.xy[0][0]
			col_spacing   = (element.xy[1][0] - curr_x_offset) / element.cols
			curr_y_offset = element.xy[0][1]
			row_spacing   = (element.xy[2][1] - curr_y_offset) / element.rows

			# Iterate over elements of referenced structures
			for row_index in range(element.rows):
				for col_index in range(element.cols):
					for sub_element in self.gdsii_structures[element.struct_name]:
						nearby_polygons.extend(self.is_element_nearby(sub_element, x_coord, y_coord, threshold_distance, gdsii_layer, curr_x_offset, curr_y_offset, element.strans, element.angle))
					curr_x_offset += col_spacing
				curr_y_offset += row_spacing
		# Ignore GDSII Text elements
		# elif isinstance(element, Text):
		elif isinstance(element, Box):
			print "UNSUPPORTED %s: GDSII Box elements are not supported." % (inspect.stack()[1][3])
			sys.exit(3)
		elif isinstance(element, Node):
			print "UNSUPPORTED %s: GDSII Node elements are not supported." % (inspect.stack()[1][3])
			sys.exit(3)

		return nearby_polygons

	# Extracts a list of GDSII elements (converted to polygon objects)
	# that are in close proimity to a given security-critical net segement.
	# By only examining nearby elements, the runtime of this tool
	# significantly descreases.
	def extract_nearby_elements(self, net_segment, threshold_distance):
		# Check that GDSII library has been loaded
		if self.gdsii_lib == None or self.top_gdsii_structure == None:
			print "ERROR %s: must load GDSII library before indexing GDSII structures." % (inspect.stack()[0][3])
			sys.exit(1)

		nearby_polygons = []
		path_center_x   = net_segment.ur_x_coord - net_segment.ll_x_coord
		path_center_y   = net_segment.ur_y_coord - net_segment.ll_y_coord

		# Find all polygons that are within the threshold distance
		# of the critical GDSII path object.
		for element in self.top_gdsii_structure:
			nearby_polygons.extend(self.is_element_nearby(element, path_center_x, path_center_y, threshold_distance, net_segment.gdsii_path.layer, 0, 0, 0, 0))
		return nearby_polygons

	# Loads GDSII structures elements into a dictionary
	# keyed by structure name to allow for efficient
	# structure object lookups.
	def index_gdsii_structures_by_name(self):
		# Check that GDSII library has been loaded
		if self.gdsii_lib == None:
			print "ERROR %s: must load GDSII library before indexing GDSII structures." % (inspect.stack()[0][3])
			sys.exit(1)

		# Load GDSII structures in a dictionary
		gdsii_structures_index = {}
		for structure in self.gdsii_lib:
			if structure.name not in gdsii_structures_index.keys():
				gdsii_structures_index[structure.name] = structure
			else:
				print "ERROR %s: encountered multiple GDSII structures with the same name (%s)." % (inspect.stack()[0][3], structure.struct_name)
				sys.exit(2)
		return gdsii_structures_index

	# Cross references the critical nets identified with the 
	# Nemo tool, to all path objects declared in the GDSII file.
	# Returns a list containing the critical Net objects.
	def extract_critical_nets_from_gdsii(self, critical_net_names):
		print "Extracting critical GDSII paths (nets)..."
		start_time = time.time()

		critical_nets  = []
		critical_paths = {}

		# Extract path structures from GDSII file
		for structure in self.gdsii_lib:
			if structure.name == self.top_level_name:
				for element in structure:
					if isinstance(element, Path):
						path_name = element.properties[0][1] # property 1 of Path element is the net name
						if path_name in critical_paths:
							critical_paths[path_name].append(element)
						else:
							# Check if path is critical or not
							path_basename = path_name.split('/')[-1]
							if path_basename in critical_net_names.values():
								critical_paths[path_name] = [element]
				break

		# Initialize Net Objects
		for net_name in critical_paths.keys():
			critical_nets.append(net.Net(net_name, critical_paths[net_name], self.lef, self.layer_map))

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return critical_nets

	# Loads nets from a Graphviz dot file.
	# Returns a dictionary of net names in the format:
	# Key<net fullname> --> Value<net basename>
	def load_dot_file(self, dot_fname):
		print "Loading nets from .dot file ..."
		start_time = time.time()

		nets = {}

		# Load critical nets .dot file
		nets_graph = pgv.AGraph(dot_fname)

		# Extract graph node full names
		net_full_names = nets_graph.nodes()

		# Extract base names of graph nodes
		for full_name in net_full_names:
			full_name       = full_name.encode('ascii', 'replace')
			full_name_list  = full_name.split('.')
			base_name 	    = full_name_list[-1]
			nets[full_name] = base_name

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return nets

	# Loads entire circuit layout from GDSII file. 
	# Returns a GDSII library object.
	def load_gdsii_library(self, gdsii_fname):
		print "Loading GDSII file ..."
		start_time = time.time()

		# Open GDSII File
		with open(gdsii_fname, 'rb') as stream:
		    lib = Library.load(stream)

		# Close GDSII File
		stream.close()  

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return lib

	# Loads entire layer map file for technology node. 
	# Returns a dictionary of the following format:
	# Key<gdsii layer number> --> Value< Key<data type> --> Value <layer name> >
	def load_layer_map(self, map_fname):
		print "Loading layer map file ..."
		start_time = time.time()

		layer_map = {}

		# Open GDSII File
		with open(map_fname, 'rb') as stream:
			for line in stream:
				# Do not process comment lines
				if (len(line) > 0) and (line[0] != "#"):
					line = line.rstrip()
					line_list = line.split(' ')

					# Check if layer map file is the correct format
					# Correct Line Format: <Cadence Layer Name> | <layer purpose> | <layer number> | <data type>
					if len(line_list) != 4:
						print "ERROR <load_layer_map>: layer map file format not recognized."
						sys.exit(1)
					cad_layer_name = line_list[0]
					layer_num 	   = int(line_list[2])
					data_type      = int(line_list[3])
					if layer_num not in layer_map:
						layer_map[layer_num] = {data_type: cad_layer_name}
					else:
						if data_type not in layer_map[layer_num]:
							layer_map[layer_num][data_type] = cad_layer_name

		# Close GDSII File
		stream.close()  

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return layer_map
