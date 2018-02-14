from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from ssa_methods.ssa_i2c_conf import *
from ssa_methods.cal_utility import *
from myScripts.Utilities import *
import numpy as np
import time
import sys
import inspect
import random


def set_lateral_data_phase(left, right):
	fc7.write("ctrl_phy_ssa_gen_lateral_phase_1", right)
	fc7.write("ctrl_phy_ssa_gen_lateral_phase_2", left)

def set_lateral_data(left, right):
	fc7.write("cnfg_phy_SSA_gen_right_lateral_data_format", right)
	fc7.write("cnfg_phy_SSA_gen_left_lateral_data_format", left)

def lateral_input_phase_tuning(display = False, timeout = 256):
	alined_left  = False
	alined_right = False
	print ""
	fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", 4)
	dig_pulse_injection(initialise = True)

	set_lateral_data(0b00001001, 0)
	cnt = 0
	while ((alined_left == False) and (cnt < timeout)):  
		clusters = readout_clusters(display_prev = display)
		if len(clusters) == 2:
			if(clusters[0] == 121 and clusters[1] == 124):
				alined_left = True
		time.sleep(0.001)
		set_lateral_data_phase(0,5)
		time.sleep(0.001)
		utils.ShowPercent(cnt, timeout+1, "Allaining left input line                    " )
		cnt += 1
	if(alined_left == True):
		utils.ShowPercent(100, 100, "Left Input line alined                    ")
	else: 
		utils.ShowPercent(100, 100, "Impossible to align left input data line  ")
	print "   " 

	set_lateral_data(0, 0b10011001)
	cnt = 0
	while ((alined_right == False) and (cnt < timeout)):  
		clusters = readout_clusters(display_prev = display)
		if len(clusters) == 2:
			if(clusters[0] == 0 and clusters[1] == -2):
				alined_right = True
		time.sleep(0.001)
		set_lateral_data_phase(5,0)
		time.sleep(0.001)
		utils.ShowPercent(cnt, timeout+1, "Allaining right input line")
		cnt += 1
	utils.ShowPercent(100)
	if(alined_right == True):
		utils.ShowPercent(100, 100, "Right input line alined")
	else: 
		utils.ShowPercent(100, 100, "Impossible to align right input data line")
	print "   " 

def dig_pulse_injection(hit_list = [], hip_list = [], initialise = True):
	
	if(initialise == True):
		#reset digital calib patterns
		activate_readout_normal()
		I2C.strip_write("DigCalibPattern_L", 0, 0)
		I2C.strip_write("DigCalibPattern_H", 0, 0)
		I2C.peri_write("CalPulse_duration", 15)
		I2C.strip_write("ENFLAGS", 0, 0b01001)
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", 4)
	
	I2C.strip_write("DigCalibPattern_L", 0, 0)
	I2C.strip_write("DigCalibPattern_H", 0, 0)
	leftdata  = 0b00000000
	rightdata = 0b00000000

	for cl in hit_list:
		if (cl < 1): 
			rightdata = rightdata | (0b1 << (7+cl))
		elif (cl > 120): 
			leftdata = leftdata | (0b1 << (cl-121))
		else: 
			I2C.strip_write("DigCalibPattern_L", cl, 0xff)

	set_lateral_data(left = leftdata, right = rightdata)

	for cl in hip_list:	
		I2C.strip_write("DigCalibPattern_H", cl, 0xff)

def analog_pulse_injection(hit_list = [], hip_list = [], threshold = 50, cal_pulse_amplitude = 200):
	
	activate_readout_normal()
	
	init_cal_pulse(cal_pulse_amplitude, 5)
	Configure_TestPulse_MPA_SSA(200, 1)
	set_threshold(threshold)

	#reset digital calib patterns
	I2C.strip_write("ENFLAGS", 0, 0b00001)
	I2C.strip_write("DigCalibPattern_L", 0, 0)
	I2C.strip_write("DigCalibPattern_H", 0, 0)

	#enable pulse injection in selected clusters
	for cl in hit_list:
		I2C.strip_write("ENFLAGS", cl, 0b10001)

	SendCommand_CTRL("start_trigger")
	sleep(0.01)


