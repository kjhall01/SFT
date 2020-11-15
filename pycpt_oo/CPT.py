from __future__ import print_function
import sys, os
import json
from pathlib import Path
import platform, copy, warnings
import subprocess
import struct, copy, json
import numpy as np
import datetime as d


class CPT:
	"""A Class for Abstracting CPT-related tasks like CPTscript and writeCPT
	---------------------------------------------------------------------------
	Variables:
		cpt (Path):	path to CPT.x or CPT_batch.exe
		modes (Modes):	holds all the cca / x / y /eof modes parameters
		MOS (str)	 : 	indicates which model output statistic we're using - ['PCR', 'CCA', 'ELR', 'None']
		MOSs (dict)	 : 	predefined dict that lets us convert MOS to mpref
		mpref (str)	 :	string describing MOS- not sure why we dont use MOS but here we are
		met (list)	 :	list of metrics to use - must be from ['Pearson','Spearman','2AFC','RocAbove','RocBelow', 'RMSE',  'Ignorance', 'RPSS', 'GROC']
		verbose (Boolean): Whether or not to print output
	---------------------------------------------------------------------------
	Class Methods (callable without instantiation):
		None
	---------------------------------------------------------------------------
	Object Methods:
		callSys(arg) -> runs a system command
		__init__(cptdir: Path, modes: Modes, MOS: str, met: list	) -> Mode (holds modes for CPT)
		validate_args( same as init ) -> Boolean (returns false if there are invalid parameters)
		write_cpt_script( IRIDL: IRIDL, model: str) -> None (writes a CPT file)
		run (IRIDL: IRIDL, model: str) -> None (Runs CPT for a given season / domain and model )
		set_model_output_statistic (newmos: str) -> None (sets MOS and mpref)
	---------------------------------------------------------------------------"""
	def callSys(self, arg):
		"""Calling a system command, but get_ipython().system breaks too easily when youre not in a jupyter notebook"""
		try:
			get_ipython().system(arg)
		except:
			subprocess.check_output(arg, shell=True)

	def __init__(self, cptdir, modes, MOS, met, verbose=True):
		self.verbose = verbose
		if not self.validate_args(cptdir, MOS, met):
			print('Fix your parameters!')
			return -999
		self.cpt = str(Path(cptdir, 'CPT_batch.exe' )) if platform.system() == "Windows" else str(Path(cptdir, 'CPT.x')) #this is part of what makes it platform independent
		self.modes, self.MOS, self.met = modes, MOS, met
		self.MOSs = {"None": "noMOS", "CCA":"CCA", "PCR":"PCR", "ELR":"ELRho"} #just so we can set mpref, though its only used in filenames now
		self.mpref = self.MOSs[self.MOS]

	def set_model_output_statistic(self, newmos):
		self.MOS=newmos
		self.mpref = self.MOSs[self.MOS]

	def write_cpt_script(self, IRIDL, model):
		"""write a CPT script using an IRIDL object and a model name"""
		MOS_options = {'CCA':611, 'PCR':612, 'ELR':614, 'None':614}

		# Set up CPT parameter file
		f=open("./scripts/params","w")
		f.write("{}\n".format(MOS_options[self.MOS]))


		# First, ask CPT to stop if error is encountered
		f.write("571\n")
		f.write("3\n")

		# Opens X input file
		f.write("1\n")
		file='./input/'+model+'_'+IRIDL.fprefix+'_'+IRIDL.hindcasts_tgt.tgt+'_ini'+IRIDL.hindcasts_tgt.init+'.tsv\n'
		f.write(file)
		# Nothernmost latitude
		f.write(str(IRIDL.hindcasts_domain.nla)+'\n')
		# Southernmost latitude
		f.write(str(IRIDL.hindcasts_domain.sla)+'\n')
		# Westernmost longitude
		f.write(str(IRIDL.hindcasts_domain.wlo)+'\n')
		# Easternmost longitude
		f.write(str(IRIDL.hindcasts_domain.elo)+'\n')

		if self.MOS=='CCA' or self.MOS=='PCR':
			# Minimum number of X modes
			f.write("{}\n".format(self.modes.xmodes_min))
			# Maximum number of X modes
			f.write("{}\n".format(self.modes.xmodes_max))

			# Opens forecast (X) file
			f.write("3\n")
			file='./input/'+model+'fcst_'+IRIDL.fprefix+'_'+IRIDL.forecasts_tgt.tgt+'_ini'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'.tsv\n'
			f.write(file)
			#Start forecast:
			f.write("223\n")
			if IRIDL.forecasts_tgt.monf=="Dec":
				f.write(str(IRIDL.forecasts_domain.fyr+1)+"\n")
			else:
				f.write(str(IRIDL.forecasts_domain.fyr)+"\n")

		# Opens Y input file
		f.write("2\n")
		file='./input/obs_'+IRIDL.predictand+'_'+IRIDL.observations_tgt.tgt+'.tsv\n'
		f.write(file)
		if IRIDL.station==False:
			# Nothernmost latitude
			f.write(str(IRIDL.observations_domain.nla)+'\n')
			# Southernmost latitude
			f.write(str(IRIDL.observations_domain.sla)+'\n')
			# Westernmost longitude
			f.write(str(IRIDL.observations_domain.wlo)+'\n')
			# Easternmost longitude
			f.write(str(IRIDL.observations_domain.elo)+'\n')
		if self.MOS=='CCA':
			# Minimum number of Y modes
			f.write("{}\n".format(self.modes.ymodes_min))
			# Maximum number of Y modes
			f.write("{}\n".format(self.modes.ymodes_max))

			# Minimum number of CCA modes
			f.write("{}\n".format(self.modes.ccamodes_min))
			# Maximum number of CCAmodes
			f.write("{}\n".format(self.modes.ccamodes_max))

		# X training period
		f.write("4\n")
		# First year of X training period
		if IRIDL.hindcasts_tgt.monf in ['Dec', 'Nov']:
			f.write("{}\n".format(IRIDL.hindcasts_domain.tini+1))
		else:
			f.write("{}\n".format(IRIDL.hindcasts_domain.tini))
		# Y training period
		f.write("5\n")
		# First year of Y training period
		if IRIDL.forecasts_tgt.monf in ['Dec', 'Nov']:
			f.write("{}\n".format(IRIDL.forecasts_domain.tini+1))
		else:
			f.write("{}\n".format(IRIDL.forecasts_domain.tini))


		# Goodness index
		f.write("531\n")
		# Kendall's tau
		f.write("3\n")

		# Option: Length of training period
		f.write("7\n")
		# Length of training period
		f.write(str(IRIDL.h_ntrain)+'\n')
		#	%store 55 >> params
		# Option: Length of cross-validation window
		f.write("8\n")
		# Enter length
		f.write("3\n")

		if self.MOS!="None":
			# Turn ON transform predictand data
			f.write("541\n")

		if IRIDL.fprefix=='RFREQ':
			# Turn ON zero bound for Y data	 (automatically on by CPT if variable is precip)
			f.write("542\n")
		# Turn ON synchronous predictors
		f.write("545\n")
		# Turn ON p-values for masking maps
		#f.write("561\n")

		### Missing value options
		f.write("544\n")
		# Missing value X flag:
		blurb='-999\n'
		f.write(blurb)
		# Maximum % of missing values
		f.write("10\n")
		# Maximum % of missing gridpoints
		f.write("10\n")
		# Number of near-neighbors
		f.write("1\n")
		# Missing value replacement : best-near-neighbors
		f.write("4\n")
		# Y missing value flag
		blurb='-999\n'
		f.write(blurb)
		# Maximum % of missing values
		f.write("10\n")
		# Maximum % of missing stations
		f.write("10\n")
		# Number of near-neighbors
		f.write("1\n")
		# Best near neighbor
		f.write("4\n")

		# Transformation settings
		#f.write("554\n")
		# Empirical distribution
		#f.write("1\n")

		#######BUILD MODEL AND VALIDATE IT	!!!!!

		# NB: Default output format is GrADS format
		# select output format
		f.write("131\n")
		# GrADS format
		f.write("3\n")

		# save goodness index
		f.write("112\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_Kendallstau_'+IRIDL.hindcasts_tgt.tgt+'_'+IRIDL.hindcasts_tgt.tgt+'\n'
		f.write(file)

		# Build cross-validated model
		f.write("311\n")

		# save EOFs
		if self.MOS=='CCA' or self.MOS=='PCR' :    #kjch092120
			f.write("111\n")
			#X EOF
			f.write("302\n")
			file= './output/'+model +'_'+ IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_EOFX_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
			f.write(file)
			#Exit submenu
			f.write("0\n")
		if self.MOS=='CCA' :        #kjch092120
			f.write("111\n")
			#Y EOF
			f.write("312\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_EOFY_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
			f.write(file)
			#Exit submenu
			f.write("0\n")

		# cross-validated skill maps
		f.write("413\n")
		# save Pearson's Correlation
		f.write("1\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_Pearson_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# cross-validated skill maps
		f.write("413\n")
		# save Spearmans Correlation
		f.write("2\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_Spearman_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# cross-validated skill maps
		f.write("413\n")
		# save 2AFC score
		f.write("3\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_2AFC_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# cross-validated skill maps
		f.write("413\n")
		# save RocBelow score
		f.write("15\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_RocBelow_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# cross-validated skill maps
		f.write("413\n")
		# save RocAbove score
		f.write("16\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_RocAbove_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# cross-validated skill maps
		f.write("413\n")
		# save RocAbove score
		f.write("7\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_RMSE_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)



		if self.MOS=='CCA' or self.MOS=='PCR' or self.MOS=='None':  #kjch092120 #DO NOT USE CPT to compute probabilities if MOS='None' --use IRIDL for direct counting
			#######FORECAST(S)	!!!!!
			# Probabilistic (3 categories) maps
			f.write("455\n")
			# Output results
			f.write("111\n")
			# Forecast probabilities
			f.write("501\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_P_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			#502 # Forecast odds
			#Exit submenu
			f.write("0\n")

			# Compute deterministc values and prediction limits
			f.write("454\n")
			# Output results
			f.write("111\n")
			# Forecast values
			f.write("511\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_V_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			#502 # Forecast odds


			#######Following files are used to plot the flexible format
			# Save cross-validated predictions
			f.write("201\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_xvPr_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save deterministic forecasts [mu for Gaussian fcst pdf]
			f.write("511\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_mu_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save prediction error variance [sigma^2 for Gaussian fcst pdf]
			f.write("514\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_var_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save z
			f.write("532\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_z_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save predictand [to build predictand pdf]
			f.write("102\n")
			file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'FCST_Obs_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)

			#Exit submenu
			f.write("0\n")

			# Change to ASCII format to send files to DL
			f.write("131\n")
			# ASCII format
			f.write("2\n")
			# Output results
			f.write("111\n")
			# Save cross-validated predictions
			f.write("201\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_xvPr_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save deterministic forecasts [mu for Gaussian fcst pdf]
			f.write("511\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_mu_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Forecast probabilities
			f.write("501\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_P_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save prediction error variance [sigma^2 for Gaussian fcst pdf]
			f.write("514\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_var_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save z
			f.write("532\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_z_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Save predictand [to build predictand pdf]
			f.write("102\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'FCST_Obs_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)

			# cross-validated skill maps
			if self.MOS=="PCR" or self.MOS=="CCA" or self.MOS=="None": #kjch092120
				f.write("0\n")

			# cross-validated skill maps
			f.write("413\n")
			# save 2AFC score
			f.write("3\n")
			file='./output/'+model+'_'+IRIDL.fprefix+'_'+self.mpref+'_2AFC_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
			f.write(file)
			# Stop saving  (not needed in newest version of CPT)

		###########PFV --Added by AGM in version 1.5
		#Compute and write retrospective forecasts for prob skill assessment.
		#Re-define forecas file if PCR or CCA
		if self.MOS=="PCR" or self.MOS=="CCA" or self.MOS=="None" : #kjch092120
			f.write("3\n")
			file='./input/'+model+'_'+IRIDL.fprefix+'_'+IRIDL.forecasts_tgt.tgt+'_ini'+IRIDL.forecasts_tgt.init+'.tsv\n'  #here a conditional should choose if rainfall freq is being used
			f.write(file)
		#Forecast period settings
		f.write("6\n")
		# First year to forecast. Save ALL forecasts (for "retroactive" we should only assess second half)
		if IRIDL.forecasts_tgt.monf=="Oct" or IRIDL.forecasts_tgt.monf=="Nov" or IRIDL.forecasts_tgt.monf=="Dec":
			f.write(str(IRIDL.forecasts_domain.tini+1)+'\n')
		else:
			f.write(str(IRIDL.forecasts_domain.tini)+'\n')

		#Number of forecasts option
		f.write("9\n")
		# Number of reforecasts to produce
		if IRIDL.forecasts_tgt.monf=="Oct" or IRIDL.forecasts_tgt.monf=="Nov" or IRIDL.forecasts_tgt.monf=="Dec":
			f.write(str(IRIDL.f_ntrain-1)+'\n')
		else:
			f.write(str(IRIDL.f_ntrain)+'\n')
		# Change to ASCII format
		f.write("131\n")
		# ASCII format
		f.write("2\n")
		# Probabilistic (3 categories) maps
		f.write("455\n")
		# Output results
		f.write("111\n")
		# Forecast probabilities --Note change in name for reforecasts:
		f.write("501\n")
		file='./output/'+model+'_RFCST_'+IRIDL.fprefix+'_'+IRIDL.forecasts_tgt.tgt+'_ini'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'\n'
		f.write(file)
		#502 # Forecast odds
		#Exit submenu
		f.write("0\n")

		# Close X file so we can access the PFV option
		f.write("121\n")
		f.write("Y\n")  #Yes to cleaning current results:# WARNING:
		#Select Probabilistic Forecast Verification (PFV)
		f.write("621\n")
		# Opens X input file
		f.write("1\n")
		file='./output/'+model+'_RFCST_'+IRIDL.fprefix+'_'+IRIDL.forecasts_tgt.tgt+'_ini'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'.txt\n'
		f.write(file)
		# Nothernmost latitude
		f.write(str(IRIDL.hindcasts_domain.nla)+'\n')
		# Southernmost latitude
		f.write(str(IRIDL.hindcasts_domain.sla)+'\n')
		# Westernmost longitude
		f.write(str(IRIDL.hindcasts_domain.wlo)+'\n')
		# Easternmost longitude
		f.write(str(IRIDL.hindcasts_domain.elo)+'\n')

		f.write("5\n")
		# First year of the PFV
		# for "retroactive" only first half of the entire training period is typically used --be wise, as sample is short)
		if IRIDL.forecasts_tgt.monf=="Oct" or IRIDL.forecasts_tgt.monf=="Nov" or IRIDL.forecasts_tgt.monf=="Dec":
			f.write(str(IRIDL.forecasts_domain.tini+1)+'\n')
		else:
			f.write(str(IRIDL.forecasts_domain.tini)+'\n')


		#If these prob forecasts come from a cross-validated prediction (as it's coded right now)
		#we don't want to cross-validate those again (it'll change, for example, the xv error variances)
		#Forecast Settings menu
		f.write("552\n")
		#Conf level at 50% to have even, dychotomous intervals for reliability assessment (as per Simon suggestion)
		f.write("50\n")
		#Fitted error variance option  --this is the key option: 3 is 0-leave-out cross-validation, so no cross-validation!
		f.write("3\n")
		#-----Next options are required but not really used here:
		#Ensemble size
		f.write("10\n")
		#Odds relative to climo?
		f.write("N\n")
		#Exceedance probabilities: show as non-exceedance?
		f.write("N\n")
		#Precision options:
		#Number of decimal places (Max 8):
		f.write("3\n")
		#Forecast probability rounding:
		f.write("1\n")
		#End of required but not really used options ----

		#Verify
		f.write("313\n")

		#Reliability diagram
		f.write("431\n")
		f.write("Y\n") #yes, save results to a file
		file='./output/'+model+'_RFCST_reliabdiag_'+IRIDL.fprefix+'_'+IRIDL.forecasts_tgt.tgt+'_ini'+IRIDL.forecasts_tgt.monf+str(IRIDL.forecasts_domain.fyr)+'.tsv\n'
		f.write(file)

		# select output format -- GrADS, so we can plot it in Python
		f.write("131\n")
		# GrADS format
		f.write("3\n")

		# Probabilistic skill maps
		f.write("437\n")
		# save Ignorance (all cats)
		f.write("101\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_Ignorance_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# Probabilistic skill maps
		f.write("437\n")
		# save Ranked Probability Skill Score (all cats)
		f.write("122\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_RPSS_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)

		# Probabilistic skill maps
		f.write("437\n")
		# save Ranked Probability Skill Score (all cats)
		f.write("131\n")
		file='./output/'+model+'_'+IRIDL.fprefix+IRIDL.predictand+'_'+self.mpref+'_GROC_'+IRIDL.forecasts_tgt.tgt+'_'+IRIDL.forecasts_tgt.init+'\n'
		f.write(file)


		# Exit
		f.write("0\n")
		f.write("0\n")
		f.close()
		if platform.system() == 'Windows':
			self.callSys("cd scripts && copy params "+model+"_"+IRIDL.fprefix+"_"+self.mpref+"_"+IRIDL.forecasts_tgt.tgt+"_"+IRIDL.forecasts_tgt.init+".cpt")
		else:
			self.callSys("cp ./scripts/params ./scripts/"+model+"_"+IRIDL.fprefix+"_"+self.mpref+"_"+IRIDL.forecasts_tgt.tgt+"_"+IRIDL.forecasts_tgt.init+".cpt")

	def run(self, IRIDL, model):
		if self.verbose:
			print('Executing CPT for '+model+' and initialization '+IRIDL.hindcasts_tgt.init+'...')
		else:
			f = open('./results.out', 'a')
			f.write('Executing CPT for '+model+' and initialization '+IRIDL.hindcasts_tgt.init+'...\n')
			f.close()
		try: #this calls CPT and runs it on the inputs we downloaded with the script we just wrote
			subprocess.check_output(self.cpt + ' < ./scripts/params > ./scripts/CPT_stout_train_'+model+'_'+IRIDL.hindcasts_tgt.tgt+'_'+IRIDL.hindcasts_tgt.init+'.txt',stderr=subprocess.STDOUT, shell=True) #Calls CPT with a params.cpt input file
		except subprocess.CalledProcessError as e:
			if self.verbose:
				print("CPT Windows version throws an error right at the end of its operation- everything should be fine for the rest of this notebook, but you need to click 'close' on the 'Access Violation' Window that pops up for now. ")
			else:
				f = open('./results.out', 'a')
				f.write("CPT Windows version throws an error right at the end of its operation- everything should be fine for the rest of this notebook, but you need to click 'close' on the 'Access Violation' Window that pops up for now. \n")
				f.close()
		if self.verbose:
			print('----------------------------------------------')
			print('Calculations for '+IRIDL.hindcasts_tgt.init+' initialization completed!')
			print('See output folder, and check scripts/CPT_stout_train_'+ model+'_'+IRIDL.hindcasts_tgt.tgt+'_'+IRIDL.hindcasts_tgt.init+'.txt for errors')
			print('----------------------------------------------')
			print('----------------------------------------------\n\n\n')

	def validate_args(self, cptdir, MOS, met):
		retval = True
		if not os.path.isdir(cptdir):
			if self.verbose:
				print('CPTdir must be an existing directory!')
			retval = retval and False

		if platform.system == "Windows":
			if not os.path.isfile(str(Path(cptdir, "CPT_batch.exe"))):
				if self.verbose:
					print('On Windows, CPT_batch.exe must be in CPTdir!')
				retval = retval and False
		else:
			if not os.path.isfile(str(Path(cptdir, "CPT.x"))):
				if self.verbose:
					print('On Mac/Unix, CPT.x must be inside CPTdir!')
				retval = retval and False

		valid_mets = ['Pearson','Spearman','2AFC','RocAbove','RocBelow', 'RMSE',  'Ignorance', 'RPSS', 'GROC']
		for metric in met:
			if metric not in valid_mets:
				if self.verbose:
					print('{} not a valid metric- must be one of {}'.format(metric, valid_mets))
				retval = retval and False

		valid_mos = ['PCR', 'CCA', 'ELR', 'None']
		if MOS not in valid_mos:
			if self.verbose:
				print('{} not a valid MOS - must be one of {}'.format(MOS, valid_mos))
			retval = retval and False
		return retval

	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if vars(self)[key] != vars(other)[key]:
				ret = False
		return ret
