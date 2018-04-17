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

	def __init__(self, ssa, I2C, fc7, cal):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7
		self.cal = cal

	def cluster_data_basic(self, mode = "digital", chip = '0', shift = -1, shiftL = 1, display=False, lateral = False, doreset = False):
		if(isinstance(chip, int)): chip = str(chip)
		fo = open("../SSA_Results/" + "TestLogs" + "/Chip-" + chip + "_Test_ClusterData_" + mode + ".log", 'w')
		print "->  \tRemember to call test.lateral_input_phase_tuning() before to run this test"
		utils.activate_I2C_chip()
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = 0xff
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
			shift += 2
		else:
			return False
		if(doreset):
			initialise = True
		else:
			initialise = False
		if(lateral):
			clrange = random.sample(range(-2, 125), 127)
		else:
			clrange = random.sample(range(1, 121), 120)
		self.ssa.readout.cluster_data(initialize = True)
		cnt = 0
		for i in clrange:
			cnt += 1
			err = [False]*3
			if(doreset):
				self.ssa.init_all(display=False)
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = [i], initialise = initialise)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse(hit_list = [i], initialise = initialise)
			time.sleep(0.01)
			r, status = self.ssa.readout.cluster_data(initialize = initialise, shift = shift, getstatus = True)
			l = []
			if(i>0 and i < 121):
				if (len(r) != 1): err[0] = True
				elif (r[0] != i): err[0] = True
			elif (mode == "digital"):
				if (len(r) != 1): err[1] = True
				elif (r[0] != i): err[1] = True

			if( ((i < 8 and i > 0) or (i > 112 and i < 121)) and (mode == "digital") ):
				l = self.ssa.readout.lateral_data(initialize = False, shift = shiftL)
				if (len(l) != 1): err[2] = True
				elif (l[0] != i): err[2] = True
			dstr = " -> expected: "+utils.cl2str(i)+" | cl: " + utils.cl2str(r) + " | lat: " + utils.cl2str(l) + " | prev: " + utils.cl2str(prev) + " | st: [" + str(status[1]) + "-" + str(status[1]) +"]"
			if (err[0]):
				r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
				dstr += " | Reread: "+utils.cl2str(r)
				erlog = "\tCluster data Error   " + dstr
			elif(err[1]):
				erlog = "\tLateral Input Error  " + dstr
			elif(err[2]):
				erlog = "\tLateral Output Error " + dstr
			else:
				if(display == True):
					print "\tPassed       " + dstr
			prev = i
			if True in err:
				fo.write(erlog + '\n')
				print erlog
			utils.ShowPercent(cnt, 130, "Running clusters test based on digital test pulses")
		utils.ShowPercent(120, 120, "Done                                                      ")
		fo.close()



	def lateral_input_phase_tuning(self, display = False, timeout = 256, shift = 4):
		utils.activate_I2C_chip()
		alined_left  = False
		alined_right = False
		print ""
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", shift)
		self.ssa.inject.digital_pulse(initialise = True)

		self.ssa.ctrl.set_lateral_data(0b00001001, 0)
		cnt = 0
		while ((alined_left == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data()
			if len(clusters) == 2:
				if(clusters[0] == 121 and clusters[1] == 124):
					alined_left = True
			utils.ShowPercent(cnt, timeout+1, "Allaining left input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			self.ssa.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			cnt += 1
		if(alined_left == True):
			utils.ShowPercent(100, 100, "Left Input line alined    \t\t" + str(clusters) + "           ")
		else:
			utils.ShowPercent(100, 100, "Impossible to align left input data line  ")
		print "   "

		self.ssa.ctrl.set_lateral_data(0, 0b10100000)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data()
			if len(clusters) == 2:
				if(clusters[0] == -2 and clusters[1] == 0):
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
		print "   "




	def l1_data_basic(self, mode = "digital", chip = '0', calpulse = [50, 200], threshold = [10, 100], shift = 0, display = False, doreset = False, latency = 50):
		if(isinstance(chip, int)): chip = str(chip)
		fo = open("../SSA_Results/" + "TestLogs" + "/Chip-" + chip + "_Test_L1Data_" + mode + ".log", 'w')
		counter = [0,0]
		utils.activate_I2C_chip()
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		if(mode == "analog"): shift += 2
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency)
		if(L1_counter_init < 0): return 'error'
		l1hitlistprev = []
		hiplistprev = []
		if(doreset):  initialise = True
		else: initialise = False
		for H in range(0,2):
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(initialise = True)
			else:
				self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])
			for i in random.sample(range(1, 121), 120):
				err = False
				if(doreset):
					self.ssa.init_all(display=False)
				if(mode == "digital"):
					self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = initialise)
				else:
					self.ssa.inject.analog_pulse(hit_list = [i], initialise = initialise)
				counter[0] += 1
				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				time.sleep(0.03)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = initialise, shift = shift, latency = latency)
				if(L1_counter < 0): return 'error'
				if ((L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ): err = True
				if (len(l1hitlist) != 1): err = True
				if (len(l1hitlist) > 0):
					if (l1hitlist[0] != i): err = True
				if (len(hiplist) != H): err = True
				if (len(hiplist) > 0):
					if (hiplist[0] != H): err = True

				dstr = "expected: [%2d][%3s][%3s]\t  |  found: [%2d][%3s][%3s]  |  previously: [%2d][%3s][%3s]" % (
				        (L1_counter_init+1)&0b1111, i, H,
				        L1_counter,      ', '.join(map(str, l1hitlist)),       ', '.join(map(str, hiplist)) ,
				        L1_counter_init, ', '.join(map(str, l1hitlistprev)) ,  ', '.join(map(str, hiplistprev))
				       )
				l1hitlistprev = l1hitlist
				hiplistprev   = hiplist
				L1_counter_init = L1_counter
				if (err):
					counter[1] += 1
					fo.write("L1 Data Error -> " + dstr + '\n')
					print "\tError -> " + dstr + "                                  "
				else:
					if(display == True):
						print "\tOk    -> " + dstr + "                                  "
				if(display): utils.ShowPercent(counter[0], 240, "")
				else: utils.ShowPercent(counter[0], 240, "Running basic HIP flag test based on digital test pulses")
		fo.close()
		result = (1.0 - float(counter[1])/float(counter[0]))*100.0
		return "%5.2f%%" % (result)



	def memory(self, chip = '0', delay = [10], shift = 0, latency = 200, display = 1):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + "TestLogs" + "/Chip-" + str(chip) + "_Test_Memory" + ".log", 'w')
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency)
		self.ssa.inject.digital_pulse(initialise = True)
		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
		errlist = []
		cnt = [0, 0]
		for d in delay:
			Configure_TestPulse(
				delay_after_fast_reset = 512 + d,
				delay_after_test_pulse = (latency+3+shift),
				delay_before_next_pulse = 200, number_of_test_pulses = 1)
			for strip in range(1,121):
				self.ssa.inject.digital_pulse(hit_list = [strip], hip_list = [], initialise = False)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False)
				if(l1hitlist == [strip-1]):
					L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False)
				dstr = "expected: [   1][%3d][%3s][%3s]\t  |  found: [%3d][%3d][%3s][%3s]" % (
						strip, (d+1)%16, '', L1_counter, BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)))
				if(((L1_counter != 1) or (BX_counter != (d+1)%16)) and (display >= 1) ):
					print "\tCounter Error -> " + dstr + "                                  "
				error = False
				if(len(l1hitlist) != 1): error = True
				elif (l1hitlist[0] != strip): error = True
				if(error):
					cnt[1] += 1
					errlist.append(strip)
					if(display >= 1):
						print "\tMemory Error  -> " + dstr + "                                  "
				if(display >= 2):
					print "\tOk            -> " + dstr + "                                  "
				cnt[0] += 1
		fo.close()
		eff = ((1-(cnt[1]/float(cnt[0])))*100 )
		return eff, errlist

	def memory_vs_voltage(self, chip = '0', step = 0.01, start = 1.25, stop = 0.9):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + "TestLogs" + "/Chip-" + str(chip) + "_Test_Memory-Supply" + ".log", 'w')
		strout = "DVDD;       EFFICIENCY;    ERROR LIST; \n"
		for dvdd in np.arange(start, stop, -step):
			self.ssa.ctrl.set_dvdd( dvdd )
			eff, erlist = self.memory(display = 0)
			strout += "%4.3fV ;     %7.2f%% ;       %s ; \n" % (dvdd, eff, erlist)
			print "%4.3fV ;  %7.2f%% ;" % (dvdd, eff)
			if eff == 0:
				break
		fo.write(strout)
		fo.close()




'''
def prova(i):
	ssa.inject.digital_pulse([i])
	r = ssa.readout.cluster_data(initialize = False)
	if([i] != r): print 'error ' + str(i) + '  ' +str(r)



while 1:
	for i in range(1,121): prova(i)
'''
