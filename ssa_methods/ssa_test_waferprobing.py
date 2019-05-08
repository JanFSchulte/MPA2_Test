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
			self.runtest.enable('alignment')
			self.runtest.enable('Lateral_In')
			self.runtest.enable('Cluster_Data')
			self.runtest.enable('Pulse_Injection')
			self.runtest.enable('Cluster_Data2')
			self.runtest.enable('Memory_1')
			self.runtest.enable('Memory_2')
			self.runtest.enable('L1_data')
			self.runtest.disable('memory_vs_voltage')
			self.runtest.enable('threshold_trimming')
			self.runtest.enable('noise_baseline')
			self.runtest.enable('gain_offset_noise')
			self.runtest.enable('threshold_spread')
			self.runtest.enable('Bias_THDAC')
			self.runtest.enable('Bias_CALDAC')
			self.runtest.enable('Configuration')
		else:
			self.runtest = runtest

	def Run(self, chipinfo=''):
		time_init = time.time()
		fo = self.DIR
		#if(fo):
		#	dir = fo[:fo.rindex(os.path.sep)]
		#if not os.path.exists(dir):
		#	os.makedirs(dir)
		# Enable supply and initialise
		self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
		time.sleep(0.5)
		self.pwr.reset(False, 0)
		self.test_routine_power(fo,'','_Reset')
		self.pwr.reset(False, 1)
		self.test_routine_power(fo,'','_Enabled')
		self.test_routine_initialize(fo)
		self.test_routine_power(fo,'','_Initialized')
		self.test_routine_measure_bias(fo,'','_Reset')
		self.test_routine_dacs(fo, '')
		self.test_routine_calibrate(fo)
		self.test_routine_power(fo,'','_Calibrated')
		self.test_routine_measure_bias(fo,'','_Calibrated')
		self.test_routine_digital(fo, '')
		self.test_routine_dacs(fo, '')
		self.test_routine_analog(fo, '')

		self.summary.display()

		self.ssa.pwr.off()

		#self.test_routine_analog(filename = fo, runname = runname)
		#self.test_routine_dacs(filename = fo, runname = runname)
		#self.summary.display(runname)
		#self.summary.save(fo, runname)
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)
		#self.ssa.init(reset_board = True, reset_chip = False, display = False)


	def test_routine_power(self, filename = 'default', runname = '', mode = ''):
		wd = 0
		while self.runtest.is_active('Power') and wd < 3:
			try:
				[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.pwr.get_power(display=True, return_all = True)
				self.summary.set('V_DVDD'+mode, Vd, 'mV', '',  runname)
				self.summary.set('V_AVDD'+mode, Va, 'mV', '',  runname)
				self.summary.set('V_PVDD'+mode, Vp, 'mV', '',  runname)
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

	def test_routine_digital(self, filename = 'default', runname = '', shift = [0,0,0,0,0,0,0]):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		while self.runtest.is_active('alignment') and wd < 3:
			try:
				self.fc7.reset(); time.sleep(0.1)
				r1,r2,r3,r4 = self.ssa.alignment_all(display = False)
				self.summary.set('alignment_cluster_data', r2, '', '',  runname)
				self.summary.set('alignment_lateral_input', r3, '', '',  runname)
				if(r1 and r2 and r3 and r4):
					utils.print_good("->\tAlignment test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tAlignment test error. Reiterating...")
				wd +=1
		wd = 0
		while self.runtest.is_active('Cluster_Data') and wd < 3:
			try:
				r1 = self.test.cluster_data(mode = 'digital', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_DigitalPulses',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with Digital Pulses test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tCluster Data with Digital Pulses test error. Reiterating...")
				wd +=1
		wd = 0
		while self.runtest.is_active('Cluster_Data') and wd < 3:
			try:
				r1 = self.test.cluster_data(mode = 'analog', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_ChargeInjection',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with ChargeInjection test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tCluster Data with Charge Injection test error. Reiterating...")
				wd +=1
		wd = 0
		while self.runtest.is_active('L1_data') and wd < 3:
			try:
				#self.fc7.reset(); time.sleep(0.1)
				r1, r2 = self.test.l1_data_basic(mode = 'digital', shift = shift[5], file = filename, filemode = 'a', runname = runname)
				self.summary.set('L1_data',    r1, '%', '',  runname)
				self.summary.set('HIP_flags',  r2, '%', '',  runname)
				print "->  \tl1_data_basic Time = %7.2f" % (time.time() - time_init); time_init = time.time();
				break
			except:
				print "X>  \tError in l1_data_basic test. Reiterating."
				wd +=1
		wd = 0

	def test_routine_dacs(self, filename, runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		while self.runtest.is_active('Bias_THDAC') and wd < 3:
			try:
				self.thdac = self.measure.dac_linearity(name = 'Bias_THDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_THDAC_GAIN'    , self.thdac[0], '', '',  runname)
				self.summary.set('Bias_THDAC_OFFS'    , self.thdac[1], '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias_THDAC test error. Reiterating...")
				wd +=1
		wd = 0
		while self.runtest.is_active('Bias_CALDAC') and wd < 3:
			try:
				self.caldac = self.measure.dac_linearity(name = 'Bias_CALDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_CALDAC_GAIN'    , self.caldac[0], '', '',  runname)
				self.summary.set('Bias_CALDAC_OFFS'    , self.caldac[1], '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias_CALDAC test error. Reiterating...")
				wd +=1
		wd = 0


	def test_routine_analog(self, filename, runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0


		while self.runtest.is_active('threshold_trimming') and wd < 3:
			try:
				r1 = self.measure.scurve_trim(
						charge_fc = 2,             # Input charge in fC
						threshold_mv = 'default',  # Threshold in mV
						caldac = self.caldac,      # 'default' | 'evaluate' | value [gain, offset]
						thrdac = self.thdac,       # 'default' | 'evaluate' | value [gain, offset]
						nevents = 1000,            # Number of calibration pulses
						iterative_step = 2,        # Iterative steps to acheive lower variability
						plot = False,              # Fast plot of the results
						filename = filename)
				self.summary.set('ClusterData_ChargeInjection',  r1, '%', '',  runname)
				if(r1): utils.print_good( "->\tScurve trimming successfull. Std = {std:3.2f}lsb ({t:7.2f}s)".format(std=r1, t=(time.time()-time_init))); time_init = time.time();
				else:   utils.print_error("->\tScurve trimming error. ({t:7.2f}s)".format(t=(time.time()-time_init))); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tScurve trimming test error. Reiterating...")
				wd +=1
		wd = 0

		# while self.runtest.is_active('gain_offset_noise') and wd < 3 and wd < 3:
		# 	try:
		# 		#self.ssa.load_configuration(self.config_file, display = False)
		# 		r1, r2, r3, r4 = self.measure.gain_offset_noise(calpulse = 50, ret_average = True, plot = True, use_stored_data = False, file = filename, filemode = 'a', runname = runname)
		# 		self.summary.set('FE_gain'          , r1, 'ThDAC/CalDAC', '',  runname)
		# 		self.summary.set('FE_offset'        , r2, 'ThDAC'       , '',  runname)
		# 		self.summary.set('FE_noise_scurve'  , r3, 'ThDAC'       , '',  runname)
		# 		self.summary.set('FE_scurve_issues' , r4, 'list'        , '',  runname)
		# 		print "->  \tgain_offset_noise Time = %7.2f" % (time.time() - time_init); time_init = time.time();
		# 		break
		# 	except:
		# 		print "X>  \tError in gain_offset_noise test. Reiterating."
		# 		wd +=1
		# wd = 0
		# while self.runtest.is_active('threshold_spread') and wd < 3:
		# 	try:
		# 		r1 = self.measure.threshold_spread(calpulse = 50, use_stored_data = True, plot = True, file = filename, filemode = 'a', runname = runname)
		# 		self.summary.set('threshold std' , r1, 'ThDAC', '',  runname)
		# 		print "->  \tthreshold_spread Time = %7.2f" % (time.time() - time_init); time_init = time.time();
		# 		break
		# 	except:
		# 		print "X>  \tError in threshold_spread test. Reiterating."
		# 		wd +=1
		# wd = 0
