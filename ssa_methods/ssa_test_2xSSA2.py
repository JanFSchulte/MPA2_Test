import time
import sys
import inspect
import random
import numpy as np
from utilities.tbsettings import *
from scipy import interpolate as scipy_interpolate
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import itertools

class Test_2xSSA2():

	def __init__(self, ssa0, ssa1, fc7):
		self.fc7 = fc7;
		self.ssa0 = ssa0
		self.ssa1 = ssa1

	def align_2xSSA(self):
		self.ssa0.chip.ctrl.activate_readout_shift()
		self.ssa1.chip.ctrl.activate_readout_shift()
		self.ssa0.chip.ctrl.set_shift_pattern_all(0b10000000)
		self.ssa1.chip.ctrl.set_shift_pattern_all(0b10000000)
		rt = self.ssa0.chip.ctrl.align_out()
		self.ssa0.chip.ctrl.reset_pattern_injection()
		self.ssa0.chip.ctrl.activate_readout_normal()
		self.ssa1.chip.ctrl.reset_pattern_injection()
		self.ssa1.chip.ctrl.activate_readout_normal()
		if(rt): utils.print_good( "->\tPhase alignment successfull")
		else:   utils.print_error("->\tPhase alignment error")
		return rt

	def lateral_communication_phase(self):
		testvect_L2R = [10, 20, 30, 117, 119]
		testvect_R2L = [1, 3, 5, 15, 25, 35]
		aligned = [False, False]
		self.ssa0.inject.digital_pulse(testvect_L2R)
		self.ssa1.inject.digital_pulse(testvect_R2L)
		for i in range(7,0,-1):
			self.ssa0.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_R_PhaseData', data=i)
			rt0 = self.ssa0.readout.cluster_data(shift = -2)
			if(rt0 == [10.0, 20.0, 30.0, 117.0, 119.0, 121.0, 123.0]):
				aligned[0] = True
				break
		for j in range(7,3,-1):
			self.ssa1.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_L_PhaseData', data=j)
			rt1 = self.ssa1.readout.cluster_data(shift = -2)
			if(rt1 == [-3.0, -1.0, 1.0, 3.0, 5.0, 15.0, 25.0]):
				aligned[1] = True
				break
		if(aligned[0]):
			if(i==7): utils.print_good("->  Lateral communication ok. Phase value = {:d} -> as expected.".format(i))
			else: utils.print_warning("->  Lateral communication ok. Phase value = {:d} -> not as expected but it is fine.".format(i))
		else:
			utils.print_error("->  Lateral communication not working properly")
		if(aligned[1]):
			if(j==7): utils.print_good("->  Lateral communication ok. Phase value = {:d} -> as expected.".format(j))
			else: utils.print_warning("->  Lateral communication ok. Phase value = {:d} -> not as expected but it is fine.".format(j))
		else:
			utils.print_error("->  Lateral communication not working properly")




