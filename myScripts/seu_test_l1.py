import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from mpa_methods.cal_utility import *
from mpa_methods.power_utility import *
from mpa_methods.bias_calibration import *
from myScripts.BasicMultimeter import *


timer_data_taking = 3

def configureChipsL1(cluster_col, cluster_row, cluster_width, analog_injection = 0):
	#have to reset the chip so that the l1 counter would start at 1
	SendCommand_CTRL("fast_fast_reset")
	#here define the way to generate the fixed l1 payload pattern on the MPA/SSA
	sleep(0.1)
	#For the emulator:
	#SendCommand_I2C(command type, hybrid_id, chip_id, page, read, register_address, data, ReadBack)
	#For the chip:
	pcluster = ""
	scluster = ""
	n_pclust = 1
	n_sclust = 0
	activate_I2C_chip()
	disable_pixel(0,0)
	if (analog_injection):
		set_calibration(100)
		set_threshold(200)
	else:
		I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
	for i in range(0, n_pclust):
		for j in range(0, cluster_width[i]):
			if (analog_injection):
				enable_pix_EdgeBRcal(cluster_row[i], cluster_col[i] + j)
			else:
				I2C.pixel_write('ENFLAGS', cluster_row[i], cluster_col[i] + j , 0x20)
		pcluster = pcluster + bin(cluster_col[i]).lstrip('-0b').zfill(7) + bin(cluster_width[i]-1).lstrip('-0b').zfill(3) + bin(cluster_row[i]-1).lstrip('-0b').zfill(4)

	payload = bin(2).lstrip('-0b').zfill(2) +  bin(0).lstrip('-0b').zfill(9) + "0" + bin(n_sclust).lstrip('-0b').zfill(5) + bin(n_pclust).lstrip('-0b').zfill(5) + "0" + scluster + pcluster + bin(3).lstrip('-0b').zfill(7) + bin(0).lstrip('-0b').zfill(32)
	pattern7 = 0
	pattern6 = 0
	pattern5 = 0
	pattern4 = 0
	pattern3 = 0
	pattern2 = 0
	pattern1 = 0
	try:
		pattern7 = int(payload[0:   32], 2)
		pattern6 = int(payload[32:  64], 2)
		pattern5 = int(payload[64:  96], 2)
		pattern4 = int(payload[96:  128], 2)
		pattern3 = int(payload[128: 160], 2)
		pattern2 = int(payload[160: 192], 2)
		pattern1 = int(payload[192: 224], 2)
	except ValueError:
		print "Empty Pattern"
	loadCheckPatternOnFC7L1(pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7)

	#ReadStatus()
	#ReadChipData(0,0)
	#return payload
	return payload, pattern7, pattern6, pattern5, pattern4, pattern3, pattern2, pattern1


def loadCheckPatternOnFC7L1(pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7):

	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1",pattern1)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2",pattern2)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3",pattern3)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4",pattern4)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5",pattern5)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6",pattern6)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7",pattern7)

	sleep(0.5)

	print "Content of the patterns1 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1"))
	print "Content of the patterns2 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2"))
	print "Content of the patterns3 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3"))
	print "Content of the patterns4 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4"))
	print "Content of the patterns5 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5"))
	print "Content of the patterns6 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6"))
	print "Content of the patterns7 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7"))

def printInfo(message):
	print "*************************"
	print message
	print "State of FSM: " , fc7.read("stat_phy_l1_slvs_compare_state_machine")
	print "Fifo almost full: ", fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
	print "Header # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
	print "Trigger # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
	print "number of events written to FIFO", fc7.read("stat_phy_l1_slvs_compare_numbere_events_written_to_fifo")
	print "number of matched events:", fc7.read("stat_phy_l1_slvs_compare_number_good_data")
	print "*************************"

