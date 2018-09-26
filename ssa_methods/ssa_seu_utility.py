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
### seuutil.L1_RunStateMachine()
#### seuutil.Stub_ReadFIFOs()

class SSA_SEU_utilities():

	def __init__(self, ssa, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map; self.ssa = ssa;
		self.analog_mux_map = analog_mux_map; self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;	self.fc7 = FC7;	self.pwr = pwr;

	##############################################################
	def Run_Test_SEU(self, strip =[10,20,30,40], hipflags = [], cal_pulse_period = 1, l1a_period = 39, latency = 100, run_time = 5, display = 1, filename = '', runname = '', delay = 72):
		sleep(0.1); SendCommand_CTRL("global_reset")
		sleep(0.1); SendCommand_CTRL("fast_fast_reset")
		sleep(1)
		s1, s2, s3 = self.Stub_Evaluate_Pattern(strip)
		p1, p2, p3, p4, p5, p6, p7 = self.L1_Evaluate_Pattern(strip, hipflags)
		sleep(0.1); self.Configure_Injection(strip_list = strip, hipflag_list = hipflags, analog_injection = 0)
		sleep(0.1); SendCommand_CTRL("global_reset")
		sleep(0.1); self.Stub_loadCheckPatternOnFC7(pattern1 = s1, pattern2 = s2, pattern3 = 1, lateral = s3, display = display)
		sleep(0.1); self.L1_loadCheckPatternOnFC7(p1, p2, p3, p4, p5, p6, p7, display = display)
		sleep(0.1); Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses = 0, initial_reset = 1)
		fc7.write("cnfg_fast_backpressure_enable", 0)
		sleep(0.1); self.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", delay)
		sleep(0.1); self.RunStateMachine_L1_and_Stubs(timer_data_taking = run_time)
		#sleep(0.1); self.Stub_RunStateMachine(run_time = run_time, display = display)
		sleep(0.1); SendCommand_CTRL("stop_trigger")
		#ReadFIFOs("MPA", 1)
		#ReadFIFOsL1("MPA", 1)
		print "Number of good BX: ", fc7.read("stat_phy_slvs_compare_number_good_data")

	##############################################################
	def Run_Test_SEU_ClusterData(self, strip =[10,20,30,40,50,60,70], hipflags = [], delay_after_fast_reset = 0, run_time = 5, display = 1, filename = '', runname = '', delay = 72):
		SendCommand_CTRL("global_reset")
		p1, p2, p3 = self.Stub_Evaluate_Pattern(strip)

		sleep(0.1);self.Stub_loadCheckPatternOnFC7(pattern1 = p1, pattern2 = p2, pattern3 = 1, lateral = p3, display = display)
		sleep(0.1); self.Configure_Injection(strip_list = strip, hipflag_list = hipflags, analog_injection = 0)
		sleep(0.1); self.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", delay)
		sleep(0.1); Configure_TestPulse_SSA(delay_after_fast_reset = 0, delay_after_test_pulse = 1, delay_before_next_pulse = 0, number_of_test_pulses = 0, enable_rst_L1 = 0, enable_initial_reset = 1)
		sleep(0.1); self.Stub_delayDataTaking()
		sleep(0.1); self.Stub_RunStateMachine(run_time = run_time, display = display)
		sleep(0.1); SendCommand_CTRL("stop_trigger")
		sleep(0.1);
		CntBad  = fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
		CntGood = fc7.read("stat_phy_slvs_compare_number_good_data")
		print "____________________________________________"
		print("->  \tSEU Cluster-Data  -> Number of good BX: %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad)))
		print("->  \tSEU Cluster-Data  -> Number of bad  BX: %12d (%10.6f%%)" % (CntBad,  100*np.float(CntBad)/(CntGood+CntBad)))
		print "____________________________________________"
		return [CntGood, CntBad]

	##############################################################
	def Run_Test_SEU_L1(self, strip = [1,9,17,25,33,17,118,119,120], hipflags = [], run_time = 5, delay_after_fast_reset = 512, latency = 500, shift = 0, cal_pulse_period = 100, display = 1, filename = '', runname = '', delay = 71, cnt_shift = 0):
		chip = 'SSA'
		SendCommand_CTRL("global_reset")
		sleep(1)
		p1, p2, p3, p4, p5, p6, p7 = self.L1_Evaluate_Pattern(strip, hipflags)
		self.Configure_Injection(strip_list = strip, hipflag_list = hipflags, analog_injection = 0, latency = latency)
		self.L1_loadCheckPatternOnFC7(p1, p2, p3, p4, p5, p6, p7, display = display)
		#Configure_TestPulse_MPA(delay_after_fast_reset = 512, delay_after_test_pulse = latency+3+offset, delay_before_next_pulse = cal_pulse_period, number_of_test_pulses = 0, enable_rst_L1 = 1)
		#Configure_TestPulse_SSA(delay_after_fast_reset = delay_after_fast_reset,delay_after_test_pulse = latency+3+shift,	delay_before_next_pulse = cal_pulse_period,	number_of_test_pulses = 0,	enable_rst_L1 = 0,	enable_L1 = 1)
		SendCommand_CTRL('fast_fast_reset')
		sleep(0.1)
		for i in range(cnt_shift):
			send_trigger()
		fc7.write("cnfg_fast_backpressure_enable", 0)
		fc7.write("cnfg_fast_initial_fast_reset_enable", 0 )
		fc7.write("cnfg_fast_delay_after_fast_reset",  delay_after_fast_reset )
		fc7.write("cnfg_fast_delay_after_test_pulse",   latency+3+shift )
		fc7.write("cnfg_fast_delay_before_next_pulse",  cal_pulse_period)
		fc7.write("cnfg_fast_tp_fsm_fast_reset_en",  0 )
		fc7.write("cnfg_fast_tp_fsm_test_pulse_en",  1)
		fc7.write("cnfg_fast_tp_fsm_l1a_en",  1 )
		fc7.write("cnfg_fast_triggers_to_accept",  0 )
		fc7.write("cnfg_fast_source", 6)
		fc7.write("cnfg_fast_initial_fast_reset_enable",  0 )
		sleep(0.1)
		SendCommand_CTRL("load_trigger_config")
		sleep(0.1)
		self.L1_RunStateMachine(timer_data_taking = run_time)
		## SendCommand_CTRL("stop_trigger")
		#self.L1_ReadFIFOs(nevents = 5)878
		self.L1_printInfo('        SUMMARY        ')
		n_in_fifo  = fc7.read("stat_phy_l1_slvs_compare_numbere_events_written_to_fifo")
		n_correct  = fc7.read("stat_phy_l1_slvs_compare_number_good_data")
		n_triggers = fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
		n_headers  = fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
		return [n_correct, n_in_fifo, (n_triggers-n_headers)]

	##############################################################
	def Configure_Injection(self, strip_list = [], hipflag_list = [], lateral = [], analog_injection = 0, latency = 100):
		#here define the way to generate stub/centroid data pattern on the MPA/SSA
		utils.activate_I2C_chip()
		self.ssa.ctrl.activate_readout_normal(mipadapterdisable = 1)
		self.I2C.peri_write("CalPulse_duration", 1)
		self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0x0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0x0)
		self.I2C.peri_write('L1-Latency_MSB', (latency & 0xff00) >> 8)
		self.I2C.peri_write('L1-Latency_LSB', (latency & 0x00ff) >> 0)
		word = np.zeros(16, dtype = np.uint8)
		row = np.zeros(16, dtype = np.uint8)
		pixel = np.zeros(16, dtype = np.uint8)
		l = np.zeros(10, dtype = np.uint8)
		for st in strip_list:
			if(st>0 and st<121):
				self.I2C.strip_write("DigCalibPattern_L", st, 0x1)
		for st in hipflag_list:
			if(st>0 and st<121):
				self.I2C.strip_write("DigCalibPattern_H", st, 0x1)
		sleep(0.1)

	##############################################################
	def Stub_Evaluate_Pattern(self, strip_list):
		strip = np.sort(strip_list)
		slist = np.zeros(8, dtype = ctypes.c_uint32)
		lateral_left = 0; lateral_right = 0;
		for i in range(np.size(strip)):
			if strip[i] < 8:
				lateral_left += (0x1 << strip[i])
			if (strip[i] < 120 and strip[i] >= 112):
				lateral_right += (0x1 << (strip[i]-112))
			else:
				slist[i] = ((strip[i] + 3) << 1) & 0xff
		p1 = (slist[0]<<0) | (slist[1]<<8) | (slist[2]<<16) | (slist[3]<<24)
		p2 = (slist[4]<<0) | (slist[5]<<8) | (slist[6]<<16) | (slist[7]<<24)
		p3 = ((lateral_right & 0xFF) << 8) + (lateral_left & 0xFF)
		return p1, p2, p3

	##############################################################
	def L1_Evaluate_Pattern(self, strip_list, hflag_list):
		strip = np.sort(strip_list)
		hfleg = np.sort(hflag_list)
		l1hit  = np.full(120, '0')
		l1flag = np.full( 24, '0')
		for st in strip:
			l1hit[ st-1 ] = '1'
		l1flag = ['0']*24
		cnt = 0
		for st in strip_list:
			if st in hflag_list:
				l1flag[cnt] = '1'
			cnt += 1
		p1 = 0x00000000
		p2 = 0x00000000
		p3 = int( '0b' + ( ''.join((l1hit[0:30])[::-1])  + '10'    ) , 2)
		p4 = int( '0b' + ( ''.join((l1hit[30:62])[::-1])  ) , 2)
		p5 = int( '0b' + ( ''.join((l1hit[62:94])[::-1])  ) , 2)
		p6 = int( '0b' + ( ''.join((l1flag[0:6])[::-1])   + ''.join((l1hit[94:120])[::-1])  ) , 2)
		p7 = int( '0b' + ( '0'*10 + ''.join((l1flag[6:24])[::-1])  ) , 2)
		#print l1hit
		#print l1flag
		return p1, p2, p3, p4, p5, p6, p7

		#pattern7(17 downto 0) = bit(23 downto 6) of the MIP flags
		#pattern6(31 downto 26) = bit (5 downto 0) of the MIP flags
		#pattern6(25 downto 0) = bit (119 downto 94) of the hit info
		#pattern5 = bit (93 downto 61) of the hit info
		#pattern4 = bit (60 downto 29) of the hit info
		#pattern3(31 downto 2)= last 30 bits of the hit info
		#pattern3(1)= trailer bit

		############################
		#########for SSA:###########
		############################
		##### as am using the same state machine and the same registers the mapping for the SSA configuration check registers might look a bit odd. The state machine actaully saves a bit longer the data then the SSA l1 frame length. The l1 counter is incremented on FPGA, for the moment the BX counter is not checked.
		##### pattern7(18 downto 0) = bit(23 downto 5) of the MIP flags
		##### pattern6(31 downto 27) = bit (4 downto 0) of the MIP flags
		##### pattern6(26 downto 0) = bit (119 downto 93) of the hit info
		##### pattern5 = bit (92 downto 62) of the hit info
		##### pattern4 = bit (61 downto 30) of the hit info
		##### pattern3(31 downto 3)= last 29 bits of the hit info
		##### pattern3(2)= trailer bit
		#####
		##### pattern2 = not used
		##### pattern1 = not used
		#####
		##### pattern1 = 0x00000000
		##### pattern2 = 0x00000000
		##### pattern3                 # [31:3] = last 29 bits of the hit info
		#####
		##### #Example: last 8 hits: 10101010, HIP: 000011110000111100001111
		##### pattern7 = 0b00000000000001111000011110000111
		##### pattern6 = 0b10000000000000000000000000000000
		##### pattern5 = 0x00000000
		##### pattern4 = 0x00000000
		##### #correct
		##### pattern3 = 0b00000000000000000000010101010100
		##### #wrong
		##### #pattern3 = 0b10000000000000000000010101010100
		##### pattern2 = 0x00000000
		##### pattern1 = 0x00000000

	##############################################################
	def Stub_loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, lateral = 0, display = 2):
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2)
		fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3)
		#### fc7.write("cnfg_phy_lateral_MPA_SSA_SEU_check_patterns1",lateral)

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
					FIFO[i,8] = (fifo2_word & 0xff000000)>>24
					FIFO[i,7] = (fifo2_word & 0x00ff0000)>>16
					FIFO[i,6] = (fifo2_word & 0x0000ff00)>>8
					FIFO[i,5] = fifo2_word & 0x000000f
					FIFO[i,4] = (fifo1_word & 0xff000000)>>24
					FIFO[i,3] = (fifo1_word & 0x00ff0000)>>16
					FIFO[i,2] = (fifo1_word & 0x0000ff00)>>8
					FIFO[i,1] = (fifo1_word & 0x000000ff)
				elif(chip == "MPA"):
					FIFO[i,10] = (fifo3_word & 0x0000ff00)>>8
					FIFO[i, 9] = fifo3_word & 0x000000ff
					FIFO[i, 8] = (fifo2_word & 0xff000000)>>24
					FIFO[i, 7] = (fifo2_word & 0x00ff0000)>>16
					FIFO[i, 6] = (fifo2_word & 0x0000ff00)>>8
					FIFO[i, 5] = fifo2_word & 0x000000ff
					FIFO[i, 4] = (fifo1_word & 0xff000000)>>24
					FIFO[i, 3] = (fifo1_word & 0x00ff0000)>>16
					FIFO[i, 2] = (fifo1_word & 0x0000ff00)>>8
					FIFO[i, 1] = fifo1_word & 0x000000ff
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

	#####################################################################################################################
	#####################################################################################################################
	def L1_phase_tuning_MPA_emulator(self):
		sleep(0.1)
		fc7.write("ctrl_phy_phase_tune_again", 1)
		count_waiting = 0
		while(fc7.read("stat_phy_phase_tuning_done") == 0):
			sleep(0.5)
			print "Phase tuning in state: ", fc7.read("stat_phy_phase_fsm_state_chip0")
			print "Waiting for the phase tuning"
			fc7.write("ctrl_phy_phase_tune_again", 1)
			print("resend phase tuning signal")

	##############################################################
	def L1_loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, display):
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1",pattern1)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2",pattern2)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3",pattern3)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4",pattern4)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5",pattern5)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6",pattern6)
		fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7",pattern7)
		sleep(0.5)
		if(display > 1):
			print "Content of the patterns1 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1"))
			print "Content of the patterns2 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2"))
			print "Content of the patterns3 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3"))
			print "Content of the patterns4 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4"))
			print "Content of the patterns5 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5"))
			print "Content of the patterns6 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6"))
			print "Content of the patterns7 cnfg register: ",self.parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7"))

	##############################################################
	def L1_printInfo(self, message):
		state      = fc7.read("stat_phy_l1_slvs_compare_state_machine")
		full       = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		n_in_fifo  = fc7.read("stat_phy_l1_slvs_compare_numbere_events_written_to_fifo")
		n_correct  = fc7.read("stat_phy_l1_slvs_compare_number_good_data")
		n_triggers = fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
		n_headers  = fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
		print("____________________________________________________________________________\n")
		print(message)
		print("->  \tSEU L1-Data       -> FSM state:          %12d "           % (state))
		print("->  \tSEU L1-Data       -> Full Flag:          %12d "           % (full))
		print("->  \tSEU L1-Data       -> Correct events:     %12d (%10.6f%%)" % (n_correct, 100*np.float(n_correct)/(n_triggers)))
		print("->  \tSEU L1-Data       -> Packets with Error: %12d (%10.6f%%)" % (n_in_fifo,  100*np.float(n_in_fifo)/(n_triggers)))
		print("->  \tSEU L1-Data       -> Packets Missing:    %12d (%10.6f%%)" % ((n_triggers-n_headers),  100*np.float(n_triggers-n_headers)/(n_triggers)))

	##############################################################
	def printInfo(self, message):
		print "*************************"
		print message
		print "Number of good BX STUBS: ", fc7.read("stat_phy_slvs_compare_number_good_data")
		print "*** L1 ***"
		print "State of FSM: " , fc7.read("stat_phy_l1_slvs_compare_state_machine")
		print "Fifo almost full: ", fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		print "Header # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
		print "Trigger # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
		print "number of events written to FIFO", fc7.read("stat_phy_l1_slvs_compare_numbere_events_written_to_fifo")
		print "number of matched events:", fc7.read("stat_phy_l1_slvs_compare_number_good_data")
		print "*************************"

	##############################################################
	def L1_RunStateMachine(self, timer_data_taking = 5, display = 0):
		if(display > 1):
			self.L1_printInfo("BEFORE STATE MACHINE RUNNING:")
		fc7.write("ctrl_phy_l1_SLVS_compare_start",1)
		if(display > 1):
			self.L1_printInfo("AFTER START STATE MACHINE:")
		#start the triggering
		#Configure_Fast(0, 1000, 3, 0, 0)
		#fc7.write("cnfg_fast_backpressure_enable",0)
		#sleep(0.5)
		SendCommand_CTRL("start_trigger")
		if(display > 1):
			self.L1_printInfo("AFTER START TRIGGER:")
		#start taking data and check the 80% full threshold of the FIFO
		FIFO_almost_full = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		timer = 0
		while(FIFO_almost_full != 1 and timer < timer_data_taking):
			FIFO_almost_full = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
			timer = timer + 1
			message =  "Timer at: ", timer, "/", timer_data_taking
			self.L1_printInfo(message)
			sleep(1)
		SendCommand_CTRL("stop_trigger")
		sleep(1)
		fc7.write("ctrl_phy_SLVS_compare_stop",1)
		self.L1_printInfo("STATE MACHINE AND TRIGGER STOPPED:")
		if(timer == timer_data_taking and FIFO_almost_full == 0):
			print "data taking stopped because reached the adequate time"
		elif(FIFO_almost_full == 1 and timer < timer_data_taking ):
			print "data taking stopped because the FIFO reached the 80%"
		else:
			print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"

	##############################################################
	def L1_ReadFIFOs(self, chip = 'SSA', nevents = 16386):
		print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
		self.L1_printInfo("BEFORE READING FIFO:")
		print "Now printing the data in the FIFO:"
		i = 0
		for i in range (0,nevents):
				print "________________________________________________________________________________________"
				print("Entry number: ", i ," in the FIFO:")
				fifo1_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data1_fifo")
				fifo2_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data2_fifo")
				fifo3_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data3_fifo")
				fifo4_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data4_fifo")
				fifo5_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data5_fifo")
				fifo6_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data6_fifo")
				fifo7_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data7_fifo")
				fifo8_word = fc7.read("ctrl_phy_l1_SLVS_compare_read_data8_fifo")

				print "Full l1 data package without the header (MSB downto LSB): "
				print(self.parse_to_bin32(fifo7_word),self.parse_to_bin32(fifo6_word),self.parse_to_bin32(fifo5_word),self.parse_to_bin32(fifo4_word),self.parse_to_bin32(fifo3_word),self.parse_to_bin32(fifo2_word),self.parse_to_bin32(fifo1_word))
				if(chip == "MPA"):
					print "l1 counter: ", (fifo7_word & 0x3FE00000)>>21
				if(chip == "SSA"):
					print "L1 counter: ", (fifo7_word >>27) & 0xf
					print "BX counter: ", fifo8_word
		self.L1_printInfo("AFTER READING FIFO:")

	##############################################################
	def RunStateMachine_L1_and_Stubs(self, timer_data_taking = 5):
		sleep(0.1)
		FSM = fc7.read("stat_phy_slvs_compare_state_machine")
		print "State of FSM before starting: " , FSM
		if (FSM == 4):
			print "Error in FSM"
			return
		print "Almost full flag of FIFO before starting: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")


		fc7.write("ctrl_phy_l1_SLVS_compare_start",1)
		fc7.write("ctrl_phy_SLVS_compare_start",1)
		SendCommand_CTRL("start_trigger")
		#self.printInfo("AFTER START STATE MACHINE:")
		#self.printInfo("AFTER START TRIGGER:")
		print "State of FSM after starting: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "Almost full flag of FIFO after starting: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		#start taking data and check the 80% full threshold of the FIFO
		FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		FIFO_almost_full_L1 = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		timer = 0
		while(FIFO_almost_full != 1 and FIFO_almost_full_L1 != 1 and timer < timer_data_taking):
			FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			FIFO_almost_full_L1 = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
			timer = timer + 1
			print "Timer at: ", timer, "/", timer_data_taking
			print "----------------------------- STUB -------------------------------------------"
			CntBad  = fc7.read("stat_phy_slvs_compare_numbere_events_written_to_fifo")
			CntGood = fc7.read("stat_phy_slvs_compare_number_good_data")
			state   = (fc7.read("stat_phy_slvs_compare_state_machine"))
			full    = (fc7.read("stat_phy_slvs_compare_fifo_almost_full"))
			print("->  \tSEU Cluster-Data  -> Iteration number:  %12d / %0d" % (timer, timer_data_taking))
			print("->  \tSEU Cluster-Data  -> State of FSM:      %12d" % (state))
			print("->  \tSEU Cluster-Data  -> FIFO almost full:  %12d" % (full))
			print("->  \tSEU Cluster-Data  -> Number of bad  BX: %12d" % (CntBad  ))
			print("->  \tSEU Cluster-Data  -> Number of good BX: %12d" % (CntGood ))
			print "------------------------------ L1 -------------------------------------------"
			print "->  \tSEU L1-Data       -> State of FSM: " , fc7.read("stat_phy_l1_slvs_compare_state_machine")
			print "->  \tSEU L1-Data       -> Fifo almost full: ", fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
			print "->  \tSEU L1-Data       -> number of events written to FIFO", fc7.read("stat_phy_l1_slvs_compare_numbere_events_written_to_fifo")
			print "->  \tSEU L1-Data       -> number of matched events:", fc7.read("stat_phy_l1_slvs_compare_number_good_data")
			print "->  \tSEU L1-Data       -> number of l1 triggers sent during the state machine running:", fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
			print "->  \tSEU L1-Data       -> number l1 headers found:", fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
			print "-----------------------------------------------------------------------------"
			sleep(1)

		fc7.write("ctrl_phy_SLVS_compare_stop",1)
		SendCommand_CTRL("stop_trigger")

		self.L1_printInfo("STATE MACHINE AND TRIGGER STOPPED:")
		print "----------------------------- STUB -------------------------------------------"
		print "State of FSM after stopping: " , fc7.read("stat_phy_slvs_compare_state_machine")
		if(timer == timer_data_taking and FIFO_almost_full == 0):
			print "data taking stopped because reached the adequate time"
		elif(FIFO_almost_full == 1 and timer < timer_data_taking ):
			print "data taking stopped because the FIFO reached the 80%"
		else:
			print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"
		print "-----------------------------------------------------------------------------"
		print "------------------------------ L1 -------------------------------------------"
		print "State of FSM after stopping: " , fc7.read("stat_phy_slvs_compare_state_machine")
		if(timer == timer_data_taking and FIFO_almost_full_L1 == 0):
			print "data taking stopped because reached the adequate time"
		elif(FIFO_almost_full_L1 == 1 and timer < timer_data_taking ):
			print "data taking stopped because the FIFO reached the 80%"
		else:
			print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"
		print "-----------------------------------------------------------------------------"

	##############################################################
	def parse_to_bin32(self, input):
		return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

	##############################################################
	def parse_to_bin8(self, input):
		return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

	##############################################################
	def parse_to_bin9(self, input):
		return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)


# seuutil.L1_RunStateMachine()

#  seuutil.Run_Test_SEU_ClusterData()
#  seuutil.Stub_ReadFIFOs()

#  ssa.inject.digital_pulse([1,2,3,4,5, 116,117,118,119,120])
#
#  seuutil.Run_Test_SEU_L1(cal_pulse_period = 100)
#  seuutil.L1_ReadFIFOs(nevents = 10)
