from __future__ import print_function
import sys, os
import json
from pathlib import Path
import platform, copy, warnings
import subprocess
import struct, copy, json
import numpy as np
import datetime as d

class IRIDL:
	"""Class for fetching & managing Hindcasts, Obs, & Forecasts Files from the IRIDL for one Target Season
	---------------------------------------------------------------------------
	Variables:
		fm (FileManager)	: 	A Filemanager object for checking if files exist or not
		obs_args (ArgSet)	:	ArgSet object that holds tgt and obs_domain
		hindcast_args (ArgSet):	Argset object that holds tgt and model_domain
		forecast_args (ArgSet):	Argset object that holds forecasts_tgt and forecast_domain
		verbose (Boolean)	:	Whether or not output will be printed
		models (list)		:	List of strings holding names of models, only used really for validation purposes  - see available options in validate_args
		obs (str)			: 	string holding the name of the observations source user desires - see available options in validate_args
		station (boolean)	:	Whether or not observation data comes from stations, i think this is from another version, not sure if it's used
		obs_domain (Domain)	:	Domain object holding data about the observations spatiotemporal domain
		model_domain (Domain):	Domain object holding data about the hindcasts spatiotemporal domain
		forecast_domain (Domain): Domain object holding data about the forecasts spatiotemporal domain (usually 1 season that hasn't physically occurred yet, and same spatial as obs)
		forecast_tgt (TargetSeason): TargetSeason object holding data about season we will be forecasting
		predictor (str)		: 	string representing what kind of data were using, rainfall totals or wet day frequency
		predictand(str)		: 	string holding what kind of predictand data we have
		arg_dict (dict)		:	dictionary holding all the data that needs to be unpacked into an IRIDL query Ingrid url string
		url_dict (dict)		:	dictionary holding all of the URLs with {var-name} string formatters inserted in the required locations so arg_dict can be unpacked
		fprefix (str)		: 	this is the same as predictor, unless somebody else uses it differently
		L (list)			:	the constant value ['1'] and i dont know why really, dont think its used anymore
		obs_sources (dict) 	:	dictionary storing Ingrid strings to be put into the query URL for observations data
		obs_source (str)	:	dynamically selected from obs_sources depending on obs selection
		hdate_lasts (dict) 	:	dictionary containing a variable for IRIDL querying, i believe it is year of last available data for observations
		hdate_last (int)	:	i beleive last available year of data for observations
		rainfall_frequency (bool) :	 something to do with the RFREQ predictand
		threshold_pctle (bool)	:	something to do with using the RFREQ predictand
		wetday_threshold	:	minimum amount of rainfall to define a 'wetday'
		valid_models (list)	:	allowed model names: ['NextGen', 'CMC1-CanCM3', 'CMC2-CanCM4', 'CanSIPSv2', 'COLA-RSMAS-CCSM4', 'GFDL-CM2p5-FLOR-A06', 'GFDL-CM2p5-FLOR-B01','GFDL-CM2p1-aer04', 'NASA-GEOSS2S', 'NCEP-CFSv2']
		valid_obs (list)	:	allowed obs names: ['CPC-CMAP-URD', 'CHIRPS', 'TRMM', 'CPC', 'Chilestations','GPCC', 'ENACTS-BD']
		valid_preds (list)	:	allowed predictand/or names: ['PRCP', 'RFREQ', 'UQ', 'VQ']
		unallowed (string)	: 	string full of characters that should not be used in directory names.
		verbose(bool)		: 	whether to print stuff or not
	---------------------------------------------------------------------------
	Class Methods (Callable without Instantiation):
		None, sorry can't print/save/load this puppy
	---------------------------------------------------------------------------
	Object Methods:
	__init__(	work: str,	workdir: str,	tgt: TargetSeason, 	models: list of str,
				obs: str,	station: bool,	obs_domain: Domain, model_domain: Domain,
				forecast_domain: Domain (with tend=fyr), forecast_tgt: TargetSeason (with init=monf),
				predictor: str  ) -> IRIDL
	validate_args( work: str, workdir: str, models: list of str, obs: str, station: bool, predictor: str) -> boolean
	__setup() -> None (sets up more internal variables)
	prep_files(model: str, check: Boolean) -> None (Calls 'fetch' for each datatype, hindcasts, forecasts, and observations for the model)
	fetch(model: str, check: boolean) -> None (queries the IRIDL for a file as appropriate, and writes to the working_directory/input folder )
	callSys(arg: str) -> None (runs a system command)
	---------------------------------------------------------------------------"""

	def callSys(self, arg):
		"""Calling a system command, but get_ipython().system breaks too easily when youre not in a jupyter notebook"""
		try:
			get_ipython().system(arg) #if we're in jupyter notebook, use this
		except:
			subprocess.check_output(arg, shell=True) #if were not, get_ipython acts weirdly so jsut used subprocess

	def __init__(self, fm,  obs_args, hindcast_args, forecast_args,  models, verbose=True):
		"""constructor - creates an IRIDL object"""
		self.verbose = verbose #whether or not to print out the output. CURL output may print anyway.
		obs, station, predictor, predictand = obs_args.obs, obs_args.station, obs_args.predictor, obs_args.predictand
		if not self.validate_args( models, obs, station, predictor, predictand):
			if self.verbose:
				print('Fix your Arguments!') # if any args are invalid
			return -999
		self.fm = fm
		self.hindcasts_tgt = hindcast_args.target_season #the target season for the hindcasts (X data)
		self.h_ntrain = hindcast_args.ntrain #getting ntrain for hindcasts - they should all be the same so we use this one in CPT but just to be safe, get others
		self.f_ntrain = forecast_args.ntrain #getting ntrain for forecasts
		self.obs_ntrain = obs_args.ntrain #getting ntrain for obs
		self.observations_tgt = obs_args.target_season #same target season for the observations (Y Data) - makes sense because X is predictors, Y is predictands (Y is what X should be outputting after modeling)
		self.forecasts_tgt = forecast_args.target_season #target season for the forecast for the next season - true future forecast
		self.hindcasts_domain = hindcast_args.domain #spatiotemporal domain for hindcasts   #padded by forecasts if not enough years of hindcast data
		self.observations_domain = obs_args.domain #spatiotemporal domain for observations #limiting factor for training
		self.forecasts_domain = forecast_args.domain #spatiotemporal domain for forecast - next N months, same spatial as observations usually
		self.models = models #list of models
		self.obs, self.station = obs, station #where to get observations ,, is it station data? not sure that station is used really
		self.predictor, self.predictand = predictor, predictand #Type of data we are working with, PRCP, UQ, VQ, RFREQ, and in the future TEMP
		self.fprefix = self.predictor #this is an artifact of old versions of PyCPT, just roll with it
		self.L=['1'] #this is an artefact of an older time, I dont think it's used anymore but dont have time to verify
		self.__setup() #finishes up some more internal variables automatically

		self.arg_dict = { #need to unpack stuff from TargetSeason and Domain members into a dict that we can use for dynamic string formatting
			'Hindcasts': {**vars(self.hindcasts_tgt), **vars(self.hindcasts_domain), 'wetday_threshold':self.wetday_threshold, 'hdate_last':self.hdate_last, 'threshold_pctle': self.threshold_pctle, 'rainfall_frequency':self.rainfall_frequency},
			'Observations': {**vars(self.observations_tgt), **vars(self.observations_domain), 'wetday_threshold':self.wetday_threshold, 'obs_source': self.obs_source, 'hdate_last':self.hdate_last, 'threshold_pctle': self.threshold_pctle, 'rainfall_frequency':self.rainfall_frequency},
			'Forecasts': {**vars(self.forecasts_tgt), **vars(self.forecasts_domain), 'wetday_threshold':self.wetday_threshold, 'hdate_last':self.hdate_last, 'threshold_pctle': self.threshold_pctle, 'rainfall_frequency':self.rainfall_frequency}
		}

		self.url_dict = { #dict  that stores urls  to be dynamically formatted with arg_dicts contents
		  'Hindcasts': { #Hindcasts is [fprefix][model]
		    'PRCP': {	'CanSIPSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CanSIPSv2/.HINDCAST/.MONTHLY/.prec/SOURCES/.Models/.NMME/.CanSIPSv2/.FORECAST/.MONTHLY/.prec/appendstream/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'CMC1-CanCM3': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC1-CanCM3/.HINDCAST/.MONTHLY/.prec/SOURCES/.Models/.NMME/.CMC1-CanCM3/.FORECAST/.MONTHLY/.prec/appendstream/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'CMC2-CanCM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC2-CanCM4/.HINDCAST/.MONTHLY/.prec/SOURCES/.Models/.NMME/.CMC2-CanCM4/.FORECAST/.MONTHLY/.prec/appendstream/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'COLA-RSMAS-CCSM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.COLA-RSMAS-CCSM4/.MONTHLY/.prec/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-A06': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-A06/.MONTHLY/.prec/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-B01': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-B01/.MONTHLY/.prec/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p1-aer04': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p1-aer04/.MONTHLY/.prec/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NASA-GEOSS2S': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NASA-GEOSS2S/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NCEP-CFSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NCEP-CFSv2/.HINDCAST/.PENTAD_SAMPLES/.MONTHLY/.prec/SOURCES/.Models/.NMME/.NCEP-CFSv2/.FORECAST/.PENTAD_SAMPLES/.MONTHLY/.prec/appendstream/S/%280000%201%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/M/%281%29%2824%29RANGE/%5BM%5D/average/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'UQ': {'NCEP-CFSv2': 'http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.ENSEMBLE/.PGBF/.pressure_level/.VGRD/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.ENSEMBLE/.PGBF/.pressure_level/.SPFH/mul/P/850/VALUE/S/%2812%20{init}%20{tini}-{tend}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'VQ': {'NCEP-CFSv2': 'http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.ENSEMBLE/.PGBF/.pressure_level/.VGRD/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.ENSEMBLE/.PGBF/.pressure_level/.SPFH/mul/P/850/VALUE/S/%281%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'RFREQ': {	'CanSIPSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CanSIPSv2/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'CMC1-CanCM3': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC1-CanCM3/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'CMC2-CanCM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC2-CanCM4/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'COLA-RSMAS-CCSM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.COLA-RSMAS-CCSM4/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-A06': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-A06/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-B01': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-B01/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p1-aer04': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p1-aer04/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NASA-GEOSS2S': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NASA-GEOSS2S/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NCEP-CFSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NCEP-CFSv2/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{init}%201982-2009%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{ndays}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		},
		  'Observations': { #obs is [fpre][threshold_pctle if fpre==RFREQ else obs]
		    'RFREQ': {
		        True: 'https://iridl.ldeo.columbia.edu/{obs_source}/Y/{sla}/{nla}/RANGE/X/{wlo}/{elo}/RANGE/T/(days%20since%201960-01-01)/streamgridunitconvert/T/(1%20Jan%201982)/(31%20Dec%202010)/RANGEEDGES/%5BT%5Dpercentileover/{wetday_threshold}/flagle/T/{ndays}/runningAverage/{ndays}/mul/T/2/index/.T/SAMPLE/nip/dup/T/npts//I/exch/NewIntegerGRID/replaceGRID/dup/I/5/splitstreamgrid/%5BI2%5Daverage/sub/I/3/-1/roll/.T/replaceGRID/-999/setmissing_value/grid%3A//name/(T)/def//units/(months%20since%201960-01-01)/def//standard_name/(time)/def//pointwidth/1/def/16/Jan/1901/ensotime/12./16/Jan/3001/ensotime/%3Agrid/use_as_grid//name/(fp)/def//units/(unitless)/def//long_name/(rainfall_freq)/def/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv.gz',
		        False:'http://datoteca.ole2.org/SOURCES/.UEA/.CRU/.TS4p0/.monthly/.wet/lon/%28X%29/renameGRID/lat/%28Y%29/renameGRID/time/%28T%29/renameGRID/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv'},
		    'PRCP': {   'Chilestations': 'http://iridl.ldeo.columbia.edu/{obs_source}/T/%28{tgt}%29/seasonalAverage/-999/setmissing_value/%5B%5D%5BT%5Dcptv10.tsv',
		                'ENACTS-BD':'https://datalibrary.bmd.gov.bd/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv',
		                'CPC-CMAP-URD': 'https://iridl.ldeo.columbia.edu/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv',
		                'TRMM': 'https://iridl.ldeo.columbia.edu/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv',
		                'CPC': 'https://iridl.ldeo.columbia.edu/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv',
		                'CHIRPS': 'https://iridl.ldeo.columbia.edu/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv',
		                'GPCC': 'https://iridl.ldeo.columbia.edu/{obs_source}/T/%28Jan%201982%29/%28Dec%202010%29/RANGE/T/%28{tgt}%29/seasonalAverage/Y/%28{sla}%29/%28{nla}%29/RANGEEDGES/X/%28{wlo}%29/%28{elo}%29/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BT%5Dcptv10.tsv'
		    }
		  },
		  'Forecasts': { #keys if first key is forecasts are ['Forecasts'][fprefix][model]
		    'PRCP': {	'CanSIPSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CanSIPSv2/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'CMC1-CanCM3': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC1-CanCM3/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
					    'CMC2-CanCM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC2-CanCM4/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'COLA-RSMAS-CCSM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.COLA-RSMAS-CCSM4/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-A06': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-A06/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-B01': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-B01/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p1-aer04': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p1-aer04/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NASA-GEOSS2S': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NASA-GEOSS2S/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NCEP-CFSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NCEP-CFSv2/.FORECAST/.EARLY_MONTH_SAMPLES/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/{nmonths30}/mul/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'UQ': {'NCEP-CFSv2': 'http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.REALTIME_ENSEMBLE/.PGBF/.pressure_level/.VGRD/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.REALTIME_ENSEMBLE/.PGBF/.pressure_level/.SPFH/mul/P/850/VALUE/S/%281%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'VQ': {'NCEP-CFSv2': 'http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.REALTIME_ENSEMBLE/.PGBF/.pressure_level/.VGRD/SOURCES/.NOAA/.NCEP/.EMC/.CFSv2/.REALTIME_ENSEMBLE/.PGBF/.pressure_level/.SPFH/mul/P/850/VALUE/S/%281%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		    'RFREQ': {	'CMC1-CanCM3': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC1-CanCM3/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
					    'CMC2-CanCM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.CMC2-CanCM4/.FORECAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'COLA-RSMAS-CCSM4': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.COLA-RSMAS-CCSM4/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-A06': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-A06/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p5-FLOR-B01': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p5-FLOR-B01/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'GFDL-CM2p1-aer04': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.GFDL-CM2p1-aer04/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NASA-GEOSS2S': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NASA-GEOSS2S/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv',
						'NCEP-CFSv2': 'https://iridl.ldeo.columbia.edu/SOURCES/.Models/.NMME/.NCEP-CFSv2/.HINDCAST/.MONTHLY/.prec/S/%280000%201%20{monf}%20{fyr}%29/VALUES/L/{tgti}/{tgtf}/RANGEEDGES/%5BL%5D//keepgrids/average/%5BM%5D/average/Y/{sla}/{nla}/RANGEEDGES/X/{wlo}/{elo}/RANGEEDGES/-999/setmissing_value/%5BX/Y%5D%5BL/S/add%5D/cptv10.tsv'},
		  }
		}

	def fetch(self, model, datatype):
		"""downloads data from the IRI Data Library Using Ingrid"""
		if datatype == 'Observations': #Get the proper URL from the URL dict defined in constructor - different datatypes have different key patterns, so you need the if/else
			url = self.url_dict[datatype][self.fprefix][self.threshold_pctle if self.fprefix == 'RFREQ' else self.obs ]
		else:
			url = self.url_dict[datatype][self.fprefix][model]

		if datatype == 'Hindcasts':
			outpath =  Path('input', model+"_{}_".format(self.fprefix)+self.hindcasts_tgt.tgt+"_ini"+self.hindcasts_tgt.init+".tsv")
		elif datatype == 'Observations':
			outpath =  Path("input", "obs_"+self.fpre+"_"+self.observations_tgt.tgt+".tsv") #we set fpre as an artefact of old versions , its probably just predictand or predictor
		else:
			outpath = Path("input", model+"fcst_{}_".format(self.fprefix)+self.forecasts_tgt.tgt+"_ini"+self.forecasts_tgt.monf+str(self.forecasts_domain.fyr)+".tsv")

		check, outpath = self.fm.check(outpath) #filemanager looks if there is a file named this yet or not, returns true if so

		if self.fm.force_download or not check: #if user has selected force_download=True or the FileManager filecheck returned False indicating a missing input file
			if self.verbose:
				print("\033[1mWarning:\033[0;0m {0}".format("FileNotFoundError:")) #print message saying we need to download file
				print("{} precip file doesn't exist --\033[1mSOLVING: downloading file\033[0;0m".format(datatype))  #dont ask me, it prints out the message lol
				print("\n {} data - URL: \n\n ".format(datatype)+url.format(**self.arg_dict[datatype])) #print out the url - can click on the link in jupyter notebook to download the file / see where it takes you if theres an error
				self.callSys("curl -k "+url.format(**self.arg_dict[datatype])+" > {}".format(outpath)) #curl is a command line utility that asks a website for the files it serves - we give it the url of an IRIDL download link
			else:
				f = open('./results.out', 'a')
				f.write("\033[1mWarning:\033[0;0m {0}".format("FileNotFoundError:\n"))
				f.write("{} precip file doesn't exist --\033[1mSOLVING: downloading file\033[0;0m\n".format(datatype))
				f.write("\n {} data - URL: \n\n ".format(datatype)+url.format(**self.arg_dict[datatype]))
				self.callSys("curl -k "+url.format(**self.arg_dict[datatype])+" 2> {} > {}".format(str(outpath)[:-4] + '.out', outpath)) #curl is a command line utility that asks a website for the files it serves - we give it the url of an IRIDL download link
				f.close()
			if self.obs_source=='home/.xchourio/.ACToday/.CHL/.prcp':   #weirdly enough, Ingrid sends the file with nfields=0. This is my solution for now. AGM
				replaceAll("./input/obs_"+self.predictor+"_"+self.observations_tgt.tgt+".tsv","cpt:nfields=0","cpt:nfields=1") #unclear

		if self.verbose:  #if force_download is false and check returns that it found the files, no need to download
			print('{} file ready to go'.format(datatype))
			print('----------------------------------------------')
		else:
			f = open('./results.out', 'a')
			f.write('Preparing CPT files for '+model+' and initialization '+self.hindcasts_tgt.init+'...\n')
			f.close()

	def fetch_one(self, model, datatype, arg_dict):
		"""downloads data from the IRI Data Library Using Ingrid for one model if passed a dict filled with the args to put into the IRIDL url"""
		if datatype == 'Observations': #Get the proper URL from the URL dict defined in constructor - different datatypes have different key patterns, so you need the if/else
			url = self.url_dict[datatype][arg_dict['fprefix']][arg_dict['threshold_pctle'] if arg_dict['fprefix'] == 'RFREQ' else arg_dict['obs'] ]
		else:
			url = self.url_dict[datatype][arg_dict['fprefix']][model]

		if datatype == 'Hindcasts':
			outpath =  Path('input', model+"_{}_".format(arg_dict['fprefix'])+arg_dict['tgt']+"_ini"+arg_dict['init']+".tsv")
		elif datatype == 'Observations':
			outpath =  Path("input", "obs_"+arg_dict['fpre']+"_"+arg_dict['tgt']+".tsv") #we set fpre as an artefact of old versions , its probably just predictand or predictor
		else:
			outpath = Path("input", model+"fcst_{}_".format(arg_dict['fprefix'])+arg_dict['tgt']+"_ini"+arg_dict['monf']+str(arg_dict['fyr'])+".tsv")

		check, outpath = self.fm.check(outpath) #filemanager looks if there is a file named this yet or not, returns true if so

		if self.fm.force_download or not check: #if user has selected force_download=True or the FileManager filecheck returned False indicating a missing input file
			if self.verbose:
				print("\033[1mWarning:\033[0;0m {0}".format("FileNotFoundError:")) #print message saying we need to download file
				print("{} precip file doesn't exist --\033[1mSOLVING: downloading file\033[0;0m".format(datatype))  #dont ask me, it prints out the message lol
				print("\n {} data - URL: \n\n ".format(datatype)+url.format(**self.arg_dict[datatype])) #print out the url - can click on the link in jupyter notebook to download the file / see where it takes you if theres an error
				self.callSys("curl -k "+url.format(**self.arg_dict[datatype])+" > {}".format(outpath)) #curl is a command line utility that asks a website for the files it serves - we give it the url of an IRIDL download link
			else:
				f = open('./results.out', 'a')
				f.write("\033[1mWarning:\033[0;0m {0}".format("FileNotFoundError:\n"))
				f.write("{} precip file doesn't exist --\033[1mSOLVING: downloading file\033[0;0m\n".format(datatype))
				f.write("\n {} data - URL: \n\n ".format(datatype)+url.format(**self.arg_dict[datatype]))
				self.callSys("curl -k "+url.format(**self.arg_dict[datatype])+" 2> {} > {}".format(str(outpath)[:-4] + '.out', outpath)) #curl is a command line utility that asks a website for the files it serves - we give it the url of an IRIDL download link
				f.close()
			if arg_dict['obs_source']=='home/.xchourio/.ACToday/.CHL/.prcp':   #weirdly enough, Ingrid sends the file with nfields=0. This is my solution for now. AGM
				replaceAll("./input/obs_"+arg_dict['predictor']+"_"+arg_dict['tgt']+".tsv","cpt:nfields=0","cpt:nfields=1") #unclear

		if self.verbose:  #if force_download is false and check returns that it found the files, no need to download
			print('{} file ready to go'.format(datatype))
			print('----------------------------------------------')
		else:
			f = open('./results.out', 'a')
			f.write('Preparing CPT files for '+model+' and initialization '+arg_dict['init']+'...\n')
			f.close()


	def prep_files(self, model):
		"""Function to download (or not) the needed files"""
		if model not in self.models:
			if self.verbose:
				print("unvalidated model - you may get an unexpected error")
			else:
				f = open('./results.out', 'a')
				f.write("unvalidated model - you may get an unexpected error\n")
		if self.verbose:
			print('Preparing CPT files for '+model+' and initialization '+self.hindcasts_tgt.init+'...')
		else:
			f = open('./results.out', 'a')
			f.write("'Preparing CPT files for '+model+' and initialization '+self.hindcasts_tgt.init+'...\n")
			f.close()
		self.fetch(model, 'Hindcasts') # download  HIndcasts data
		self.fetch(model, 'Observations') #download observatiosn data
		self.fetch(model, 'Forecasts')  #download forecasts data

	def __setup(self):
		"""housekeeping to do"""
		obs_sources = {'CPC-CMAP-URD':'SOURCES/.Models/.NMME/.CPC-CMAP-URD/prate',
			'TRMM':'SOURCES/.NASA/.GES-DAAC/.TRMM_L3/.TRMM_3B42/.v7/.daily/.precipitation/X/-180./1.5/180./GRID/Y/-50/1.5/50/GRID',
			'CPC': 'SOURCES/.NOAA/.NCEP/.CPC/.UNIFIED_PRCP/.GAUGE_BASED/.GLOBAL/.v1p0/.extREALTIME/.rain/X/-180./1.5/180./GRID/Y/-90/1.5/90/GRID',
			'CHIRPS':'SOURCES/.UCSB/.CHIRPS/.v2p0/.daily-improved/.global/.0p25/.prcp/'+str(self.observations_tgt.ndays)+'/mul',
			'Chilestations': 'home/.xchourio/.ACToday/.CHL/.prcp',
			'GPCC':'SOURCES/.WCRP/.GCOS/.GPCC/.FDP/.version7/.0p5/.prcp/'+str(self.observations_tgt.nmonths)+'/mul',
			'ENACTS-BD':'SOURCES/.Bangladesh/.BMD/.monthly/.rainfall/.rfe_merged/'+str(self.observations_tgt.nmonths)+'/mul'
		} #This is part of the ingrid code for fetching each of these observations datasets
		self.obs_source = obs_sources[self.obs] #select correct Ingrid code for our observation choices

		hdate_lasts = {'CPC-CMAP-URD':2010,
			'TRMM':2014,
			'CPC': 2018,
			'CHIRPS':2018,
			'Chilestations': 2019,
			'GPCC': 2013,
			'ENACTS-BD':2020
		} #I believe this variable represents the last year that each of these datasets has data for? but i am not sure
		self.hdate_last = hdate_lasts[self.obs]

		# set up Predictor switches
		self.rainfall_frequency = False if self.predictor in ['PRCP', 'UQ','VQ'] else True #False uses total rainfall for forecast period, True uses frequency of rainy days
		self.threshold_pctle = False if self.predictor in ['PRCP', 'UQ','VQ'] else False #False for threshold in mm; Note that if True then if counts DRY days!!!
		self.wetday_threshold = -999 if self.predictor in ['PRCP', 'UQ','VQ'] else 3 #WET day threshold (mm) --only used if rainfall_frequency is True!

		if self.verbose:
			if self.rainfall_frequency:
				print('Predictand is Rainfall Frequency; wet day threshold = '+str(self.wetday_threshold)+' mm')
			else:
				print('Predictand is Rainfall Total (mm)')
		else:
			f = open('./results.out', 'a')
			if self.rainfall_frequency:
				f.write('Predictand is Rainfall Frequency; wet day threshold = '+str(self.wetday_threshold)+' mm\n')
			else:
				f.write('Predictand is Rainfall Total (mm)\n')
			f.close()
		self.fpre = 'RFREQ' if self.fprefix == 'RFREQ' else 'PRCP' #neeeded when fetching obs files for some reason

	def validate_args(self,  models, obs, station, predictor, predictand):
		"""Make sure all arguments are valid"""
		#tgt & domains should be validated during its construction, no need to repeat
		retval = True
		valid_models = ['NextGen', 'CMC1-CanCM3', 'CMC2-CanCM4', 'CanSIPSv2', 'COLA-RSMAS-CCSM4', 'GFDL-CM2p5-FLOR-A06', 'GFDL-CM2p5-FLOR-B01','GFDL-CM2p1-aer04', 'NASA-GEOSS2S', 'NCEP-CFSv2']
		for model in models: #check each model for validity
			if model not in valid_models:
				if self.verbose:
					print('{} Not a valid model'.format(model))
				retval = retval and False

		valid_obs = ['CPC-CMAP-URD', 'CHIRPS', 'TRMM', 'CPC', 'Chilestations','GPCC', 'ENACTS-BD']
		if obs not in valid_obs:  #check if user requested a valid observations source
			if self.verbose:
				print('{} not a valid observations source'.format(obs))
			retval = retval and False

		if station not in [True, False]:
			if self.verbose:
				print('Station must be boolean - True, or False')
			retval = retval and False

		valid_preds = ['PRCP', 'RFREQ', 'UQ', 'VQ']
		if predictor not in valid_preds:
			if self.verbose:
				print('{} not a valid predictor - must be one of {}'.format(predictor, valid_preds))
			retval = retval and False

		valid_preds = ['PRCP', 'RFREQ']
		if predictand not in valid_preds:
			if self.verbose:
				print('{} not a valid predictand - must be one of {}'.format(predictand, valid_preds))
			retval = retval and False

		return retval

	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if vars(self)[key] != vars(other)[key]:
				ret = False
		return ret
