# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from polygon import *

# Other Imports
import inspect
import sys
import copy
# from multiprocessing import Lock

class Window():
	def __init__(self, start_pt, width, height, direction):
		self.initial_start_pt = start_pt
		self.width            = width
		self.height           = height
		self.direction        = direction
		self.window           = LineSegment(copy.deepcopy(start_pt), Point.from_point_and_offset(start_pt, width, height))

	@classmethod
	def from_bbox(cls, bbox, direction):
		return cls(bbox.ll, bbox.get_width(), bbox.get_height(), direction)

	def reset_x_position(self):
		self.window.p1.x = self.initial_start_pt.x
		self.window.p2.x = self.initial_start_pt.x + self.width 

	def reset_y_position(self):
		self.window.p1.y = self.initial_start_pt.y
		self.window.p2.y = self.initial_start_pt.y + self.height

	def reset_position(self):
		self.reset_x_position()
		self.reset_y_position()

	def get_start_pt_copy(self):
		return copy.deepcopy(self.window.p1)

	def get_start_pt(self):
		return self.window.p1

	def get_end_pt(self):
		return self.window.p2

	def shift_horizontal(self, step):
		self.window.p1.x += step
		self.window.p2.x += step

	def shift_vertical(self, step):
		self.window.p1.y += step
		self.window.p2.y += step

	def increase_width(self, step):
		self.width       += step
		self.window.p2.x += step

	def increase_height(self, step):
		self.window.p1
		self.height      += step
		self.window.p2.y += step

	def offset(self, offset_pt):
		self.window.p1.x += offset_pt.x
		self.window.p2.x += offset_pt.x
		self.window.p1.y += offset_pt.y
		self.window.p2.y += offset_pt.y

	def get_window_center_line_segment(self):
		if self.direction == 'H':
			y_pt = self.window.p1.y + (self.height / 2)
			p1 = Point(self.window.p1.x, y_pt)
			p2 = Point(self.window.p2.x, y_pt)
		elif self.direction == 'V':
			x_pt = self.window.p1.x + (self.width / 2)
			p1 = Point(x_pt, self.window.p1.y)
			p2 = Point(x_pt, self.window.p2.y)
		else:
			print "UNSUPPORTED %s: window direction." % (inspect.stack()[0][3], token)
			sys.exit(3)

		return LineSegment(p1, p2)

	def get_bitmap_splice(self, bitmap):
		return bitmap[self.window.p1.y : self.window.p2.y, self.window.p1.x : self.window.p2.x]

	def print_window(self, convert_to_microns=False, scale_factor=1):
		if convert_to_microns:
			self.window.print_segment(convert_to_microns=True, scale_factor=scale_factor)
		else:
			self.window.print_segment()

class Net():
	def __init__(self, fullname, gdsii_elements, lef, layer_map):
		self.fullname           = fullname
		self.basename           = fullname.split('/')[-1]
		self.num_segments       = len(gdsii_elements)
		self.segments           = []
		for i in range(len(gdsii_elements)):
			net_element_polygon = gdsii_elements[i]
			layer_num  = lef.get_layer_num(net_element_polygon.gdsii_element.layer, net_element_polygon.gdsii_element.data_type, layer_map)
			layer_name = lef.get_layer_name(net_element_polygon.gdsii_element.layer, net_element_polygon.gdsii_element.data_type, layer_map)
			# Only analyze metal ROUTING layers
			if layer_num != -1:
				self.segments.append(Net_Segment(i, self.basename, net_element_polygon, lef, layer_num, layer_name))

class Net_Segment():
	def __init__(self, num, net_basename, poly, lef, layer_num, layer_name):
		self.num                 = num
		self.net_basename        = net_basename
		self.layer_num           = layer_num
		self.layer_name          = layer_name
		self.polygon             = poly
		self.nearby_sl_bbox      = BBox.from_bbox_and_extension(self.polygon.bbox, (lef.layers[layer_num].pitch * lef.database_units))
		if layer_num < lef.top_routing_layer_num:
			self.nearby_al_bbox  = BBox.from_bbox_and_extension(self.polygon.bbox, lef.layers[layer_num + 1].min_spacing_db - 1)
		else:
			self.nearby_al_bbox  = None
		if layer_num > lef.bottom_routing_layer_num:
			self.nearby_bl_bbox  = BBox.from_bbox_and_extension(self.polygon.bbox, lef.layers[layer_num - 1].min_spacing_db - 1)
		else:
			self.nearby_bl_bbox  = None
		self.nearby_sl_polygons  = [] # nearby polygons on the same layer
		self.nearby_al_polygons  = [] # nearby polygons on above layer
		self.nearby_bl_polygons  = [] # nearby polygons on below layer
		self.sides_unblocked     = [] # sides of net segment polygon not 100% blocked
		self.unblocked_windows   = {'N': [], 'S': [], 'E': [], 'W': [], 'T': [], 'B': []} # Areas with no blockage north of net segment
		self.same_layer_units_blocked = 0 # perimeter windows blocked (according to step_size)
		self.diff_layer_units_blocked = 0 # top/bottom area units blocked
		self.same_layer_units_checked = 0 # locations valid rogue wires can be attached around wire perimeter
		self.diff_layer_units_checked = 0 # locations valid rogue wires can be attached along wire top/bottom
	
	def get_perimeter_blockage_percentage(self):
		return ((float(self.same_layer_units_blocked) / float(self.same_layer_units_checked)) * 100.0)

	def get_top_bottom_blockage_percentage(self):
		return ((float(self.diff_layer_units_blocked) / float(self.diff_layer_units_checked)) * 100.0)

	def get_weighted_blockage_percentage(self):
		return ((self.get_perimeter_blockage_percentage() * float(4.0/6.0)) + (self.get_top_bottom_blockage_percentage() * float(2.0/6.0)))


