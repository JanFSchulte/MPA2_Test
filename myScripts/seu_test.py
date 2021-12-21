import numpy as np
import time
import sys
import random
import matplotlib.pyplot as plt
import matplotlib.axes as ax
from mpa_methods.cal_utility import *
from mpa_methods.power_utility import *
from mpa_methods.bias_calibration import *
from myScripts.Multimeter_GPIB_Keithley import *
from mpa_methods.fast_readout_utility import *
#import ProbeCardTest2 as PCT
#PM = PCT.ProbeMeasurement("./")
#timer_data_taking = 3

def align_SSA_input(edge, curr):
	#STUB
	reset()
	mpa_reset()
	activate_I2C_chip(verbose = 0)
	I2C.peri_write('EdgeSelT1Raw', edge)
	currSLVS = 0b00111000 | curr
	I2C.peri_write("ConfSLVS", currSLVS)
	sleep(0.01)
	align_out()
	sleep(0.01)
	strip_in_scan(n_pulse = 1, print_file = 0)
	# L1
def align_SSA_L1(latency, delay, curr):
	reset()
	sleep(0.1)
	mpa_reset()
	sleep(0.1)
	#fc7.write("ctrl_phy_ssa_gen_trig_phase",42)
	sleep(0.1)
	fc7.write("cnfg_phy_SSA_enable_gen_l1_data", 1)
	sleep(0.1)
	fc7.write("cnfg_phy_SSA_gen_delay_trig_data", delay)
	sleep(0.1)
	fc7.write("cnfg_phy_SSA_gen_l1_data_format_3", 129)
	sleep(0.1)
	activate_I2C_chip(verbose = 0)
	sleep(0.1)
	I2C.peri_write('EdgeSelT1Raw', 0)
	sleep(0.1)
	currSLVS = 0b00111000 | curr
	I2C.peri_write("ConfSLVS", currSLVS)
	sleep(0.1)
	I2C.peri_write('LatencyRx320', latency)
	sleep(0.1)
	disable_pixel(0, 0)
	sleep(1)
	align_out()
	send_trigger()
	read_L1()

def parse_to_bin32(input):
	return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

def parse_to_bin8(input):
	return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

def parse_to_bin9(input):
	return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)

def checkSEU(filename = "../cernbox/SEU_results/SEUcnt_test.csv", SEUcnt_start = 8, latency = 500):
	cnt = 0
	f = open(filename, 'a')
	seu = I2C.peri_read("SEUcntPeri") - SEUcnt_start - 2
	message = str(seu) + ", "
	cnt += seu
	f.write(message);
	for i in range(1,17):
		if (latency > 255):
			seu = I2C.row_read("SEUcntRow", i) - 6
		else:
			seu = I2C.row_read("SEUcntRow", i) - 4
		message = str(seu) + ", "
		cnt += seu
		f.write(message);
	f.write("\n")
	f.close()
	return cnt

def checkI2C(col, row, width, filename = "../cernbox/SEU_results/I2C_test.csv"):
	f = open(filename, 'a')
	base = 0b1000100000000000
	for i in range(0,136):
		adr = i | base
		message = str(read_I2C('MPA', adr, 0.001)) + ", "
		f.write(message);
	for i in range(0,len(col)):
		for j in range(0, width[i]):
			message = str(I2C.pixel_read('ENFLAGS', row[i], col[i] + j)) +", "; f.write(message)
			message = str(I2C.pixel_read('ModeSel', row[i], col[i] + j)) +", "; f.write(message)
			message = str(I2C.pixel_read('ClusterCut', row[i], col[i] + j)) +", "; f.write(message)
			message = str(I2C.pixel_read('DigPattern', row[i], col[i] + j)) +", "; f.write(message)
	f.write("\n")
	f.close()


