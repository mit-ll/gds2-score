from enum import Enum

class Route_Direction(Enum):
	VERTICAL   = 1
	HORIZONTAL = 2

class LEF:
	def __init__(self):
		self.database_units = 0
		slef.manufacturing_grid = 0
		self.layers = []

	def load_lef_file(self, lef_fame):
		
		return

class LEF_Routing_Layer:
	def __init__(self):
		self.direction = None
		self.pitch     = None
		self.offset    = None
		self.min_width = None
		self.max_width = None
		self.width     = None
		self.spacing   = None
		# self.area
		# self.min_enclosed_area
		# self.min_density
		# self.max_density
		# self.density_check_window
		# self.density_check_step
		# self.min_cut

	def __init__(self, direction, pitch, offset, min_width, max_width, width, spacing):
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

class LEF_Via_Layer:
	def __init__(self):
		self.spacing = None

	def __init__(self, spacing):
		self.spacing = spacing
