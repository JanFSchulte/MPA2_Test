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


class SSA_test_top():

	def __init__(self, ssa, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal;   self.pwr = pwr;   self.biascal = biascal;
		self.test = test; self.measure = measure;
		self.summary = results()
		self.runtest = RunTest('default')
		self.config_file = ''; self.dvdd = 1.05; self.pvdd = 1.20; #for the offset of the board
		self.filename = False


	def run_caracterization(self):
		self.initialise(filename)
		self.test_routine_main(filename, "")


	def configure_tests(self, runtest = 'default'):
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



	def initialise(self, file = False, plot = False):
		if (isinstance(file, str)):
			self.filename = file
		filename = self.filename
		if (not isinstance(filename, str)):
			print("Log file name not setup")
			return
		filename = '../SSA_Results/' + filename
		dir = filename[:filename.rindex(os.path.sep)]
		if not os.path.exists(dir):
			os.makedirs(dir)
		self.ssa.init(reset_board = True, reset_chip = True)
		self.biascal.calibrate_to_nominals()
		self.measure.scurve_trim(plot = plot, filename = file + '_Init')
		self.config_file = filename + '_Configuration_Init.scv'
		self.ssa.save_configuration(self.config_file, display=False)



	def test_routine_main(self, filename, runname = 'RUN1'):
		print('\n\n\n\n')
		print('========================================================')
		print('     STARTING TEST   ' + str(runname))
		print('========================================================')
		print('\n\n')
		time_init = time.time()
		#fo = "../SSA_Results/X-Ray/" + runname + '_' + utils.date_time() + '_X-Ray_'
		#if(self.config_file == ''):
		fo = '../SSA_Results/' + filename
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir):
			os.makedirs(dir)
		self.config_file = fo + '_Configuration_Init.scv'
		self.pwr.set_dvdd(self.dvdd)
		self.pwr.set_pvdd(self.pvdd)
		time.sleep(0.5)
		self.ssa.init(reset_board = True, reset_chip = False)
		time.sleep(0.5)
		self.ssa.load_configuration(self.config_file, display = False)
		time.sleep(0.5)
		self.test_routine_parameters(filename = fo, runname = runname)
		self.test_routine_analog(filename = fo, runname = runname)
		self.test_routine_digital(filename = fo, runname = runname)
		self.test_routine_dacs(filename = fo, runname = runname)
		self.summary.display(runname)
		self.summary.save(fo, runname)
		print('\n\n')
		print('========================================================')
		print("->  END TEST \tRun time = {:7.2f}".format( (time.time()-time_init) ) )
		print('========================================================')
		print('\n\n\n\n')
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)
		self.ssa.init(reset_board = True, reset_chip = False, display = False)



	def test_routine_parameters(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)
		wd = 0
		while self.runtest.is_active('Power') and wd < 3:
			try:
				[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.pwr.get_power(display=True, return_all = True)
				self.summary.set('P_DVDD', Pd, 'mW', '',  runname)
				self.summary.set('P_AVDD', Pa, 'mW', '',  runname)
				self.summary.set('P_PVDD', Pp, 'mW', '',  runname)
				self.summary.set('V_DVDD', Vd, 'mW', '',  runname)
				self.summary.set('V_AVDD', Va, 'mW', '',  runname)
				self.summary.set('V_PVDD', Vp, 'mW', '',  runname)
				self.summary.set('I_DVDD', Id, 'mW', '',  runname)
				self.summary.set('I_AVDD', Ia, 'mW', '',  runname)
				self.summary.set('I_PVDD', Ip, 'mW', '',  runname)
				break
			except:
				print("X>  \tError in Power test. Reiterating.")
				wd +=1
		wd = 0
		while self.runtest.is_active('Bias') and wd < 3:
			try:
				r1 = self.biascal.measure_bias(return_data=True)
				for i in r1:
					self.summary.set( i[0], i[1], 'mV', '',  runname)
				break
			except:
				print("X>  \tError in Bias test. Reiterating.")
				wd +=1
		wd = 0
		while self.runtest.is_active('Configuration') and wd < 3:
			try:
				self.ssa.save_configuration('../SSA_Results/' + filename + '_Configuration_' + str(runname) + '.scv', display=False)
				break
			except:
				print("X>  \tError in reading Config regs. Reiterating.")
				wd +=1
		wd = 0



	def test_routine_digital(self, filename = 'default', runname = '  0Mrad', shift = [0,0,0,0,0,0,0]):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		self.ssa.init(reset_board = True, reset_chip = False, display = False)
		wd = 0
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)
		#try:
		#	self.test.force_alinament()
		#except:
		#	print("X>  \tError in Initial Alinement")
		#print('start')

		while self.runtest.is_active('Lateral_In') and wd < 3:
			try:
				r1, r2 = self.test.lateral_input_phase_tuning(display=False, file = filename, filemode = 'a', runname = runname, shift = shift[6])
				self.summary.set('Lateral_In_L', r1, '', '',  runname)
				self.summary.set('Lateral_In_R', r2, '', '',  runname)
				print("->  \tlateral_input_phase_tuning test Time = {:7.2f}".format( (time.time()-time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in lateral_input_phase_tuning test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Cluster_Data') and wd < 3:
			try:
				r1, r2, r3 = self.test.cluster_data_basic(mode = 'digital', shift = shift[0], shiftL = shift[1], display=False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('Cluster_Data',         r1, '%', '',  runname)
				self.summary.set('Lateral_In_Clusters',  r2, '%', '',  runname)
				self.summary.set('Lateral_Out_Clusters', r3, '%', '',  runname)
				print("->  \tcluster_data_basic test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in cluster_data_basic test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Pulse_Injection') and wd < 3:
			try:
				r1, r2, r3 = self.test.cluster_data_basic(mode = 'analog',  shift = shift[2], shiftL = shift[3], display=False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('Pulse_Injection', r1, '%', '',  runname)
				print("->  \tPulse_Injection test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in Pulse_Injection test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Cluster_Data2') and wd < 3:
			try:
				r1 = self.test.cluster_data(mode = 'digital', nstrips = 3, shift = shift[0], display=False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('Cluster_Data2',  r1, '%', '',  runname)
				print("->  \tcluster_data_basic test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in Cluster_Data2 test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Memory_1') and wd < 3:
			try:
				r1 = self.test.memory(memory = 1, shift = shift[4], display= 0,  file = filename, filemode = 'a', runname = runname)
				self.summary.set('Memory_1', r1, '%', '',  runname)
				print("->  \tMemory_1 test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in Memory_1 test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Memory_2') and wd < 3:
			try:
				r1 = self.test.memory(memory = 2, shift = shift[4], display= 0,  file = filename, filemode = 'a', runname = runname)
				self.summary.set('Memory_2', r1, '%', '',  runname)
				print("->  \tMemory_2 test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in Memory_2 test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('L1_data') and wd < 3:
			try:
				r1, r2 = self.test.l1_data_basic(mode = 'digital', shift = shift[5], file = filename, filemode = 'a', runname = runname)
				self.summary.set('L1_data',    r1, '%', '',  runname)
				self.summary.set('HIP_flags',  r2, '%', '',  runname)
				print("->  \tl1_data_basic test Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in l1_data_basic test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('memory_vs_voltage') and wd < 3:
			try:
				time.sleep(0.1)
				self.test.memory_vs_voltage(memory = 2, step = 0.005, start = 1.2, stop = 0.90, latency = 200, shift = 0, file = filename, filemode = 'a', runname = runname)
				print("->  \tmemory_vs_voltage Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				self.pwr.set_dvdd(self.dvdd)
				break
			except:
				print("X>  \tError in memory_vs_voltage test. Reiterating.")
				wd +=1
		wd = 0


		while self.runtest.is_active('memory_vs_voltage') and wd < 3:
			try:
				time.sleep(0.1)
				self.test.memory_vs_voltage(memory = 1, step = 0.010, start = 1.1, stop = 0.90, latency = 200, shift = 0, file = filename, filemode = 'a', runname = runname)
				print("->  \t memory_vs_voltage Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				self.pwr.set_dvdd(self.dvdd)
				break
			except:
				print("X>  \tError in memory_vs_voltage test. Reiterating.")
				wd +=1
		wd = 0

		self.pwr.set_dvdd(self.dvdd)
		#self.summary.display(runname)
		#self.summary.save(filename, runname)


	def test_routine_analog(self, filename = 'default', runname = '  0Mrad'):

		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0

		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)

		while self.runtest.is_active('noise_baseline') and wd < 3:
			try:
				#self.ssa.load_configuration(self.config_file, display = False)
				r1, r2 = self.measure.baseline_noise(ret_average = True, plot = False, mode = 'all', filename = filename, runname = runname, filemode = 'a')
				self.summary.set('noise_baseline' , r1, 'LSB', '',  runname)
				self.summary.set('baseline_issues', r2, '#',   '',  runname)
				print("->  \tl1_data_basic Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in baseline_noise test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('gain_offset_noise') and wd < 3 and wd < 3:
			try:
				self.ssa.load_configuration(self.config_file, display = False)
				r1, r2, r3, r4 = self.measure.gain_offset_noise(calpulse = 50, ret_average = True, plot = False, use_stored_data = False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('gain'          , r1, 'ThDAC/CalDAC', '',  runname)
				self.summary.set('offset'        , r2, 'ThDAC'       , '',  runname)
				self.summary.set('noise_scurve'  , r3, 'ThDAC'       , '',  runname)
				self.summary.set('scurve_issues' , r4, 'list'        , '',  runname)
				print("->  \tgain_offset_noise Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in gain_offset_noise test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('threshold_spread') and wd < 3:
			try:
				r1 = self.measure.threshold_spread(calpulse = 50, use_stored_data = True, plot = False, file = filename, filemode = 'a', runname = runname)
				self.summary.set('threshold std' , r1, 'ThDAC', '',  runname)
				print("->  \tthreshold_spread Time = {:7.2f}".format( (time.time() - time_init) ))
				time_init = time.time();
				break
			except:
				print("X>  \tError in threshold_spread test. Reiterating.")
				wd +=1
		wd = 0


	def test_routine_dacs(self, filename = 'default', runname = '  0Mrad'):
		filename = self.summary.get_file_name(filename)
		time_init = time.time()
		wd = 0
		#self.ssa.init(reset_board = True, reset_chip = True)
		#self.ssa.load_configuration(self.config_file, display = False)

		while self.runtest.is_active('Bias_THDAC') and wd < 3:
			try:
				r1, r2, r3, r4 = self.measure.dac_linearity(name = 'Bias_THDAC', nbits = 8, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_THDAC_DNL'     , r1, '', '',  runname)
				self.summary.set('Bias_THDAC_INL'     , r2, '', '',  runname)
				self.summary.set('Bias_THDAC_GAIN'    , r3*1E3, '', '',  runname)
				self.summary.set('Bias_THDAC_OFFS'    , r4*1E3, '', '',  runname)
				break
			except:
				print("X>  \tError in Bias_THDAC test. Reiterating.")
				wd +=1
		wd = 0

		while self.runtest.is_active('Bias_CALDAC') and wd < 3:
			try:
				r1, r2, r3, r4 = self.measure.dac_linearity(name = 'Bias_CALDAC', nbits = 8, filename = filename, plot = False, filemode = 'a', runname = runname)
				self.summary.set('Bias_CALDAC_DNL'   , r1, '', '',  runname)
				self.summary.set('Bias_CALDAC_INL'   , r2, '', '',  runname)
				self.summary.set('Bias_CALDAC_GAIN'  , r3*1E3, '', '',  runname)
				self.summary.set('Bias_CALDAC_OFFS'  , r4*1E3, '', '',  runname)
				break
			except:
				print("X>  \tError in Bias_CALDAC test. Reiterating.")
				wd +=1
		wd = 0


	def idle_routine(self, filename = 'default', runname = ''):
		print('========================================================')
		print('     IDLE ROUTINE   ' + str(runname))
		r1, r2, r3 = [0]*3
		filename = self.summary.get_file_name('../SSA_Results/' + filename + '_IDLE')
		print(filename)
		try:
			time.sleep(0.1); r4, r5 = self.test.lateral_input_phase_tuning(display=False, file = '../SSA_Results/' + filename + '_lateral.csv', filemode = 'a', runname = runname + '_idle', shift = 0)
			time.sleep(0.1); r1 = self.test.cluster_data(mode = 'digital', nstrips = 3, shift = 0,  display=False, file = '../SSA_Results/' + filename + '_CL.csv', filemode = 'a', runname = runname + '_idle')
			time.sleep(0.1); r2, r3 = self.test.l1_data_basic(mode = 'digital', shift = 0, file = '../SSA_Results/' + filename + '_L1.csv', filemode = 'a', runname = runname + '_idle')
		except:
			print("X>  \tError in Idle Routine.")
		fo = open(filename+'.csv', 'a')
		fo.write('\n%16s,   %10.3f,   %10.3f,   %10.3f,' % (runname, r1, r2, r3))
		fo.close()
		print('========================================================')
