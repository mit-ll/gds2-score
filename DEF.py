# Import Custom Modules
from polygon import *

# Other Imports
import copy
import time

class DEF:
	def __init__(self, def_fname, lef_info):
		self.database_units           = 0
		self.die_bbox                 = None
		self.placement_rows           = []
		self.num_placement_rows       = 0
		self.num_placement_cols       = 0
		self.placement_grid_bbox      = None
		self.load_def_file(def_fname, lef_info)

	def load_def_file(self, def_fname, lef_info):
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
		
		# Set placement grid bbox (in database units)
		# @TODO currently supporting only horizontal placement rows
		self.num_placement_rows  = len(self.placement_rows)
		self.num_placement_cols  = self.placement_rows[0].dimension.x
		placement_grid_site      = lef_info.placement_sites[self.placement_rows[0].site_name]
		placement_grid_bbox_ll   = copy.copy(self.placement_rows[0].origin)
		placement_grid_bbox_ur   = Point(placement_grid_bbox_ll.x + (self.placement_rows[-1].dimension.x * placement_grid_site.dimension.x), placement_grid_bbox_ll.y + (self.num_placement_rows * placement_grid_site.dimension.y))
		self.placement_grid_bbox = BBox(placement_grid_bbox_ll, placement_grid_bbox_ur)

		# Close LEF File
		stream.close()

		print "Done - Time Elapsed:", (time.time() - start_time), "seconds."
		print "----------------------------------------------"
		return

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
