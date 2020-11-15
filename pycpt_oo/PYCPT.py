from __future__ import print_function
import sys, os
import json
from pathlib import Path
import platform, copy, warnings
import subprocess
import struct, copy, json
import numpy as np
import datetime as d

import cartopy.crs as ccrs
from cartopy import feature
import cartopy.mpl.ticker as cticker
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
import fileinput
import matplotlib as mpl
from IPython import get_ipython
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
warnings.filterwarnings("ignore")

from .ArgSet import ArgSet
from .CPT import CPT
from .Domain import Domain
from .FileManager import FileManager
from .IRIDL import IRIDL
from .MetaTensor import MetaTensor
from .MidpointNormalize import MidpointNormalize
from .Modes import Modes
from .TargetSeason import TargetSeason
from .Visualizer import Visualizer

class PYCPT:
	"""Wrapper class for holding all the stuff we put in the notebook & automating testing
	----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	Variables:
		work (str)		:	A string describing the name of a directory into which we will put everything we make 																																																	- validated by FileManager constructor
		workdir (str)	:	string holding absolute path to work folder 																																																											- validated by FileManager Constructor
		cptdir (str)	:	string holding path to folder containing CPT_batch.exe or CPT.x 																																																						- validated by CPT constructor
		use_topo (str)	:	string-cast Boolean (so, "False", or "True") indicating whether to use pixelated topographic imagery in pltdomain 																																										- validated by Visualizer Constructor, plotting functions
		shp_file (str)	:	string holding path to a custom shape file for plotting maps																																																							- validated by Visualizer Constructor, plotting functions
		use_default (str) :	string-cast Boolean (like use_topo) indicating whether to use default shape files for mapping																																															- validated by Visualizer Constructor, plotting functions
		map_color (str)	:	either a pyplot colormap string name, or 'CPT'																																																											- validated by Visualizer Constructor, plotting functions
		models (list)	: 	a list of models to run CPT for - must be one or more of CMC1-CanCM3, CMC2-CanCM4,  COLA-RSMAS-CCSM4, GFDL-CM2p5-FLOR-A06, GFDL-CM2p5-FLOR-B01,GFDL-CM2p1-aer04, NASA-GEOSS2S, NCEP-CFSv2) 																								- validated by IRIDL constructor
		tgts (list)		:	a list of target seasons to run CPT for - must be like 'Jun-Sep', 'Aug-Oct', or a single month like "Sep" 																																												- validated by TargetSeason constructor
		met (list)		:	a list of metrics to use to evaluate performance of each model's forecast- must be one or more of   'Pearson','Spearman','2AFC','RocAbove','RocBelow', 'RMSE',  'Ignorance', 'RPSS', 'GROC' 																							- validated by CPT constructor
		obs (str)		:	a string describing which observations data set to use - one of CPC-CMAP-URD, CHIRPS, TRMM, CPC, Chilestations,GPCC 																																									- validated by IRIDL constructor
		station (Bool)	:	True or False (not a string) indicating whether observations are station data or not: 																																																	- validated by IRIDL constructor
		MOS (str)		:	string describing method of model output statistic to use for calibration - one of 'CCA', 'PCR', 'ELR', or 'None' 																																									 	- validated by CPT constructor
		xmodes_min (int) :	int (1-5) describing minimum number of EOF modes to use for input data (hindcasts) if performing PCR or CCA 																																											- validated by Modes constructor
		xmodes_max (int) :	int (1-5), > xmodes_min describing maximum number of EOF modes to use for input data (hindcasts) if performing PCR or CCA 																																								- validated by Modes constructor
		ymodes_min (int) :	int (1-5) describing minimum number of EOF modes to use for output data (observations) if performing CCA 																																												- validated by Modes constructor
		ymodes_max (int) :	int (1-5), > ymodes_min describing maximum number of EOF modes to use for output data (observations) if performing CCA 																																									- validated by Modes constructor
		ccamodes_min (int) :	int (1-5) describing minimum number of EOF modes to use for output data (observations) if performing CCA 																																												- validated by Modes constructor
		ccamodes_max (int) :	int (1-5), > ccamodes_min describing maximum number of EOF modes to use for output data (observations) if performing CCA 																																								- validated by Modes constructor
		eofmodes (int)	:	number of EOF modes to compute - i would assume that this limits the other modes variables too, but idk 																																												- validated by Modes constructor
		predictand (str) :	string describing type of predictand data (for now, only PRCP and RFREQ) 																																																				- validated by IRIDL constructor
		predictor (str)	:	string describing type of predictor data (for now only PRCP - UQ and VQ only work for NCEP-CFSv2)																																														- validated by IRIDL constructor
		mons (list)		:	(called 'init' by the rest of the code) list of strings describing initialization months of the hindcasts for X (input) data (pretending the forecast was made in this month, before the target season 'May', etc)																		- validated by TargetSeason constructor
		tgti (list)		:	list of strings describing # of months from initialzation month to the middle of the first month of the target season (eg, '1.5' for initialization of may, and target season of June (May 1 - June 15). 2.5 for init may target of July (may 1 - july 15) ). Artefact of iridl			-calculated by TargetSeason Constructor
		tgtf (list)		:	same as tgti but for describing # months from init to middle of last month of target season ie 4.5 for init may tgt jun-sep may 1 to sep 15																																				-calculated by TargetSeason Constructor
		tini (int)		:	first year of training data 																																																															- validated by domain constructor
		tend (int)		: 	last year of training data 																																																																- validated by domain constructor
		monf (list)		:	list of initialization months for forecasts 																																																											- validated by TargetSeason constructor
		fyr (int)		:	year of forecast																																																																		- validated by TargetSeason constructor
		force_download (Boolean) : 	True or False - force redownload of data even if it exists locally 																																																				- validated by FileManager constructor
		nla1, sla1 (ints) :	northermost & southernmost latitudes of predictor (GCM data) spatial domain 																																																			- validated by Modes constructor
		elo1, wlo1 (ints) :	easternmost & westernnmost longitudes of predictor (GCM data) spatial domain 																																																			- validated by Modes constructor
		nla2, sla2 (ints) :	northermost & southernmost latitudes of predictand (observations) spatial domain																																																		- validated by Modes constructor
		elo2, wlo2 (ints) :	easternmost & westernnmost longitudes of predictand (observations) spatial domain 																																																		- validated by Modes constructor
	------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	Class Methods (Callable without instantiation):
		from_file(filename: str) -> PYCPT (loads a previously saved set of PYCPT run parameters)
		test(test: str) -> runs the pycpt script for every saved parameter set in this tests folder
	---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	Object Methods:
		__init__(all args) -> PYCPT  (Constructor)
		save() -> None (Saves current run parameters to file)
		execute() -> runs entire script of jupyter notebook without plotting or printing anything
		pltdomain() -> Plots Predictor / Predictand Domains (calls Visualizer.pltdomain )
		prepFiles(tgt_index: int, model: str) -> Downloads data for a given model and seasn ( calls IRIDLs[tgt_index].prep_files(model) )
		CPTscript(tgt_index: int, model: str) -> Writes a CPT script for a given model and season (calls cpt.write_cpt_script(IRIDLs[tgt_index], model)  )
		run(tgt_ndx: int, model: str) -> Runs CPT for a given model and season ( calls cpt.run(IRIDLs[tgt_index], model) )
		pltmap(metric: str) -> Plots a metric for all models and seasons  (calls vis.pltmap(metric, models, obs_argsets, MOS))
		plteofs(mode: int) -> plots eofs for all models for all seasons for a given mode (calls vis.plteofs(models, MOS, eofmodes, cur_mode, obs_argsets))
		NGensemble(models: list) -> computes nextgen multimodel ensembel for a non-strict subset of the models (calls filemanager.NGensemble(models, hindcast_argsets[tgt], MOS))
		plt_deterministic() -> plots deterministic forecast map based on nextgen  (calls vis.plt_deterministic('NextGen', obs_argsets, 'None'))
		plt_probabilistic() -> plots probabilistic forecast map based on nextgen (calls vis.plt_probabilistic('NextGen', obs_argsets, 'None'))
	------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
	def __init__(self, work, workdir, cptdir, use_topo, shp_file, use_default, map_color, models, tgts, met, obs, station, MOS, xmodes_min, xmodes_max, ymodes_min, ymodes_max, ccamodes_min, ccamodes_max, eofmodes, predictand, predictor, mons, tgti, tgtf, tini, tend,monf, fyr, force_download, nla1, sla1, elo1, wlo1, nla2, sla2, elo2, wlo2, verbose=True):
		self.work, self.workdir, self.cptdir = work, workdir, cptdir
		self.use_topo, self.shp_file, self.use_default, self.map_color = use_topo, shp_file, use_default, map_color
		self.models, self.tgts, self.met, self.obs, self.station, self.MOS = models, tgts, met, obs, station, MOS
		self.xmodes_min, self.xmodes_max, self.ymodes_min, self.ymodes_max, self.ccamodes_min, self.ccamodes_max, self.eofmodes = xmodes_min, xmodes_max, ymodes_min, ymodes_max, ccamodes_min, ccamodes_max, eofmodes
		self.predictand, self.predictor, self.mons, self.tgti, self.tgtf = predictand, predictor, mons, tgti, tgtf
		self.tini, self.tend, self.monf, self.fyr, self.force_download = tini, tend,monf, fyr, force_download
		self.nla1, self.sla1, self.elo1, self.wlo1 = nla1, sla1, elo1, wlo1
		self.nla2, self.sla2, self.elo2, self.wlo2 = nla2, sla2, elo2, wlo2
		self.verbose = verbose
		self.initialized = 0
		self.params = copy.deepcopy(vars(self)) #allow us to save run params without the classes
		self.setup(verbose)

	@classmethod
	def auto_test(self, pycpt_file, testdir='..', work='.'):
		py = PYCPT.from_file(pycpt_file)
		py.workdir = str(Path(os.getcwd(), testdir))
		py.work = str( work)
		return py.test()

	@classmethod
	def run_tests(self, test_dir):
		"""tests pycpt for all saved instances in the test_dir"""
		tests, names = [], []
		for testfile in os.listdir(test_dir):
			if os.path.isfile(os.path.join(test_dir, testfile)):
				tests.append(os.path.join(test_dir, testfile))
				names.append(testfile.split('.')[0])
		os.chdir(test_dir) #testdir should be a relative path from current directory not absolute
		for name in names:
			os.system('mkdir {}'.format(name))
		os.chdir('..')
		for test in range(len(tests)):
			print('{} Running test for {}.pycpt - '.format(d.datetime.now(),names[test]), end='')
			sys.stdout.flush()
			result = self.auto_test(tests[test], test_dir, names[test])
			if result is None:
				 print(' - success for {}'.format(names[test]))
			else:
				 print(' - ' + result + ' for {}'.format(names[test]))
			print(os.getcwd())
			os.chdir('..') #go back to start dir so we can find test_dir/nexttest

	def reset(self):
		self.initialized = 0
		os.chdir(self.workdir)

	def initialize(self):
		#create filemanager object
		self.filemanager = FileManager(self.workdir, self.work, self.force_download, verbose=self.verbose)

		#create IRIDL objects for each tgt
		self.IRIDLs = [IRIDL(self.filemanager, self.obs_argsets[i], self.hindcast_argsets[i], self.forecasts_argsets[i], self.models, verbose=self.verbose) for i in range(len(self.tgts))]

		#store CPT arguments in Modes Object
		self.modes = Modes(self.xmodes_max, self.xmodes_min, self.ymodes_max, self.ymodes_min, self.ccamodes_max, self.ccamodes_min, self.eofmodes)

		#create CPT object
		self.cpt = CPT(self.cptdir, self.modes, self.MOS, self.met, verbose=self.verbose)
		self.vis = Visualizer(self.filemanager, shp_file=self.shp_file, map_color=self.map_color, use_topo=self.use_topo, verbose=self.verbose)
		self.initialized = 1

	def execute(self):
		if self.initialized == 0:
			self.initialize()
		self.pltdomain() #examine domains
		for model in self.models:
			for tgt in range(len(self.tgts)):
				self.prepFiles(model, tgt) #download data if forced or needed
				self.CPTscript(model, tgt) #write CPT scripts for models
				self.run(model, tgt) #run cpt for models
		for metric in self.met:
			self.pltmap(metric, self.models) #plot forecast metrics produced by CPT
		for mode in range(self.eofmodes):
			self.plteofs(mode) #plot eofs calculated by CPT
		for tgt in range(len(self.tgts)):
			self.NGensemble(self.models, tgt) #calculate NEXTGEN multi-model ensemble mean
			self.CPTscript('NextGen', tgt) #write CPT script for nextgen
			self.run('NextGen', tgt) #run CPT on nextgen ensemble cross-validated Prediction files
		for metric in self.met:
			self.pltmap(metric, ['NextGen'], MOS="None") #plot nextgen metrics
		self.plt_deterministic()  #make deterministic forecast with nextgen
		self.plt_probabilistic() #make probabilistic forecast with nextgen
		self.ensemblefiles() #packages files in ./output/nextgen/ asdlkfj.tar.gz for sending to IRI
		self.reset()

	def test(self):
		self.verbose = False
		i = 0
		total = 2 + len(self.met) * 2 + (len(self.models) * len(self.tgts)) + self.eofmodes + len(self.tgts) + 2 + 1 #a star for each step in the process  - initialize, pltdomain, downlao/run for each tgt/model, pltmetrics * metrics, plteofs * eofmodes, ngensemble /runcpt for each nextgen tgt season, plt metrics * nmetrics again for nextgen, pltdeterministic, plt_probabilistic, and ensemble files
		"""script for testing"""
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		try:
			if self.initialized == 0:
				self.initialize()
		except:
			return 'Failed to initialize - check validity of directory name for "work"'
		i+= 1
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		try:
			self.pltdomain() #examine domains
		except:
			return 'Failed to plot domain'
		i+= 1
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		for model in self.models:
			for tgt in range(len(self.tgts)):
				try:
					self.prepFiles(model, tgt) #download data if forced or needed
				except:
					return 'Failed to download files for {} target {}'.format(model, tgt+1)
				try:
					self.CPTscript(model, tgt) #write CPT scripts for models
				except:
					return 'Failed to write CPT script for {} target {}'.format(model, tgt+1)
				try:
					self.run(model, tgt) #run cpt for models
				except:
					return 'CPT failed for {} target {}'.format(model, tgt +1)
				i+= 1
				print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
				sys.stdout.flush()
		for metric in self.met:
			try:
				self.pltmap(metric, self.models) #plot forecast metrics produced by CPT
			except:
				return 'failed to plot {} metric'.format(metric)
			i+= 1
			print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
			sys.stdout.flush()
		for mode in range(self.eofmodes):
			try:
				self.plteofs(mode) #plot eofs calculated by CPT
			except:
				return 'failed to plot {} EOF'.format(mode+1)
			i+= 1
			print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
			sys.stdout.flush()
		for tgt in range(len(self.tgts)):
			try:
				self.NGensemble(self.models, tgt) #calculate NEXTGEN multi-model ensemble mean
			except:
				return 'Failed to calculate nextgen ensemble mean'
			try:
				self.CPTscript('NextGen', tgt) #write CPT scripts for models
			except:
				return 'Failed to write CPT script for {} target {}'.format(model, tgt+1)
			try:
				self.run('NextGen', tgt) #run cpt for models
			except:
				return 'CPT failed for {} target {}'.format(model, tgt +1)
			i+= 1
			print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
			sys.stdout.flush()
		for metric in self.met:
			try:
				self.pltmap(metric, ['NextGen'], MOS="None") #plot nextgen metrics
			except:
				return 'failed to plot {} metric for nextgen'.format(metric)
			i+= 1
			print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
			sys.stdout.flush()
		try:
			self.plt_deterministic()  #make deterministic forecast with nextgen
		except:
			return 'deterministic forecast plot failed '
		i+= 1
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		try:
			self.plt_probabilistic() #make probabilistic forecast with nextgen
		except:
			return 'probabilistic forecast plot failed'
		i+= 1
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		try:
			self.ensemblefiles() #packages files in ./output/nextgen/ asdlkfj.tar.gz for sending to IRI
		except:
			return 'failed to generate ensemblefiles '
		i+= 1
		print('\r{} Running test for {}.pycpt: [{}]'.format(d.datetime.now(),self.work, i*'*'+(total-i)*' ' ), end='')
		sys.stdout.flush()
		self.reset()
		return 'success'

	####### Start functions for hiding complicated stuff from users in notebook
	def pltdomain(self):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.vis.pltdomain(self.obs_argsets[0], self.hindcast_argsets[0])

	def prepFiles(self, model, tgt):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.IRIDLs[tgt].prep_files(model)

	def CPTscript(self, model, tgt):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		if model == 'NextGen':
			self.cpt.set_model_output_statistic('None')
		self.cpt.write_cpt_script(self.IRIDLs[tgt], model)

	def run(self, model, tgt):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.cpt.run(self.IRIDLs[tgt], model)

	def pltmap(self, metric, models, MOS=None):
		MOS = self.MOS if MOS is None else MOS
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.vis.pltmap(metric, models, self.obs_argsets, MOS)

	def plteofs(self, mode):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.vis.plteofs(self.models, self.MOS, self.eofmodes, mode, self.obs_argsets)

	def NGensemble(self, models, tgt):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.filemanager.NGensemble(models, self.forecasts_argsets[tgt], self.MOS)

	def plt_deterministic(self):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.vis.plt_deterministic('NextGen', self.forecasts_argsets, 'None')

	def plt_probabilistic(self):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.vis.plt_probabilistic('NextGen', self.forecasts_argsets, 'None')

	def ensemblefiles(self):
		if self.initialized != 1:
			print('PYCPT not initialized - call .initialize()')
			return
		self.filemanager.ensemblefiles(['NextGen'])
	#####end functions for hiding complicated stuff in notebook

	def setup(self, verbose):
		self.hind_obs_seasons = [TargetSeason(self.mons[i], self.tgts[i]) for i in range(len(self.tgts))] #create a TargetSeason for each tgt
		self.forecast_seasons = [TargetSeason(self.monf[i], self.tgts[i]) for i in range(len(self.tgts))] #create a TargetSeason for each tgt
		self.obs_domain = Domain(self.nla2, self.sla2, self.elo2, self.wlo2, self.tini, self.tend) #domain to represent observations
		self.hindcast_domain = Domain(self.nla1, self.sla1, self.elo1, self.wlo1, self.tini, self.tend) #domain to represent hindcast
		self.forecast_domain = Domain(self.nla1, self.sla1, self.elo1, self.wlo1, self.tini, self.fyr, isForecast=True)

		#put targetseasons and domains together
		self.obs_argsets = [ArgSet(self.hind_obs_seasons[i], self.obs_domain, obs=self.obs, station=self.station, predictor=self.predictor, predictand=self.predictand) for i in range(len(self.tgts))]
		self.hindcast_argsets = [ArgSet(self.hind_obs_seasons[i], self.hindcast_domain, obs=self.obs, predictor=self.predictor, predictand=self.predictand) for i in range(len(self.tgts))]
		self.forecasts_argsets = [ArgSet(self.forecast_seasons[i], self.forecast_domain, obs=self.obs, predictor=self.predictor, predictand=self.predictand) for i in range(len(self.tgts))]


	def save(self, fname=None):
		self.params = {}
		for key in vars(self).keys():
			if key not in ['IRIDLs', 'params','modes', 'cpt', 'vis', 'filemanager', 'obs_argsets', 'hindcast_argsets', 'forecasts_argsets', 'hind_obs_seasons', 'forecast_seasons', 'obs_domain' , 'hindcast_domain', 'forecast_domain']:
				self.params[key] = vars(self)[key]
		if fname is None:
			fname = self.work
		f = open(fname, 'w')
		json.dump(self.params, f, indent=4, sort_keys=True)
		f.close()

	@classmethod
	def from_file(self, fname):
		f = open(fname, 'r')
		params = json.loads(f.read())
		return PYCPT(params['work'], params['workdir'], params['cptdir'], params['use_topo'], params['shp_file'], params['use_default'], params['map_color'], params['models'], params['tgts'], params['met'], params['obs'], params['station'], params['MOS'], params['xmodes_min'], params['xmodes_max'], params['ymodes_min'], params['ymodes_max'], params['ccamodes_min'], params['ccamodes_max'], params['eofmodes'], params['predictor'], params['predictand'], params['mons'], params['tgti'], params['tgtf'], params['tini'], params['tend'], params['monf'], params['fyr'], params['force_download'], params['nla1'], params['sla1'], params['elo1'], params['wlo1'], params['nla2'], params['sla2'], params['elo2'], params['wlo2'], verbose=params['verbose'])

	def __str__(self):
		self.params = {}
		for key in vars(self).keys():
			if key not in ['IRIDLs', 'params','modes', 'cpt', 'vis', 'filemanager', 'obs_argsets', 'hindcast_argsets', 'forecasts_argsets', 'hind_obs_seasons', 'forecast_seasons', 'obs_domain' , 'hindcast_domain', 'forecast_domain']:
				self.params[key] = vars(self)[key]
		return json.dumps(self.params, indent=8)

	def __repr__(self):
		self.params = {}
		for key in vars(self).keys():
			if key not in ['IRIDLs', 'params','modes', 'cpt', 'vis', 'filemanager', 'obs_argsets', 'hindcast_argsets', 'forecasts_argsets', 'hind_obs_seasons', 'forecast_seasons', 'obs_domain' , 'hindcast_domain', 'forecast_domain']:
				self.params[key] = vars(self)[key]
		return json.dumps(self.params, indent=8)

	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if key not in ['shape_feature', 'states_provinces']:
				if vars(self)[key] != vars(other)[key]:
					ret = False
		return ret
