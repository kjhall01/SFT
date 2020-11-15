from __future__ import print_function
import sys, os
import json, struct
import numpy as np
from pathlib import Path
import platform, copy, warnings
import subprocess
from .MetaTensor import MetaTensor




class FileManager:
	"""A class for managing all the Files, Data, and Directories used in PyCPT
	---------------------------------------------------------------------------
	Variables:
		workdir (str)(2): 	a string representing the start directory, where 'work' will be created if it doesnt already exist
		work (str)		: 	a string representing the name of a new directory to be created in which all inputs and outputs will reside
		working_directory: 	a pathlib object holding the combination of workdir and work-  /workdir/work
		force_download (bool): whether or not to force erasure of files and redownload  - if true, deletes work folder
		verbose (bool)	:	boolean indicating whether or not to print everything - stuff my print anyway from system commands
	---------------------------------------------------------------------------
	Class Methods (callable without instantiation):
		None so far
	---------------------------------------------------------------------------
	Object Methods:
		callSys(arg: str) -> None (calls a command in the system)
		__init__(workdir: str, work: str, force_download: bool) -> Filemanager (constructor)
		validate_args(workdir: str, work: str, force_download: bool) -> Bool (checks if all parameters are valid)
		check(path: pathfile.Path) -> Bool, Path (checks if a file exists within working_directory (workdir/work) and then returns true if it does, also the global path to the file.)
		ensemblefiles(models: list) -> None (packages all IRIDL maproom-relevant output files into a .tgz file in the NextGen folder so users can send to their contacts at IRI)
		NGensembles(models: list, obs_args: ArgSet, MOS: str, file: str) -> None (computes NextGen Multi-model Ensemble mean and writes input X file for CPT )
		write_cpt_file(path: Path, var: Array[T,X,Y], obs_args: ArgSet, meta: MetaTensor) -> None (does the file writing part of NGensmeble )
		read_xvPr_dat(path: Path, meta: MetaTensor) -> Array (Reads CPT output FCST_xvPr for a model and return data to NGensemble for averaging)
		read_eof_dat(eofmodes: int, model:str, args: ArgSet, eof:int, MOS:str, metadata: MetaTensor) -> Array (reads and returns data from EOF output files from CPT to plteofs function for plotting )
		read_met_dat(model:str, args: ArgSet, met: Str, MOS: str, metadata: MetaTensor) -> Array (reads and returns skill score output from CPT for a model to pltmap for plotting)
		read_ctl(path:Path) -> MetaTensor (Reads a CTL file and returns a MetaTensor object)
		read_forecast(path: Path, MOS: str, fcst_type: str, ctlfname:Path) -> array (reads and returns a model's CPT FCST_mu or FCST_P .txt file data for plt_deterministic and plt_probabilistic respectively  )
		read_forecast_bin(path: Path, MOS: str, fcst_type: str) -> array (reads and returns a model's CPT FCST_mu or FCST_P .dat file data for plt_deterministic and plt_probabilistic respectively - only for Windows  )
	---------------------------------------------------------------------------"""

	def __init__(self, workdir, work, force_download, verbose=True):
		"""creates a FileManager Object """
		if not self.validate_args(workdir, work, force_download):
			if self.verbose:
				print('Enter valid directories please!')
			return -999
		else:
			self.work = work
			self.workdir = workdir
		self.force_download = force_download #whether to force download or not
		self.working_directory = Path(copy.deepcopy(self.workdir), copy.deepcopy(self.work)) #use copy to make sure changing workdir and work dont change working_directory, python is funky
		self.verbose = verbose #whether or not to print output
		self.MOSs = {"None": "noMOS", "CCA":"CCA", "PCR":"PCR", "ELR":"ELRho"} #just so we can set mpref, though its only used in filenames now
		self.workdir = str(self.workdir) #stringing it because we just Path'd it in validate_args if its not valid iniitialy.
		self.work = str(self.work) #same for this
		os.chdir(self.workdir) #should work with or without a trailing /

		if self.force_download and os.path.isdir(str(self.work)): #we only delete folders if were forcing download AND the folders exist
			if platform.system() == 'Windows':
				if self.verbose:
					print('Windows deleting folders')
				self.callSys('del /S /Q {}/{}'.format(self.work)) #these all just delete  folders
				self.callSys('rmdir /S /Q {}/{}'.format(self.work + '/scripts'))
				self.callSys('rmdir /S /Q {}/{}'.format(self.work + '/input'))
				self.callSys('rmdir /S /Q {}/{}'.format(self.work + '/output'))
				self.callSys('rmdir /S /Q {}/{}'.format(self.work + '/images'))
				self.callSys('rmdir /S /Q {}/{}'.format(self.work))
			else:
				if self.verbose:
					print('Mac deleting folders')
				self.callSys('rm -rf {}'.format(self.work)) #these delete folders on mac / unix

		if not os.path.isdir(self.work):
			self.callSys('mkdir {}'.format(self.work)) #makes the 'work' directory (JJAS_SEASONAL_ETC_EX) inside the working directory (/Users/KJ/Example/), these names are bad

		if not os.path.isdir(self.work + '/scripts'): #the following all just remake folders
			if platform.system() == 'Windows':
				self.callSys('cd {} && mkdir scripts'.format(self.work))
			else:
				self.callSys('mkdir {}/scripts'.format(self.work))

		if not os.path.isdir(self.work + '/images'):
			if platform.system() == "Windows":
				self.callSys('cd {} && mkdir images'.format(self.work))
			else:
				self.callSys('mkdir {}/images'.format(self.work))

		if not os.path.isdir(self.work + '/input'):
			if platform.system() == "Windows":
				self.callSys('cd {} && mkdir input'.format(self.work))
			else:
				self.callSys('mkdir {}/input'.format(self.work))

		if not os.path.isdir(self.work + '/output'):
			if platform.system() == "Windows":
				self.callSys('cd {} && mkdir output'.format(self.work))
			else:
				self.callSys('mkdir {}/output'.format(self.work))

		os.chdir(self.work) #we are now in working_directory/work for the rest of the scripts

	def callSys(self, arg):
		"""Calling a system command, but get_ipython().system breaks too easily when youre not in a jupyter notebook"""
		try:
			get_ipython().system(arg) #used in jupyter notebook
		except:
			subprocess.check_output(arg, shell=True) #used outside of jupyter notebook bc get_ipython acts weird when youre not in it

	def ensemblefiles(self, models):
		"""saves all files relevant to maproom to a .tgz file in the NextGen folder for easy sending """
		if platform.system() == 'Windows': #check if windows
			self.callSys("cd output && mkdir NextGen") #windows command for making NextGen folder
			self.callSys("cd output\\NextGen &&  del /s /q *_NextGen.tgz") #windows command for deleting previous tar.gz files
			self.callSys("cd output\\NextGen && del /s /q *.txt") #windows command for deleting previous text files
			for i in range(len(models)):
				self.callSys("cd " + os.path.normpath("output/") + " && copy "+ os.path.normpath("*"+models[i]+"*.ctl") + " NextGen") #windows command for copying model ctl files to NextGen Folder
				self.callSys("cd " + os.path.normpath("output/") + " && copy "+ os.path.normpath("*"+models[i]+"*.dat") + " NextGen") #windows command for copying model dat files to nextgenfolder - should be .txt , but CPT breaks on windows

			self.callSys("cd " + os.path.normpath("output/") + " && copy "+ os.path.normpath("*NextGen*.ctl") + " NextGen") #windows command for copyitng nextgen ctl files
			self.callSys("cd " + os.path.normpath("output/") + " && copy "+ os.path.normpath("*NextGen*.dat") + " NextGen") #windows command for copyting nextgen dat files
			if self.verbose:
				self.callSys("cd " + os.path.normpath("output/NextGen/") + " && tar cvzf " + self.work + "_NextGen.tgz *") #this ~should~ be fine ? unless they have a computer older than last march 2019  - windows command for compressing all Nextgen files
			else:
				self.callSys("cd " + os.path.normpath("output/NextGen/") + " && tar czf " + self.work + "_NextGen.tgz *") #this ~should~ be fine ? unless they have a computer older than last march 2019  - windows command for compressing all Nextgen files

			self.callSys("cd " + os.path.normpath("output/NextGen/") + " && del /s /q *.ctl") #windows delete files outside of .tgz file
			self.callSys("cd " + os.path.normpath("output/NextGen/") + " && del /s /q *.dat") #windows dlete files outside of .tgz file
			self.callSys("echo %cd%") #print current workign directory for some reason

		else:
			try:
				self.callSys("cd ./output/; rm -rf NextGen")
			except:
				pass
			try:
				self.callSys("mkdir ./output/NextGen/") # unix makes NextGen folder
			except:
				pass
			self.callSys("cd ./output/NextGen/; rm -Rf *_NextGen.tgz *.txt") #delets everything in nextgen folder
			for i in range(len(models)):
				self.callSys("cd ./output/NextGen; cp ../*"+models[i]+"*.txt .") #copys all model outputs to nextgen folder - but we call with models = "nextgen" so only nextgen
			self.callSys("cd ./output/NextGen; cp ../*NextGen*.txt .") #copys all nextgen files to nextgen folder
			if self.verbose:
				self.callSys("cd ./output/NextGen; tar cvzf " + self.work+"_NextGen.tgz *.txt") #this ~should~ be fine ? unless they have a computer older than last march 2019 - unix compress all nextgen fiels
			else:
				self.callSys("cd ./output/NextGen; tar czf " + self.work+"_NextGen.tgz *.txt") #this ~should~ be fine ? unless they have a computer older than last march 2019 - unix compress all nextgen fiels
			self.callSys("cd ./output/NextGen/; rm -Rf *.txt") #unix delete all files outside of .tgz file .
			self.callSys('pwd') #unix print current directory for some reason
		if self.verbose:
			print("Compressed file "+self.work+"_NextGen.tgz created in output/NextGen/") #success message .
			print("Now send that file to your contact at the IRI")

	def validate_args(self, workdir, work, force_download):
		"""makes sure all of the variables are valid"""
		retval = True
		flag, unallowed = False, "/<>:\"\\|?* \t\n\r" # we are removing any explicitly disallowed characters from work
		for ch in unallowed:
			if ch in work:
				flag = True
			work = work.replace(ch, '')
		if flag: #if there were any banned characters, remove  and warn by printing out the new value
			if self.verbose:
				print('New "Work" Directory: {}'.format(work))


		if not os.path.isdir(workdir): #if workdir is not a pre-existing directory, use current directory and warn
			if self.verbose:
				print('Workdir does not exist! Go make it- copy output of "pwd" on Mac/Unix, or "cd" on Windows')
				print('For now, using Current Directory as Workdir - {}'.format(Path.cwd()))
			self.workdir = Path.cwd()

		if force_download not in [True, False]:
			if self.verbose:
				print('force_download must be boolean - True, or False')
			retval = retval and False
		return retval

	def check(self, path):
		"""determine whether a given filepath exists or not"""
		outpath = self.working_directory / path #these are pathlib.Path objects - the / appends the path to the current working_directory path platform-independently
		if outpath.is_file(): #checks if this resulting file exists or not
			return True, outpath #if it does, return true + the path
		else:
			return False, outpath #else return false + the path

	def NGensemble(self, models, obs_args, MOS, file='FCST_xvPr'):
		"""reads output/model _ xvPr files and calculates the NextGen ensemble mean-- plot twist its the mean of all the models """
		filename = 'output/{}_{}{}_{}{}_{}_{}{}'.format(models[0], obs_args.predictand, obs_args.predictand, self.MOSs[MOS], file, obs_args.target_season.tgt, obs_args.target_season.init, obs_args.domain.fyr ) #this is the name of a FCST_xvPr GrADS CTL file generated for a model by CPT.
		ndx, meta = 0, self.read_ctl('{}.ctl'.format(filename)) #sets an index variable = 0  and creates a MetaData object to hold X,Y,Z, Xi, Yi,Zi, dx,dy,and dz  for describing
		ensemble_data = np.empty([len(models), meta.T, meta.Y, meta.X]) #assume that all models have same data size / shape /lats/longs

		for model in models:
			if  model not in ['NextGen', 'CMC1-CanCM3', 'CMC2-CanCM4', 'CanSIPSv2', 'COLA-RSMAS-CCSM4', 'GFDL-CM2p5-FLOR-A06', 'GFDL-CM2p5-FLOR-B01','GFDL-CM2p1-aer04', 'NASA-GEOSS2S', 'NCEP-CFSv2']:
				if self.verbose: #double checking that its a valid model
					print('{} Not a valid model'.format(model))
				return -999
			filename = 'output/{}_{}{}_{}{}_{}_{}{}'.format(model, obs_args.predictor, obs_args.predictand, self.MOSs[MOS], file, obs_args.target_season.tgt, obs_args.target_season.init, obs_args.domain.fyr ) #name of a FCST_xvPr GrADS CTL file
			meta = self.read_ctl('{}.ctl'.format(filename)) #creates a MetaData object to hold X,Y,Z, Xi, Yi,Zi, dx,dy,and dz
			ensemble_data[ndx] = copy.deepcopy(self.read_xvPr_dat('{}.dat'.format(filename), meta)) #stores result of reading the binary file for that model xvPr.dat file in the ensemble_data array[ndx]
			ndx += 1
		nextgen = np.nanmean(ensemble_data, axis=0) #this takes the average over each model - nextgen  is shape [T, Y, X] where ensemble_data was [nmodels, T, Y,X]


		if file=='FCST_xvPr': # this is pretty much the only one we use, but keepting the other just in case
			filename = 'input/NextGen_{}_{}_ini{}.tsv'.format(obs_args.predictand, obs_args.target_season.tgt, obs_args.target_season.init)
			self.write_cpt_file(filename, nextgen, obs_args, meta) #calles write CPT to write a .tsv input file for NextGen
			if self.verbose:
				print('Cross-validated prediction files successfully produced')
		if file=='FCST_mu' or file == 'FCST_var':
			filename = 'output/NextGen_{}{}_{}_{}{}_{}_{}{}.tsv'.format(obs_args.predictand, obs_args.predictand, MOS, file, obs_args.target_season.tgt, obs_args.target_season.monf, obs_args.domain.fyr)
			self.write_cpt_file(filename, nextgen, obs_args, meta)
			if self.verbose:
				print('Forecast {} files successfully produced'.format('' if file=='FCTS_mu' else 'error'))

	def write_cpt_file(self,  path, var, obs_args, meta):
		"""function for writing a .tsv cpt input file by hand """
		varname, units = 'prec', 'mm' #variables for CPT data format
		var[np.isnan(var)]=-999. #use CPT missing value
		L=0.5*(float(obs_args.target_season.tgtf)+float(obs_args.target_season.tgti)) #also for CPT data format, time from init month to middle of forecast period
		months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'} #helpful for writing Cpt
		S=months[obs_args.target_season.init]
		if '-' in obs_args.target_season.tgt:
			mi, mf = obs_args.target_season.tgt.split('-')
			mi, mf = months[mi], months[mf]
		else:
			mi, mf = months[obs_args.target_season.tgt] #just making more CPT variables for mon_ini and mon_final

		xyear = True if obs_args.target_season.tgt=='Dec-Feb' or obs_args.target_season.tgt=='Nov-Jan' else False #set cross-year to true if target is cross-year
		Xarr, Yarr, Tarr = meta.x_coords, meta.y_coords, meta.years #can just use x_coord, y coordinates, and years list from meta data class
		#Now write the CPT file
		f = open(path, 'w') #opens file to be written
		f.write("xmlns:cpt=http://iri.columbia.edu/CPT/v10/\n") #CPT header
		f.write("cpt:nfields=1\n") #CPT Header
		for it in range(meta.T): #for each year
			if xyear: 	#if cross-year target
				f.write("cpt:field="+varname+", cpt:L="+str(L)+" months, cpt:S="+str(int(meta.tini))+"-"+S+"-01T00:00, cpt:T="+str(int(Tarr[it]))+"-"+mi+"/"+str(Tarr[it]+1)+"-"+mf+", cpt:nrow="+str(meta.Y)+", cpt:ncol="+str(meta.X)+", cpt:row=Y, cpt:col=X, cpt:units="+units+", cpt:missing=-999.\n") #write CPT params
			else:
				f.write("cpt:field="+varname+", cpt:L="+str(L)+" months, cpt:S="+str(int(meta.tini))+"-"+S+"-01T00:00, cpt:T="+str(int(Tarr[it]))+"-"+mi+"/"+mf+", cpt:nrow="+str(meta.Y)+", cpt:ncol="+str(meta.X)+", cpt:row=Y, cpt:col=X, cpt:units="+units+", cpt:missing=-999.\n") #write CPT params
			np.savetxt(f, Xarr[0:-1], fmt="%.6f",newline='\t')  #writes longitudes values
			f.write("\n") #next line , for some reason separate from last line , but ill keep it
			for iy in range(meta.Y): #for each latitude
				np.savetxt(f,np.r_[Yarr[iy],var[it,iy,0:]],fmt="%.6f", newline='\t')  #write [latitude, meta.X * longitude values ]
				f.write("\n") #next line
		f.close() #closes the file

	def read_xvPr_dat(self, path, meta):
		"""reads cross-validate prediction file for making NextGen ensemble mean"""
		f = open(str(Path(self.working_directory, path)), 'rb') # opens the path for reading
		#cycle for all time steps  (same approach to read GrADS files as before, but now read T times)
		memb0=np.empty([meta.T,meta.Y,meta.X]) #creates empty array so we can fill it - shaped [nyears, latitudes, longitudes ]
		for it in range(meta.T): #for each year
			#Now we read the field
			if platform.system() == "Windows": #on windows, for some reason CPT writes an extra bite at the beginning and end of each record, so excise it
				garb = struct.unpack('s', f.read(1))[0] #reads 1 byte- it is 0b11111111
			recl=struct.unpack('i',f.read(4))[0] #reads 4 bytes into an int - this is the number of bytes stored in the record
			numval=int(recl/np.dtype('float32').itemsize) # divide recl by the size of a float32 to get number of floats in the record
			A0=np.fromfile(f,dtype='float32',count=numval) #np.fromfile reads that many floats into an array for you
			endrec=struct.unpack('i',f.read(4))[0]  #needed as Fortran sequential repeats the header at the end of the record!!!
			if platform.system() == "Windows":# same deal for the windows random byte garbage thing so excise it again
				garb = struct.unpack('s', f.read(1))[0]
			memb0[it,:,:]= np.transpose(A0.reshape((meta.X, meta.Y), order='F')) #reshape recently read float array into [longs, lats ] and store it in the array at the ndx of the correct year
		memb0[memb0==-999.]=np.nan #identify NaNs
		f.close()
		return copy.deepcopy(memb0) #copying because python sometimes does funky stuff with pointers and references and I dont want to debug that - could get rid of it to improve performance but our data isnt very big

	def read_eof_dat(self, eofmodes, model, args, eof, MOS, metadata):
		"""function for reading binary EOF output files """
		f = open(str(Path(self.working_directory, 'output/{}_{}{}_{}_{}_{}_{}.dat'.format(model, args.predictor, args.predictand, MOS, eof, args.target_season.tgt, args.target_season.init))), 'rb') #Opens the output / EOF.dat file
		eof = np.empty([eofmodes, metadata.Y, metadata.X]) #empty array of shape [#eof modes, latitudes, longitudes]
		for mo in range(eofmodes): #for each eof mode calculated
			if platform.system() == "Windows": #excise extra windows byte if on windows  - note if on windows you wont be able to read CPT files written on mac and vice versa.
				garb = struct.unpack('s', f.read(1))[0] #read the byte
			recl=struct.unpack('i',f.read(4))[0] #read an int - 4 bytes  indicates number of bytes in the record bounded by the int and a matching one on the other side
			numval=int(recl/np.dtype('float32').itemsize) #this if for each time/EOF stamp - this is the number of bytes / size of a float - the number of floats in the record
			A0=np.fromfile(f,dtype='float32',count=numval) #np.fromfile reads in numval number of floats
			endrec=struct.unpack('i',f.read(4))[0]  #needed as Fortran sequential repeats the header at the end of the record!!!
			if platform.system() == "Windows": #excise lame windows byte if needed
				garb = struct.unpack('s', f.read(1))[0]
			A0[A0==-999.] = np.nan #set missing values = nan
			eof[mo,:,:]= copy.deepcopy(np.transpose(A0.reshape((metadata.X, metadata.Y), order='F'))) #store it in pre-defined array at index of correct EOF Mode - copy is to save us from accidentally changing data with weird references
		eof[eof==-999.]=np.nan #nan #unnecessary but okay
		f.close
		return eof

	def read_met_dat(self, model, args, met, MOS, metadata):
		"""function for reading binary """
		f = open(str(Path(self.working_directory, 'output/{}_{}{}_{}_{}_{}_{}.dat'.format(model, args.predictor, args.predictand, MOS, met, args.target_season.tgt, args.target_season.init))), 'rb') #opens file
		if platform.system() == "Windows": #excise extra byte written by WIndows CPT_Batch.exe  if on windows
			garb = struct.unpack('s', f.read(1))[0]
		recl=struct.unpack('i',f.read(4))[0] # read number of bytes in the record
		numval=int(recl/np.dtype('float32').itemsize) #calculate number of floats by dividing by # of bytes in a float
		#Now we read the field
		A=np.fromfile(f,dtype='float32',count=numval) #read that many floats
		var = np.transpose(A.reshape((metadata.X, metadata.Y), order='F')) #reshape to longitudes, latitudes
		f.close()
		return var

	def read_ctl(self, path):
		"""reads a CTL file """
		f = open(str(Path(self.working_directory, path)), 'r') #opens the file
		for line in f: #loops over every line in the file
			line = line.split() #split line string on whitespace
			if "XDEF" in line: #if the line has "XDEF" in it
				X, Xi, dx  = int(line[1]), float(line[3]), float(line[4]) #read x dimension size, lowest X value, and distance between each X value  (longitudes)
			if "YDEF" in line: #if line has "YDEF" in it
				Y, Yi, dy = int(line[1]), float(line[3]), float(line[4]) # read y dimension size, lowest y value, and distance between each Y value ( latitudes)
			if "TDEF" in line: #if "TDEF in line lol"
				T, Ti, dt = int(line[1]), int(line[3][-4:len(line[3])]), int(line[4][:-2]) #read number of years of data , first year, and distance between each year (its one year, plot twist ) - usuallly not used unless it IS
		f.close()
		return MetaTensor(X,Y,T,Xi,Yi,Ti,dx,dy,dt) #store this data in a metatensor object

	def read_forecast(self, path, MOS, fcst_type='type', ctlfname='None'):
		"""reads a FCST_P .txt or a FCST_mu .txt file"""
		path = path.format(self.MOSs[MOS]) #the path to the .txt
		ctlfname = ctlfname.format(self.MOSs[MOS]) #the path to a matchin .ctl file so we can get metadata to return - dont need for data reading, jsut for returning
		f = open(str(Path(self.working_directory, path)), 'r') #opens .txt file for reading
		meta = self.read_ctl(ctlfname[:-4]+'.ctl') #gets metadata from ctl file
		lats, all_vals, vals = [], [], [] #places to store lats, data, and data for each time step
		flag = 0
		for line in f: #loop over lines in file
			if line[0:4] == 'cpt:': #if the line starts with cpt:, then
				if flag == 2: #if we've already seen some data (initially, we wont have because it'll start with a cpt: line)
					vals = np.asarray(vals, dtype=float) #cast vals as an array
					if fcst_type == 'deterministic':
						vals[vals == -999.0] = np.nan #set missing vals to nan
					if fcst_type == 'probabilistic':
						vals[vals == -1.0] = np.nan #missing val value is different for probabilistic fcst files
					all_vals.append(vals) #put data for this time step onto the end of the main data
					lats = [] #reset lats
					vals = [] # reset data for a new time step
				flag = 1 #mark that a timestep has just started
			elif flag == 1 and line[0:4] != 'cpt:': # if new time step has jsut started (this will execute if flag was JUST set to 1 on this line , so add for the first few lines of the file since theres more than one header in a row we need this it works i promise  the line[0:4]!= cpt: to keep it from loading the header as data )
				longs = line.strip().split('\t') #if we're in the first line of a timestep, it will be longitude values for each longitude (column) in the data  - and its tab separated
				longs = [float(i) for i in longs] #convert to floats
				flag = 2 #mark that we've read the longitude values and move on to the [lat, data * num_longs]  lines
			elif flag == 2: #were on the data lines
				latvals = line.strip().split('\t') #split on tabs because .tsv
				lats.append(float(latvals.pop(0))) #the first in the line is a latitude , append it to latitudes list
				vals.append(latvals) #stack the rest of the line (the data ) on the end of teh data array
		vals = np.asarray(vals, dtype=float) #at the end of the file, we add the last timestep of data we read to the data array
		if fcst_type == 'deterministic':
			vals[vals == -999.0] = np.nan #different missing data values for deterministic and probabilistic files
		if fcst_type == 'probabilistic':
			vals[vals == -1.0] = np.nan
		all_vals.append(vals)
		all_vals = np.asarray(all_vals)
		return lats, longs, all_vals, meta

	def read_forecast_bin(self, path, MOS, fcst_type='type'):
		"""reads a forecast FCST_P or FCST_mu .dat file"""
		f = open(str(Path(self.working_directory, path.format(self.MOSs[MOS]))), 'rb') ## open the file

		if fcst_type == 'deterministic':  # if deterministic, only one value in the file so no need to loop
			meta = self.read_ctl(path[:-4]+'.ctl') #open and read CTL file to get  metadata
			garb = struct.unpack('s', f.read(1))[0] #if were not on windows, we'll be using read_forecast not read_forecast_bin so no need to check if platform.system() == "Windows", just read the extra windwos byte
			recl = struct.unpack('i', f.read(4))[0] #unpack number of bytes in teh record
			numval=int(recl/np.dtype('float32').itemsize) #get number of floats by dividing by size of lfoat
			A0 = np.fromfile(f, dtype='float32', count=numval) # read in that many floats with np.fromfile
			var = np.transpose(A0.reshape((meta.X, meta.Y), order='F')) #transpose because thats the file format for ya
			var[var==-999.]=np.nan #only sensible values #set  nans
			recl = struct.unpack('i', f.read(4))[0]  #baca nomor bytes dalam rekaman ini lagi
			garb = struct.unpack('s', f.read(1))[0]#baca data tambahan lagi
			lats, lons = np.linspace(meta.Yi+meta.Y*meta.dy, meta.Yi, num=+1), np.linspace(meta.Xi, meta.Xi+meta.X*meta.dx, num=meta.X+1) # construct consistent lats / longs from metadata becasue they arent in the binary data
			return lats, lons, np.asarray([var]), meta

		if fcst_type == 'probabilistic':
			meta = self.read_ctl(path[:-4]+'.ctl') #ge tmetadata

			vars = [] #list for storing values for belownormal, noramla and above normal
			for ii in range(3): #for each of the three values
				garb = struct.unpack('s', f.read(1))[0] #read garbage byte from windows cpt
				recl = struct.unpack('i', f.read(4))[0] #read # bytes in record as int
				numval=int(recl/np.dtype('float32').itemsize) #calculate number of floats in record by dividing by size of float
				A0 = np.fromfile(f, dtype='float32', count=numval) #read in that many flaots with np.fromfile
				var = np.transpose(A0.reshape((meta.X, meta.Y), order='F')) #transpose because thats the file layout
				var[var==-1.]=np.nan #only sensible values #since probabilistic, missing data value = -1
				recl = struct.unpack('i', f.read(4))[0] #must read int again,
				garb = struct.unpack('s', f.read(1))[0] #and read garbage byte again  so the next record isnt messed up
				vars.append(var) #add data we read to the vars list
			lats, lons = np.linspace(meta.Yi+meta.Y*meta.dy, meta.Yi, num=+1), np.linspace(meta.Xi, meta.Xi+meta.X*meta.dx, num=meta.X+1) #generate consistent lats / longs from metadata
			return lats, lons, np.asarray(vars), meta

	def __eq__(self, other):
		ret = True
		for key in vars(self).keys():
			if vars(self)[key] != vars(other)[key]:
				ret = False
		return ret
