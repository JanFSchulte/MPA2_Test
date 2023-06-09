from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
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


class SSA_measurements_fe():

	def __init__(self, ssa, I2C, fc7, cal, analog_mux_map, pwr, seuutil, biascal = False):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = fc7; self.utils = utils;
		self.cal = cal; self.bias = biascal; self.muxmap = analog_mux_map;
		self.pwr = pwr; self.seuutil = seuutil;
		self.__set_variables()

	###########################################################
	def scurve_trim_gain_noise(self,
		charge_fc_trim = 3.0,
		charge_fc_test = 1.0,
		threshold_mv_trim = 'mean',
		iterative_step_trim = 1,
		caldac = 'default',
		thrdac = 'default',
		nevents = 1000,
		plot = False,
		filename = '../SSA_Results/TestLogs/Chip_0_',
		display = False
		):
		"""Generate scurve data.

		Parameters
		----------
		charge_fc_trim : float, optional
			Input charge in fC, by default 2.0
		charge_fc_test : float, optional
			Input charge in fC, by default 1.0
		threshold_mv_trim : str, optional
			Threshold in mV, by default 'mean'
		iterative_step_trim : int, optional
			Iterative steps to acheive lower variability, by default 1
		caldac : str, optional
			'default' | 'evaluate' | value [gain, offset], by default 'default'
		thrdac : str, optional
			'default' | 'evaluate' | value [gain, offset], by default 'default'
		nevents : int, optional
			Number of calibration pulses, by default 1000
		plot : bool, optional
			Fast plot of the results, by default False
		filename : str, optional
			by default '../SSA_Results/TestLogs/Chip_0_'
		display : bool, optional
			by default False

		Returns
		-------
		[type]
			[description]
		"""

		charge_fc_trim= np.float(charge_fc_trim)
		charge_fc_test= np.float(charge_fc_test)
		scurves = {}; fo = [];
		thstd, sc = self.scurve_trim(
			charge_fc = charge_fc_trim,
			threshold_mv = threshold_mv_trim,
			caldac = caldac,
			thrdac = thrdac,
			nevents = nevents,
			iterative_step = iterative_step_trim,
			plot = plot,
			filename = filename,
			return_scurves = True)
		scurves['h_0']  = sc[0];
		scurves['h_31'] = sc[1];
		scurves['h_trim'] = sc[-1];
		if(caldac=='evaluate'):  t_caldac = self.measure.dac_linearity(name='Bias_CALDAC', eval_inl_dnl=False, nbits=8, npoints=10, plot=False, runname='')
		elif(caldac=='default'): t_caldac = self.cal.caldac
		elif(isinstance(caldac, list)): t_caldac = caldac
		else: return False
		if(thrdac=='evaluate'):  t_thrdac = self.measure.dac_linearity(name='Bias_THDAC', eval_inl_dnl=False, nbits=8, npoints=10, plot=False, runname='')
		elif(thrdac=='default'): t_thrdac = self.cal.thrdac
		elif(isinstance(thrdac, list)): t_thrdac = thrdac
		else: return False
		cal_ampl = self.cal.evaluate_caldac_ampl(charge_fc_test, t_caldac)
		scurves['l_trim'] = self.cal.scurves(
			cal_ampl = cal_ampl, nevents = nevents,
			display = display, plot = False, speeduplevel = 2, countershift = 'auto',
			filename = False, mode = 'all', rdmode = 'fast')
		fo.append(filename + "frontend_Q_{c:1.3f}_scurve_trim-done.csv".format(c=charge_fc_trim))
		fo.append(filename + "frontend_Q_{c:1.3f}_scurve_trim-done.csv".format(c=charge_fc_test))
		CSV.ArrayToCSV (array = scurves['l_trim'], filename = fo[1], transpose = True)
		utils.print_log("->  Scurve data saved in {:s}".format(fo[1]))
		rp = self.FE_Gain_Noise_Std__Calculate(
			input_files = fo,
			output_file = (filename),
			nevents=nevents,
			thdac_gain = np.abs(t_thrdac[0]),
			plot = plot )
		calpulses, thresholds, noise, thmean, sigmamean, gains, gains_mVfC, offsets = rp
		threshold_std_init  = np.std(thstd[0])
		threshold_std_trim  = np.std(thresholds[str(charge_fc_trim)])
		threshold_std_test  = np.std(thresholds[str(charge_fc_test)])
		threshold_mean_trim = np.mean(thresholds[str(charge_fc_trim)])
		threshold_mean_test = np.mean(thresholds[str(charge_fc_test)])
		noise_mean_trim     = np.mean(noise[str(charge_fc_trim)])
		noise_mean_test     = np.mean(noise[str(charge_fc_test)])
		fe_gain_mean        = np.mean(gains)
		fe_gain_mVfC_mean   = np.mean(gains_mVfC)
		fe_offs_mean        = np.mean(offsets)

		return threshold_std_init, threshold_std_trim, threshold_std_test, threshold_mean_trim, threshold_mean_test, noise_mean_trim, noise_mean_test, fe_gain_mean, fe_gain_mVfC_mean, fe_offs_mean

	###########################################################
	def scurves(self, cal_list = [50], trim_list = 'keep', mode = 'all', rdmode = 'fast', filename = False, runname = '', plot = True, nevents = 1000, speeduplevel = 2, countershift = 0, d19c_firmware_issue_repeat=0):
		data = self.scurves_measure(cal_list = cal_list, trim_list = trim_list, mode = mode, rdmode = rdmode, filename = filename, runname = runname, plot = plot, nevents = nevents, speeduplevel = speeduplevel, countershift = countershift, d19c_firmware_issue_repeat=d19c_firmware_issue_repeat)
		if(plot):
			self.scurves_plot(data)
		return data

	def scurves_measure(self, cal_list = [50], trim_list = 'keep', mode = 'all', rdmode = 'fast', filename = False, runname = '', plot = True, nevents = 1000, speeduplevel = 2, countershift = 0, d19c_firmware_issue_repeat=0):
		plt.clf()
		data = []
		if(isinstance(filename, str)):
			fo = "../SSA_Results/" + filename + "_" + str(runname)
		else:
			fo = False
		for cal in cal_list:
			if(trim_list == 'keep'):
				d = self.cal.scurves(cal_ampl = cal, nevents = nevents,filename = fo, mode = mode, rdmode = rdmode,filename2 = 'trim',countershift = countershift, speeduplevel = speeduplevel,plot = False, msg = "CAL = " + str(cal), d19c_firmware_issue_repeat=d19c_firmware_issue_repeat)
				data.append(d)
			else:
				for trim in trim_list:
					t = self.cal.set_trimming(trim, 'all', False)
					d = self.cal.scurves(cal_ampl = cal, nevents = nevents,filename = fo, mode = mode, rdmode = rdmode,filename2 = 'trim'+str(trim), countershift = countershift, speeduplevel = speeduplevel,plot = False, msg = "[CAL=" + str(cal) +"][TRIM="+str(trim)+']', d19c_firmware_issue_repeat=d19c_firmware_issue_repeat)
					data.append(d)
		return data

	###########################################################
	def scurves_plot(self, data):
		plt.clf()
		fig = plt.figure(figsize=(15,5))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Counter value", fontsize=16)
		plt.xlabel('Threshold', fontsize=16)
		color=iter(sns.color_palette('husl'))
		plt.ylim(0, 2000)
		plt.xlim(10, 200)
		for d in data:
			c = next(color)
			plt.plot(d, '-', color=c, lw=1, alpha = 1)
		plt.show()

	###########################################################
	def FE_Gain_Noise_Std__Calculate(self, input_files, output_file, nevents=1000, thdac_gain = 'default', plot = False):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {}; tmp = [];
		calpulses = []; scurve_table = {}; runlist = {}
		files_list = input_files
		if(thdac_gain == 'default'):
			t_thrdac = self.cal.thrdac
		elif(isinstance(thdac_gain, float) or isinstance(thdac_gain, int)):
			t_thrdac = thdac_gain
		else: return False
		if(len(files_list) == 0): return ['er']*7
		utils.print_log('->  Sorting Informations')
		if plot:
			plt.figure()
			color=iter(sns.color_palette('deep'))
		for f in files_list:
			cfl = re.findall( '\W?Q_(\d+\.\d+)' , f )
			cal = np.float( cfl[0] )
			if not cal in calpulses:
				calpulses.append(cal)
				scurve = CSV.csv_to_array( f )
				scurve_table[str(cal)] = scurve
		calpulses.sort()
		utils.print_log('->  Loading S-Curves data completed')
		CSV.array_to_csv( calpulses,  output_file+'frontend_cal_values.csv')
		utils.print_log('->  Fitting courves for Threshold-Spread and Noise')
		for cal in calpulses:
			c_thresholds = []; c_noise = [];
			c_thmean = []; c_sigmamean = [];
			s = np.transpose(scurve_table[str(cal)])
			thround, p = self.cal.evaluate_scurve_thresholds(scurve = s, nevents = nevents)
			c_thresholds.append( np.array(p)[:,1] ) #threshold per strip not rounded
			c_thmean.append( np.mean( np.array(p)[:,1] ) ) #threshold mean
			c_noise.append( np.array(p)[:,2] ) #noise per strip
			c_sigmamean.append( np.mean( np.array(p)[:,2] ) ) #noise mean
			thresholds[str(cal)] = np.array(c_thresholds, dtype = float)
			noise[str(cal)] = np.array(c_noise, dtype = float)
			thmean[str(cal)] = np.array(c_thmean, dtype = float)
			sigmamean[str(cal)] = np.array(c_sigmamean, dtype = float)
			CSV.array_to_csv(c_thresholds, (output_file + 'frontend_Q-{:1.3f}_thresholds.csv'.format(cal)))
			CSV.array_to_csv(c_noise,      (output_file + 'frontend_Q-{:1.3f}_noise.csv'.format(cal)))
			CSV.array_to_csv(c_thmean,     (output_file + 'frontend_Q-{:1.3f}_threshold-mean.csv'.format(cal)))
			CSV.array_to_csv(c_sigmamean,  (output_file + 'frontend_Q-{:1.3f}_noise-mean.csv'.format(cal)))
			if(plot):
				c = next(color)
				plt.plot(s, '-', color=c, lw=1, alpha = 1)
		self.thresholds = thresholds
		utils.print_log('->  Evaluating Front-End Gain')
		gains = np.zeros([120]);
		gains_mV_fC = np.zeros([120]);
		offsets = np.zeros([120]);
		for strip in range(0,120):
			ths = np.array( [thresholds[k][0][strip] for k in list(map(str, calpulses)) if k in thresholds] )
			self.ths = ths
			self.calpulses = calpulses
			if(len(calpulses)==2):
				gains[strip]   = np.float(ths[1]-ths[0])/np.float(calpulses[1]-calpulses[0])
				offsets[strip] = np.float(ths[1])-gains[strip]*np.float(calpulses[1])
			else:
				par, cov = curve_fit( f= f_line,  xdata = calpulses, ydata = ths, p0 = [0, 0])
				gains[strip] = par[0]
				offsets[strip] = par[1]
			gains_mV_fC[strip] = np.abs(t_thrdac)*gains[strip]
		gainmean = np.average(gains)
		CSV.array_to_csv(gains,       output_file + 'frontend_gain.csv')
		CSV.array_to_csv(gains_mV_fC, output_file + 'frontend_gain_mVfC.csv')
		CSV.array_to_csv([gainmean],  output_file + 'frontend_gain-mean.csv')
		CSV.array_to_csv(offsets,     output_file + 'frontend_offset.csv')
		plt.savefig((output_file + 'frontend_Q-{:1.3f}_scurves.png'.format(cal)), bbox_inches="tight")
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gains_mV_fC, offsets

	####################################################################################
	def FE_Gain_Noise_Std__plot(self, filename='../SSA_Results/TestLogs/Chip_0_'):
		x = range(0,120,1)
		calpulses   = CSV.csv_to_array( filename + 'frontend_cal_values.csv')[:,1]
		gains       = CSV.csv_to_array( filename + 'frontend_gain.csv')[:,1]
		gains_mV_fC = CSV.csv_to_array( filename + 'frontend_gain_mVfC.csv')[:,1]
		gainmean    = CSV.csv_to_array( filename + 'frontend_gain-mean.csv')[:,1]
		offsets     = CSV.csv_to_array( filename + 'frontend_offset.csv')[:,1]

		fig = plt.figure(figsize=(18,12))
		self.my_hist_plot( gains_mV_fC, "Normalised distribution", 'Front-End Gain [mv/fC]', r"""$\overline{G_{FE}} $""", filename+'fe_gain')

		fig = plt.figure(figsize=(18,12))
		self.my_hist_plot( offsets, "Normalised distribution", 'Offset [mV]', r"""$\overline{Ofs_{FE}} $""", filename+'fe_offset')

		c_thresholds = {}; c_noise = {}; c_thmean = {}; c_sigmamean = {};
		for cal in calpulses:
			c_thresholds[cal] = CSV.csv_to_array( (filename + 'frontend_Q-{:1.3f}_thresholds.csv'.format(cal)))[0][1:]
			c_noise[cal]      = CSV.csv_to_array( (filename + 'frontend_Q-{:1.3f}_noise.csv'.format(cal)))[0][1:]
			c_thmean[cal]     = CSV.csv_to_array( (filename + 'frontend_Q-{:1.3f}_threshold-mean.csv'.format(cal)))[:,1]
			c_sigmamean[cal]  = CSV.csv_to_array( (filename + 'frontend_Q-{:1.3f}_noise-mean.csv'.format(cal)))[:,1]

		fig = plt.figure(figsize=(18,12))
		for cal in calpulses:
			c_noise[cal]      = CSV.csv_to_array( (filename + 'frontend_Q-{:1.3f}_noise.csv'.format(cal)))[0][1:]
			self.my_hist_plot( c_noise[cal], "Normalised distribution", 'Noise', False,  filename+'fe_noise')

	####################################################################################
	def baseline_noise(self, striplist = range(1,121), mode = 'sbs', ret_average = True, filename = False, runname= '', plot = True, filemode = 'w', set_trim = False):
		utils.print_log("->  Baseline Noise Measurement")
		data = np.zeros([120, 256])
		A = []; sigma = []; mu = []; cnt = 0;
		if(mode == 'sbs'):
			for s in striplist:
				tmp = self.cal.scurves(cal_ampl='baseline', filename = False, rdmode = 'i2c', mode = 'sbs', striplist = [s], plot = False, speeduplevel = 2)
				data[s-1] = tmp[:,s-1];	cnt += 1;
			if isinstance(filename, str):
				fo = "../SSA_Results/" + filename + "_" + str(runname) + "_scurve_SbS__cal_" + str(0) + ".csv"
				CSV.ArrayToCSV (array = data, filename = fo, transpose = False)
				utils.print_log("->  Data saved in" + fo)
		elif(mode == 'all'):
			tmp = self.cal.scurves(cal_ampl='baseline', filename = "../SSA_Results/" + filename + "_" + str(runname), rdmode = 'fast', mode = 'all', striplist = striplist, plot = False, speeduplevel = 2, set_trim = set_trim)
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
			#maxnoise = np.max( np.where( data[striplist]>0 ) )
			return [average_noise, highnoise]
		else:
			return sigma


	###########################################################
	def scurve_trim(self,
		charge_fc = 2,             # Input charge in fC
		threshold_mv = 'default',  # Threshold in mV
		caldac = 'default',        # 'default' | 'evaluate' | value [gain, offset]
		thrdac = 'default',        # 'default' | 'evaluate' | value [gain, offset]
		nevents = 1000,            # Number of calibration pulses
		iterative_step = 3,        # Iterative steps to acheive lower variability
		plot = True,               # Fast plot of the results
		filename = '../SSA_Results/TestLogs/Chip_0_',
		return_scurves = False
		):
		std = self.cal.trimming_scurves_2(
			charge_fc = charge_fc, threshold_mv = threshold_mv,	caldac = caldac,
			thrdac = thrdac, nevents = nevents,	iterative_step = iterative_step,
			filename = filename, return_scurves=return_scurves)
		if(plot and isinstance(filename, str)):
			self.scurve_trim_plot(filename = filename, charge = charge_fc)
		return std

	def scurve_trim_plot(self, filename = '../SSA_Results/TestLogs/Chip_0_', charge = 2.0):
		scurves = {}
		fi = (filename + "frontend_Q_{c:1.3f}_scurve_trim-{t:0d}_.csv".format(c=charge, t=0))
		scurves['0'] = np.transpose( CSV.csv_to_array(filename = fi) )
		fi = (filename + "frontend_Q_{c:1.3f}_scurve_trim-{t:0d}_.csv".format(c=charge, t=31))
		scurves['31'] = np.transpose( CSV.csv_to_array(filename = fi) )
		fi = (filename + "frontend_Q_{c:1.3f}_scurve_trim-done.csv".format(c=charge))
		scurves['trim'] = np.transpose( CSV.csv_to_array(filename = fi) )
		c_thresholds = {}; cmin = np.inf; cmax = 0;
		for i in scurves:
			thround, p = self.cal.evaluate_scurve_thresholds(scurve = scurves[i], nevents = 1000)
			c_thresholds[i] = np.array(p)[:,1]  #threshold per strip
			cmin = np.min([np.min(c_thresholds[i]), cmin])
			cmax = np.max([np.max(c_thresholds[i]), cmax])
		bn = np.round(np.arange(cmin-7, cmax+5, 1)).astype(int)
		bn = np.arange(cmin-7, cmax+5, 1)
		gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
		fig = plt.figure(figsize=(12,8))
		plt.style.use('seaborn-deep')
		color=iter(sns.color_palette('deep')) #iter(cm.summer(np.linspace(0,1, len(scurves) )))
		ax0 = plt.subplot(gs[1])
		ax0.get_xaxis().tick_bottom(); ax0.get_yaxis().tick_left()
		plt.xticks(fontsize=16); plt.yticks(fontsize=16)
		plt.xlim(min(bn)-10, max(bn)+10);
		plt.ylim(0, 1100)
		for i in scurves:
			c=next(color)
			plt.plot( scurves[i] , color = c)
		ax1 = plt.subplot(gs[0])
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.setp(ax1.get_xticklabels(), visible=False)
		plt.xlim(min(bn)-10, max(bn)+10);
		plt.ylim(0, 1.1)
		ax1.spines["top"].set_visible(True)
		ax1.spines["right"].set_visible(True)
		ax1.get_xaxis().tick_bottom(); ax1.get_yaxis().tick_left()
		labels = ["Optimal trimming values", "Not trimmed: THDAC = MIN", "Not trimmed: THDAC = MAX"]
		cnt = 0
		stds = []
		plot_scale = 1.2
		color=iter(sns.color_palette('deep'))
		for i in scurves:
			c=next(color)
			plt.hist(c_thresholds[i], density = True, bins = bn, alpha = 0.7, color = c, label = (labels[cnt]))
			xt = plt.xticks()[0]
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(c_thresholds[i]))
			m, s = stats.norm.fit(c_thresholds[i]) # get mean and standard deviation
			stds.append(s)
			pdf_g = stats.norm.pdf(lnspc, m, s*plot_scale) # now get theoretical values in our interval
			xnew = np.linspace(np.min(lnspc), np.max(lnspc), 1000, endpoint=True)
			#pdf_l = scipy_interpolate.BSpline(lnspc, pdf_g, xnew)
			helper_y3 = scipy_interpolate.make_interp_spline(lnspc, pdf_g)
			pdf_l = helper_y3(xnew)
			print(m)
			print('----------')
			print(s)
			print('==========')
			plt.plot(xnew, pdf_l, c = 'darkred', lw = 2) # plot i
			cnt += 1
		leg = ax1.legend(fontsize = 16, )
		leg.get_frame().set_linewidth(0.0)
		plt.savefig(filename+"frontend_Q_{c:1.3f}_scurve_trim.png".format(c=charge), bbox_inches="tight")
		#plt.show()


