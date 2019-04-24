#from mpa_methods.fast_readout_utility import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.power_utility import *
#from mpa_methods.fast_readout_utility import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
#from mpa_methods.bias_calibration import *
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
from mpa_methods.cal_utility import *




def set_out_mapping(map = [1, 2, 3, 4, 5, 0]):
	I2C.peri_write('OutSetting_0',map[0])
	I2C.peri_write('OutSetting_1',map[1])
	I2C.peri_write('OutSetting_2',map[2])
	I2C.peri_write('OutSetting_3',map[3])
	I2C.peri_write('OutSetting_4',map[4])
	I2C.peri_write('OutSetting_5',map[5])

### New alignment method - USE THIS FUNCTION
def align_MPA():
	send_test()
	test = read_regs(0)
	if ((test[0] == 2147516416) or (test[0] == 8388736)):
		print "Output already aligned"
	else:
		align_out()
		send_test()
		test = read_regs(0)
		if ((test[0] == 2147516416) or (test[0] == 8388736)):
			return True
		else:
			return False

# Pixel-Pixel Test section
#############################
# Digital Calibration test #
def test_pp_digital(row, pixel):
	I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
	sleep(0.001)
	send_test(8)
	sleep(0.001)
	return read_stubs()

def digital_pixel_test(row = range(1,17), pixel = range(1,121), print_log = 1, filename =  "../cernbox/MPA_Results/digital_pixel_test.log"):
	# I am adding something, I'm really sorry. - Marc
	OutputBadPix = []
	t0 = time.time()
	if print_log:
		f = open(filename, 'w')
		f.write("Starting Test:\n")
	activate_I2C_chip(verbose = 0)
	activate_sync()
	sleep(0.1)
	activate_pp()
	sleep(0.1)
	I2C.pixel_write('DigPattern', 0, 0,  0b10000000)
	sleep(0.1)
	I2C.peri_write('RetimePix', 1)
	sleep(0.1)
	for r in row:
		for p in pixel:
			disable_pixel(0,0)
			nst, pos, Z, bend = test_pp_digital(r, p)
			check_pix = 0
			check_row = 0
			err = 0
			for centr in pos[:,0]:
				if (centr == p*2):
					check_pix += 1
				elif (centr != 0):
					err =+ 1
			for row in Z[:,0]:
				if (row == r-1):
					if (r-1 == 0):
						check_row = 1
					else:
						check_row += 1
				elif (row != 0):
					err =+ 1
			if ((check_pix != 1) or (check_row != 1) or (err != 0)):
				error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(check_pix) + " " +  str(check_row) + " " + str(err) + "\n"
				OutputBadPix.append([p,r])
				print error_message
				if print_log:
					f.write(error_message)
	if print_log:
		f.write("Test Completed")
		f.close()
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return OutputBadPix
# Analog Calibration test #
def test_pp_analog(row, pixel):
	enable_pix_EdgeBRcal(row, pixel)
	sleep(0.001)
	send_test(8)
	#sleep(0.001)
	return read_stubs()

def analog_pixel_test(row = range(1,17), pixel = range(2,120), print_log = 1, filename =  "../cernbox/MPA_Results/analog_pixel_test.log"):
	t0 = time.time()
	# I am adding something, I'm really sorry. - Marc
	OutputBadPix = []
	if print_log:
		f = open(filename, 'w')
		f.write("Starting Test:\n")
	activate_I2C_chip(verbose = 0)
	set_calibration(200)
	set_threshold(200)
	activate_sync()
	activate_pp()
	sleep(0.1)
	for r in row:
		for p in pixel:
			disable_pixel(0,0)
			nst, pos, Z, bend = test_pp_analog(r, p)
			check_pix = 0
			check_row = 0
			err = 0
			for centr in pos[:,0]:
				if (centr == p*2):
					check_pix += 1
				elif (centr != 0):
					err =+ 1
			for row in Z[:,0]:
				if (row == r-1):
					if (r-1 == 0):
						check_row = 1
					else:
						check_row += 1
				elif (row != 0):
					err =+ 1
			if ((check_pix != 1) or (check_row != 1) or (err != 0)):
				error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(check_pix) + " " +  str(check_row) + " " + str(err) + "\n"
				OutputBadPix.append([p,r])
				print error_message
				if print_log:
					f.write(error_message)
	if print_log:
		f.write("Test Completed")
		f.close()
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return OutputBadPix

