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
		self.scurvedata = False

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
					utils.ShowPercent(threshold, 256, "Calculating S-Curves for threshold " + str(threshold) + "                                        ")
			
			utils.ShowPercent(256, 256, "Done")

			if( isinstance(filename, str) ):
				fo = "../SSA_Results/" + filename + "_scurve_" + filename2 + "__cal_" + str(cal_val) + ".csv"
				CSV.ArrayToCSV (array = scurves, filename = fo, transpose = True)

			if(plot == True):
				plt.plot(scurves)

		if(plot == True):
			plt.show()

		self.scurvedata = scurves
		return scurves

	def trimming_apply(self, default_trimming = 0, striprange = range(1,121)):
		r = True
		if(isinstance(default_trimming, int)):
			trimdac_value = np.zeros(120)
			self.I2C.strip_write("THTRIMMING", 0, default_trimming)
		elif(isinstance(default_trimming, np.ndarray) or isinstance(default_trimming, list)):
			trimdac_value = np.array(default_trimming)
			for i in striprange:
				self.I2C.strip_write("THTRIMMING", i, default_trimming[i])
		else:
			exit(1)
		return trimdac_value



	def trimming_scurves(self, default_trimming = False, striprange = range(1,121), iterations = 3, cal_pulse_amplitude = 100, th_nominal = 115, ratio = 3.90, nevents = 1000, plot = True):
		
		trimdac_value = self.trimming_apply(default_trimming, striprange)

		scurve_init = self.scurves(
			cal_pulse_amplitude = cal_pulse_amplitude, 
			nevents = nevents, 
			display = False, 
			plot = True, 
			filename = False
		)

		#scurve_init = self.scurvedata

		scurve = scurve_init
		print "Trimming DAC values: " + str(trimdac_value)

		for i in range(0, iterations):
			for strip in striprange:
				th_start = np.argmax(scurve[:,strip-1]) + 10
				th_stop = 180
				th_start = 80
				try:
					par, cov = curve_fit(
						errorfc, 
						range(th_start, th_stop), 
						scurve[th_start+1 : th_stop+1, strip-1], 
						p0 = [nevents, th_nominal, 2]
					)
				except RuntimeError:
					print "Fitting failed for Strip " + str(strip)

				th_initial            = int(round(par[1]))
				trimdac_correction    = int(round((th_nominal - th_initial)/ratio))
				trimdac_current_value = self.I2C.strip_read("THTRIMMING", strip-1)
				trimdac_value[strip-1]  = trimdac_current_value + trimdac_correction

				print th_initial, "  ", trimdac_correction , "  ", trimdac_current_value , "  ", trimdac_value[strip-1]

				if(trimdac_value[strip-1] > 31):
					print "Reached high trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 31
				elif(trimdac_value[strip-1] < 0):
					print "Reached low trimming limit for strip" + str(strip)
					trimdac_value[strip-1] = 0
				
				self.I2C.strip_write("THTRIMMING", strip, int(trimdac_value[strip-1]))

			if(i < iterations):
				scurve = self.scurves(
					cal_pulse_amplitude = cal_pulse_amplitude, 
					nevents = nevents, 
					display = False, 
					plot = True, 
					filename = False
				)
			print "Trimming DAC values: " + str(trimdac_value)


'''
scurve[:, 110]
s = np.array([ 1959,  1828,  1501,  2000, 11966, 18051, 31600,  6354,  2265,
        2016,  2005,  2001,  2000,  2000,  2000,  2001,  2000,  2000,
        2000,  2000,  2000,  1998,  1969,  1850,  1596,  1300,  1088,
        1019,  1004,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,  1000,
        1000,  1000,   998,   977,   861,   607,   310,   110,    20,
           1,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0,     0,     0,     0,     0,     0,
           0,     0,     0,     0])

'''