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

class SSA_SEU():

	def __init__(self, ssa, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map; self.ssa = ssa;
		self.analog_mux_map = analog_mux_map; self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;	self.fc7 = FC7;	self.pwr = pwr; self.timer_data_taking = 10;

	def configureChips(self, strip_in, analog_injection = 0):
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
		for st in strip_in:
			if(st>0 and st<121):
				self.I2C.strip_write("ENFLAGS", st, 0b01001)
				self.I2C.strip_write("DigCalibPattern_L", st, 0x1)
		sleep(0.1)


	def loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3):
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3)
		sleep(0.5)
		print "Content of the patterns1 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns1")
		print "Content of the patterns2 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns2")
		print "Content of the patterns3 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns3")



	def delayDataTaking(self):
		#below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
		print "BX indicator for SSA centroid data:", fc7.read("stat_phy_slvs_compare_fifo_bx_indicator")
		#fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
		sleep(1)


	def RunStateMachine(self):
		#reset()
		FSM = fc7.read("stat_phy_slvs_compare_state_machine")
		print "State of FSM before starting: " , FSM
		if (FSM == 4):
			print "Error in FSM"
			return
		print "Almost full flag of FIFO before starting: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")

		fc7.write("ctrl_phy_SLVS_compare_start",1)

		print "State of FSM after starting: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "Almost full flag of FIFO after starting: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")

		#start taking data and check the 80% full threshold of the FIFO
		FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		timer = 0
		while(FIFO_almost_full != 1 and timer < self.timer_data_taking):
			FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			timer = timer + 1
			print "Timer at: ", timer, "/", self.timer_data_taking
			print "State of FSM during comparing: " , fc7.read("stat_phy_slvs_compare_state_machine")
			print "FIFO almost full full: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			print "Number of bad  BX: ", fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
			print "Number of good BX: ", fc7.read("stat_phy_slvs_compare_number_good_data")
			print "-----------------------------------------------------------------------------"
			sleep(1)

		fc7.write("ctrl_phy_SLVS_compare_stop",1)

		print "State of FSM after stopping: " , fc7.read("stat_phy_slvs_compare_state_machine")

		if(timer == self.timer_data_taking and FIFO_almost_full == 0):
			print "data taking stopped because reached the adequate time"
		elif(FIFO_almost_full == 1 and timer < self.timer_data_taking ):
			print "data taking stopped because the FIFO reached the 80%"
		else:
			print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"


	def parse_to_bin32(self, input):
		return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

	def parse_to_bin8(self, input):
		return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

	def ReadFIFOs(self, chip = 'SSA'):
		print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
		print "State of FSM before reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "Now printing the data in the FIFO:"
		stat_phy_slvs_compare_data_ready = fc7.read("stat_phy_slvs_compare_data_ready")
		i = 0

		"""package2 = fc7.fifoRead("ctrl_phy_SLVS_compare_read_data2_fifo", 17000)
		p l5, l6, l7ackage4 = fc7.fifoRead("ctrl_phy_SLVS_compare_read_data4_fifo", 17000)
		for i in range(16384):
			print "Package2 #", i+1, ": ", package2[i]
			print "Package4 #", i+1, ": ", package4[i]
		print("State of FSM after reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine"))
		print("Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full"))"""

		for i in range (0,16386):
		#for i in range (0,10):
				print("--------------------------")
				print("Entry number: ", i ," in the FIFO:")
				fifo1_word = fc7.read("ctrl_phy_SLVS_compare_read_data1_fifo")
				fifo2_word = fc7.read("ctrl_phy_SLVS_compare_read_data2_fifo")
				fifo3_word = fc7.read("ctrl_phy_SLVS_compare_read_data3_fifo")
				fifo4_word = fc7.read("ctrl_phy_SLVS_compare_read_data4_fifo")
				print "MPA: BX counter, 0x0000, BX0 data (l4, l3, l2, l1, l0) and  BX1 data (l4, l3, l2, l1, l0)"
				print "SSA: 0x0000, BX counter, 0x0000 and centroid data (l7, l6, l5, l4, l3, l2, l1, l0)"
				print(self.parse_to_bin32(fifo4_word),self.parse_to_bin32(fifo3_word),self.parse_to_bin32(fifo2_word),self.parse_to_bin32(fifo1_word))
				print(fifo4_word,fifo3_word,fifo2_word,fifo1_word)

				print "BX counter:", fifo4_word
				if(chip == "MPA"):
					print "MPA stub BX0 l4: ", self.parse_to_bin8((fifo3_word & 0x0000ff00)>>8)
					print "MPA stub BX0 l3: ", self.parse_to_bin8(fifo3_word & 0x000000ff)
					print "MPA stub BX0 l2: ", self.parse_to_bin8((fifo2_word & 0xff000000)>>24)
					print "MPA stub BX0 l1: ", self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
					print "MPA stub BX0 l0: ", self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8)

					print "MPA stub BX1 l4: ", self.parse_to_bin8(fifo2_word & 0x000000ff)
					print "MPA stub BX1 l3: ", self.parse_to_bin8((fifo1_word & 0xff000000)>>24)
					print "MPA stub BX1 l2: ", self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
					print "MPA stub BX1 l1: ", self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
					print "MPA stub BX1 l0: ", self.parse_to_bin8(fifo1_word & 0x000000ff)
				elif(chip == "SSA"):
					print "SSA centroid l7: ", self.parse_to_bin8((fifo2_word & 0xff000000)>>24)
					print "SSA centroid l6: ", self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
					print "SSA centroid l5: ", self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8)
					print "SSA centroid l4: ", self.parse_to_bin8(fifo2_word & 0x000000ff)

					print "SSA centroid l3: ", self.parse_to_bin8((fifo1_word & 0xff000000)>>24)
					print "SSA centroid l2: ", self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
					print "SSA centroid l1: ", self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
					print "SSA centroid l0: ", self.parse_to_bin8(fifo1_word & 0x000000ff)
				else:
					print "CHIPTYPE UNKNOWN"

		print "State of FSM after reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full")

	def RunSEU(self, strip = [50,0,0,0,0,0,0,0], delay_after_fast_reset = 0):
		#mpa_reset()
		reset()
		#sleep(1)
		#align_out()
		pattern1 = ((strip[3] & 0xff)<<0) | ((strip[2] & 0xff)<<8) | ((strip[1] & 0xff)<<16) | ((strip[0] & 0xff)<<24)
		pattern2 = ((strip[4] & 0xff)<<0) | ((strip[5] & 0xff)<<8) | ((strip[6] & 0xff)<<16) | ((strip[7] & 0xff)<<24)
		pattern3 = 0

		pattern1 = 0x00000050
		pattern2 = 0x00000000
		pattern3 = 0

		self.loadCheckPatternOnFC7(pattern1, pattern2, pattern3)
		self.configureChips(strip, analog_injection = 0)

		Configure_TestPulse_MPA(delay_after_fast_reset = 0, delay_after_test_pulse = 0, delay_before_next_pulse = 0, number_of_test_pulses = 0, enable_rst_L1 = 0)
		#Configure_TestPulse_MPA_SSA(number_of_test_pulses = 0, delay_before_next_pulse = 1)

		sleep(0.001)
		#Configure_SEU(cal_pulse_period = 1, l1a_period = 20, number_of_cal_pulses = 0)

		self.fc7.SendCommand_CTRL("start_trigger")
		sleep(0.1)
		self.delayDataTaking()
		self.RunStateMachine()
		SendCommand_CTRL("stop_trigger")
		print "Number of bad  BX: ", fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
		print "Number of good BX: ", fc7.read("stat_phy_slvs_compare_number_good_data")
