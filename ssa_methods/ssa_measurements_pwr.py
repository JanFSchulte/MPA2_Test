from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from itertools import product as itertools_product
import seaborn as sns
import re
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate as scipy_interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
from collections import OrderedDict
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import re
import datetime


class SSA_measurements_pwr():

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal = False):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = fc7; self.utils = utils;
		self.cal = cal; self.bias = biascal; self.muxmap = analog_mux_map;
		self.pwr = pwr; self.seuutil = seuutil;
		self.__set_variables()

	###########################################################
	def power_vs_occupancy(self,
		maxclusters=8, l1rates=[0, 250, 500, 750, 1000],
		nsamples=5, filename = '../SSA_Results/power_vs_occupancy/', plot=False):

		self.fc7.SendCommand_CTRL("global_reset");    time.sleep(0.1);
		self.fc7.SendCommand_CTRL("fast_fast_reset"); time.sleep(0.1);
		self.fc7.write("fc7_daq_ctrl.fast_command_block", 0x10000)
		self.ssa.init(edge = 'negative', display = False)
		results = {}
		for lr in l1rates:
			res=np.zeros([33,3])
			if(lr != 0):  l1a_period = np.int( (40E3/lr)-1)
			else: l1a_period = 0xffff
			for nclusters in range(maxclusters+1):
				cl_hits, cl_centroids = self.generate_clusters(
					nclusters=nclusters,
					min_clsize=1, max_clsize=2, smin=1, smax=121)
				self.seuutil.Configure_Injection(
					strip_list = cl_hits, hipflag_list = [],
					analog_injection = 0, latency = 501)
				Configure_SEU(
					cal_pulse_period=1,
					l1a_period=l1a_period,
					number_of_cal_pulses=0,
					initial_reset = 1)
				self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
				self.fc7.SendCommand_CTRL("start_trigger")
				pret, vret, iret = self.pwr.get_power_digital_average(nsamples=nsamples)
				res[nclusters] = [pret, vret, iret]
				self.fc7.SendCommand_CTRL("stop_trigger")
				utils.print_log('L1 rate = {:6.1f}, Occupancy = {:d} cl  ->  Current = {:5.3f}'.format(lr, nclusters, iret))
			CSV.array_to_csv(array=res, filename = filename+'/power_vs_occupancy_l1rate_{:0.0f}MHz'.format(lr))
			results[lr] = res
		self.fc7.SendCommand_CTRL("global_reset");time.sleep(0.1);
		if(plot):
			self.power_vs_occupancy_plot(maxclusters=8, l1rates=l1rates, filename=filename,)
		return results

	###########################################################
	def power_vs_occupancy_plot(self,
		maxclusters=8, l1rates=[250, 500, 750, 1000], save=1, show=1,
		filename='../SSA_Results/power_vs_occupancy', fit=12, label=''):
		results = {}
		color=iter(sns.color_palette('deep'))
		if(save or show):
			plt.clf()
			fig = plt.figure(figsize=(18,12))
		for lr in l1rates:
			res = CSV.csv_to_array(filename = (filename+'/power_vs_occupancy_l1rate_{:0.0f}MHz'.format(lr)) )
			results[lr] = res
			current = res[:,3]
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(True)
			ax.spines["right"].set_visible(True)
			x = list(range(maxclusters+1))
			y = current[0:maxclusters+1]
			#plt.ylim(15, 25)
			if(fit>0):
				xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
				c = next(color);
				#y_smuth = scipy_interpolate.BSpline(x, np.array([y, xnew]))
				helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y) )
				y_smuth = helper_y3(xnew)
				y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 1001, polyorder = fit)
				plt.plot(xnew, y_smuth , color=c, lw=1, alpha = 0.5)
				#plt.plot(xnew, y_hat   , color=c, lw=1, alpha = 0.8)
				plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o', label=label + "(L1 rate = {:4d} kHz)".format(lr), color=c)
				#p = np.poly1d(np.polyfit(list(range(maxclusters+1)), current[0:maxclusters+1], fit))
				#t = np.linspace(0, 8, 1000)
				#plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o', t, p(t), '-')
			else:
				plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o')
		leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel("Digital power consuption [ mA ]", fontsize=16)
		plt.xlabel("Strip Occupancy [Hit/Bx]", fontsize=16)
		plt.xticks(range(0,maxclusters+1,1), fontsize=12)
		plt.yticks(np.arange(19,24.5,0.5), fontsize=12)
		if(save): plt.savefig(filename+'/power_vs_occupancy.png', bbox_inches="tight");
		if(show): plt.show()
		return res

	###########################################################
	def power_vs_occupancy_plot_sram_latch(self,
		l1rates=[250, 500, 750, 1000], maxclusters = 8, fit=12,
		file_sram  ='../SSA_Results/power_vs_occupancy/sram/',
		file_latch ='../SSA_Results/power_vs_occupancy/latch/',
		file_out   ='../SSA_Results/power_vs_occupancy/' ):

		plt.clf()
		fig = plt.figure(figsize=(18,12))
		self.power_vs_occupancy_plot(label='SRAM ', maxclusters=maxclusters, l1rates=l1rates, save=0, show=0, filename=file_sram,  fit=fit)
		self.power_vs_occupancy_plot(label='Latch ', maxclusters=maxclusters, l1rates=l1rates, save=0, show=0, filename=file_latch, fit=fit)
		#plt.savefig(file_out+'/power_vs_occupancy_sram_latch.png', bbox_inches="tight");
		plt.show()

