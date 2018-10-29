import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from mpa_methods.cal_utility import *
from mpa_methods.power_utility import *
from mpa_methods.bias_calibration import *
from myScripts.BasicMultimeter import *


timer_data_taking = 3

def configureChips(row_in, pixel_in, analog_injection = 0):
	#here define the way to generate stub/centroid data pattern on the MPA/SSA
    activate_I2C_chip()
    disable_pixel(0,0)
    if (analog_injection):
        set_calibration(100)
        set_threshold(200)
    else:
        I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
    activate_pp()
    word = np.zeros(16, dtype = np.uint8)
    row = np.zeros(16, dtype = np.uint8)
    pixel = np.zeros(16, dtype = np.uint8)
    l = np.zeros(10, dtype = np.uint8)
    count = 0
    for r in row_in:
        for p in pixel_in:
            if (analog_injection):
                enable_pix_EdgeBRcal(r, p)
            else:
                I2C.pixel_write('ENFLAGS', r, p, 0x20)
            row[count] = r - 1
            pixel[count] = p*2
            count += 1

    # BX0
    #count = 0
    word0  = 0b10000 | ((0b00111 & count) << 1) | ((0b10000000 & pixel[0]) >> 7)
    word1 = ((0b01111100 & pixel[0]) >> 2)
    word2 = ((0b00000011 & pixel[0]) << 3) | 0b000 #Bending 0
    word3 = ((0b00001111 & row[0]) << 1) |((0b10000000 & pixel[1]) >> 7)
    word4 = ((0b01111100 & pixel[1]) >> 2)
    word5 = ((0b00000011 & pixel[1]) << 3) | 0b000 #Bending 0
    word6 = ((0b00001111 & row[1]) << 1) |((0b10000000 & pixel[2]) >> 7)
    word7 = ((0b01111100 & pixel[2]) >> 2)
    # BX1
    word8 = (0b0 << 5) | ((0b00000011 & pixel[2]) << 2) | 0b00 #Bending 0
    word9 = (0b0 << 5) | row[2]
    word10 = ((0b11111000 & pixel[3]) >> 3)
    word11 = ((0b00000111 & pixel[3]) << 2) | 0b00
    word12 = (0b0 << 5) | row[3]
    word13= ((0b11111000 & pixel[4]) >> 3)
    word14 = ((0b00000111 & pixel[4]) << 2) | 0b00
    word15 = (0b0 << 5) | row[4]
    ###
    l0 = (word0 & 0b10000) << 3 | (word1 & 0b10000) << 2 | (word2 & 0b10000) << 1 | (word3 & 0b10000) << 0 |  (word4 & 0b10000) >> 1 | (word5 & 0b10000) >> 2 | (word6 & 0b10000) >> 3 | (word7 & 0b10000) >> 4
    l1 = (word0 & 0b01000) << 4 | (word1 & 0b01000) << 3 | (word2 & 0b01000) << 2 | (word3 & 0b01000) << 1 |  (word4 & 0b01000) << 0 | (word5 & 0b01000) >> 1 | (word6 & 0b01000) >> 2 | (word7 & 0b01000) >> 3
    l2 = (word0 & 0b00100) << 5 | (word1 & 0b00100) << 4 | (word2 & 0b00100) << 3 | (word3 & 0b00100) << 2 |  (word4 & 0b00100) << 1 | (word5 & 0b00100) << 0 | (word6 & 0b00100) >> 1 | (word7 & 0b00100) >> 2
    l3 = (word0 & 0b00010) << 6 | (word1 & 0b00010) << 5 | (word2 & 0b00010) << 4 | (word3 & 0b00010) << 3 |  (word4 & 0b00010) << 2 | (word5 & 0b00010) << 1 | (word6 & 0b00010) << 0 | (word7 & 0b00010) >> 1
    l4 = (word0 & 0b00001) << 7 | (word1 & 0b00001) << 6 | (word2 & 0b00001) << 5 | (word3 & 0b00001) << 4 |  (word4 & 0b00001) << 3 | (word5 & 0b00001) << 2 | (word6 & 0b00001) << 1 | (word7 & 0b00001) << 0
    l5 = (word8 & 0b10000) << 3 | (word9 & 0b10000) << 2 | (word10 & 0b10000) << 1 | (word11 & 0b10000) << 0 |  (word12 & 0b10000) >> 1 | (word13 & 0b10000) >> 2 | (word14 & 0b10000) >> 3 | (word15 & 0b10000) >> 4
    l6 = (word8 & 0b01000) << 4 | (word9 & 0b01000) << 3 | (word10 & 0b01000) << 2 | (word11 & 0b01000) << 1 |  (word12 & 0b01000) << 0 | (word13 & 0b01000) >> 1 | (word14 & 0b01000) >> 2 | (word15 & 0b01000) >> 3
    l7 = (word8 & 0b00100) << 5 | (word9 & 0b00100) << 4 | (word10 & 0b00100) << 3 | (word11 & 0b00100) << 2 |  (word12 & 0b00100) << 1 | (word13 & 0b00100) << 0 | (word14 & 0b00100) >> 1 | (word15 & 0b00100) >> 2
    l8 = (word8 & 0b00010) << 6 | (word9 & 0b00010) << 5 | (word10 & 0b00010) << 4 | (word11 & 0b00010) << 3 |  (word12 & 0b00010) << 2 | (word13 & 0b00010) << 1 | (word14 & 0b00010) << 0 | (word15 & 0b00010) >> 1
    l9 = (word8 & 0b00001) << 7 | (word9 & 0b00001) << 6 | (word10 & 0b00001) << 5 | (word11 & 0b00001) << 4 |  (word12 & 0b00001) << 3 | (word13 & 0b00001) << 2 | (word14 & 0b00001) << 1 | (word15 & 0b00001) << 0

    pattern1 = parse_to_bin8(l3) + parse_to_bin8(l2) + parse_to_bin8(l1) + parse_to_bin8(l0)
    pattern2 = parse_to_bin8(l8) + parse_to_bin8(l7) + parse_to_bin8(l6) + parse_to_bin8(l5)
    pattern3 = parse_to_bin8(0)  + parse_to_bin8(0)  + parse_to_bin8(l9) + parse_to_bin8(l4)
    loadCheckPatternOnFC7(int(pattern1, 2), int(pattern2, 2), int(pattern3, 2))
    return l0, l1, l2, l3, l4

