# Import Custom Modules
from polygon import *

# Other Imports
import copy
import time
import numpy
import sys

class DEF:
	def __init__(self, def_fname, lef_info, fill_cell_names, pg_filename):
		self.database_units           = 0
		self.die_bbox                 = None
		self.placement_rows           = []
		self.num_placement_rows       = 0
		self.num_placement_cols       = 0
		self.placement_grid           = None
		self.placement_grid_bbox      = None

		# Load DEF files
		self.load_def_file(def_fname, lef_info, fill_cell_names)

		# Save Placement Grid to File
		if pg_filename != None:
			self.save_placement_grid(pg_filename)

	def load_def_file(self, def_fname, lef_info, fill_cell_names):
		print "Loading DEF file ..."
		start_time = time.time()

		# Open DEF File
		with open(def_fname, 'rb') as stream:
			for line in stream:
				line = line.rstrip(' ;\n').lstrip()
				# Do not process comment lines
				if (len(line) > 0) and (line[0] != "#"):
					line_list = line.split(' ')
					if "ROW" in line_list:
						temp_origin        = Point(int(line_list[3]), int(line_list[4]))
						temp_dim           = Point(int(line_list[7]), int(line_list[9]))
						temp_spacing       = Point(int(line_list[11]), int(line_list[12]))
						temp_placement_row = PlacementRow(line_list[1], line_list[2], copy.copy(temp_origin), line_list[5], copy.copy(temp_dim), copy.copy(temp_spacing))
						self.placement_rows.append(copy.copy(temp_placement_row))
					elif "UNITS" in line_list and "DISTANCE" in line_list and "MICRONS" in line_list:
						self.database_units = int(line_list[-1])
					elif "DIEAREA" in line_list:
						ll = Point(int(line_list[2]), int(line_list[3]))
						ur = Point(int(line_list[6]), int(line_list[7]))
						self.die_bbox = BBox(ll, ur)
					elif "COMPONENTS" in line_list and "END" not in line_list:
						# Check that placement grid dimensions have already been loaded
						if not self.placement_rows:
							print "ERROR %s: Placement grid dimensions must be loaded from DEF file prior to loading component locations." % (inspect.stack()[0][3])
							sys.exit(1)
						
						# Check that standard cell dimensions have already been loaded
						if not lef_info.standard_cells:
							print "ERROR %s: Standard cell dimensions must be loaded from LEF file prior to loading component locations." % (inspect.stack()[0][3])
							sys.exit(1)

						# Set placement grid bbox (in database units)
						# @TODO currently supporting only horizontal placement rows
						self.num_placement_rows  = len(self.placement_rows)
						self.num_placement_cols  = self.placement_rows[0].dimension.x
						placement_grid_site      = lef_info.placement_sites[self.placement_rows[0].site_name]
						placement_grid_bbox_ll   = copy.copy(self.placement_rows[0].origin)
						placement_grid_bbox_ur   = Point(placement_grid_bbox_ll.x + (self.placement_rows[-1].dimension.x * placement_grid_site.dimension.x), placement_grid_bbox_ll.y + (self.num_placement_rows * placement_grid_site.dimension.y))
						self.placement_grid_bbox = BBox(placement_grid_bbox_ll, placement_grid_bbox_ur)
						self.placement_grid      = numpy.zeros(shape=(self.num_placement_rows, self.num_placement_cols))

						# Parse number of components
						num_components        = int(line_list[-1])
						num_parsed_components = 0
						while num_parsed_components < num_components:
							line = stream.next().rstrip(' ;\n').lstrip(" -")
							if "(" in line and ")" in line:
								line_list = line.split(' ')
								# Parse component name
								curr_std_cell_name = line_list[1]

								# Parse/Compute component location on the placement grid
								component_loc_found = False
								for ind, token in enumerate(line_list):
									if token == '(':
										component_loc_x      = float(line_list[ind + 1])
										component_loc_y      = float(line_list[ind + 2])
										component_loc_found  = True
										break
								if not component_loc_found:
									print "ERROR %s: Component location not identified." % (inspect.stack()[0][3], curr_std_cell_name)
									sys.exit(1)
						
								# Check if placement location is inside placement grid bbox, if not ignore
								if self.placement_grid_bbox.are_coords_inside_bbox(component_loc_x, component_loc_y):
									# Compute component row and column origin in placement grid
									component_col = (component_loc_x - placement_grid_bbox_ll.x) / placement_grid_site.dimension.x
									component_row = (component_loc_y - placement_grid_bbox_ll.y) / placement_grid_site.dimension.y
									
									# Check if placement row/col are aligned with the placement grid
									if component_col.is_integer() and component_row.is_integer():
										# Cast to row/col to integers
										component_col = int(component_col)
										component_row = int(component_row)

										# Check that component height does not exceed on placement site height
										curr_placement_site_name  = self.placement_rows[component_row].site_name
										curr_std_cell_height      = lef_info.standard_cells[curr_std_cell_name].height
										curr_placement_row_height = lef_info.placement_sites[curr_placement_site_name].dimension.y
										if curr_std_cell_height != curr_placement_row_height:
											print "ERROR %s: Component height does not match placement site height (Component Height: %d, Site Height: %d)." % (inspect.stack()[0][3], curr_std_cell_height, curr_placement_row_height)
											sys.exit(1)
										
										# Check if standard cell is a filler cell -> ignore
										if curr_std_cell_name not in fill_cell_names:
											# Check if width of std cell is an integer (i.e. an even multiple of the placement site)
											curr_std_cell_width = lef_info.standard_cells[curr_std_cell_name].width / lef_info.placement_sites[curr_placement_site_name].dimension.x
											if not curr_std_cell_width.is_integer():
												print "ERROR %s: Component (%s) width (%f) is not an even multiple of the placement site (%s)." % (inspect.stack()[0][3], curr_std_cell_name, curr_std_cell_width, curr_placement_site_name)
												sys.exit(1)

											# Mark locations on placement grid that are occupied by the standard cell
											for curr_site_num in range(int(curr_std_cell_width)):
												self.placement_grid[component_row, component_col + curr_site_num] = 1
									else:
										print "ERROR %s: Component placement (ID: %s; name: %s) not aligned to placement grid  (x: %f, y: %f)." % (inspect.stack()[0][3], line_list[0], curr_std_cell_name, component_loc_x, component_loc_y)
										sys.exit(1)

								num_parsed_components += 1

		print "Identified %d placed standard cells." % (num_parsed_components)

		# Close LEF File
		stream.close()

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return

	def save_placement_grid(self, pg_filename):
		numpy.save(pg_filename, self.placement_grid)

# Placement row as defined in the DEF file. The placement row has 
# dimensions that are in units of # of sites.
class PlacementRow():
	def __init__(self, id_name, site_name, origin, orient, dim, space):
		self.id_name   = id_name
		self.site_name = site_name
		self.origin    = origin
		self.orient    = orient
		self.dimension = dim
		self.spacing   = space

	def print_row(self):
		print "ROW %s %s %d %d %s DO %d BY %d STEP %d %d" % (self.id_name, self.site_name, self.origin.x, self.origin.y, self.orient, self.dimension.x, self.dimension.y, self.spacing.x, self.spacing.y)
