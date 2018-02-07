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
	
def start_counters_read():
    encode_fast_reset = fc7AddrTable.getItem("ctrl_fast_signal_fast_reset").shiftDataToMask(1)
    encode_orbit_reset = fc7AddrTable.getItem("ctrl_fast_signal_orbit_reset").shiftDataToMask(1)
    fc7.write("ctrl_fast", encode_fast_reset + encode_orbit_reset)

def read_counters_fast(ssa_first_counter_delay = 8, raw_mode_en = 0):
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
	timeout = 0
	while ((mpa_counters_ready == 0) & (timeout < 50)):
		sleep(0.01)
		timeout += 1
		mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	if(timeout >= 50):
		failed = True;
		return failed, 0
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
		count[119] = (I2C.strip_read("ReadCounter_MSB",120) << 8) | I2C.strip_read("ReadCounter_LSB",120)

	sleep(0.1)
	mpa_counters_ready = fc7.read("stat_slvs_debug_mpa_counters_ready")
	failed = False
	return failed, count

def set_threshold(value):
	I2C.peri_write("Bias_THDAC", value)
	if(I2C.peri_read("Bias_THDAC") != value):
		print "Error. Failed to set the threshold"
		error(1)

def init_default_thresholds():
	# init thersholds
	I2C.peri_write("Bias_THDAC", 35)
	I2C.peri_write("Bias_THDACHIGH", 120)

def init_cal_pulse(cal_pulse_amplitude = 255, cal_pulse_duration = 3):
	# enable strips
	I2C.strip_write("ENFLAGS", 0, 0b10101)
	# init the dll
	I2C.peri_write("Bias_DL_en", 1)
	I2C.peri_write("Bias_DL_ctrl", 1)
	# init cal pulse itself
	I2C.peri_write("Bias_CALDAC", cal_pulse_amplitude)
	I2C.peri_write("CalPulse_duration", cal_pulse_duration)

def measure_scurves(nevents = 50, cal_pulse_amplitude = 0):
	# first go to the async mode
	activate_readout_async()
	# close shutter and clear counters
	close_shutter()
	clear_counters()
	# configure test pulse if needed
	if cal_pulse_amplitude > 0:
		# init chip cal pulse
		init_cal_pulse(cal_pulse_amplitude, 3)
		# init firmware cal pulse
		Configure_TestPulse_MPA_SSA(200, nevents)
	else:
		# set the strip enflags (just in case)
		I2C.strip_write("ENFLAGS", 0, 0b00101)	

	# then let's try to measure the scurves
	scurves = np.zeros((256,120), dtype=np.int)
	
	threshold = 0
	while (threshold < 256):
		# debug output		
		print "Setting the threshold to ", threshold, ", sending the test pulse and reading the counters"
		# set the threshold
		set_threshold(threshold)
		# clear counters
		clear_counters()
		# open shutter
		open_shutter()
		# send sequence of NEVENTS pulses
		SendCommand_CTRL("start_trigger")
		# sleep a bit and wait for trigger to finish
		sleep(0.01)
		while(fc7.read("stat_fast_fsm_state") != 0):
			sleep(0.1)
		# close shutter and read counters
		close_shutter()
		failed, scurves[threshold] = read_counters_fast()
		if failed:
			print "Failed to read counters for threshold ", threshold, ". Redoing"
			threshold = threshold - 1
		# threshold increment
		threshold = threshold + 1
		
	return scurves
