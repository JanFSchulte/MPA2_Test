#from mpa_methods.fast_readout_utility import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.cal_utility import *
import numpy as np
import time
import sys

def activate_shift():
	I2C.peri_write('ReadoutMode',0b10)

def activate_pp():
	I2C.peri_write('ECM',0b10000001)

def activate_ss():
	I2C.peri_write('ECM',0b01000001)

def enable_dig_cal(r,p, pattern = 0b00000001):
	I2C.pixel_write('ENFLAGS', r, p, 0x20)
	I2C.pixel_write('DigPattern', r, p, pattern)

def enable_pix_sync(r,p):
	I2C.pixel_write('ENFLAGS', r, p, 0x53)

def set_out_mapping(map = [1, 2, 3, 4, 5, 0]):
	I2C.peri_write('OutSetting_0',map[0])
	I2C.peri_write('OutSetting_1',map[1])
	I2C.peri_write('OutSetting_2',map[2])
	I2C.peri_write('OutSetting_3',map[3])
	I2C.peri_write('OutSetting_4',map[4])
	I2C.peri_write('OutSetting_5',map[5])

def alignment_slvs(align_word = 128, step = 10):
	t0 = time.time()
	activate_I2C_chip()
	I2C.peri_write('LFSR_data', align_word)
	activate_shift()
	phase = 0
	fc7.write("ctrl_phy_fast_cmd_phase",phase)
	aligned = 0
	count = 0
	while ((not aligned) or (count <= (168/step))):
		send_test()
		send_trigger()
		array_stubs = read_stubs(1)
		array_l1 = read_L1()
		aligned = 1
		for word in array_stubs[:,0]: # CHheck stub lines alignment
			if (word != align_word):
				aligned = 0
		if (array_l1[0,0] != align_word): # CHheck L1 lines alignment
			aligned = 0
		if (not aligned): # if not alignment change phase with T1
			phase += step
			fc7.write("ctrl_phy_fast_cmd_phase",phase)
		count += 1
	if (not aligned):
		print "Try with finer step"
	else:
		print "All stubs line aligned!"
	t1 = time.time()
	print "Elapsed Time: " + str(t1 - t0)

def test_ss_data(val = 0):
	fc7.write("cnfg_phy_SSA_gen_stub_data_format", val)
	activate_I2C_chip()
	set_out_mapping()
	activate_ss()
	send_test()
	pos = read_stubs()
	return pos

def test_pp_data(row, pixel, pattern = 0b10000000):
	activate_I2C_chip()
	set_out_mapping()
	activate_pp()
	for r in row:
		for p in pixel:
			enable_dig_cal(r,p, pattern)
	send_test()
	pos = read_stubs()
	return pos

def check_calpulse(row, pixel, pattern = 0b00000001, n_pulse = 1000):
	count = 0
	activate_I2C_chip()
	activate_sync()
	set_out_mapping()
	activate_pp()
	disable_pixel(0,0)
	for r in row:
		for p in pixel:
			enable_dig_cal(r,p, pattern)
	send_test()
	pos_init = read_stubs()
	for i in range(0, n_pulse):
		send_test()
		sleep(0.001)
		pos_now = read_stubs()
		if (np.array_equal(pos_init, pos_now)):
			count += 1
	print "Efficiency:" + str(count) + "/" + str(n_pulse)
	return pos_init

def StartCountersRead():
    encode_fast_reset = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(1)
    fc7.write("ctrl_fast", encode_fast_reset + encode_orbit_reset)

##----- begin main
def ReadoutCounters():
	# Reset the board
	t0 = time.time()
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")

	#print "--> Status: "
	#print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready

	#print "---> Sending Start and Waiting for Data"

	StartCountersRead()
	timeout = 0
	while ((mpa_counters_ready == 0) & (timeout < 50)):
		sleep(0.01)
		mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
		timeout += 1
	#print "---> MPA Counters Ready(should be one): ", mpa_counters_ready
	count = np.zeros((2040, ), dtype = np.uint16)
	cycle = 0
	for i in range(0,20000):
		fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
		fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
		#print "1: " + bin(reverse_mask(fifo1_word))
		#print "2: " + bin(reverse_mask(fifo2_word))
		line1 = to_number(reverse_mask(fifo1_word),8,0)
		line2 = to_number(reverse_mask(fifo1_word),16,8)
		line3 = to_number(reverse_mask(fifo1_word),24,16)
		line4 = to_number(reverse_mask(fifo2_word),8,0)
		line5 = to_number(reverse_mask(fifo2_word),16,8)
		#print line1
		#print line2
		#print line3
		#print line4
		#print line5
		if (((line1 & 0b10000000) == 128) & ((line4 & 0b10000000) == 128)):
			temp = ((line2 & 0b00100000) << 9) | ((line3 & 0b00100000) << 8) | ((line4 & 0b00100000) << 7) | ((line5 & 0b00100000) << 6) | ((line1 & 0b00010000) << 6) | ((line2 & 0b00010000) << 5) | ((line3 & 0b00010000) << 4) | ((line4 & 0b00010000) << 3) | ((line5 & 0b10000000) >> 1) | ((line1 & 0b01000000) >> 1) | ((line2 & 0b01000000) >> 2) | ((line3 & 0b01000000) >> 3) | ((line4 & 0b01000000) >> 4) | ((line5 & 0b01000000) >> 5) | ((line1 & 0b00100000) >> 5)
			if (temp != 0):
				count[cycle] = temp - 1
				cycle += 1
			#print count[cycle,0]
			#print bin(line1)
			#print bin(line2)
			#print bin(line3)
			#print bin(line4)
			#print bin(line5)
	#print cycle
	sleep(0.1)
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	#print "---> MPA Counters Ready(should be zero): ", mpa_counters_ready
	#if print_file:
	#	CSV.ArrayToCSV (count, str(filename))
	#t1 = time.time()
	#print "END"
	#print "Elapsed Time: " + str(t1 - t0)

	return count
