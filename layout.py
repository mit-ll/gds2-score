# Import GDSII Library
from gdsii.library import Library
from gdsii.elements import *

# Import Custom Modules
import debug_prints as dbg
from polygon import *
from LEF     import *
from DEF     import *
from net     import *
from error   import *

# Other Imports
import copy
import time
import sys
import inspect
import pdb
import os
import itertools
import multiprocessing as mp
import functools as ft

class Layout():
	def __init__(self, top_name, metal_stack_lef_fname, std_cell_lef_name, def_fname, layer_map_fname, gdsii_fname, dot_fname, wire_rpt_fname, pg_filename, nb_step, nb_type, num_processes):
		self.top_level_name      = top_name 
		self.device_layer_nums   = {}
		self.lef                 = LEF(metal_stack_lef_fname, std_cell_lef_name)
		self.layer_map           = self.load_layer_map(layer_map_fname)
		self.wire_stats          = self.load_wire_statistics(wire_rpt_fname)
		self.gdsii_lib           = self.load_gdsii_library(gdsii_fname)
		self.gdsii_structures    = self.index_gdsii_structures_by_name()
		self.top_gdsii_structure = self.gdsii_structures[top_name]
		self.critical_nets       = self.extract_critical_nets_from_gdsii(self.load_dot_file(dot_fname))
		self.def_info            = DEF(def_fname, self.lef, self.lef.fill_cells.keys(), pg_filename, self.critical_nets, self.lef)
		self.net_blockage_step   = nb_step # in database units
		self.net_blockage_type   = nb_type # 0 for un-constrained; 1 for LEF constrained
		self.num_processes       = num_processes
		self.net_blockage_done   = False
		self.trigger_space_done  = False
		self.route_distance_done = False
		self.trigger_spaces      = None

	def generate_polys_from_element(self, element, srefs_to_ignore={}):
		polys = []
		if isinstance(element, SRef):
			# Check if SRef is to be ignored (i.e. fill cells)
			if element.struct_name not in srefs_to_ignore:
				# Check if SRef properties are supported by this tool
				# and that the structure pointed to exists.
				if element.struct_name in self.gdsii_structures:
					is_sref_type_supported(element, self.gdsii_structures[element.struct_name])
				else:
					print "ERROR %s: SRef points to unkown structure %s." % (inspect.stack()[1][3], element.struct_name)
					sys.exit(1)

				# Iterate over elements of referenced structure
				for sub_element in self.gdsii_structures[element.struct_name]:
					sub_polys = self.generate_polys_from_element(sub_element)
					
					# Compute translations of sub elements
					for poly in sub_polys:
						poly.compute_translations(element.xy[0][0], element.xy[0][1], element.strans, element.angle)
						polys.append(copy.copy(poly))
		elif isinstance(element, ARef):
			# Check if ARef properties are supported by this tool
			# and that the structure pointed to exists.
			if element.struct_name in self.gdsii_structures:
				is_aref_type_supported(element, self.gdsii_structures[element.struct_name])
			else:
				print "ERROR %s: ARef points to unkown structure %s." % (inspect.stack()[1][3], element.struct_name)
				sys.exit(1)

			# Retrieve row and column spacing
			row_spacing_vector_length = Point.from_tuple(element.xy[0]).distance_from(Point.from_tuple(element.xy[2]))
			col_spacing_vector_length = Point.from_tuple(element.xy[0]).distance_from(Point.from_tuple(element.xy[1]))
			curr_x_offset = 0.0
			col_spacing   = col_spacing_vector_length / element.cols
			curr_y_offset = 0.0
			row_spacing   = row_spacing_vector_length / element.rows

			# Iterate over elements of referenced structures
			for row_index in range(element.rows):
				for col_index in range(element.cols):
					for sub_element in self.gdsii_structures[element.struct_name]:
						# Generate polygons from all sub elements
						sub_polys = self.generate_polys_from_element(sub_element)

						# Compute translations of newly generated polygons
						for poly in sub_polys:
							poly.compute_translations(curr_x_offset, curr_y_offset, None, None)
							polys.append(copy.copy(poly))
					curr_x_offset += col_spacing
				curr_x_offset = 0.0
				curr_y_offset += row_spacing
			# Compute overall translation of ARef element polygons
			for poly in polys:				
				poly.compute_translations(element.xy[0][0], element.xy[0][1], element.strans, element.angle)
		elif isinstance(element, Path) or isinstance(element, Boundary):
			# BASE CASE
			# Compute polygon from element
			if isinstance(element, Path):
				# Element is a Path object
				polys.append(Polygon.from_gdsii_path(element))
			else:
				# Element is a Boundary object
				polys.append(Polygon.from_gdsii_boundary(element))
		# Ignore GDSII Text elements
		# elif isinstance(element, Text):
		elif isinstance(element, Box):
			print "UNSUPPORTED %s: GDSII Box elements are not supported." % (inspect.stack()[1][3])
			sys.exit(3)
		elif isinstance(element, Node):
			print "UNSUPPORTED %s: GDSII Node elements are not supported." % (inspect.stack()[1][3])
			sys.exit(3)
		return polys

	# Generates a list of polygons on the device layer(s).
	# The fill cells are ignored. Device layers must be defined
	# per process technology.
	def generate_device_layer_polys(self):
		for element in self.top_gdsii_structure:
			device_layer_polys = []
			polys = self.generate_polys_from_element(element)
			for poly in polys:
				if poly.gdsii_element.layer < self.first_metal_layer:
					device_layer_polys.append(copy.copy(poly))
			yield device_layer_polys

	def update_layout_bbox(self, poly):
		# Update UR x-coord
		if max(poly.get_x_coords()) > self.bbox.ur.x:
			self.bbox.ur.x = max(poly.get_x_coords())
		
		# Update UR y-coord
		if max(poly.get_y_coords()) > self.bbox.ur.y:
			self.bbox.ur.y = max(poly.get_y_coords())
		
		# Update LL x-coord
		if min(poly.get_x_coords()) < self.bbox.ll.x:
			print "ERROR: ASIC core LL corner should not be less than (0, 0)."
			sys.exit(1)
			self.bbox.ll.x = min(poly.get_x_coords())
		
		# Update LL y-coord
		if min(poly.get_y_coords()) < self.bbox.ll.y:
			print "ERROR: ASIC core LL corner should not be less than (0, 0)."
			sys.exit(1)
			self.bbox.ll.y = min(poly.get_y_coords())

	# Computes the minimum bounding box of the Layout.
	# Can also get layout/die dimensions from the DEF file.
	def compute_layout_bbox(self):
		start_time = time.time()
		print "Computing layout grid bounding box ..."
		print "Number of Top-Level GDSII Elements:", len(self.top_gdsii_structure)

		for element in self.top_gdsii_structure:
			polys = self.generate_polys_from_element(element)
			for poly in polys:
				self.update_layout_bbox(poly)

		print "Bounding Box of Layout (man. units):"
		print self.bbox.get_bbox_as_list()
		print "Bounding Box of Layout (microns):"
		print self.bbox.get_bbox_as_list_microns(1.0 / self.lef.database_units)
		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"

	# Checks if a polygon is nearby a net_segment,
	# i.e. the polygon intersects the net_segments 
	# "nearby" bounding box.
	def is_polygon_nearby(self, net_segment, poly):
		if net_segment.polygon.gdsii_element.layer == poly.gdsii_element.layer:
			
			# Element on the same layer as net_segment
			if poly.overlaps_bbox(net_segment.nearby_sl_bbox):
				net_segment.nearby_sl_polygons.append(poly)

		elif self.lef.is_gdsii_layer_above(net_segment.polygon.gdsii_element, poly.gdsii_element, self.layer_map):
			
			# Element is one layer above the net_segment.
			# Element is only considered "nearby" if it insects with the
			# bounding box of the path object projected one layer above.
			if poly.overlaps_bbox(net_segment.nearby_al_bbox):
				net_segment.nearby_al_polygons.append(poly)

		elif self.lef.is_gdsii_layer_below(net_segment.polygon.gdsii_element, poly.gdsii_element, self.layer_map):
			
			# Element is either one layer below the net_segment.
			# Element is only considered "nearby" if it insects with the
			# bounding box of the path object projected one layer below.
			if poly.overlaps_bbox(net_segment.nearby_bl_bbox):
				net_segment.nearby_bl_polygons.append(poly)

	# Extracts a list of GDSII elements (converted to polygon objects) that are in close
	# proimity to a given security-critical net segement. This is doen by finding all 
	# polygons that overlap the nearby-bounding-box of the critical net_segment object.
	# By only examining nearby elements, the runtime of this tool significantly descreases.
	def extract_nearby_polygons(self):
		start_time = time.time()
		print "Extracting polygons near critical nets ..."

		for element in self.top_gdsii_structure:
			polys = self.generate_polys_from_element(element)
			for net in self.critical_nets:
				for net_segment in net.segments:
					for poly in polys:
						self.is_polygon_nearby(net_segment, poly)

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"

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
					if element.properties and isinstance(element, Path): # <-- for only analyzing PATHS not BOUNDARIES (vias)
						net_name = element.properties[0][1] # property 1 of Path element is the net name
						if net_name in critical_paths:
							critical_polys = self.generate_polys_from_element(element)
							critical_paths[net_name].extend(critical_polys)
						else:
							# Check if path is critical or not
							path_basename = net_name.split('/')[-1].split('[')[0]
							if path_basename in critical_net_names.values():
								critical_polys = self.generate_polys_from_element(element)
								critical_paths[net_name] = critical_polys
				break

		# Initialize Net Objects
		for net_name in critical_paths.keys():
			critical_nets.append(Net(net_name, critical_paths[net_name], self.lef, self.layer_map))

		# Print out security critical nets extracted from GDSII
		print
		print "Security critical nets extracted from GDSII:"
		for net in critical_nets:
			print "%s -- (%d segments)" % (net.fullname, net.num_segments)
		print

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return critical_nets

	# Loads nets from a Graphviz dot file using pygraphviz module.
	# Returns a dictionary of net names in the format:
	# Key<net fullname> --> Value<net basename>
	def load_dot_file_with_pgv(self, dot_fname):
		# Import Graphviz Library
		import pygraphviz as pgv

		print "Loading nets from .dot file ..."
		start_time = time.time()

		nets = {}

		# Load critical nets .dot file
		nets_graph = pgv.AGraph(dot_fname)

		# Extract graph node full names
		net_full_names = nets_graph.nodes()

		# Extract base names of graph nodes
		for full_name in net_full_names:
			print full_name
			full_name       = full_name.encode('ascii', 'replace')
			# print full_name
			full_name_list  = full_name.split('.')
			base_name 	    = full_name_list[-1]
			nets[full_name] = base_name

		# Print out security critical nets extracted from GDSII
		print
		print "Security critical nets extracted from DOT:"
		for net_full_name in nets.keys():
			print "%s --> %s" % (net_full_name, nets[net_full_name])
		print

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return nets

	# Loads nets from a Graphviz dot file with basic parsing.
	# Note this is more flexible than method above as it 
	# does not require an installation of Graphiv and the PGV module.
	# Returns a dictionary of net names in the format:
	# Key<net fullname> --> Value<net basename>
	def load_dot_file(self, dot_fname):
		print "Loading nets from .dot file ..."
		start_time = time.time()

		nets           = {}
		net_full_names = []

		# Open LEF File
		with open(dot_fname, 'rb') as stream:
			for line in stream:
				line = line.rstrip(' \n').lstrip('	\"')
				if "->" in line or "{" in line or "}" in line:
					continue
				else:
					line_list = line.split('\"')
					net_full_names.append(copy.copy(line_list[0]))
		stream.close()

		# Extract base names of graph nodes
		for full_name in net_full_names:
			full_name_list  = full_name.split('.')
			base_name 	    = full_name_list[-1]
			nets[full_name] = base_name

		# Print out security critical nets extracted from GDSII
		print
		print "Security critical nets extracted from DOT:"
		for net_full_name in nets.keys():
			print "%s --> %s" % (net_full_name, nets[net_full_name])
		print

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

		# Show GDSII Stats
		print
		dbg.debug_print_gdsii_stats(lib)
		print

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
				line = line.rstrip()
				if (len(line) > 0) and (line[0] != "#"):
					line_list = line.split()
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

	def load_wire_statistics(self, fname):
		net_mean   = 0.0
		net_sigma  = 0.0
		conn_mean  = 0.0
		conn_sigma = 0.0

		start_time = time.time()
		print "Extracting wire length statistics..."

		with open(fname, 'rb') as stream:
			for line in stream:
				line = line.rstrip(' \n').lstrip(' \t')
				# Parse Net Length Stats
				if 'Avg net length' in line:
					line = line.split(' = ')
					net_mean  = float(line[1].rstrip(' (sigma'))
					net_sigma = float(line[2].rstrip(')'))
					print "Net Length Avg:       ", net_mean
					print "Net Length Stdv:      ", net_sigma
				# Parse Connection Length Stats
				elif 'Avg connection length' in line:
					line = line.split(' = ')
					conn_mean  = float(line[1].rstrip(' (sigma'))
					conn_sigma = float(line[2].rstrip(')'))
					print "Connection Length Avg:", conn_mean
					print "Connection Stdv:      ", conn_sigma

		stream.close()

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"

		return WireStats(net_mean, net_sigma, conn_mean, conn_sigma)

class WireStats():
	def __init__(self, n_mean, n_stdv, c_mean, c_stdv):
		self.net_sigma        = n_mean
		self.net_mean         = n_stdv
		self.connection_sigma = c_mean
		self.connection_mean  = c_stdv

class TriggerSpaces():
	def __init__(self, size):
		self.size    = size # Number of 4-connected placement sites
		self.freq    = 0    # Frequency of same size trigger spaces
		self.spaces  = []   # List of sets of Point objects comprising a single trigger space
		self.net_segment_2_sites = {} # maps net segments to closest trigger space sites

class TriggerSpace():
	def __init__(self, i, coords, md):
		self.spaces_index       = i      # Index into parent object TriggerSpace.spaces_index list 
		self.centers            = coords # Coords of center of placement site (manufacturing units)
		self.edit_distances     = []
		self.manhattan_distance = md