def readout_clusters(apply_offset_correction = False, display = False, shift = 0, initialize = True, display_prev = False):
 	ofs = [0]*6

 	if(initialize == True):
		Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 0)
		sleep(0.001)

	SendCommand_CTRL("start_trigger")
	SendCommand_CTRL("start_trigger")
	sleep(0.01)

	status = fc7.read("stat_slvs_debug_general")
	while ((status & 0x00000002) >> 1) != 1: 
		status = fc7.read("stat_slvs_debug_general")
		sleep(0.001)
		counter = 0 
	
	sleep(0.001)
	ssa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
	
	if (display is True):
		counter = 0 
		print "\n--> Stub Data: "
		for word in ssa_stub_data:
		    if (counter % 10 == 0): 
		        print "Line: " + str(counter/10) 
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)
		    counter += 1

 	if (apply_offset_correction == True):
		ofs[0] = I2C.peri_read('Offset0')
		ofs[1] = I2C.peri_read('Offset1')
		ofs[2] = I2C.peri_read('Offset2')
		ofs[3] = I2C.peri_read('Offset3')
		ofs[4] = I2C.peri_read('Offset4')
		ofs[5] = I2C.peri_read('Offset5')
 	
 	coordinates = []
 	
 	for i in range(0,8):
 		val = (to_number(ssa_stub_data[5+i*10],16,8) / 2.0) 
 		if val != 0:
	 		if (apply_offset_correction == True):
	 			val = val - 3
	 			## TO BE IMPLEMENTED
	 		else:
	 			val = val - 3
			coordinates.append( val )

	if (display_prev == True):
		coordinatesA = []
 		coordinatesC = []
	 	for i in range(0,8):
	 		val = (to_number(ssa_stub_data[5+i*10],24,16) / 2.0) 
	 		if val != 0:
		 		val = val - 3
				coordinatesA.append( val )
		for i in range(0,8):
	 		val = (to_number(ssa_stub_data[5+i*10],8,0) / 2.0) 
	 		if val != 0:
		 		val = val - 3
				coordinatesC.append( val )

		print coordinatesA
		print coordinates
		print coordinatesC
	 
	return coordinates

def readout_l1_data(latency = 50, display = False, shift = 0, initialise = True):
	if(initialise == True):
		fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
		fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
		
		I2C.peri_write('L1-Latency_MSB', 0)
		I2C.peri_write('L1-Latency_LSB', latency)

		activate_readout_normal()
		Configure_TestPulse(199, (latency+3+shift), 400, 1)
		sleep(0.001)

	SendCommand_CTRL("start_trigger")
	sleep(0.01)

	status = fc7.read("stat_slvs_debug_general")
	
	ssa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)

	if(display is True): 
		print "\n--> L1 Data: "
		for word in ssa_l1_data:
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

	data = 0
	for i in range(4,10):
		word = ssa_l1_data[i]
		tmp = (   int(bin(to_number(word,8,0)).lstrip('-0b').zfill(8),2)   <<24 
		        | int(bin(to_number(word,16,8)).lstrip('-0b').zfill(8),2)  <<16 
		        | int(bin(to_number(word,24,16)).lstrip('-0b').zfill(8),2) << 8 
		        | int(bin(to_number(word,32,24)).lstrip('-0b').zfill(8), 2)
		      )
		data = data | (tmp << (32*(9-i)))

	while ((data & 0b1) != 0b1 ):
		data =  data >> 1

	L1_counter = (data >> 154) & 0b1111
	BX_counter = (data >> 145) & 0b1111
	l1data = (data >> 1) & 0x00ffffffffffffffffffffffffffffff
	hidata = (data >> 121) & 0xffffff

	if(display is True): 
		print "L1 counter: " , str(L1_counter), "  (" ,  bin(L1_counter), ")" 
		print "BX counter: " , str(BX_counter), "  (" ,  bin(BX_counter), ")"

	l1datavect = [0]*120
	hipflagvect = [0]*24

	for i in range(0,120):
		l1datavect[i] = l1data & 0b1
		l1data = l1data >> 1

	for i in range(0,24):
		hipflagvect[i] = hidata & 0b1
		hidata = hidata >> 1

	#return l1datavect, hipflagvect
	l1hitlist = []
	for i in range(0,120):
		if(l1datavect[i] > 0): 
			l1hitlist.append(i+1)
	hiplist = [] 
	for i in range(0,24):
		if(hipflagvect[i] > 0): 
			hiplist.append(i+1)

	return L1_counter, BX_counter, l1hitlist, hiplist


