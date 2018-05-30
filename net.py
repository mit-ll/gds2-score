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
		self.num                = num
		self.net_basename       = net_basename
		self.layer_num          = layer_num
		self.layer_name         = layer_name
		self.polygon            = poly
		self.nearby_bbox        = BBox.from_bbox_and_extension(self.polygon.bbox, (2 * (self.polygon.bbox.width + self.polygon.bbox.height)))
		self.nearby_sl_polygons = [] # nearby polygons on the same layer
		self.nearby_al_polygons = [] # nearby polygons on above layer
		self.nearby_bl_polygons = [] # nearby polygons on below layer
		self.same_layer_blockage = 0 # perimeter units blocked (according to step_size)
		self.diff_layer_blockage = 0 # top/bottom area units blocked