def checkI2C_dyn(n = 1, filename = "../cernbox/SEU_results/I2C_dynamic_test.csv"):
	t0 = time.time()
	print "Starting Dynamic I2C test"
	activate_I2C_chip(frequency = 4, verbose = 0)
	f = open(filename, 'w')
	base = 0b1000100000000000
	for i in range(0,n):
		slave = random.randint(0,2)
		if (slave == 0):
			reg = random.randint(0,38)
			adr = reg | base
		elif (slave == 1):
			reg = random.randint(1,4)
			row = random.randint(1,16)
			pixel_id = 0b1111001
			adr  = ((row & 0x0001f) << 11 ) | ((reg & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
		elif (slave == 2):
			reg = random.randint(0,5)
			row = random.randint(1,16)
			pixel_id = random.randint(1,120)
			adr  = ((row & 0x0001f) << 11 ) | ((reg & 0x000f) << 7 ) | (pixel_id & 0xfffffff)
		write_I2C('MPA', adr, 255)
		max_value = read_I2C('MPA', adr, 0.01)
		if (max_value != None):
			value = random.randint(0, max_value)
			write_I2C('MPA', adr, value)
			check = read_I2C('MPA', adr, 0.01)
			if ( check != value):
				message = "Error in slave " + str(slave) + " reg: " + str(reg) + " Write " + str(bin(value)) + " Read " + str(bin(check))
				f.write(message); f.write("\n")
				print message
		else:
			message = "Error in slave " + str(slave) + " reg: " + str(reg) + " max value --> " + str(max_value)
			f.write(message); f.write("\n")
			print message
	f.close()
	t1 = time.time()
	print "Test Completed"
	print "Elapsed Time: " + str(t1 - t0)

def configureChipOnlyPixel(latency, offset = 5, analog_injection = 0):
	#I2C configuration
	activate_I2C_chip(frequency = 4, verbose = 0)
	disable_pixel(0,0)
	I2C.row_write('L1Offset_1', 0,  latency)
	if (latency > 255):
		I2C.row_write('L1Offset_2', 0, 1)
	I2C.peri_write('EdgeSelT1Raw', 0)
	sleep(0.01)
	I2C.peri_write('EdgeSelTrig', 0) # 1 = rising
	sleep(0.01)
	I2C.peri_write('LatencyRx320', 0b00011111) # Setup Test Chip #20
	if (analog_injection):
		set_calibration(100)
		set_threshold(200)
	else:
		I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
	#activate_pp()

def configureChip(latency, offset = 5, analog_injection = 0):
	#I2C configuration
	activate_I2C_chip(frequency = 4, verbose = 0)
	sleep(0.01)
	disable_pixel(0,0)
	sleep(0.01)
	I2C.row_write('L1Offset_1', 0,  latency)
	sleep(0.01)
	if (latency > 255):
		I2C.row_write('L1Offset_2', 0, 1)
	sleep(0.01)
	I2C.peri_write('EdgeSelT1Raw', 0)
	sleep(0.01)
	I2C.peri_write('EdgeSelTrig', 0) # 1 = rising
	sleep(0.01)
	#I2C.peri_write('ECM',  0)
	alignStub = 6
	alignL1 = 6
	align = 0b00000000 | (alignStub << 3) | alignL1
	I2C.peri_write('LatencyRx320', align)
	#I2C.peri_write('LatencyRx320', 0b00101111) # Trigger line aligned with FC7
	#I2C.peri_write('LatencyRx320', 0b00011010) # Setup Test Chip #17
	#I2C.peri_write('LatencyRx320', 0b00011111) # Setup Test Chip #20
	#I2C.peri_write('LatencyRx320', 0b00011111) # Setup Test Chip #20
	# Stub Strip Input
	sleep(0.01)
	fc7.write("cnfg_phy_SSA_enable_gen_l1_data", 1)
	sleep(0.01)
	fc7.write("cnfg_phy_SSA_gen_delay_trig_data",7)
	sleep(0.01)
	fc7.write("cnfg_phy_SSA_gen_offset_SSA_BX_cnt_format", 0)
	sleep(0.01)
	#fc7.write("ctrl_phy_ssa_gen_trig_phase",42)
	sleep(0.01)
	#I2C.peri_write("SSAOffset_1", offset)
	I2C.peri_write("ConfSLVS", 0b00111111)
	sleep(0.01)

	if (analog_injection):
		set_calibration(100)
		set_threshold(200)
	else:
		I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
		set_calibration(100)
		set_threshold(200)
	sleep(0.01)
	#activate_pp()


def configurePixel(cluster_col, cluster_row, cluster_width, strip, runname, iteration, analog_injection = 0, verbose = 0, print_file = 0):
	#here define the way to generate stub/centroid data pattern on the MPA/SSA
	if print_file:
		filename = str(runname) + "Patterns/Iter_" + str(iteration)+ "pattern.txt"
		f = open(filename, "a")
		message = "\n"; f.write(message);
		message = "\n"; f.write(message);
	#Variables declaration
	pcluster = ""
	scluster = ""
	n_pclust = len(cluster_col)
	n_sclust = len(strip)

	word = np.zeros(16, dtype = np.uint8)
	row = np.zeros(16, dtype = np.uint8)
	pixel = np.zeros(16, dtype = np.uint8)
	l = np.zeros(10, dtype = np.uint8)
	count = 0
	disable_pixel(0,0)
	# Pixel activation
	for i in range(0, n_pclust):
		for j in range(0, cluster_width[i]):
			if (analog_injection):
				enable_pix_EdgeBRcal(cluster_row[i], cluster_col[i] + j)
			else:
				I2C.pixel_write('DigPattern', cluster_row[i], cluster_col[i] + j,  0b00000001)
				I2C.pixel_write('ENFLAGS', cluster_row[i], cluster_col[i] + j , 0x20)
		#
		if (n_pclust > 5):
			if (i != n_pclust-1):
				row[n_pclust - i -2] = cluster_row[i] - 1
				pixel[n_pclust - i -2] = cluster_col[i]*2 + cluster_width[i] - 1
			#row[n_pclust - i -1] = cluster_row[i] - 1
			#pixel[n_pclust - i -1] = cluster_col[i]*2 + cluster_width[i] - 1
		else:
			row[n_pclust - i -1] = cluster_row[i] - 1
			pixel[n_pclust - i -1] = cluster_col[i]*2 + cluster_width[i] - 1
		pcluster = pcluster + bin(cluster_col[i]).lstrip('-0b').zfill(7) + bin(cluster_width[i]-1).lstrip('-0b').zfill(3) + bin(cluster_row[i]-1).lstrip('-0b').zfill(4)
		count += 1

	if (strip != []):
		strip_0 = 0
		strip_1 = 0
		strip_2 = 0
		strip_3 = 0
		for i in range(0, n_sclust):
			strip_in_def( line = i ,strip = 8*[pixel[i]+8])
			if (strip[i] <= 32):
				strip_3 = strip_3 | (1 << strip[i]-1)
			elif (strip[i] <= 64):
				strip_2 = strip_2 | (1 << (strip[i]- 32 -1))
			elif (strip[i] <= 96):
				strip_1 = strip_1 | ( 1 << (strip[i]- 64 - 1))
			elif ((strip[i] <= 120)):
				strip_0 = strip_0 | ( 1 << (strip[i]- 96 - 1))
			else:
				print "WARNING: Strip coordinate out of range!"
			scluster = scluster + bin(strip[i]).lstrip('-0b').zfill(7) + bin(0).lstrip('-0b').zfill(4)
		fc7.write("cnfg_phy_SSA_gen_l1_data_format_3", strip_3)
		fc7.write("cnfg_phy_SSA_gen_l1_data_format_2", strip_2)
		fc7.write("cnfg_phy_SSA_gen_l1_data_format_1", strip_1)
		fc7.write("cnfg_phy_SSA_gen_l1_data_format_0", strip_0)
	if (count > 5): count = 5

	# Pattern preparation stubs
	# BX0
	#count = 0
	if verbose:
		print " Injected pixels: ", pixel
		print " Injected row: ", row
		print " Injected count: ",count
		print " Injected strip: ", strip
	#print strip_3
	#print strip_2
	#print strip_1
	#print strip_0

	word0  = 0b10000 | ((0b00111 & count) << 1) | ((0b10000000 & pixel[0]) >> 7)
	word1 = ((0b01111100 & pixel[0]) >> 2)
	word2 = ((0b00000011 & pixel[0]) << 3) | 0b000 #Bending 0
	word3 = ((0b00001111 & row[0]) << 1) |((0b10000000 & pixel[1]) >> 7)
	word4 = ((0b01111100 & pixel[1]) >> 2)
	word5 = ((0b00000011 & pixel[1]) << 3) | 0b000 #Bending 0
	word6 = ((0b00001111 & row[1]) << 1) |((0b10000000 & pixel[2]) >> 7)
	word7 = ((0b01111100 & pixel[2]) >> 2)
	# BX1
	word8 = 0b00000 | ((0b00000011 & pixel[2]) << 2) | 0b00 #Bending 0
	word9 = 0b00000 | row[2]
	word10 = ((0b11111000 & pixel[3]) >> 3)
	word11 = ((0b00000111 & pixel[3]) << 2) | 0b00
	word12 = 0b00000 | row[3]
	word13 = ((0b11111000 & pixel[4]) >> 3)
	word14 = ((0b00000111 & pixel[4]) << 2) | 0b00
	word15 = 0b00000 | row[4]
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

	if (verbose):
		print parse_to_bin8(l4)
		print parse_to_bin8(l3)
		print parse_to_bin8(l2)
		print parse_to_bin8(l1)
		print parse_to_bin8(l0)
		print parse_to_bin8(l9)
		print parse_to_bin8(l8)
		print parse_to_bin8(l7)
		print parse_to_bin8(l6)
		print parse_to_bin8(l5)
	if print_file:
		f.write("Stub pattern check")
		message = parse_to_bin8(l4) + "\n"; f.write(message);
		message = parse_to_bin8(l3) + "\n"; f.write(message);
		message = parse_to_bin8(l2) + "\n"; f.write(message);
		message = parse_to_bin8(l1) + "\n"; f.write(message);
		message = parse_to_bin8(l0) + "\n"; f.write(message);
		message = parse_to_bin8(l9) + "\n"; f.write(message);
		message = parse_to_bin8(l8) + "\n"; f.write(message);
		message = parse_to_bin8(l7) + "\n"; f.write(message);
		message = parse_to_bin8(l6) + "\n"; f.write(message);
		message = parse_to_bin8(l5) + "\n"; f.write(message);

	pattern1 = parse_to_bin8(l3) + parse_to_bin8(l2) + parse_to_bin8(l1) + parse_to_bin8(l0)
	pattern2 = parse_to_bin8(l8) + parse_to_bin8(l7) + parse_to_bin8(l6) + parse_to_bin8(l5)
	pattern3 = parse_to_bin8(0)  + parse_to_bin8(0)  + parse_to_bin8(l9) + parse_to_bin8(l4)
	loadCheckPatternOnFC7(int(pattern1, 2), int(pattern2, 2), int(pattern3, 2))

	# Pattern preparation L1
	payload = bin(2).lstrip('-0b').zfill(2) +  bin(0).lstrip('-0b').zfill(9) + "0" + bin(n_sclust).lstrip('-0b').zfill(5) + bin(n_pclust).lstrip('-0b').zfill(5) + "0" + scluster + pcluster  + bin(cluster_col[n_pclust-1] & 0b1111110).lstrip('-0b').zfill(7)+ bin(0).lstrip('-0b').zfill(32)
	#+ bin(cluster_col[n_pclust-1] & 0b1111000).lstrip('-0b').zfill(7)
	if print_file:
		f.write("L1 pattern check:\n")
		f.write(payload)
	pattern7 = 0
	pattern6 = 0
	pattern5 = 0
	pattern4 = 0
	pattern3 = 0
	pattern2 = 0
	pattern1 = 0
	if (verbose): print payload
	try:
		pattern7 = int(payload[0:   32], 2)
		pattern6 = int(payload[32:  64], 2)
		pattern5 = int(payload[64:  96], 2)
		pattern4 = int(payload[96:  128], 2)
		pattern3 = int(payload[128: 160], 2)
		pattern2 = int(payload[160: 192], 2)
		pattern1 = int(payload[192: 224], 2)
	except ValueError:
		if (verbose): print "Empty Pattern"
	loadCheckPatternOnFC7L1(pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7)
	if print_file:	f.close()

def loadCheckPatternOnFC7(pattern1, pattern2, pattern3, verbose = 0):
	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1)
	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2)
	fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3)
	#sleep(0.5)
	if (verbose):
		print "Content of the patterns1 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns1")
		print "Content of the patterns2 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns2")
		print "Content of the patterns3 cnfg register: ",fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns3")

