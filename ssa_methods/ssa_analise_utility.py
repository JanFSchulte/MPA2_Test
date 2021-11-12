from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from itertools import product as itertools_product
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import sem
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import fnmatch
import re
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns



class SSA_Analise_Test_results():

	def __init__(self, toptest, test, measure, biascal):
		self.test = test; self.measure = measure; self.toptest = toptest; self.biascal = biascal;
		self.set_configuration(9)
		### temporary:
		#self.set_data_path('/home/acaratel/MPA-SSA_Test/SSA_Results/TestLogs/')
		#self.set_data_path('Chip_0_frontend')

	## Setup Plots ####################################################################################

	def set_configuration(self, preset = 'custom'):
		self.noise_mean = []; self.noise_std = []; self.noise_x = [];self.PAVDD = []; self.PDVDD = []; self.pwr_x = [];
		self.VBG = []; self.thresholds = []; self.DAC_GAINs = [];
		if preset == 'custom:':
			print('Use set_data_path(), set_test_name(), set_data_rate(), set_dataseries_name() methods.')
		else: self.__set_run_preset(preset)

	def set_data_path(self, val):
		self.path = val # the path of the data
	def set_test_name(self, val):
		self.run_name = val # The initial part of the name of every SSA log
	def set_data_rate(self, val):
		self.measure_rate = val # for instance the X-Ray Dose Rate or Temperature Step
	def set_dataseries_name(self, val):
		self.XLabel_Series = val

	## Top Methods ####################################################################################

	def FE_Threshold_Trimming(self, filename = 'Init', plot = True):
		plt.clf()
		return self.FE_Threshold_Trimming__Plot(filename = filename, plot = plot)


	def FE_Gain_Noise_Std(self, plot = True, evaluate = False, return_values = False):
		er = True
		if not evaluate:
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets, er = self.FE_Gain_Noise_Std__Reload()
		if(er or evaluate):
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets = self.FE_Gain_Noise_Std__Calculate()
		if(plot):
			self.FE_Gain_Noise_Std__Plot(calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets)
		if return_values:
			return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean


	def DAC_Gain_Ofs_Dnl_Inl_all(self, plot = True):
		self.DAC_Gain_Ofs_Dnl_Inl(name = 'CALDAC', plot = plot, return_values = False)
		self.DAC_Gain_Ofs_Dnl_Inl(name = 'THDAC' , plot = plot, return_values = False)


	def FE_Gain_mVfC(self, evaluate = False):
		t1, t2, t3, t4, t5, t6, FE_gain = self.FE_Gain_Noise_Std(evaluate = evaluate, plot = False, return_values = True)
		t1, t2, CAL_gain_array, t3 = self.DAC_Gain_Ofs_Dnl_Inl(name = 'CALDAC', plot = False, return_values = True)
		t1, t2, THD_gain_array, t3 = self.DAC_Gain_Ofs_Dnl_Inl(name = 'THDAC', plot = False, return_values = True)
		G = self.Convert_ThDacCalDac_to_mVfC(FE_gain, CAL_gain_array, THD_gain_array)
		return G

	def Multi_run(self, runlist = [2,5], evaluate = False):
		self.noise_mean = []; self.noise_std = []; self.noise_x = [];self.PAVDD = []; self.PDVDD = []; self.pwr_x = []; self.VBG = []; self.thresholds = [];
		for r in runlist:
			self.__set_run_preset(r)
			self.pltname = 'MULTI-1'
			self.DAC_Gain_Ofs_Dnl_Inl_all()
			self.FE_Gain_Noise_Std(evaluate = evaluate)
			try:
				self.Power_plot()
			except: #in case of single file or recalibration point
				pass
		self.noise_gain_multirun_plot(len(runlist))
		self.power_multirun_plot(len(runlist))
		self.dacs_multirun_plot(len(runlist))


	def DAC_Gain_Ofs_Dnl_Inl(self, name = 'CALDAC', plot = True, return_values = False):
		DNLs, INLs, GAINs, OFSs, vals, INLs_array = self.DAC_Gain_Ofs_Dnl_Inl__Calculate(name = name)
		if(plot):  self.DAC_Gain_Ofs_Dnl_Inl__Plot(name, DNLs, INLs, GAINs, OFSs, vals, INLs_array)
		if (return_values):  return DNLs, INLs, GAINs, OFSs

	##############################################################################################


	def FE_Gain_Noise_Std__Calculate(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print('->  Searching for matching files in ' + self.path)
		fl = self._get_file_name()
		#files_list = self._get_files_list( 'scurve_trim__cal_' + '*', 'csv')
		files_list = self._get_files_list( 'scurve_trim__cal_' + '*', 'csv')

		if(len(files_list) == 0): return ['er']*7
		calpulses = []; scurve_table = {}; runlist = {}
		print('->  Sorting Informations')
		for f in files_list:
			cfl = re.findall( '\W?cal_(\d+)' , f )
			cal = np.int( cfl[0] )
			if not cal in calpulses:
				calpulses.append(cal)
		for f in files_list:
			tmp = re.findall( self.run_name+'(.*)_scurve_trim__cal_\d+' , f )[0]
			if not tmp in runlist:  runlist[tmp] = [1, f]
			else:  runlist[tmp][0] += 1
		for i in runlist:
			if runlist[i][0] < 2:
				print("->  Excluded file not matching requirements: " + runlist[i][1])
				files_list.remove(runlist[i][1])
		calpulses.sort()
		print('->  Loading data')
		for cal in calpulses:
			tmp = []
			for f in files_list:
				clf = re.findall( '\W?cal_'+str(cal) , f )
				if(len(clf) > 0):
					if (clf[0] == ('cal_'+str(cal)) ):
						scurve = CSV.csv_to_array( self.path + f )
						tmp.append( scurve )
			scurve_table[str(cal)] = tmp
		CSV.array_to_csv( calpulses,  self.path + 'ANALYSIS/S-Curve_cal_values.csv')
		# Threshold spread and Noise
		print('->  Fitting courves for Threshold-Spread and Noise')
		for cal in calpulses:
			c_thresholds = []; c_noise = [];
			c_thmean = []; c_sigmamean = [];
			for st in scurve_table[str(cal)]:
				s = np.transpose(st)
				thround, p = self.measure.cal.evaluate_scurve_thresholds(scurve = s, nevents = 1000)
				#plt.figure();
				#plt.plot(s[:,50], 'b');
				#plt.plot(np.linspace(0,255, 1000), f_errorfc(np.linspace(1,256, 1000), p[50][0], p[50][1], p[50][2]), 'r');
				#plt.show()
				c_thresholds.append( np.array(p)[:,1] ) #threshold per strip
				c_thmean.append( np.mean( np.array(p)[:,1] ) ) #threshold mean
				c_noise.append( np.array(p)[:,2] ) #noise per strip
				c_sigmamean.append( np.mean( np.array(p)[:,2] ) ) #noise mean
			thresholds[str(cal)] = np.array(c_thresholds, dtype = float)
			noise[str(cal)] = np.array(c_noise, dtype = float)
			thmean[str(cal)] = np.array(c_thmean, dtype = float)
			sigmamean[str(cal)] = np.array(c_sigmamean, dtype = float)
			CSV.array_to_csv(c_thresholds, self.path + 'ANALYSIS/S-Curve_Threshold_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_noise,      self.path + 'ANALYSIS/S-Curve_Noise_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_thmean,     self.path + 'ANALYSIS/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_sigmamean,  self.path + 'ANALYSIS/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
		# FE Gain and offset
		print('->  Evaluating Front-End Gain')
		if not (np.shape(thresholds[ str(calpulses[0])])[0] == np.shape(thresholds[ str(calpulses[1])])[0] == np.shape(thresholds[ str(calpulses[2])])[0]):
			print('->   ERROR. The number of files for different calibration charge are not equal. This may make the fitting fail.')
		nelements = np.shape(thresholds[ str(calpulses[0])])[0]
		gains    = np.zeros([120,nelements]);
		offsets  = np.zeros([120,nelements]);
		gainmean = np.zeros(nelements);
		#return thresholds, calpulses
		print(nelements)
		#print(gains)
		for s in range(0,120):
			ths = np.array( [np.array( thresholds[k] , dtype = float)[ : , s ] for k in thresholds if k in list(map(str, calpulses))] )
			self.ths = ths
			for i in range( 0, nelements ):
				par, cov = curve_fit( f= f_line,  xdata = calpulses, ydata = ths[:, i], p0 = [0, 0])
				gains[s, i] = par[0]
				offsets[s, i] = par[1]
		for i in range( 0, nelements ):
			gainmean[i] = np.average(gains[:, i] )
		CSV.array_to_csv(gains,    self.path + 'ANALYSIS/S-Curve_Gain.csv')
		CSV.array_to_csv(gainmean, self.path + 'ANALYSIS/S-Curve_Gain_Mean.csv')
		CSV.array_to_csv(offsets,  self.path + 'ANALYSIS/S-Curve_Offset.csv')
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets



	def FE_Gain_Noise_Std__Reload(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print('->  Loading results')
		f1 = self.path + 'ANALYSIS/S-Curve_cal_values.csv'
		f2 = self.path + 'ANALYSIS/S-Curve_Gain.csv'
		f3 = self.path + 'ANALYSIS/S-Curve_Gain_Mean.csv'
		f4 = self.path + 'ANALYSIS/S-Curve_Offset.csv'
		if(not( os.path.isfile(f1) and os.path.isfile(f2) and os.path.isfile(f3) )):
			print('->  Impossible to find pre-calculated results. Re-calculating..')
			return -1,-1,-1,-1,-1,-1,-1, -1, True
		calpulses = CSV.csv_to_array(f1)[:,1]
		c_gains = CSV.csv_to_array(f2)
		c_offsets = CSV.csv_to_array(f4)
		gainmean = CSV.csv_to_array(f3)[:,1]
		gains = c_gains[:, 1:(np.shape(c_gains)[1])]
		offsets = c_offsets[:, 1:(np.shape(c_offsets)[1])]
		for cal in calpulses:
			c_thresholds = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Threshold_cal_'+str(cal)+'.csv')
			c_noise      = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Noise_cal_'+str(cal)+'.csv')
			c_thmean     = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			c_sigmamean  = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
			thresholds[str(cal)] = c_thresholds[:, 1:(np.shape(c_thresholds)[1])]
			noise[str(cal)]     = c_noise[:, 1:(np.shape(c_noise)[1])]
			thmean[str(cal)]     = c_thmean[:, 1]
			sigmamean[str(cal)]  = c_sigmamean[:, 1]
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets, False

	#def FE_Gain_Noise_Std__Plot_singleRun(self, alpulses, thresholds, noise, thmean, sigmamean, gains, gainmean):

	def FE_Gain_Noise_Std__Plot(self, calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, offsets):
		typcal = str(calpulses[int(len(calpulses)/2)])
		self.typcal = typcal
		multifile = (np.shape(thresholds[typcal])[0] > 1)
		self.thresholds.append(thresholds)
		if multifile:
			# FE Gain evolution #################################
			plt.clf();
			w, h = plt.figaspect(1/6.0)
			fig = plt.figure(figsize=(w,h))
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(False)
			ax.spines["right"].set_visible(False)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
			x = np.array(range(len(gains[0,:]))) * self.measure_rate
			plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
			plt.yticks(fontsize=16)
			plt.ylabel("Front-End Gain", fontsize=16)
			plt.xlabel(self.XLabel_Series, fontsize=16)
			gain_mean = np.array([np.mean(gains[:,i]) for i in x])
			gain_std  = np.array([ np.std(gains[:,i]) for i in x])
			plt.ylim(np.mean(gain_mean)-np.max(gain_std)*3, np.mean(gain_mean)+np.max(gain_std)*3)
			sl_mean = self._sliding_mean(gain_std , 1)
			sl_std  = self._sliding_mean(gain_mean , 1)
			plt.fill_between(x, gain_mean - gain_std,  gain_mean + gain_std, color="#3F5D7D")
			plt.plot(x, gain_mean, color="white", lw=3)
			fpl = self.path + 'ANALYSIS/S-Curve_Gain_Mean'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

		# FE Gain distribution ################################
		plt.clf();
		#w, h = plt.figaspect(1/1.5)
		#fig = plt.figure(figsize=(w,h))
		fig = plt.figure(figsize=(18,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Normalised distribution", fontsize=32)
		plt.xlabel('Front-End Gain [mv/fC]', fontsize=32)
		FE_Gain_mVfC, THD_gain_array, CAL_gain_array, = self.Convert_ThDacCalDac_to_mVfC( np.ones(len(gains[0,:])) , return_vals = True)
		bn = False
		sermean = []
		for i in range(len(self.instances_to_plot)):
			ser = (gains[:,self.instances_to_plot[i]]) * FE_Gain_mVfC[self.instances_to_plot[i]]
			print(len(ser))
			if(bn is False):
				bn = np.arange(min(ser)-2, max(ser)+2, 0.2)
			plt.hist(ser, normed = True, bins = bn, alpha = 0.7)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser))
			m, s = stats.norm.fit(ser) # get mean and standard deviation
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, 'r' , label="Norm") # plot i
			sermean.append(np.mean(ser))
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{G_{FE}} = %6.2f $' % (sermean[i]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=32, color='darkred')
		fpl = self.path + 'ANALYSIS/S-Curve_Gain_hist'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))

		# FE Offset distribution ################################
		plt.clf();
		#w, h = plt.figaspect(1/1.5)
		#fig = plt.figure(figsize=(w,h))
		fig = plt.figure(figsize=(18,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Normalised distribution", fontsize=32)
		plt.xlabel('Front-End Offset [mv]', fontsize=32)
		bn = False
		sermean = []
		for i in range(len(self.instances_to_plot)):
			ser = (offsets[:,self.instances_to_plot[i]]) * offsets[self.instances_to_plot[i]]
			print(len(ser))
			if(bn is False):
				bn = np.arange(min(ser)-2, max(ser)+2, 0.2)
			plt.hist(ser, normed = True, bins = bn, alpha = 0.7)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser))
			m, s = stats.norm.fit(ser) # get mean and standard deviation
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, 'r' , label="Norm") # plot i
			sermean.append(np.mean(ser))
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{OFS_{FE}} = %6.2f mV$' % (sermean[i]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=32, color='darkred')
		fpl = self.path + 'ANALYSIS/S-Curve_Offset_hist'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))

		# FE Noise evolution #################################
		if multifile:
			plt.clf();
			#w, h = plt.figaspect(1/6.0)
			#fig = plt.figure(figsize=(w,h))
			fig = plt.figure(figsize=(18,12))
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(False)
			ax.spines["right"].set_visible(False)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
			x = np.array(range( min( len(noise[typcal][:,0]), len(THD_gain_array), len(FE_Gain_mVfC)))) * self.measure_rate
			plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=32)
			plt.yticks(fontsize=32)
			plt.ylabel("Front-End Noise", fontsize=32)
			plt.xlabel(self.XLabel_Series, fontsize=32)
			ser = []
			for i in x:
				ser.append( self.Convert_Noise_dac_to_electrons(noise[typcal][i,:], THD_gain_array[i] , FE_Gain_mVfC[i]) )
			ser = np.array(ser)
			noise_mean = np.array([np.mean(ser[i]) for i in x])
			noise_std  = np.array([ np.std(ser[i]) for i in x])
			self.noise_mean.append( noise_mean )
			self.noise_std.append( noise_std )
			self.noise_x.append( x )
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			noise_mean_smooth = interpolate.BSpline(x, noise_mean, xnew)
			noise_std_smooth = interpolate.BSpline(x, noise_std, xnew)
			noise_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 999, polyorder = 5)
			color=iter(sns.color_palette('deep'))
			c = next(color)
			plt.fill_between(xnew, noise_hat - noise_std_smooth,  noise_hat + noise_std_smooth, color=c, alpha = 0.3, lw = 3)
			#plt.plot(x, noise_mean, color='#3F5D7D', lw=1)
			plt.plot(xnew, noise_hat, color=c, lw=1)
			fpl = self.path + 'ANALYSIS/S-Curve_Noise_Mean'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

		# Noise #############################################
		plt.clf();
		#w, h = plt.figaspect(1/1.5)
		#fig = plt.figure(figsize=(w,h))
		fig = plt.figure(figsize=(18,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Normalised distribution", fontsize=32)
		plt.xlabel('Noise [e-]', fontsize=32)
		bn = False
		FE_Gain_mVfC, THD_gain_array, CAL_gain_array, = self.Convert_ThDacCalDac_to_mVfC( np.ones(len(gains[0,:])) , return_vals = True)
		ser = []
		for i in range(len(self.instances_to_plot)):
			self.noise = noise
			dataset = np.array(noise[typcal])[self.instances_to_plot[i],:]
			print(len(dataset))
			ser.append( self.Convert_Noise_dac_to_electrons(dataset, THD_gain_array[self.instances_to_plot[i]] , FE_Gain_mVfC[self.instances_to_plot[i]]) )
		bn = np.arange(np.min(ser)-2, np.max(ser)+2, 2)
		for i in range(len(self.instances_to_plot)):
			zorder = i+1 if i!=2 else 0
			plt.hist(ser[i], normed = True, bins = bn, alpha = 0.8, zorder = zorder)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser[i]))
			m, s = stats.norm.fit(ser[i]) # get mean and standard deviation
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			plt.plot(lnspc, pdf_g, color = 'red' , label="Norm") # plot i
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{noise} = %6.2f $' % (np.mean(ser[i])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=32, color='darkred')
		fpl = self.path + 'ANALYSIS/S-Curve_Noise_hist'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))

		plt.clf();
		#w, h = plt.figaspect(1/1.5)
		#fig = plt.figure(figsize=(w,h))
		fig = plt.figure(figsize=(18,12))
		plt.style.use('seaborn-deep')
		ax = fig.add_subplot(111, projection='3d')
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		#ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Normalised distribution", fontsize=32)
		plt.xlabel('Noise [e-]', fontsize=32)
		#plt.zlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i, z, in zip( range(len(self.instances_to_plot)), range(len(self.instances_to_plot))):
			hist, bins = np.histogram(ser[i], bins=bn, normed = True)
			xs = (bins[:-1] + bins[1:])/2
			c = next(color)
			ax.bar(xs, hist, zs=z, zdir='y', alpha=0.8, color = c, width = 2)
			#plt.hist(ser[i], normed = True, bins = bn, alpha = 0.5)
		ax.set_xlabel('X')
		ax.set_ylabel('Y')
		ax.set_zlabel('Z')
		fpl = self.path + 'ANALYSIS/S-Curve_Noise_hist'+self.pltname+'_3d.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))



		# FE threshold distribution ################################
		plt.clf();
		#w, h = plt.figaspect(1/1.5)
		#fig = plt.figure(figsize=(w,h))
		fig = plt.figure(figsize=(18,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel("Normalised distribution", fontsize=32)
		plt.xlabel('Threshold', fontsize=32)
		bn = False
		ser = []
		for i in range(len(self.instances_to_plot)):
			dataset = np.array(thresholds[typcal])[self.instances_to_plot[i],:]
			print(len(dataset))
			ser.append(dataset)
		bn = np.round(np.arange(np.min(ser)-2, np.max(ser)+3, 1))
		plt.xticks( bn, fontsize=32)
		plt.yticks(fontsize=32)
		sigma = []
		for i in range(len(self.instances_to_plot)):
			plt.hist(ser[i], normed = True, bins = bn, alpha = 0.7)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser[i])*100)
			m, s = stats.norm.fit(ser[i]) # get mean and standard deviation
			sigma.append(s)
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			#plt.text(2011.5, 100 , 'mean noise pre-rad' , fontsize=16, color='r')
			plt.plot(lnspc, pdf_g, color = 'red' , label="Norm") # plot i
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{\sigma} = %6.2f $' % (sigma[i]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=32, color='darkred')
			fpl = self.path + 'ANALYSIS/S-Curve_Threshold_Std'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))



	##############################################################################################

	def FE_Threshold_Trimming__Plot(self, filename = 'Init', plot = True):
		print('->  Searching for matching files')
		filename = filename + '*scurve_trim*_cal_*'
		files_list = self._get_files_list( filename, 'csv')
		if(len(files_list) == 0): return
		scurves = {}
		for f in files_list:
			cfl = re.findall( '\W?trim(\d+)_' , f )
			print(cfl)
			if(cfl == []):
				scurves['trim'] = np.transpose( CSV.csv_to_array( self.path + f ) )
			elif(cfl[0] == '0' or cfl[0] == '31'):
				scurves[cfl[0]] = np.transpose( CSV.csv_to_array( self.path + f ) )
		c_thresholds = {}; cmin = np.inf; cmax = 0;
		for i in scurves:
			thround, p = self.measure.cal.evaluate_scurve_thresholds(scurve = scurves[i], nevents = 1000)
			c_thresholds[i] = np.array(p)[:,1]  #threshold per strip
			cmin = np.min([np.min(c_thresholds[i]), cmin])
			cmax = np.max([np.max(c_thresholds[i]), cmax])
		bn = np.round(np.arange(cmin-7, cmax+5, 1)).astype(int)
		bn = np.arange(cmin-7, cmax+5, 1)
		plt.clf();
		gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
		#w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(18,18))
		plt.style.use('seaborn-deep')
		color=iter(sns.color_palette('deep')) #iter(cm.summer(np.linspace(0,1, len(scurves) )))
		#plt.subplot(2, 1, 2)
		ax0 = plt.subplot(gs[1])
		ax0.spines["top"].set_visible(False); ax0.spines["right"].set_visible(False)
		ax0.get_xaxis().tick_bottom(); ax0.get_yaxis().tick_left()
		plt.xticks(fontsize=32); plt.yticks(fontsize=32)
		plt.xlim(min(bn), max(bn)); plt.ylim(0, 1100)
		for i in scurves:
			c=next(color)
			plt.plot( scurves[i] , color = c)
		#plt.subplot(2, 1, 1)
		ax1 = plt.subplot(gs[0])
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.setp(ax1.get_xticklabels(), visible=False)
		plt.xlim(min(bn), max(bn));
		plt.ylim(0, 1)
		ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)
		ax1.get_xaxis().tick_bottom(); ax1.get_yaxis().tick_left()
		labels = ["Optimal trimming values", "Not trimmed: THDAC = MIN", "Not trimmed: THDAC = MAX"]
		cnt = 0
		stds = []
		for i in scurves:
			plt.hist(c_thresholds[i], normed = True, bins = bn, alpha = 0.7, label = (labels[cnt]))
			xt = plt.xticks()[0]
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(c_thresholds[i]))
			m, s = stats.norm.fit(c_thresholds[i]) # get mean and standard deviation
			stds.append(s)
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			xnew = np.linspace(np.min(lnspc), np.max(lnspc), 1000, endpoint=True)
			pdf_l = interpolate.BSpline(lnspc, pdf_g, xnew)
			plt.plot(xnew, pdf_l, c = 'darkred', lw = 2) # plot i
			cnt += 1
		leg = ax1.legend(fontsize = 24, )
		leg.get_frame().set_linewidth(0.0)
		fpl = self.path + 'ANALYSIS/S-Curve_Threshold_Trimming'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))
		plt.show()
		return stds


	##############################################################################################

	def Power_AnalogParams_plot(self, filename = 'default', plot = True):
		print('->  Searching for matching files')
		if filename == 'default':
			filename = '*GlobalLog'
		files_list = self._get_files_list( filename, 'csv')
		if(len(files_list)==0): return
		params = CSV.csv_to_array_en( self.path + files_list[0] )
		PDVDD = np.array( params[:,1], dtype = float);
		PAVDD = np.array( params[:,2], dtype = float);
		PPVDD = np.array( params[:,3], dtype = float);
		GND = np.array( params[:,4], dtype = float);
		VBG = np.array( params[:,5], dtype = float);
		Bias_BOOSTERBASELINE = np.array( params[:,6], dtype = float);
		Bias_D5BFEED = np.array( params[:,7], dtype = float);
		Bias_D5PREAMP = np.array( params[:,8], dtype = float);
		Bias_D5TDR = np.array( params[:,9], dtype = float);
		Bias_D5ALLV = np.array( params[:,10], dtype = float);
		Bias_D5ALLI = np.array( params[:,11], dtype = float);
		Bias_D5DAC8 = np.array( params[:,12], dtype = float);
		inj = np.array( params[:,27], dtype = float);
		cldata = np.array( params[:,28], dtype = float);
		mem1 = np.array( params[:,29], dtype = float);
		l1 = np.array( params[:,31], dtype = float);
		#return params
		x = np.array(range(len(params[:,0]))) * self.measure_rate
		xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
		w, h = plt.figaspect(1/6.0)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("mV", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)

		plt.plot(xnew, interpolate.BSpline(x, PAVDD, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, PDVDD, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, PPVDD, xnew), color='r', lw=1)

		fig = plt.figure(figsize=(w,h))
		plt.plot(xnew, interpolate.BSpline(x, VBG, xnew), color='r', lw=1)

		fig = plt.figure(figsize=(w,h))
		plt.plot(xnew, interpolate.BSpline(x, Bias_D5BFEED, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, Bias_D5PREAMP, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, Bias_D5ALLV, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, Bias_D5ALLI, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, Bias_D5DAC8, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, GND, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, VBG, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.BSpline(x, Bias_BOOSTERBASELINE, xnew), color='r', lw=1)
		plt.show()

	def Power_plot(self, filename = 'default', plot = True, save = True):
		print('->  Searching for matching files')
		if filename == 'default':
			filename = '*GlobalLog'
		files_list = self._get_files_list( filename, 'csv')
		if(len(files_list)==0): return
		params = CSV.csv_to_array_en( self.path + files_list[0] )
		PDVDD = np.array( params[:,1], dtype = float);
		PAVDD = np.array( params[:,2], dtype = float);
		PPVDD = np.array( params[:,3], dtype = float);
		VBG   = np.array( params[:,5], dtype = float);
		x = np.array(range(len(params[:,0]))) * self.measure_rate
		xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
		w, h = plt.figaspect(1/6.0)
		if save: fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("mW", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		#PAVDD_int = interpolate.BSpline(x, PAVDD, xnew)
		#PDVDD_int = interpolate.BSpline(x, PDVDD, xnew)
		#VBG_int   = interpolate.BSpline(x, VBG, xnew)
		self.PAVDD.append(PAVDD)
		self.PDVDD.append(PDVDD)
		self.VBG.append(VBG)
		self.pwr_x.append(xnew)
		c = next(color)
		plt.plot(x, PAVDD, color=c, lw=3)
		c = next(color)
		plt.plot(x, PDVDD, color=c, lw=3)
		#c = next(color)
		#plt.plot(x, VBG, color=c, lw=3)
		self.PrcPAVDD = PAVDD
		self.PrcPDVDD = PDVDD
		self.PrcVBG   = VBG

		if save:
			fpl = self.path + 'ANALYSIS/Power_'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

	def power_gain_percent_variation_plot(self):

		self.DAC_Gain_Ofs_Dnl_Inl(name = 'THDAC')
		self.Power_plot()
		plt.clf();
		fig = plt.figure(figsize=(18,18))
		plt.style.use('seaborn-deep')
		color=iter(sns.color_palette('deep'))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = range(0,100)
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=32)
		plt.ylabel(" Variation [%]", fontsize=32)
		plt.xlabel(self.XLabel_Series, fontsize=32)
		plt.yticks(fontsize=32)
		xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)

		c = next(color)
		PrcPAVDD = (100.0*(self.PrcPAVDD/self.PrcPAVDD[0]-1))[x]
		plt.plot(x, PrcPAVDD, color=c, lw=0, marker='o')
		PrcPAVDD = interpolate.BSpline(x, PrcPAVDD, xnew)
		PrcPAVDD = scypy_signal.savgol_filter(x = PrcPAVDD , window_length = 501, polyorder = 5, mode='nearest')
		plt.plot(xnew, PrcPAVDD, color=c, lw=2)

		c = next(color)
		PrcPDVDD = (100.0*(self.PrcPDVDD/self.PrcPDVDD[0]-1))[x]
		plt.plot(x, PrcPDVDD, color=c, lw=0, marker='o')
		PrcPDVDD = scypy_signal.savgol_filter(x = PrcPDVDD , window_length = 51, polyorder = 5, mode='nearest')
		#PrcPDVDD[0] = 0
		#PrcPDVDD = interpolate.BSpline(x, PrcPDVDD, xnew)
		plt.plot(x, PrcPDVDD, color=c, lw=2)

		c = next(color)
		PrcThGAIN = (100.0*(self.PrcThGAIN/self.PrcThGAIN[0]-1))[x]
		plt.plot(x, PrcThGAIN, color=c, lw=0, marker='o')
		#PrcThGAIN = interpolate.BSpline(x, PrcThGAIN, xnew)
		#PrcThGAIN = scypy_signal.savgol_filter(x = PrcThGAIN , window_length = 501, polyorder = 5, mode='nearest')
		fn = interpolate.interp1d(x, PrcThGAIN, kind='cubic')
		plt.plot(xnew, fn(xnew), color=c, lw=2)



		#plt.plot(x, (100.0*(self.PrcVBG/self.PrcVBG[0]-1))[x], color=c, lw=0, marker='o')
		#c = next(color)
		#plt.plot(x, (100.0*(self.PrcThGAIN/self.PrcThGAIN[0]-1))[x], color=c, lw=0, marker='o')
		fpl = self.path + 'ANALYSIS/' + '_Percent_Evolution'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))



	def power_multirun_plot(self, nplots):
		xmax = np.min(list( np.max(self.pwr_x[i]) for i in range(len(self.pwr_x))))
		x = range(np.int(xmax+1))
		w, h = plt.figaspect(1/4.0)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("mW", fontsize=16)
		#plt.ylim(10, 35)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots):
			c = next(color);
			plt.plot(x, self.PAVDD[i][x], color=c, lw=3, alpha = 0.8)
			plt.plot(x, self.PDVDD[i][x], color=c, lw=3, alpha = 0.8)
			#c = next(color);
		fpl = self.path + 'ANALYSIS/Power'+self.pltname+'_multirun.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Bandgap [mV]", fontsize=16)
		#plt.ylim(240, 290)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
		for i in range(nplots):
			c = next(color);
			vbg_smuth = interpolate.BSpline(x, np.array(self.VBG[i][x]), xnew)
			vbg_hat = scypy_signal.savgol_filter(x = vbg_smuth , window_length = 999, polyorder = 5)
			plt.plot(xnew, vbg_smuth , color=c, lw=0.8, alpha = 0.8)
			plt.plot(xnew, vbg_hat   , color=c, lw=3, alpha = 0.8)
			#c = next(color);
		fpl = self.path + 'ANALYSIS/V_BG'+self.pltname+'_multirun.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))


	def dacs_multirun_plot(self, nplots):
		xmax = np.min( list(len(self.DAC_GAINs[i]) for i in range(nplots) ))
		x = range(np.int(xmax))
		w, h = plt.figaspect(1/4.0)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("mV/cnt", fontsize=16)
		#plt.ylim(10, 35)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
		for i in range(nplots):
			c = next(color);
			gain_smuth = interpolate.BSpline(x, -1*np.array(self.DAC_GAINs[i][0:xmax]), xnew)
			gain_hat = scypy_signal.savgol_filter(x = gain_smuth , window_length = 999, polyorder = 5)
			plt.plot(xnew, gain_smuth , color=c, lw=0.8, alpha = 0.8)
			plt.plot(xnew, gain_hat , color=c, lw=3, alpha = 0.8)

			#c = next(color);
		fpl = self.path + 'ANALYSIS/DAC_GAIN'+self.pltname+'_multirun.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))






		#plt.savefig(self.path + 'ANALYSIS/S-Curve_Noise_Mean.png', bbox_inches="tight");





	##############################################################################################

	def DAC_Gain_Ofs_Dnl_Inl__Calculate(self, name = 'CALDAC'):
		fl = self._get_file_name()
		files_list = self._get_files_list( 'DNL_INL_Bias_' + name + '.csv', 'csv')
		if(len(files_list) == 0): return
		vals = []; DNLs = []; INLs = []; GAINs = []; OFSs = []; INLs_array = []; nbits = 8;
		for filename in files_list:
			tmp = CSV.csv_to_array( self.path + filename )
			vals.append(tmp)
		for v in vals:
			dnl, inl = self.biascal._dac_dnl_inl(data = v[:,1], nbits = 8, plot = False)
			INLs_array.append(inl)
			inl_max = np.max(np.abs(inl))
			dnl_max = np.max(np.abs(dnl))
			gain, ofs, sigma = utils.linear_fit(range(0,2**nbits), v[:,1])
			gain *= 1E3; ofs *= 1E3
			DNLs.append(dnl_max)
			INLs.append(inl_max)
			GAINs.append(gain)
			OFSs.append(ofs)
		CSV.array_to_csv(DNLs,  self.path + 'ANALYSIS/' + name + '_DNL.csv')
		CSV.array_to_csv(INLs,  self.path + 'ANALYSIS/' + name + '_INL.csv')
		CSV.array_to_csv(GAINs, self.path + 'ANALYSIS/' + name + '_GAIN.csv')
		CSV.array_to_csv(OFSs,  self.path + 'ANALYSIS/' + name + '_OFS.csv')
		return DNLs, INLs, GAINs, OFSs, vals, INLs_array


	def DAC_Gain_Ofs_Dnl_Inl__Plot(self, name, DNLs, INLs, GAINs, OFSs, vals, INLs_array):
		plt.clf();
		w, h = plt.figaspect(1/4.0)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.array(range(len(GAINs))) * self.measure_rate
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel(name + " Gain [mV/cnt]", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		gain_mean = np.array([np.mean(GAINs) for i in x])
		gain_std  = np.array([ np.std(GAINs) for i in x])
		plt.ylim(np.mean(gain_mean)-np.max(gain_std)*5, np.mean(gain_mean)+np.max(gain_std)*5)
		#plt.title("Chess games are getting longer", fontsize=22)
		#sl_mean = self._sliding_mean(gain_std , 1)
		#sl_std  = self._sliding_mean(gain_mean , 1)
		# plt.fill_between(range(len(GAINs[0,:])), sl_mean - sl_std,  sl_mean + sl_std, color="#3F5D7D")
		if name == 'THDAC':
			self.DAC_GAINs.append(GAINs)
		plt.plot(x, GAINs, color="#3F5D7D", lw=3)
		fpl = self.path + 'ANALYSIS/' + name + '_GAIN_Evolution'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))


		plt.clf();
		fig = plt.figure(figsize=(18,18))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.array(range(len(GAINs))) * self.measure_rate
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=32)
		plt.ylabel(name + " Gain [mV/cnt]", fontsize=32)
		plt.xlabel(self.XLabel_Series, fontsize=32)
		plt.yticks(fontsize=32)
		gain_mean = np.array([np.mean(GAINs) for i in x])
		gain_std  = np.array([ np.std(GAINs) for i in x])
		#plt.ylim(np.mean(gain_mean)-np.max(gain_std)*5, np.mean(gain_mean)+np.max(gain_std)*5)
		if name == 'THDAC':
			self.DAC_GAINs.append(GAINs)
			self.PrcThGAIN = GAINs
		plt.plot(x, 100.0*(GAINs/GAINs[0]-1), color="#3F5D7D", lw=0, marker='o')
		fpl = self.path + 'ANALYSIS/' + name + '_GAIN_Evolution'+self.pltname+'Percent.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))



		plt.clf();
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		#plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		x = np.array(range(len(vals[0][:,1])))
		plt.xticks(range(0,255,16), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel(" Output Voltage [mV]", fontsize=16)
		plt.xlabel('Control code' , fontsize=16)
		for i in self.instances_to_plot:
			plt.plot(x, vals[i][:,1], lw=6, alpha = 0.5)
		fpl = self.path + 'ANALYSIS/' + name + '_GAIN_Caracteristics.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))

		plt.clf();
		w, h = plt.figaspect(1/2.5)
		fig = plt.figure(figsize=(w,h))
		#plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		ax.set_ylim([-0.8,0.8])
		x = np.array(range(len(INLs_array[0])))
		plt.xticks(range(0,255,16), fontsize=16)
		plt.yticks(np.arange(-0.8, 1, 0.2), fontsize=16)
		plt.ylabel(" Integral Non-Linearity [cnts]", fontsize=16)
		plt.xlabel('Control code [cnts]' , fontsize=16)
		for i in self.instances_to_plot:
			plt.plot(x, INLs_array[i], lw=6, alpha = 0.5)
		plt.plot(x, [np.max(INLs_array[self.instances_to_plot[-1]])]*len(x), 'r--', lw=1, alpha = 0.5)
		plt.plot(x, [np.min(INLs_array[self.instances_to_plot[-1]])]*len(x), 'r--', lw=1, alpha = 0.5)
		plt.text(1, 1.00, self.label[0] + r'  ${INL_{MAX}} = %6.2f $' % ( INLs[self.instances_to_plot[ 0]] ), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
		if(len(self.instances_to_plot)>1):
			plt.text(1, 0.95, self.label[-1]  + r'  ${INL_{MAX}} = %6.2f $' % ( INLs[self.instances_to_plot[-1]]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
		fpl = self.path + 'ANALYSIS/' + name + '_GAIN_INLs'+self.pltname+'.png'
		plt.savefig(fpl, bbox_inches="tight");
		print("->  Plot saved in %s" % (fpl))


	##############################################################################################
	def noise_gain_multirun_plot(self, nplots):
		plt.clf();
		fig = plt.figure(figsize=(18,18))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		xmax = np.min(list( np.max(self.noise_x[i]) for i in range(len(self.noise_x))))
		x = range(xmax+1)
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("FE Noise [e-]", fontsize=32)
		plt.xlabel(self.XLabel_Series, fontsize=32)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots):
			noise_mean = np.array(self.noise_mean[i])
			for nk in range(1,len(noise_mean)-1):
				if(np.abs(noise_mean[nk]-noise_mean[nk-1])  > 20):
					noise_mean[nk] = (noise_mean[nk+1]+noise_mean[nk-1])/2.0
			noise_std  = np.array(self.noise_std[i])
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			noise_mean_smooth = interpolate.BSpline(x, noise_mean[x], xnew)
			noise_std_smooth = interpolate.BSpline(x, noise_std[x], xnew)
			noise_mean_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 301, polyorder = 5)
			noise_std_hat = scypy_signal.savgol_filter(x = noise_std_smooth , window_length = 301, polyorder = 5)
			c = next(color)
			plt.fill_between(xnew, noise_mean_hat - noise_std_hat,  noise_mean_hat + noise_std_hat, alpha = 0.3, color = c)
			plt.plot(x, noise_mean[x], lw=0, color = c, marker='.') ## no filter
			plt.plot(xnew, noise_mean_hat, lw=3, color = c)

			fpl = self.path + 'ANALYSIS/S-Curve_Noise_Mean_DoubleRun'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

		plt.clf();
		w, h = plt.figaspect(1/1)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		xmax = np.min(list( np.max(self.noise_x[i]) for i in range(len(self.noise_x))))
		x = range(xmax+1)
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("FE Noise [e-]", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots):
			noise_mean = np.array(self.noise_mean[i])
			noise_std  = np.array(self.noise_std[i])
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			noise_mean_smooth = interpolate.BSpline(x, noise_mean[x], xnew)
			noise_std_smooth = interpolate.BSpline(x, noise_std[x], xnew)
			noise_mean_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 301, polyorder = 5)
			noise_std_hat = scypy_signal.savgol_filter(x = noise_std_smooth , window_length = 301, polyorder = 5)
			c = next(color)
			plt.fill_between(xnew, ((noise_mean_hat-noise_std_hat)/noise_mean_hat[0]-1),  ((noise_mean_hat+noise_std_hat)/noise_mean_hat[0]-1), alpha = 0.3, color = c)
			plt.plot(xnew, 100.0*((noise_mean_hat/noise_mean_hat[0])-1), lw=3, color = c)
			fpl = self.path + 'ANALYSIS/S-Curve_Noise_Mean_DoubleRun'+self.pltname+'Percent.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

		plt.clf();
		w, h = plt.figaspect(1/1)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		xmax = np.min(list( np.max(self.noise_x[i]) for i in range(len(self.noise_x))))
		x = range(xmax+1)
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("FE Noise [e-]", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots):
			plt.xscale('log')
			noise_mean = np.array(self.noise_mean[i])
			noise_std  = np.array(self.noise_std[i])
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			noise_mean_smooth = interpolate.BSpline(x, noise_mean[x], xnew)
			noise_std_smooth = interpolate.BSpline(x, noise_std[x], xnew)
			noise_mean_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 501, polyorder = 5)
			noise_std_hat = scypy_signal.savgol_filter(x = noise_std_smooth , window_length = 501, polyorder = 5)
			c = next(color)
			plt.fill_between(xnew, noise_mean_hat - noise_std_hat,  noise_mean_hat + noise_std_hat, alpha = 0.3, color = c)
			plt.plot(xnew, noise_mean_hat, lw=2, color = c)
			fpl = self.path + 'ANALYSIS/S-Curve_Noise_Mean_DoubleRun'+self.pltname+'LOG.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))

		plt.clf();
		w, h = plt.figaspect(1/1)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		xmax = np.min(list( np.max(self.noise_x[i]) for i in range(len(self.noise_x))))
		x = range(xmax+1)
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("FE Noise [e-]", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots):
			noise_mean = np.array(self.noise_mean[i])
			noise_std  = np.array(self.noise_std[i])
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			noise_mean_smooth = interpolate.BSpline(x, noise_mean[x], xnew)
			noise_std_smooth = interpolate.BSpline(x, noise_std[x], xnew)
			noise_mean_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 501, polyorder = 5)
			noise_mean_hat = (noise_mean_hat)/noise_mean_hat[0] - 1
			noise_std_hat = scypy_signal.savgol_filter(x = noise_std_smooth , window_length = 501, polyorder = 5)
			noise_std_hat = (noise_std_hat)/noise_mean_hat[0]
			c = next(color)
			plt.fill_between(xnew, noise_mean_hat - noise_std_hat,  noise_mean_hat + noise_std_hat, alpha = 0.3, color = c)
			plt.plot(xnew, noise_mean_hat, lw=2, color = c)
			fpl = self.path + 'ANALYSIS/S-Curve_Noise_Mean_DoubleRun'+self.pltname+'Percent1.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))


		plt.clf();
		w, h = plt.figaspect(1/6.0)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("FE Threshold mean [LSB]", fontsize=16)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		xmax = np.min( list(len(self.thresholds[i][self.typcal][:,0]) for i in range(nplots) ))
		x = range(xmax)
		color=iter(sns.color_palette('deep'))
		for p in range(nplots):
			th_mean = np.zeros(xmax, dtype = float)
			th_std = np.zeros(xmax, dtype = float)
			for i in x:
				th_mean[i], th_std[i] = stats.norm.fit(self.thresholds[p][self.typcal][i,:])
			xnew = np.linspace(np.min(x), np.max(x), 1000, endpoint=True)
			th_mean_smooth = interpolate.BSpline(x, th_mean[x], xnew)
			th_std_smooth = interpolate.BSpline(x, th_std[x], xnew)
			th_mean_hat = scypy_signal.savgol_filter(x = th_mean_smooth , window_length = 501, polyorder = 5)
			th_std_hat = scypy_signal.savgol_filter(x = th_std_smooth , window_length = 501, polyorder = 5)
			c = next(color)
			plt.fill_between(xnew, th_mean_hat - th_std_hat,  th_mean_hat + th_std_hat, alpha = 0.3, color = c)
			plt.plot(xnew, th_mean_smooth, lw=2, color = c)
			fpl = self.path + 'ANALYSIS/S-Curve_Threshold_Mean_DoubleRun'+self.pltname+'.png'
			plt.savefig(fpl, bbox_inches="tight");
			print("->  Plot saved in %s" % (fpl))






	##############################################################################################

	def Convert_ThDacCalDac_to_mVfC(self, FE_gain_array, CAL_gain_array = 'evaluate', THD_gain_array = 'evaluate', return_vals = False):
		if(isinstance(CAL_gain_array, str)):
			t1, t2, CAL_gain_array, CAL_ofs = self.DAC_Gain_Ofs_Dnl_Inl(name = 'CALDAC', plot = False, return_values = True)
		if(isinstance(THD_gain_array, str)):
			t1, t2, THD_gain_array, THD_ofs = self.DAC_Gain_Ofs_Dnl_Inl(name = 'THDAC', plot = False, return_values = True)
		THD_gain_array = -np.array(THD_gain_array) #should be respect to Bias feedback baseline (the leftover offset is < 1mV, tracured here)
		CAL_gain_array = np.array(CAL_gain_array)
		if(not (len(FE_gain_array)==len(THD_gain_array)==len(CAL_gain_array))): #there should be equal numbers of files, this situation should never happen, but in case
			m = min(len(FE_gain_array), len(THD_gain_array), len(CAL_gain_array))
			FE_gain_array = FE_gain_array[0:m]; THD_gain_array = THD_gain_array[0:m]; CAL_gain_array = CAL_gain_array[0:m];
		G = FE_gain_array * THD_gain_array / (CAL_gain_array * 52.0) * 1E3
		if not return_vals:
			return G
		else:
			return G, THD_gain_array, CAL_gain_array


	def Convert_Noise_dac_to_electrons(self, Sigma, DAC_Gain, FE_Gain): # use [lsb - mV/lsb - mV/fC]
		Noise = ( np.array(Sigma) * DAC_Gain * 1E-3) / (FE_Gain * 1E12 * ph_const.elementary_charge )
		for i in range(len(Noise)):
			if Noise[i] > 600:
				print('High Noise strip: ' + str(i) + '   ' + str(Sigma[i]) + '   ' +   str(DAC_Gain) + '   ' +   str(FE_Gain) +  '   ' +   str(Noise[i]))
				print('Average:          ' + '  '   + '   ' + str(np.mean(Sigma)) + '   ' +   str(np.mean(DAC_Gain)) + '   ' +   str(np.mean(FE_Gain)) +  '   ' +   str(np.mean(Noise)))
		return Noise


	def Power(self, plot = True, evaluate = False, return_values = False):
		print('TO DO')


	def _get_file_name(self, folder='default' , run_name='default'):
		if(run_name == 'default'):
			f = self.run_name
		if(folder == 'default'):
			r = self.path
		fi = r + str(f) + '_'
		return fi


	def _get_files_list(self, test_name, file_format = 'csv'):
		matchstr = self.run_name + '*' + '_' + test_name + '.' + file_format
		#print(matchstr)
		rp = fnmatch.filter( os.listdir( self.path ), matchstr)
		rp = sorted(rp)
		print('->  Found %d data files matching %s' % (len(rp), matchstr))
		return rp


	def _sliding_mean(self, data_array, window=5):
		data_array = np.array(data_array)
		new_list = []
		for i in range(len(data_array)):
			indices = range(max(i - window + 1, 0), min(i + window + 1, len(data_array)))
			avg = 0
			for j in indices:
				avg += data_array[j]
			avg /= float(len(indices))
			new_list.append(avg)
		return np.array(new_list)


	def __set_run_preset(self, n):
		if(n==0):
			self.path =  '../../Desktop/aaa/X-Ray_CHIP-C8_25C_200Mrad/'
			self.run_name = 'X-Ray_C8_'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, -2] #first and last
			self.label = [' Pre-Rad :', '200 Mrad :']
			self.pltname = ''
		elif(n==1):
			self.path =  '../../Desktop/aaa/X-Ray_CHIP-C8_25C_200Mrad/'
			self.run_name = 'X-Ray_C8_'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, 100, -2] #first and last
			self.pltname = '_v2'
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']
		elif(n==2):
			self.path =  '../../Desktop/aaa/X-Ray_Chip-C5_T-30C_100Mrad_final/'
			self.run_name = 'X-Ray_-30C'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, 100] #first and last
			self.pltname = ''
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']
		elif(n==3):
			self.path =  '../../Desktop/aaa/SSA_Results/ChipC8/'
			self.run_name = 'ChipC8_25C'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, -1] #first and last
			self.pltname = 'PROVA'
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']
		elif(n==4):
			self.path =  '../../Desktop/aaa/Chip1/ALL/'
			self.run_name = 'Chip1'
			self.measure_rate = 1
			self.XLabel_Series = ''
			self.instances_to_plot = [0]
			self.pltname = ''
			self.label[0] = ''
			self.label[-1] = ''
		elif(n==5):
			self.path =  '../../Desktop/aaa/X-Ray_Chip-C7_T+250C_100Mrad/'
			self.run_name = 'X-Ray_ChipC7_T25C'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, 100] #first and last
			self.pltname = '_Run3'
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']
		elif(n==6):
			self.path =  '../../Desktop/aaa/NEW_RECALIB/'
			self.run_name = 'X-Ray_ChipC7_T25C'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0,1,2]
			self.pltname = '_Run3'
			self.label = [' Pre-Rad :', '120 Mrad :', '120 Mrad Re-Calib :']
		elif(n==7):
			self.path =  '../../Desktop/aaa/X-Ray_Chip-C5_T-30C_100Mrad_final/'
			self.run_name = 'X-Ray_-30C_'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0] #first and last
			self.label = ['']
			self.pltname = ''
		elif(n==8):
			self.path =  '../../Desktop/aaa/NEW_RECALIB/'
			self.run_name = 'X-Ray_ChipC7_T25C_RECALIB'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, -1] #first and last
			self.pltname = ''
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']
		elif(n==9):
			self.path =  '../SSA_Results/XRAY/'
			self.run_name = 'X-Ray_ChipC7_T25C_RECALIB'
			self.measure_rate = 1
			self.XLabel_Series = 'Total Ionising Dose [Mrad]'
			self.instances_to_plot = [0, -1] #first and last
			self.pltname = ''
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']




	def __set_run_temperature(self):
		self.path =  '../../Desktop/aaa/SSA_Results/'








#relevant_path = '../../Desktop/aaa/prova'
#file_names = [fn for fn in os.listdir(relevant_path) if any(fn.endswith(ext) for ext in included_extensions)]
