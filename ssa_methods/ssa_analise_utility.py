from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
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
		self.set_configuration(0)

	## Setup Plots ####################################################################################

	def set_configuration(self, preset = 'custom'):
		self.noise_mean = []; self.noise_std = []; self.noise_x = [];
		if preset == 'custom:':  print 'Use set_data_path(), set_test_name(), set_data_rate(), set_dataseries_name() methods.'
		else: self.__set_run_preset(preset)

	def set_data_path(self, val):
		self.path = path # the path of the data
	def set_test_name(self, val):
		self.run_name = name # The initial part of the name of every SSA log
	def set_data_rate(self, val):
		self.measure_rate = measure_rate # for instance the X-Ray Dose Rate or Temperature Step
	def set_dataseries_name(self, val):
		self.XLabel_Series = XLabel_Series

	## Top Methods ####################################################################################

	def FE_Threshold_Trimming(self, filename = 'Init', plot = True):
		return self.FE_Threshold_Trimming__Plot(filename = filename, plot = plot)


	def FE_Gain_Noise_Std(self, plot = True, evaluate = False, return_values = False):
		if not evaluate:
			er = True
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, er = self.FE_Gain_Noise_Std__Reload()
		if(er or evaluate):
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean = self.FE_Gain_Noise_Std__Calculate()
		if(plot):
			self.FE_Gain_Noise_Std__Plot(calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean)
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

	def Multi_run(self, runlist = [2,5]):
		self.noise_mean = []; self.noise_std = []; self.noise_x = [];self.PAVDD = []; self.PDVDD = []; self.pwr_x = []; self.VBG = [];
		for r in runlist:
			self.__set_run_preset(r)
			self.DAC_Gain_Ofs_Dnl_Inl_all()
			self.FE_Gain_Noise_Std()
			self.Power_plot()
		self.noise_gain_multirun_plot(len(runlist))
		self.power_multirun_plot(len(runlist))

	def DAC_Gain_Ofs_Dnl_Inl(self, name = 'CALDAC', plot = True, return_values = False):
		DNLs, INLs, GAINs, OFSs, vals, INLs_array = self.DAC_Gain_Ofs_Dnl_Inl__Calculate(name = name)
		if(plot):  self.DAC_Gain_Ofs_Dnl_Inl__Plot(name, DNLs, INLs, GAINs, OFSs, vals, INLs_array)
		if (return_values):  return DNLs, INLs, GAINs, OFSs

	##############################################################################################


	def FE_Gain_Noise_Std__Calculate(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print '->  \tSearching for matching files in ' + self.path
		fl = self._get_file_name()
		files_list = self._get_files_list( 'scurve_trim__cal_' + '*', 'csv')
		if(len(files_list) == 0): return ['er']*7
		calpulses = []; scurve_table = {}; runlist = {}
		print '->  \tSorting Informations'
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
				print "->  \tExcluded file not matching requirements: " + runlist[i][1]
				files_list.remove(runlist[i][1])
		calpulses.sort()
		print '->  \tLoading data'
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
		print '->  \tFitting courves for Threshold-Spread and Noise'
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
			CSV.array_to_csv(c_noise,     self.path + 'ANALYSIS/S-Curve_Noise_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_thmean,     self.path + 'ANALYSIS/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_sigmamean,  self.path + 'ANALYSIS/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
		# FE Gain and offset
		print '->  \tEvaluating Front-End Gain'
		nelements = np.shape(thresholds[ str(calpulses[0])])[0]
		gains = np.zeros([120,nelements]);
		gainmean = np.zeros(nelements);
		#return thresholds, calpulses
		print nelements
		#print gains
		self.thresholds = thresholds
		for s in range(0,120):
			ths = np.array( [np.array( thresholds[k] , dtype = float)[ : , s ] for k in thresholds if k in list(map(str, calpulses))] )
			self.ths = ths
			for i in range( 0, nelements ):
				par, cov = curve_fit( f= f_line,  xdata = calpulses, ydata = ths[:, i], p0 = [0, 0])
				gains[s, i] = par[0]
		for i in range( 0, nelements ):
			gainmean[i] = np.average(gains[:, i] )
		CSV.array_to_csv(gains, self.path    + 'ANALYSIS/S-Curve_Gain.csv')
		CSV.array_to_csv(gainmean, self.path + 'ANALYSIS/S-Curve_Gain_Mean.csv')
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean



	def FE_Gain_Noise_Std__Reload(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print '->  \tLoading results'
		f1 = self.path + 'ANALYSIS/S-Curve_cal_values.csv'
		f2 = self.path + 'ANALYSIS/S-Curve_Gain.csv'
		f3 = self.path + 'ANALYSIS/S-Curve_Gain_Mean.csv'
		if(not( os.path.isfile(f1) and os.path.isfile(f2) and os.path.isfile(f3) )):
			print '->  \tImpossible to find pre-calculated results. Re-calculating..'
			return -1,-1,-1,-1,-1,-1,-1, True
		calpulses = CSV.csv_to_array(f1)[:,1]
		c_gains = CSV.csv_to_array(f2)
		gainmean = CSV.csv_to_array(f3)[:,1]
		gains = c_gains[:, 1:(np.shape(c_gains)[1])]
		for cal in calpulses:
			c_thresholds = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Threshold_cal_'+str(cal)+'.csv')
			c_noise     = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Noise_cal_'+str(cal)+'.csv')
			c_thmean     = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			c_sigmamean  = CSV.csv_to_array(self.path + 'ANALYSIS/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
			thresholds[str(cal)] = c_thresholds[:, 1:(np.shape(c_thresholds)[1])]
			noise[str(cal)]     = c_noise[:, 1:(np.shape(c_noise)[1])]
			thmean[str(cal)]     = c_thmean[:, 1]
			sigmamean[str(cal)]  = c_sigmamean[:, 1]
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean, False



	def FE_Gain_Noise_Std__Plot(self, calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean):
		typcal = str(calpulses[int(len(calpulses)/2)])
		multifile = (np.shape(thresholds[typcal])[0] > 1)
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
			plt.savefig(self.path + 'ANALYSIS/S-Curve_Gain_Mean'+self.pltname+'.png', bbox_inches="tight");

		# FE Gain distribution ################################
		plt.clf();
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Normalised distribution", fontsize=16)
		plt.xlabel('Front-End Gain [mv/fC]', fontsize=16)
		FE_Gain_mVfC, THD_gain_array, CAL_gain_array, = self.Convert_ThDacCalDac_to_mVfC( np.ones(len(gains[0,:])) , return_vals = True)
		bn = False
		sermean = []
		for i in range(len(self.instances_to_plot)):
			ser = (gains[:,self.instances_to_plot[i]]) * FE_Gain_mVfC[self.instances_to_plot[i]]
			print len(ser)
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
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{G_{FE}} = %6.2f $' % (sermean[i]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
		plt.savefig(self.path + 'ANALYSIS/S-Curve_Gain_hist'+self.pltname+'.png', bbox_inches="tight");

		# FE Noise evolution #################################
		if multifile:
			plt.clf();
			w, h = plt.figaspect(1/6.0)
			fig = plt.figure(figsize=(w,h))
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(False)
			ax.spines["right"].set_visible(False)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
			x = np.array(range( min( len(noise[typcal][:,0]), len(THD_gain_array), len(FE_Gain_mVfC)))) * self.measure_rate
			plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
			plt.yticks(fontsize=16)
			plt.ylabel("Front-End Noise", fontsize=16)
			plt.xlabel(self.XLabel_Series, fontsize=16)
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
			noise_mean_smooth = interpolate.spline(x, noise_mean, xnew)
			noise_std_smooth = interpolate.spline(x, noise_std, xnew)
			noise_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 999, polyorder = 5)
			plt.fill_between(xnew, noise_hat - noise_std_smooth,  noise_hat + noise_std_smooth, color="#3F5D7D", alpha = 0.3)
			#plt.plot(x, noise_mean, color='#3F5D7D', lw=1)
			plt.plot(xnew, noise_hat, color='r', lw=1)
			plt.savefig(self.path + 'ANALYSIS/S-Curve_Noise_Mean'+self.pltname+'.png', bbox_inches="tight");

		# Noise #############################################
		plt.clf();
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Normalised distribution", fontsize=16)
		plt.xlabel('Noise [e-]', fontsize=16)
		bn = False
		FE_Gain_mVfC, THD_gain_array, CAL_gain_array, = self.Convert_ThDacCalDac_to_mVfC( np.ones(len(gains[0,:])) , return_vals = True)
		ser = []
		for i in range(len(self.instances_to_plot)):
			self.noise = noise
			dataset = np.array(noise[typcal])[self.instances_to_plot[i],:]
			print len(dataset)
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
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{noise} = %6.2f $' % (np.mean(ser[i])), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
		plt.savefig(self.path + 'ANALYSIS/S-Curve_Noise_hist'+self.pltname+'.png', bbox_inches="tight");

		plt.clf();
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		ax = fig.add_subplot(111, projection='3d')
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		#ax.get_yaxis().tick_left()
		plt.xticks(fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Normalised distribution", fontsize=16)
		plt.xlabel('Noise [e-]', fontsize=16)
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
		plt.savefig(self.path + 'ANALYSIS/S-Curve_Noise_hist'+self.pltname+'_3d.png', bbox_inches="tight");



		# FE threshold distribution ################################
		plt.clf();
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel("Normalised distribution", fontsize=16)
		plt.xlabel('Threshold', fontsize=16)
		bn = False
		ser = []
		for i in range(len(self.instances_to_plot)):
			dataset = np.array(thresholds[typcal])[self.instances_to_plot[i],:]
			print len(dataset)
			ser.append(dataset)
		bn = np.round(np.arange(np.min(ser)-2, np.max(ser)+3, 1))
		plt.xticks( bn, fontsize=16)
		plt.yticks(fontsize=16)
		sigma = []
		for i in range(len(self.instances_to_plot)):
			plt.hist(ser[i], normed = True, bins = bn, alpha = 0.7)
			xt = plt.xticks()[0] # find minimum and maximum of xticks to know where we should compute theoretical distribution
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(ser[i]))
			m, s = stats.norm.fit(ser[i]) # get mean and standard deviation
			sigma.append(s)
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			#plt.text(2011.5, 100 , 'mean noise pre-rad' , fontsize=16, color='r')
			plt.plot(lnspc, pdf_g, color = 'red' , label="Norm") # plot i
			plt.text(1, 1-(0.05*i), self.label[i] + r'  $\overline{\sigma} = %6.2f $' % (sigma[i]), horizontalalignment='right',verticalalignment='top', transform=ax.transAxes, fontsize=16, color='darkred')
			plt.savefig(self.path + 'ANALYSIS/S-Curve_Threshold_Std'+self.pltname+'.png', bbox_inches="tight");


	##############################################################################################

	def FE_Threshold_Trimming__Plot(self, filename = 'Init', plot = True):
		print '->  \tSearching for matching files'
		filename = filename + '*scurve_trim*_cal_*'
		files_list = self._get_files_list( filename, 'csv')
		if(len(files_list) == 0): return
		scurves = {}
		for f in files_list:
			cfl = re.findall( '\W?trim(\d+)_' , f )
			print cfl
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
		w, h = plt.figaspect(1/1.5)
		fig = plt.figure(figsize=(w,h))
		plt.style.use('seaborn-deep')
		color=iter(sns.color_palette('deep')) #iter(cm.summer(np.linspace(0,1, len(scurves) )))
		#plt.subplot(2, 1, 2)
		ax0 = plt.subplot(gs[1])
		ax0.spines["top"].set_visible(False); ax0.spines["right"].set_visible(False)
		ax0.get_xaxis().tick_bottom(); ax0.get_yaxis().tick_left()
		plt.xticks(fontsize=16); plt.yticks(fontsize=16)
		plt.xlim(min(bn), max(bn)); plt.ylim(0, 1100)
		for i in scurves:
			c=next(color)
			plt.plot( scurves[i] , color = c)
		#plt.subplot(2, 1, 1)
		ax1 = plt.subplot(gs[0])
		plt.xticks(fontsize=16); plt.yticks(fontsize=16)
		plt.xlim(min(bn), max(bn));
		ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)
		ax1.get_xaxis().tick_bottom(); ax1.get_yaxis().tick_left()
		for i in scurves:
			plt.hist(c_thresholds[i], normed = True, bins = bn, alpha = 0.7)
			xt = plt.xticks()[0]
			xmin, xmax = min(xt), max(xt)
			lnspc = np.linspace(xmin, xmax, len(c_thresholds[i]))
			m, s = stats.norm.fit(c_thresholds[i]) # get mean and standard deviation
			pdf_g = stats.norm.pdf(lnspc, m, s) # now get theoretical values in our interval
			xnew = np.linspace(np.min(lnspc), np.max(lnspc), 1000, endpoint=True)
			pdf_l = interpolate.spline(lnspc, pdf_g, xnew)
			plt.plot(xnew, pdf_l, 'r' , label="Norm") # plot i
		plt.savefig(self.path + 'ANALYSIS/S-Curve_Threshold_Trimming'+self.pltname+'.png', bbox_inches="tight");


	##############################################################################################

	def Power_AnalogParams_plot(self, filename = 'default', plot = True):
		print '->  \tSearching for matching files'
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

		plt.plot(xnew, interpolate.spline(x, PAVDD, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, PDVDD, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, PPVDD, xnew), color='r', lw=1)

		fig = plt.figure(figsize=(w,h))
		plt.plot(xnew, interpolate.spline(x, VBG, xnew), color='r', lw=1)

		fig = plt.figure(figsize=(w,h))
		plt.plot(xnew, interpolate.spline(x, Bias_D5BFEED, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, Bias_D5PREAMP, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, Bias_D5ALLV, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, Bias_D5ALLI, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, Bias_D5DAC8, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, GND, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, VBG, xnew), color='r', lw=1)
		plt.plot(xnew, interpolate.spline(x, Bias_BOOSTERBASELINE, xnew), color='r', lw=1)
		plt.show()

	def Power_plot(self, filename = 'default', plot = True, save = True):
		print '->  \tSearching for matching files'
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
		PAVDD_int = interpolate.spline(x, PAVDD, xnew)
		PDVDD_int = interpolate.spline(x, PDVDD, xnew)
		VBG_int   = interpolate.spline(x, VBG, xnew)
		self.PAVDD.append(PAVDD_int)
		self.PDVDD.append(PDVDD_int)
		self.VBG.append(VBG_int)
		self.pwr_x.append(xnew)
		c = next(color)
		plt.plot(xnew, PAVDD_int, color=c, lw=3)
		c = next(color)
		plt.plot(xnew, PDVDD_int, color=c, lw=3)
		#c = next(color)
		#plt.plot(xnew, VBG_int, color=c, lw=2)
		if save: plt.savefig(self.path + 'ANALYSIS/Power_'+self.pltname+'.png', bbox_inches="tight");

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
		plt.ylim(10, 35)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots-1, -1, -1):
			c = next(color);
			plt.plot(x, self.PAVDD[i][x], color=c, lw=3, alpha = 0.8)
			plt.plot(x, self.PDVDD[i][x], color=c, lw=3, alpha = 0.8)
			c = next(color);
		plt.savefig(self.path + 'ANALYSIS/Power'+self.pltname+'_multirun.png', bbox_inches="tight");
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(range(np.int(np.round(float(np.min(x))/10)*10), np.int(np.round(float(np.max(x))/10)*10) , 20), fontsize=16)
		plt.yticks(fontsize=16)
		plt.ylabel("Bandgap [mV]", fontsize=16)
		plt.ylim(240, 290)
		plt.xlabel(self.XLabel_Series, fontsize=16)
		color=iter(sns.color_palette('deep'))
		for i in range(nplots-1, -1, -1):
			c = next(color);
			plt.plot(x, self.VBG[i][x], color=c, lw=3, alpha = 0.8)
			c = next(color);
		plt.savefig(self.path + 'ANALYSIS/V_BG'+self.pltname+'_multirun.png', bbox_inches="tight");






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
		sl_mean = self._sliding_mean(gain_std , 1)
		sl_std  = self._sliding_mean(gain_mean , 1)
		# plt.fill_between(range(len(GAINs[0,:])), sl_mean - sl_std,  sl_mean + sl_std, color="#3F5D7D")
		plt.plot(x, GAINs, color="#3F5D7D", lw=3)
		plt.savefig(self.path + 'ANALYSIS/' + name + '_GAIN_Evolution'+self.pltname+'.png', bbox_inches="tight");

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
		plt.savefig(self.path + 'ANALYSIS/' + name + '_GAIN_Caracteristics.png', bbox_inches="tight");

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
		plt.savefig(self.path + 'ANALYSIS/' + name + '_GAIN_INLs'+self.pltname+'.png', bbox_inches="tight");


	##############################################################################################
	def noise_gain_multirun_plot(self, nplots):
		plt.clf();
		w, h = plt.figaspect(1/6.0)
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
			noise_mean_smooth = interpolate.spline(x, noise_mean[x], xnew)
			noise_std_smooth = interpolate.spline(x, noise_std[x], xnew)
			noise_mean_hat = scypy_signal.savgol_filter(x = noise_mean_smooth , window_length = 501, polyorder = 5)
			noise_std_hat = scypy_signal.savgol_filter(x = noise_std_smooth , window_length = 501, polyorder = 5)
			c = next(color)
			plt.fill_between(xnew, noise_mean_hat - noise_std_hat,  noise_mean_hat + noise_std_hat, alpha = 0.3, color = c)
			plt.plot(xnew, noise_mean_hat, lw=2, color = c)
			plt.savefig(self.path + 'ANALYSIS/S-Curve_Noise_Mean_DoubleRun'+self.pltname+'.png', bbox_inches="tight");


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
				print 'High Noise strip: ' + str(i) + '   ' + str(Sigma[i]) + '   ' +   str(DAC_Gain) + '   ' +   str(FE_Gain) +  '   ' +   str(Noise[i])
				print 'Average:          ' + '  '   + '   ' + str(np.mean(Sigma)) + '   ' +   str(np.mean(DAC_Gain)) + '   ' +   str(np.mean(FE_Gain)) +  '   ' +   str(np.mean(Noise))
		return Noise


	def Power(self, plot = True, evaluate = False, return_values = False):
		print 'TO DO'


	def _get_file_name(self, folder='default' , run_name='default'):
		if(run_name == 'default'):
			f = self.run_name
		if(folder == 'default'):
			r = self.path
		fi = r + str(f) + '_'
		return fi


	def _get_files_list(self, test_name, file_format = 'csv'):
		matchstr = self.run_name + '*' + '_' + test_name + '.' + file_format
		#print matchstr
		rp = fnmatch.filter( os.listdir( self.path ), matchstr)
		rp = sorted(rp)
		print '->  \tFound %d data files matching %s' % (len(rp), matchstr)
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
			self.pltname = ''
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
			self.pltname = '_Run2'
			self.label = [' Pre-Rad :', '100 Mrad :', '200 Mrad :']








	def __set_run_temperature(self):
		self.path =  '../../Desktop/aaa/SSA_Results/'








#relevant_path = '../../Desktop/aaa/prova'
#file_names = [fn for fn in os.listdir(relevant_path) if any(fn.endswith(ext) for ext in included_extensions)]
