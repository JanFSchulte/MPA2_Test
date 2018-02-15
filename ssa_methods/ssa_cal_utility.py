from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

class SSA_cal_utility():

	def __init__(self, ssa, I2C, fc7):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7

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
		
		return scurves

