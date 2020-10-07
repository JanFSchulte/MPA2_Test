import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.tbsettings import *

'''
fc7.read("stat_slvs_debug_general")
mpa_l1_data = fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
mpa_stub_data = fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
fc7.read("stat_slvs_debug_general")
'''

class SSA_readout():

	def __init__(self, index, I2C, FC7, ssactrl, ssastrip):
		self.index = index
		self.I2C = I2C;	self.fc7 = FC7; self.ctrl = ssactrl;
		self.strip = ssastrip; self.utils = utils;
		self.ofs_initialised = False;  self.ofs = [0]*6;
		self.cl_shift = {'digital':0, 'analog':0}
		self.lateral_shift = {'digital':0, 'analog':0}
		self.countershift = {'state':False, 'value':0}

	def status(self, display=True):
		status = self.fc7.read("stat_slvs_debug_general")
		l1_data_ready   = ((status & 0x1) >> 0)
		stub_data_ready = ((status & 0x2) >> 1)
		counters_ready  = ((status & 0x4) >> 2)
		if(display):
			utils.print_log('->  L1 data ready:   {:d}'.format(l1_data_ready))
			utils.print_log('->  Stub data ready: {:d}'.format(stub_data_ready))
			utils.print_log('->  Counters ready:  {:d}'.format(counters_ready))
		return [l1_data_ready, stub_data_ready, counters_ready]


	def cluster_data(self, apply_offset_correction = False, display = False, shift = 'default', initialize = True, lookaround = False, getstatus = False, display_pattern = False, send_test_pulse = True, raw = False, return_as_pattern = False, profile=False):
		data = []; tmp = [];
		if(shift == 'default'):
			ishift = self.cl_shift['digital']
			if('ssa_inject_utility_mode') in utils.generic_parameters:
				if(utils.generic_parameters['ssa_inject_utility_mode'] == 'analog'):
					ishift = self.cl_shift['analog']
		else:
			ishift = shift
		counter = 0; data_loc = 21 + ishift;
		status = [0]*3; timeout = 10;
		if(initialize):
			self.ctrl.setup_readout_chip_id()
			#Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 1)
			Configure_TestPulse_SSA(delay_after_fast_reset = 0, delay_after_test_pulse = 0, delay_before_next_pulse = 500, number_of_test_pulses = 1, enable_rst_L1 = 0)
			time.sleep(0.005)
			self.fc7.SendCommand_CTRL("stop_trigger")
		if(profile): pr_start=time.time()
		#status_init = self.status(display=0)
		if(send_test_pulse):
			#self.fc7.SendCommand_CTRL("stop_trigger")
			self.fc7.SendCommand_CTRL("start_trigger")
			self.fc7.SendCommand_CTRL("start_trigger") # repeated for FC7 code timing issue
			self.fc7.SendCommand_CTRL("start_trigger") # repeated for FC7 code timing issue

		if(profile): utils.print_log('->  cluster readout 1 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		#### status doesn't get reset in the FC7
		#### while (status[1] != 1 and counter<timeout):
		#### 	#time.sleep(0.001)
		#### 	status = self.status(display=0)
		#### 	counter += 1
		ssa_stub_data = self.fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
		#self.fc7.SendCommand_CTRL("stop_trigger")
		counter = 0
		if(profile): utils.print_log('->  cluster readout 2 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		for word in ssa_stub_data:
			counter += 1
			tmp.append( to_number(word, 8, 0)/2.0 )
			tmp.append( to_number(word,16, 8)/2.0 )
			tmp.append( to_number(word,24,16)/2.0 )
			tmp.append( to_number(word,32,24)/2.0 )
			if (counter % 10 == 0):
				data.append(tmp)
				tmp = []
		if(profile): utils.print_log('->  cluster readout 3 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		if raw:
			return data
		if(display):
			for i in data:
				utils.print_log("-->  " + str(i) )
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
			utils.print_log( "[{:5s}]".format( '|'.join(map(str, ctmp)) ) )
		if(self.index==1): # 2xSSA test board has inverted lines for chip 1
			coordinates.sort()
		if return_as_pattern:
			ctmp = np.zeros([8,40])
			for i in range(0,8):
				ctmp[i,:] = data[i]
			return ctmp
		elif(getstatus):
			return coordinates, status
		else:
			return coordinates

	def cluster_data_delay(self, shift = 'default', display = False, debug = False):
		self.ctrl.setup_readout_chip_id()
		if(shift == 'default'):
			ishift = self.cl_shift
		cl_array = self.cluster_data(lookaround = True, display = display, display_pattern = debug)
		delay = [] #[-np.inf]*len(cl_array[0])
		cnt = -21 - ishift
		for cl in cl_array[0]:
			if(cl != 0):
				delay.append(cnt)
			cnt += 1
		return delay

	def send_trigger(self, duration = 0):
		self.fc7.compose_fast_command(duration, resync_en = 0, l1a_en = 1, cal_pulse_en = 0, bc0_en = 0)


	def l1_data(self, latency = 50, shift = 0, initialise = True, mipadapterdisable = True, trigger = True, multi = True, display = False, display_raw = False, profile=False):
		#disable_pixel(0,0)
		if(initialise == True):
			self.ctrl.setup_readout_chip_id()
			self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
			self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
			Configure_TestPulse_SSA(
				delay_after_fast_reset = 0, delay_after_test_pulse = (latency+2+shift),
				delay_before_next_pulse = 0, number_of_test_pulses = 1, enable_rst_L1 = 0,
				enable_initial_reset = 0, enable_L1 = 1)
			self.fc7.write("cnfg_fast_delay_between_consecutive_trigeers", 0)
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.peri_write(register="control_1", field='L1_Latency_msb', data = 0 )
				self.I2C.peri_write(register="control_3", field='L1_Latency_lsb', data = latency )
			else:
				self.I2C.peri_write('L1_Latency_msb', 0)
				self.I2C.peri_write('L1_Latency_lsb', latency)
			self.ctrl.activate_readout_normal(mipadapterdisable = mipadapterdisable)
			time.sleep(0.001)
		if(profile): pr_start=time.time()
		if trigger:
			self.fc7.SendCommand_CTRL("start_trigger")
			#self.send_trigger(1)
		if(profile): utils.print_log('->  L1 readout 1 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		#time.sleep(0.01)
		status = self.fc7.read("stat_slvs_debug_general")
		#time.sleep(0.001)
		if(profile): utils.print_log('->  L1 readout 2 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		ssa_l1_data = self.fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
		if(profile): utils.print_log('->  L1 readout 3 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		if(display_raw):
			utils.print_log("\n->  L1 Data: ")
			for word in ssa_l1_data:
			    utils.print_log(
					'    \t->' +
					'{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) )
				)
		data = 0
		for i in range(0,50):
			word = ssa_l1_data[i]
			tmp = (   int(bin(to_number(word,8,0)).lstrip('-0b').zfill(8),2)   <<24
			        | int(bin(to_number(word,16,8)).lstrip('-0b').zfill(8),2)  <<16
			        | int(bin(to_number(word,24,16)).lstrip('-0b').zfill(8),2) << 8
			        | int(bin(to_number(word,32,24)).lstrip('-0b').zfill(8), 2)
			      )
			data = data | (tmp << (32*(49-i)))
		end = False; ret = [];
		timeoutcnt = 50*32
		if(profile): utils.print_log('->  L1 readout 4 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		while (not end):
			while ((data & 0b1) != 0b1 ):
				data =  data >> 1
				if(timeoutcnt > 0):
					timeoutcnt -= 1
				else:
					end = True;	break;
			if(end): break
			if(display_raw):
				utils.print_log("\n->  L1 Data Subset: {:s}\n".format(bin(data)))
			if(tbconfig.VERSION['SSA'] >= 2):
				L1_counter = (data >> 157) & 0x1ff
				BX_counter = (data >> 148) & 0x1ff
				l1data = (data >> 4) & 0x00ffffffffffffffffffffffffffffff
				hidata = (data >> 124) & 0xffffff
			else:
				L1_counter = (data >> 154) & 0xf
				BX_counter = (data >> 145) & 0x1ff
				l1data = (data >> 1) & 0x00ffffffffffffffffffffffffffffff
				hidata = (data >> 121) & 0xffffff
			#utils.print_log(bin(hidata))
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
			if(display):
				utils.print_log("->  L1 ={:3d}  |  BX ={:4d}  |  HIT = [{:3s}]  |  HIP = [{:3s}]".format(
					L1_counter,  BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)) ) )

			#utils.print_log(data)
			data =  data >> 160
			if(not multi):
				end = True
				ret = [L1_counter, BX_counter, l1hitlist, hiplist]
			else:
				ret.append([L1_counter, BX_counter, l1hitlist, hiplist])
		if len(ret) == 0:
			if multi: ret = [[-1,-1,[],[]]]
			else: ret = [-1,-1,[],[]]
		if(profile): utils.print_log('->  L1 readout 5 -> {:0.3f}ms'.format(1000*(time.time()-pr_start)))
		return ret
#		ssa.readout.l1_data(display = True, trigger = False, display_raw = 1)


	def lateral_data(self, display = False, shift = 0, initialize = True, raw = False):
		if(shift == 'default'):
			ishift = self.lateral_shift['digital']
			if('ssa_inject_utility_mode') in utils.generic_parameters:
				if(utils.generic_parameters['ssa_inject_utility_mode'] == 'analog'):
					ishift = self.lateral_shift['analog']
		else:
			ishift = shift
		if(initialize == True):
			#Configure_TestPulse_MPA_SSA(number_of_test_pulses = 1, delay_before_next_pulse = 0)
			self.ctrl.setup_readout_chip_id()
			Configure_TestPulse_SSA(    number_of_test_pulses = 1, delay_before_next_pulse = 500, delay_after_test_pulse = 0, delay_after_fast_reset = 0, enable_rst_L1 = 0)
			time.sleep(0.001)
		self.fc7.SendCommand_CTRL("start_trigger")
		#self.fc7.SendCommand_CTRL("start_trigger")
		time.sleep(0.01)
		status = self.fc7.read("stat_slvs_debug_general")
		#while ((status & 0x00000002) >> 1) != 1:
		#	status = self.fc7.read("stat_slvs_debug_general")
		#	time.sleep(0.001)
		#	counter = 0
		time.sleep(0.001)
		lateral_data = self.fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
		if (display is True):
			counter = 0
			utils.print_log("\n--> Lateral Data: ")
			for word in lateral_data:
				utils.print_log(
					'    \t->' +
					'{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
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
		left  = (left  >> ((ishift+9)*8)) & 0xff
		right = (right >> ((ishift+9)*8)) & 0xff
		if(raw):
			return bin(left), bin(right)
		for i in range(1,9):
			if ((right & 0b1) == 1):
				coordinates.append(i)
			right = right >> 1
		for i in range(1,9):
			if ((left & 0b1) == 1):
				coordinates.append(112+i)
			left = left >> 1
		return coordinates


	def counters_fast(self, striplist = range(1,121), raw_mode_en = 0, shift = 'auto', initialize = True, silent=0):
		#t = time.time()
		if(initialize):
			self.ctrl.setup_readout_chip_id()
			self.fc7.write("cnfg_phy_slvs_raw_mode_en", raw_mode_en)# set the raw mode to the firmware
			#self.I2C.peri_write('AsyncRead_StartDel_LSB', (11 + shift) )
		if(isinstance(shift, int) and (shift != self.countershift['value'])):
			self.ctrl.set_async_readout_start_delay(delay=8, fc7_correction=shift)
			self.countershift['state'] = True
			self.countershift['value'] = shift
			if(not silent): utils.print_log('->  Updating the counters alignment value to {:d}'.format(shift))
		else:
			if(self.countershift['state']):
				self.ctrl.set_async_readout_start_delay(delay=8, fc7_correction=self.countershift['value'])
			else:
				self.align_counters_readout()
		mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
		#self.I2C.peri_write('AsyncRead_StartDel_LSB', (8) )
		self.fc7.start_counters_read(1)
		timeout = 0
		failed = False
		while ((mpa_counters_ready == 0) & (timeout < 100)):
			#### time.sleep(0.01)
			timeout += 1
			mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
			time.sleep(0.001)
		if(timeout >= 50):
			failed = True;
			return failed, -1
		if raw_mode_en == 0:
			count = self.fc7.fifoRead("ctrl_slvs_debug_fifo2_data", 120)
			if(tbconfig.VERSION['SSA'] == 1):
				if(119 in striplist): ## BUG IN SSA CHIP (STRIP 120 COUNTER READABLE ONLY VIA I2C) FIXED in SSAv2
					count[119] = (self.I2C.strip_read("ReadCounter_MSB",120) << 8) | self.I2C.strip_read("ReadCounter_LSB",120)
		else:
			count = np.zeros((20000, ), dtype = np.uint16)
			for i in range(0,20000):
				fifo1_word = self.fc7.read("ctrl_slvs_debug_fifo1_data")
				fifo2_word = self.fc7.read("ctrl_slvs_debug_fifo2_data")
				line1 = to_number(fifo1_word,8,0)
				line2 = to_number(fifo1_word,16,8)
				count[i] = (line2 << 8) | line1
				if (i%1000 == 0): utils.print_log("Reading BX #" + str(i))
		#### time.sleep(0.1)
		#### mpa_counters_ready = self.fc7.read("stat_slvs_debug_mpa_counters_ready")
		for s in range(0,120):
			if (not (s+1) in striplist):
				count[s] = 0
		#utils.print_log((time.time()-t)*1E3)
		return failed, count

	def align_counters_readout(self, threshold=50, amplitude=150, duration=1):
		utils.print_log('->  Running counters readout alignment procedure')
		self.fc7.SendCommand_CTRL("stop_trigger")
		self.cluster_data(initialize=True)
		self.ctrl.activate_readout_async(ssa_first_counter_delay='keep')
		time.sleep(0.001)
		Configure_TestPulse_SSA(50,50,500,1000,0,0,0)
		self.strip.set_cal_strips(mode = 'counter', strip = 'all')
		self.ctrl.set_cal_pulse(amplitude=amplitude, duration=duration, delay='keep')
		self.ctrl.set_threshold(threshold);  # set the threshold
		self.fc7.clear_counters(1)
		self.fc7.open_shutter(1, 1)
		self.fc7.SendCommand_CTRL("start_trigger")
		time.sleep(0.1)
		self.fc7.close_shutter(1,1)
		successfull = False
		for countershift in range(-5,5):
			failed, counters = self.counters_fast(range(1,121), shift = countershift, initialize = 1, silent=True)
			mean = np.mean(counters)
			print('->  ' + str([countershift, mean]))
			if((not failed) and (mean>990) and (mean<1100)):
				successfull = True
				break
		self.countershift['state'] = True
		self.countershift['value'] = countershift
		return [successfull, countershift, mean]


	def counters_via_i2c(self, striplist = range(1,120)):
		count = [0]*120
		for s in striplist:
			if(tbconfig.VERSION['SSA'] >= 2):
				rmsb  = self.I2C.strip_read(register="AC_ReadCounterMSB", field=False, strip=s)
				rlsb  = self.I2C.strip_read(register="AC_ReadCounterLSB", field=False, strip=s)
				count[s-1] = ((rmsb << 8) | rlsb)
			else:
				count[s-1] = (self.I2C.strip_read("ReadCounter_MSB", s) << 8) | self.I2C.strip_read("ReadCounter_LSB", s)
		return False, count

	def all_lines_debug(self, trigger = True, configure = True, cluster = True, l1data = True, lateral = False):
		if(configure):
			self.ctrl.setup_readout_chip_id()
			self.fc7.SendCommand_CTRL("fast_test_pulse")
			self.fc7.SendCommand_CTRL("fast_trigger")
			self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
			self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 0)
			Configure_TestPulse(199, 50, 400, 1)

			#Configure_TestPulse_SSA(    number_of_test_pulses = 1, delay_before_next_pulse = 500, delay_after_test_pulse = 0, delay_after_fast_reset = 0, enable_rst_L1 = 0)

			time.sleep(0.001)
		if(trigger):
			self.fc7.SendCommand_CTRL("start_trigger")
			time.sleep(0.001)
		status = self.fc7.read("stat_slvs_debug_general")
		ssa_l1_data = self.fc7.blockRead("stat_slvs_debug_mpa_l1_0", 50, 0)
		ssa_stub_data = self.fc7.blockRead("stat_slvs_debug_mpa_stub_0", 80, 0)
		lateral_data = self.fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
		utils.print_log("--> Status: ")
		utils.print_log("---> MPA L1 Data Ready: " + str((status & 0x00000001) >> 0))
		utils.print_log("---> MPA Stub Data Ready: " + str((status & 0x00000002) >> 1))
		utils.print_log("---> MPA Counters Ready: " +str((status & 0x00000004) >> 2))
		utils.print_log("---> Lateral Data Counters Ready: "  + str((status & 0x00000008) >> 3))
		if(l1data):
			utils.print_log("\n--> L1 Data: ")
			for word in ssa_l1_data:
				utils.print_log(
					'    \t->' +
					'{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
		if(cluster):
			counter = 0
			utils.print_log("\n--> Stub Data: ")
			for word in ssa_stub_data:
				if (counter % 10 == 0):
					utils.print_log("Line: " + str(counter/10))
				utils.print_log(
					'    \t->' +
					'{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
				counter += 1
		if(lateral):
			utils.print_log("\n--> Lateral Data: ")
			for word in lateral_data:
				utils.print_log(
					'    \t->' +
					'{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
					'{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )


	def __apply_offset_correction(self, val, enable = True):
		if(not enable):
			if(tbconfig.VERSION['SSA'] >= 2):
				cr = val - 3.5
			else:
				cr = val - 3.0
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


#	def alignment_slvs(align_word = 128, step = 10):
#	    t0 = time.time()
#	    activate_I2C_chip(self.fc7)
#	    I2C.peri_write('LFSR_data', align_word)
#	    activate_shift()
#	    phase = 0
#	    fc7.write("ctrl_phy_fast_cmd_phase",phase)
#	    aligned = 0
#	    count = 0
#	    while ((not aligned) or (count <= (168/step))):
#	        send_test()
#	        send_trigger()
#	        array_stubs = read_stubs(1)
#	        array_l1 = read_L1()
#	        aligned = 1
#	        for word in array_stubs[:,0]: # CHheck stub lines alignment
#	            if (word != align_word):
#	                aligned = 0
#	        if (array_l1[0,0] != align_word): # CHheck L1 lines alignment
#	            aligned = 0
#	        if (not aligned): # if not alignment change phase with T1
#	            phase += step
#	            fc7.write("ctrl_phy_fast_cmd_phase",phase)
#	        count += 1
#	    if (not aligned):
#	        utils.print_log("Try with finer step")
#	    else:
#	        utils.print_log("All stubs line aligned!")
#	    t1 = time.time()
#	    utils.print_log("Elapsed Time: " + str(t1 - t0))
