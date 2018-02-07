from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from ssa_methods.ssa_i2c_conf import *
from ssa_methods.cal_utility import *

import numpy as np
import time
import sys
import inspect

def select_dig_pulse_injection(hit_list = [], hip_list = []):
	
	activate_readout_normal()
	#reset digital calib patterns
	I2C.strip_write("ENFLAGS", 0, 0b00001)
	I2C.strip_write("DigCalibPattern_L", 0, 0)
	I2C.strip_write("DigCalibPattern_H", 0, 0)
	
	#enable pulse injection in selected clusters
	for cl in hit_list:
		I2C.strip_write("ENFLAGS", 0, 0b01001)
		I2C.strip_write("DigCalibPattern_L", cl, 0xff)
	for cl in hip_list:	
		I2C.strip_write("ENFLAGS", 0, 0b01001)
		I2C.strip_write("DigCalibPattern_H", cl, 0xff)


def readout_clusters(apply_offset_correction = True, display = False):

 	coordinates = []
 	ofs = [0]*6
	fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
	fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
	fc7.write("cnfg_fast_tp_fsm_l1a_en", 0)
	activate_readout_normal()
	Configure_TestPulse(199, 50, 400, 1)
	sleep(0.001)
	SendCommand_CTRL("start_trigger")
	sleep(0.01)

	status = fc7.read("stat_slvs_debug_general")
	ssa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
	lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
	
	while ((status & 0x00000002) >> 1) != 1: 
		status = fc7.read("stat_slvs_debug_general")
		sleep(0.001)
		counter = 0 
	
	if (display is True):
		counter = 0 
		print "\n--> Stub Data: "
		for word in ssa_stub_data:
		    if (counter % 10 == 0): 
		        print "Line: " + str(counter/10) 
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)
		    counter += 1
		
		print "\n--> Lateral Data: "
		for word in lateral_data:
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)


 	if (apply_offset_correction == True):
		ofs[0] = I2C.peri_read('Offset0')
		ofs[1] = I2C.peri_read('Offset1')
		ofs[2] = I2C.peri_read('Offset2')
		ofs[3] = I2C.peri_read('Offset3')
		ofs[4] = I2C.peri_read('Offset4')
		ofs[5] = I2C.peri_read('Offset5')

 	for i in range(0,8):
 		
 		val = (to_number(ssa_stub_data[5+i*10],32,24) / 2.0) 
 		
 		if val != 0:
	 		if (apply_offset_correction == True):
	 			## TO BE IMPLEMENTED
	 			val = val - 3
			coordinates.append( val )

	return coordinates


def readout_l1_data(latency = 50, display = False):

	l1datavect = [0]*120
	hipflagvect = [0]*24

	fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
	fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
	fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
	
	activate_readout_normal()
	Configure_TestPulse(199, (latency+3), 400, 1)
	sleep(0.001)
	SendCommand_CTRL("start_trigger")
	sleep(0.1)

	I2C.peri_write('L1-Latency_MSB', 0)
	I2C.peri_write('L1-Latency_LSB', latency)

	status = fc7.read("stat_slvs_debug_general")
	
	ssa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
	
	if(display is True): 
		print "\n--> L1 Data: "
		for word in ssa_l1_data:
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

	L1_counter = int(bin(to_number(ssa_l1_data[4],21,17)).lstrip('-0b').zfill(8),2)
	BX_counter = (int(bin(to_number(ssa_l1_data[4],23,22)).lstrip('-0b').zfill(8),2) << 8) | (int(bin(to_number(ssa_l1_data[4],32,24)).lstrip('-0b').zfill(8),2)) 
	data = 0

	print "L1 counter: " + str(L1_counter)
	print "BX counter: " + str(BX_counter)

	for i in range(5,10):
		word = ssa_l1_data[i]
		tmp = (   int(bin(to_number(word,8,0)).lstrip('-0b').zfill(8),2)   <<32 
		        | int(bin(to_number(word,16,8)).lstrip('-0b').zfill(8),2)  <<16 
		        | int(bin(to_number(word,24,16)).lstrip('-0b').zfill(8),2) << 8 
		        | int(bin(to_number(word,32,24)).lstrip('-0b').zfill(8), 2)
		      )
		data = data | (tmp << (32*(9-i)))
	data = data >> 16
	for i in range(0,120):
		l1datavect[i] = data & 0b1
		data = data >> 1
	tmp = (   int(bin(to_number(ssa_l1_data[5], 8, 0)).lstrip('-0b').zfill(8),2)  << 16 
		    | int(bin(to_number(ssa_l1_data[5],16, 8)).lstrip('-0b').zfill(8),2)  << 8 
	        | int(bin(to_number(ssa_l1_data[5],24,16)).lstrip('-0b').zfill(8),2)  
	        
	      )
	for i in range(0,24):
		hipflagvect[i] = tmp & 0b1
		tmp = tmp >> 1

	return l1datavect, hipflagvect

def read_all_lines():
	#SendCommand_CTRL("fast_test_pulse")
	#SendCommand_CTRL("fast_trigger")
	fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
	fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
	fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)

	Configure_TestPulse(199, 50, 400, 1)
	sleep(0.001)
	SendCommand_CTRL("start_trigger")
	sleep(0.1)
	status = fc7.read("stat_slvs_debug_general")
	ssa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
	ssa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
	lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)

	print "--> Status: "
	print "---> MPA L1 Data Ready: ", ((status & 0x00000001) >> 0)
	print "---> MPA Stub Data Ready: ", ((status & 0x00000002) >> 1)
	print "---> MPA Counters Ready: ", ((status & 0x00000004) >> 2)
	print "---> Lateral Data Counters Ready: ", ((status & 0x00000008) >> 3)
	
	print "\n--> L1 Data: "
	for word in ssa_l1_data:
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

	counter = 0 
	print "\n--> Stub Data: "
	for word in ssa_stub_data:
	    if (counter % 10 == 0): 
	        print "Line: " + str(counter/10) 
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)
	    counter += 1
	
	print "\n--> Lateral Data: "
	for word in lateral_data:
	    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)


#print "\n--> L1 Data: "
#for word in ssa_l1_data:
#    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)



