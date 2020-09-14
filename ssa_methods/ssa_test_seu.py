import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import ctypes
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import fnmatch
import re
import traceback

from collections import OrderedDict
from functools import reduce
from pandas.core.common import flatten as pandas_flatten
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from ssa_methods.ssa_logs_utility import *
from utilities.tbsettings import *

class SSA_SEU():

	def __init__(self, ssa, seuutil, I2C, fc7, cal, biascal, pwr, test, measure):
		self.ssa = ssa;	  self.I2C = I2C;	self.seuutil = seuutil; self.fc7 = fc7; self.cal = cal;
		self.pwr = pwr;   self.test = test; self.biascal = biascal; self.measure = measure;
		self.init_parameters()

	##############################################################
	def main_test(self, niterations=16, run_time=30, memory_select='SRAM', delay_adjust=0):
		self.run_time = run_time
		self.set_info()
		self.time   = utils.date_time()
		self.filename = "SEU_SSA_" + self.time + "__Ion-" + self.ion + "__Tilt-" + str(self.tilt) + "__Flux-" + str(self.flux) + "__"
		self.seu_test(
			filename=self.filename, folder=self.folder, niterations=niterations,
			memory_select=memory_select, delay_adjust=delay_adjust)

	##############################################################
	def seu_test(self, filename = 'Try', folder = 'PROVA0', niterations=16, memory_select='SRAM', delay_adjust=0):
		print(folder)
		runname = self.run_info()
		logfile = folder + filename + '__full.log'
		errfile = folder + filename + '__errors.log'
		summary = folder + filename + '__summary.csv'
		stublog = folder + '/CL-FIFO/'+ filename +'__'+str(runname)+'__'
		l1dtlog = folder + '/L1-FIFO/'+ filename +'__'+str(runname)+'__'
		conflog = folder + '/CONFIG/' + filename +'__'+str(runname)+'__'
		utils.set_log_files(logfile, errfile)
		starttime=time.time()
		compare_del = 74+delay_adjust
		for latency in self.l1_latency:
			if(self.terminate): break
			#striplist = []
			#stavailable = range(1,121)
			for iteration in list(range(niterations)):
				if(self.terminate): break
				wd=0
				while (wd < 3):
					try:
						self.ssa.reset(display = False)
						init_time = time.time();
						start_date_time = utils.date_and_time()
						time.sleep(0.2); #after reset
						self.ssa.ctrl.load_basic_calib_configuration(strips=[], peri=True, display=0)
						self.ssa.ctrl.set_active_memory(memory_select, memory_select)
						#self.ssa.init(edge = 'negative', display = False)
						#self.test.lateral_input_phase_tuning(shift = 1)
						#stavailable = [x for x in stavailable if x not in striplist]
						#striplist = sorted(random.sample(stavailable, 7))
						#hipflags  = sorted(random.sample(striplist, np.random   ))
						striplist, centroids, hip_hits, hip_flags  = self.test.generate_clusters(
							nclusters=8, min_clsize=1, max_clsize=2, smin=1,
							smax=119, HIP_flags=True)

						self.ssa.ctrl.read_seu_counter(display=False, return_rate=True) #only to initialize timer for rate calculation

						results = self.seuutil.Run_Test_SEU(
							check_stub=True, check_l1=True, check_lateral=False, create_errors = False,
							strip = striplist, centroids=centroids, hipflags = hip_hits, delay = compare_del, run_time = self.run_time,
							cal_pulse_period = 1, l1a_period = 39, latency = latency, display = 1, stop_if_fifo_full = 1)

						utils.print_info("->  Active strips     -> " + str(striplist))
						utils.print_info("->  HIP strips        -> " + str(hip_hits))
						utils.print_info("->  L1 Latency        -> " + str(latency))

						time_since_reset = time.time()-init_time

						seucounter = self.ssa.ctrl.read_seu_counter(display=True, return_short_array=True, printmode='info')

						self.seuutil.Stub_ReadFIFOs( nevents = 'all', filename = stublog +str(iteration))

						self.seuutil.L1_ReadFIFOs( nevents = 'all', filename = l1dtlog +str(iteration))

						conf_p_er, conf_s_er = self.check_configuration(
							filename = (conflog + str(iteration)),
							active_strip_list = striplist, active_HIP_list = hip_hits,
							latency = latency, memory_select=memory_select)

						self.write_summary(
							summary, results, striplist, hip_hits, time_since_reset, seucounter, iteration,
							latency, runname,  conf_p_er,  conf_s_er, memory_select, start_date_time)

						utils.print_log('->  Total time since the start of testing is {:s}'.format(utils.time_delta(time_init=starttime) ))
						break
					except(KeyboardInterrupt):
						utils.print_warning("\n->  Keyboard Interrupt request. Exiting SEU test procedure.")
						self.terminate = True
						break
					except:
						utils.print_warning("\n\nX>  Exception.. Reiterating..." + str(wd))
						self.exc_info = sys.exc_info()
						utils.print_warning("======================")
						exeptinfo = traceback.format_exception(*self.exc_info )
						for extx in exeptinfo:
							utils.print_warning(extx)
						utils.print_warning("======================")
						self.fc7.reset(); time.sleep(0.1)
						self.fc7.reset(); time.sleep(0.1)
						wd +=1;
		utils.print_good('->  SEE test procedure completed! (total time: {:s})'.format(utils.time_delta(time_init=starttime) ))


	##############################################################
	def seucounter_try(self, iterations = 1000):
		curtime = time.time()
		for i in range(iterations):
			cnt = self.ssa.ctrl.read_seu_counter()
			print("->  %10.6f -> %3d" % ( (time.time()-curtime), cnt))

	##############################################################
	def check_configuration(self, filename = '../SSA_Results/SEU/test', active_strip_list = [], active_HIP_list = [], latency = 500, memory_select='SRAM'):
		#t = time.time()
		utils.print_info("->  Saving configuration to " + str(filename))

		conf_new = self.ssa.ctrl.save_configuration(
			rtarray = True, display=False, strip_list = 'all',
			file = (filename+'__configuration.scv'),
			notes = [['note','active_strip_and_HIPs','[{:s}] - [{:s}]'.format(
				', '.join(map(str, active_strip_list)), ', '.join(map(str, active_HIP_list))   ) ]] )

		utils.print_info("->  Reading default configuration ")
		conf_ref = self.ssa.ctrl.load_configuration(
			rtarray = True, display=False, upload_on_chip = False,
			file = 'ssa_methods/Configuration/ssa_configuration_base_calib_v{:d}.csv'.format(tbconfig.VERSION['SSA']))
		ctrl_3_val = latency & 0x00ff
		if(memory_select == 'LATCH'):
			ctrl_1_val = ((latency&0x0100)>>4)|0b01100100
		else:
			ctrl_1_val = ((latency&0x0100)>>4)|0b00000100
		conf_ref = self.ssa.ctrl._change_config_value(field='StripControl1',     new_value=0b00001001,  conf=conf_ref, strips=active_strip_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='DigCalibPattern_L', new_value=0b00000001,  conf=conf_ref, strips=active_strip_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='DigCalibPattern_H', new_value=0b00000001,  conf=conf_ref, strips=active_HIP_list )
		conf_ref = self.ssa.ctrl._change_config_value(field='control_1',         new_value=ctrl_1_val,  conf=conf_ref, strips=[-1] )
		conf_ref = self.ssa.ctrl._change_config_value(field='control_3',         new_value=ctrl_3_val,  conf=conf_ref, strips=[-1] )

		utils.print_info("->  Comparing configuration")
		error = self.ssa.ctrl.compare_configuration(conf_new, conf_ref)
		#print(time.time() - t)
		peri_er = bool(error[0])
		strip_er = not all(v == 0 for v in error[1:])
		if(peri_er):
			utils.print_error("->  SEU Configuration -> Error in Periphery configuration")
		if(strip_er):
			utils.print_error("->  SEU Configuration -> Error in Strip configuration")
		if(not peri_er and not strip_er):
			utils.print_good("->  SEU Configuration -> Correct")
		return peri_er, strip_er

	##############################################################
	def set_info(self):
		self.ion    = input("Ion    : ")
		self.tilt   = input("Angle  : ")
		self.flux   = input("Flux : ")
		self.folder = "../SSA_Results/SEU_Results/" + "Ion-" + self.ion + "__Tilt-" + str(self.tilt) + "__Flux-" + str(self.flux) + '/'
		if not os.path.exists(self.folder):
			os.makedirs(self.folder)

	##############################################################
	def write_summary(self, summary, results, striplist, hip_hits, time_since_reset, seucounter, iteration, latency, runname, conf_p_er,  conf_s_er, memory, start_time):
		striplist.extend([0]*(8-len(striplist)))
		hip_hits.extend([0]*(8-len(hip_hits)))
		utils.print_log('->  Writing summary')
		[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1]  = results
		logdata = list(pandas_flatten([
			runname, iteration, start_time,  time_since_reset, test_duration, latency, memory,
			CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, conf_p_er,  conf_s_er, fifo_full_stub, fifo_full_L1,
			seucounter, list(striplist), list(hip_hits),
			]))
		header = [
			'runname'   , 'iteration' , 'date',     'start_time'  , 'time_reset', 'time_test' , 'latency'  , 'memory',
			'CL_ok'     , 'LA_ok'     , 'L1_ok'     , 'LH_ok'     , 'CL_er'     , 'LA_er'     , 'L1_er'    , 'LH_er', 'conf_p_er',  'conf_s_er',
			'FIFO_Stub' , 'FIFO_L1'   , 'seucnt_A_P', 'seucnt_A_S', 'seucnt_S_P', 'seucnt_S_S', 'seucnt_T' ,
			'strip_0'   , 'strip_1'   , 'strip_2'   , 'strip_3'   , 'strip_4'   , 'strip_5'   , 'strip_6'  , 'strip_7',
			'hip_0'     , 'hip_1'     , 'hip_2'     , 'hip_3'     , 'hip_4'     , 'hip_5'     , 'hip_6'    , 'hip_7'  ]
		msg = ''
		if(not os.path.exists(summary)):
			for data in header:
				msg += self.__write_fixed_width(data)
			msg += '\n'
		for data in logdata:
			msg += self.__write_fixed_width(data)
		with open(summary, 'a') as fo:
			fo.write(msg + '\n')

	##############################################################
	def __write_fixed_width(self, data):
		if  (type(data)==int):    msg = '{:10d}, '.format(data)
		elif(type(data)==str):    msg = '{:10s}, '.format(data)
		elif(type(data)==float):  msg = '{:10.3f}, '.format(data)
		elif(type(data)==bool):   msg = '{:10s}, '.format(str(data))
		else:                     msg = str(data)
		return msg

	##############################################################
	def init_parameters(self):
		self.summary = results()
		self.runtest = RunTest('default')
		self.l1_latency = [101, 501]
		self.run_time = 5 #sec
		self.terminate = False


	##############################################################
	##### OLD METHODS ############################################
	##############################################################

	def analyse_stub_error_buffer(self, folder = "../SSA_Results/SEU_Results_anl"):
		labels = []
		datalog = []
		self.dirs = os.listdir(folder)
		self.dirs = [s for s in self.dirs  if "Test_" in s]
		self.dirs.sort()

	##############################################################
	def compile_logs(self, folder = "../SSA_Results/SEU_Results", cl_cut = 100, l1_cut = 100):
		labels = []
		datalog = []
		self.dirs = os.listdir(folder)
		self.dirs = [s for s in self.dirs  if "Test_" in s]
		self.dirs.sort()
		datalog.append( ["LET", "TILT", "LATENCY", "FLUX", "Run Time", "Average SEU Counter in 30sec", "Average Cluster Errors in 30sec", "Average L1 Errors in 30sec", "Average Cluster Errors / (30sec*Flux)", "Average L1 Errors in 30sec / (30sec*Flux)", "Duration Cluster test [s]", "Cluster data errors", "Duration L1 test [s]", "L1 data errors"])
		for dt in self.dirs:
			summary = []
			l1er_lowlatency  = []
			l1er_highlatency = []
			info = CSV.csv_to_array( folder + "/" + dt + "/info.csv" )
			ION  = info[0,1]
			LET  = float(info[3,1])
			FLUX = float(info[4,1])
			TILT = float(info[5,1])
			for f in os.listdir(folder + '/' + dt):
				if(len(re.findall("\W?SEU_SSA(.+).csv", f))>0):
					#print(folder + '/' + dt + '/' + f)
					summary = CSV.csv_to_array( folder + '/' + dt + '/' + f )
			self.summary = summary

			tmp = summary[np.where(summary[:,21] < 100)][:,21]
			seucnt = np.mean(tmp)

			tmp = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]<250) )][:,15]
			cor = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]<250) )][:,24]
			clusterr_l_sum = np.sum(tmp + cor)
			clusterr_l_len = len(tmp + cor)
			clusterr_l = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]>250) )][:,15]
			cor = summary[np.where( (summary[:,22] != 'X') * (summary[:,2]>250) )][:,24]
			clusterr_h = np.mean(tmp + cor)
			clusterr_h_sum = np.sum(tmp + cor)
			clusterr_h_len = len(tmp + cor)
			clusterr_h = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]<250)  )][:,17]
			cor = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]<250)  )][:,25]
			l1dataer_l_sum = np.sum(tmp + cor)
			l1dataer_l_len = len(tmp + cor)
			l1dataer_l = np.float(np.mean(tmp + cor))

			tmp = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]>250)  )][:,17]
			cor = summary[np.where( (summary[:,23] != 'X') * (summary[:,2]>250)  )][:,25]
			l1dataer_h_sum = np.sum(tmp + cor)
			l1dataer_h_len = len(tmp + cor)
			l1dataer_h = np.float(np.mean(tmp + cor))

			print( "->  {:2s}   {:%7.3f}   {:7.3f}  {:7.3f}  {:7.3f} ".format(ION, LET,  clusterr_l+clusterr_h, l1dataer_l, l1dataer_h)  )

			datalog.append( [LET, TILT, 100 , FLUX, 30, seucnt, clusterr_l, l1dataer_l, clusterr_l/(float(FLUX)*30), l1dataer_l/(float(FLUX)*30), clusterr_l_len*30,  clusterr_l_sum, l1dataer_l_len*30,  l1dataer_l_sum ])
			#print(datalog[-1])
			datalog.append( [LET, TILT, 500 , FLUX, 30, seucnt, clusterr_h, l1dataer_h, clusterr_h/(float(FLUX)*30), l1dataer_h/(float(FLUX)*30), clusterr_h_len*30,  clusterr_h_sum, l1dataer_h_len*30,  l1dataer_h_sum ])
			#print(datalog[-1])
			#time.sleep(2)
		CSV.array_to_csv( datalog , folder + "/cmplog.csv" )
		print("->  Compiled log saved in: " + str( folder + "/cmplog.csv") )

	##############################################################
	def run_seu_counter(self, folder, filename, runtime = 60):
		logfile = "../SSA_Results/SEU/" + folder + "/" + filename + "_seucounter.csv"
		tinit = time.time()
		while True:
			seucounter = self.ssa.ctrl.read_seu_counter()
			fo = open(logfile, 'a')
			fo.write(str(time.time()-tinit) + ", " + str(seucounter) + '\n')
			fo.close()
			time.sleep(0.2)
			print(str(seucounter))
			if( (time.time()-tinit) > runtime):
				return

	def run_info(self):
		return ''

	def I2C_test(self, file):
		for i in range(10000):
			registers = []; rm = []
			peri_reg_map  = self.ssa.ctrl.ssa_peri_reg_map.copy()

			for i in peri_reg_map:
				if('Fuse' in i): rm.append(i)
				if('SEU' in i): rm.append(i)
			for k in rm:
				peri_reg_map.pop(k, None)
			strip_reg_map = self.ssa.ctrl.ssa_strip_reg_map.copy()
			for i in strip_reg_map:
				if('ReadCounter' in i): rm.append(i)
			for k in rm:
				strip_reg_map.pop(k, None)

			for reg in peri_reg_map:
				self.I2C.peri_write(reg, 0x1)
				r = self.I2C.peri_read(reg)
				registers.append([ reg,  r])
				if(r != 0x1):
					print([ reg,  r])
			#for reg in strip_reg_map:
			#	for strip in range(1,120):
			#		self.I2C.strip_write(reg, strip, 0x1)
			#		r = self.I2C.strip_read(reg,  strip)
			#		registers.append([ reg,  r])
			#		#if(r != 0x1):
			#		print([ reg,  r])
			CSV.ArrayToCSV(registers, file+ str(i))

	##############################################################
	def plot_logs(self, folder = "../SSA_Results/SEU_Results", compile_data = True, cl_cut = 70, l1_cut = 70):
		if(compile_data):
			self.compile_logs(folder = folder, cl_cut = cl_cut, l1_cut = l1_cut)
		datalog = CSV.csv_to_array(folder + "/cmplog.csv" )
		xvalues = np.unique(datalog[1: , 1])
		er_clus_100_t00 = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		er_clus_500_t00 = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		er_l100_t00     = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		er_l500_t00     = np.array( datalog[ np.where( (datalog[:,2]== '0.0') * (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		er_clus_100_t30 = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		er_clus_500_t30 = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		er_l100_t30     = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		er_l500_t30     = np.array( datalog[ np.where( (datalog[:,2]=='30.0') * (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		l1_data100      = np.array( datalog[ np.where( (datalog[:,3]=='100') )][:,[1,10]] , dtype=float)
		l1_data500      = np.array( datalog[ np.where( (datalog[:,3]=='500') )][:,[1,10]] , dtype=float)
		clust_data100   = np.array( datalog[ np.where( (datalog[:,3]=='100') )][:,[1, 9]] , dtype=float)
		clust_data500   = np.array( datalog[ np.where( (datalog[:,3]=='500') )][:,[1, 9]] , dtype=float)
		clust_data      = np.array( datalog[1: ,[1,9]] , dtype=float)
		er_clus = []; er_l100 = []; er_l500 = [];
		for i in np.unique(clust_data[:,0]):
			tmp = np.array(  clust_data[ np.where((clust_data[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_clus.append( [i , tmp] )
			tmp = np.array(  l1_data100[ np.where((l1_data100[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_l100.append( [i , tmp] )
			tmp = np.array(  l1_data500[ np.where((l1_data500[:,0] == i)) ] )[:,1]
			tmp = np.mean( np.array(tmp) )
			er_l500.append( [i , tmp] )
		er_clus = np.array(er_clus)
		er_l100 = np.array(er_l100)
		er_l500 = np.array(er_l500)

		#plt.clf()
		fig = plt.figure(figsize=(16,12))
		plt.style.use('seaborn-deep')
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False)
		ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.xticks(fontsize=32)
		plt.yticks(fontsize=32)
		plt.ylabel("Errors per particle", fontsize=32)
		plt.xlabel('LET', fontsize=16)
		color=iter(sns.color_palette('deep'))
		#plt.ylim(bottom = 1E-9)
		c = next(color)
		plt.semilogy(er_clus[:,0], er_clus[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)
		c = next(color)
		plt.semilogy(er_l100[:,0], er_l100[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)
		c = next(color)
		plt.semilogy(er_l500[:,0], er_l500[:,1], '--o', color = c, markersize = 10, markeredgewidth = 0)

	##############################################################
	def CheckConfiguration(self, folder = "../SSA_Results/SEU_Results/"):
		labels = []; datalog = [];
		dirs = os.listdir(folder)
		dirs = [s for s in dirs  if "Test_" in s]
		dirs.sort()
		conf_correct = CSV.csv_to_array('ssa_methods/Configuration/ssa_configuration_base.csv')
		conf_default = CSV.csv_to_array('ssa_methods/Configuration/ssa_configuration_reset.csv')
		for dt in dirs:
			errors = []
			for f in os.listdir( folder + '/' + dt + "/CONFIG/" ):
				if(len(re.findall("SEU_SSA_(.+)_configuration.scv", f))>0):
					filename = folder + '/' + dt + "/CONFIG/" + f
					tmp = CSV.csv_to_array( filename )
					print("->  Elaborating file: " + filename)
					conf_read = np.zeros([np.shape(tmp)[0], 8], dtype="|S32")
					conf_read[:,0:4] = tmp[:,0:4]
					for reg in conf_read:
						correct_val = conf_correct[map(lambda x : (str(x[1]) == reg[1]) and (str(x[2]) == reg[2]) , conf_correct )][0][3]
						default_val = conf_default[map(lambda x : (str(x[1]) == reg[1]) and (str(x[2]) == reg[2]) , conf_default )][0][3]
						reg[4] = ''
						reg[6] = str(correct_val)
						reg[7] = str(default_val)
						if((reg[3] == str(correct_val)) or ((reg[2] == 'L1_Latency_lsb') and (reg[3] in ['101', '501'])) or ((reg[2] == 'L1_Latency_msb') and (reg[3] in ['0', '1']))):
							reg[5] = ""
						elif(reg[3] == str(default_val)):
							reg[5] = "Reset"
							errors.append(np.array([filename, reg[0], reg[1], reg[2], reg[3], reg[4], reg[5], reg[6], reg[7]]))
						else:
							reg[5] = "Error"
							errors.append(np.array([filename, reg[0], reg[1], reg[2], reg[3], reg[4], reg[5], reg[6], reg[7]]))

					CSV.array_to_csv(conf_read[:,1:], folder + '/' + dt + "/CONFIG/" + f )
			CSV.array_to_csv(errors, folder + '/' + dt + "/CONFIG/Conf_ErLog.csv")


		#fig = plt.figure(figsize=(16,12))
		#color=iter(sns.color_palette('deep'))
		#plt.semilogy(er_clus_100_t00[:,0], er_clus_100_t00[:,1], 'ro')
		#plt.semilogy(er_clus_500_t00[:,0], er_clus_500_t00[:,1], 'ro')
		#plt.semilogy(er_l100_t00[:,0], er_l100_t00[:,1], 'bo')
		#plt.semilogy(er_l500_t00[:,0], er_l500_t00[:,1], 'go')
		#plt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], 'bo')
		#plt.semilogy(er_l500_t30[:,0], er_l500_t30[:,1], 'go')
		#plt.show()
		#plt.figure(7)
		#plt.semilogy(er_l100[:,0], er_l100[:,1], '-ro')
		#plt.semilogy(l1_data100[:,0], l1_data100[:,1], '-go')
		#plt.semilogy(er_l100_t00[:,0], er_l100_t00[:,1], '-bo')
		#plt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], '-bo')
		#plt.show()
		#return er_l100, er_l100_t00, er_l100_t30

		#lt.figure(7)
		#lt.semilogy(er_clus_100_t30[:,0], er_clus_100_t30[:,1], 'ro')
		#lt.semilogy(er_clus_500_t30[:,0], er_clus_500_t30[:,1], 'ro')
		#lt.semilogy(er_l100_t30[:,0], er_l100_t30[:,1], 'bo')
		#lt.semilogy(er_l500_t30[:,0], er_l500_t30[:,1], 'go')
		#lt.show()

		#return er_clus[:,1],er_l100[:,1],er_l500[:,1]
		#plt.figure()
		#plt.plot(er_l100_t00[:,0], er_l100_t00[:,1], 'o')
		#plt.plot(er_l500_t00[:,0], er_l500_t00[:,1], 'o')
		#plt.figure()
		#plt.plot(er_l100[:,0], er_l100[:,1], 'o')
		#plt.figure()
		#plt.plot(er_clus_t00[:,0], er_clus_t00[:,1], 'o')
		#plt.figure()
		#plt.plot(er_clus_t30[:,0], er_clus_t30[:,1], 'o')
		#plt.show()
		#eturn datalog




#for reg in ssa.ctrl.ssa_peri_reg_map:
#	I2C.peri_write(reg, 0xff)
#	print("")
#	print(reg)
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	time.sleep(0.2); print(ssa.ctrl.read_seu_counter())
#	print(pwr.get)


#6 10, 30, 45, 60
