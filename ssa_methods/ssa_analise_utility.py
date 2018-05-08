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


class SSA_Analise_Test_results():

	def __init__(self, toptest, test, measure, biascal):
		self.test = test; self.measure = measure; self.toptest = toptest; self.biascal = biascal;
		self.config_file = '';
		self.path =  '../../Desktop/aaa/X-Ray_CHIP-C8_25C_200Mrad/'
		self.run_name = 'X-Ray_C8_'
		self.measure_rate = 1

	##############################################################################################

	def set_run_name(self, path, name, measure_rate = 1):
		self.path = path # the path of the data
		self.run_name = name # The initial part of the name of every SSA log
		self.measure_rate = measure_rate # for instance the X-Ray Dose Rate or Temperature Step



	def DAC_Gain_Ofs_Dnl_Inl(self, name = 'CALDAC', plot = True, return_values = False):
		DNLs, INLs, GAINs, OFSs = self.DAC_Gain_Ofs_Dnl_Inl__Calculate(name = name)
		if(plot):
			self.DAC_Gain_Ofs_Dnl_Inl__Plot(DNLs, INLs, GAINs, OFSs)
		if (return_values):
			return DNLs, INLs, GAINs, OFSs



	def FE_Gain_Noise_Std(self, plot = True, evaluate = False, return_values = False):
		if evaluate:
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean = self.FE_Gain_Noise_Std__Calculate()
		else:
			calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean = self.FE_Gain_Noise_Std__Reload()
		if(plot):
			self.FE_Gain_Noise_Std__Plot(calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean)
		if return_values:
			return thmean, sigmamean, gainmean, thresholds, noise, gains, gainmean
			#return thresholds[typcal], noise[typcal], thmean[typcal], sigmamean[typcal]


	##############################################################################################


	def FE_Gain_Noise_Std__Calculate(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print '->  \tSearching for matching files'
		fl = self.__get_file_name()
		files_list = self._get_files_list( 'scurve_trim__cal_' + '*', 'csv')
		calpulses = []; scurve_table = {};
		print '->  \tFound %d data files' % (len(files_list))

		print '->  \tSorting Informations'
		for f in files_list:
			cfl = re.findall( '\W?cal_(\d+)' , f )
			cal = np.int( cfl[0] )
			if not cal in calpulses:
				calpulses.append(cal)
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

		CSV.array_to_csv( calpulses,  self.path + 'SUMMARY/S-Curve_cal_values.csv')

		# Threshold spread and Noise
		print '->  \tFitting courves for Threshold-Spread and Noise'
		for cal in calpulses:
			c_thresholds = []; c_noise = [];
			c_thmean = []; c_sigmamean = [];
			for st in scurve_table[str(cal)]:
				s = np.transpose(st)
				thround, p = self.measure.cal.evaluate_scurve_thresholds(scurve = s, nevents = 1000)
				c_thresholds.append( np.array(p)[:,1] ) #threshold per strip
				c_thmean.append( np.mean( np.array(p)[:,1] ) ) #threshold mean
				c_noise.append( np.array(p)[:,2] ) #noise per strip
				c_sigmamean.append( np.mean( np.array(p)[:,2] ) ) #noise mean
			thresholds[str(cal)] = c_thresholds
			noise[str(cal)] = c_noise
			thmean[str(cal)] = c_thmean
			sigmamean[str(cal)] = c_sigmamean
			CSV.array_to_csv(c_thresholds, self.path + 'SUMMARY/S-Curve_Threshold_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_noise,     self.path + 'SUMMARY/S-Curve_Noise_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_thmean,     self.path + 'SUMMARY/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			CSV.array_to_csv(c_sigmamean,  self.path + 'SUMMARY/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')

		# FE Gain and offset
		print '->  \tEvaluating Front-End Gain'
		nelements = np.shape(thresholds[ str(calpulses[0])])[0]
		gains = np.zeros([120,nelements]);
		gainmean = np.zeros(nelements);

		#return thresholds, calpulses
		for s in range(0,120):
			ths = np.array( [np.array( thresholds[k] )[ : , s ] for k in thresholds if k in list(map(str, calpulses))] )
			for i in range( 0, nelements ):
				par, cov = curve_fit( f= f_line,  xdata = calpulses, ydata = ths[:, i], p0 = [0, 0])
				gains[s, i] = par[0]

		for i in range( 0, nelements ):
			gainmean[i] = np.average(gains[:, i] )

		CSV.array_to_csv(gains, self.path    + 'SUMMARY/S-Curve_Gain.csv')
		CSV.array_to_csv(gainmean, self.path + 'SUMMARY/S-Curve_Gain_Mean.csv')

		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean



	def FE_Gain_Noise_Std__Reload(self):
		thresholds = {}; noise = {};
		thmean = {}; sigmamean = {};
		print '->  \tLoading results'
		calpulses = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_cal_values.csv')[:,1]
		c_gains = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Gain.csv')
		gainmean = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Gain_Mean.csv')[:,1]
		gains = c_gains[:, 1:(np.shape(c_gains)[1])]
		for cal in calpulses:
			c_thresholds = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Threshold_cal_'+str(cal)+'.csv')
			c_noise     = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Noise_cal_'+str(cal)+'.csv')
			c_thmean     = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
			c_sigmamean  = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
			thresholds[str(cal)] = c_thresholds[:, 1:(np.shape(c_thresholds)[1])]
			noise[str(cal)]     = c_noise[:, 1:(np.shape(c_noise)[1])]
			thmean[str(cal)]     = c_thmean[:, 1]
			sigmamean[str(cal)]  = c_sigmamean[:, 1]
		return calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean



	def FE_Gain_Noise_Std__Plot(self, calpulses, thresholds, noise, thmean, sigmamean, gains, gainmean):
		typcal = str(calpulses[int(len(calpulses)/2)])
		#plt.figure(1); plt.plot(thresholds[typcal])
		#plt.figure(2); plt.plot(noise[typcal])
		#plt.figure(3); plt.plot(thmean[typcal])
		#plt.figure(4); plt.plot(sigmamean[typcal])
		#plt.figure(5); plt.plot(np.transpose(gains) )
		#plt.figure(6); plt.plot(gainmean)

		plt.figure(1) # FE Gain
		plt.figure(figsize=(12, 9))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylim(0.5, 1.5)
		x = np.array(range(len(gains[0,:]))) * self.measure_rate
		gain_mean = np.array([np.mean(gains[:,i]) for i in x])
		gain_std  = np.array([ np.std(gains[:,i]) for i in x])
		sl_mean = self._sliding_mean(gain_std , 1)
		sl_std  = self._sliding_mean(gain_mean , 1)
		plt.fill_between(x, gain_mean - gain_std,  gain_mean + gain_std, color="#3F5D7D")
		# plt.fill_between(range(len(gains[0,:])), sl_mean - sl_std,  sl_mean + sl_std, color="#3F5D7D")
		plt.plot(x, gain_mean, color="white", lw=3)
		plt.show()



	##############################################################################################


	def DAC_Gain_Ofs_Dnl_Inl__Calculate(self, name = 'CALDAC'):
		fl = self.__get_file_name()
		files_list = self._get_files_list( 'DNL_INL_Bias_' + name + '.csv', 'csv')
		vals = []; DNLs = []; INLs = []; GAINs = []; OFSs = []; nbits = 8
		for filename in files_list:
			tmp = CSV.csv_to_array( self.path + filename )
			vals.append(tmp)
		for v in vals:
			dnl, inl = self.biascal._dac_dnl_inl(data = v[:,1], nbits = 8, plot = False)
			inl_max = np.max(np.abs(inl))
			dnl_max = np.max(np.abs(dnl))
			gain, ofs, sigma = utils.linear_fit(range(0,2**nbits), v[:,1])
			gain *= 1E3; ofs *= 1E3
			DNLs.append(dnl_max)
			INLs.append(inl_max)
			GAINs.append(gain)
			OFSs.append(ofs)
		CSV.array_to_csv(DNLs,  self.path + 'SUMMARY/' + name + '_DNL.csv')
		CSV.array_to_csv(INLs,  self.path + 'SUMMARY/' + name + '_INL.csv')
		CSV.array_to_csv(GAINs, self.path + 'SUMMARY/' + name + '_GAIN.csv')
		CSV.array_to_csv(OFSs,  self.path + 'SUMMARY/' + name + '_OFS.csv')
		return DNLs, INLs, GAINs, OFSs


	def DAC_Gain_Ofs_Dnl_Inl__Plot(self, DNLs, INLs, GAINs, OFSs):
		plt.figure(1); plt.plot(DNLs  , 'o-')
		plt.figure(2); plt.plot(INLs  , 'o-')
		plt.figure(3); plt.plot(GAINs , 'o-')
		plt.figure(4); plt.plot(OFSs  , 'o-')
		plt.show()
		#return vals, DNLs, INLs, GAINs, OFSs

	##############################################################################################







	def Power(self, plot = True, evaluate = False, return_values = False):
		print 'TO DO'




	def __get_file_name(self, folder='default' , run_name='default'):
		if(run_name == 'default'):
			f = self.run_name
		if(folder == 'default'):
			r = self.path
		fi = r + str(f) + '_'
		return fi

	def _get_files_list(self, test_name, file_format = 'csv'):
		matchstr = self.run_name + '_' + '*' + '_' + test_name + '.' + file_format
		#print matchstr
		rp = fnmatch.filter( os.listdir( self.path ), matchstr)
		rp = sorted(rp)
		return rp



#################################################################

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





#relevant_path = '../../Desktop/aaa/prova'
#file_names = [fn for fn in os.listdir(relevant_path) if any(fn.endswith(ext) for ext in included_extensions)]
