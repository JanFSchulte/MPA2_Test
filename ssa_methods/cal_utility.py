from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from ssa_methods.ssa_i2c_conf import *
import numpy as np
import time
import sys
import inspect

def init_all():
	reset()
	activate_I2C_chip()
	init_slvs()
	activate_readout_shift()
	set_shift_pattern_all(128) 
	time.sleep(0.01)
	do_phase_tuning()
	I2C.peri_write('OutPattern7/FIFOconfig', 7)
	activate_readout_normal()
	
def print_method(name):
	lines = inspect.getsourcelines(name)
	print("".join(lines[0]))

def init_slvs():
	I2C.peri_write('SLVS_pad_current', 0b001)

def do_phase_tuning():
	fc7.write("ctrl_phy_phase_tune_again", 1)
	while(fc7.read("stat_phy_phase_tuning_done") == 0):
        	sleep(0.5)
        	print "Waiting for the phase tuning"	

def set_t1_sampling_edge(edge):
	if edge == "rising" or edge == "positive":
		I2C.peri_write('EdgeSel_T1', 1)
	elif edge == "falling" or edge == "negative":
		I2C.peri_write('EdgeSel_T1', 0)
	else:
		print "Error! The edge name is wrong"

def activate_readout_normal():
	I2C.peri_write('ReadoutMode',0b00)

def activate_readout_async():
	I2C.peri_write('ReadoutMode',0b01)

def activate_readout_shift():
        I2C.peri_write('ReadoutMode',0b10)

def set_shift_pattern_all(pattern):
	set_shift_pattern(pattern,pattern,pattern,pattern,pattern,pattern,pattern,pattern)

def set_shift_pattern(line0, line1, line2, line3, line4, line5, line6, line7):
	I2C.peri_write('OutPattern0',line0)
	I2C.peri_write('OutPattern1',line1)
	I2C.peri_write('OutPattern2',line2)
	I2C.peri_write('OutPattern3',line3)
	I2C.peri_write('OutPattern4',line4)
	I2C.peri_write('OutPattern5',line5)
	I2C.peri_write('OutPattern6',line6)
	I2C.peri_write('OutPattern7/FIFOconfig',line7)

def set_async_delay(value):
	msb = (value & 0xFF00) >> 8
	lsb = (value & 0x00FF) >> 0 
	I2C.peri_write('AsyncRead_StartDel_MSB', msb)
	I2C.peri_write('AsyncRead_StartDel_LSB', lsb)
	
def read_all_lines():
	#SendCommand_CTRL("fast_test_pulse")
	#SendCommand_CTRL("fast_trigger")
	Configure_TestPulse(199, 50, 400, 1)
	sleep(0.001)
	SendCommand_CTRL("start_trigger")
	sleep(0.1)
	status = fc7.read("stat_slvs_debug_general")
	mpa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
	mpa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
	lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)

	print "--> Status: "
	print "---> MPA L1 Data Ready: ", ((status & 0x00000001) >> 0)
	print "---> MPA Stub Data Ready: ", ((status & 0x00000002) >> 1)
	print "---> MPA Counters Ready: ", ((status & 0x00000004) >> 2)
	print "---> Lateral Data Counters Ready: ", ((status & 0x00000008) >> 3)
	
	print "\n--> L1 Data: "
	for word in mpa_l1_data:
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

	counter = 0 
	print "\n--> Stub Data: "
	for word in mpa_stub_data:
	    if (counter % 10 == 0): 
	        print "Line: " + str(counter/10) 
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)
	    counter += 1
	
	print "\n--> Lateral Data: "
	for word in lateral_data:
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)


def start_counters_read():
    encode_fast_reset = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(1)
    fc7.write("ctrl_fast", encode_fast_reset + encode_orbit_reset)

def read_counters_fast(ssa_first_counter_delay, raw_mode_en = 0):
	# set the raw mode to the firmware
	fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_en)
	# write to the I2C
	I2C.peri_write("AsyncRead_StartDel_MSB", 0)
	I2C.peri_write("AsyncRead_StartDel_LSB", ssa_first_counter_delay)
	# check the value
	if (I2C.peri_read("AsyncRead_StartDel_LSB") != ssa_first_counter_delay):
		print "Error! I2C did not work properly"
		exit(1)
	# ssa set delay of the counters
	fc7.write("cnfg_phy_slvs_ssa_first_counter_del", ssa_first_counter_delay+25)
	
	# counter ready signal
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")

	start_counters_read()
	while ((mpa_counters_ready == 0)):
		sleep(0.01)
		mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	#print "---> MPA Counters Ready(should be one): ", mpa_counters_ready
	if raw_mode_en == 1:
		count = np.zeros((20000, ), dtype = np.uint16)
		for i in range(0,20000):
			fifo1_word = fc7.read("ctrl_slvs_debug_fifo1_data")
			fifo2_word = fc7.read("ctrl_slvs_debug_fifo2_data")
			#print "1: " + bin(reverse_mask(fifo1_word))
			#print "2: " + bin(reverse_mask(fifo2_word))
			line1 = to_number(fifo1_word,8,0)
			line2 = to_number(fifo1_word,16,8)
			count[i] = (line2 << 8) | line1
			#print line1, line2
			if (i%1000 == 0):
				print "Reading BX #", i
	else:
		# here is the parsed mode, when the fpga parses all the counters
		count = fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 120)
		# the last counter has to be read over I2C
		count[119] = I2C.strip_read("ReadCounter_LSB",120)

	sleep(0.1)
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")

	return count

def init_test_pulse():
	# enable strips
	I2C.strip_write("ENFLAGS", 0, 0b10101)
	# init thersholds
	I2C.peri_write("Bias_THDAC", 255-35)
	I2C.peri_write("Bias_THDACHIGH", 255-120)
	# init the dll
	I2C.peri_write("Bias_DL_en", 1)
	I2C.peri_write("Bias_DL_ctrl", 1)
	# init cal pulse itself
	I2C.peri_write("Bias_CALDAC", 255)
	I2C.peri_write("CalPulse_duration", 7)