def loadCheckPatternOnFC7L1(pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, verbose = 0):

	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1",pattern1)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2",pattern2)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3",pattern3)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4",pattern4)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5",pattern5)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6",pattern6)
	fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7",pattern7)
	#sleep(0.5)
	if (verbose):
		print "Content of the patterns1 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1"))
		print "Content of the patterns2 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2"))
		print "Content of the patterns3 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3"))
		print "Content of the patterns4 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4"))
		print "Content of the patterns5 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5"))
		print "Content of the patterns6 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6"))
		print "Content of the patterns7 cnfg register: ",parse_to_bin32(fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7"))

def delayDataTaking():
	#below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
	print "BX indicator for SSA centroid data:", fc7.read("stat_phy_slvs_compare_fifo_bx_indicator")
	#fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
	sleep(1)

def printInfo(message):
	print
	print message
	print "*** STUB ***"
	print "State of FSM: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
	print "FIFO almost full: " , fc7.read("stat_phy_slvs_compare_fifo_almost_full")
	print "number of events written to FIFO", fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
	print "Number of good 2xBX STUBS: ", fc7.read("stat_phy_slvs_compare_number_good_data")
	print
	print "*** L1 ***"
	print "State of FSM: " , fc7.read("stat_phy_l1_slvs_compare_state_machine")
	print "Fifo almost full: ", fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
	print "Header # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
	print "Trigger # ", fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
	print "number of events written to FIFO", fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo")
	print "number of matched events:", fc7.read("stat_phy_l1_slvs_compare_number_good_data")
	print "*************************"

def RunStateMachine(runname, iteration, print_file, timer_data_taking, latency):
	fc7.write("ctrl_phy_l1_SLVS_compare_start",1)
	SendCommand_CTRL("start_trigger")
	sleep(0.01)
	FSM = fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
	if (FSM == 4):
		print "-----------------------------"
		print "-----------------------------"
		print "-----------------------------"
		print "Error in FSM"
		print "-----------------------------"
		print "-----------------------------"
		print "-----------------------------"
		return
	fc7.write("ctrl_phy_SLVS_compare_start",1)

	#start taking data and check the 80% full threshold of the FIFO
	FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
	FIFO_almost_full_L1 = fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
	timer = 0
	sleep(1)
	PM.CheckTotalPower(1)
	activate_I2C_chip(verbose = 0)
	while(FIFO_almost_full != 1 and FIFO_almost_full_L1 != 1 and timer < timer_data_taking):
		FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		FIFO_almost_full_L1 = fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
		timer = timer + 5
		message = "TIMER at: ", timer, "/", timer_data_taking
		printInfo(message)
		sleep(5)
	fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.stop",1)
	sleep(0.01)
	SendCommand_CTRL("stop_trigger")
	FIFO_almost_full = fc7.read("stat_phy_slvs_compare_fifo_almost_full")
	FIFO_almost_full_L1 = fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")

	#
		#print
		#print "----------------------------- FINAL REPORT------------------------------------"
		#print "----------------------------- STUB -------------------------------------------"
		#print "State of FSM after stopping: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		##if(timer == timer_data_taking and FIFO_almost_full == 0):
		#if(FIFO_almost_full == 0):
		#	print "data taking stopped because reached the adequate time"
		##elif(FIFO_almost_full == 1 and timer < timer_data_taking ):
		#elif(FIFO_almost_full == 1):
		#	print "data taking stopped because the FIFO reached the 80%"
		#else:
		#	print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"
		#print "-----------------------------------------------------------------------------"
		#print "------------------------------ L1 -------------------------------------------"
		#print "State of FSM after stopping: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		##if(timer == timer_data_taking and FIFO_almost_full_L1 == 0):
		#if(FIFO_almost_full_L1 == 0):
		#	print "data taking stopped because reached the adequate time"
		##elif(FIFO_almost_full_L1 == 1 and timer < timer_data_taking ):
		#elif(FIFO_almost_full_L1 == 1):
		#	print "data taking stopped because the FIFO reached the 80%"
		#else:
		#	print "data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)"
		#print "-----------------------------------------------------------------------------"
	print
	message = "-------------------------------- RESULTS ITERATION " + str(iteration) + " ---------------------------------------------"
	printInfo(message)
	n = fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
	if (latency == 500): l1_limit = 12
	else: l1_limit = 7
	if ((n > 0) and print_file):
		filename = str(runname) + "Error/Iter_" + str(iteration) + "_STUB" + ".csv"
		writeFIFO(n, filename)
	n = fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo")
	if ((n > l1_limit ) and print_file):
		filename = str(runname) + "Error/Iter_" + str(iteration)+ "_L1" +  ".csv"
		writeFIFO_L1(n, filename)
	return 	fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo"), fc7.read("stat_phy_slvs_compare_number_good_data"), fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo"), fc7.read("stat_phy_l1_slvs_compare_number_good_data")

