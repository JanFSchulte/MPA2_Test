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

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, biascal = False):
		self.ssa      = ssa
		self.I2C      = I2C
		self.fc7      = fc7
		self.cal      = cal
		self.bias     = biascal
		self.muxmap   = analog_mux_map

	def scurves(self, cal_list = [50], trim_list = 'keep', mode = 'all', rdmode = 'fast', filename = False, plot = True):
		plt.clf()
		if (isinstance(filename, str)):
			filename =  filename+'/'+filename
		data = []
		for cal in cal_list:
			if(trim_list == 'keep'):
				d = self.cal.scurves(cal_ampl = cal, filename = filename, mode = mode, rdmode = rdmode, filename2 = 'trim', plot = False, msg = "CAL = " + str(cal))
				data.append(d)
			else:
				for trim in trim_list:
					t = self.cal.set_trimming(trim, 'all', False)
					d = self.cal.scurves(cal_ampl = cal, filename = filename, mode = mode, rdmode = rdmode, filename2 = 'trim'+str(trim), plot = False, msg = "[CAL=" + str(cal) +"][TRIM="+str(trim)+']')
					data.append(d)
		if plot: plt.show()
		return data



	def baseline_noise(self, striplist = range(1,120), filename = False, plot = True):
		data = np.zeros([120, 256])
		parameters = []
		cnt = 0
		for s in striplist:
			tmp = self.cal.scurves(cal_ampl='baseline', rdmode = 'i2c', mode = 'sbs', striplist = [s], plot = False, speedup = True)
			data[s-1] = tmp[:,s-1]
			cnt += 1
			par, cov = self.cal._scurve_fit_gaussian(curve = data[s-1], errmsg=' for strip %d'%s)
			parameters.append(par)
			x = range(1, np.size(data[s-1]))
			plt.plot(x, f_gauss(x, par[0], par[1], par[2]))
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "/Scurve_NoiseBaseline/" + filename + "_scurve_trim31__cal_0.csv"
			CSV.ArrayToCSV (array = data, filename = fo, transpose = False)
			print "->  \tData saved in" + fo
		if(plot):
			plt.show()
		return  parameters #[A, mu, sigma]



	def scurve_trim_spread(self, filename = 'Chip1', calpulse = 50, plot = True, iterations = 5):
		scurve_init, scurve_trim = self.cal.trimming_scurves(method = 'center', default_trimming = 15, cal_ampl = calpulse, iterations = iterations, plot = False)
		data = self.scurves(cal_list = [calpulse], trim_list = [0, 31], name = filename)
		scurve_0 = data[0]
		scurve_31 = data[1]
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "/" + filename + "_scurve_trim15__cal_" + str(calpulse) +".csv"
			CSV.ArrayToCSV (array = scurve_init, filename = fo, transpose = True)
			fo = "../SSA_Results/" + filename + "/" + filename + "_scurve_trim__cal_" + str(calpulse) +".csv"
			CSV.ArrayToCSV (array = scurve_trim, filename = fo, transpose = True)
		if plot:
			plt.clf()
			plt.figure(1)
			plt.plot(scurve_init, 'b', alpha = 0.5)
			plt.plot(scurve_trim, 'r', alpha = 0.5)
			tmp, par_init = self.cal.evaluate_scurve_thresholds(scurve = scurve_init, nevents = 1000)
			tmp, par = self.cal.evaluate_scurve_thresholds(scurve = scurve_trim, nevents = 1000)
			plt.figure(2)
			xplt = np.linspace(0,256, 2561)
			for i in par_init:
				plt.plot( xplt, f_errorfc(xplt, i[0], i[1], i[2]) , 'b', alpha = 0.5)
			for i in par:
				plt.plot( xplt, f_errorfc(xplt, i[0], i[1], i[2]) , 'r', alpha = 0.5)
			plt.figure(3)
			plt.axis([calpulse*1.15-30, calpulse*1.15+30, 0, 1010])
			plt.plot(scurve_0,    'b', alpha = 0.5)
			plt.plot(scurve_31,   'r', alpha = 0.5)
			plt.plot(scurve_trim, 'y', alpha = 0.5)
			plt.show()
			return scurve_trim, scurve_init



	def shaper_pulse(self, calrange = [46, 58, 69, 81], strip = 5, baseline = 'auto', iterations = 10, pattern = False):
		shaper_rise = []; shaper_fall = [];
		thresholds_list = []; shapervalues_list = [];
		self.cal.set_trimming(0, 'all')
		self.cal.set_trimming(31, [strip])
		if(isinstance(baseline, int)):
			self.cal.baseline = baseline
		else:
			a, mu, sigma = self.baseline_noise([strip], plot=False)[0]
			self.cal.baseline = int(np.round(mu))
			print "->  \tBaseline = %3.2f" % self.cal.baseline
		thmin = self.cal.baseline+5   # thmin measured = 8.5 THDAC (0.3fC)
		for cal in calrange:
			latency, thlist = self.cal.shaper_pulse_rising(
				calpulse = cal,
				mode = 'caldll', targetbx = 25,
				thmin = int(thmin), thmax = 255,
				resolution = 5, iterations = iterations,
				basedelay = 10, plot = False, display_pattern = pattern)
			shaper_rise.append(latency)
			thlist_rise = np.array(thlist)

			latency, thlist = self.cal.shaper_pulse_falling(
				calpulse = cal,
				mode = 'caldll', targetbx = 25,
				thmin = int(thmin), thmax = 255,
				resolution = 5, iterations = iterations,
				basedelay = 10, plot = False, display_pattern = pattern)
			shaper_fall.append(latency)
			thlist_fall = np.array(thlist)


			#for i in np.unique(shaper_rise[-1]):
			#	tmp = np.where(shaper_rise[-1] == i)
			#	mean = np.mean( thlist_rise[tmp])
			#	thlist_rise[tmp] = mean
			#for i in np.unique(shaper_fall[-1]):
			#	tmp = np.where(shaper_fall[-1] == i)
			#	mean = np.mean( thlist_fall[tmp])
			#	thlist_fall[tmp] = mean

			thresholds = np.concatenate( [ np.array(thlist_rise)-self.cal.baseline , np.array(thlist_fall)-self.cal.baseline ] )
			shapervalu = np.concatenate( [ shaper_rise[-1], shaper_fall[-1] ] )
			plt.axis([0, np.max(shaper_rise[-1])*2.5, 0, thresholds[ np.where(shaper_rise[-1]>-256)[0] ][-1] + 20 ])
			plt.plot(shapervalu, thresholds, 'o')
			thresholds_list.append(thresholds); shapervalues_list.append(shapervalu)
		plt.show()
		return thresholds_list, shapervalues_list



	def dac_linearity(self, name = 'Bias_THDAC', nbits = 8, ideal_gain = 1.840, ideal_offset = 0.8, filename = False, plot = True):
		if(self.bias == False): return False, False
		if(not (name in self.muxmap)): return False, False
		nlin_params, nlin_data, fit_params, raw = self.bias.measure_dac_linearity(
			name = name,
			nbits = nbits,
			filename = filename,
			filename2 = "",
			plot = False,
			average = 10)
		g, ofs, sigma = fit_params
		DNL, INL = nlin_data
		DNLMAX, INLMAX = nlin_params
		x, data = raw
		if name == 'Bias_THDAC':
			baseline = self.bias.get_voltage('Bias_BOOSTERBASELINE')
			data = (0 - np.array(data)) + baseline
		elif name in self.muxmap:
			data = np.array(data)
		else: return False
		if plot:
			plt.clf()
			plt.figure(1)
			plt.plot(x, f_line(x, ideal_gain/1000, ideal_offset/1000), '-b', linewidth=5, alpha = 0.5)
			plt.plot(x, data, '-r', linewidth=5,  alpha = 0.5)
			plt.figure(2); plt.ylim(-1, 1); plt.bar( x, DNL, color='b', edgecolor = 'b', align='center')
			plt.figure(3); plt.ylim(-1, 1); plt.bar( x, INL, color='r', edgecolor = 'r', align='center')
			plt.figure(4); plt.ylim(-1, 1); plt.plot(x, INL, color='r')

			plt.show()

		return DNL, INL, x, data
		return DNLMAX, INLMAX

	def delayline_resolution(self, debug = False):
		resolution = []
		resolution.append( "MAX: " + self.cal.delayline_resolution(set_bias = 31, shift = 3, display = debug, debug = False) )
		resolution.append( "TYP: " + self.cal.delayline_resolution(set_bias = 15, shift = 3, display = debug, debug = False) )
		#resolution.append( "MIN: " + self.cal.delayline_resolution(set_bias =  1, shift = 3, display = debug, debug = False) )
		return resolution




'''
plt.axis([20, 100, 0, 1050])
plt.plot(s0,    'b', colour = #85C0DE)
plt.plot(s31,   'r', )
plt.plot(s, 	'y', )
plt.show()
'''
