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

'''
It run most of tests on the SSA ASIC in ~2min.
This class is used in th ewafer probing mpl_toolkits

Example:
ssa_main_measure = SSA_Measurements_All()
ssa_main_measure.RUN()
'''
try:
	ssa
except:
	ssa = False

class SSA_Measurements_All():

	def __init__(self, tag="ChipN_0", runtest='default', directory='../SSA_Results/Wafer0/', chip = ssa, mode_2xSSA=False):
		self.mode_2xSSA = mode_2xSSA
		if(chip):
			self._init(chip)
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
		utils.print_info("->  The log files are located in {:s}/ \n".format(curdir))
		fo = curdir + "/Test_"
		utils.set_log_files(curdir+'/OperationLog.txt',curdir+'/ErrorLog.txt')

		## Main test routine ##################
		if(not self.mode_2xSSA):
			self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
			self.pwr.reset(False, 0)
			self.test_routine_power(        filename=fo, mode='reset')
			self.pwr.reset(False, 1)
			self.test_routine_power(        filename=fo, mode='startup')
			self.test_routine_initialize(   filename=fo)
			self.test_routine_power(        filename=fo, mode='uncalibrated')
		self.test_routine_measure_bias( filename=fo, mode='uncalibrated')
		self.test_routine_calibrate(    filename=fo)
		if(not self.mode_2xSSA):
			self.test_routine_power(        filename=fo, mode='calibrated')
		self.test_routine_measure_bias( filename=fo, mode='calibrated')
		self.test_routine_dacs(         filename=fo)
		self.test_routine_analog(       filename=fo)
		self.test_routine_save_config   (filename=fo)
		self.test_routine_L1_data(      filename=fo, vlist=[self.dvdd,1.2])
		self.test_routine_stub_data(    filename=fo)

		## Save summary ######################
		self.summary.save(directory=self.DIR, filename=("Chip_{c:s}_v{v:d}/".format(c=str(chip_info), v=version)), runname='')
		self.summary.display()
		if(not self.mode_2xSSA):
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
				self.summary.set('Initialize', int(r1), '', '',  runname)
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
				self.summary.set('Calibration', int(r1), '', '',  runname)
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
				print("X>  \tError in Bias test. Reiterating.")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_save_config(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Configuration')
		while (en and wd < 3):
			try:
				self.ssa.save_configuration(filename + 'configuration' + str(runname) + '.csv', display=False)
				utils.print_good("->  Config registers readout via I2C and saved corrrectly.")
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
				self.summary.set('alignment_cluster_data',  int(r2), '', '',  runname)
				self.summary.set('alignment_lateral_left',  int(r3), '', '',  runname)
				self.summary.set('alignment_lateral_right', int(r4), '', '',  runname)
				if(not r2): self.test_good = False
				break
			except  Exception as error:
				utils.print_warning("X>\tAlignment test error. Reiterating...")
				exc_info = sys.exc_info()
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('Cluster_Data')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'digital', nstrips='random', nruns = 100, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_DigitalPulses',  r1, '%', '',  runname)
				utils.print_good("->  Cluster Data with Digital Pulses test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				if(r1<100.0): self.test_good = False
				break
			except  Exception as error:
				utils.print_warning("X>\tCluster Data with Digital Pulses test error. Reiterating...")
				exc_info = sys.exc_info()
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('Pulse_Injection')
		while (en and wd < 3):
			try:
				r1 = self.test.cluster_data(mode = 'analog', lateral=0, nstrips='random', nruns = 100, shift='default', display=False, file=filename, filemode='a', runname=runname)
				self.summary.set('ClusterData_ChargeInjection',  r1, '%', '',  runname)
				utils.print_good("->  Cluster Data with ChargeInjection test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
				if(r1<100.0): self.test_good = False
				break
			except Exception as error:
				utils.print_warning("X>\tCluster Data with Charge Injection test error. Reiterating...")
				exc_info = sys.exc_info()
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_L1_data(self, vlist = [1.0, 1.2], filename = '../SSA_Results/Chip0/Chip_0', runname = '', shift = -1):
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
						#self.ssa.init(display=0)
					r1, r2 = self.test.BIST_LOOP(nruns=5, note='[DVDD={:5.5f}] '.format(v))
					#r1, r2 = self.test.memory(
					#	memory = [1,2], runname = str(v)+'V',
					#	latency = 199, display = 1,
					#	file = filename, filemode = 'a')
					memres[v] = [r1, r2]
					self.summary.set('Memory1_{:d}V'.format(int(v*1000)), r1, '%', '',  runname)
					self.summary.set('Memory2_{:d}V'.format(int(v*1000)), r2, '%', '',  runname)
					if(r1>0): self.test_good = False
					if(r2>0): self.test_good = False
				break
			except Exception as error:
				utils.print_warning("X>\tMemory test error. Reiterating...")
				exc_info = sys.exc_info()
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd  = 0
		en = self.runtest.is_active('L1_Data')
		#print(memres)

		while (en and wd < 3):
			try:
				self.pwr.set_dvdd(self.dvdd)
				self.ssa.init(reset_chip=1, display=0)
				self.summary.set('L1_data',   0, '%', '',  runname)
				self.summary.set('HIP_flags', 0, '%', '',  runname)
				if(memres[v]==[0,0]):
					print("->  L1 data test will run at DVDD={:1.3f}V".format(v))
					r1, r2, r3 = self.test.l1_data(
						mode = 'digital', runname =  str(v)+'V',
						shift = shift, filemode = 'a', file = filename)
					self.summary.set('L1_data',   r1, '%', '',  runname)
					self.summary.set('HIP_flags', r2, '%', '',  runname)
					if(r1<100): self.test_good = False
					if(r2<100): self.test_good = False
					break
				break
			except Exception as error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tL1_Data test error. Reiterating...")
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
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
			except Exception as error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tBias_THDAC test error. Reiterating...")
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
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
					utils.print_good( "->  Scurve FE Trim Std: {:7.3f} cnt (L)    {:7.3f} cnt (H)".format(rp[1], rp[2]));
					utils.print_good( "->  Scurve FE Noise:    {:7.3f} cnt (L)    {:7.3f} cnt (H)".format(rp[5], rp[6]));
					utils.print_good( "->  Scurve FE Gain:     {:7.3f} mV/fC".format(rp[8]));
					utils.print_good( "->  Scurve FE Offset:   {:7.3f} mV".format(rp[9]));
					utils.print_log(  "->  Analog test time:   {:7.2f} s".format((time.time()-time_init))); time_init = time.time();
				else:
					utils.print_error( "->  Scurve trimming error.")
					utils.print_error( "->  Scurve noise evaluation error.")
					utils.print_error( "->  Scurve Gain and Offset evaluation error.")

				self.summary.set("threshold_std_init",  str(rp[0]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_std_trim",  str(rp[1]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_std_test",  str(rp[2]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_mean_trim", str(rp[3]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_mean_test", str(rp[4]), 'cnt_thdac', '', runname)
				self.summary.set("noise_mean_trim",     str(rp[5]), 'cnt_thdac', '', runname)
				self.summary.set("noise_mean_test",     str(rp[6]), 'cnt_thdac', '', runname)
				self.summary.set("fe_gain_mean",        str(rp[8]), 'mV/fC'    , '', runname)
				self.summary.set("fe_offs_mean",        str(rp[9]), 'mV'       , '', runname)
				break
			except Exception as error:
				exc_info = sys.exc_info()
				utils.print_warning("X>\tScurve measures test error. Reiterating...")
				utils.print_warning("----------------------")
				print(Exception)
				print(error)
				traceback.print_exception(*exc_info)
				utils.print_warning("----------------------")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0

	def _init(self, chip):
		self.ssa = chip;
		self.I2C = chip.i2c;
		self.fc7 = chip.chip.fc7;
		self.cal = chip.cal;
		self.pwr = chip.pwr;
		self.biascal = chip.biascal;
		self.test = chip.test;
		self.measure = chip.measure;
		self.dvdd = 1.05; #for the offset of the board
		self.pvdd = 1.15;
		self.avdd = 1.20;
		self.thdac = False
		self.caldac = False