###############################
def check_calpulse(row, pixel, pattern = 0b00000001, n_pulse = 1000):
	count = 0
	activate_I2C_chip(verbose = 0)
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

def strip_in_test(n_pulse = 10, line = range(0,8),  value = [128, 64, 32, 16, 8, 4, 2, 1], latency = 0b00111011, edge = 0):
	#t0 = time.time()

	I2C.peri_write('EdgeSelTrig',edge) # 1 = rising
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
				for centr in pos[8:14,0]:
					if (centr == val):
						check += 1
				for centr in pos[8:14,1]:
					if (centr == val):
						check += 1
			line_check[count_line, count_val ] = check
			count_val += 1
		count_line += 1
	#t1 = time.time()
	#print "END"
	#print "Elapsed Time: " + str(t1 - t0)

	return line_check

def strip_in_scan(n_pulse = 10, probe = 0, print_file = 1, filename =  "../cernbox/MPA_Results/strip_in_scan"):
	t0 = time.time()
	activate_I2C_chip(verbose = 0)
	activate_ss()
	data_array = np.zeros((16, 8 ), dtype = np.float16 )
	if probe:
		I2C.peri_write("InSetting_0",0)
		I2C.peri_write("InSetting_1",1)
		I2C.peri_write("InSetting_2",2)
		I2C.peri_write("InSetting_3",3)
		I2C.peri_write("InSetting_4",4)
		I2C.peri_write("InSetting_5",5)
		I2C.peri_write("InSetting_6",6)
		I2C.peri_write("InSetting_7",7)
		I2C.peri_write("InSetting_8",8)
	sleep(1)
	for i in range(0,8):
		latency = (i  << 3)
		edge = 255
		print "Testing Latency ", i
		temp = strip_in_test(n_pulse = n_pulse, latency = latency , edge = edge)
		for line in range(0,8):
			data_array[i*2, line ] = np.average(temp[line])/(n_pulse*8)
		edge = 0
		temp = strip_in_test(n_pulse = n_pulse, latency = latency , edge = edge)
		#print temp
		for line in range(0,8):
			data_array[i*2+1, line ] = np.average(temp[line])/(n_pulse*8)
	if print_file:
		CSV.ArrayToCSV (data_array, str(filename) + "_npulse_" + str(n_pulse) + ".csv")
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
	return data_array

#def strip_in_l1():
#	reset()
#	activate_I2C_chip(verbose = 0)
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

def memory_test(latency, row, pixel, diff, dig_inj = 1, verbose = 1): # Diff = 2
	#disable_pixel(0,0)
	#I2C.pixel_write('ENFLAGS', row, pixel - 1, 0x00)
	disable_pixel(0,0)
	if dig_inj:
		I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
	else:
		enable_pix_LevelBRcal(row,pixel, polarity = "rise")
	sleep(0.001)
	SendCommand_CTRL("start_trigger")
	sleep(0.001)
	return read_L1(verbose)

