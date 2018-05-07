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
import fnmatch
import re


class SSA_Analise_Test_results():

	def __init__(self, toptest, test, measure, biascal):
		self.test = test; self.measure = measure; self.toptest = toptest; self.biascal = biascal;
		self.config_file = '';
		self.path =  '../../Desktop/aaa/X-Ray/'
		self.run_name = 'X-Ray_C8_'

	def set_run_name(self, path, name):
		self.path = path
		self.run_name = name

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

	def DAC(self, name = 'CALDAC', plot = True):
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
		if(plot):
			plt.figure(1); plt.plot(DNLs  , 'o-')
			plt.figure(2); plt.plot(INLs  , 'o-')
			plt.figure(3); plt.plot(GAINs , 'o-')
			plt.figure(4); plt.plot(OFSs  , 'o-')
			plt.show()
		#return vals, DNLs, INLs, GAINs, OFSs

	def FE_Gain(self, plot = True, evaluate = False):
		thresholds = {}; sigmas = {};
		thmean = {}; sigmamean = {};

		if not evaluate: # load pre-computed results
			print '->  \tLoading results'
			calpulses = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_cal_values.csv')[:,1]
			for cal in calpulses:
				c_thresholds = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Threshold_cal_'+str(cal)+'.csv')
				c_sigmas     = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Noise_cal_'+str(cal)+'.csv')
				c_thmean     = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
				c_sigmamean  = CSV.csv_to_array(self.path + 'SUMMARY/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')
				thresholds[str(cal)] = c_thresholds[:, 1:(np.shape(c_thresholds)[1])]
				sigmas[str(cal)]     = c_sigmas[:, 1:(np.shape(c_sigmas)[1])]
				thmean[str(cal)]     = c_thmean[:, 1]
				sigmamean[str(cal)]  = c_sigmamean[:, 1]

		else: # load data and compute results
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
			print '->  \tFitting courves'
			CSV.array_to_csv( calpulses,  self.path + 'SUMMARY/S-Curve_cal_values.csv')

			for cal in calpulses:
				c_thresholds = []; c_sigmas = [];
				c_thmean = []; c_sigmamean = [];
				for st in scurve_table[str(cal)]:
					s = np.transpose(st)
					thround, p = self.measure.cal.evaluate_scurve_thresholds(scurve = s, nevents = 1000)
					c_thresholds.append( np.array(p)[:,1] ) #threshold per strip
					c_thmean.append( np.mean( np.array(p)[:,1] ) ) #threshold mean
					c_sigmas.append( np.array(p)[:,2] ) #noise per strip
					c_sigmamean.append( np.mean( np.array(p)[:,2] ) ) #noise mean
				thresholds[str(cal)] = c_thresholds
				sigmas[str(cal)] = c_sigmas
				thmean[str(cal)] = c_thmean
				sigmamean[str(cal)] = c_sigmamean
				CSV.array_to_csv(c_thresholds, self.path + 'SUMMARY/S-Curve_Threshold_cal_'+str(cal)+'.csv')
				CSV.array_to_csv(c_sigmas,     self.path + 'SUMMARY/S-Curve_Noise_cal_'+str(cal)+'.csv')
				CSV.array_to_csv(c_thmean,     self.path + 'SUMMARY/S-Curve_Threshold_Mean_cal_'+str(cal)+'.csv')
				CSV.array_to_csv(c_sigmamean,  self.path + 'SUMMARY/S-Curve_Noise_Mean_cal_'+str(cal)+'.csv')

		typcal = str(calpulses[int(len(calpulses)/2)])
		if(plot):
			plt.figure(1); plt.plot(thresholds[typcal])
			plt.figure(2); plt.plot(sigmas[typcal])
			plt.figure(3); plt.plot(thmean[typcal])
			plt.figure(4); plt.plot(sigmamean[typcal])

		return thresholds[typcal], sigmas[typcal], thmean[typcal], sigmamean[typcal]
		return thresholds, sigmas, thmean, sigmamean








#relevant_path = '../../Desktop/aaa/prova'
#file_names = [fn for fn in os.listdir(relevant_path) if any(fn.endswith(ext) for ext in included_extensions)]
