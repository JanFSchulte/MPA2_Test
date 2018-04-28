from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class SSA_test_utility():

	def __init__(self, ssa, I2C, fc7, cal, pwr):
		self.ssa = ssa;	self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal; self.pwr = pwr;


	def cluster_data_basic(self, mode = "digital", shift = -1, shiftL = 1, display=False, lateral = True, init = True, hfi = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		fo = open("../SSA_Results/" + file + "_Test_ClusterData_" + mode + ".log", filemode)
		stexpected = ''; stfound = ''; stlateralout = '';
		#print "->  \tRemember to call test.lateral_input_phase_tuning() before to run this test"
		utils.activate_I2C_chip()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 3)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 20, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = 0xff
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
			shift += 2
		else:
			return False
		if(lateral):
			clrange = random.sample(range(-2, 125), 127)
		else:
			clrange = random.sample(range(1, 121), 120)
		self.ssa.readout.cluster_data(initialize = True)
		cnt = {'cl_sum': 0, 'cl_err' : 0, 'li_sum': 0, 'li_err' : 0, 'lo_sum': 0, 'lo_err' : 0};
		for i in clrange:
			cnt['cl_sum'] += 1; wd = 0;
			err = [False]*3
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
			time.sleep(0.001)
			r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
			if(hfi):
				while(r==prev):
					r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
					if(wd>3): break
					wd += 1;
			l = []
			if(i>0 and i < 121):
				if (len(r) != 1): err[0] = True
				elif (r[0] != i): err[0] = True
			else:
				cnt['li_sum'] += 1;
				if (mode == "digital"):
					if (len(r) != 1): err[1] = True
					elif (r[0] != i): err[1] = True
			if( ((i < 8 and i > 0) or (i > 112 and i < 121))):
				cnt['lo_sum'] += 1;
				if (mode == "digital"):
					l = self.ssa.readout.lateral_data(initialize = False, shift = shiftL)
					if (len(l) != 1): err[2] = True
					elif (l[0] != i): err[2] = True
			stexpected = utils.cl2str(i);
			stfound = utils.cl2str(r);
			stlateralout = utils.cl2str(l);
			dstr = stexpected + ';    ' + stfound + ';    ' + stlateralout + "                                            "
			if (err[0]):
				erlog = "Cluster-Data-Error;   " + dstr
				cnt['cl_err'] += 1
			elif(err[1]):
				erlog = "Lateral-Input-Error;  " + dstr
				cnt['li_err'] += 1;
			elif(err[2]):
				erlog = "Lateral-Output-Error; " + dstr
				cnt['lo_err'] += 1;
			else:
				if(display == True):
					print   "\tPassed                " + dstr
			prev = i
			if True in err:
				fo.write(runname + ';\t' + erlog + '\n')
				print '\t' + erlog
			utils.ShowPercent(cnt['cl_sum'], 130, "Running clusters test based on digital test pulses")
		utils.ShowPercent(120, 120, "Done                                                      ")
		fo.close()
		rt = [100*(1-cnt['cl_err']/float(cnt['cl_sum'])) , 100*(1-cnt['li_err']/float(cnt['li_sum'])) , 100*(1-cnt['lo_err']/float(cnt['lo_sum'])) ]
		return rt



	def lateral_input_phase_tuning(self, display = False, timeout = 256*3, delay = 4, shift = 0, init = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + file + "_Test_LateralInput.log", filemode)
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.readout.cluster_data(initialize = True)
		alined_left  = False; alined_right = False; cnt = 0; print "";
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay)
		self.ssa.inject.digital_pulse([100, 121, 124], initialise = True)
		#self.ssa.ctrl.set_lateral_data(0b00001001, 0)
		while ((alined_left == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == 100 and clusters[1] == 121 and clusters[2] == 124):
					alined_left = True
			utils.ShowPercent(cnt, timeout+1, "Allaining left input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			#if  (cnt==256): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+1)
			#elif(cnt==512): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+2)
			self.ssa.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			cnt += 1
		if(alined_left == True):
			utils.ShowPercent(100, 100, "Left Input line alined    \t\t" + str(clusters) + "           ")
		else:
			utils.ShowPercent(100, 100, "Impossible to align left input data line  ")
		#self.ssa.ctrl.set_lateral_data(0, 0b10100000)
		self.ssa.inject.digital_pulse([-2, 0, 10], initialise = True)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == -2 and clusters[1] == 0 and clusters[2] == 10):
					alined_right = True
			utils.ShowPercent(cnt, timeout+1, "Allaining right input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			self.ssa.ctrl.set_lateral_data_phase(5,0)
			time.sleep(0.001)
			cnt += 1
		if(alined_right == True):
			utils.ShowPercent(100, 100, "Right input line alined     \t\t" + str(clusters) + "           ")
		else:
			utils.ShowPercent(100, 100, "Impossible to align right input data line")
		fo.write(str(runname) + ';\t' + str(alined_left) + ";\t" + str(alined_right) + '\n')
		return [alined_left, alined_right]



	def l1_data_basic(self, mode = "digital", calpulse = [100, 200], threshold = [20, 150], shift = 0, display = False, latency = 50, init = True, hfi = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		fo = open("../SSA_Results/" + file + "_Test_L1_" + mode + ".log", filemode)
		counter = [[0,0],[0,0]]
		utils.activate_I2C_chip()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		if(mode == "analog"): shift += 2
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency)
		if(L1_counter_init < 0): return 'error'
		l1hitlistprev = []
		hiplistprev = []
		for H in range(0,2):
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(initialise = True)
			else:
				self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])
			for i in random.sample(range(1, 121), 120):
				err = [False, False]; wd = 0;
				if(mode == "digital"):
					self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = False)
				else:
					self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
				counter[H][0] += 1
				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				time.sleep(0.001)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift, latency = latency)
				if (hfi):
					while(l1hitlist == l1hitlistprev and len(l1hitlist) == 1):
						sleep(0.001); L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False)
						if(wd>3): break
						wd += 1
				if(L1_counter < 0): return 'error'
				if ((L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ): err[H] = True
				if (len(l1hitlist) != 1): err[H] = True
				if (len(l1hitlist) > 0):
					if (l1hitlist[0] != i): err[H] = True
				if (len(hiplist) != H): err[H] = True
				if (len(hiplist) > 0):
					if (hiplist[0] != H): err[H] = True

				dstr = "expected: [%2d][%3s][%3s]\t  |  found: [%2d][%3s][%3s]"  % (
				        (L1_counter_init+1)&0b1111, i, H,
				        L1_counter,      ', '.join(map(str, l1hitlist)),       ', '.join(map(str, hiplist)))
				fstr = "[%2d][%3s][%3s];   \t[%2d][%3s][%3s]"  % (
				        (L1_counter_init+1)&0b1111, i, H,
				        L1_counter,      ', '.join(map(str, l1hitlist)),       ', '.join(map(str, hiplist)))
				l1hitlistprev = l1hitlist
				hiplistprev   = hiplist
				L1_counter_init = L1_counter
				if (err[H]):
					counter[H][1] += 1
					fo.write(runname + ';\t' + fstr + '\n')
					print "\tError -> " + dstr + "                                  "
				else:
					if(display == True):
						print "\tOk    -> " + dstr + "                                  "
				if(display): utils.ShowPercent(counter[0], 240, "")
				else: utils.ShowPercent(counter[0][0]+counter[1][0], 240, "Running L1 test")
		fo.close()
		result = [ (1.0 - float(counter[0][1])/float(counter[0][0]))*100.0  ,  (1.0 - float(counter[1][1])/float(counter[1][0]))*100.0  ]
		#return "%5.2f%%" % (result)
		return result



	def memory(self, memory = 1, delay = [10], shift = 0, latency = 200, display = 1, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		HIP = memory-1
		fo = open("../SSA_Results/" + file + "_Test_Memory_" + str(memory) + ".log", filemode)
		self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency)
		self.ssa.inject.digital_pulse(initialise = True)
		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
		errlist = []
		cnt = [0, 0, 0]
		for d in delay:
			Configure_TestPulse(
				delay_after_fast_reset = 512 + d,
				delay_after_test_pulse = (latency+3+shift),
				delay_before_next_pulse = 200, number_of_test_pulses = 1)
			for strip in range(1,121):
				if HIP: self.ssa.inject.digital_pulse(hit_list = [strip], hip_list = [strip], initialise = False)
				else:   self.ssa.inject.digital_pulse(hit_list = [strip], hip_list = [], initialise = False)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False)
				while(l1hitlist == [strip-1]):
					L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False)
					if cnt[2] > 3: break;
					cnt[2] += 1
				dstr = "expected: [   1][%3d][%3s][%3s]\t  |  found: [%3d][%3d][%3s][%3s]" % (
						strip, (d+1)%16, '', L1_counter, BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)))
				if(((L1_counter != 1) or (BX_counter != (d+1)%16)) ):
					print "\tCounter Error -> " + dstr + "                                  "
				error = False
				if(len(l1hitlist) != 1): error = True
				elif (l1hitlist[0] != strip or len(hiplist) != HIP): error = True
				if(error):
					cnt[1] += 1
					errlist.append([[strip], l1hitlist])
					if(display >= 1):
						print "\tMemory Error  -> " + dstr + "                                  "
				elif(display >= 2):
					print "\tOk            -> " + dstr + "                                  "
				cnt[0] += 1
		eff = ((1-(cnt[1]/float(cnt[0])))*100 )
		fo.write( "\n%s ;\t %7.2f%% ;\t %s" % (runname, eff, '; '.join(map(str, errlist)) ))
		fo.close()
		self.memerrlist = errlist
		return eff

	def memory_vs_voltage(self, memory = 1, step = 0.005, start = 1.25, stop = 0.9, latency = 200, shift = 0, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + file + "_Test_Memory-Supply_" + str(memory) + ".log", filemode)
		fo.write("\n    RUN ; DVDD;       EFFICIENCY;    ERROR LIST; \n")
		for dvdd in np.arange(start, stop, -step):
			self.pwr.set_dvdd( dvdd )
			eff = self.memory(memory = memory, display = 0, latency = latency, shift = shift)
			erlist = self.memerrlist
			fo.write("%8s ; %4.3fV ;     %7.2f%% ;       %s ; \n" % (runname, dvdd, eff, erlist))
			print "%4.3fV ;  %7.2f%% ;" % (dvdd, eff)
			if eff == 0:
				break
		fo.close()




'''
def prova(i):
	ssa.inject.digital_pulse([i])
	r = ssa.readout.cluster_data(initialize = False)
	if([i] != r): print 'error ' + str(i) + '  ' +str(r)



while 1:
	for i in range(1,121): prova(i)
'''