def readout_lateral_data(display = False, shift = 0, initialize = True):
	if(initialize == True):
		Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 0)
		sleep(0.001)

	SendCommand_CTRL("start_trigger")
	SendCommand_CTRL("start_trigger")
	sleep(0.01)

	status = fc7.read("stat_slvs_debug_general")
	while ((status & 0x00000002) >> 1) != 1: 
		status = fc7.read("stat_slvs_debug_general")
		sleep(0.001)
		counter = 0 
	
	sleep(0.001)
	lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
	
	if (display is True):
		counter = 0 
		print "\n--> Lateral Data: "
		for word in lateral_data:
		    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)

 	coordinates = []

	right = to_number(lateral_data[5+shift+0*10],16,8)
 	left  = to_number(lateral_data[5+shift+1*10],16,8)

 	for i in range(1,9): 
 		if ((right & 0b1) == 1): 
 			coordinates.append(i)
 		right = right >> 1

 	for i in range(1,9): 
 		if ((left & 0b1) == 1): 
 			coordinates.append(112+i)
 		left = left >> 1
	 
	return coordinates


def test_cluster_data(display=False):
	dig_pulse_injection(hit_list = [], initialise = True)
	readout_clusters(initialize = True)
	cnt = 0
	for i in random.sample(range(-3, 125), 128):
		cnt += 1
		err = [False]*2
		dig_pulse_injection(hit_list = [i], initialise = False)
		#dig_pulse_injection(hit_list = [i], initialise = False)
		time.sleep(0.01)
		
		r = readout_clusters(initialize = False)
		l = []

		if (len(r) != 1): err[0] = True
		elif (r[0] != i): err[0] = True

		if( (i < 9 and i > 0) or (i > 112 and i < 121) ):
			l = readout_lateral_data(initialize = False)
			if (len(l) != 1): err[1] = True
			elif (l[0] != i): err[1] = True

		dstr = " -> expected: "+cl2str(i)+" found cluster: " + cl2str(r) + " found lateral: " + cl2str(l) 
		if (err[0]):
			print "\tCluster Error" + dstr
		elif(err[1]):
			print "\tLateral Error" + dstr  
		else:
			if(display == True): 
				print "\tPassed       " + dstr 

		utils.ShowPercent(cnt, 130, "Running clusters test based on digital test pulses")
	utils.ShowPercent(120, 120, "Done                                                      ")



def test_l1_data(display=False):
	
	dig_pulse_injection(hit_list = [], initialise = True)
	L1_counter_init, BX_counter, l1hitlist, hiplist = readout_l1_data(initialise = True)

	
	for H in range(0,2):
		cnt = 0
		dig_pulse_injection(hit_list = [], hip_list = [], initialise = True)
		for i in random.sample(range(1, 121), 120):
			cnt += 1
			err = False
			dig_pulse_injection(hit_list = [i], hip_list = [i]*H, initialise = False)
			#dig_pulse_injection(hit_list = [i], initialise = False)
			time.sleep(0.01)
			
			L1_counter, BX_counter, l1hitlist, hiplist = readout_l1_data(initialise = False)

			if( (L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ):
				print "\tL1 counter error. Expected" + str(((L1_counter_init + 1) & 0b1111)) + "Found: " + str((L1_counter & 0b1111)) + "                                   " 
			L1_counter_init = L1_counter

			if (len(l1hitlist) != 1): err = True
			elif (l1hitlist[0] != i): err = True
			if (len(hiplist) != H): err = True
			if(len(hiplist) > 0):
				if (hiplist[0] != H): err = True

			dstr = "\tError   -> expected: [" + str(i) + "]["+str(1)*H+"] found: " + str(l1hitlist) + str(hiplist) + "                                   "

			if (err):
				print dstr
			else:
				if(display == True): 
					print "\tPassed   -> expected: [" + str(i) + "]["+str(1)*H+"] found: " + str(l1hitlist) + str(hiplist) + "                                   "

			if(H == 1):
				utils.ShowPercent(cnt, 120, "Running basic HIP flag test based on digital test pulses")
			else:
				utils.ShowPercent(cnt, 120, "Running basic L1 data test based on digital test pulses")
		
		utils.ShowPercent(120, 120, "Done\t\t\n")





def read_all_lines():
	#SendCommand_CTRL("fast_test_pulse")
	#SendCommand_CTRL("fast_trigger")
	
	#fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
	#fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
	#fc7.write("cnfg_fast_tp_fsm_l1a_en", 0)
	#
	#Configure_TestPulse(199, 50, 400, 1)
	#sleep(0.001)
	#SendCommand_CTRL("start_trigger")
	#sleep(0.1)
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





#Configure_TestPulse_MPA_SSA(3, 0)
#SendCommand_CTRL('start_trigger')