def writeFIFO(n = 16386, filename = "test.log"):
	f = open(filename, 'w')
	stat_phy_slvs_compare_data_ready = fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.data_ready")
	for i in range (0,n):
		fifo1_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data1_fifo")
		fifo2_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo")
		fifo3_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data3_fifo")
		fifo4_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo")
		message = str(i) + ", "
		f.write(message); message = str(fifo4_word) + ", "
		f.write(message); message = str(parse_to_bin8((fifo3_word & 0x0000ff00)>>8)) + ", "
		f.write(message); message = str(parse_to_bin8(fifo3_word & 0x000000ff)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo2_word & 0xff000000)>>24)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo2_word & 0x00ff0000)>>16)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo2_word & 0x0000ff00)>>8)) + ", "
		f.write(message); message = str(parse_to_bin8(fifo2_word & 0x000000ff)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo1_word & 0xff000000)>>24)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo1_word & 0x00ff0000)>>16)) + ", "
		f.write(message); message = str(parse_to_bin8((fifo1_word & 0x0000ff00)>>8)) + ", "
		f.write(message); message = str(parse_to_bin8(fifo1_word & 0x000000ff)) + "\n"
		f.write(message)
	f.close

def ReadFIFOs(chip, n = 16386):
	print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
	print "State of FSM before reading FIFOs: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
	print "Now printing the data in the FIFO:"
	stat_phy_slvs_compare_data_ready = fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.data_ready")
	i = 0

	"""package2 = fc7.fifoRead("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo", 17000)
	p l5, l6, l7ackage4 = fc7.fifoRead("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo", 17000)
	for i in range(16384):
		print "Package2 #", i+1, ": ", package2[i]
		print "Package4 #", i+1, ": ", package4[i]
	print("State of FSM after reading FIFOs: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
	print("Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full"))"""

	for i in range (0,n):
			print("--------------------------")
			print("Entry number: ", i ," in the FIFO:")
			fifo1_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data1_fifo")
			fifo2_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo")
			fifo3_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data3_fifo")
			fifo4_word = fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo")
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

	print "State of FSM after reading FIFOs: " , fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
	print "Fifo almost full: ", fc7.read("stat_phy_slvs_compare_fifo_almost_full")

