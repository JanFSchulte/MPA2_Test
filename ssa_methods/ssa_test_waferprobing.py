from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from collections import OrderedDict
from ssa_methods.main import *
import traceback

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_Measurements():

	def __init__(self, tag="ChipN_0", runtest='default', directory='../SSA_Results/Wafer0/'):
		self._init()
		self.summary = results()
		self.runtest = RunTest('default')
		self.tag = tag
		self.Configure(directory=directory, runtest=runtest)

	def Configure(self, directory = '../SSA_Results/Wafer0/', runtest = 'default'):
		self.DIR = directory
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

	def RUN(self, info='', chip='default'):
		self.test_good = True
		## Setup log files #####################
		if(chip=='default'): chip_info = self.tag
		else: chip_info = chip
		time_init = time.time()
		version = 0
		while(True):
			fo = (self.DIR + "/Chip_{c:s}_v{v:d}/timetag.log".format(c=str(chip_info), v=version))
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
		utils.set_log_files(curdir+'/OperationLog.txt',curdir+'/ErrorLog.txt')

		## Main test routine ##################
		self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
		self.pwr.reset(False, 0)
		self.test_routine_power(        filename=fo, mode='reset')
		self.pwr.reset(False, 1)
		self.test_routine_power(        filename=fo, mode='startup')
		self.test_routine_initialize(   filename=fo)
		self.test_routine_power(        filename=fo, mode='uncalibrated')
		self.test_routine_measure_bias( filename=fo, mode='uncalibrated')
		self.test_routine_calibrate(    filename=fo)
		self.test_routine_power(        filename=fo, mode='calibrated')
		self.test_routine_measure_bias( filename=fo, mode='calibrated')
		self.test_routine_dacs(         filename=fo)
		self.test_routine_analog(       filename=fo)
		self.test_routine_stub_data(    filename=fo)
		self.test_routine_save_config   (filename=fo)
		self.test_routine_L1_data(      filename=fo, vlist=[self.dvdd,1.2])

		## Save summary ######################
		self.summary.save(directory=self.DIR, filename=("Chip_{c:s}_v{v:d}/".format(c=str(chip_info), v=version)), runname='')
		self.summary.display()
		self.ssa.pwr.off(display=False)
		utils.close_log_files()
		return self.test_good



	def test_routine_power(self, filename = 'default', runname = '', mode = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Power')
		while (en and wd < 3):
			try:
				[st, Id, Ia, Ip] = self.pwr.test_power(display=True)
				self.summary.set('I_DVDD_'+mode, Id, 'mA', '',  runname)
				self.summary.set('I_AVDD_'+mode, Ia, 'mA', '',  runname)
				self.summary.set('I_PVDD_'+mode, Ip, 'mA', '',  runname)
				if(not st): self.test_good = False
				break
			except:
				utils.print_warning("X>\tpower measurements error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_initialize(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Initialize')
		while (en and wd < 3):
			try:
				r1 = self.ssa.init(reset_board = True, reset_chip = True)
				self.summary.set('Initialize', str(r1), '', '',  runname)
				if(not r1): self.test_good = False
				break
			except:
				utils.print_warning("X>\tInitializing SSA error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_calibrate(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Calibrate')
		while (en and wd < 3):
			try:
				r1 = self.biascal.calibrate_to_nominals(measure=False)
				self.summary.set('Calibration', r1, '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias Calibration error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_measure_bias(self, filename = 'default', runname = '', mode = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Bias')
		while (en and wd < 3):
			try:
				r1 = self.biascal.measure_bias(return_data=True)
				for i in r1:
					self.summary.set( i[0]+'_'+mode, i[1], 'mV', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias measurements error. Reiterating...")
				print "X>  \tError in Bias test. Reiterating."
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_save_config(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Configuration')
		while (en and wd < 3):
			try:
				self.ssa.save_configuration(filename + 'configuration' + str(runname) + '.scv', display=False)
				utils.print_good("->\tConfig registers readout via I2C and saved corrrectly.")
				break
			except:
				utils.print_warning("X>\tConfig registers save error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_stub_data(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('alignment')
		while (en and wd < 3):
			try:
				self.fc7.reset(); time.sleep(0.1)
				r1,r2,r3,r4 = self.ssa.alignment_all(display = False)
				self.summary.set('alignment_cluster_data',  r2, '', '',  runname)
				self.summary.set('alignment_lateral_left',  r3, '', '',  runname)
				self.summary.set('alignment_lateral_right', r3, '', '',  runname)
				if(not r2): self.test_good = False
				break
			except:
				utils.print_warning("X>\tAlignment test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('Cluster_Data')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'digital', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_DigitalPulses',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with Digital Pulses test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				if(r1<90): self.test_good = False
				break
			except:
				utils.print_warning("X>\tCluster Data with Digital Pulses test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('Pulse_Injection')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'analog', nstrips=8, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_ChargeInjection',  r1, '%', '',  runname)
				utils.print_good("->\tCluster Data with ChargeInjection test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				if(r1<90): self.test_good = False
				break
			except:
				utils.print_warning("X>\tCluster Data with Charge Injection test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False


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
					memres[v] = [r1, r2]
					self.summary.set('Memory-1_{:s}V'.format(str(v)), r1, '%', '',  runname)
					self.summary.set('Memory-2_{:s}V'.format(str(v)), r2, '%', '',  runname)
					if(r1<90): self.test_good = False
					if(r2<90): self.test_good = False
				break
			except Exception, error:
				utils.print_warning("X>\tMemory test error. Reiterating...")
				exc_info = sys.exc_info()
				utils.print_warning("----------------------")
				print Exception, error
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd  = 0
		en = self.runtest.is_active('L1_Data')
		while (en and wd < 3):
			try:
				self.summary.set('L1_data',   0, '%', '',  runname)
				self.summary.set('HIP_flags', 0, '%', '',  runname)
				for v in vlist:
					if(memres[v]==[100,100]):
						print("->\tL1 data test will run ad DVDD={:1.3f}V".format(v))
						if(v != self.dvdd_curr):
							self.pwr.set_dvdd(v)
							self.ssa.init(display=0)
						r1, r2 = self.test.l1_data_basic(
							mode = 'digital', runname =  str(v)+'V',
							shift = shift[5], filemode = 'a',
							file = filename)
						self.summary.set('L1_data',   r1, '%', '',  runname)
						self.summary.set('HIP_flags', r2, '%', '',  runname)
						if(r1<90): self.test_good = False
						if(r2<90): self.test_good = False
						break
				break
			except Exception, error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tL1_Data test error. Reiterating...")
				utils.print_warning("----------------------")
				print Exception, error
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_dacs(self, filename, runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('DACs')
		while (en and wd < 3):
			try:
				self.thdac = self.measure.dac_linearity(name = 'Bias_THDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_THDAC_GAIN'    , self.thdac[0], '', '',  runname)
				self.summary.set('Bias_THDAC_OFFS'    , self.thdac[1], '', '',  runname)
				break
			except Exception, error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tBias_THDAC test error. Reiterating...")
				utils.print_warning("----------------------")
				print Exception, error
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('DACs')
		while (en and wd < 3):
			try:
				self.caldac = self.measure.dac_linearity(name = 'Bias_CALDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_CALDAC_GAIN'    , self.caldac[0], '', '',  runname)
				self.summary.set('Bias_CALDAC_OFFS'    , self.caldac[1], '', '',  runname)
				break
			except:
				utils.print_warning("X>\tBias_CALDAC test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0


	def test_routine_analog(self, filename='../SSA_Results/Chip0/', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		if(self.thdac == False or self.caldac == False):
			self.test_routine_dacs(filename=filename)
		en = self.runtest.is_active('trim_gain_offset_noise')
		while (en and wd < 3):
			try:
				rp = self.measure.scurve_trim_gain_noise(
					charge_fc_trim = 2.5,           # Input charge in fC
					charge_fc_test = 1.2,           # Input charge in fC
					threshold_mv_trim = 'mean',  # Threshold in mV
					iterative_step_trim = 1,        # Iterative steps to acheive lower variability
					caldac = self.caldac,           # 'default' | 'evaluate' | value [gain, offset]
					thrdac = self.thdac,            # 'default' | 'evaluate' | value [gain, offset]
					nevents = 1000,                 # Number of calibration pulses
					plot = False,                    # Fast plot of the results
					filename = filename)

				if(rp):
					utils.print_good( "->\tScurve trimming successfull. (Std = [trim->{:3.2f}lsb, test->{:3.2f}lsb])".format(rp[1], rp[2]));
					utils.print_good( "->\tScurve noise evaluation successfull. (noise = [trim->{:3.2f}lsb, test->{:3.2f}lsb])".format(rp[5], rp[6]));
					utils.print_good( "->\tScurve Gain and Offset evaluation successfull. g={g:3.2f} ofs=({of:3.2f})".format(g=rp[7], of=rp[8]));
					utils.print_log(  "->\tAnalog test time = {t:7.2f}s".format(t=(time.time()-time_init))); time_init = time.time();
				else:
					utils.print_error( "->\tScurve trimming error.")
					utils.print_error( "->\tScurve noise evaluation error.")
					utils.print_error( "->\tScurve Gain and Offset evaluation error.")

				self.summary.set("threshold_std_init",  str(rp[0]), '', '', runname)
				self.summary.set("threshold_std_trim",  str(rp[1]), '', '', runname)
				self.summary.set("threshold_std_test",  str(rp[2]), '', '', runname)
				self.summary.set("threshold_mean_trim", str(rp[3]), '', '', runname)
				self.summary.set("threshold_mean_test", str(rp[4]), '', '', runname)
				self.summary.set("noise_mean_trim",     str(rp[5]), '', '', runname)
				self.summary.set("noise_mean_test",     str(rp[6]), '', '', runname)
				self.summary.set("fe_gain_mean",        str(rp[7]), '', '', runname)
				self.summary.set("fe_offs_mean",        str(rp[8]), '', '', runname)
				break
			except Exception, error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tScurve measures test error. Reiterating...")
				utils.print_warning("----------------------")
				print Exception, error
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0

	def _init(self):
		self.ssa = ssa;
		self.I2C = ssa_i2c;
		self.fc7 = ssa.fc7;
		self.cal = ssa_cal;
		self.pwr = ssa_pwr;
		self.biascal = ssa_biascal;
		self.test = ssa_test;
		self.measure = ssa_measure;
		self.dvdd = 1.05; #for the offset of the board
		self.pvdd = 1.20;
		self.avdd = 1.20;
		self.thdac = False
		self.caldac = False
