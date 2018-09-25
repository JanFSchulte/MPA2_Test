from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import ctypes

class SSA_SEU_utilities():

	def __init__(self, ssa, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map; self.ssa = ssa;
		self.analog_mux_map = analog_mux_map; self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;	self.fc7 = FC7;	self.pwr = pwr; self.timer_data_taking = 60*5

	##############################################################
	def Configure_Injection(self, strip_list, analog_injection = 0):
		#here define the way to generate stub/centroid data pattern on the MPA/SSA
		utils.activate_I2C_chip()
		self.ssa.ctrl.activate_readout_normal()
		self.I2C.peri_write("CalPulse_duration", 1)
		self.I2C.strip_write("ENFLAGS", 0, 0)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0x1)
		word = np.zeros(16, dtype = np.uint8)
		row = np.zeros(16, dtype = np.uint8)
		pixel = np.zeros(16, dtype = np.uint8)
		l = np.zeros(10, dtype = np.uint8)
		for st in strip_list:
			if(st>0 and st<121):
				self.I2C.strip_write("ENFLAGS", st, 0b01001)
				self.I2C.strip_write("DigCalibPattern_L", st, 0x1)
		sleep(0.1)

	def Stub_Evaluate_Pattern(self, strip_list):
		strip = np.sort(strip_list)
		slist = np.zeros(8, dtype = ctypes.c_uint32)
		for i in range(np.size(strip)):
			slist[i] = ((strip[i] + 3) << 1) & 0xff
		p1 = (slist[0]<<0) | (slist[1]<<8) | (slist[2]<<16) | (slist[3]<<24)
		p2 = (slist[4]<<0) | (slist[5]<<8) | (slist[6]<<16) | (slist[7]<<24)
		return p1, p2

	##############################################################
	def Stub_loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, display = 2):
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3)
		sleep(0.5)
		if(display>1):
			print "Content of the patterns1 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns1")
			print "Content of the patterns2 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns2")
			print "Content of the patterns3 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns3")

	##############################################################
	def Stub_delayDataTaking(self, display = 2):
		#below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
		if(display>1):
			print "BX indicator for SSA centroid data:", fc7.read("stat_phy_slvs_compare_fifo_bx_indicator")
		#fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
		sleep(1)

	##############################################################
	def Stub_RunStateMachine(self, display = 2, run_time = 10):
		FSM = fc7.read("stat_phy_slvs_compare_state_machine")
		if(display>1): print "  \tState of FSM before starting: " , FSM
		if (FSM == 4):
			print "-X  \tError in FSM"
			return
		rp = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		if(display>1):
			print "->  \tAlmost full flag of FIFO before starting: " , rp

		self.fc7.write("ctrl_phy_SLVS_compare_start",1)

		state = fc7.read("stat_phy_slvs_compare_state_machine")
		full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		if(display>1):
			print "->  \tState of FSM after starting: " , state
			print "->  \tAlmost full flag of FIFO after starting: " , full

		self.fc7.SendCommand_CTRL("start_trigger")

		timer = 0
		CntBad = 0
		CntGood = 0
		FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		while(FIFO_almost_full != 1 and timer < run_time):
			FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			timer = timer + 1
			if(display>0):
				CntBad  = fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
				CntGood = fc7.read("stat_phy_slvs_compare_number_good_data")
				state   = (fc7.read("stat_phy_slvs_compare_state_machine"))
				full    = (fc7.read("stat_phy_slvs_compare_fifo_almost_full"))
				print("____________________________________________________________________________")
				print("->  \tSEU Cluster-Data  -> Iteration number:  %12d / %0d" % (timer, run_time))
				print("->  \tSEU Cluster-Data  -> State of FSM:      %12d" % (state))
				print("->  \tSEU Cluster-Data  -> FIFO almost full:  %12d" % (full))
				print("->  \tSEU Cluster-Data  -> Number of bad  BX: %12d (%10.6f%%)" % (CntBad,  100*np.float(CntBad)/(CntGood+CntBad)))
				print("->  \tSEU Cluster-Data  -> Number of good BX: %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad)))
			sleep(1)
		if(display>0): print("____________________________________________________________________________")
		fc7.write("ctrl_phy_SLVS_compare_stop",1)
		if(display>1): print "State of FSM after stopping: " , fc7.read("stat_phy_slvs_compare_state_machine")
		if(timer == run_time and FIFO_almost_full == 0):
			print "->  \tSEU Cluster-Data  -> data taking stopped because reached the adequate time"
		elif(CntGood > (2**31-3)):
			print "->  \tSEU Cluster-Data  -> data taking stopped because reached the good-clusters counter size"
		elif(FIFO_almost_full == 1 and timer < run_time ):
			print "-X  \tSEU Cluster-Data  -> data taking stopped because the FIFO reached the 80%"
		else:
			print "-X  \tSEU Cluster-Data  -> data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"

	##############################################################
	def parse_to_bin32(self, input):
		return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

	##############################################################
	def parse_to_bin8(self, input):
		return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

	##############################################################
	def parse_to_bin9(input):
		return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)

	##############################################################
	def Stub_ReadFIFOs(self, display = False, chip = 'SSA'):
		print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
		print "State of FSM before reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine")
		stat_phy_slvs_compare_data_ready = fc7.read("stat_phy_slvs_compare_data_ready")
		i = 0
		#FIFO = np.ones( [16386,10], dtype = ctypes.c_uint32 )
		FIFO = np.full( [16386,10], np.NaN)
		FIFO_depth = fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")

		"""package2 = fc7.fifoRead("ctrl_phy_SLVS_compare_read_data2_fifo", 17000)
		p l5, l6, l7ackage4 = fc7.fifoRead("ctrl_phy_SLVS_compare_read_data4_fifo", 17000)
		for i in range(16384):
			print "Package2 #", i+1, ": ", package2[i]
			print "Package4 #", i+1, ": ", package4[i]
		print("State of FSM after reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine"))
		print("Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full"))"""

		for i in range (0, FIFO_depth):
				fifo1_word = fc7.read("ctrl_phy_SLVS_compare_read_data1_fifo")
				fifo2_word = fc7.read("ctrl_phy_SLVS_compare_read_data2_fifo")
				fifo3_word = fc7.read("ctrl_phy_SLVS_compare_read_data3_fifo")
				fifo4_word = fc7.read("ctrl_phy_SLVS_compare_read_data4_fifo")
				fw1 = self.parse_to_bin32(fifo1_word)
				fw2 = self.parse_to_bin32(fifo2_word)
				fw3 = self.parse_to_bin32(fifo3_word)
				fw4 = self.parse_to_bin32(fifo4_word)
				FIFO[i, 0] = fifo4_word #BX
				if(chip == "SSA"):
					FIFO[i,8] = self.parse_to_bin8((fifo2_word & 0xff000000)>>24)
					FIFO[i,7] = self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
					FIFO[i,6] = self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8)
					FIFO[i,5] = self.parse_to_bin8(fifo2_word & 0x000000ff)
					FIFO[i,4] = self.parse_to_bin8((fifo1_word & 0xff000000)>>24)
					FIFO[i,3] = self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
					FIFO[i,2] = self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
					FIFO[i,1] = self.parse_to_bin8(fifo1_word & 0x000000ff)
				elif(chip == "MPA"):
					FIFO[i,10] = self.parse_to_bin8((fifo3_word & 0x0000ff00)>>8)
					FIFO[i, 9] = self.parse_to_bin8(fifo3_word & 0x000000ff)
					FIFO[i, 8] = self.parse_to_bin8((fifo2_word & 0xff000000)>>24)
					FIFO[i, 7] = self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
					FIFO[i, 6] = self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8)
					FIFO[i, 5] = self.parse_to_bin8(fifo2_word & 0x000000ff)
					FIFO[i, 4] = self.parse_to_bin8((fifo1_word & 0xff000000)>>24)
					FIFO[i, 3] = self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
					FIFO[i, 2] = self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
					FIFO[i, 1] = self.parse_to_bin8(fifo1_word & 0x000000ff)
				if(display):
					print("--------------------------")
					print("Entry number: ", i ," in the FIFO:")
					print "MPA: BX counter, 0x0000, BX0 data (l4, l3, l2, l1, l0) and  BX1 data (l4, l3, l2, l1, l0)"
					print "SSA: 0x0000, BX counter, 0x0000 and centroid data (l7, l6, l5, l4, l3, l2, l1, l0)"
					print(fw4, fw3, fw2, fw1)
					print(fifo4_word, fifo3_word, fifo2_word, fifo1_word)
					print "BX counter:", fifo4_word
					if(chip == "SSA"):
						print "SSA centroid l7: ", FIFO[i,8]
						print "SSA centroid l6: ", FIFO[i,7]
						print "SSA centroid l5: ", FIFO[i,6]
						print "SSA centroid l4: ", FIFO[i,5]
						print "SSA centroid l3: ", FIFO[i,4]
						print "SSA centroid l2: ", FIFO[i,3]
						print "SSA centroid l1: ", FIFO[i,2]
						print "SSA centroid l0: ", FIFO[i,1]
					elif(chip == "MPA"):
						print "MPA stub BX0 l4: ", FIFO[i,10]
						print "MPA stub BX0 l3: ", FIFO[i, 9]
						print "MPA stub BX0 l2: ", FIFO[i, 8]
						print "MPA stub BX0 l1: ", FIFO[i, 7]
						print "MPA stub BX0 l0: ", FIFO[i, 6]
						print "MPA stub BX1 l4: ", FIFO[i, 5]
						print "MPA stub BX1 l3: ", FIFO[i, 4]
						print "MPA stub BX1 l2: ", FIFO[i, 3]
						print "MPA stub BX1 l1: ", FIFO[i, 2]
						print "MPA stub BX1 l0: ", FIFO[i, 1]
					else:
						print "CHIPTYPE UNKNOWN"
		print "State of FSM after reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		CSV.ArrayToCSV(FIFO, "../SSA_Results/seu_tmp.csv")



	##############################################################
	def Run_Test_SEU_ClusterData(self, strip =[10,20,30,40,50,60,70], delay_after_fast_reset = 0, run_time = 5, display = 1, filename = '', runname = '', delay = 71):
		#reset(); reset(); sleep(0.1)
		p1, p2 = self.Evaluate_Pattern(strip)
		sleep(0.1); self.loadCheckPatternOnFC7(p1, p2, 1, display)
		sleep(0.1); self.Configure_Injection(strip, analog_injection = 0)
		sleep(0.1); self.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", delay)
		sleep(0.1); Configure_TestPulse_SSA(delay_after_fast_reset = 0, delay_after_test_pulse = 1, delay_before_next_pulse = 0, number_of_test_pulses = 0, enable_rst_L1 = 0, enable_initial_reset = 1)
		sleep(0.1); self.delayDataTaking()
		sleep(0.1); self.RunStateMachine(run_time = run_time, display = display)
		sleep(0.1); SendCommand_CTRL("stop_trigger")
		sleep(0.1);
		CntBad  = fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
		CntGood = fc7.read("stat_phy_slvs_compare_number_good_data")
		print "____________________________________________"
		print("->  \tSEU Cluster-Data  -> Number of bad  BX: %12d (%10.6f%%)" % (CntBad,  100*np.float(CntBad)/(CntGood+CntBad)))
		print("->  \tSEU Cluster-Data  -> Number of good BX: %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad)))
		print "____________________________________________"

		return [CntGood, CntBad]
		# self.ReadFIFOs()
		# seuutil.ReadFIFOs()


#  seuutil.Run_Test_SEU_ClusterData()
#  seuutil.ReadFIFOs()
