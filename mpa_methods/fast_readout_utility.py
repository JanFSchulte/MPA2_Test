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
	activate_ss()
	send_test()
	pos = read_stubs()
	return pos

def test_pp_data(row, pixel, pattern = 0b10000000):
	activate_I2C_chip()
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
def ReadoutCounters(raw_mode_en = 0):
	# set the raw mode to the firmware
	fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_en)
	t0 = time.time()
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	#print "---> Sending Start and Waiting for Data"
	#StartCountersRead()
	start_counters_read(8)
	timeout = 0
	while ((mpa_counters_ready == 0) & (timeout < 50)):
		sleep(0.01)
		mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
		timeout += 1
	if (timeout >= 50):
		failed = True;
		return failed, 0
	#print "---> MPA Counters Ready(should be one): ", mpa_counters_ready
	if raw_mode_en == 1:
		count = np.zeros((2040, ), dtype = np.uint16)
		cycle = 0
		for i in range(0,20000):
			fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
			fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
			line1 = to_number(fifo1_word,8,0)
			line2 = to_number(fifo1_word,16,8)
			line3 = to_number(fifo1_word,24,16)
			line4 = to_number(fifo2_word,8,0)
			line5 = to_number(fifo2_word,16,8)
			if (((line1 & 0b10000000) == 128) & ((line4 & 0b10000000) == 128)):
				temp = ((line2 & 0b00100000) << 9) | ((line3 & 0b00100000) << 8) | ((line4 & 0b00100000) << 7) | ((line5 & 0b00100000) << 6) | ((line1 & 0b00010000) << 6) | ((line2 & 0b00010000) << 5) | ((line3 & 0b00010000) << 4) | ((line4 & 0b00010000) << 3) | ((line5 & 0b10000000) >> 1) | ((line1 & 0b01000000) >> 1) | ((line2 & 0b01000000) >> 2) | ((line3 & 0b01000000) >> 3) | ((line4 & 0b01000000) >> 4) | ((line5 & 0b01000000) >> 5) | ((line1 & 0b00100000) >> 5)
				if (temp != 0):
					count[cycle] = temp - 1
					cycle += 1
	else:
		# here is the parsed mode, when the fpga parses all the counters
		count = fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 2040)
		for i in range(2040):
			count[i] = count[i] - 1

	sleep(0.001)
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	failed = False
	return failed, count

def reset_strip_in( line = range(0,8), strip = [0, 0, 0, 0, 0, 0, 0, 0]):
	value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
	for l in line:
		reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(l) + "_0"
		fc7.write(reg, value)
		value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
		reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(l) + "_1"
		fc7.write(reg, value)

def strip_in_def( line ,strip = 8*[128]):
	value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
	reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(line) + "_0"
	fc7.write(reg, value)
	value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
	reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(line) + "_1"
	fc7.write(reg, value)

def strip_in_test(n_pulse = 10, line = range(0,8),  value = [128, 64, 32, 16, 8, 4, 2, 1], latency = 0b00111011):
	t0 = time.time()
	activate_ss()
	I2C.peri_write('EdgeSelTrig',0)
	I2C.peri_write('LatencyRx320', latency) # Trigger line aligned with FC7
	#I2C.peri_write('EdgeSelTrig', 0b000000000)
	line = np.array(line)
	value = np.array(value)
	nline = int(line.shape[0])
	nvalue = int(value.shape[0])
	line_check = np.zeros((nline,nvalue), dtype = np.int)
	count_line = 0
	for l in line:
		count_val = 0
		for val in value:
			reset_strip_in()
			strip_in_def(l, 8*[val])
			check = 0
			for i in range(0, n_pulse):
				send_test()
				nst, pos, Z, bend = read_stubs()
				for centr in pos[:,0]:
					if (centr == val):
						check += 1
				for centr in pos[:,1]:
					if (centr == val):
						check += 1
			line_check[count_line, count_val ] = check
			count_val += 1
		count_line += 1
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)

	return line_check

#def strip_in_l1():
#	reset()
#	activate_I2C_chip()
#	activate_sync()
# 	align_out()
#	fc7.write("cnfg_phy_SSA_enable_gen_l1_data", 1)
#	fc7.write("cnfg_phy_SSA_gen_l1_data_format_3", 16)
#	fc7.write("cnfg_phy_SSA_gen_delay_trig_data",6)
#	fc7.write("ctrl_phy_ssa_gen_trig_phase",168)

def test_L1_fast_command(npulse):
	for j in range(0,npulse):
		send_trigger()
		sleep(0.001)
		L1_ID = read_L1()
		if (L1_ID!=1): print "ERROR 1"
		sleep(0.001)
		send_resync()
		sleep(0.001)
		send_trigger()
		sleep(0.001)
		L1_ID = read_L1()
		if (L1_ID!=0): print "ERROR 2"
		sleep(0.001)
