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

	def test_cluster_data(self, mode = "digital", shift = 0, display=False):
		print "->  \tRemember to call test.lateral_input_phase_tuning() before to run this test"
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)

		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)

		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
			shift += 2
		else:
			return False
		self.ssa.readout.cluster_data(initialize = True)
		cnt = 0
		for i in random.sample(range(-3, 125), 128):
			cnt += 1
			err = [False]*3
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
			
			time.sleep(0.01)
			
			r = self.ssa.readout.cluster_data(initialize = False, shift = shift)
			l = []

			if(i>0 and i < 121):
				if (len(r) != 1): err[0] = True
				elif (r[0] != i): err[0] = True
			elif (mode == "digital"):
				if (len(r) != 1): err[1] = True
				elif (r[0] != i): err[1] = True

			if( ((i < 8 and i > 0) or (i > 112 and i < 121)) and (mode == "digital") ):
				l = self.ssa.readout.lateral_data(initialize = False)
				if (len(l) != 1): err[2] = True
				elif (l[0] != i): err[2] = True

			dstr = " -> expected: "+utils.cl2str(i)+" found cluster: " + utils.cl2str(r) + " found lateral: " + utils.cl2str(l) 
			if (err[0]):
				print "\tCluster data Error   " + dstr
			elif(err[1]):
				print "\tLateral Input Error  " + dstr  
			elif(err[2]):
				print "\tLateral Output Error " + dstr  
			else:
				if(display == True): 
					print "\tPassed       " + dstr 

			utils.ShowPercent(cnt, 130, "Running clusters test based on digital test pulses")
		utils.ShowPercent(120, 120, "Done                                                      ")



	def test_l1_data(self, mode = "digital", calpulse = [50, 200], threshold = [10, 100], shift = 0, display = False):
		
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		if(mode == "analog"): shift += 2

		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift)
		l1hitlistprev = []
		
		for H in range(0,2):
			cnt = 0
			self.ssa.inject.digital_pulse(initialise = True)
			self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])

			for i in random.sample(range(1, 121), 120):
				cnt += 1
				err = False
				if(mode == "digital"):
					self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = False)
				elif(mode == "analog"):
					self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)

				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				time.sleep(0.03)
				
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift)

				if( (L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ):
					print "\tL1 counter error. Expected" + str(((L1_counter_init + 1) & 0b1111)) + "Found: " + str((L1_counter & 0b1111)) + "                                   " 
				L1_counter_init = L1_counter

				if (len(l1hitlist) != 1): err = True
				elif (l1hitlist[0] != i): err = True
				if (len(hiplist) != H): err = True
				if(len(hiplist) > 0):
					if (hiplist[0] != H): err = True

				dstr = "\tError   -> expected: [" + str(i) + "]["+str(1)*H+"] found: " + str(l1hitlist) + str(hiplist) + " prev: " + str(l1hitlistprev) + "                                 "
				l1hitlistprev = l1hitlist
				if (err):
					print dstr
				else:
					if(display == True): 
						print "\tPassed   -> expected: [" + str(i) + "]["+str(1)*H+"] found: " + str(l1hitlist) + str(hiplist) + "                                   "

				if(H == 1):
					utils.ShowPercent(cnt, 120, "Running basic HIP flag test based on digital test pulses")
				else:
					utils.ShowPercent(cnt, 120, "Running basic L1 data test based on digital test pulses")
			
			utils.ShowPercent(120, 120, "Done\t\t\n")


	def lateral_input_phase_tuning(self, display = False, timeout = 256, shift = 4):
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
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