#		self.ssa.ctrl.set_threshold(100)
#		if print_file:
#			CSV.ArrayToCSV (data, '../SSA_Results/'+filename+'_PowerVsOccupancy.csv')
#		if plot:
#			plt.clf()
#			w, h = plt.figaspect(1/1.5)
#			fig = plt.figure(figsize=(8,5.2))
#			ax = plt.subplot(111)
#			ax.spines["top"].set_visible(False)
#			ax.spines["right"].set_visible(False)
#			ax.get_xaxis().tick_bottom()
#			ax.get_yaxis().tick_left()
#			plt.xticks(range(0,9,1), fontsize=16)
#			plt.yticks(fontsize=16)
#			plt.ylabel("Digital power consuption [ mW ]", fontsize=16)
#			plt.xlabel("Strip Occupancy [Hit/Bx]", fontsize=16)
#			p = np.poly1d(np.polyfit(data[:,1], data[:,2], 3))
#			t = np.linspace(0, 8, 1000)
#			plt.plot(data[:,1], data[:,2], 'o', t, p(t), '-')
#			plt.show()
#		return data

	###########################################################
	def power_vs_occupancy_old(self, th = range(2,13), trim = False, plot = 1, print_file =1, filename = "pwr1", itr = 1000, rp= 1):
		self.ssa.inject.analog_pulse(initialise = True)
		if trim:
			cal.trimming_scurves(method = 'highest', iterations = 3)
		else:
			self.cal.set_trimming(default_trimming = 31, striprange = 'all', display=False)
		th = np.array(th)
		data = np.zeros((len(th)*rp, 3), dtype = float )
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b10001)
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b10001)
		nitr = 0
		for i in range(len(th)):
			for l in range(rp):
				cnt = np.zeros(itr, dtype = int)
				self.utils.activate_I2C_chip(self.fc7)
				self.ssa.ctrl.set_threshold(th[i])
				for m in range(itr):
					compose_fast_command(duration = 0, resync_en = 0, l1a_en = 0, cal_pulse_en = 1, bc0_en = 0)
					cl = self.ssa.readout.cluster_data(raw = False, apply_offset_correction = False, send_test_pulse = False, shift = 0, initialize = False, lookaround = False, getstatus = False, display_pattern = False, display = False)
					cnt[m] = len(cl)
				time.sleep(0.1)
				data[nitr, 0] = th[i]
				data[nitr, 1] = np.average(cnt)
				data[nitr, 2] = self.pwr.get_power_digital(display = False)
				utils.print_log('->  th = %3d | pwr = %7.3f | ncl = %8.5f | itr = %3d' % (data[nitr, 0], data[nitr, 2], data[nitr, 1], nitr))
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

	###########################################################
	def power_vs_state(self, display = True, ):
		data = OrderedDict()
		self.ssa.disable(display=False)
		data['reset'] = self.pwr.get_power(display = False)
		self.ssa.enable(display=False)
		data['enable'] = self.pwr.get_power(display = False)
		self.ssa.ctrl.init_slvs(0b100)
		data['min-pad'] = self.pwr.get_power(display = False)
		self.ssa.ctrl.init_slvs(0b111)
		data['max-pad'] = self.pwr.get_power(display = False)
		self.ssa.ctrl.activate_readout_async(ssa_first_counter_delay = 0xffff, correction = 0)
		self.fc7.start_counters_read(1)
		data['async'] = self.pwr.get_power(display = False)
		self.bias.calibrate_to_nominals()
		data['calib'] = self.pwr.get_power(display = False)
		self._display_power_value(data, 'reset',   display)
		self._display_power_value(data, 'enable',  display)
		self._display_power_value(data, 'min-pad', display)
		self._display_power_value(data, 'max-pad', display)
		self._display_power_value(data, 'async',   display)
		self._display_power_value(data, 'calib',   display)
		return data

	###########################################################
	def _display_power_value(self, data, field, display):
		if(display):
			utils.print_log("->  {:8s} : Digital = {:7.3f}, Analog = {:7.3f}, Pads = {:7.3f}".format( field, data[field][0], data[field][1], data[field][2]))

	###########################################################
	def __set_variables(self):
		self.dll_resolution = 1.3157894736842106;
		self.thdac_gain = 2.01 # mv/cnt
		self.caldac_q = 0.04305 #fC/cnts

	###########################################################
	def generate_clusters(self, nclusters, min_clsize = 1, max_clsize = 4, smin=-2, smax=124):
		hit = []; c = []; exc = [];
		for i in range(nclusters):
			size = random.sample(range(min_clsize, max_clsize), 1)[0]
			rangelist = list( set(range(smin, smax-size)) - set(exc) )
			adr = random.sample(rangelist, 1)[0]
			cll = range(adr, adr+size)
			hit += cll
			c.append( np.mean(cll) )
			exc += range(min(cll)-max_clsize-1, max(cll)+2)
		hit.sort()
		c.sort()
		return hit, c

	###########################################################
	def my_hist_plot(self, ser, xlabel, ylabel, mean_label=False, save=False):
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel(xlabel, fontsize=32)
		plt.xlabel(ylabel, fontsize=32)
		bn = np.arange(min(ser)*0.95, max(ser)*1.15, ((max(ser)-min(ser))/50.0) )
		plt.hist(ser,  density=True, bins = bn, alpha = 0.7)
		xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
		xmin, xmax = min(xt), max(xt)
		lnspc = np.linspace(xmin, xmax, len(ser))
		m, s = stats.norm.fit(ser) # get mean and standard deviation
		pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
		plt.plot(lnspc, pdf_g, 'r' , label="Norm") # plot i
		sermean = np.mean(ser)
		if(mean_label):
			plt.text(0.95,0.95, mean_label + '= {:6.2f}'.format(sermean), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=32, color='darkred')
		if(save):
			plt.savefig(save+'.png', bbox_inches="tight")
			utils.print_log('->  Plot saved in ' + save +'.png')
		#fpl = self.path + 'ANALYSIS/S-Curve_Gain_hist'+self.pltname+'.png'
		#plt.savefig(fpl, bbox_inches="tight");
		#print("->  Plot saved in %s" % (fpl))

	###########################################################
	def my_linear_plot(self, x, y, xlabel, ylabel, fit=True, mean_label=False, save=False):
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel(xlabel, fontsize=32)
		plt.xlabel(ylabel, fontsize=32)
		xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
		xmin, xmax = min(xt), max(xt)
		if(fit>0):
			xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
			c = next(color);
			#y_smuth = scipy_interpolate.BSpline(x, np.array([y, xnew]))
			helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y) )
			y_smuth = helper_y3(xnew)
			y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 1001, polyorder = fit)
			plt.plot(xnew, y_smuth , color=c, lw=1, alpha = 0.5)
			#plt.plot(xnew, y_hat   , color=c, lw=1, alpha = 0.8)
			plt.plot(x, y, 'o', label=label + "(L1 rate = {:4d} kHz)".format(lr), color=c)
			#p = np.poly1d(np.polyfit(list(range(maxclusters+1)), current[0:maxclusters+1], fit))
			#t = np.linspace(0, 8, 1000)
			#plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o', t, p(t), '-')
		else:
			plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o')
		leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel(xlabel, fontsize=16)
		if(save):
			plt.savefig(save+'.png', bbox_inches="tight")
			print('->  Plot saved in ' + save +'.png')
