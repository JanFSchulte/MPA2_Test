from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

class SSA_readout():

	def __init__(self, I2C, FC7, ssactrl, ssastrip):
		self.I2C = I2C
		self.fc7 = FC7
		self.ctrl = ssactrl
		self.strip = ssastrip
		self.ofs_initialised = False
		self.ofs = [0]*6


	def status(self):
		status = self.fc7.read("stat_slvs_debug_general")
		l1_data_ready   = ((status & 0x1) >> 0)
		stub_data_ready = ((status & 0x2) >> 1)
		counters_ready  = ((status & 0x4) >> 2)
		return [l1_data_ready, stub_data_ready, counters_ready]


	def cluster_data(self, apply_offset_correction = False, display = False, shift = 0, initialize = True, lookaround = False, getstatus = False, display_pattern = False):
	 	data = []
	 	tmp = []
	 	counter = 0
	 	data_loc = 21 + shift
	 	status = [0]*3
	 	#status_init = [0]*3
	 	timeout = 10
	 	if(initialize == True):
			Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 1)
			sleep(0.001)
		#status_init = self.status()
		SendCommand_CTRL("start_trigger")
		while (status[1] != 1 and counter<timeout):
			sleep(0.001)
			status = self.status()
			counter += 1
		ssa_stub_data = self.fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
		counter = 0
	 	for word in ssa_stub_data:
	 		counter += 1
 			tmp.append( to_number(word, 8, 0)/2.0 )
 			tmp.append( to_number(word,16, 8)/2.0 )
 			tmp.append( to_number(word,24,16)/2.0 )
 			tmp.append( to_number(word,32,24)/2.0 )
 			if (counter % 10 == 0):
 				data.append(tmp)
 				tmp = []
		if(display):
 			for i in data:
 				print "-->  ", i
 		if (not lookaround):
 			coordinates = []
	 		for block in data:
	 			if block[ data_loc ] != 0:
	 				val = self.__apply_offset_correction(block[ data_loc ], apply_offset_correction)
					coordinates.append( val )
		else:
			coordinates = np.zeros([8,40], dtype = np.float16)
			cnt0 = 0
			for i in range(0, 40):
				tmp = []
				cnt1 = 0
				for block in data:
		 			if block[ i ] != 0:
		 				val = self.__apply_offset_correction(block[ i ], apply_offset_correction)
						tmp.append( val )
				for st in tmp:
					coordinates[cnt1, cnt0] = st
					cnt1 += 1
				cnt0 += 1
		if(display_pattern):
			ctmp = np.array(data[0]).astype(bool).astype(int)
			print "[%5s]" % '|'.join(map(str, ctmp))
		if(getstatus):
			return coordinates, status
		else:
			return coordinates

	def cluster_data_delay(self, shift = 0, display = False, debug = False):
		cl_array = self.cluster_data(lookaround = True, display = display, display_pattern = debug)
		delay = [] #[-np.inf]*len(cl_array[0])
		cnt = -21 - shift
		for cl in cl_array[0]:
			if(cl != 0):
				delay.append(cnt)
			cnt += 1
		return delay

	def send_trigger(duration = 0):
		compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)

	def l1_data(self, latency = 50, display = False, shift = 0, initialise = True, mipadapterdisable = False):
		if(initialise == True):
			self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
			self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
			Configure_TestPulse(delay_after_fast_reset = 0, delay_after_test_pulse = (latency+3+shift), delay_before_next_pulse = 0, number_of_test_pulses = 1)
			self.fc7.write("cnfg_fast_delay_between_consecutive_trigeers", 0)
			self.I2C.peri_write('L1-Latency_MSB', 0)
			self.I2C.peri_write('L1-Latency_LSB', latency)
			self.ctrl.activate_readout_normal(mipadapterdisable = mipadapterdisable)
			sleep(0.001)

		SendCommand_CTRL("start_trigger")
		#send_trigger(1)
		sleep(0.01)
		status = self.fc7.read("stat_slvs_debug_general")
		sleep(0.001)
		ssa_l1_data = self.fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
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
		timeoutcnt = 1000
		while ((data & 0b1) != 0b1 ):
			data =  data >> 1
			if(timeoutcnt > 0):
				timeoutcnt -= 1
			else:
				print "->  \tL1 data packet missing"
				return -1, -1, -1, -1
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


	def lateral_data(self, display = False, shift = 0, initialize = True):
		if(initialize == True):
			Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 0)
			sleep(0.001)
		SendCommand_CTRL("start_trigger")
		SendCommand_CTRL("start_trigger")
		sleep(0.01)
		status = self.fc7.read("stat_slvs_debug_general")
		while ((status & 0x00000002) >> 1) != 1:
			status = self.fc7.read("stat_slvs_debug_general")
			sleep(0.001)
			counter = 0
		sleep(0.001)
		lateral_data = self.fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
		if (display is True):
			counter = 0
			print "\n--> Lateral Data: "
			for word in lateral_data:
			    print "--->", '%10s' % bin(to_number(word,8,0)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(word,32,24)).lstrip('-0b').zfill(8)
	 	coordinates = []
	 	left = 0
	 	right = 0
	 	for i in range(0,20):
			word = lateral_data[i]
			tmp = (   to_number(word, 8, 0) <<24
			        | to_number(word,16, 8) <<16
			        | to_number(word,24,16) << 8
			        | to_number(word,32,24) << 0
			      )
			if(i< 10):
				right = right | (tmp << (32*i))
			else:
				left = left | (tmp << (32*(i-10)))
		left  = (left  >> ((shift+13)*8)) & 0xff
		right = (right >> ((shift+13)*8)) & 0xff
	 	for i in range(1,9):
	 		if ((right & 0b1) == 1):
	 			coordinates.append(i-1)
	 		right = right >> 1
	 	for i in range(1,9):
	 		if ((left & 0b1) == 1):
	 			coordinates.append(112+i)
	 		left = left >> 1
		return coordinates


	def read_counters_fast(self, striplist = range(1,121), raw_mode_en = 0):
		self.fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_en)# set the raw mode to the firmware
		mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
		start_counters_read(1)
		timeout = 0
		failed = False
		while ((mpa_counters_ready == 0) & (timeout < 50)):
			sleep(0.01)
			timeout += 1
			mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
		if(timeout >= 50):
			failed = True;
			return failed, 0
		if raw_mode_en == 0:
			count = self.fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 120)
			count[119] = (self.I2C.strip_read("ReadCounter_MSB",120) << 8) | self.I2C.strip_read("ReadCounter_LSB",120)
		else:
			count = np.zeros((20000, ), dtype = np.uint16)
			for i in range(0,20000):
				fifo1_word = self.fc7.read("ctrl_slvs_debug_fifo1_data")
				fifo2_word = self.fc7.read("ctrl_slvs_debug_fifo2_data")
				line1 = to_number(fifo1_word,8,0)
				line2 = to_number(fifo1_word,16,8)
				count[i] = (line2 << 8) | line1
				if (i%1000 == 0): print "Reading BX #", i
		sleep(0.1)
		mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
		for s in range(0,120):
			if (not (s+1) in striplist):
				count[s] = 0
		return failed, count


	def read_counters_i2c(self, striplist = range(1,120)):
		count = [0]*120
		for s in striplist:
			count[s-1] = (self.I2C.strip_read("ReadCounter_MSB", s) << 8) | self.I2C.strip_read("ReadCounter_LSB", s)
		return False, count


	def all_lines(self):
		SendCommand_CTRL("fast_test_pulse")
		SendCommand_CTRL("fast_trigger")

		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 0)

		Configure_TestPulse(199, 50, 400, 1)
		sleep(0.001)
		SendCommand_CTRL("start_trigger")
		sleep(0.1)
		status = self.fc7.read("stat_slvs_debug_general")
		ssa_l1_data = self.fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
		ssa_stub_data = self.fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
		lateral_data = self.fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)

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


	def __apply_offset_correction(self, val, enable = True):
		if(not enable):
			cr = val - 3
		else:
			if(not self.ofs_initialised):
				self.ofs[0] = self.I2C.peri_read('Offset0')
				self.ofs[1] = self.I2C.peri_read('Offset1')
				self.ofs[2] = self.I2C.peri_read('Offset2')
				self.ofs[3] = self.I2C.peri_read('Offset3')
				self.ofs[4] = self.I2C.peri_read('Offset4')
				self.ofs[5] = self.I2C.peri_read('Offset5')
				self.ofs_initialised = True
			## TO BE IMPLEMENTED
			cr = val - 3
			## TO BE IMPLEMENTED
		return cr




