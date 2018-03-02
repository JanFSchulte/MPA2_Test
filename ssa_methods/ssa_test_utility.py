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

	def __init__(self, ssa, I2C, fc7):
		self.ssa = ssa
		self.I2C = I2C
		self.fc7 = fc7


	def test_cluster_data(self, mode = "digital", display=False):
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)

		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
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
			
			r = self.ssa.readout.cluster_data(initialize = False)
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



	def test_l1_data(self, display=False):
		
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)

		self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True)

		
		for H in range(0,2):
			cnt = 0
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
			for i in random.sample(range(1, 121), 120):
				cnt += 1
				err = False
				self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = False)
				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				time.sleep(0.03)
				
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False)

				if( (L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ):
					print "\tL1 counter error. Expected" + str(((L1_counter_init + 1) & 0b1111)) + "Found: " + str((L1_counter & 0b1111)) + "                                   " 
				L1_counter_init = L1_counter

				if (len(l1hitlist) != 1): err = True
				elif (l1hitlist[0] != i): err = True
				if (len(hiplist) != H): err = True
				if(len(hiplist) > 0):
					if (hiplist[0] != H): err = True

				dstr = "\tError   -> expected: [" + str(i) + "]["+str(1)*H+"] found: " + str(l1hitlist) + str(hiplist) + "                                   "

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
		alined_left  = False
		alined_right = False
		print ""
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", shift)
		self.ssa.inject.digital_pulse(initialise = True)

		self.ssa.ctrl.set_lateral_data(0b00001001, 0)
		cnt = 0
		while ((alined_left == False) and (cnt < timeout)):  
			clusters = self.ssa.readout.cluster_data(display_prev = display)
			if len(clusters) == 2:
				if(clusters[0] == 121 and clusters[1] == 124):
					alined_left = True
			time.sleep(0.001)
			self.ssa.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			utils.ShowPercent(cnt, timeout+1, "Allaining left input line                    " + str(clusters) + "           ")
			cnt += 1
		if(alined_left == True):
			utils.ShowPercent(100, 100, "Left Input line alined                    ")
		else: 
			utils.ShowPercent(100, 100, "Impossible to align left input data line  ")
		print "   " 

		self.ssa.ctrl.set_lateral_data(0, 0b10100000)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):  
			clusters = self.ssa.readout.cluster_data(display_prev = display)
			if len(clusters) == 2:
				if(clusters[0] == -2 and clusters[1] == 0):
					alined_right = True
			time.sleep(0.001)
			self.ssa.ctrl.set_lateral_data_phase(5,0)
			time.sleep(0.001)
			utils.ShowPercent(cnt, timeout+1, "Allaining right input line                  " + str(clusters) + "           ")
			cnt += 1
		utils.ShowPercent(100)
		if(alined_right == True):
			utils.ShowPercent(100, 100, "Right input line alined")
		else: 
			utils.ShowPercent(100, 100, "Impossible to align right input data line")
		print "   " 

	def sampling_slack(self, strips = range(1,121), display=True, shift = 0): 
		delay = []
		cnt = 0
		self.ssa.inject.analog_pulse(initialise = True)
		for s in strips:
			cnt += 1
			self.ssa.inject.analog_pulse(hit_list = [s], mode = 'edge', initialise = False)
			cl_array , sdel = self.ssa.readout.cluster_data_delay(shift = shift)
			delay.append(sdel)
			if(display): utils.ShowPercent(cnt, len(strips), " Sampling")
		if(display): utils.ShowPercent(len(strips), len(strips), " Done")	
		return delay

	def sampling_clk_deskewing(self, strip = [10], step = 1, start = 3, shift = 2, display = False):
		prev1 = 0xff
		prev2 = 0xff

		edge = [False, False]
		for i in range(start,7):
			for j in range(0, 16, step):
				utils.ShowPercent(i*16+j, 16*8, " Sampling")
				self.ssa.ctrl.set_sampling_deskewing_coarse(value = i)
				self.ssa.ctrl.set_sampling_deskewing_fine(value = j, enable = True, bypass = True)
				sleep(0.01)
				delay = self.sampling_slack(strip, display = False, shift = shift)
				if(display): 
					print "deskewing = [%d][%d] \t->  delay = %s)" % (i, j, delay)
				if(delay < prev2 and prev1 < prev2): 
					if(j>0): edge = [i,j-1]
					else: edge = [i-1,15]
					utils.ShowPercent(100, 100, " Done         ")
					return edge
				prev2 = prev1
				prev1 = delay
		return edge

	def CalPulse_DelayLine_Resolution(self):
		r = []
		for i in range(0,64):
			self.ssa.ctrl.set_cal_pulse_delay(i)
			r.append(self.sampling_slack(strips = [50], display=False, shift = 3))
			utils.ShowPercent(i, 63, "Calculating")
		resolution = 25.0 / np.size( np.where(  np.array(r) == 0 ) )
		return '%0.3fns' % resolution

	#  ssa.ctrl.set_cal_pulse_delay(11)
	#  test.sampling_clk_deskewing(step = 1)
	#  I2C.peri_write('Bias_D5DLLB', 20)