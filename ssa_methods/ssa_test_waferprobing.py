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
		self.Configure(runtest='default')
		

	def Configure(self, DIR ='../SSA_Results/Wafer0/', runtest = 'default'):
		self.DIR = DIR
		self.dvdd_curr = self.dvdd
		if(runtest == 'default'):
			self.runtest.enable('Power')
			self.runtest.enable('Initialize')
			self.runtest.enable('Calibrate')
			self.runtest.enable('Bias')
			self.runtest.enable('alignment')
			self.runtest.enable('Lateral_In')
			self.runtest.enable('Cluster_Data')
			self.runtest.enable('Pulse_Injection')
			self.runtest.enable('L1_Data')
			self.runtest.enable('Memory')
			self.runtest.disable('noise_baseline')
			self.runtest.enable('trim_gain_offset_noise')
			self.runtest.enable('DACs')
			self.runtest.enable('Configuration')
		else:
			self.runtest = runtest

	def Run(self, chipinfo=''):

		## Setup log files #####################
		time_init = time.time()
		version = 0
		while(True):
			fo = (self.DIR + "/Chip_{c:s}_v{v:d}/timetag.log".format(c=str(chipinfo), v=version))
			if(os.path.isfile(fo)):
				version += 1
			else:
				curdir = fo[:fo.rindex(os.path.sep)]
				if not os.path.exists(curdir):
					os.makedirs(curdir)
				fp = open(fo, 'w')
				fp.write( utils.date_time('csv') + '\n')
				fp.close()
				break
		utils.print_info("->\tThe log files are located in {:s}/ \n".format(curdir))
		fo = curdir + "/Test_"
		
		## Main test routine ##################
		self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
		time.sleep(0.5)
		self.pwr.reset(False, 0)
		self.test_routine_power(        filename=fo, mode='_Reset')
		self.pwr.reset(False, 1)
		self.test_routine_power(        filename=fo, mode='_Enabled')
		self.test_routine_initialize(   filename=fo)
		self.test_routine_power(        filename=fo, mode='_Initialized')
		self.test_routine_measure_bias( filename=fo, mode='_Reset')
		self.test_routine_calibrate(    filename=fo)
		self.test_routine_power(        filename=fo, mode='_Calibrated')
		self.test_routine_measure_bias( filename=fo, mode='_Calibrated')
		self.test_routine_dacs(         filename=fo)
		self.test_routine_analog(       filename=fo)
		self.test_routine_stub_data(    filename=fo)
		self.test_routine_save_configuration(filename=fo)
		self.test_routine_L1_data(      filename=fo, vlist=[self.dvdd,1.2])

		## Save summary ######################
		self.summary.save(directory=self.DIR, filename=("Chip_{c:s}_v{v:d}/".format(c=str(chipinfo), v=version)), runname='')
		self.summary.display()
		self.ssa.pwr.off(display=False)



	def test_routine_power(self, filename = 'default', runname = '', mode = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Power') 
		while (en and wd < 3):
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
				utils.print_warning("X>\tpower measurements error. Reiterating...")
				wd +=1

	def test_routine_initialize(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Initialize')
		while (en and wd < 3):
			try:
				r1 = self.ssa.init(reset_board = True, reset_chip = True)
				self.summary.set('Initialize', str(r1), '', '',  runname)
				break
			except:
				utils.print_warning("X>\tInitializing SSA error. Reiterating...")
				wd +=1

	def test_routine_calibrate(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Calibrate') 
		while (en and wd < 3):
			try:
				r1 = self.biascal.calibrate_to_nominals(measure=False)
				self.summary.set('init', r1, '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias Calibration error. Reiterating...")
				wd +=1

	def test_routine_measure_bias(self, filename = 'default', runname = '', mode = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Bias') 
		while (en and wd < 3):
			try:
				r1 = self.biascal.measure_bias(return_data=True)
				for i in r1:
					self.summary.set( i[0]+mode, i[1], 'mV', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias measurements error. Reiterating...")
				print "X>  \tError in Bias test. Reiterating."
				wd +=1


	def test_routine_save_configuration(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Configuration')
		while (en and wd < 3):
			try:
				self.ssa.save_configuration(filename + 'configuration' + str(runname) + '.scv', display=False)
				break
			except:
				utils.print_warning("X>\tConfig registers save error. Reiterating...")
				wd +=1


	def test_routine_stub_data(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('alignment')
		while (en and wd < 3):
			try:
				self.fc7.reset(); time.sleep(0.1)
				r1,r2,r3,r4 = self.ssa.alignment_all(display = False)
				self.summary.set('alignment_cluster_data', r2, '', '',  runname)
				self.summary.set('alignment_lateral_input', r3, '', '',  runname)
				break
			except:
				utils.print_warning("X>\tAlignment test error. Reiterating...")
				wd +=1
		wd = 0
		en = self.runtest.is_active('Cluster_Data')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'digital', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_DigitalPulses',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with Digital Pulses test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tCluster Data with Digital Pulses test error. Reiterating...")
				wd +=1
		wd = 0
		en = self.runtest.is_active('Pulse_Injection')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'analog', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_ChargeInjection',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with ChargeInjection test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				break
			except:
				utils.print_warning("X>\tCluster Data with Charge Injection test error. Reiterating...")
				wd +=1


	def test_routine_L1_data(self, vlist = [1.0, 1.2], filename = '../SSA_Results/Chip0/Chip_0', runname = '', shift = [0,0,0,0,0,0,0]):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		memtest = False
		en = self.runtest.is_active('Memory') 
		while (en and wd < 3):
			try:
				memtest= True
				memres = {}
				for v in vlist:
					if(v != self.dvdd_curr):
						self.pwr.set_dvdd(v)
						self.dvdd_curr = v
						self.ssa.init(display=0)
					r1, r2 = self.test.memory(
						memory = [1,2], runname = str(v)+'V',
						latency = 199, display = 1, 
						file = filename, filemode = 'a')
					memres[v] = r1
					self.summary.set('Memory-1_{:s}V'.format(str(v)), r1, '%', '',  runname)
					self.summary.set('Memory-2_{:s}V'.format(str(v)), r2, '%', '',  runname)
				break
			except:
				utils.print_warning("X>\tMemory test error. Reiterating...")
				wd +=1
		wd  = 0
		en = self.runtest.is_active('L1_Data')
		while (en and wd < 3):
			try:
				if(not memtest): 
					for v in vlist: memres[v]=100
				self.summary.set('L1_data',   0, '%', '',  runname)
				self.summary.set('HIP_flags', 0, '%', '',  runname)
				for v in vlist:
					if(memres[v]==100):
						if(v != self.dvdd_curr):
							self.pwr.set_dvdd(v)
							self.dvdd_curr
							self.ssa.init(display=0)
						r1, r2 = self.test.l1_data_basic(
							mode = 'digital', runname =  str(v)+'V',
							shift = shift[5], filemode = 'a',
							file = filename)
						self.summary.set('L1_data',   r1, '%', '',  runname)
						self.summary.set('HIP_flags', r2, '%', '',  runname)
						break
				break
			except:
				utils.print_warning("X>\tL1_Data test error. Reiterating...")
				wd +=1


	def test_routine_dacs(self, filename, runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Bias_THDAC')
		while (en and wd < 3):
			try:
				self.thdac = self.measure.dac_linearity(name = 'Bias_THDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_THDAC_GAIN'    , self.thdac[0], '', '',  runname)
				self.summary.set('Bias_THDAC_OFFS'    , self.thdac[1], '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias_THDAC test error. Reiterating...")
				wd +=1
		wd = 0
		en = self.runtest.is_active('Bias_CALDAC')
		while (en and wd < 3):
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
		en = self.runtest.is_active('trim_gain_offset_noise') 
		while (en and wd < 3):
			try:
				rp = self.measure.scurve_trim_gain_noise(
					charge_fc_trim = 2.0,           # Input charge in fC
					charge_fc_test = 0.8,           # Input charge in fC
					threshold_mv_trim = 'default',  # Threshold in mV
					threshold_mv_test = 'default',  # Threshold in mV
					iterative_step_trim = 1,        # Iterative steps to acheive lower variability
					caldac = 'default',             # 'default' | 'evaluate' | value [gain, offset]
					thrdac = 'default',             # 'default' | 'evaluate' | value [gain, offset]
					nevents = 1000,                 # Number of calibration pulses
					plot = True,                    # Fast plot of the results
					filename = filename)

				if(rp): 
					utils.print_good( "->\tScurve trimming successfull. (Std={std:3.2f}lsb)".format(std=rp[1]));
					utils.print_good( "->\tScurve noise evaluation successfull. ({std:3.2f}lsb)".format(std=rp[6]));
					utils.print_good( "->\tScurve Gain and Offset evaluation successfull. g={g:3.2f} ofs=({of:3.2f})".format(g=rp[7], of=rp[8])); 
					utils.print_log(  "->\tAnalog test time = {t:7.2f}s".format(t=(time.time()-time_init))); time_init = time.time();
				else:   
					utils.print_error( "->\tScurve trimming error.")
					utils.print_error( "->\tScurve noise evaluation error.")
					utils.print_error( "->\tScurve Gain and Offset evaluation error.")

				self.summary.set("threshold_std_init",  rp[0], '', '', runname)
				self.summary.set("threshold_std_trim",  rp[1], '', '', runname) 
				self.summary.set("threshold_std_test",  rp[2], '', '', runname)   
				self.summary.set("threshold_mean_trim", rp[3], '', '', runname)   
				self.summary.set("threshold_mean_test", rp[4], '', '', runname) 
				self.summary.set("noise_mean_trim",     rp[5], '', '', runname)
				self.summary.set("noise_mean_test",     rp[6], '', '', runname)  
				self.summary.set("fe_gain_mean",        rp[7], '', '', runname)  
				self.summary.set("fe_offs_mean",        rp[8], '', '', runname)       
				break
			except:
				utils.print_warning("X>\tScurve measures test error. Reiterating...")
				wd +=1
		wd = 0

