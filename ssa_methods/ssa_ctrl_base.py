from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt

class ssa_ctrl_base:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;
		self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
		self.dll_chargepump = 0b00;
		self.bias_dl_enable = False


	def resync(self):
		SendCommand_CTRL("fast_fast_reset");
		print '->  \tSent Re-Sync command'
		sleep(0.001)


	def reset(self, display=True):
		rp = self.pwr.reset(display=display)
		self.set_t1_sampling_edge("negative")
		return rp

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True, rtarray = False, strip_list = range(1,121)):
		registers = []; rm = []
		peri_reg_map  = self.ssa_peri_reg_map.copy()
		for i in peri_reg_map:
			if('Fuse' in i): rm.append(i)
			if('SEU' in i): rm.append(i)
		for k in rm:
			peri_reg_map.pop(k, None)
		strip_reg_map = self.ssa_strip_reg_map.copy()
		for i in strip_reg_map:
			if('ReadCounter' in i): rm.append(i)
		for k in rm:
			strip_reg_map.pop(k, None)
		for reg in peri_reg_map:
			tmp = [-1, reg, self.I2C.peri_read(reg)]
			registers.append(tmp)
		for strip in strip_list:
			for reg in strip_reg_map:
				tmp = [strip, reg, self.I2C.strip_read(reg, strip)]
				registers.append(tmp)
		#print "->  \tConfiguration Saved on file:   " + str(file)
		if display:
			for i in registers:
				print i
		dir = file[:file.rindex(os.path.sep)]
		if not os.path.exists(dir): os.makedirs(dir)
		CSV.ArrayToCSV(registers, file)
		if(rtarray):
			return np.array(registers)

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True, upload_on_chip = True, rtarray = False):
		registers = CSV.CsvToArray(file)[:,1:4]
		if(upload_on_chip):
			for tmp in registers:
				if(tmp[0] == -1):
					if display: print 'writing'
					if (not 'Fuse' in tmp[1]):
						self.I2C.peri_write(tmp[1], tmp[2])
						r = self.I2C.peri_read(tmp[1])
						if(r != tmp[2]):
							print 'X>  \t Configuration ERROR Periphery  ' + str(tmp[1]) + '  ' + str(tmp[2]) + '  ' + str(r)
				elif(tmp[0]>=1 and tmp[0]<=120):
					if display: print 'writing'
					if ((not 'ReadCounter' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
						self.I2C.strip_write(tmp[1], tmp[0], tmp[2])
						r = self.I2C.strip_read(tmp[1], tmp[0])
						if(r != tmp[2]):
							print 'X>  \t Configuration ERROR Strip ' + str(tmp[0])
				if display:
					print [tmp[0], tmp[1], tmp[2], r]
			print "->  \tConfiguration Loaded from file"
		if(rtarray):
			return registers

	def compare_configuration(self, conf, conf_ref, display = True):
		error = [0]*121
		#checklist = np.unique(conf[:,0])
		for i in range(len(conf)):
			if(int(conf[i,0]) == -1):
				if(int(conf[i,2]) != int(conf_ref[i,2])):
					error[0] += 1
					if(display):
						print("-X  \tConfiguration error. Reg: " + str(conf[i,1]) + " Expected: " + str(int(conf_ref[i,2])) + "Found: " + str(int(conf[i,2])))
			elif(int(conf[i,0]) > 0):
				if(int(conf[i,2]) != int(conf_ref[i,2])):
					if(display):
						print("-X  \tConfiguration error. Reg: " + str(conf[i,1]) + " Strip: " + str(int(conf[i,0])) + " Expected: " + str(int(conf_ref[i,2])) + " Found: " + str(int(conf[i,2])) )
					error[int(conf[i,0])] += 1
		return error


	def set_output_mux(self, testline = 'highimpedence'):
		#utils.activate_I2C_chip()
		ctrl = self.analog_mux_map[testline]
		self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
		self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
		self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
		self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
		r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
		r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			print "Error. Failed to set the MUX"
			return False
		else:
			return True


	def init_slvs(self, current = 0b111):
		self.I2C.peri_write('SLVS_pad_current', current)
		r = self.I2C.peri_read('SLVS_pad_current')
		if (self.I2C.peri_read("SLVS_pad_current") != (current & 0b111) ):
			utils.print_error("->\tI2C did not work properly")
			#exit(1)


	def set_lateral_lines_alignament(self):
		self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0)
		self.I2C.peri_write( "CalPulse_duration", 15)
		self.I2C.strip_write("ENFLAGS",   7, 0b01001)
		self.I2C.strip_write("ENFLAGS", 120, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L",   7, 0xff)
		self.I2C.strip_write("DigCalibPattern_L", 120, 0xff)


	def reset_pattern_injection(self):
		self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		self.I2C.strip_write("DigCalibPattern_L", 0, 0)
		self.I2C.strip_write("DigCalibPattern_H", 0, 0)


	def __do_phase_tuning(self):
		cnt = 0; done = True
		#print self.fc7.read("stat_phy_phase_tuning_done")
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		#print self.fc7.read("stat_phy_phase_tuning_done")
		send_test(15)
		#print self.fc7.read("stat_phy_phase_tuning_done")
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0 and cnt < 5):
			sleep(0.1)
			print "Waiting for the phase tuning"
			cnt += 1
		if cnt>4:
			done = False
		return  done


	def phase_tuning(self):
		self.activate_readout_shift()
		if(self.fc7.invert):
			self.set_shift_pattern_all(0b01111111) #128 #0b01111111
		else:
			self.set_shift_pattern_all(128) #128 #0b01111111
		time.sleep(0.01)
		self.set_lateral_lines_alignament()
		time.sleep(0.01)
		#rt = self.__do_phase_tuning()
		rt = self.align_out()
		self.I2C.peri_write('OutPattern7/FIFOconfig', 7)
		self.reset_pattern_injection()
		self.activate_readout_normal()
		return rt

	def align_out(self):
		fc7.write("ctrl_phy_phase_tune_again", 1)
		timeout_max = 3
		timeout = 0
		sleep(0.1)
		while(fc7.read("stat_phy_phase_tuning_done") == 0):
			sleep(0.1)
			utils.print_warning("->\tWaiting for the phase tuning")
			timeout+=1
			if (timeout == timeout_max):
				return False
		return True

	def set_t1_sampling_edge(self, edge):
		if edge == "rising" or edge == "positive":
			self.I2C.peri_write('EdgeSel_T1', 1)
			utils.print_info("->  \tT1 sampling edge set to rising")
		elif edge == "falling" or edge == "negative":
			self.I2C.peri_write('EdgeSel_T1', 0)
			utils.print_info("->  \tT1 sampling edge set to falling")
		else:
			print("Error! The edge name is wrong")


	def activate_readout_normal(self, mipadapterdisable = 0):
		val = 0b100 if (mipadapterdisable) else 0b000
		self.I2C.peri_write('ReadoutMode',val)
		if (self.I2C.peri_read("ReadoutMode") != val):
			print "Error! I2C did not work properly"
			exit(1)


	def activate_readout_async(self, ssa_first_counter_delay = 8, correction = 0):
		self.I2C.peri_write('ReadoutMode',0b01)
		# write to the I2C
		self.I2C.peri_write("AsyncRead_StartDel_MSB", ((ssa_first_counter_delay >> 8) & 0x01))
		self.I2C.peri_write("AsyncRead_StartDel_LSB", (ssa_first_counter_delay & 0xff))
		# check the value
		if (self.I2C.peri_read("AsyncRead_StartDel_LSB") != ssa_first_counter_delay & 0xff):
			print "Error! I2C did not work properly"
			error(1)
		# ssa set delay of the counters
		fwdel = ssa_first_counter_delay + 24 + correction
		if(fwdel >= 255):
			print '->  \tThe counters delay value selected is not supposrted by the firmware [> 255]'
		self.fc7.write("cnfg_phy_slvs_ssa_first_counter_del", fwdel & 0xff)


	def activate_readout_shift(self):
		self.I2C.peri_write('ReadoutMode',0b10)


	def set_shift_pattern_all(self, pattern):
		self.set_shift_pattern(pattern,pattern,pattern,pattern,pattern,pattern,pattern,pattern)


	def set_shift_pattern(self, line0, line1, line2, line3, line4, line5, line6, line7):
		self.I2C.peri_write('OutPattern0',line0)
		self.I2C.peri_write('OutPattern1',line1)
		self.I2C.peri_write('OutPattern2',line2)
		self.I2C.peri_write('OutPattern3',line3)
		self.I2C.peri_write('OutPattern4',line4)
		self.I2C.peri_write('OutPattern5',line5)
		self.I2C.peri_write('OutPattern6',line6)
		self.I2C.peri_write('OutPattern7/FIFOconfig',line7)


	def set_async_delay(self, value):
		msb = (value & 0xFF00) >> 8
		lsb = (value & 0x00FF) >> 0
		self.I2C.peri_write('AsyncRead_StartDel_MSB', msb)
		self.I2C.peri_write('AsyncRead_StartDel_LSB', lsb)


	def set_threshold(self, value):
		self.I2C.peri_write("Bias_THDAC", value)
		sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDAC")
		if(test_read != value):
			print "Was writing: ", value, ", got: ", test_read
			print "Error. Failed to set the threshold"
			error(1)


	def set_threshold_H(self, value):
		self.I2C.peri_write("Bias_THDACHIGH", value)
		sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDACHIGH")
		if(test_read != value):
			print "Was writing: ", value, ", got: ", test_read
			print "Error. Failed to set the threshold"
			error(1)


	def init_default_thresholds(self):
		# init thersholds
		self.I2C.peri_write("Bias_THDAC", 35)
		self.I2C.peri_write("Bias_THDACHIGH", 120)


	def init_trimming(self, th_trimming = 15, gain_trimming = 15):
		self.I2C.strip_write('THTRIMMING', 0, th_trimming)
		self.I2C.strip_write('GAINTRIMMING', 0, gain_trimming)
		repT = [0xff]*120
		repG = [0xff]*120
		error = False
		for i in range(1,121):
			repT[i-1] = self.I2C.strip_read('THTRIMMING', i)
			repG[i-1] = self.I2C.strip_read('GAINTRIMMING', i)
		for i in repT:
			if (i != th_trimming): error = True
		for i in repG:
			if (i != gain_trimming): error = True
		if error:
			print "Error. Failed to set the trimming"


	def set_cal_pulse(self, amplitude = 255, duration = 5, delay = 'keep'):
		self.I2C.peri_write("Bias_CALDAC", amplitude) # init cal pulse itself
		self.I2C.peri_write("CalPulse_duration", duration) # set cal pulse duration
		self.set_cal_pulse_delay(delay) # init the cal pulse digital delay line

	def set_cal_pulse_amplitude(self, amplitude = 255):
		self.I2C.peri_write("Bias_CALDAC", amplitude)

	def set_cal_pulse_duration(self, duration = 5):
		self.I2C.peri_write("CalPulse_duration", duration)

	def set_cal_pulse_delay(self, delay):
		if(isinstance(delay, str)):
			if(delay == 'disable' or delay == 'off'):
				self.I2C.peri_write("Bias_DL_en", 0)
				self.bias_dl_enable = False
			elif(delay == 'enable'or delay == 'on'):
				self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			elif(delay == 'keep'): pass
			else: exit(1)
		elif(isinstance(delay, int)):
			if (not self.bias_dl_enable):
				self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			self.I2C.peri_write("Bias_DL_ctrl", delay)
		return True


	def set_sampling_deskewing_coarse(self, value):
		word = value & 0b111
		self.I2C.peri_write("PhaseShiftClock", word)
		r = self.I2C.peri_read("PhaseShiftClock")
		if(r != word): return False
		else: return True


	def set_sampling_deskewing_fine(self, value, enable = True, bypass = False):
		word = (
			((value & 0b1111) << 0) |
			((self.dll_chargepump & 0b11) << 4) |
			((bypass & 0b1) << 6) |
			((enable & 0b1) << 7)
		)
		self.I2C.peri_write("ClockDeskewing", word)
		r = self.I2C.peri_read("ClockDeskewing")
		if(r != word): return False
		else: return True


	def set_sampling_deskewing_chargepump(self, val):
		self.dll_chargepump = val & 0b11
		r = self.I2C.peri_read("ClockDeskewing")
		word = (r & 0b11001111) | (self.dll_chargepump << 4)
		self.I2C.peri_write("ClockDeskewing", word)
		r = self.I2C.peri_read("ClockDeskewing")
		if(r != word): return False
		else: return True


	def set_lateral_data_phase(self, left, right):
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_1", right)
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_2", left)


	def set_lateral_data(self, left, right):
		self.fc7.write("cnfg_phy_SSA_gen_right_lateral_data_format", right)
		self.fc7.write("cnfg_phy_SSA_gen_left_lateral_data_format", left)

	def read_fuses(self, pulse = True, display = True):
		if(pulse):
			self.I2C.peri_write('Fuse_Mode', 0b00001111)
			self.I2C.peri_write('Fuse_Mode', 0b00000000)
		r0 = self.I2C.peri_read('Fuse_Value_b0')
		r1 = self.I2C.peri_read('Fuse_Value_b1')
		r2 = self.I2C.peri_read('Fuse_Value_b2')
		r3 = self.I2C.peri_read('Fuse_Value_b3')
		if display:
			print( "{0:02x}-{1:02x}-{2:02x}-{3:02x}".format(r3, r2, r1, r0) )
		else:
			r = (r3<<24) | (r2<<16) | (r1<<8) | (r0<<0)
			return r

	def write_fuses(self, val = 0, pulse = True, display = False, confirm = False):
		d0 = (val >>  0) & 0xFF
		d1 = (val >>  8) & 0xFF
		d2 = (val >> 16) & 0xFF
		d3 = (val >> 24) & 0xFF
		self.I2C.peri_write('Fuse_Prog_b0', d0)
		self.I2C.peri_write('Fuse_Prog_b1', d1)
		self.I2C.peri_write('Fuse_Prog_b2', d2)
		self.I2C.peri_write('Fuse_Prog_b3', d3)
		r0 = self.I2C.peri_read('Fuse_Prog_b0')
		r1 = self.I2C.peri_read('Fuse_Prog_b1')
		r2 = self.I2C.peri_read('Fuse_Prog_b2')
		r3 = self.I2C.peri_read('Fuse_Prog_b3')
		if (((r3<<24) | (r2<<16) | (r1<<8) | (r0<<0) ) != val):
			print("\n->  \tError in setting the e-fuses write buffer")
			return -1
		if(pulse):
			if confirm:  rp = 'Y'
			else:  rp = raw_input("\n->  \tAre you sure you want to write the e-fuses? [Y|n] : ")
			if (rp == 'Y'):
				time.sleep(0.1); self.I2C.peri_write('Fuse_Mode', 0b11110000)
				time.sleep(0.1); self.fc7.send_test(15)
				time.sleep(0.1); self.I2C.peri_write('Fuse_Mode', 0b00000000)
		r = self.read_fuses(pulse = True, display = display)
		if(r != val):
			print('->  \tE-Fuses write error: ')
			print('    \t    Written:...{0:032b}'.format(val))
			print('    \t    Read:......{0:032b}'.format(r))
			return False
		else:
			return True

	def read_seu_counter(self):
		rp = self.I2C.peri_read('SEU_Counter')
		return rp

	def set_l1_latency(self, latency):
		time.sleep(0.001)
		self.I2C.peri_write('L1-Latency_MSB', (latency & 0xff00) >> 8)
		time.sleep(0.001)
		self.I2C.peri_write('L1-Latency_LSB', (latency & 0x00ff) >> 0)
		time.sleep(0.001)








# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
