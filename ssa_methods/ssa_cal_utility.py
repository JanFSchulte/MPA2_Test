from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from scipy.optimize import curve_fit
from scipy.special import erfc
from scipy.special import erf
from scipy.interpolate import spline
from itertools import product as itertools_product
from lmfit import Model as lmfitModel
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
		self.calpulse_dll_resolution = 1.2
		self.tempvalue = np.inf
		self.baseline = 'nondefined'
		self.storedscurve = {}

	def scurves(self, cal_ampl = [50], mode = 'all', nevents = 1000, rdmode = 'fast', display = False, plot = True, filename = 'TestLogs/Chip-0', filename2 = '', msg = "", striplist = range(1,121), speeduplevel = 2, countershift = 1):
		'''	cal_ampl  -> int |'baseline'  -> Calibration pulse charge (in CALDAC LSBs)
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
		if(speeduplevel > 0):
			utils.activate_I2C_chip()
		# first go to the async mode
		self.ssa.ctrl.activate_readout_async()
		ermsg = ''
		baseline = False

		if isinstance(cal_ampl, int):
			cal_ampl = [cal_ampl]
		elif cal_ampl == 'baseline':
			baseline = True
			cal_ampl = [0]
			self.set_trimming(0, display=False)
			self.set_trimming(31, striplist, display=False)

		elif not isinstance(cal_ampl, list):
			return False

		for cal_val in  cal_ampl:
			# close shutter and clear counters
			close_shutter(1)
			clear_counters(1)
			# init chip cal pulse
			self.ssa.strip.set_cal_strips(mode = 'counter', strip = 'all')
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
				self.ssa.ctrl.set_threshold(threshold); sleep(0.05); # set the threshold

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
						self.ssa.strip.set_cal_strips(mode = 'counter', strip = s )
						sleep(0.01);
						open_shutter(2); sleep(0.01);
						SendCommand_CTRL("start_trigger"); sleep(0.01); # send sequence of NEVENTS pulses
						while(self.fc7.read("stat_fast_fsm_state") != 0):
							sleep(0.01)
						close_shutter(2); sleep(0.01);

				elif(baseline and (mode == 'all')):
					clear_counters(2); sleep(0.01);
					open_shutter(2);   sleep(0.01);
					close_shutter(2);  sleep(0.01);

				elif(baseline and (mode == 'sbs')):
					# with this method, the time between open and close shutter
					# change from strip to strip due to the communication time
					# so do not use to compare the counters value,
					# from the point of view of the atandard deviation is not influent
					clear_counters(2); sleep(0.01);
					for s in striplist:
						# all trims at 0 and one at 31 to remove the crosstalks effect
						self.ssa.strip.set_trimming('all', 0)
						self.ssa.strip.set_trimming(s, 31)
						sleep(0.01);
						open_shutter(2);  sleep(0.01);
						close_shutter(2); sleep(0.01);
				if(rdmode == 'fast'):
					failed, scurves[threshold] = self.ssa.readout.read_counters_fast(striplist, shift = countershift)
				elif(rdmode == 'i2c'):
					failed, scurves[threshold] = self.ssa.readout.read_counters_i2c(striplist)
				else:
					failed = True

				if (failed):
					error = True; ermsg = '[Counters readout]';
				else:
					for s in range(0,120):
						if ((threshold > 0) and (scurves[threshold,s])==0 and (scurves[threshold-1,s]>(nevents*0.8)) ) :
							error = True; ermsg = '[Condition 1]' + str(scurves[threshold,s]) +'  ' + str(scurves[threshold-1,s])
						elif ((not baseline) and (threshold > 10) and (scurves[threshold,s])== 2*scurves[threshold-1,s] and (scurves[threshold,s] != 0)):
							error = True; ermsg = '[Condition 2]'

				if (error == True):
					threshold = (threshold-1) if (threshold>0) else 0
					utils.ShowPercent(threshold, 256, "Failed to read counters for threshold " + str(threshold) + ". Redoing. " +  ermsg)
					sleep(0.5)
					continue
				else:
					strout += "Counters samples = 1->[" + str(scurves[threshold][0]) + "]  30->[" + str(scurves[threshold][29]) + "]  60->[" + str(scurves[threshold][59]) + "]  90->[" + str(scurves[threshold][89]) + "]  120->[" + str(scurves[threshold][119]) + "]"

				if(speeduplevel >= 2 and threshold > 32):
					if( (scurves[threshold-8: threshold ] == np.zeros((8,120), dtype=np.int)).all() ):
						break

				if (display == True):
					utils.ShowPercent(threshold, 256, strout)
				else:
					utils.ShowPercent(threshold, 256, "Calculating S-Curves "+msg+"                                      ")
				threshold = threshold + 1

			utils.ShowPercent(256, 256, "Done calculating S-Curves "+msg+"                                            ")

			if( isinstance(filename, str) ):
				fo = "../SSA_Results/" + filename + "_scurve_" + filename2 + "__cal_" + str(cal_val) + ".csv"
				CSV.ArrayToCSV (array = scurves, filename = fo, transpose = True)
				print "->  \tData saved in" + fo

		if(plot == True): plt.clf()
		plt.plot(scurves)
		if(plot == True): plt.show()
		self.scurve_data     = scurves
		self.scurve_nevents  = nevents
		self.scurve_calpulse = cal_ampl

		return scurves


	def trimming_scurves(self, method = 'expected', cal_ampl = 100, th_nominal = 'default', default_trimming = 'keep', striprange = range(1,121), ratio = 'default', iterations = 5, nevents = 1000, plot = True, display = False, reevaluate = True):
		utils.activate_I2C_chip()
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
				trimdac_value = self.set_trimming(default_trimming, striprange, display = False)
			elif(default_trimming == 'keep'):
				trimdac_value = self.set_trimming('keep', display = False)
			else: return False
		elif(method == 'center'):
			if(default_trimming == 'keep'):
				trimdac_value = self.set_trimming('keep', display = False)
			else:
				trimdac_value = self.set_trimming(15, striprange, display = False)
		elif (method == 'highest'):
			trimdac_value = self.set_trimming(0, striprange, display = False)
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

		print "->  \tDifference = " +  str(np.max(thlist)-np.min(thlist))

		# start trimming on the S-Curves
		for i in range(0, iterations):
			trimdac_correction = np.zeros(120)

			for strip in striprange:

				th_initial                  = thlist[strip-1]
				trimdac_correction[strip-1] = int(round((th_expected - th_initial) * dacratiolist[strip-1] ))
				trimdac_current_value       = self.ssa.strip.get_trimming(strip)
				trimdac_value[strip-1]      = trimdac_current_value + trimdac_correction[strip-1]

				if(trimdac_value[strip-1] > 31):
					print "->  \tReached high trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 31
				elif(trimdac_value[strip-1] < 0):
					print "->  \tReached low trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 0

				# Apply correction to the trimming DAC
				self.ssa.strip.set_trimming(strip, int(trimdac_value[strip-1]))

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


	def set_trimming(self, default_trimming = 'keep', striprange = 'all', display = True):
		r = True
		if(isinstance(default_trimming, int)):
			if(striprange == 'all'):
				self.ssa.strip.set_trimming('all', default_trimming)
				if(display):
					print "->  \tTrimming: Applied value %d to all channels" % (default_trimming)
				if(default_trimming == 0): self.scurve_trimming = 'zeros'
				else:self.scurve_trimming = 'const'
			else:
				for i in striprange:
					self.ssa.strip.set_trimming(i, default_trimming)
					if(display):
						print "->  \tTrimming: Applied value %d to channel %d" % (default_trimming, i)
		elif(isinstance(default_trimming, np.ndarray) or isinstance(default_trimming, list)):
			for i in striprange:
				self.ssa.strip.set_trimming( i, default_trimming[i])
			if(display):
				print "->  \tTrimming: Applied trimming array" % (default_trimming)
			self.scurve_trimming = 'trimmed'

		elif(default_trimming != False and default_trimming != 'keep'):
			self.scurve_trimming = 'none'
			error(1)
		readback = np.zeros(120)
		for i in range(0,120):
			readback[i] = self.ssa.strip.get_trimming(i+1)
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
			self.set_trimming(trimdac)
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
				thidx , par = self._scurve_fit_errorfunction(sct, nevents)
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
			th, par = self._scurve_fit_errorfunction(
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


	def _scurve_fit_errorfunction(self, curve, nevents, expected = 'autodefine', errmsg="", reiterate = 3):
		sct = curve;
		err = True;	itr = 0;
		erret = (-1, [-1, -1, -1])

		if( np.size(np.where( curve > (nevents-1) )) < 1):
			print "Fitting Zeros " + errmsg
			return erret

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
			print "Fitting failed " + errmsg
			return erret

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
			return erret
		else:
			# readd number of th points removed by the noise cleaning
			thidx = int(round(par[1]))
			return thidx, par


	def _scurve_fit_gaussian(self, curve, errmsg="", reiterate = 10):
		guess_mean = np.argmax(curve)
		guess_sigma = np.size( np.where(curve > 10) )/6.0
		errret = [np.inf, np.inf, np.inf]
		if(guess_mean == 0 or guess_sigma == 0 ):
			print "Fitting zeros " + errmsg
			return errret
		err = True; itr = 0;
		while(err == True and itr < reiterate):
			try:
				par, cov = curve_fit(
					f = f_gauss,
					xdata = range(0, np.size(curve)-1),
					ydata = curve[0 : np.size(curve)-1],
					p0 = [1, guess_mean, guess_sigma])
			except:
				itr += 1
			else:
				err = False
		if(err):
			print "Fitting failed " + errmsg
			return errret
		else:
			return par

	def _scurve_fit_gaussian1(self, curve, x = 'default', errmsg="", reiterate = 10):
		if(x == 'default'):
			x = range(np.size(curve))
		guess_mean = np.argmax(curve)
		guess_sigma = np.size( np.where(curve > 10) )/6.0
		errret = [np.inf, np.inf, np.inf]
		if(guess_mean == 0 or guess_sigma == 0 ):
			print "Fitting zeros " + errmsg
			return errret
		gmodel = lmfitModel(f_gauss1)
		err = True; itr = 0;
		while(err == True and itr < reiterate):
			try:
				result = gmodel.fit(curve, x=x, A=1, mu=guess_mean, sigma=(guess_sigma) )
			except:
				itr += 1
			else:
				err = False
		if(err):
			print "Fitting failed " + errmsg
			return errret
		else:
			sigma = np.abs(result.params['sigma'].value)
			A = result.params['A'].value
			mu = result.params['mu'].value
			return  [A, mu, sigma]





	def shaper_pulse_rising(self, calpulse = 60, mode = 'caldll', targetbx = 25, resolution = 1, strip = 5, display = False, display_pattern = False, plot = True, thmin = 20, thmax = 255, iterations = 1, basedelay = 'auto', samplingmode = 'level'):
		# mode = [clkdll][caldll]
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		thlist = np.array(range(thmin, thmax, resolution))
		latency = np.ones(np.shape(thlist)[0], dtype = np.float16 )*(-np.inf)
		cnt = 0
		self.ssa.ctrl.activate_readout_normal()
		self.ssa.strip.set_enable(strip='all', enable=0, polarity=0, hitcounter=0, digitalpulse=0, analogpulse=0)
		self.ssa.inject.analog_pulse(initialise = True, hit_list = [strip], mode = samplingmode, threshold = [1,100], cal_pulse_amplitude = calpulse)
		self.ssa.ctrl.set_sampling_deskewing_coarse(0)
		self.ssa.ctrl.set_sampling_deskewing_fine(5, True, True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		self.I2C.peri_write('Bias_D5DLLB', 31) #to maximise the dll resolution
		self.ssa.strip.set_hipcut('default', 'all')
		self.ssa.strip.set_hipcut('disable', strip)
		if(not display and not display_pattern):
			utils.ShowPercent(0, len(thlist) , "Calculating..")
		if  (mode == 'caldll'): self.tempvalue = 62
		elif(mode == 'clkdll'): self.tempvalue = 0
		saturated = False
		for th in thlist:
			self.ssa.ctrl.set_threshold(th)
			latency[cnt], edge = self.deskew_samplingedge(
				strip = strip,
				targetbx = targetbx,
				step = 1,
				mode = mode,
				samplingmode=samplingmode,
				start = 0,
				shift = 2,
				display = False,
				iterations = iterations,
				displaypercent = display,
				display_pattern = display_pattern
			)
			if(latency[cnt] > 100):
				saturated = True
			if(cnt == 0):
				if(basedelay == 'auto'):  latency0 = latency[0]
				else:  latency0 = 25*(targetbx-22)+basedelay
			if(mode == 'clkdll'):
				latency[cnt] = latency[cnt] - latency0
			elif(mode == 'caldll'):
				latency[cnt] = latency0 - latency[cnt]
			if(not display):
				utils.ShowPercent(cnt, len(thlist) , ("Th = %d -> latency = %3.5f" % (th, latency[cnt])))
				print ''
			cnt += 1
			if(saturated):
				break
		if(not display and not display_pattern):
			utils.ShowPercent(100, 100 , "Done.                       ")
		if(plot):
			plt.axis([0, np.max(latency)+5, 0, 150])
			plt.plot(latency, thlist, 'o')
			plt.show()
		return latency, thlist

	def shaper_pulse_falling(self, calpulse = 60, mode = 'caldll', targetbx = 25, resolution = 1, strip = 5, display = False, display_pattern = False, plot = True, thmin = 20, thmax = 255, iterations = 1, basedelay = 'auto', samplingmode = 'level'):
		# mode = [clkdll][caldll]
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		thlist = np.array(range(thmin, thmax, resolution))
		latency = np.ones(np.shape(thlist)[0], dtype = np.float16 )*(-np.inf)
		cnt = 0
		self.ssa.ctrl.activate_readout_normal()
		self.ssa.strip.set_enable(strip='all', enable=0, polarity=1, hitcounter=0, digitalpulse=0, analogpulse=0)
		self.ssa.inject.analog_pulse(initialise = True, hit_list = [strip], mode = samplingmode, threshold = [1,100], cal_pulse_amplitude = calpulse)
		#self.ssa.strip.set_polarity(1, strip)
		self.ssa.strip.set_hipcut('default', 'all')
		self.ssa.strip.set_hipcut('disable', strip)
		self.ssa.ctrl.set_sampling_deskewing_coarse(0)
		self.ssa.ctrl.set_sampling_deskewing_fine(5, True, True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		self.I2C.peri_write('Bias_D5DLLB', 31) #to maximise the dll resolution
		if(not display and not display_pattern):
			utils.ShowPercent(0, len(thlist) , "Calculating..")
		if  (mode == 'caldll'): self.tempvalue = 60
		elif(mode == 'clkdll'): self.tempvalue = 0
		saturated = False
		for th in thlist:
			self.ssa.ctrl.set_threshold(th)
			latency[cnt], edge = self.deskew_samplingedge(
				strip = strip,
				targetbx = targetbx,
				step = 1,
				mode = mode,
				samplingmode=samplingmode,
				start = 0,
				shift = 2,
				display = False,
				iterations = iterations,
				displaypercent = display,
				display_pattern = display_pattern,
				polarity = 'falling'
			)
			if(latency[cnt] > 100):
				saturated = True
			if(cnt == 0):
				if(basedelay == 'auto'):  latency0 = latency[0]
				else:  latency0 = 25*(targetbx-22)+basedelay
			if(mode == 'clkdll'):
				latency[cnt] = latency[cnt] - latency0
			elif(mode == 'caldll'):
				latency[cnt] = latency0 - latency[cnt]
			if(not display):
				utils.ShowPercent(cnt, len(thlist) , ("Th = %d -> latency = %3.5f" % (th, latency[cnt])))
				print ''
			cnt += 1
			if(saturated):
				break
		if(not display and not display_pattern):
			utils.ShowPercent(100, 100 , "Done.                       ")
		if(plot):
			plt.axis([0, np.max(latency)+5, 0, 150])
			plt.plot(latency, thlist, 'o')
			plt.show()
		return latency, thlist


	def sampling_slack(self, strips = [50], shift = 0, samplingmode='level', display=True, debug = False):
		delay = []
		cnt = 0
		for s in strips:
			cnt += 1
			self.ssa.inject.analog_pulse(hit_list = [s], mode = samplingmode, initialise = False)
			sdel = self.ssa.readout.cluster_data_delay(shift = shift, display = display, debug = debug)
			delay.append(sdel)
			if(display): utils.ShowPercent(cnt, len(strips), " Sampling")
		if(display): utils.ShowPercent(len(strips), len(strips), " Done")
		return delay


	def data_latency(self, strip = 50, shift = 0, samplingmode='level', iterations = 1, display_pattern = False, polarity = 'rising'):
		lv = np.ones(iterations, dtype = np.float16)*np.inf
		for i in range(0, iterations):
			#self.ssa.inject.analog_pulse(hit_list = [strip], mode = samplingmode, initialise = False, trigger = False)
			cl_array = self.ssa.readout.cluster_data(shift = shift, lookaround = True, display_pattern = display_pattern, initialize = False)
			tmp = (np.where( cl_array[0,:] == strip )[0])
			if (np.size(tmp) > 0):
				if (polarity == 'rising'):
					val = float(tmp[0])
					if( cl_array[0, int(val)-1] == 0):
						lv[i] = float(tmp[0])
				elif (polarity == 'falling'):
					val = float(tmp[-1])
					print cl_array[0,:]
					if( cl_array[0, int(val)+1] == 0):
						 lv[i] = float(tmp[-1])
				else:
					exit(1)
			else:
				lv[i] = np.inf
		lvtmp = lv[ np.where(lv<256) ]
		###lvtmp = lv; lvtmp[lvtmp>256] = 0;
		if(np.size(np.where(lv>256)) < 1):
		#if (np.size(lvtmp) > 0):
			latency=np.mean(lvtmp)
		else:
			latency=np.inf
		return latency


	def deskew_samplingedge(self, strip, mode = 'clkdll', targetbx = 1 , step = 1, samplingmode='level', start = 1, shift = 2, display = False, displaypercent = True, raw = False, msg='', iterations = 10, display_pattern = False, polarity = 'rising'):
		if(mode == 'clkdll'):
			latency, edge = self._deskew_samplingedge_clk_dll(strip=strip, target = targetbx, step=step, start=start, shift=shift+4, display=display, displaypercent=displaypercent, msg=msg, samplingmode=samplingmode, iterations = iterations, display_pattern = display_pattern)
		elif(mode == 'caldll'):
			latency, edge = self._deskew_samplingedge_cal_dl( strip=strip, target = targetbx, step=step, start=start, shift=shift+7, display=display, displaypercent=displaypercent, msg=msg, samplingmode=samplingmode, iterations = iterations, display_pattern = display_pattern, polarity = polarity)
		else:
			error(1)
		return latency, [edge[0], edge[1]]


	def _deskew_samplingedge_clk_dll(self, strip, target, shift = 2, samplingmode='level', display = False, displaypercent = True, msg='', step = 1, start = 0,  iterations = 1, display_pattern = False):
		edge = [False, False]
		for i, j in itertools_product(range(start,7), range(0, 16, step)):
			if(displaypercent):
				utils.ShowPercent(i*16+j, 16*8, msg + " Sampling..")
			self.ssa.ctrl.set_sampling_deskewing_coarse(value = i)
			self.ssa.ctrl.set_sampling_deskewing_fine(value = j, enable = True, bypass = True)
			sleep(0.01)
			delay = self.data_latency(strip = strip, shift = shift, samplingmode=samplingmode, iterations = iterations, display_pattern = display_pattern)
			if(display):
				print "deskewing = [%d][%d] \t->  delay = %s)" % (i, j, delay)
			if (delay == target):
				break
		latency = float(i*3.125 + j*0.1953125)
		if(displaypercent):
			utils.ShowPercent(100, 100, msg + " Delay = %3.4f [%d-%d]" % (latency, edge[0], edge[1]) )
		return latency, [i, j]


	def _deskew_samplingedge_cal_dl(self, strip, target, shift = 2, samplingmode='level', display = False, displaypercent = True, msg='', step = 1, start = 0, iterations = 1, display_pattern = False, polarity = 'rising'):
		edge = 0
		delay = np.inf
		temp = np.zeros(3)
		#if (polarity == 'rising'):
		#	rangelist = range(self.tempvalue+3, -1, -1)
		#elif (polarity == 'falling'):
		#	rangelist = range(self.tempvalue+3, -1, -1)
		rangelist = range(63, -1, -1)
		for i in rangelist:	#range(63, -1, -1):
			if(displaypercent):
				utils.ShowPercent(i, 64, msg + " Sampling..")
			self.ssa.ctrl.set_cal_pulse_delay(i)
			sleep(0.01)
			latency = self.data_latency(strip = strip, shift = shift, samplingmode=samplingmode, iterations = iterations, display_pattern = display_pattern, polarity=polarity)
			if(display):
				print "->  \tdeskewing = [%d] \t->  latency = %s)" % (i, latency)
			temp = np.insert(temp[:-1], 0, latency)
			if(temp[0]>256 and temp[1]>256 and temp[2]>256):
				delay = np.inf
				#break
			elif (latency == target):
				delay = i
				#break
		self.tempvalue = delay
		latency = float(delay)* self.calpulse_dll_resolution
		return latency , [delay, 0]


	def delayline_resolution(self, set_bias = False, shift = 3, display = False, debug = False):
		prev = 0xff
		if(isinstance(set_bias, int)):
			if(set_bias > 0 and set_bias < 64):
				self.I2C.peri_write('Bias_D5DLLB', set_bias) # to change the resolution
		self.ssa.strip.set_enable(strip='all', enable=0, polarity=0, hitcounter=0, digitalpulse=0, analogpulse=0)
		self.ssa.inject.analog_pulse(initialise = True, hit_list = [], mode = 'edge', threshold = [50,200], cal_pulse_amplitude = 200)
		self.ssa.ctrl.set_cal_pulse_delay('on')
		r = []
		for i in range(0,64):
			self.ssa.ctrl.set_cal_pulse_delay(i)
			tmp = self.sampling_slack(strips = [50], display=False, debug = debug, shift = shift, samplingmode='edge')
			if(np.size(tmp[0]) > 0):
				r.append(tmp[0][0])
				if(tmp[0][0] == 1 and prev == 1):
					break # to speedup
				if(i == 0 and tmp[0][0] > -1):
					break
				prev = tmp[0][0]
			else: # delay out of considered range (< -2 or > +2)
				r.append(0xff)
			utils.ShowPercent(i, 63, "Calculating")
		if(display): print r
		tmp = np.size( np.where(  np.array(r) == 0 ) )
		if(tmp > 0):
			resolution = 25.0 / tmp
			rtval = '%5.3fns' % resolution
			self.calpulse_dll_resolution = resolution
		else:
			rtval = 'error'
			self.calpulse_dll_resolution = -1
		return rtval
		#  ssa.ctrl.set_cal_pulse_delay(11)
		#  measure.deskew_samplingedge(step = 1)
		#  I2C.peri_write('Bias_D5DLLB', 20)


	def noise_occupancy(self, nevents = 100, upto = 20, plot = True):
		integ = []
		self.ssa.readout.l1_data(initialise = True)
		for th in range(0, upto+1):
			count = [0]*120
			self.ssa.ctrl.set_threshold(th)
			for i in range(0, nevents):
				utils.ShowPercent(th*nevents + i, (upto+1)*nevents , "Calculating")
				lcnt, bcnt, hit, hip = self.ssa.readout.l1_data(initialise = False)
				for s in range(0,120):
					if s in hit:
						count[s] += 1
			integ.append(count)
		utils.ShowPercent(100, 100, "Done")
		noise_occupancy = (np.array(integ) / float(nevents)) * 100.0
		plt.clf()
		plt.plot(noise_occupancy)
		plt.show()
		return noise_occupancy
