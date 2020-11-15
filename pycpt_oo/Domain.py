class Domain:
	"""Class for holding a Spatiotemporal domain
	---------------------------------------------------------------------------
	Variables:
		nla (float)	:	Northernmost Boundary, a Latitude
		sla (float)	:	Southernmost Boundary, a Latitude
		elo (float)	: 	Easternmost Boundary, a Longitude
		wlo (float)	:	Westernmost Boundary, a Longitude
		tini (int)	:	Earliest year of temporal domain
		tend (int)	:	Most recent year of temporal domain
		fyr (int)	:	~Necessary for a Forecast domain, we set fyr=tend in constructor so throw fyr in the tend spot~
		isForecast (Bool): is this a forecast domain or no - used to allow Fyr to be outside of 1982-2020
	---------------------------------------------------------------------------
	Class Methods (Callable without instantiation):
		from_string(string: str) -> Domain  (Constructs a Domain object from a previously saved string)
	---------------------------------------------------------------------------
	Object Methods:
		__init__(nla: float, sla: float, elo: float, wlo: float, tini: int, tend: int) -> Domain (Constructs a Domain Object)
		validate_args(nla: float, sla: float, elo: float, wlo: float, tini: int, tend: int) -> Boolean (ensures all args are valid)
		__str__() -> str (string representation of a Domain Object)
		__repr__() -> str (short string representation of a domain object)
		__eq__(other: Domain) -> Boolean (Compares self with another Domain object )
	---------------------------------------------------------------------------"""

	def __init__(self, nla, sla, elo, wlo, tini, tend, isForecast=False):
		"""Constructor - requires all args"""
		if not self.validate_args(nla, sla, elo, wlo, tini, tend, isForecast): #if argumentrs are invalid:
			print("Fix your arguments!")
			return -999
		self.nla, self.sla = nla, sla  #northernmost and southernmost latitudes
		self.elo, self.wlo = elo, wlo  #easternmost and westernmost latitudes
		self.tini, self.tend = tini, tend  #first and last years of data
		self.fyr = tend  # forecast year, hopefully only used if this is a domain for a forecast

	def validate_args(self, nla, sla, elo, wlo, tini, tend, isForecast):
		"""Make sure all spatial and temporal args are valid"""
		retval = True
		if  -90 > nla > 90: #if invalid lat
			print('Northernmost Boundary Invalid - Latitude: [-90, 90]')
			retval = retval and False
		if -180 > elo > 180: #if invalid lon
			print('Easternmost Boundary Invalid - Longitude: [-180, 180]')
			retval = retval and False
		if  -90 > sla > 90: #if invalid lat
			print('Southernmost Boundary Invalid - Latitiude: [-90, 90]')
			retval = retval and False
		if -180 > wlo > 180: #if invalid lon
			print('Westernmost Boundary Invalid - Longitude: [-180, 180]')
			retval = retval and False
		if sla > nla: #don't allow going around the other way south-north
			print('Southernmost Boundary north of Northernmost Boundary - Invalid')
			retval = retval and False
		if wlo > elo: #allow going around the other way east-west, but warn
			print('Warning - Western Bound east of Eastern Bound - Behavior may be allowed or not, depending on data sources, but youd be going around the world the other way (Eastern Bound becomes Western Bound & Vice Versa). ')
		if not isForecast and 1982 > tini > 2020 or 1982 > tend > 2020: #minimum years for data, we need to look this up on IRIDL at some point
			print('Years before 1982 or after 2020 not yet allowed')
			retval = retval and False
		if isForecast and tend < 1982:
			print('Forecast year cannot be before 1982')
			retval = retval and False
		return retval #retval will be false if any of the above are triggered

	def __str__(self): #print(Domain)
		return "N: {}, S: {}, E: {}, W: {}, Tini: {}, Tend: {}".format(self.nla, self.sla, self.elo, self.wlo, self.tini, self.tend)

	def __repr__(self): #representation of Domain if printed as part of a list
		return "NE: ({},{}), SW: ({},{}), {}-{}".format(self.nla, self.elo, self.sla, self.wlo, self.tini, self.tend)

	def __eq__(self, other): #allow us to compare to other domains
		return str(self) == str(other)
