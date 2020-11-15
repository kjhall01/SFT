import numpy as np


class MetaTensor:
	"""holds metadata about a climatetensor object
	---------------------------------------------------------------------------
		Variables:
		  	X (int) 	:	number of longitude values in data (# columns, xdimension)
			Y (int)		:	number of latitude values in data (# of rows, ydimension)
			T (int)		:	number of years in data (# dimension1, #years )
			Xi (float)	:	lowest longitude value (westernmost)
			Yi (float)	:	lowest latitude value (southernmost)
			Ti (int)	: 	lowest time value (first year )
			dx (float)	:	change in longitude between columns
			dy (float)	:	change in latitude between nrows
			dt (int)	:	change in year between (1stdim)
			x_coords (np.array) :	array with all longitude values  from min to max
			y_coords (np.array) :	array with all latitude values   from max to min
			years (np.array)	:	array with all years  from min to max
			nla, sla, elo, wlo  :	northermost, southernmost, easternmost, westernmost lat/longs
			tini, tend	:	first year , last year
			shape (tuple)	: 	like np.array.shape
	---------------------------------------------------------------------------
		Class Methods:
			None
	---------------------------------------------------------------------------
		Object Methods:
			None
	---------------------------------------------------------------------------"""

	def validate_args(self, X, Y, T, Xi, Yi, Ti, dx, dy, dt ):
		"""makes sure everything is good with the parameters """
		retval = True
		floats = [Xi, dx, Yi, dy]
		ints = [X, Y, T, Ti, dt]
		for flt in floats:
			if type(flt) != float:
				retval = retval and False
		for nt in ints:
			if type(nt) != int:
				retval = retval and False
		return retval

	def __init__(self, X, Y, T, Xi, Yi, Ti, dx, dy, dt):
		"""Creates a MetaTensor"""
		if not self.validate_args(X, Y, T, Xi, Yi, Ti, dx, dy, dt):
			print('Invalid MetaTensor parameter types, sorry')
			return -999
		#lets assume dx, dy, dt are never negative
		self.shape = (T, Y, X)
		self.X, self.Y, self.T = X, Y, T
		self.Xi, self.Yi, self.Ti = Xi, Yi, Ti
		self.dx, self.dy, self.dt = dx, dy, dt
		self.x_coords, self.y_coords, self.years = np.asarray([ round(i, 6) for i in np.linspace(Xi, Xi+X*dx, num=X+1)]), np.asarray([round(i,6) for i in np.linspace(Yi+Y*dy, Yi, num=Y+1)]), np.linspace(Ti, Ti+T*dt, num=T+1)
		self.nla, self.sla, self.elo, self.wlo = Yi+Y*dy, Yi, Xi, Xi+X*dx
		self.tini, self.tend = Ti, Ti+T*dt

	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if vars(self)[key] != vars(other)[key]:
				ret = False
		return ret