#	def cluster_data(self, mode = "digital",  nstrips = 'random', min_clsize = 1, max_clsize = 4, nruns = 100, shift = -2, display=False, init = False, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False, lateral = True):
#		fo = open(file + "readout_cluster-data_" + mode + ".csv", filemode)
#		stexpected = ''; stfound = '';
#		SendCommand_CTRL("stop_trigger")
#		prev = [0xff]*8
#		if(mode == "digital"):
#			self.ssa0.inject.digital_pulse(initialise = True, times = 1)
#			self.ssa1.inject.digital_pulse(initialise = True, times = 1)
#		elif(mode == "analog"):
#			self.ssa0.inject.analog_pulse(initialise = True, mode = 'edge', cal_pulse_amplitude = 130, threshold = [100, 150])
#			self.ssa1.inject.analog_pulse(initialise = True, mode = 'edge', cal_pulse_amplitude = 130, threshold = [100, 150])
#		else:
#			return False
#		self.ssa.readout.cluster_data(initialize = True)
#		cnt = {'cl_sum': 0, 'cl_err' : 0};
#		timeinit = time.time()
#		for i in range(0,nruns):
#
#if(isinstance(nstrips, int)): nclusters_generated = nstrips
#else: nclusters_generated = random.randint(1, 8)
#cl_hits, cl_centroids = self.ssa0.test.generate_clusters(nclusters_generated, min_clsize, max_clsize, 1, 240)
#wd = 0; err = [False]*3
#
#ssa0_list = [i for i in (np.array(cl_hits)) if i < 121] or None
#ssa1_list = [i for i in (np.array(cl_hits)-120) if i > 0] or None
#
#if(mode == "digital"):
#	self.ssa0.inject.digital_pulse(hit_list = ssa0_list, initialise = False)
#	self.ssa1.inject.digital_pulse(hit_list = ssa1_list, initialise = False)
#elif(mode == "analog"):
#	self.ssa0.inject.analog_pulse(hit_list = ssa0_list, initialise = False)
#	self.ssa1.inject.analog_pulse(hit_list = ssa1_list, initialise = False)
#
#time.sleep(0.005) #### important at nstrips = 8 (I2C time)
#received0, status0 = self.ssa0.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
#received1, status1 = self.ssa1.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
#
#if (len(received) != len(cl_centroids)):
#	err[0] = True
##else:
#missing=[]; exceding=[];
#for k in cl_centroids:
#	if k not in received:
#		err[0] = True
#		missing.append(k)
#for k in received:
#	if k not in cl_centroids:
#		err[0] = True
#		exceding.append(k)
#
#
#			stexpected = utils.cl2str(cl_centroids, flag=missing,  color_flagged='red', color_others='green');
#			stfound    = utils.cl2str(received,     flag=exceding, color_flagged='red', color_others='green')
#			stprev     = utils.cl2str(prev)
#			sthits     = utils.cl2str(cl_hits)
#			#dstr = stexpected + ';    ' + stfound + '; ' + ';    ' + sthits + ';    ' + "                                            "
#			dstr = "->       REF:" + stexpected + ',\n' + ' '*39 + 'OUT:' + stfound + ', ' + ",                                            \n"
#			if (err[0]):
#				erlog = "Cluster-Data-Error,   " + dstr
#				cnt['cl_err'] += 1
#				if stop_on_error:
#					fo.write(runname + ', ' + erlog + ' \n')
#					utils.print_log('\t' + erlog)
#					return 100*(1-cnt['cl_err']/float(cnt['cl_sum']))
#			else:
#				if(display == True):
#					utils.print_log(   "\tPassed                " + dstr)
#			prev = received.copy()
#
#			cl_centroids.extend([0]*(8-len(cl_centroids)))
#			received.extend([0]*(8-len(received)))
#			savestr = "{:s}, REF, {:s}, OUT, {:s}".format(runname, ', '.join(map(str, cl_centroids)),  ', '.join(map(str, received)) )
#			if True in err:
#				fo.write('ER' + ', ' + savestr + ' \n')
#				utils.print_log( '\t' + erlog)
#			else:
#				fo.write('OK' + ', ' + savestr + ' \n')
#			cnt['cl_sum'] += 1;
#			if(mode == 'digital'):  utils.ShowPercent(cnt['cl_sum'], nruns, "Running clusters test based on digital test pulses")
#			elif(mode == 'analog'): utils.ShowPercent(cnt['cl_sum'], nruns, "Running clusters test based on analog test pulses")
#		utils.ShowPercent(nruns, nruns, "Done                                                      ")
#		fo.close()
#		rt = 100.0*(1.0-float(cnt['cl_err'])/float(cnt['cl_sum']))
#		fo = open(file + "readout_cluster-data_summary" + mode + ".csv", 'a')
#		fo.write("->  Cluster data test with {mode:s} injection -> {res:5.3f}%".format(mode=mode, res=rt))
#		if(rt == 100.0):
#			utils.print_good("->  Cluster data test with {mode:s} injection -> 100%".format(mode=mode))
#		else:
#			utils.print_error("->  Cluster data test with {mode:s} injection -> {res:5.3f}%".format(mode=mode, res=rt))
#		#print(time.time()-timeinit)
#		return rt
#
