class ArgSet:
	"""Class for bundling a Domain and a TargetSeason and assorted vars for code brevity
		Each ArgSet represents one forecast target season for one spatiotemportal domain
	---------------------------------------------------------------------------
	Variables:
		target_season (TargetSeason)	: 	Holds the TargetSeason object for the forecast target season - can be for hindcasts, observations or forecasts
		domain (Domain)					:	Holds the domain object describing the spatiotemporal domain considered when building models / forecasting
		obs (str)						:	Holds a string indicating source of observations data - so we can pass to IRIDL
		station (boolean)				:	Whether or not obs data is station data- this is used in options i don't usually use
		predictor (string)				: 	holds a string representing type of predictor data- either PRCP, RFREQ, and some models have UQ & VQ i think. Temp in future
		predictand (string)				:	holds a string representing type of predictand data - i think for not just PRCP & RFREQ, but in future Temp, SST, etc
		ntrain	(int)					:	holds the number of years used for training
	---------------------------------------------------------------------------
	Class Methods:
	 	None
	---------------------------------------------------------------------------
	Object Methods:
		__init__(tgt: TargetSeason, dom: Domain, obs: str, station: Bool, predictor: str, predictand: str)
		__str__() -> str   (string representation of class)
		__repr__() -> str  (short string representation of class for other python objects like lists)
		__eq__(other: ArgSet) -> Boolean (compares with another ArgSet)
	---------------------------------------------------------------------------"""

	def __str__(self):
		return "ArgSet: \n  {}\n  {}\n Obs: {}, Station: {}, Predictor: {}, Predictand: {}, ntrain: {}".format(str(self.target_season), str(self.domain), self.obs, self.station, self.predictor, self.predictand, self.ntrain)

	def __repr__(self):
		return "ArgSet: \n  {}\n  {}\n Obs: {}, Station: {}, Predictor: {}, Predictand: {}, ntrain: {}".format(self.target_season, self.domain, self.obs, self.station, self.predictor, self.predictand, self.ntrain)

	def __eq__(self, other):
		return self.target_season == other.target_season and self.domain == other.domain and self.obs == other.obs and self.station == other.station and self.predictor == other.predictor and self.predictand == other.predictand and self.ntrain == other.ntrain

	def __init__(self, tgt, dom, obs=None, station=None, predictor=None, predictand=None):
		self.target_season = tgt
		self.domain = dom
		self.obs = obs #for IRIDL object - indicats obs source
		self.station = station #for IRIDL object - indicates station data or not
		self.predictor = predictor #for IRIDL Object - indicates type of data
		self.predictand = predictand #same for IRIDL object
		if self.target_season.tgt in ['Nov-Jan', 'Dec-Feb', 'Jan-Mar']: #if the target is cross - year
			self.ntrain= self.domain.tend-self.domain.tini # don't adjust length of training period
		else:
			self.ntrain= self.domain.tend-self.domain.tini + 1# adjust length of training period
