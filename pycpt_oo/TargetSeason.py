class TargetSeason:
	"""class to hold & handle all variables relating to a forecast target period
	---------------------------------------------------------------------------
	Variables:
		init (str)		: 	a month abbreviation, indicating month of forecast initialization
		tgt (str)		: 	either a month abbrev, or two joined by a dash eg "Jun" or "Jun-Aug" : forecast period start/end
		ndays (int)		:	Number of days in forecast period, no leap year fix
		nmonths	(int)	:	Number of months in forecast period, including end
		nmonths30 (int)	: 	Number of months in forecast period * 30 - need for certain models / data sources
		tgti   			:  	arg for data library query string, number of months from init to start of tgt + 0.5 because thats how the IRIDL does it
		tgtf			: 	arg for data library query string, number of months from init to end of tgt + 0.5 because thats how the IRIDL does it
		monf			:	~for a Forecast target season, monf is the name of the init month, put your monf in place of init in the constructor~
	-----------------------------------------------------------------------
	Class Methods (Callable Without Instantiation):
		from_string(string: str) -> TargetSeason	(Constructs a TargetSeason object from a previously saved String)
	-----------------------------------------------------------------------
	Object Methods:
		__init__(init: str, tgt: str, tgti=float, tgtf=float) -> TargetSeason (class constructor)
		__str__() -> str   (string representation of class)
		__repr__() -> str  (short string representation of class for other python objects like lists)
		__eq__(other: TargetSeason) -> Boolean (compares with another TargetSeason)
		validate_args(init: str, tgt: str) -> Boolean (ensures all arguments are valid)
		__count_days_and_months(): -> None (determines days and months in forecast period, sets self variables)
		__determine_iridl_tgti_args() -> None (determines IRIDL tgti/tgtf arguments, sets self variables)
	-----------------------------------------------------------------------	"""

	def __init__(self, init, tgt, tgti=0.5, tgtf=0.5):
		"""constructor - requires init & tgt, can specify tgti & tgtf but we calculate them if you dont'"""
		if not self.validate_args(init, tgt): #if any arguments are invalid
			print('Fix your Arguments!')
			return -999

		#only executes if arguments are valid
		self.init = init #setting instance variable
		self.monf = init #set monf so we can access it in IRIDL
		self.tgt = tgt #setting instance variable
		self.nmonths, self.ndays = 0, 0 #instance variables for # months in tgt, # of days in tgt, is filled in during __count_days_and_months
		self.tgti, self.tgtf = tgti, tgtf #args for IRIDL query string - indicate months from initialization to target period start and end  - filled during __determine_iridl_tgti_args
		self.__count_days_and_months()
		self.__determine_iridl_tgti_args()

	@classmethod
	def from_string(self, string):
		"""Allows us to build a TargetSeason from a previously saved string"""
		string = string.split()
		return TargetSeason(string[2], string[0][:-1], tgti=string[-3][:-1], tgtf=string[-1])

	def __str__(self):
		"""string representation of a TargetSeason"""
		return "{} Init {}: {} months, {} days, {} nmonths30, tgti: {}, tgtf: {}".format(self.tgt, self.init, self.nmonths, self.ndays, self.nmonths30, self.tgti, self.tgtf)

	def __eq__(self, other):
		return str(self) == str(other)

	def __repr__(self):
		"""String representation of a TargetSeason for python objects like lists"""
		return "{} Init {}: {}m {}d".format(self.tgt, self.init, self.nmonths, self.ndays)

	def validate_args(self, init, tgt):
		"""Check that all the months specified are valid month abbreviations"""
		months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] #list of valid Month args

		def _check_valid(init): #helper function determines whether  a month is valid or not
			if init not in months: #Check that initialization month is valid
				print('Invalid Month - {} must be one of {}'.format(init, months))
				return False
			else:
				return True

		if '-' in tgt:
			return _check_valid(init) and len(tgt.split('-')) ==  2 and _check_valid(tgt.split('-')[0]) and _check_valid(tgt.split('-')[1]) #split "Jun-Aug" into ["Jun","Aug"] - if there's more than one '-', or either month in tgt or the init month is invalid, return False
		else:
			return _check_valid(init) and _check_valid(tgt) #if '-' not in tgt, simply check that the initialization month is valid & the tgt month is valid
		pass

	def __count_days_and_months(self):
		"""Count number of months in the forecast period, and the number of days"""
		days_in_month_dict = {"Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30, "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
		months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

		if '-' in self.tgt: #if User has specified multi-month target season
			mon_ini, mon_fin = self.tgt.split('-') #split "Jun-Aug" into ["Jun", "Aug"] - first and last months of tgt

			#Here we loop over 'months' to find the months in between mon_ini & mon_end, even if it's a cross-year target (Dec-Feb, etc)
			flag, found_end, count = 0, 0, 0 # flag for whether weve found mon_ini yet, flag for whether we've found mon_fin yet, which can only be set to True after we've found mon_ini, and a var for storing the index we're on in months
			while found_end == 0 and count < 24: #must end when we find mon_fin, this will never take more than 2 loops  so end at count=24 for safety
				if flag == 1: #If we have found mon_ini and not yet found mon_fin (since loop would have exited)
					self.nmonths += 1 #add one to the number of months in the target season
					self.ndays += days_in_month_dict[months[count % 12]] #get the number of days in the current month from days_in_month_dict, count % 12 lets us loop multiple times, otherwise count would be out of the range of indexes of months
					if months[count % 12] == mon_fin: #if this month is mon_fin,
						flag, found_end = 0, 1 #found_end = True, so exit loop

				if flag == 0 and months[count % 12] == mon_ini: #if we haven't yet found mon_ini, and this month is it:
					flag = 1 #set flag to indicate we have entered target season during our loop
					self.nmonths += 1 #add one to count of months , since above code will have been skipped for this month
					self.ndays += days_in_month_dict[months[count % 12]] #get # days in mon_ini from days_in_month_dict and add to instance var
				count += 1 #increase counter / index

		else: #if user specified single month target season
			self.nmonths += 1
			self.ndays += days_in_month_dict[self.tgt] #get days in that month from days_in_month_dict
		self.nmonths30 = self.nmonths * 30

	def __determine_iridl_tgti_args(self):
		"""If unspecified, calculate tgti & tgtf (times in months from init to bounds of forecast period)"""
		if self.tgti == 0.5 and  self.tgtf == 0.5: #if default args are unchanged, user did not specify
			days_in_month_dict = {"Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30, "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
			months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

			count, init_ndx, mon_ini_ndx, mon_fin_ndx = 0, -1, -1, -1 #stores index into months, index of initialization month, index of mon_ini, index of mon_fin
			while mon_fin_ndx == -1: #loop over months until we find initialization month, then until we find mon_ini, and then until we find mon_fin
				if init_ndx == -1 and months[count % 12] == self.init: # if we have not yet found initialization month, check if this month is initialization month
					init_ndx = count
				if init_ndx > -1 and mon_ini_ndx == -1 and count > init_ndx and months[count % 12] == self.tgt.split('-')[0]: #only if we have found initialization month, and this month isn't initialization month, and we haven't yet found mon_ini do we check if this month is mon_ini
					mon_ini_ndx = count
					if '-' not in self.tgt: #if user specified 1 month long target season, set mon_fin_ndx = mon_ini_ndx
						mon_fin_ndx = count
				if mon_ini_ndx > -1 and '-' in self.tgt and mon_fin_ndx == -1 and months[count % 12] == self.tgt.split('-')[1]: #if we have found mon_ini and not mon_fin, and the user specified a multimonth target season, check if this month is mon_fin
					mon_fin_ndx = count
				count += 1
			self.tgti += mon_ini_ndx - init_ndx #set tgti = # months between initialization month and mon_ini (start of target period) + 0.5 bc of data library weirdness
			self.tgtf += mon_fin_ndx - init_ndx #set tgtf = #months between initialization month and mon_fin (end of target period) + 0.5 bc of data library weirdness
