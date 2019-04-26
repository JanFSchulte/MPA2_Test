from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from collections import OrderedDict

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_ProbeMeasurement():

	def __init__(self, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure;
		self.summary = results()
		self.runtest = RunTest('default')
		self.config_file = ''; self.dvdd = 1.05; self.pvdd = 1.20; #for the offset of the board
		self.filename = False

	def Configure(self, DIR, runtest = 'default'):
		self.DIR = DIR
		if(runtest == 'default'):
			self.runtest.enable('Lateral_In')
			self.runtest.enable('Cluster_Data')
			self.runtest.enable('Pulse_Injection')
			self.runtest.enable('Cluster_Data2')
			self.runtest.enable('Memory_1')
			self.runtest.enable('Memory_2')
			self.runtest.enable('L1_data')
			self.runtest.disable('memory_vs_voltage')
			self.runtest.enable('noise_baseline')
			self.runtest.enable('gain_offset_noise')
			self.runtest.enable('threshold_spread')
			self.runtest.enable('Power')
			self.runtest.enable('Bias')
			self.runtest.enable('Bias_THDAC')
			self.runtest.enable('Bias_CALDAC')
			self.runtest.enable('Configuration')
		else:
			self.runtest = runtest


	def Run(self, chipinfo):
		time_init = time.time()
		#fo = "../SSA_Results/X-Ray/" + runname + '_' + utils.date_time() + '_X-Ray_'
		#if(self.config_file == ''):
		fo = self.DIR
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir):
			os.makedirs(dir)

		self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=d=self.avdd, p=self.pvdd)
		time.sleep(0.5)
		self.ssa.init(reset_board = True, reset_chip = True)
		time.sleep(0.5)

		self.test_routine_parameters(filename = fo)
		self.test_routine_analog(filename = fo, runname = runname)
		self.test_routine_digital(filename = fo, runname = runname)
		self.test_routine_dacs(filename = fo, runname = runname)
		self.summary.display(runname)
		self.summary.save(fo, runname)
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)
		self.ssa.init(reset_board = True, reset_chip = False, display = False)