def mem_test(latency = 255, delay = [10], row = range(1,17), pixel = range(1,121), diff = 2, print_log = 1, filename =  "../cernbox/MPA_Results/digital_mem_test.log", dig_inj =1, gate = 0, verbose = 1):
	t0 = time.time()
	bad_pix = []
	print "Running Test:"
	if print_log:
		f = open(filename, 'w')
		f.write("Starting Test:\n")
	activate_I2C_chip(verbose = 0)
	activate_sync()
	activate_pp()
	I2C.row_write('L1Offset_1', 0,  latency - diff)
	I2C.row_write('L1Offset_2', 0,  0)
	I2C.row_write('MemGatEn', 0,  gate)
	I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
	fc7.write("cnfg_fast_backpressure_enable", 0)
	disable_pixel(0,0)
	stuck = 0
	i2c_issue = 0
	error = 0
	missing = 0


	for d in delay:
		Configure_TestPulse_MPA(delay_after_fast_reset = d + 512, delay_after_test_pulse = latency, delay_before_next_pulse = 200, number_of_test_pulses = 1, enable_L1 = 1, enable_rst = 1, enable_init_rst = 1)
		sleep(1)
		try:
			strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = memory_test(latency = latency, row = 10, pixel = 5, diff = diff, dig_inj = dig_inj, verbose = 0)
		except TypeError:
			print "Header not Found! Changing sampling phase of T1"
			#I2C.peri_write('EdgeSelT1Raw', 0)
		sleep(1)
		for r in row:
			for p in pixel:
				try:
					strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = memory_test(latency = latency, row = r, pixel = p, diff = diff, dig_inj = dig_inj, verbose = 0)
					found = 0
					for i in range(0, pixel_counter):
						if (pos_pixel[i] == p) and (Z[i] == r):
							found = 1
						elif (pos_pixel[i] == p-1) and (Z[i] == r):
							found = 1
							i2c_issue += 1
					if (pixel_counter > 1): stuck += 1
					if (not found):
						bad_pix.append([p,r])
						error += 1
						error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(d) + " " + str(pixel_counter) + " " +  str(pos_pixel) + " " + str(Z) + "\n"
						if verbose: print error_message
						if print_log: f.write(error_message)
				except TypeError:
					missing += 1
					error_message = "Header not Found in Pixel: " + str(p) + " of Row: " + str(r) + "\n"
					if verbose: print error_message
					if print_log: f.write(error_message)
	print "-------------------------------------"
	print "-------------------------------------"
	print " Number of error: ", error
	print " Number of stucks: ", stuck
	print " Number of I2C issues: ", i2c_issue
	print " Number of missing: ", missing
	if print_log:
		f.write("Test Completed:\n")
		f.write("-------------------------------------\n")
		f.write("-------------------------------------\n")
		line = " Number of error: " + str(error) + "\n"
		f.write(line)
		line = " Number of stucks: " + str(stuck) + "\n"
		f.write(line)
		line = " Number of I2C issues: " + str(i2c_issue) + "\n"
		f.write(line)
		line = " Number of missing: " + str(missing) + "\n"
		f.write(line)
		f.write("-------------------------------------\n")
		f.write("-------------------------------------\n")
		f.close()
	t1 = time.time()
	print " Elapsed Time: " + str(t1 - t0)
	print "-------------------------------------"
	print "-------------------------------------"
	I2C.peri_write('EdgeSelT1Raw', 3)
	return bad_pix, error, stuck, i2c_issue, missing

def mem_test_probing(edge = 0, verbose = 1, print_log = 0, filename =  "../cernbox/MPA_Results/digital_mem_test.log"):
	reset()
	sleep(1)
	mpa_reset()
	sleep(1)
	activate_I2C_chip(verbose = 0)
	sleep(1)
	I2C.peri_write('EdgeSelT1Raw', edge)
	sleep(1)
	align_out()
	sleep(1)
	bad_pix, error, stuck, i2c_issue, missing = mem_test(print_log = print_log, filename = filename, gate = 0, verbose = verbose)
	return bad_pix, error, stuck, i2c_issue, missing

def mem_test_REN (latency = 255, delay = [10], delay_pulse_cal = 200,  delay_pulse_next = 200, row = range(1,17), pixel = range(1,121), diff = 2, print_log = 1, filename =  "../cernbox/MPA_Results/digital_mem_test.log", gate = 0):
	t0 = time.time()
	if print_log:
		f = open(filename, 'w')
		f.write("Starting Test:\n")
	activate_I2C_chip(verbose = 0)
	activate_sync()
	activate_pp()
	I2C.row_write('L1Offset_1', 0,  latency - diff)
	I2C.row_write('L1Offset_2', 0,  0)
	I2C.row_write('MemGatEn', 0,  gate)
	I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
	fc7.write("cnfg_fast_backpressure_enable", 0)
	disable_pixel(0,0)
	for d in delay:
		Configure_TestPulse_MPA(delay_after_fast_reset = d + 512, delay_after_test_pulse = delay_pulse_cal, delay_before_next_pulse = delay_pulse_next, number_of_test_pulses = 3, enable_L1 = 1, enable_rst = 1, enable_init_rst = 1)
		for r in row:
			for p in pixel:
				try:
					strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = memory_test(latency, r, p, diff, 0)
					if ((pixel_counter != 1) or (pos_pixel[0] != p) or (Z[0] != r)):
						error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(d) + " " + str(pixel_counter) + " " +  str(pos_pixel) + " " + str(Z) + "\n"
						print error_message
						if print_log:
							f.write(error_message)
				except TypeError:
					error_message = "Header not Found in Pixel: " + str(p) + " of Row: " + str(r) + "\n"
					print error_message
					if print_log:
						f.write(error_message)

	if print_log:
		f.write("Test Completed")
		f.close()
	t1 = time.time()
	print "END"
	print "Elapsed Time: " + str(t1 - t0)