#fpl = self.path + 'ANALYSIS/S-Curve_Threshold_Trimming'+self.pltname+'.png'
#plt.savefig(fpl, bbox_inches="tight");
#print("->  Plot saved in %s" % (fpl))
#plt.show()
#return stds

	def scurve_trim_old(self, filename = 'TestLogs/', calpulse = 50, method = 'center', iterations = 5, countershift = 0, compute_min_max = True, plot = True):
		print("->  S-Curve Trimming")
		if(compute_min_max):
			data = self.scurves(mode = 'all', rdmode = 'fast', cal_list = [calpulse], trim_list = [0, 31], filename = filename, plot = False, countershift = countershift)
			scurve_0 = data[0]; scurve_31 = data[1];
		scurve_init, scurve_trim = self.cal.trimming_scurves(
			method = method,
			default_trimming = 15,
			cal_ampl = calpulse,
			iterations = iterations,
			plot = False,
			countershift = countershift,
			filename = filename)
		if( isinstance(filename, str) ):
			fo = "../SSA_Results/" + filename + "_scurve_" + "trim15" + "__cal_" + str(calpulse) + ".csv"
			CSV.ArrayToCSV (array = scurve_init, filename = fo, transpose = True)
			fo = "../SSA_Results/" + filename + "_scurve_" + "trim" + "__cal_" + str(calpulse) + ".csv"
			CSV.ArrayToCSV (array = scurve_trim, filename = fo, transpose = True)
			if(compute_min_max):
				fo = "../SSA_Results/" + filename + "_scurve_" + "trim0" + "__cal_" + str(calpulse) + ".csv"
				CSV.ArrayToCSV (array = scurve_0, filename = fo, transpose = True)
				fo = "../SSA_Results/" + filename + "_scurve_" + "trim31" + "__cal_" + str(calpulse) + ".csv"
				CSV.ArrayToCSV (array = scurve_31, filename = fo, transpose = True)
		if plot:
			self.scurve_trim_plot(filename = filename, calpulse = calpulse)
		return scurve_trim, scurve_init

	###########################################################
	def threshold_spread(self, calpulse = 50, file = '../SSA_results/TestLogs/', runname = '', use_stored_data = False, plot = True, nevents=1000, speeduplevel = 2, filemode = 'w'):
		utils.print_log( "->  threshold Spread Measurement")
		fi = "../SSA_Results/" + file + "_" + str(runname) + "_scurve_" + "trim" + "__cal_" + str(calpulse) + ".csv"
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


	###########################################################
	def gain_offset_noise(self, calpulse = 50, ret_average = True, plot = True, use_stored_data = False, file = 'TestLogs/TestLogs', filemode = 'w', runname = '', nevents=1000, speeduplevel = 2):
		utils.print_log("->  SCurve Gain, Offset and Noise Measurement")
		utils.activate_I2C_chip(self.fc7)
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
		with open("../SSA_Results/" + file + "_Measure_Noise_SCurve.csv", filemode) as fo:
			fo.write( "\n%s ; Noise S-Curve ; %s" % (runname, '; '.join(map(str, noise)) ))
		with open("../SSA_Results/" + file + "_Measure_Gain_SCurve.csv", filemode) as fo:
			fo.write( "\n%s ; Gain          ; %s" % (runname, '; '.join(map(str, gain)) ))
		with open("../SSA_Results/" + file + "_Measure_Offset_SCurve.csv", filemode) as fo:
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

	###########################################################
	def shaper_pulse_measure(self, charge=[30, 40, 50, 60], filename = False, strip=30, naverages=100, dll_resolution = 'default', runname = '', plot = True):
		if(dll_resolution == 'evaluate'):
			timeresolution = self.self.cal.delayline_resolution(naverages = 100)
		elif(isinstance(dll_resolution, float)):
			timeresolution = dll_resolution
		else:
			timeresolution = self.dll_resolution
		plt.clf()
		tm = np.arange(0, 128)*timeresolution
		tm = tm[tm <= 75]
		if(not isinstance(charge, list)):
			charge = [charge]
		pmean = []; pstd = [];
		for ch in charge:
			tmp1, tmp2, raw = self.cal.shaperpulse(
				charge = ch, naverages = naverages, plot = False, raw = True,
				strip = strip, display = False, hitloc0 = 24, thmin = 15)
			pmean.append(tmp1)
			pstd.append(tmp2)
		if(not isinstance(filename, str)):
			filename = "temp/ShaperPulseTmp"
		fo = "../SSA_Results/" + filename + "_" + str(runname) + "_ShaperPulse"
		data1 = []; data2 = [];
		data1.append(tm);
		data2.append(tm);
		for p in pmean: data1.append(p[range(np.size(tm))])
		for p in pstd:  data2.append(p[range(np.size(tm))])
		CSV.ArrayToCSV (array = data1, filename = (fo+'_mean.csv'), transpose = False)
		CSV.ArrayToCSV (array = data2, filename = (fo+'_std.csv'), transpose = False)
		CSV.ArrayToCSV (array = raw,   filename = (fo+'_raw.csv'), transpose = False)
		CSV.ArrayToCSV (array = np.array([timeresolution]),  filename = (fo+'_dllres.csv'), transpose = False)
		utils.print_log("->  Data saved in" + fo)
		if(plot):
			self.shaper_pulse_plot(filename = filename, runname = runname)
		#return pmean, tm, charge

	def shaper_pulse_plot(self, filename = False, runname = '', rawdata = False, invert = True, interpolate = True):  #filename = 'Chip-B6/Shaper/Chip-B6_Cal_all'
		if(not isinstance(filename, str)):
			filename = "temp/ShaperPulseTmp"
		fig = plt.figure(figsize=(8,9))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Threshold Voltage [mV]", fontsize=16)
		plt.xlabel('Time [ns]', fontsize=16)
		color=iter(sns.color_palette('deep'))
		fo = "../SSA_Results/" + filename + "_" + str(runname) + "_ShaperPulse"
		dmean = CSV.CsvToArray(filename = (fo+'_mean.csv'))[:,1:]
		dstd  = CSV.CsvToArray(filename = (fo+'_std.csv'))[:,1:]
		raw   = CSV.CsvToArray(filename = (fo+'_raw.csv'))[:,1:]
		res   = CSV.CsvToArray(filename = (fo+'_dllres.csv'))[0,1]
		tm    = dmean[0]
		dmean = dmean[1:,:]
		dstd  = dstd[1:,:]
		cnt   = 0; pol = []; data = [];
		inv   = -1 if invert else 1
		if(rawdata):
			plt.plot(raw[0]*res, range(np.shape(raw)[1]*inv), 'ob-', mew = 0)
			plt.plot(raw[1]*res, range(np.shape(raw)[1]*inv), 'or-', mew = 0)
		for dset in dmean:
			tmp = []
			for i in range(np.size(dset)):
				if(dset[i]>0 and tm[i]>0):
					tmp.append( [tm[i] , dset[i], (dstd[cnt][i]) ])
			cnt += 1
			tmp = np.array(tmp)
			c = next(color)
			pol.append( np.polynomial.Polynomial.fit(tmp[:,0], tmp[:,1], 3) )
			plt.errorbar(
				tmp[:,0], tmp[:,1]*inv*self.thdac_gain, fmt='o', yerr=tmp[:,2]*3, color=c, label = '               ',
				mew = 0, elinewidth = 1, ecolor = c, markersize = 3, capthick=2, capsize = 2)
			plt.legend(numpoints=1, loc=('lower right'), frameon=False)
			data.append(tmp)
		roots = []
		for p in pol:
			r = p.roots()
			roots.append( np.min( r[r > 0] ) )
		injectPnt = np.mean(roots)
		color=iter(sns.color_palette('deep'))
		first = True
		peakingTime = []
		if(interpolate):
			for t in data:
				t = np.insert(t, 0, [[injectPnt, 0, 0 ]], axis = 0)
				z = np.polyfit(t[:,0], t[:,1], 3)
				p = np.poly1d(z)
				c = next(color)
				plt.plot(tm, p(tm)*inv*self.thdac_gain, '-', color=c, lw=1, alpha = 0.8)
				vl = np.argmax( p(tm)*self.thdac_gain ) * self.dll_resolution # - injectPnt
				peakingTime.append( vl - injectPnt )
				if(first):
					vh = np.max( p(tm)*self.thdac_gain )
					first = False
		if(invert):
			plt.ylim(-np.max(dmean*self.thdac_gain)-10, 0)
		else:
			plt.ylim(-10, np.max(dmean*self.thdac_gain)+10)
		plt.savefig("../SSA_Results/" + filename + ".png", bbox_inches="tight");
		plt.show()
		#return tm, raw, tmp
		return peakingTime

	###########################################################
	def dac_linearity(self, name = 'Bias_THDAC', nbits = 8, eval_inl_dnl = True, npoints = 10, average=10, filename = 'temp/temp', plot_save=True, plot_show=True, filemode = 'w', runname = '', return_raw=False):
		utils.activate_I2C_chip(self.fc7)
		if(self.bias == False): return False, False
		if(not (name in self.muxmap)): return False, False
		if(isinstance(filename, str)):
			fo = "../SSA_Results/" + filename
		if(eval_inl_dnl):
			nlin_params, nlin_data, fit_params, raw = self.bias.measure_dac_linearity(
				name = name, nbits = nbits,	filename = fo,	filename2 = "",
				plot_save=plot_save, plot_show=False, average = 1, runname = runname, filemode = filemode)
			g, ofs, sigma = fit_params
			DNL, INL = nlin_data
			DNLMAX, INLMAX = nlin_params
			x, data = raw
		else:
			g, ofs, raw = self.bias.measure_dac_gain_offset(name = name, nbits = nbits, npoints = npoints)
			x, data = raw
		if name == 'Bias_THDAC':
			baseline = self.bias.get_voltage('Bias_BOOSTERBASELINE')
			data = (0 - np.array(data)) + baseline
		elif name in self.muxmap:
			data = np.array(data)
			baseline = 0
		else:
			return False
		if (plot_save or plot_show):
			plt.clf()
			plt.figure(1)
			#plt.plot(x, f_line(x, ideal_gain/1000, ideal_offset/1000), '-b', linewidth=5, alpha = 0.5)
			plt.plot(x, data, '-r', linewidth=5,  alpha = 0.5)
			if(eval_inl_dnl):
				plt.figure(2); plt.ylim(-1, 1); plt.bar( x, DNL, color='b', edgecolor = 'b', align='center')
				plt.figure(3); plt.ylim(-1, 1); plt.bar( x, INL, color='r', edgecolor = 'r', align='center')
				plt.figure(4); plt.ylim(-1, 1); plt.plot(x, INL, color='r')
			if (plot_show):
				plt.show()
			#if(plot_save):
				#plt.savefig(filename+'/ring_oscillator_vs_dvdd_{:s}.png'.format(mode), bbox_inches="tight");

		#return DNL, INL, x, data
		if(eval_inl_dnl):
			if(return_raw): return [DNLMAX, INLMAX, g, ofs, raw]
			else:           return [DNLMAX, INLMAX, g, ofs]
		else:
			if(return_raw): return [g*1E3, ofs*1E3, baseline*1E3, raw]
			else:           return [g*1E3, ofs*1E3, baseline*1E3]

	###########################################################
	def __shaper_pulse_OLD(self, calrange = [46, 58, 69, 81], strip = 5, baseline = 'auto', iterations = 10, pattern = False):
		shaper_rise = []; shaper_fall = [];
		thresholds_list = []; shapervalues_list = [];
		self.cal.set_trimming(0, 'all')
		self.cal.set_trimming(31, [strip])
		if(isinstance(baseline, int)):
			self.cal.baseline = baseline
		else:
			a, mu, sigma = self.baseline_noise([strip], plot=False)[0]
			self.cal.baseline = int(np.round(mu))
			utils.print_log("->  Baseline = {:3.2f}".format(self.cal.baseline))
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
			thresholds = np.concatenate( [ np.array(thlist_rise)-self.cal.baseline , np.array(thlist_fall)-self.cal.baseline ] )
			shapervalu = np.concatenate( [ shaper_rise[-1], shaper_fall[-1] ] )
			plt.axis([0, np.max(shaper_rise[-1])*2.5, 0, thresholds[ np.where(shaper_rise[-1]>-256)[0] ][-1] + 20 ])
			plt.plot(shapervalu, thresholds, 'o')
			thresholds_list.append(thresholds); shapervalues_list.append(shapervalu)
		plt.show()
		return thresholds_list, shapervalues_list

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


	def quick_test_l1_fifo_overflow_counter(self, latency=11):
		ret = {}
		for l1_rate in [1500, 1600, 1700, 1750, 1800]:
			l1a_period = int(1E6/(25.0*l1_rate)-1)
			self.ssa.reset()
			#rp = self.seuutil.run_seu_test(stop_if_fifo_full=False, latency=11, run_time=1, l1a_period=l1a_period, delay=73)
			#time.sleep(0.1)
			self.I2C.peri_write( register="control_1", field='L1_Latency_msb', data = ((latency & 0x0100)>>8) )
			self.I2C.peri_write( register="control_3", field='L1_Latency_lsb', data = ((latency & 0x00ff)>>0) )
			rp = self.seuutil.run_seu_test(stop_if_fifo_full=False, latency=11, run_time=1, l1a_period=l1a_period, delay=1)
			self.fc7.SendCommand_CTRL("start_trigger")
			time.sleep(0.1)
			l1_trigger = self.ssa.readout.l1_data()[0][0]
			ret[l1_rate] = self.ssa.ctrl.get_L1_FIFO_overflow_counter()
			utils.print_good('->  L1 rate = {:d} kHz -> L1 FIFO Overflow Counter = {:d} | L1 Counter = {:d}'.format(l1_rate, ret[l1_rate], l1_trigger))
		return ret

	def quick_test_digital_pattern(self, strips=[10,20,30,40,50,60,70,80], calpulse_duration=8):
		pattern_list = []
		for cnt in range(8): pattern_list.append(0b0001<<cnt)
		for cnt in range(7): pattern_list.append(0b0011<<cnt)
		for cnt in range(6): pattern_list.append(0b0101<<cnt)
		for cnt in range(5): pattern_list.append(0b1001<<cnt)
		for pattern in pattern_list:
			self.ssa.inject.digital_pulse(strips)
			self.ssa.strip.set_pattern_injection('all', pattern, 0)
			self.ssa.ctrl.set_cal_pulse(amplitude = 255, duration = calpulse_duration)
			ret = self.ssa.readout.cluster_data_delay_new()
			utils.print_info(ret)

	def quick_test_stub_data_offset(self, shift=-3):
		offset = [0]*6
		self.ssa.inject.digital_pulse([19,20,21, 49,50,51, 79,80,81, 109,110,111])
		for i in range(-16,16):
			offset[4] = i
			self.ssa.ctrl.set_stub_data_offset(0, offset[1], offset[2], offset[3], offset[4], 0)
			ret = self.ssa.readout.cluster_data(shift=shift)
			print(ret)

	def quick_dll_phase_measure_scope(self):

		voltage = 0.9

		ssa.pwr.set_supply(d=voltage)

		ssa.pwr.set_dvdd(0.8, chip='MPA')

		self.reset()

		ssa.pwr.set_dvdd(1.0, chip='MPA')

		ssa.chip.ctrl.set_sampling_deskewing_chargepump(1)


		self.reset()

		self.ctrl.init_slvs(0b111)
		self.ctrl.activate_readout_shift()
		self.ctrl.set_shift_pattern_all(0b10000000)

		self.ctrl.init_slvs(0b111)
		self.ctrl.set_t1_clock_output_select('clock')
		self.ctrl.set_sampling_deskewing_coarse(0)

		self.ctrl.set_sampling_deskewing_fine(enable=1, bypass=0, value=0)

		self.ctrl.set_sampling_deskewing_fine(enable=1, bypass=0, value=15)




#self.ctrl.set_sampling_deskewing_coarse(1)
#self.ctrl.set_sampling_deskewing_fine(enable=1, bypass=0, value=0)









		#ssa.test.l1_data(shift=1, nruns=10)



'''
plt.axis([20, 100, 0, 1050])
plt.plot(s0,    'b', colour = #85C0DE)
plt.plot(s31,   'r', )
plt.plot(s, 	'y', )
plt.show()
'''