def loadCheckPatternOnFC7(pattern1, pattern2, pattern3):

	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1)
	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2)
	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3)

	sleep(0.5)

        print "Content of the patterns1 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns1")
        print "Content of the patterns2 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns2")
        print "Content of the patterns3 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns3")

def delayDataTaking():
	#below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
	print "BX indicator for SSA centroid data:", fc7.read("stat_phy_slvs_compare_fifo_bx_indicator")
	#fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
	sleep(1)

def RunStateMachine():
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
	while(FIFO_almost_full != 1 and timer < timer_data_taking):
		FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		timer = timer + 1
		print "Timer at: ", timer, "/", timer_data_taking
		print "State of FSM during comparing: " , fc7.read("stat_phy_slvs_compare_state_machine")
		print "FIFO almost full full: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		print "-----------------------------------------------------------------------------"
		sleep(1)

	fc7.write("ctrl_phy_SLVS_compare_stop",1)

	print "State of FSM after stopping: " , fc7.read("stat_phy_slvs_compare_state_machine")

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

def ReadFIFOs(chip, n = 16386):
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

	for i in range (0,n):
			print("--------------------------")
			print("Entry number: ", i ," in the FIFO:")
			fifo1_word = fc7.read("ctrl_phy_SLVS_compare_read_data1_fifo")
			fifo2_word = fc7.read("ctrl_phy_SLVS_compare_read_data2_fifo")
			fifo3_word = fc7.read("ctrl_phy_SLVS_compare_read_data3_fifo")
			fifo4_word = fc7.read("ctrl_phy_SLVS_compare_read_data4_fifo")
			print "MPA: BX counter, 0x0000, BX0 data (l4, l3, l2, l1, l0) and  BX1 data (l4, l3, l2, l1, l0)"
			print "SSA: 0x0000, BX counter, 0x0000 and centroid data (l7, l6, l5, l4, l3, l2, l1, l0)"
			print(parse_to_bin32(fifo4_word),parse_to_bin32(fifo3_word),parse_to_bin32(fifo2_word),parse_to_bin32(fifo1_word))
			print(fifo4_word,fifo3_word,fifo2_word,fifo1_word)

			print "BX counter:", fifo4_word
			if(chip == "MPA"):
				print "MPA stub BX0 l4: ", parse_to_bin8((fifo3_word & 0x0000ff00)>>8)
				print "MPA stub BX0 l3: ", parse_to_bin8(fifo3_word & 0x000000ff)
				print "MPA stub BX0 l2: ", parse_to_bin8((fifo2_word & 0xff000000)>>24)
				print "MPA stub BX0 l1: ", parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
				print "MPA stub BX0 l0: ", parse_to_bin8((fifo2_word & 0x0000ff00)>>8)

				print "MPA stub BX1 l4: ", parse_to_bin8(fifo2_word & 0x000000ff)
				print "MPA stub BX1 l3: ", parse_to_bin8((fifo1_word & 0xff000000)>>24)
				print "MPA stub BX1 l2: ", parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
				print "MPA stub BX1 l1: ", parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
				print "MPA stub BX1 l0: ", parse_to_bin8(fifo1_word & 0x000000ff)
			elif(chip == "SSA"):
				print "SSA centroid l7: ", parse_to_bin8((fifo2_word & 0xff000000)>>24)
				print "SSA centroid l6: ", parse_to_bin8((fifo2_word & 0x00ff0000)>>16)
				print "SSA centroid l5: ", parse_to_bin8((fifo2_word & 0x0000ff00)>>8)
				print "SSA centroid l4: ", parse_to_bin8(fifo2_word & 0x000000ff)

				print "SSA centroid l3: ", parse_to_bin8((fifo1_word & 0xff000000)>>24)
				print "SSA centroid l2: ", parse_to_bin8((fifo1_word & 0x00ff0000)>>16)
				print "SSA centroid l1: ", parse_to_bin8((fifo1_word & 0x0000ff00)>>8)
				print "SSA centroid l0: ", parse_to_bin8(fifo1_word & 0x000000ff)
			else:
				print "CHIPTYPE UNKNOWN"

	print "State of FSM after reading FIFOs: " , fc7.read("stat_phy_slvs_compare_state_machine")
	print "Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full")

def RunSEU(row, pixel, delay_after_fast_reset = 0):
	mpa_reset()
	reset()
	sleep(1)
	align_out()
	l0, l1, l2, l3, l4 = configureChips(row,  pixel, analog_injection = 0)
	#I2C.peri_write('EdgeSelT1Raw', 0)
	#I2C.peri_write("ConfSLVS", 0b00111111)
	#Configure_TestPulse_MPA(delay_after_fast_reset = 0, delay_after_test_pulse = 0, delay_before_next_pulse = 0, number_of_test_pulses = 0, enable_rst_L1 = 0)
	Configure_SEU(cal_pulse_period = 1, l1a_period = 39, number_of_cal_pulses = 0)
	SendCommand_CTRL("start_trigger")
	RunStateMachine()
	SendCommand_CTRL("stop_trigger")
	ReadFIFOs("MPA", 2)
	print "Number of good BX: ", fc7.read("stat_phy_slvs_compare_number_good_data")
	return l0, l1, l2, l3, l4


# l0, l1, l2, l3, l4 = RunSEU(row = [3], pixel = [10])
