from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.logs_utility import *
from collections import OrderedDict
from main import *
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
ssa_main_measure = main_ssa_test_3()
ssa_main_measure.RUN()
'''
try:
	ssa
except:
	ssa = False

class main_ssa_test_fast():

	def __init__(self, tag="ChipN_0", runtest='default', directory='../SSA_Results/TEST/', chip = ssa, mode_2xSSA=False):
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
			self.runtest.set_enable('Power', 'ON')
			self.runtest.set_enable('Initialize', 'ON')
			self.runtest.set_enable('Calibrate', 'ON')
			self.runtest.set_enable('Bias', 'ON')
			self.runtest.set_enable('alignment', 'ON')
			self.runtest.set_enable('Lateral_In', 'OFF')
			self.runtest.set_enable('Cluster_Data', 'ON')
			self.runtest.set_enable('Pulse_Injection', 'ON')
			self.runtest.set_enable('L1_Data', 'ON')
			self.runtest.set_enable('Memory', 'ON')
			self.runtest.set_enable('noise_baseline', 'OFF')
			self.runtest.set_enable('trim_gain_offset_noise', 'ON')
			self.runtest.set_enable('DACs', 'ON')
			self.runtest.set_enable('ADC', 'OFF')
			self.runtest.set_enable('Configuration', 'ON')
			self.runtest.set_enable('ring_oscillators', 'ON')
			self.runtest.set_enable('stub_l1_max_speed', 'ON')
		else:
			self.runtest = runtest


	def RUN(self, runname='default', write_header=True):
		if(not self.mode_2xSSA):
			self.test_good = True
			## Setup log files #####################
			if(runname=='default'): chip_info = self.tag
			else: chip_info = runname
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
			fo = curdir + "/Test_"
			utils.close_log_files()
			utils.set_log_files(curdir+'/OperationLog.txt',curdir+'/ErrorLog.txt')
			utils.print_info('==============================================')
			utils.print_info('TEST ROUTINE {:s}\n'.format(str(runname)))
			utils.print_info("->  The log files are located in {:s}/ \n".format(curdir))
			if(self.runtest.is_active('ADC', display=False)):
				self.ssa.biascal.SetMode('Keithley_Sourcemeter_2410_GPIB')
			## Main test routine ##################
			self.pwr.set_supply(mode='ON', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
			self.pwr.reset(False, 0)
			self.test_routine_power(filename=fo, mode='reset')
			self.ssa.reset(); time.sleep(1);
			self.ssa.resync(); time.sleep(0.1);
			self.test_routine_power(filename=fo, mode='startup')
			self.test_routine_initialize(filename=fo)
			self.test_routine_calibrate(filename=fo)
			self.test_routine_power(filename=fo, mode='calibrated')
			self.test_routine_measure_bias(filename=fo, mode='calibrated')
			self.test_routine_dacs(filename=fo)
			self.test_routine_analog(filename=fo)
			self.test_routine_save_config(filename=fo)
			self.test_routine_stub_data(filename=fo, samples=300, voltage=[1.0, 0.9, 1.1])
			self.test_routine_L1_data(filename=fo, samples=300, voltage=[1.0, 0.9, 1.1])
			self.test_routine_ring_oscillators(filename=fo)
			#self.finalize()
			## Save summary ######################
			self.summary.save(
				directory=self.DIR, filename=("Chip_{c:s}_v{v:d}/".format(c=str(chip_info), v=version)),
				runname='', write_header = write_header)
			self.summary.display()
			#utils.close_log_files()
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
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  power measurements error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_initialize(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Initialize')
		while (en and wd < 3):
			try:
				time.sleep(1)
				r1 = self.ssa.init()
				self.summary.set('Initialize', int(r1), '', '',  runname)
				if(not r1): self.test_good = False
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Initializing SSA error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_calibrate(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Calibrate')
		while (en and wd < 3):
			try:
				self.measure.adc.mesure_vref(filename=filename, runname='', chip='ADC_VREF/Test_')
				r1 = self.biascal.calibrate_to_nominals(measure=False)
				self.summary.set('Calibration', int(r1), '', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias Calibration error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_measure_bias(self, filename = 'default', runname = '', mode = '', nsamples=1000):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Bias')
		while (en and wd < 3):
			try:
				r1 = self.biascal.measure_bias(return_data=True)
				for i in r1:self.summary.set( i[0]+'_'+mode, i[1], 'mV', '',  runname)
				self.ssa.analog.adc_set_trimming(8)
				r2 = self.ssa.measure.adc.measure_param('DVDD', nsamples=nsamples, directory=filename)
				r3 = self.ssa.measure.adc.measure_param('VBG',  nsamples=nsamples, directory=filename)
				r4 = self.ssa.measure.adc.temperature_sensor( nsamples=nsamples, directory=filename)
				self.summary.set('adc_DVDD_mean' , r2[0], 'cnt', '',  runname)
				self.summary.set('adc_DVDD_std'  , r2[1], 'cnt', '',  runname)
				self.summary.set('adc_VBG_mean'  , r3[0], 'cnt', '',  runname)
				self.summary.set('adc_VBG_std'   , r3[1], 'cnt', '',  runname)
				self.summary.set('adc_TEMP_mean' , r4[0], 'cnt', '',  runname)
				self.summary.set('adc_TEMP_std'  , r4[1], 'cnt', '',  runname)

				#r2 = self.ssa.chip.analog.adc_measure_supply(nsamples=nsamples, raw=True)
				#self.summary.set('adc_DVDD', r2[0], 'cnt', '',  runname)
				#self.summary.set('adc_AVDD', r2[1], 'cnt', '',  runname)
				#self.summary.set('adc_PVDD', r2[2], 'cnt', '',  runname)
				#self.summary.set('adc_GND' , r2[3], 'cnt', '',  runname)
				#self.summary.set('adc_VBG' , r2[4], 'cnt', '',  runname)
				#self.summary.set('adc_TEMP', r2[5], 'cnt', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias measurements error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_save_config(self, filename = 'default', runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('Configuration')
		while (en and wd < 3):
			try:
				self.ssa.chip.ctrl.save_configuration(filename + 'configuration' + str(runname) + '.csv', display=False)
				utils.print_good("->  Config registers readout via I2C and saved corrrectly.")
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Config registers save error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False


	def test_routine_stub_data(self, filename = 'default', runname = '', samples=50, voltage='default'):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		if(voltage=='default'):
			voltage = [self.dvdd]
		for vvv in voltage:
			wd = 0
			en = self.runtest.is_active('alignment')
			while (wd < 3):
				try:
					self.pwr.set_dvdd(vvv); time.sleep(1)
					self.ssa.reset(); time.sleep(0.5)
					utils.print_info('->  DVDD set to {:0.3f}'.format(vvv))
					self.ssa.resync();
					r1,r2,r3,r4 = self.ssa.chip.alignment_all(display = False, lateral = False)
					if(en):
						self.summary.set('alignment_cluster_data_{:3.1f}'.format(vvv),  int(r2), '', '',  runname)
						self.summary.set('alignment_lateral_left_{:3.1f}'.format(vvv),  int(r3), '', '',  runname)
						self.summary.set('alignment_lateral_right_{:3.1f}'.format(vvv), int(r4), '', '',  runname)
					if(not r2):
						self.test_good = False
					break
				except(KeyboardInterrupt): break
				except:
					self.print_exception("->  Alignment test error. Reiterating...")
					wd +=1;
					if(wd>=3): self.test_good = False
			wd = 0
			en = self.runtest.is_active('Cluster_Data')
			while (en and wd < 3):
				try:
					self.ssa.resync();
					r1 = self.test.cluster_data(
						mode = 'digital', nstrips='random', nruns = samples, display=False,
						file=filename, filemode='a', runname=runname+'V{:0.1f}'.format(vvv), lateral=False)
					self.summary.set('ClusterData_DigitalPulses_{:3.1f}'.format(vvv),  r1, '%', '',  runname)
					if(r1<100.0):
						self.test_good = False
						utils.print_error("->  Cluster Data with Digital Pulses test NOT successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
					else:
						utils.print_good("->  Cluster Data with Digital Pulses test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
					break
				except(KeyboardInterrupt): break
				except:
					self.print_exception("->  Stub Data with Digital Pulses test error. Reiterating...")
					wd +=1;
					if(wd>=3): self.test_good = False
			wd = 0
			time.sleep(0.5)
			en = self.runtest.is_active('Pulse_Injection')
			while (en and wd < 3):
				try:
					self.ssa.resync();
					r1 = self.test.cluster_data(
						mode = 'analog', nstrips='random', nruns = samples, display=False,
						file=filename, filemode='a', runname=runname+'V{:0.1f}'.format(vvv), lateral=False)
					self.summary.set('ClusterData_ChargeInjection_{:3.1f}'.format(vvv),  r1, '%', '',  runname)
					if(r1<100.0):
						self.test_good = False
						utils.print_error("->  Cluster Data with ChargeInjection test NOT successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();
					else:
						utils.print_good("->  Cluster Data with ChargeInjection test successfull (%7.2fs)" % (time.time() - time_init)); time_init = time.time();

					break
				except(KeyboardInterrupt): break
				except:
					self.print_exception("->  Stub Data with Charge Injection test error. Reiterating...")
					wd +=1;
					if(wd>=3): self.test_good = False


	def test_routine_L1_data(self, filename = '../SSA_Results/Chip0/Chip_0', runname = '', shift = 1, samples=500, voltage='default'):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		if(voltage=='default'):
			voltage = [self.dvdd]
		for vvv in voltage:
			wd = 0
			memtest = False
			en = self.runtest.is_active('L1_Data')
			while (en and wd < 3):
				try:
					#self.pwr.set_dvdd(self.dvdd)
					self.pwr.set_dvdd(vvv); time.sleep(1)
					utils.print_info('->  DVDD set to {:0.3f}'.format(vvv))
					self.ssa.reset(); time.sleep(0.5)
					self.ssa.init(reset_chip=0, display=1); time.sleep(0.1)
					self.ssa.resync(); time.sleep(0.1);
					result = self.test.l1_data(
						mode = 'digital', runname =  runname+'V{:0.1f}'.format(vvv), nruns = samples,
						shift = shift, filemode = 'a', file = filename)
					r1, r2, r3 = result
					self.summary.set('L1_data_{:3.1f}'.format(vvv),   r1, '%', '',  runname)
					self.summary.set('HIP_flags_{:3.1f}'.format(vvv), r2, '%', '',  runname)
					self.summary.set('L1_headers_{:3.1f}'.format(vvv), r3, '%', '',  runname)
					if(r1<100): self.test_good = False
					if(r2<100): self.test_good = False
					break
				except(KeyboardInterrupt): break
				except:
					self.print_exception("->  L1_Data test error. Reiterating...")
					wd +=1;
					if(wd>=3): self.test_good = False
		for vvv in voltage:
			wd = 0
			memtest = False
			en = self.runtest.is_active('L1_Data')
			while (en and wd < 3):
				try:
					#self.pwr.set_dvdd(self.dvdd)
					self.pwr.set_dvdd(vvv); time.sleep(1)
					utils.print_info('->  DVDD set to {:0.3f}'.format(vvv))
					self.ssa.reset(); time.sleep(0.5)
					self.ssa.init(reset_chip=0, display=1); time.sleep(0.1)
					self.ssa.resync(); time.sleep(0.1);
					self.ssa.chip.ctrl.set_active_memory('latch', 'latch')
					time.sleep(0.1);
					result = self.test.l1_data(
						mode = 'digital', runname =  runname+'V{:0.1f}'.format(vvv), nruns = samples,
						shift = shift, filemode = 'a', file = filename)
					r1, r2, r3 = result
					self.summary.set('L1_data_latch_{:3.1f}'.format(vvv),   r1, '%', '',  runname)
					self.summary.set('HIP_flags_latch_{:3.1f}'.format(vvv), r2, '%', '',  runname)
					if(r1<100): self.test_good = False
					if(r2<100): self.test_good = False
					break
				except(KeyboardInterrupt): break
				except:
					self.print_exception("->  L1_Data test error. Reiterating...")
					wd +=1;
					if(wd>=3): self.test_good = False
		wd  = 0
		en = self.runtest.is_active('Memory')
		while (en and wd < 3):
			try:
				memtest= True
				results = self.test.SRAM_BIST_vs_DVDD(
					step=0.1, dvdd_max=1.3, dvdd_min=0.7, nruns_per_point=1, plot=False,
					filename = filename + '_memory_bist_vs_dvdd/', filemode='w', runname = runname)

				for v in results:
					self.summary.set('Memory1_{:5.3f}V'.format(v), results[v][0], '%', '',  runname)
					self.summary.set('Memory2_{:5.3f}V'.format(v), results[v][1], '%', '',  runname)
				if(results[1.0][0]<100): self.test_good = False
				if(results[1.0][1]<100): self.test_good = False
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Memory test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False



	def test_routine_ring_oscillators(self, filename = '../SSA_Results/Chip0/Chip_0', runname = '', shift = 0):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('ring_oscillators')
		while (en and wd < 3):
			try:
				results = self.test.ring_oscillators_vs_dvdd(
					dvdd_step=0.05, dvdd_max=1.3, dvdd_min=0.8, plot=False, printmode='log',
					filename = filename + '_ring_oscillator_vs_dvdd/', filemode='w', runname = '')

				self.summary.set('Ring_INV_BR', results[4][1], 'MHz', '',  runname)
				self.summary.set('Ring_INV_TR', results[4][2], 'MHz', '',  runname)
				self.summary.set('Ring_INV_BC', results[4][3], 'MHz', '',  runname)
				self.summary.set('Ring_INV_BL', results[4][4], 'MHz', '',  runname)
				self.summary.set('Ring_DEL_BR', results[4][5], 'MHz', '',  runname)
				self.summary.set('Ring_DEL_TR', results[4][6], 'MHz', '',  runname)
				self.summary.set('Ring_DEL_BC', results[4][7], 'MHz', '',  runname)
				self.summary.set('Ring_DEL_BL', results[4][8], 'MHz', '',  runname)
				self.pwr.set_dvdd(self.dvdd)
				time.sleep(1)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Ring Oscillators test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False




	def test_stub_l1_max_speed(self, filename = '../SSA_Results/Chip0/Chip_0', runname = '', compare_del = 74, run_time=5):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('stub_l1_max_speed')
		while (en and wd < 3):
			try:
				striplist, centroids, hip_hits, hip_flags  = self.test.generate_clusters(
					nclusters=8, min_clsize=1, max_clsize=2, smin=1,
					smax=119, HIP_flags=True)

				results = self.ssa.seuutil.Run_Test_SEU(
					check_stub=True, check_l1=True, check_lateral=False, create_errors = False,
					strip = striplist, centroids=centroids, hipflags = hip_hits, delay = compare_del, run_time = run_time,
					cal_pulse_period = 1, l1a_period = 39, latency = 501, display = 1, stop_if_fifo_full = 1)

				[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1] = results

				self.summary.set('stub_data_fast_err',   CL_er, 'cnt', '',  runname)
				self.summary.set('l1_data_fast_err',     L1_er, 'cnt', '',  runname)
				self.summary.set('l1_headers_fast_err',  LH_er, 'cnt', '',  runname)
				self.summary.set('stub_data_fast_ok',    CL_ok, 'cnt', '',  runname)
				self.summary.set('l1_data_fast_ok',      L1_ok, 'cnt', '',  runname)
				self.summary.set('l1_headers_fast_ok',   LH_ok, 'cnt', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Fast test with SEU state machine error. Reiterating...")
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
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias_THDAC test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		while (en and wd < 3):
			try:
				self.caldac = self.measure.dac_linearity(name = 'Bias_CALDAC', eval_inl_dnl = False, nbits = 8, npoints = 10, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_CALDAC_GAIN'    , self.caldac[0], '', '',  runname)
				self.summary.set('Bias_CALDAC_OFFS'    , self.caldac[1], '', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias_CALDAC test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0
		en = self.runtest.is_active('ADC')
		while (en and wd < 3):
			try:
				r_adc = self.measure.adc.measure_curve(nsamples=1, npoints=2**10, directory=(filename), plot=False)
				self.summary.set('ADC_GAIN'    , r_adc[0], '', '',  runname)
				self.summary.set('ADC_OFFS'    , r_adc[1], '', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias_ADC test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False

	def test_routine_temperature_sensor(self, filename, runname = ''):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		en = self.runtest.is_active('DACs')
		while (en and wd < 3):
			try:
				self.thdac = self.measure.adc.temperature_sensor(name = 'Bias_THDAC', eval_inl_dnl = False, nbits = 8, npoints = 1000, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_THDAC_GAIN'    , self.thdac[0], '', '',  runname)
				self.summary.set('Bias_THDAC_OFFS'    , self.thdac[1], '', '',  runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Bias_THDAC test error. Reiterating...")
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

				self.summary.set("threshold_std_init",  '{:7.6f}'.format(rp[0]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_std_trim",  '{:7.6f}'.format(rp[1]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_std_test",  '{:7.6f}'.format(rp[2]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_mean_trim", '{:7.6f}'.format(rp[3]), 'cnt_thdac', '', runname)
				self.summary.set("threshold_mean_test", '{:7.6f}'.format(rp[4]), 'cnt_thdac', '', runname)
				self.summary.set("noise_mean_trim",     '{:7.6f}'.format(rp[5]), 'cnt_thdac', '', runname)
				self.summary.set("noise_mean_test",     '{:7.6f}'.format(rp[6]), 'cnt_thdac', '', runname)
				self.summary.set("fe_gain_mean",        '{:7.6f}'.format(rp[8]), 'mV/fC'    , '', runname)
				self.summary.set("fe_offs_mean",        '{:7.6f}'.format(rp[9]), 'mV'       , '', runname)
				break
			except(KeyboardInterrupt): break
			except:
				self.print_exception("->  Scurve measures test error. Reiterating...")
				wd +=1;
				if(wd>=3): self.test_good = False
		wd = 0

	def print_exception(self, text='Exception'):
		utils.print_warning(text)
		self.exc_info = sys.exc_info()
		utils.print_warning("======================")
		exeptinfo = traceback.format_exception(*self.exc_info )
		for extx in exeptinfo:
			utils.print_warning(extx)
		utils.print_warning("======================")

	def finalize(self):
		while (wd < 3):
			try:
				self.pwr.set_dvdd(self.dvdd); time.sleep(1)
				self.ssa.reset(); time.sleep(1)
			except:
				wd +=1;

	def idle_routine(self, filename = 'default', runname = '', duration=5, voltage=1.0):
		# run all functional test with STUB at BX rate, L1 data at 1MHz
		# if during X-ray irradiation, this is running all time except
		# of when the other tests are running
		utils.print_info('==============================================')
		utils.print_info('IDLE ROUTINE {:s}\n'.format(str(runname)))
		wd=0
		while (wd < 3):
			try:
				self.pwr.set_dvdd(voltage); time.sleep(1)
				self.ssa.reset(); time.sleep(1)
				pwr = self.pwr.get_power()

				striplist, centroids, hip_hits, hip_flags  = self.test.generate_clusters(
					nclusters=8, min_clsize=1, max_clsize=2, smin=1,
					smax=119, HIP_flags=True)

				print(striplist)

				results = self.ssa.seuutil.Run_Test_SEU(
					check_stub=True, check_l1=True, check_lateral=False, create_errors = False, t1edge='falling',
					strip = striplist, centroids=centroids, hipflags = hip_hits, delay = 75, run_time = duration,
					cal_pulse_period = 1, l1a_period = 39, latency = 501, display = 1, stop_if_fifo_full = 1, show_every=-1)

				[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, alignment] = results
				fo = open(filename+'.csv', 'a')
				fo.write('\n{:16s},{:8.3f},{:8.3f},{:8.3f},{:10d},{:10d},{:10d},{:10d},{:10d},{:10d},{:10.3f}'.format(
					runname, pwr[0], pwr[1], pwr[2], CL_er, L1_er, LH_er, CL_ok, L1_ok, LH_ok, test_duration) )
				fo.close()
				break
			except(KeyboardInterrupt):
				utils.print_info("\n\n\nUser interrupt. The routine will stop at the end of the iteration.\n\n\n")
				return 'KeyboardInterrupt'
			except:
				self.print_exception(text="->  Error in Idle Routine.")
				wd +=1;
				if(wd>=3): self.test_good = False
		return 0

	def _init(self, chip):
		self.ssa = chip;
		self.I2C = chip.i2c;
		self.fc7 = chip.chip.fc7;
		self.cal = chip.cal;
		self.pwr = chip.pwr;
		self.biascal = chip.biascal;
		self.test = chip.test;
		self.measure = chip.measure;
		self.dvdd = 1.00; #for the offset of the board
		self.pvdd = 1.20;
		self.avdd = 1.20;
		self.thdac = False
		self.caldac = False
