from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from scipy.optimize import curve_fit
from scipy.special import erfc
from scipy.special import erf
from scipy.interpolate import spline
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import sys
import inspect
import random
import numpy as np

class SSA_cal_utility():

	def __init__(self, ssa, I2C, fc7):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.scurve_data = False
		self.scurve_nevents  = 0
		self.scurve_calpulse = 0
		self.default_dac_ratio = 4.9 / 2
		self.fe_ofs = 0.3708
		self.fe_gain = 1.1165

	def scurves(self, cal_ampl = 'baseline', mode = 'all', nevents = 1000, rdmode = 'fast', display = False, plot = True, filename = False, filename2 = "trim0", msg = "", striplist = range(1,121)):
		'''	cal_ampl  -> int number      -> Calibration pulse charge (in CALDAC LSBs)         
			mode      -> 'all' | 'sbs'   -> All strips together or one by one     
			nevents   -> int number      -> Number of calibration pulses (default 1000)  
			striplist -> [list 1:120]    -> Select specific strip (default all) 
			rdmode    -> 'fast' | 'i2c'  -> Select if use fast readout or I2C readout  
			display   -> True | False    -> Display additional informations     
			plot      -> True | False    -> Plot S-Curve      
			filename  -> False | string  -> If not False the data is vritten in the file named by 'string'     
			filename2 -> 'string'        -> Additional string to complete the filename    
			msg       -> internal use         
		'''
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		# first go to the async mode
		self.ssa.ctrl.activate_readout_async()
		plt.clf()
		baseline = False

		if isinstance(cal_ampl, int):
			cal_ampl = [cal_ampl]
		elif cal_ampl == 'baseline':
			baseline = True
			cal_ampl = [0]
		elif not isinstance(cal_ampl, list): 
			return False
		
		for cal_val in  cal_ampl:
			# close shutter and clear counters
			close_shutter(1)
			clear_counters(1)
			# init chip cal pulse
			self.ssa.ctrl.set_cal_strips(mode = 'counter', strip = 'all')
			self.ssa.ctrl.set_cal_pulse(amplitude = cal_val, duration = 15, delay = 'keep')
			# init firmware cal pulse
			Configure_TestPulse_MPA_SSA(200, nevents)
			# then let's try to measure the scurves
			scurves = np.zeros((256,120), dtype=np.int)
			threshold = 0
			utils.ShowPercent(0, 256, "Calculating S-Curves "+msg+" ")

			while (threshold < 256):
				strout = ""
				error = False
				#print "Setting the threshold to ", threshold, ", sending the test pulse and reading the counters"
				strout += "threshold = " + str(threshold) + ".   " 
				self.ssa.ctrl.set_threshold(threshold)# set the threshold
				sleep(0.05)

				if (not baseline and (mode == 'all')):	# provide cal pulse to all strips together
					clear_counters(2)
					open_shutter(2) 
					SendCommand_CTRL("start_trigger") # send sequence of NEVENTS pulses
					sleep(0.02)   
					while(self.fc7.read("stat_fast_fsm_state") != 0): sleep(0.01)
					close_shutter(2) 

				elif(not baseline and (mode == 'sbs')): # provide cal pulse strip by strip
					clear_counters(1)
					for s in striplist:
						self.ssa.ctrl.set_cal_strips(mode = 'counter', strip = s )
						sleep(0.01)
						open_shutter(2) 
						sleep(0.01)
						SendCommand_CTRL("start_trigger") # send sequence of NEVENTS pulses
						sleep(0.01)   
						while(self.fc7.read("stat_fast_fsm_state") != 0): sleep(0.01)
						close_shutter(2) 
						sleep(0.01)

				elif(baseline and (mode == 'all')):
					clear_counters(1)
					sleep(0.01)
					open_shutter(2) 
					sleep(0.01)
					close_shutter(2)
					sleep(0.01)

				elif(baseline and (mode == 'sbs')):
					# with this method, the time between open and close shutter
					# change from strip to strip due to the communication time
					# so do not use to compare the counters value, 
					# from the point of view of the atandard deviation is not influent
					clear_counters(2)# clear counters
					sleep(0.01)
					for s in striplist:
						# all trims at 0 and one at 31 to remove the crosstalks effect
						self.I2C.strip_write("THTRIMMING", 0, 0)
						self.I2C.strip_write("THTRIMMING", s, 31)
						sleep(0.01)
						open_shutter(2) 
						sleep(0.01)
						close_shutter(2)
						sleep(0.01)

				if(rdmode == 'fast'):
					failed, scurves[threshold] = self.ssa.readout.read_counters_fast(striplist)
				elif(rdmode == 'i2c'):
					failed, scurves[threshold] = self.ssa.readout.read_counters_i2c(striplist)
				else:
					failed = True
					
				if (failed): 
					error = True
				else:
					for s in range(0,120):
						if ((threshold > 0) and (scurves[threshold,s])==0 and (scurves[threshold-1,s]>(nevents*0.8)) ) : 
							error = True
						elif ((not baseline) and (threshold > 0) and (scurves[threshold,s])== 2*scurves[threshold-1,s] and (scurves[threshold,s] != 0)): 
							error = True
				if (error == True): 	
					threshold = threshold - 1
					utils.ShowPercent(threshold, 256, "Failed to read counters for threshold " + str(threshold) + ". Redoing")
					sleep(0.5)
					continue
				else: 
					strout += "Counters samples = 1->[" + str(scurves[threshold][0]) + "]  30->[" + str(scurves[threshold][29]) + "]  60->[" + str(scurves[threshold][59]) + "]  90->[" + str(scurves[threshold][89]) + "]  120->[" + str(scurves[threshold][119]) + "]"    
				
				# threshold increment
				threshold = threshold + 1
				
				if (display == True): 
					utils.ShowPercent(threshold, 256, strout)
				else: 
					utils.ShowPercent(threshold, 256, "Calculating S-Curves "+msg+"                                      ")
			
			utils.ShowPercent(256, 256, "Done calculating S-Curves "+msg+"                                            ")

			if( isinstance(filename, str) ):
				fo = "../SSA_Results/" + filename + "_scurve_" + filename2 + "__cal_" + str(cal_val) + ".csv"
				CSV.ArrayToCSV (array = scurves, filename = fo, transpose = True)
				print "->  \tData saved in" + fo

		if(plot == True): 
			plt.plot(scurves)
			plt.show(block=False)

		self.scurve_data     = scurves
		self.scurve_nevents  = nevents
		self.scurve_calpulse = cal_ampl

		return scurves


	def trimming_scurves(self, method = 'expected', cal_ampl = 100, th_nominal = 'default', default_trimming = 'keep', striprange = range(1,121), ratio = 'default', iterations = 3, nevents = 1000, plot = True, display = False, reevaluate = True):

		# trimdac/thdac ratio
		if(ratio == 'evaluate'):
			dacratiolist = np.array(self.evaluate_thdac_trimdac_ratio(trimdac_pvt_calib = False, cal_ampl = cal_ampl, th_nominal = th_nominal,  nevents = nevents, plot = False))
		elif(ratio == 'default'):
			dacratiolist = np.array([self.default_dac_ratio]*120)
		elif isinstance(ratio, float) or isinstance(ratio, int):
			dacratiolist = np.array([ratio]*120)
		else: exit(1)

		# apply starting trimming
		if(method == 'expected'):
			if( isinstance(default_trimming, np.ndarray) or isinstance(default_trimming, list) or isinstance(default_trimming, int)):
				trimdac_value = self.trimming_apply(default_trimming, striprange)
			elif(default_trimming == 'keep'): 
				trimdac_value = self.trimming_apply('keep')
			else: return False
		elif(method == 'center'):
			if(default_trimming == 'keep'): 
				trimdac_value = self.trimming_apply('keep')
			else:
				trimdac_value = self.trimming_apply(15, striprange)
		elif (method == 'highest'):
			trimdac_value = self.trimming_apply(0, striprange)
		else: return False

		# evaluate initial S-Curves
		scurve_init = self.scurves(
			cal_ampl = cal_ampl, 
			nevents = nevents, 
			display = False, 
			plot = False, 
			filename = False,
			msg = "for iteration 0")

		thlist_init, par_init = self.evaluate_scurve_thresholds(
			scurve = scurve_init, 
			nevents = nevents)

		# Define the target threshold
		if(method == 'expected'):
			if(th_nominal == 'evaluate'):
				fe_gain , fe_ofs = self.evaluate_fe_gain(nevents = nevents, plot = False)
				th_expected = fe_ofs + fe_gain * cal_ampl
			elif(th_nominal == 'default'):
				th_expected = self.fe_ofs + self.fe_gain * cal_ampl
			elif isinstance(ratio, float) or isinstance(ratio, int):
				th_expected = th_nominal
			else: exit(1)
		elif(method == 'center'):
			th_expected = np.mean(thlist_init)
		elif (method == 'highest'):
			th_expected = np.max(thlist_init)		

		thlist = thlist_init
		scurve = scurve_init
		par = par_init

		print "Difference = " +  str(np.max(thlist)-np.min(thlist))

		# start trimming on the S-Curves
		for i in range(0, iterations):
			trimdac_correction = np.zeros(120)

			for strip in striprange:
				
				th_initial                  = thlist[strip-1]
				trimdac_correction[strip-1] = int(round((th_expected - th_initial) * dacratiolist[strip-1] ))
				trimdac_current_value       = self.I2C.strip_read("THTRIMMING", strip)
				trimdac_value[strip-1]      = trimdac_current_value + trimdac_correction[strip-1]

				if(trimdac_value[strip-1] > 31):
					print "->  \tReached high trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 31
				elif(trimdac_value[strip-1] < 0):
					print "->  \tReached low trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 0

				# Apply correction to the trimming DAC				
				self.I2C.strip_write("THTRIMMING", strip, int(trimdac_value[strip-1]))

			if(display):
				print "->  \tInitial threshold    " + str(thlist[0:10])
				print "->  \tTarget threshold     " + str([th_expected]*10)
				print "->  \tTrim-DAC Correction  " + str(trimdac_correction[0:10])
				print "->  \tTrimming DAC values: " + str(trimdac_value[0:10])

			# evaluate new S-Curves
			scurve = self.scurves(
				cal_ampl = cal_ampl, 
				nevents = nevents, 
				display = False, 
				plot = False, 
				filename = False,
				msg = "for iteration " + str(i+1))

			thlist, par = self.evaluate_scurve_thresholds(
				scurve = scurve, 
				nevents = nevents)

			dacratiolist = dacratiolist/2.0

			print "Difference = " +  str(np.max(thlist)-np.min(thlist))
			if ((np.max(thlist)-np.min(thlist)) < 1):
				break   
			if (i == iterations-1):
				print "->  \tReached the maximum number of iterations (d = " + str(np.max(thlist)-np.min(thlist)) + ")"

		#plot initial and final S-Curves
		if(plot):
			xplt = np.linspace(int(th_expected-30), int(th_expected+31), 601)
			plt.clf()
			for i in par_init:
				plt.plot( xplt, f_errorfc(xplt, i[0], i[1], i[2]) , 'b')
			for i in par:
				plt.plot( xplt, f_errorfc(xplt, i[0], i[1], i[2]) , 'r')
			#utils.smuth_plot(scurve_init[xplt], xplt, 'b')
			#utils.smuth_plot(scurve[xplt], xplt, 'r')
			plt.show()

		return scurve_init , scurve


	def evaluate_fe_gain(self, callist = [30, 60, 90], nevents=1000, plot = True):
		thmean = []
		cnt = 0
		for cal in callist:
			s = self.scurves(
				cal_ampl = cal, 
				nevents = nevents, 
				display = False, 
				plot = False, 
				filename = False,
				msg = "")
			thlist, p = self.evaluate_scurve_thresholds(scurve = s, nevents = nevents)
			thmean.append( np.mean(thmean) )

		par, cov = curve_fit(f= f_line,  xdata = callist, ydata = thmean, p0 = [0, 0])
		gain = par[0]
		offset = par[1]

		if(plot):
			plt.clf()
			plt.plot(callist, offset+gain*np.array(callist))
			plt.plot(callist, thmean, 'o')
			plt.show()

		return gain, offset


	def trimming_apply(self, default_trimming = 'keep', striprange = range(1,121), display = True):
		r = True
		if(isinstance(default_trimming, int)):
			trimdac_value = np.array([default_trimming]*120)
			self.I2C.strip_write("THTRIMMING", 0, default_trimming)
			if(display):
				print "->  \tTrimming: Applied value %d to all channels" % (default_trimming)
			if(default_trimming == 0):
				self.scurve_trimming = 'zeros'
			else:
				self.scurve_trimming = 'const'

		elif(isinstance(default_trimming, np.ndarray) or isinstance(default_trimming, list)):
			trimdac_value = np.array(default_trimming)
			for i in striprange:
				self.I2C.strip_write("THTRIMMING", i, default_trimming[i])
			if(display):
				print "->  \tTrimming: Applied trimming array" % (default_trimming)
			self.scurve_trimming = 'trimmed'			

		elif(default_trimming != False or default_trimming != 'keep'):
			self.scurve_trimming = 'none'
			exit(1)

		readback = np.zeros(120)
		for i in range(0,120):
			readback[i] = self.I2C.strip_read("THTRIMMING", i+1)
		return readback


	def evaluate_thdac_trimdac_ratio(self, trimdac_pvt_calib = False, cal_ampl = 100, th_nominal = 115,  nevents = 500, plot = False):
		# set the value of the dac that controls the trimmin dacs currents
		# to compensate for process variations
		if(isinstance(trimdac_pvt_calib, int)):
			self.I2C.peri_write('Bias_D5TDR', trimdac_pvt_calib)
		sc = []
		th = []
		cnt = 0
		for trimdac in [31, 0]:
			thtmp = np.zeros(120)
			# apply trimming dact values
			self.trimming_apply(trimdac)
			# calculate scurves
			sc.append(
				self.scurves(
					cal_ampl = cal_ampl, 
					nevents = nevents, 
					display = False, 
					plot = False, 
					filename = False
				)
			)
			for strip in range(0,120):
				sct = sc[cnt][:,strip]
				thidx , par = self.__errfitting_get_mean(sct, nevents)
				thtmp[strip] = thidx
			th.append( thtmp )
			cnt += 1 
		if(plot):
			plt.plot(th)
			plt.show()
		ratios = 32.0 / (th[0]-th[1])
		return ratios


	def evaluate_scurve_thresholds(self, scurve, nevents = 1000):
		ths = []
		pars = []

		for strip in range(1,121):
			th, par = self.__errfitting_get_mean(
				curve = scurve[: , strip-1],
				nevents = nevents,
				expected = 'autodefine',
				errmsg = "", 
				reiterate = 3)
			ths.append(th)
			pars.append(par)

		ths = np.array(ths)
		pars = np.array(pars)
		return ths, pars


	def __errfitting_get_mean(self, curve, nevents, expected = 'autodefine', errmsg="", reiterate = 3):
		sct = curve
		err = True
		itr = 0
		# get read of the noise peack 
		while ( not ((sct[0] == nevents) and (sct[1] == nevents)) ):
			sct = sct[ np.argmax(sct)+1 : ]
		
		for i in range(0, len(curve)-len(sct)):
			sct = np.insert(sct, 0, nevents)

		# find a first guess for the scurve mean value
		if(expected == 'autodefine'):
			par_guess = np.abs(np.abs(sct - (nevents/2) )).argmin()	
		elif(isinstance(expected, int) or isinstance(expected, float)):
			par_guess = expected
		else:
			err = True
			return False

		while(err == True and itr < reiterate):
			try:
				# fit the curve with 1-error_function (function defined in myScripts/Utilities.py)
				par, cov = curve_fit(
					f     = f_errorfc, 
					xdata = range(1, len(sct)), 
					ydata = sct[0 : len(sct)-1], 
					p0    = [nevents, par_guess, 2]
				)
			except RuntimeError:
				itr += 1
			else:
				err = False
		if(err):
			print "Fitting failed " + errmsg
			return False
		else:
			# readd number of th points removed by the noise cleaning
			thidx = int(round(par[1]))
			return thidx, par


	def save_multiple_scurves(self, cal_list = range(0, 160, 10), name = "Chip1", name2 = "trim0"):
		plt.clf()
		for cal in cal_list:
			print "Trimming: " + str(self.trimming_apply()[0:10])
			sleep(0.1)
			self.scurves(
				cal_ampl = cal, 
				filename = name+'/'+name, 
				filename2 = name2,
				plot = True,
				msg = "for calibration pulse = " + str(cal))
