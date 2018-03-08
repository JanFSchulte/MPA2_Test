from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from itertools import product as itertools_product

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_measurements():

	def __init__(self, ssa, I2C, fc7, cal):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.cal = cal

	def sampling_slack(self, strips = range(1,121), display=True, shift = 0, calpulse = 200, threshold = 50, samplingmode='edge'): 
		delay = []
		cnt = 0
		for s in strips:
			cnt += 1
			self.ssa.inject.analog_pulse(hit_list = [s], mode = 'edge', initialise = False)
			cl_array , sdel = self.ssa.readout.cluster_data_delay(shift = shift)
			delay.append(sdel)
			if(display): utils.ShowPercent(cnt, len(strips), " Sampling")
		if(display): utils.ShowPercent(len(strips), len(strips), " Done")	
		return delay

	def deskew_samplingedge(self, strip, step = 1, start = 1, shift = 2, display = False, displaypercent = True, raw = False, msg=''):
		prev1 = 0xff
		prev2 = 0xff

		edge = [False, False]
		for i, j in itertools_product(range(start,7), range(0, 16, step)): 
			if(displaypercent): 
				utils.ShowPercent(i*16+j, 16*8, msg + " Sampling..")
			self.ssa.ctrl.set_sampling_deskewing_coarse(value = i)
			self.ssa.ctrl.set_sampling_deskewing_fine(value = j, enable = True, bypass = True)
			sleep(0.01)
			delay = self.sampling_slack(strip, display = False, shift = shift)
			if(display): 
				print "deskewing = [%d][%d] \t->  delay = %s)" % (i, j, delay)
			if(delay < prev2 and prev1 < prev2): 
				if(j>0): edge = [i,j-1]
				else: edge = [i-1,15]
				break
			prev2 = prev1
			prev1 = delay
		latency = float(edge[0]*3.125 + edge[1]*0.1953125)
		if(displaypercent): 
			utils.ShowPercent(100, 100, msg + " Delay = %3.4f" % latency)
		return latency if not raw else edge

	def delayline_resolution(self):
		r = []
		for i in range(0,64):
			self.ssa.ctrl.set_cal_pulse_delay(i)
			r.append(self.sampling_slack(strips = [50], display=False, shift = 3))
			utils.ShowPercent(i, 63, "Calculating")
		resolution = 25.0 / np.size( np.where(  np.array(r) == 0 ) )
		return '%0.3fns' % resolution

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


	def shaper_pulse_reconstruction(self, thlist, calpulse, strip = [50], display = True, plot = False):
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		val = np.zeros(256, dtype = np.float16 )
		edgemax = 0

		self.ssa.ctrl.activate_readout_normal()
		self.ssa.strip.set_enable(strip='all', enable=0, polarity=0, hitcounter=0, digitalpulse=0, analogpulse=0)
		self.ssa.inject.analog_pulse(initialise = True, hit_list = [], mode = 'level', threshold = [0,0], cal_pulse_amplitude = calpulse)

		for th in thlist: 
			self.ssa.ctrl.set_threshold(th)
			edge = self.deskew_samplingedge(strip = strip, step = 1, start = edgemax, shift = 2, display = False, raw = True)
			if(isinstance(edge[0], int)): 
				val[th] = edge[0]*3.125 + edge[1]*0.1953125
			else:
				val[th] = False
			if(edge[0]>edgemax):
				edgemax = edge[0]

		if(plot): 
			plt.plot(val, 'o')
			plt.show()
		return val



