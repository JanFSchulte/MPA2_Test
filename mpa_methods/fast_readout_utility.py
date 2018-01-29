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
