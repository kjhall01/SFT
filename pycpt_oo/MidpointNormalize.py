import numpy as np
import matplotlib.colors as colors

class MidpointNormalize(colors.Normalize):
	"""Helper class for matplotlib plotting custom colormaps - dont change, its from stackoverflow"""
	def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
		self.midpoint = midpoint
		colors.Normalize.__init__(self, vmin, vmax, clip)

	def __call__(self, value, clip=None):
		x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
		return np.ma.masked_array(np.interp(value, x, y))