def ReadFIFOsL1(n = 16386, verbose = 1):
	#print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
	#printInfo("BEFORE READING FIFO:")
	#print "Now printing the data in the FIFO:"
	t0 = time.time()
	i = 0
	for i in range (0,n):
			fifo1_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data1_fifo")
			fifo2_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data2_fifo")
			fifo3_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data3_fifo")
			fifo4_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data4_fifo")
			fifo5_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data5_fifo")
			fifo6_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data6_fifo")
			fifo7_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data7_fifo")
			fifo8_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data8_fifo")
			fifo9_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo")
			if (verbose):
				print("--------------------------")
				print("Entry number: ", i ," in the FIFO:")
				print "Full l1 data package without the header (MSB downto LSB): "
				print(parse_to_bin32(fifo7_word),parse_to_bin32(fifo6_word),parse_to_bin32(fifo5_word),parse_to_bin32(fifo4_word),parse_to_bin32(fifo3_word),parse_to_bin32(fifo2_word),parse_to_bin32(fifo1_word))
				print "l1 counter: ", parse_to_bin9((fifo7_word & 0x3FE00000)>>21)
				print "l1 counter: ", (fifo7_word & 0x3FE00000)>>21
				print "FC7 l1 mirror counter: ", (fifo9_word & 0x000001FF)
				print "BX counter: ", fifo8_word
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	#printInfo("AFTER READING FIFO:")

