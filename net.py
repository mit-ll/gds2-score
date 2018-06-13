# Import GDSII Library
from gdsii.elements import *

# Import Custom Modules
from polygon import *

# Other Imports
import inspect
import sys
# from multiprocessing import Lock

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
		self.top_unblocked_windows    = [] # Areas with no blockage above net segment
		self.bottom_unblocked_windows = [] # Areas with no blockage below net segment
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