from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from itertools import product as itertools_product
from collections import OrderedDict
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_measurements():

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, pwr, biascal = False):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = fc7; self.utils = utils;
		self.cal = cal; self.bias = biascal; self.muxmap = analog_mux_map; self.pwr = pwr;

	def scurves(self, cal_list = [50], trim_list = 'keep', mode = 'all', rdmode = 'fast', filename = False, runname = '', plot = True, nevents = 1000, speeduplevel = 2):
		plt.clf()
		data = []
		if(isinstance(filename, str)):
			fo = "../SSA_Results/" + filename + "_" + str(runname)
		else:
			fo = False
		for cal in cal_list:
			if(trim_list == 'keep'):
				d = self.cal.scurves(cal_ampl = cal, nevents = nevents,filename = fo, mode = mode, rdmode = rdmode,filename2 = 'trim',speeduplevel = speeduplevel,plot = False, msg = "CAL = " + str(cal))
				data.append(d)
			else:
				for trim in trim_list:
					t = self.cal.set_trimming(trim, 'all', False)
					d = self.cal.scurves(cal_ampl = cal, nevents = nevents,filename = fo, mode = mode, rdmode = rdmode,filename2 = 'trim'+str(trim),speeduplevel = speeduplevel,plot = False, msg = "[CAL=" + str(cal) +"][TRIM="+str(trim)+']')
					data.append(d)
		if plot:
			plt.clf()
			for i in data:
				plt.plot(i)
			plt.show()
		return data



	def baseline_noise(self, striplist = range(1,121), mode = 'sbs', ret_average = True, filename = False, runname= '', plot = True, filemode = 'w'):
		print "->  \tBaseline Noise Measurement"
		data = np.zeros([120, 256])
		A = []; sigma = []; mu = []; cnt = 0;
		if(mode == 'sbs'):
			for s in striplist:
				tmp = self.cal.scurves(cal_ampl='baseline', filename = False, rdmode = 'i2c', mode = 'sbs', striplist = [s], plot = False, speeduplevel = 2)
				data[s-1] = tmp[:,s-1];	cnt += 1;
			if isinstance(filename, str):
				fo = "../SSA_Results/" + filename + "_" + str(runname) + "_scurve_SbS__cal_" + str(0) + ".csv"
				CSV.ArrayToCSV (array = data, filename = fo, transpose = False)
				print "->  \tData saved in" + fo
		elif(mode == 'all'):
			tmp = self.cal.scurves(cal_ampl='baseline', filename = "../SSA_Results/" + filename + "_" + str(runname), rdmode = 'fast', mode = 'all', striplist = striplist, plot = False, speeduplevel = 2)
			data = np.transpose(tmp)
		plt.clf()
		plt.figure(1)
		for s in striplist:
			par = self.cal._scurve_fit_gaussian1(curve = data[s-1], errmsg=' for strip %d'%s)
			A.append(par[0]);
			mu.append(par[1]);
			sigma.append(par[2]);
			x = range(1, np.size(data[s-1]))
			if(plot and par[2] < np.inf):
				plt.plot(data[s-1], 'og')
				plt.plot(x, f_gauss(x, par[0], par[1], par[2]), '-r')
		if( isinstance(filename, str) ):
			#f1 = "../SSA_Results/" + filename + "/Scurve_NoiseBaseline/" + filename + "_scurve_trim31__cal_0.csv"
			#fo = "../SSA_Results/" + filename + "_Baseline_scurve_trim31_cal0.csv"
			#CSV.ArrayToCSV (array = data, filename = fo, transpose = False)
			#fo = "../SSA_Results/" + filename + "_" + str(runname) + "_Baseline_Noise.csv"
			#CSV.ArrayToCSV (array = [[runname]*len(striplist), striplist, A, mu, sigma], filename = fo, transpose = False)
			fo = open("../SSA_Results/" + filename + "_Measure_Noise_Baseline.csv", filemode)
			fo.write( "\n%s ; Amplitude ;  %s" % (runname, '; '.join(map(str, A)) ))
			fo.write( "\n%s ; Mean      ;  %s" % (runname, '; '.join(map(str, mu)) ))
			fo.write( "\n%s ; Sigma     ;  %s" % (runname, '; '.join(map(str, sigma)) ))
		if(plot):
			plt.figure(2)
			plt.plot(striplist, sigma, 'go-')
			plt.show()

		sigma = np.array(sigma)
		if(ret_average):
			highnoise = np.where( sigma > 3)[0]
			sigma_filter = sigma[(np.where(sigma < 100)[0])]
			average_noise = np.mean(sigma_filter)
			return [average_noise, highnoise]
		else:
			return sigma



	def scurve_trim(self, filename = '../SSA_results/Chip0', calpulse = 50, plot = True, iterations = 5):
		print "->  \tS-Curve Trimming"
		if plot:
			data = self.scurves(mode = 'all', rdmode = 'fast', cal_list = [calpulse], trim_list = [0, 31], filename = filename, plot = False)
			scurve_0 = data[0]; scurve_31 = data[1];

		scurve_init, scurve_trim = self.cal.trimming_scurves(
			method = 'center',
			default_trimming = 15,
			cal_ampl = calpulse,
			iterations = iterations,
			plot = False)

		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "_scurve_" + "trim15" + "__cal_" + str(calpulse) + ".csv"
			CSV.ArrayToCSV (array = scurve_init, filename = fo, transpose = True)
			fo = "../SSA_Results/" + filename + "_scurve_" + "trim" + "__cal_" + str(calpulse) + ".csv"
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


	def threshold_spread(self, calpulse = 50, file = '../SSA_results/Chip0', runname = '', use_stored_data = False, plot = True, nevents=1000, speeduplevel = 2, filemode = 'w'):
		print "->  \tthreshold Spread Measurement"
		fi = "../SSA_Results/" + file + "_" + str(runname) + "_scurve_" + "trim" + "__cal_" + str(calpulse) + ".csv"
		print fi
		if(use_stored_data):
			if(os.path.exists(fi)):
				s = CSV.CsvToArray(fi)
				s = np.transpose(s)
			else:
				return -1
		else:
			s = self.scurves(
				cal_list = [calpulse],
				trim_list = 'keep',
				mode = 'all',
				rdmode = 'fast',
				filename = file,
				runname = runname,
				nevents = nevents,
				speeduplevel = speeduplevel,
				plot = False)[0]

		tmp, par = self.cal.evaluate_scurve_thresholds(scurve = s, nevents = nevents)
		thresholds = par[:,1]
		std = np.std(thresholds)
		fo = open("../SSA_Results/" + file + "_Measure_ThresholdSpread.csv", filemode)
		fo.write( "\n%s ; %7.2f ; %s" % (runname, std, '; '.join(map(str, thresholds)) ))
		if(plot):
			plt.clf()
			plt.hist(thresholds)
			plt.show()
		return std



	def gain_offset_noise(self, calpulse = 50, ret_average = True, plot = True, use_stored_data = False, file = 'TestLogs/Chip0', filemode = 'w', runname = '', nevents=1000, speeduplevel = 2):
		print "->  \tSCurve Gain, Offset and Noise Measurement"
		utils.activate_I2C_chip()
		callist = [calpulse-20, calpulse, calpulse+20]
		thresholds = []; sigmas = [];
		gain = []; offset = []; cnt = 0;
		noise = np.zeros(120)
		if(plot):
			plt.clf();
			plt.figure(1)

		for cal in callist:
			fi = "../SSA_Results/" + file + "_" + str(runname) + "_scurve_" + "trim" + "__cal_" + str(cal) + ".csv"
			if(use_stored_data and os.path.exists(fi)):
				s = CSV.CsvToArray(fi)
				s = np.transpose(s)
			else:
				s = self.scurves(
					cal_list = [cal],
					trim_list = 'keep',
					mode = 'all',
					rdmode = 'fast',
					filename = file,
					runname = runname,
					speeduplevel = speeduplevel,
					nevents = nevents,
					plot = False)[0]

			thlist, p = self.cal.evaluate_scurve_thresholds(scurve = s, nevents = nevents)
			thresholds.append( np.array(p)[:,1] ) #threshold per strip
			sigmas.append( np.array(p)[:,2] ) #threshold per strip

		if(plot): plt.figure(2)
		for i in range(0,120):
			ths = np.array(thresholds)[:,i]
			par, cov = curve_fit(f= f_line,  xdata = callist, ydata = ths, p0 = [0, 0])
			gain.append(par[0])
			offset.append(par[1])
			if(plot):
				plt.plot(callist, offset[i]+gain[i]*np.array(callist))
				plt.plot(callist, ths, 'o')
		gain=np.array(gain)
		offset=np.array(offset)
		for i in range(0,120):
			noise[i] = np.average(np.array(sigmas)[:,i])
		if(plot):
			plt.figure(3)
			plt.bar(range(0,120), noise)
			plt.show()

		fo = open("../SSA_Results/" + file + "_Measure_Noise_SCurve.csv", filemode)
		fo.write( "\n%s ; Noise S-Curve ; %s" % (runname, '; '.join(map(str, noise)) ))
		fo = open("../SSA_Results/" + file + "_Measure_Gain_SCurve.csv", filemode)
		fo.write( "\n%s ; Gain          ; %s" % (runname, '; '.join(map(str, gain)) ))
		fo = open("../SSA_Results/" + file + "_Measure_Offset_SCurve.csv", filemode)
		fo.write( "\n%s ; Offset        ; %s" % (runname, '; '.join(map(str, offset)) ))

		if(ret_average):
			highnoise = np.concatenate([np.where( noise < 0 )[0], np.where( noise > 3 )[0]])
			noise_filter = noise[  np.where( noise > 0 )[0]  ]
			average_noise = np.mean(noise_filter)
			gain_mean = np.mean(gain)
			offset_mean = np.mean(offset)
			return [gain_mean, offset_mean, average_noise, highnoise]
		else:
			return gain, offset, noise



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



	def dac_linearity(self, name = 'Bias_THDAC', nbits = 8, ideal_gain = 1.840, ideal_offset = 0.8, filename = False, plot = True, filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		if(self.bias == False): return False, False
		if(not (name in self.muxmap)): return False, False
		if(isinstance(filename, str)):
			fo = "../SSA_Results/" + filename
		nlin_params, nlin_data, fit_params, raw = self.bias.measure_dac_linearity(
			name = name,
			nbits = nbits,
			filename = fo,
			filename2 = "",
			plot = False,
			average = 10,
			runname = runname,
			filemode = filemode)
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
			#plt.plot(x, f_line(x, ideal_gain/1000, ideal_offset/1000), '-b', linewidth=5, alpha = 0.5)
			plt.plot(x, data, '-r', linewidth=5,  alpha = 0.5)
			plt.figure(2); plt.ylim(-1, 1); plt.bar( x, DNL, color='b', edgecolor = 'b', align='center')
			plt.figure(3); plt.ylim(-1, 1); plt.bar( x, INL, color='r', edgecolor = 'r', align='center')
			plt.figure(4); plt.ylim(-1, 1); plt.plot(x, INL, color='r')

			plt.show()

		#return DNL, INL, x, data
		return DNLMAX, INLMAX, g, ofs



	def delayline_resolution(self, debug = False):
		resolution = []
		resolution.append( "MAX: " + self.cal.delayline_resolution(set_bias = 31, shift = 3, display = debug, debug = False) )
		resolution.append( "TYP: " + self.cal.delayline_resolution(set_bias = 15, shift = 3, display = debug, debug = False) )
		#resolution.append( "MIN: " + self.cal.delayline_resolution(set_bias =  1, shift = 3, display = debug, debug = False) )
		return resolution



	def power_vs_occupancy(self, th = range(2,13), trim = False, plot = 1, print_file =1, filename = "pwr1", itr = 1000, rp= 1):
		self.ssa.inject.analog_pulse(initialise = True)
		if trim:
			cal.trimming_scurves(method = 'highest', iterations = 3)
		else:
			self.cal.set_trimming(default_trimming = 31, striprange = 'all', display=False)
		th = np.array(th)
		data = np.zeros((len(th)*rp, 3), dtype = float )
		self.I2C.strip_write("ENFLAGS", 0, 0b10001)
		nitr = 0
		for i in range(len(th)):
			for l in range(rp):
				cnt = np.zeros(itr, dtype = int)
				self.utils.activate_I2C_chip()
				self.ssa.ctrl.set_threshold(th[i])
				for m in range(itr):
					compose_fast_command(duration = 0, resync_en = 0, l1a_en = 0, cal_pulse_en = 1, bc0_en = 0)
					cl = self.ssa.readout.cluster_data(raw = False, apply_offset_correction = False, send_test_pulse = False, shift = 0, initialize = False, lookaround = False, getstatus = False, display_pattern = False, display = False)
					cnt[m] = len(cl)
				sleep(0.1)
				data[nitr, 0] = th[i]
				data[nitr, 1] = np.average(cnt)
				data[nitr, 2] = self.pwr.get_power_digital(display = False)
				print '->  \tth = %3d | pwr = %7.3f | ncl = %8.5f | itr = %3d' % (data[nitr, 0], data[nitr, 2], data[nitr, 1], nitr)
				nitr += 1
		self.ssa.ctrl.set_threshold(100)
		if print_file:
			CSV.ArrayToCSV (data, '../SSA_Results/'+filename+'_PowerVsOccupancy.csv')
		if plot:
			plt.clf()
			w, h = plt.figaspect(1/1.5)
			fig = plt.figure(figsize=(8,5.2))
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(False)
			ax.spines["right"].set_visible(False)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
			plt.xticks(range(0,9,1), fontsize=16)
			plt.yticks(fontsize=16)
			plt.ylabel("Digital power consuption [ mW ]", fontsize=16)
			plt.xlabel("Strip Occupancy [Hit/Bx]", fontsize=16)
			p = np.poly1d(np.polyfit(data[:,1], data[:,2], 3))
			t = np.linspace(0, 8, 1000)
			plt.plot(data[:,1], data[:,2], 'o', t, p(t), '-')
			plt.show()
		return data

	def power_vs_state(self, display = True):
		data = OrderedDict()
		self.ssa.disable(display=False)
		data['reset'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)
		self.ssa.enable(display=False)
		data['enable'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)
		self.ssa.ctrl.init_slvs(0b100)
		data['min-pad'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)
		self.ssa.ctrl.init_slvs(0b111)
		data['max-pad'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)
		self.ssa.ctrl.activate_readout_async(ssa_first_counter_delay = 0xffff, correction = 0)
		start_counters_read(1)
		data['async'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)
		self.bias.calibrate_to_nominals()
		data['calib'] = self.pwr.get_power(display = False)
		self._display_power_value(data.items()[-1], display)

		return data



	def _display_power_value(self, data, display):
		if(display):
			print "->  \t%8s : Digital = %7.3f, Analog = %7.3f, Pads = %7.3f" %(data[0], data[1][0], data[1][1], data[1][2])




'''
plt.axis([20, 100, 0, 1050])
plt.plot(s0,    'b', colour = #85C0DE)
plt.plot(s31,   'r', )
plt.plot(s, 	'y', )
plt.show()
'''
