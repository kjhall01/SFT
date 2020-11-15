class Modes:
	"""A class for holding CPT Arguments
	---------------------------------------------------------------------------
	Variables:
		xmodes_max (int): 	max number of xmodes CPT can use (it decides based whats best within your parameters)
		xmodes_min (int): 	min number of xmodes CPT can use
		ymodes_max (int):	max number of ymodes CPT can use
		ymodes_min (int):	min number of ymodes CPT can use
		ccamodes_max (int):	max number of cca modes CPT can use
		ccamodes_min (int): min number of cca modes CPT can use
		eofmodes (int)	:	number of EOFs for CPT to compute
	---------------------------------------------------------------------------
	Class Methods (callable without instantiation):
		None
	---------------------------------------------------------------------------
	Object Methods:
		__init__(	xmodes_max: int, xmodes_min: int, ymodes_max: int, ymodes_min: int,
					ccamodes_max: int, ccamodes_min: int, eofmodes: int) -> Mode (holds modes for CPT)
		validate_args( same as init ) -> Boolean (returns false if there are invalid parameters)
	---------------------------------------------------------------------------"""
	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if vars(self)[key] != vars(other)[key]:
				ret = False
		return ret

	def __init__(self, xmodes_max, xmodes_min, ymodes_max, ymodes_min, ccamodes_max, ccamodes_min, eofmodes):
		if not self.validate_args(xmodes_max, xmodes_min, ymodes_max, ymodes_min, ccamodes_max, ccamodes_min, eofmodes):
			print('Fix your parameters!')
			return -999
		self.xmodes_max, self.xmodes_min = xmodes_max, xmodes_min
		self.ymodes_max, self.ymodes_min = ymodes_max, ymodes_min
		self.ccamodes_max, self.ccamodes_min = ccamodes_max, ccamodes_min
		self.eofmodes = eofmodes

	def validate_args(self, xmodes_max, xmodes_min, ymodes_max, ymodes_min, ccamodes_max, ccamodes_min, eofmodes):
		retval = True
		if type(xmodes_max) != int or 10 < xmodes_max < 1:
			print('xmodes_max must be between 1-10 inclusive')
			retval = retval and False
		if type(xmodes_min) != int or 10 < xmodes_min < 1:
			print('xmodes_min must be between 1-10 inclusive')
			retval = retval and False
		if xmodes_max < xmodes_min:
			print('xmodes_max must be >= xmodes min')
			retval = retval and False

		if type(ymodes_max) != int or 5 < ymodes_max < 1:
			print('ymodes_max must be between 1-5 inclusive')
			retval = retval and False
		if type(ymodes_min) != int or 5 < ymodes_min < 1:
			print('ymodes_min must be between 1-5 inclusive')
			retval = retval and False
		if ymodes_max < ymodes_min:
			print('ymodes_max must be >= ymodes min')
			retval = retval and False

		if type(ccamodes_max) != int or 5 < ccamodes_max < 1:
			print('ccamodes_max must be between 1-5 inclusive')
			retval = retval and False
		if type(ccamodes_min) != int or 5 < ccamodes_min < 1:
			print('ccamodes_min must be between 1-5 inclusive')
			retval = retval and False
		if ccamodes_max < ccamodes_min:
			print('ccamodes_max must be >= ccamodes min')
			retval = retval and False

		if type(eofmodes) != int or 0 >= eofmodes:
			print('eofmodes must be greater than 0')
			retval = retval and False
		return retval
