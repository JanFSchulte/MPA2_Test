from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


def errorf(x, *p):
    a, mu, sigma = p
#    print x
    return 0.5*a*(1.0+erf((x-mu)/sigma))

def line(x, *p):
    g, offset = p
    return  numpy.array(x) *g + offset

def gauss(x, *p):
    A, mu, sigma = p
    return A*numpy.exp(-(x-mu)**2/(2.*sigma**2))

def errorfc(x, *p):
    a, mu, sigma = p
    return a*0.5*erfc((x-mu)/sigma)



class SSA_cal_utility():

	def __init__(self, ssa, I2C, fc7):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.scurve_data = False
		self.scurve_nevents  = 0
		self.scurve_calpulse = 0

	def scurves(self, cal_pulse_amplitude = [100], nevents = 1000, display = False, plot = True, filename = False, filename2 = ""):
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		# first go to the async mode
		self.ssa.ctrl.activate_readout_async()
		plt.clf()

		if isinstance(cal_pulse_amplitude, int):
			cal_pulse_amplitude = [cal_pulse_amplitude]
		elif not isinstance(cal_pulse_amplitude, list): 
			return False
		
		for cal_val in  cal_pulse_amplitude:
			# close shutter and clear counters
			close_shutter(1)
			clear_counters(1)
			# init chip cal pulse
			self.ssa.ctrl.init_cal_pulse(cal_val, 5)
			# init firmware cal pulse
			Configure_TestPulse_MPA_SSA(200, nevents)

			# then let's try to measure the scurves
			scurves = np.zeros((256,120), dtype=np.int)
			
			threshold = 0
			while (threshold < 256):
				# debug output		
				strout = ""
				error = False
				#print "Setting the threshold to ", threshold, ", sending the test pulse and reading the counters"
				# set the threshold
				strout += "threshold = " + str(threshold) + ".   " 
				self.ssa.ctrl.set_threshold(threshold)
				# clear counters
				clear_counters(1)
				# open shutter
				open_shutter(2)
				open_shutter(2)
				# send sequence of NEVENTS pulses
				SendCommand_CTRL("start_trigger")
				# sleep a bit and wait for trigger to finish
				sleep(0.01)
				while(self.fc7.read("stat_fast_fsm_state") != 0):
					sleep(0.1)
				# close shutter and read counters
				close_shutter(1)
				failed, scurves[threshold] = self.ssa.readout.read_counters_fast()
				if (failed): error = True
				if (threshold > 0):
					if (scurves[threshold,0] == 0 and  scurves[threshold-1,0] > (nevents*0.9)) : error = True

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
					utils.ShowPercent(threshold, 256, "Calculating S-Curves                                       ")
			
			utils.ShowPercent(256, 256, "Done calculating S-Curves")

			if( isinstance(filename, str) ):
				fo = "../SSA_Results/" + filename + "_scurve_" + filename2 + "__cal_" + str(cal_val) + ".csv"
				CSV.ArrayToCSV (array = scurves, filename = fo, transpose = True)

			if(plot == True):
				plt.plot(scurves)

		if(plot == True):
			plt.show()

		self.scurve_data     = scurves
		self.scurve_nevents  = nevents
		self.scurve_calpulse = cal_pulse_amplitude

		return scurves

	def trimming_apply(self, default_trimming = 'keep_current', striprange = range(1,121)):
		r = True

		if(isinstance(default_trimming, int)):
			trimdac_value = np.zeros(120)
			self.I2C.strip_write("THTRIMMING", 0, default_trimming)
			print "Trimming: Applied value %d to all channels" % (default_trimming)
			if(default_trimming == 0):
				self.scurve_trimming = 'zeros'
			else:
				self.scurve_trimming = 'const'
		elif(isinstance(default_trimming, np.ndarray) or isinstance(default_trimming, list)):
			trimdac_value = np.array(default_trimming)
			for i in striprange:
				self.I2C.strip_write("THTRIMMING", i, default_trimming[i])
			print "Trimming: Applied trimming array" % (default_trimming)
			self.scurve_trimming = 'trimmed'
		elif(default_trimming != False or default_trimming != 'keep_current'):
			self.scurve_trimming = 'none'
			exit(1)
		return trimdac_value


	def errfitting_get_mean(self, curve, nevents, expected = 'autodefine', errmsg="", reiterate = 3):
		sct = curve
		err = True
		itr = 0
		# get read of the noise peack 
		while ( not ((sct[0] == nevents) and (sct[1] == nevents)) ):
			sct = sct[ np.argmax(sct)+1 : ]
		
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
				# fit the curve with 1-error_function 
				# and find the mean
				par, cov = curve_fit(
					f     = errorfc, 
					xdata = range(0, len(sct)-1), 
					ydata = sct[1 : len(sct)], 
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
			thidx = int(round( par[1] + (255-len(sct)) ))
			return thidx


	def trimming_evaluate_thdac_trimdac_ratio(self, trimdac_pvt_calib = False, cal_pulse_amplitude = 100, th_nominal = 115,  nevents = 500, plot = False):
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
					cal_pulse_amplitude = cal_pulse_amplitude, 
					nevents = nevents, 
					display = False, 
					plot = False, 
					filename = False
				)
			)
			
			for strip in range(0,120):
				sct = sc[cnt][:,strip]
				thidx = self.errfitting_get_mean(sct, nevents)
				thtmp[strip] = thidx
			th.append( thtmp )
			cnt += 1 
		if(plot):
			plt.plot(th)
			plt.show()
		ratios = 32.0 / (th[0]-th[1])
		return ratios


	def trimming_scurves(self, cal_pulse_amplitude = 100, th_nominal = 'evaluate', default_trimming = 'keep_current', striprange = range(1,121), ratio = 'evaluate', iterations = 3, nevents = 1000, plot = True, display = True, reevaluate = True):
		
		# evaluate TRIMDAC/THDAC ratio
		if(ratio == 'evaluate'):
			dacratiolist = self.trimming_evaluate_thdac_trimdac_ratio(trimdac_pvt_calib = False, cal_pulse_amplitude = cal_pulse_amplitude, th_nominal = th_nominal,  nevents = nevents, plot = False)
		elif isinstance(ratio, float) or isinstance(ratio, int):
			dacratiolist = [ratio]*120
		else: exit(1)

		# evaluate expected threshold value
		if(th_nominal == 'evaluate'):
			th_expected = 0
		else:
			th_expected = th_nominal

		# apply the starting trimming
		trimdac_value = self.trimming_apply(default_trimming, striprange)
		
		# evaluate inital S-Curves
		scurve_data_available = False
		if(isinstance(self.scurve_data, np.ndarray)):
			if((reevaluate == False) and (self.scurve_nevents == nevents) and (self.scurve_calpulse == cal_pulse_amplitude) ):
				scurve_data_available = True
				scurve_init = self.scurve_data
				print "Trimming: Using available S-Curves data"
		if(scurve_data_available == False):
			scurve_init = self.scurves(
				cal_pulse_amplitude = cal_pulse_amplitude, 
				nevents = nevents, 
				display = False, 
				plot = True, 
				filename = False
			)
		scurve = scurve_init
		if(display):
			print "Trimming DAC values: " + str(trimdac_value)

		# start trimming on the S-Curves
		for i in range(0, iterations):
			for strip in striprange:
				
				# fit the S-Curve and find the actual threshold
				th_initial = self.errfitting_get_mean(
					curve = scurve[: , strip-1],
					nevents = nevents,
					expected = 'autodefine',
					errmsg = "", 
					reiterate = 3
				)
				#calculate the trimming DAC correcton value
				trimdac_correction    = int(round((th_nominal - th_initial) * dacratiolist[strip-1] ))
				trimdac_current_value = self.I2C.strip_read("THTRIMMING", strip)
				trimdac_value[strip-1]  = trimdac_current_value + trimdac_correction
				if(trimdac_value[strip-1] > 31):
					print "Reached high trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 31
				elif(trimdac_value[strip-1] < 0):
					print "Reached low trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 0

				# Apply correction to the trimming DAC				
				self.I2C.strip_write("THTRIMMING", strip, int(trimdac_value[strip-1]))

			if(display):
				print "Trimming DAC values: " + str(trimdac_value)

			# evaluate new S-Curves
			scurve = self.scurves(
				cal_pulse_amplitude = cal_pulse_amplitude, 
				nevents = nevents, 
				display = False, 
				plot = True, 
				filename = False
			)

		#plot initial and final S-Curves
		if(plot):
			plt.clf()
			plt.plot(scurve_init, 'b')
			plt.plot(scurve_init, 'r')
			plt.show()

		return trimdac_value