class SSA_inject():


	def __init__(self, I2C, FC7, ssactrl, ssastrip):
		self.I2C = I2C
		self.fc7 = FC7
		self.ctrl = ssactrl
		self.strip = ssastrip
		self.hitmode = 'none'


	def digital_pulse(self, hit_list = [], hip_list = [], times = 1, initialise = True):
		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.I2C.peri_write("CalPulse_duration", times)
			self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			#fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", 4)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0)
		leftdata  = 0b00000000
		rightdata = 0b00000000
		for cl in hit_list:
			if (cl < 1):
				rightdata = rightdata | (0b1 << (7+cl))
			elif (cl > 120):
				leftdata = leftdata | (0b1 << (cl-121))
			else:
				self.I2C.strip_write("DigCalibPattern_L", cl, 0xff)
		self.ctrl.set_lateral_data(left = leftdata, right = rightdata)
		for cl in hip_list:
			self.I2C.strip_write("DigCalibPattern_H", cl, 0xff)
		sleep(0.001)


	def analog_pulse(self, hit_list = [], mode = 'edge', threshold = [20, 100], cal_pulse_amplitude = 200, initialise = True, trigger = False):
		if(initialise == True):
			self.ctrl.activate_readout_normal()
			self.ctrl.set_cal_pulse(amplitude = cal_pulse_amplitude, duration = 15, delay = 'keep')
			self.ctrl.set_threshold(threshold[0])
			self.ctrl.set_threshold_H(threshold[1])
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			#Configure_TestPulse_MPA_SSA(200, 1)
		if(mode != self.hitmode): # to speed up
			self.hitmode = mode
			self.strip.set_sampling_mode('all', mode)
		#enable pulse injection in selected clusters
		self.I2C.strip_write("ENFLAGS", 0, 0b00000)
		for cl in hit_list:
			if(cl > 0 and cl < 121):
				self.I2C.strip_write("ENFLAGS", cl, 0b10001)
				sleep(0.001)
		if(trigger == True):
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
			SendCommand_CTRL("start_trigger")
			sleep(0.01)
		sleep(0.001)
