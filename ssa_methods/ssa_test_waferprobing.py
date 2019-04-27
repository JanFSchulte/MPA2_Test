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
		self.config_file = ''; self.dvdd = 1.05; self.pvdd = 1.20; self.avdd = 1.20; #for the offset of the board
		self.filename = False
		self.Configure(False, 'default')

	def Configure(self, DIR = False, runtest = 'default'):
		self.DIR = DIR
		if(runtest == 'default'):
			self.runtest.enable('Power')
			self.runtest.enable('Initialize')
			self.runtest.enable('Calibrate')
			self.runtest.enable('Bias')
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
			self.runtest.enable('Bias_THDAC')
			self.runtest.enable('Bias_CALDAC')
			self.runtest.enable('Configuration')
		else:
			self.runtest = runtest

	def Run(self, chipinfo):
		time_init = time.time()
		fo = self.DIR
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir):
			os.makedirs(dir)

		# Enable supply and initialise
		self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
		time.sleep(0.5)

		self.test_routine_power(fo,'','_PowerOn')
		self.test_routine_initialize(fo)
		self.test_routine_power(fo,'','_Enabled')
		self.test_routine_measure_bias(fo,'','_Reset')
		self.test_routine_calibrate(fo)
		self.test_routine_measure_bias(fo,'','_Calibrated')

		self.summary.display()

		self.test_routine_parameters(filename = fo)
		self.test_routine_analog(filename = fo, runname = runname)
		self.test_routine_digital(filename = fo, runname = runname)
		self.test_routine_dacs(filename = fo, runname = runname)
		self.summary.display(runname)
		self.summary.save(fo, runname)
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)
		self.ssa.init(reset_board = True, reset_chip = False, display = False)


	def test_routine_power(self, filename = 'default', runname = '', mode = ''):
		wd = 0
		while self.runtest.is_active('Power') and wd < 3:
			try:
				[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.pwr.get_power(display=True, return_all = True)
				self.summary.set('V_DVDD'+mode, Vd, ' V', '',  runname)
				self.summary.set('V_AVDD'+mode, Va, ' V', '',  runname)
				self.summary.set('V_PVDD'+mode, Vp, ' V', '',  runname)
				self.summary.set('I_DVDD'+mode, Id, 'mA', '',  runname)
				self.summary.set('I_AVDD'+mode, Ia, 'mA', '',  runname)
				self.summary.set('I_PVDD'+mode, Ip, 'mA', '',  runname)
				break
			except:
				print "X>  \tError in Power test. Reiterating."
				wd +=1

	def test_routine_initialize(self, filename = 'default', runname = ''):
		wd = 0
		while self.runtest.is_active('Initialize') and wd < 3:
			try:
				r1 = self.ssa.init(reset_board = True, reset_chip = True)
				self.summary.set('Initialize', str(r1), '', '',  runname)
				break
			except:
				print "X>  \tError in Initializing SSA. Reiterating."
				wd +=1

	def test_routine_calibrate(self, filename = 'default', runname = ''):
		wd = 0
		while self.runtest.is_active('Calibrate') and wd < 3:
			try:
				r1 = self.biascal.calibrate_to_nominals(measure=False)
				self.summary.set('init', r1, '', '',  runname)
				break
			except:
				print "X>  \tError in Initializing SSA. Reiterating."
				wd +=1


	def test_routine_measure_bias(self, filename = 'default', runname = '', mode = ''):
		filename = self.summary.get_file_name(filename)
		wd = 0
		while self.runtest.is_active('Bias') and wd < 3:
			try:
				r1 = self.biascal.measure_bias(return_data=True)
				for i in r1:
					self.summary.set( i[0]+mode, i[1], 'mV', '',  runname)
				break
			except:
				print "X>  \tError in Bias test. Reiterating."
				wd +=1
		wd = 0

	def test_routine_get_calibration(self, filename = 'default', runname = ''):
		while self.runtest.is_active('Configuration') and wd < 3:
			try:
				self.ssa.save_configuration('../SSA_Results/' + filename + '_Configuration_' + str(runname) + '.scv', display=False)
				break
			except:
				print "X>  \tError in reading Config regs. Reiterating."
				wd +=1
		wd = 0