def RunStateMachineL1():
	printInfo("BEFORE STATE MACHINE RUNNING:")

	fc7.write("ctrl_phy_l1_SLVS_compare_start", 1)

	printInfo("AFTER START STATE MACHINE:")

	#start the triggering
	#Configure_Fast(9000, 1000, 3, 0, 0)
	SendCommand_CTRL("start_trigger")
	printInfo("AFTER START TRIGGER:")

	#start taking data and check the 80% full threshold of the FIFO
	FIFO_almost_full = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
	timer = 0
	while(FIFO_almost_full != 1 and timer < timer_data_taking):
		FIFO_almost_full = fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		timer = timer + 1
		print "Timer at: ", timer, "/", timer_data_taking
		print "State of FSM during comparing: " , fc7.read("stat_phy_l1_slvs_compare_state_machine")
		print "FIFO almost full full: " , fc7.read("stat_phy_l1_slvs_compare_fifo_almost_full")
		print "-----------------------------------------------------------------------------"
		sleep(1)

	SendCommand_CTRL("stop_trigger")
	sleep(1)
	fc7.write("ctrl_phy_SLVS_compare_stop",1)

	printInfo("STATE MACHINE AND TRIGGER STOPPED:")


	if(timer == timer_data_taking and FIFO_almost_full == 0):
		print "data taking stopped because reached the adequate time"
	elif(FIFO_almost_full == 1 and timer < timer_data_taking ):
		print "data taking stopped because the FIFO reached the 80%"
	else:
		print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"


def parse_to_bin32(input):
	return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

def parse_to_bin8(input):
	return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

def parse_to_bin9(input):
	return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)

def ReadFIFOsL1(chip, n = 16386):

	print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
	printInfo("BEFORE READING FIFO:")
	print "Now printing the data in the FIFO:"
	i = 0


	for i in range (0,n):
			print("--------------------------")
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
			print(parse_to_bin32(fifo7_word),parse_to_bin32(fifo6_word),parse_to_bin32(fifo5_word),parse_to_bin32(fifo4_word),parse_to_bin32(fifo3_word),parse_to_bin32(fifo2_word),parse_to_bin32(fifo1_word))
			print "l1 counter: ", parse_to_bin9((fifo7_word & 0x3FE00000)>>21)
			print "l1 counter: ", (fifo7_word & 0x3FE00000)>>21
			print "BX counter: ", fifo8_word
	#enablePrint()
	printInfo("AFTER READING FIFO:")
	#blockPrint()

def RunSEU_L1(col, row, width, cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 0):
	mpa_reset()
	reset()
	sleep(1)
	align_out()
	payload, pattern7, pattern6, pattern5, pattern4, pattern3, pattern2, pattern1 = configureChipsL1(col,  row, width,  analog_injection = 0)
	I2C.row_write('L1Offset_1', 0,  latency - diff)
	I2C.row_write('L1Offset_2', 0,  0)
	I2C.peri_write('EdgeSelT1Raw', 0)
	I2C.peri_write("ConfSLVS", 0b00111111)
#	I2C.row_write('MemGatEn', 0,  1)
	align_out()
	fc7.write("cnfg_fast_backpressure_enable", 0)
	if (skip == 0):
		Configure_TestPulse_MPA(delay_after_fast_reset = 512, delay_after_test_pulse = latency, delay_before_next_pulse = cal_pulse_period, number_of_test_pulses = 0, enable_rst_L1 = 1)
	else:
		Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses = 0)
	RunStateMachineL1()
	SendCommand_CTRL("stop_trigger")
	ReadFIFOsL1("MPA", n = 1)
	return payload, pattern7, pattern6, pattern5, pattern4, pattern3, pattern2, pattern1

def LatencyScan(col, row, width, cal_pulse_period = 10, l1a_period = 101, latency = range(95,106), diff = 2, delay_after_fast_reset = 0):
	for l in latency:
		#enablePrint()
		print "Latency Scan: ", l
		#blockPrint()
		payload, pattern7, pattern6, pattern5, pattern4, pattern3, pattern2, pattern1 = RunSEU_L1(col = [3], row = [10], width = [1], cal_pulse_period = 10, l1a_period = 101, latency = l, diff = 2, delay_after_fast_reset = 0)

# fc7.read("stat_fast_trigger_in_counter")

# payload, pattern7, pattern6, pattern5, pattern4, pattern3, pattern2, pattern1 = RunSEU_L1(col = [3], row = [10], width = [1], cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 0)