def writeFIFO_L1(n = 16386, filename = "test_L1.csv"):
	f = open(filename, 'w')
	for i in range (0,n):
		fifo1_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data1_fifo")
		fifo2_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data2_fifo")
		fifo3_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data3_fifo")
		fifo4_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data4_fifo")
		fifo5_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data5_fifo")
		fifo6_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data6_fifo")
		fifo7_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data7_fifo")
		fifo8_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data8_fifo")
		fifo9_word = fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo")
		message = str(fifo8_word) + ", " + str(fifo9_word & 0x000001FF) + ", " + str((fifo7_word & 0x3FE00000)>>21) + ", " + str(parse_to_bin32(fifo7_word) + parse_to_bin32(fifo6_word) + parse_to_bin32(fifo5_word) + parse_to_bin32(fifo4_word) + parse_to_bin32(fifo3_word) + parse_to_bin32(fifo2_word) + parse_to_bin32(fifo1_word)) +"\n"
		f.write(message);
	f.close


def RunSEU(col, row, width, strip, timer_data_taking = 5, offset = 5, cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 1, verbose = 0, print_file = 0, runname =  "../cernbox/SEU_results/", iteration = 0):
	mpa_reset()
	reset()
	SendCommand_CTRL("fast_fast_reset")
	configureChip( latency = latency - diff,  offset = offset, analog_injection = 0)
	align_out(0)
	if (skip == 0):
		Configure_TestPulse_MPA(delay_after_fast_reset = 512, delay_after_test_pulse = latency, delay_before_next_pulse = cal_pulse_period, number_of_test_pulses = 0, enable_L1 = 1, enable_rst = 0, enable_init_rst = 1)
	else:
		Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses = 0)
	configurePixel(col,  row, width, strip, runname = runname, iteration = iteration, print_file = print_file, analog_injection = 0, verbose = verbose)
	SEUcnt_start = I2C.peri_read("SEUcntPeri")
	wrong, good, wrong_L1, good_L1 = RunStateMachine(runname = runname, iteration = iteration, print_file = print_file, timer_data_taking = timer_data_taking, latency = latency)
	return wrong, good, wrong_L1, good_L1, SEUcnt_start

def SEU_Random_Test_8p_8s(n = 5, timer_data_taking = 5, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test"):
	t0 = time.time()
	folder = "../cernbox/SEU_results/" + str(runname) +"/"
	os.mkdir(folder)
	folder = "../cernbox/SEU_results/" + str(runname) +"/Patterns/"
	os.mkdir(folder)
	folder = "../cernbox/SEU_results/" + str(runname) +"/Error/"
	os.mkdir(folder)
	folder = "../cernbox/SEU_results/" + str(runname) +"/"
	logname = folder + "SEU_RT_8p8s.csv"
	f = open(logname, 'w')
	wrong_tot = 	np.zeros(n, dtype = np.int )
	good_tot = 		np.zeros(n, dtype = np.int )
	wrong_tot_L1 = 	np.zeros(n, dtype = np.int )
	good_tot_L1 = 	np.zeros(n, dtype = np.int )
	seu_tot = 		np.zeros(n, dtype = np.int )
	plt.title("On-line check")
	plt.xlim(0, n)
	plt.ion()
	for i in range(0,n):
		print
		print "-------------------------------- ITERATION ", str(i), " ---------------------------------------------"
		row_1 = random.sample(range(1,9), 4)
		row_2 = random.sample(range(9,17), 4)
		row = np.sort(np.append(row_1, row_2 ))
		llim = 1
		col = np.zeros(8, dtype = np.int )
		for j in range(0,8):
			temp = random.sample(range(llim,15*(j+1)), 1)
			col[j] = temp[0]
			llim = col[j] + 9
		corr = 0
		if (i%2 == 0): corr = 1
		#col = np.array(random.sample(range(1+corr,120,2), 8))
		width = 8*[1]
		strip_64 = np.sort(random.sample(range(1+corr,60,2), 4))
		strip_128 = np.array(random.sample(range(61-corr,120,2), 4))
		strip_128 = -np.sort(-strip_128)
		strip = [strip_64[0], strip_128[0], strip_64[1], strip_128[1], strip_64[2], strip_128[2], strip_64[3], strip_128[3]]

		#print col
		#print row
		#print strip

		wrong, good, wrong_L1, good_L1, SEUcnt_start = RunSEU(col, row, width, strip, timer_data_taking = timer_data_taking, offset = 5, cal_pulse_period = cal_pulse_period, l1a_period = l1a_period, latency = latency, print_file = 1, runname = folder, iteration = i, verbose = 0)
		#filename_SEU = folder + "SEUcnt.csv"
		#filename_I2C = folder + "I2Ccheck.csv"
		SEUcnt = checkSEU(filename = folder + "SEUcnt.csv", SEUcnt_start = SEUcnt_start, latency = latency)
		checkI2C(col, row, width, folder + "I2Ccheck.csv")
		if ((wrong < 100) and (wrong_L1 < 100)):
			message = "1, "; f.write(message)
		else:
			message = "0, "; f.write(message)
		message = str(row) + ", "; f.write(message)
		message = str(col) + ", "; f.write(message)
		message = str(width) + ", "; f.write(message)
		message = str(strip) + ", "; f.write(message)
		message = str(wrong) + ", "; f.write(message)
		message = str(good) + ", "; f.write(message)
		message = str(wrong_L1) + ", "; f.write(message)
		message = str(good_L1) + ", "; f.write(message)
		message = str(SEUcnt) + "\n"; f.write(message)

		wrong_tot[i] = wrong
		wrong_tot_L1[i] = wrong_L1
		good_tot[i] = good
		good_tot_L1[i] = good_L1
		seu_tot[i] = SEUcnt
		plt.plot(range(0,i+1), wrong_tot[0:i+1], "r*")
		plt.plot(range(0,i+1), wrong_tot_L1[0:i+1], "bo")
		plt.plot(range(0,i+1), seu_tot[0:i+1], "g+")
		plt.draw()
		plt.pause(0.1)
		t1 = time.time()
		print "Elapsed Time: " + str(t1 - t0)
	mpa_reset()
	reset()
	sleep(0.1)
	checkI2C_dyn(n = 1000, filename = folder + "I2C_dynamic_test.log")
	mpa_reset
	f.close()
	t1 = time.time()
	print "Run Completed"
	print "Elapsed Time: " + str(t1 - t0)
	return wrong_tot, good_tot, wrong_tot_L1, good_tot_L1, SEUcnt

def SEU_Random_Test_8p(n = 5, timer_data_taking = 5, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test"):
	t0 = time.time()
	folder = "../cernbox/SEU_results/" + str(runname) +"/"
	os.mkdir(folder)
	logname = folder + "SEU_RT_8p.csv"
	f = open(logname, 'w')
	wrong_tot = 	np.zeros(n, dtype = np.int )
	good_tot = 		np.zeros(n, dtype = np.int )
	wrong_tot_L1 = 	np.zeros(n, dtype = np.int )
	good_tot_L1 = 	np.zeros(n, dtype = np.int )
	seu_tot = 		np.zeros(n, dtype = np.int )
	plt.title("On-line check")
	plt.xlim(0, n)
	plt.ion()
	for i in range(0,n):
		row_1 = random.sample(range(1,9), 4)
		row_2 = random.sample(range(9,17), 4)
		row = np.sort(np.append(row_1, row_2 ))
		llim = 1
		col = np.zeros(8, dtype = np.int )
		for j in range(0,8):
			temp = random.sample(range(llim,15*(j+1)), 1)
			col[j] = temp[0]
			llim = col[j] + 9
		width = 8*[1]

		print row
		print col

		wrong, good, wrong_L1, good_L1, SEUcnt_start = RunSEU(col, row, width, strip = [], timer_data_taking = timer_data_taking, offset = 5, cal_pulse_period = cal_pulse_period, l1a_period = l1a_period, latency = latency, runname = folder + "Iter_" + str(i) + "_" , verbose = 1)
		#filename_SEU = folder + "SEUcnt.csv"
		#filename_I2C = folder + "I2Ccheck.csv"
		SEUcnt = checkSEU(folder + "SEUcnt.csv", SEUcnt_start, latency)
		checkI2C(col, row, width, folder + "I2Ccheck.csv")
		message = str(row) + ", "; f.write(message)
		message = str(col) + ", "; f.write(message)
		message = str(width) + ", "; f.write(message)
		message = str(wrong) + ", "; f.write(message)
		message = str(good) + ", "; f.write(message)
		message = str(wrong_L1) + ", "; f.write(message)
		message = str(good_L1) + ", "; f.write(message)
		message = str(SEUcnt) + "\n "; f.write(message)
		wrong_tot[i] = wrong
		wrong_tot_L1[i] = wrong_L1
		good_tot[i] = good
		good_tot_L1[i] = good_L1
		seu_tot[i] = SEUcnt
		plt.plot(range(0,i+1), wrong_tot[0:i+1], "r*")
		plt.plot(range(0,i+1), wrong_tot_L1[0:i+1] - (latency/l1a_period), "bo")
		plt.plot(range(0,i+1), seu_tot[0:i+1], "g+")
		plt.draw()
		plt.pause(0.1)
		t1 = time.time()
		print "-------------------------------- ITERATION ", str(i), " COMPLETED ---------------------------------------------"
		print "Elapsed Time: " + str(t1 - t0)
	f.close()
	t1 = time.time()
	print "Run Completed"
	print "Elapsed Time: " + str(t1 - t0)
	return wrong_tot, good_tot, wrong_tot_L1, good_tot_L1, SEUcnt


def ScanPixelSEU(col, row, width, cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 0):
	t0 = time.time()
	wrong_tot = np.zeros(len(col)*len(row), dtype = np.int )
	good_tot = np.zeros(len(col)*len(row), dtype = np.int )
	wrong_tot_L1 = np.zeros(len(col)*len(row), dtype = np.int )
	good_tot_L1 = np.zeros(len(col)*len(row), dtype = np.int )
	pix = np.zeros(len(col)*len(row), dtype = np.int )
	plt.title("On-line check")
	plt.xlim((row[0]-1)*120 + col[0], row[len(row)-1]*120 + col[len(col)-1])
	plt.ion()
	for j in range(0, len(row)):
		for i in range(0, len(col)):
			print
			print "###### Injection in Column ", col[i], "and Row ", row[j]
			print
			wrong, good, wrong_L1, good_L1 = RunSEU([col[i]], [row[j]], width, cal_pulse_period, l1a_period, latency, diff, skip)
			wrong_tot[j*len(col)+i] = wrong
			wrong_tot_L1[j*len(col)+i] = wrong_L1
			good_tot[j*len(col)+i] = good
			good_tot_L1[j*len(col)+i] = good_L1
			pix[j*len(col)+i] = (row[j]-1)*120 + col[i]
			plt.plot(pix[0:j*len(col)+i], wrong_tot[0:j*len(col)+i], "r*")
			plt.plot(pix[0:j*len(col)+i], wrong_tot_L1[0:j*len(col)+i] - 2, "bo")
			plt.draw()
			plt.pause(0.1)
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return wrong_tot, good_tot, wrong_tot_L1, good_tot_L1

def RandPixelSEU(clust, n, cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 0):
	t0 = time.time()
	wrong_tot = 	np.zeros(n, dtype = np.int )
	good_tot  = 	np.zeros(n, dtype = np.int )
	wrong_tot_L1 = 	np.zeros(n, dtype = np.int )
	good_tot_L1 = 	np.zeros(n, dtype = np.int )
	pix = 			np.zeros((n, clust), dtype = np.int )

	plt.title("On-line check")
	plt.xlim(0, n)
	plt.ion()
	for i in range(0, n):
		col = random.sample(range(1,120), clust)
		row = random.sample(range(1,16), clust)
		width = 1
		print
		print "###### Injection Run ", i
		print "###### column: ", col
		print "###### row: ", col
		print
		wrong, good, wrong_L1, good_L1 = RunSEU(col, row, width, cal_pulse_period, l1a_period, latency, diff, skip)
		wrong_tot[i] = wrong
		wrong_tot_L1[i] = wrong_L1
		good_tot[i] = good
		good_tot_L1[i] = good_L1
		for j in range(0,clust):
			pix[i,j] = (row[j]-1)*120 + col[j]
		plt.plot(range(0, i), wrong_tot[0:i], "r*")
		plt.plot(range(0, i), wrong_tot_L1[0:i] - 2, "bo")
		plt.draw()
		plt.pause(0.1)
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return wrong_tot, good_tot, wrong_tot_L1, good_tot_L1

# RunSEU(col = [3], row = [10], width = [1], cal_pulse_period = 1, l1a_period = 39, latency = 100, diff = 2, skip = 1)
# ScanPixelSEU(col = [3,4], row = [10], width = [1],cal_pulse_period = 1, l1a_period = 39, latency = 100, diff = 2, skip = 1)
# ScanPixelSEU(col = 16*range(1,120), row = row, width = [1],cal_pulse_period = 1, l1a_period = 39, latency = 100, diff = 2, skip = 1)
# RunSEU(col = [3,17, 37,57,77,93,101,116 ], row = [1, 4, 8, 9,10,11,12, 16], width = [1,1,1,1,1,1,1,1], cal_pulse_period = 1, l1a_period = 39, latency = 50, diff = 2, skip = 1, verbose = 1)
#ReadFIFOs("MPA", 1)
#ReadFIFOsL1(1)
