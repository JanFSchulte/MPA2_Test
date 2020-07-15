import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
from random import randint

from utilities.tbsettings import *
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *



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
		print('->  Sent Re-Sync command')
		sleep(0.001)

	def reset_and_set_sampling_edge(self, display=True):
		rp = self.pwr.reset(display=display)
		self.set_t1_sampling_edge("negative")
		return rp

	def reset(self, display=True):
		rp = self.pwr.reset(display=display)
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
		#print("->  Configuration Saved on file:   " + str(file))
		if display:
			for i in registers:
				print(i)
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
					if display: print('writing')
					if (not 'Fuse' in tmp[1]):
						self.I2C.peri_write(tmp[1], tmp[2])
						r = self.I2C.peri_read(tmp[1])
						if(r != tmp[2]):
							print('X>   Configuration ERROR Periphery  ' + str(tmp[1]) + '  ' + str(tmp[2]) + '  ' + str(r))
				elif(tmp[0]>=1 and tmp[0]<=120):
					if display: print('writing')
					if ((not 'ReadCounter' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
						self.I2C.strip_write(tmp[1], tmp[0], tmp[2])
						r = self.I2C.strip_read(tmp[1], tmp[0])
						if(r != tmp[2]):
							print('X>   Configuration ERROR Strip ' + str(tmp[0]))
				if display:
					print([tmp[0], tmp[1], tmp[2], r])
			print("->  Configuration Loaded from file")
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
						print("-X  Configuration error. Reg: " + str(conf[i,1]) + " Expected: " + str(int(conf_ref[i,2])) + "Found: " + str(int(conf[i,2])))
			elif(int(conf[i,0]) > 0):
				if(int(conf[i,2]) != int(conf_ref[i,2])):
					if(display):
						print("-X  Configuration error. Reg: " + str(conf[i,1]) + " Strip: " + str(int(conf[i,0])) + " Expected: " + str(int(conf_ref[i,2])) + " Found: " + str(int(conf[i,2])) )
					error[int(conf[i,0])] += 1
		return error

	def set_output_mux(self, testline = 'highimpedence'):
		if(tbconfig.VERSION['SSA'] >= 2):
			ctrl = self.analog_mux_map[testline]
			r =    self.I2C.peri_write( register="ADC_trimming",    field='TestPad_Enable',        data=0b1)
			r = r| self.I2C.peri_write( register="adr_ADC_control", field='ADC_control_input_sel', data=ctrl)
			r = r| self.I2C.peri_read(  register="adr_ADC_control", field='ADC_control_input_sel')
		else:
			#utils.activate_I2C_chip()
			ctrl = self.analog_mux_map[testline]
			self.I2C.peri_write('Bias_TEST_LSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_MSB', 0) # to avoid short
			self.I2C.peri_write('Bias_TEST_LSB', (ctrl >> 0) & 0xff)
			self.I2C.peri_write('Bias_TEST_MSB', (ctrl >> 8) & 0xff)
			r = ((self.I2C.peri_read('Bias_TEST_LSB') & 0xff))
			r = ((self.I2C.peri_read('Bias_TEST_MSB') & 0xff) << 8) | r
		if(r != ctrl):
			print("Error. Failed to set the MUX")
			return False
		else:
			return True

	def adc_measeure(self, testline = 'highimpedence', fast=True):
		input_sel = self.analog_mux_map[testline]
		if(fast):
			r =    self.I2C.peri_write( register="ADC_trimming", field=False, data=(0b11100000 | (input_sel & 0b00011111)) )
			r = r| self.I2C.peri_write( register="ADC_trimming", field=False, data=(0b11000000 | (input_sel & 0b00011111)) )
		else:
			r =    self.I2C.peri_write( register="ADC_trimming", field=False                     , data=0x00)
			r = r| self.I2C.peri_write( register="ADC_trimming", field='ADC_control_reset'       , data=0b1)
			r = r| self.I2C.peri_write( register="ADC_trimming", field='ADC_control_reset'       , data=0b0)
			r = r| self.I2C.peri_write( register="ADC_trimming", field='ADC_control_input_sel'   , data=input_sel)
			r = r| self.I2C.peri_write( register="ADC_trimming", field='ADC_control_enable_start', data=0b11)
		if(not r):
			print("Error. Failed to use the ADC")
			return False
		msb = self.I2C.peri_read( register="ADC_out_H", field=False )
		lsb = self.I2C.peri_read( register="ADC_out_L", field=False )
		if((msb==None) or (lsb==None)):
			res = False
		else:
			res = ((msb<<8) | lsb)
		return res

	def init_slvs(self, current = 0b111):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(  register="SLVS_pad_current_Lateral",  field='SLVS_pad_current_Left',   data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Lateral",  field='SLVS_pad_current_Right',  data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_0_1", field='SLVS_pad_current_Stub_0', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_0_1", field='SLVS_pad_current_Stub_1', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_2_3", field='SLVS_pad_current_Stub_2', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_2_3", field='SLVS_pad_current_Stub_3', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_4_5", field='SLVS_pad_current_Stub_4', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_4_5", field='SLVS_pad_current_Stub_5', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_6_7", field='SLVS_pad_current_Stub_6', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Stub_6_7", field='SLVS_pad_current_Stub_7', data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_L1",       field='SLVS_pad_current_L1',     data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Clk_T1",   field='SLVS_pad_current_Clk',    data=current)
			self.I2C.peri_write(  register="SLVS_pad_current_Clk_T1",   field='SLVS_pad_current_T1',     data=current)
		else:
			self.I2C.peri_write('SLVS_pad_current', current)
			r = self.I2C.peri_read('SLVS_pad_current')
			if (self.I2C.peri_read("SLVS_pad_current") != (current & 0b111) ):
				utils.print_error("->  I2C did not work properly")

	def set_lateral_lines_alignament(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write( register="StripControl1",     field='ENFLAGS', strip='all', data=0b00001001)
			self.I2C.strip_write( register="DigCalibPattern_L", field=False,     strip='all', data=0)
			self.I2C.strip_write( register="DigCalibPattern_H", field=False,     strip='all', data=0)
			self.I2C.peri_write(  register="control_2",         field='CalPulse_duration',    data=15)
			self.I2C.strip_write( register="StripControl1",     field='ENFLAGS', strip=7,     data=0b01001)
			self.I2C.strip_write( register="StripControl1",     field='ENFLAGS', strip=120,   data=0b01001)
			self.I2C.strip_write( register="DigCalibPattern_L", field=False,     strip=7,     data=0xff)
			self.I2C.strip_write( register="DigCalibPattern_L", field=False,     strip=120,   data=0xff)
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			self.I2C.peri_write( "CalPulse_duration", 15)
			self.I2C.strip_write("ENFLAGS",   7, 0b01001)
			self.I2C.strip_write("ENFLAGS", 120, 0b01001)
			self.I2C.strip_write("DigCalibPattern_L",   7, 0xff)
			self.I2C.strip_write("DigCalibPattern_L", 120, 0xff)


	def reset_pattern_injection(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write("StripControl1", 'all', 0b01001)
			self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip='all', data=0)
			self.I2C.strip_write( register="DigCalibPattern_H", field=False, strip='all', data=0)
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)

	def __do_phase_tuning(self):
		cnt = 0; done = True
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		send_test(15)
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0 and cnt < 5):
			sleep(0.1)
			print("Waiting for the phase tuning")
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
			utils.print_warning("->  Waiting for the phase tuning")
			timeout+=1
			if (timeout == timeout_max):
				return False
		return True

	def set_t1_sampling_edge(self, edge):
		V = tbconfig.VERSION['SSA']
		if edge == "rising" or edge == "positive":
			if(V>=2): self.I2C.peri_write(register="control_1", field='EdgeSel_T1', data=1)
			else:     self.I2C.peri_write('EdgeSel_T1', 1)
			utils.print_info("->  T1 sampling edge set to rising")
		elif edge == "falling" or edge == "negative":
			if(V>=2): self.I2C.peri_write(register="control_1", field='EdgeSel_T1', data=0)
			else:     self.I2C.peri_write('EdgeSel_T1', 0)
			utils.print_info("->  T1 sampling edge set to falling")
		else:
			print("Error! The edge name is wrong")


	def activate_readout_normal(self, mipadapterdisable = 0):
		val = 0b100 if (mipadapterdisable) else 0b000
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=gain_trimming)
			rep = self.I2C.peri_read( register="control_1", field='ReadoutMode')
		else:
			self.I2C.peri_write('ReadoutMode',val)
			rep = self.I2C.peri_read("ReadoutMode")
		if(rep != val):
			print("Error! I2C did not work properly in activate_readout_normal")
			#exit(1)


	def activate_readout_async(self, ssa_first_counter_delay = 8, correction = 0):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=0b001)
		else:
			self.I2C.peri_write('ReadoutMode',0b01)

		self.I2C.peri_write("AsyncRead_StartDel_MSB", ((ssa_first_counter_delay >> 8) & 0x01))
		self.I2C.peri_write("AsyncRead_StartDel_LSB", (ssa_first_counter_delay & 0xff))
		if (self.I2C.peri_read("AsyncRead_StartDel_LSB") != ssa_first_counter_delay & 0xff):
			print("Error! I2C did not work properly")
		# ssa set delay of the counters
		fwdel = ssa_first_counter_delay + 24 + correction
		if(fwdel >= 255):
			print('->  The counters delay value selected is not supposrted by the firmware [> 255]')
		self.fc7.write("cnfg_phy_slvs_ssa_first_counter_del", fwdel & 0xff)


	def activate_readout_shift(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=0b010)
		else:
			self.I2C.peri_write('ReadoutMode',0b10)

	def set_shift_pattern_all(self, pattern):
		self.set_shift_pattern( ST = [pattern]*8, L1 = pattern, Left = pattern, Right = pattern)


	def set_shift_pattern(self, ST=[0xaa]*8, L1=0x80, Left=0x80, Right=0x80):
		if(tbconfig.VERSION['SSA'] >= 2):
			R_ST = [-1]*7
			self.I2C.peri_write(register="Shift_pattern_st_0",      field=False, data = ST[0])
			self.I2C.peri_write(register="Shift_pattern_st_1",      field=False, data = ST[1])
			self.I2C.peri_write(register="Shift_pattern_st_2",      field=False, data = ST[2])
			self.I2C.peri_write(register="Shift_pattern_st_3",      field=False, data = ST[3])
			self.I2C.peri_write(register="Shift_pattern_st_4_st_5", field=False, data = ST[4])
			self.I2C.peri_write(register="Shift_pattern_st_6_st_7", field=False, data = ST[6])
			self.I2C.peri_write(register="Shift_pattern_Left",      field=False, data = Left)
			self.I2C.peri_write(register="Shift_pattern_Right",     field=False, data = Right)
			self.I2C.peri_write(register="Shift_pattern_L1",        field=False, data = L1)
			R_ST[0] = self.I2C.peri_read(register="Shift_pattern_st_0",      field=False )
			R_ST[1] = self.I2C.peri_read(register="Shift_pattern_st_1",      field=False )
			R_ST[2] = self.I2C.peri_read(register="Shift_pattern_st_2",      field=False )
			R_ST[3] = self.I2C.peri_read(register="Shift_pattern_st_3",      field=False )
			R_ST[4] = self.I2C.peri_read(register="Shift_pattern_st_4_st_5", field=False )
			R_ST[6] = self.I2C.peri_read(register="Shift_pattern_st_6_st_7", field=False )
			R_Left  = self.I2C.peri_read(register="Shift_pattern_Left",      field=False )
			R_Right = self.I2C.peri_read(register="Shift_pattern_Right",     field=False )
			R_L1    = self.I2C.peri_read(register="Shift_pattern_L1",        field=False )
			print(ST)
			if(R_ST[0] != ST[0] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[0] ))
			if(R_ST[1] != ST[1] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[1] ))
			if(R_ST[2] != ST[2] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[2] ))
			if(R_ST[3] != ST[3] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[3] ))
			if(R_ST[4] != ST[4] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[4] ))
			if(R_ST[6] != ST[6] ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_ST[6] ))
			if(R_Left  != Left  ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_Left  ))
			if(R_Right != Right ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_Right ))
			if(R_L1    != L1    ): utils.print_error('->  Shift pattern set I2C error: {:8b}'.format(R_L1    ))

		else:
			self.I2C.peri_write('OutPattern0', ST[0])
			self.I2C.peri_write('OutPattern1', ST[1])
			self.I2C.peri_write('OutPattern2', ST[2])
			self.I2C.peri_write('OutPattern3', ST[3])
			self.I2C.peri_write('OutPattern4', ST[4])
			self.I2C.peri_write('OutPattern5', ST[5])
			self.I2C.peri_write('OutPattern6', ST[6])
			self.I2C.peri_write('OutPattern7/FIFOconfig',ST[7])

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
			print("Was writing: ", value, ", got: ", test_read)
			print("Error. Failed to set the threshold")
			error(1)


	def set_threshold_H(self, value):
		self.I2C.peri_write("Bias_THDACHIGH", value)
		sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDACHIGH")
		if(test_read != value):
			print("Was writing: ", value, ", got: ", test_read)
			print("Error. Failed to set the threshold")
			error(1)


	def init_default_thresholds(self):
		# init thersholds
		self.I2C.peri_write("Bias_THDAC", 35)
		self.I2C.peri_write("Bias_THDACHIGH", 120)


	def init_trimming(self, th_trimming = 15, gain_trimming = 15):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write( register="ThresholdTrimming", field='ThresholdTrimming', strip='all', data=th_trimming)
			self.I2C.strip_write( register="StripControl2",     field='GainTrimming',      strip='all', data=gain_trimming)
		else:
			self.I2C.strip_write('THTRIMMING', 0, th_trimming)
			self.I2C.strip_write('GAINTRIMMING', 0, gain_trimming)
		repT = [0xff]*120
		repG = [0xff]*120
		error = False
		for i in range(1,121):
			if(tbconfig.VERSION['SSA'] >= 2):
				repT[i-1] = self.I2C.strip_read( register="ThresholdTrimming", field='ThresholdTrimming', strip=i, data=th_trimming)
				repG[i-1] = self.I2C.strip_read( register="StripControl2",     field='GainTrimming',      strip=i, data=gain_trimming)
			else:
				repT[i-1] = self.I2C.strip_read('THTRIMMING', i)
				repG[i-1] = self.I2C.strip_read('GAINTRIMMING', i)
		for i in repT:
			if (i != th_trimming): error = True
		for i in repG:
			if (i != gain_trimming): error = True
		if error:
			print("Error. Failed to set the trimming")


	def set_cal_pulse(self, amplitude = 255, duration = 5, delay = 'keep'):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write("Bias_CALDAC", amplitude)
			self.I2C.peri_write(register="control_2", field='CalPulse_duration', data=15)
			self.set_cal_pulse_delay(delay)
		else:
			self.I2C.peri_write("Bias_CALDAC", amplitude) # init cal pulse itself
			self.I2C.peri_write("CalPulse_duration", duration) # set cal pulse duration
			self.set_cal_pulse_delay(delay) # init the cal pulse digital delay line

	def set_cal_pulse_amplitude(self, amplitude = 255):
		self.I2C.peri_write("Bias_CALDAC", amplitude)

	def set_cal_pulse_duration(self, duration = 5):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_2", field='CalPulse_duration', data=duration)
		else:
			self.I2C.peri_write("CalPulse_duration", duration)

	def set_cal_pulse_delay(self, delay):
		V = tbconfig.VERSION['SSA']
		if(isinstance(delay, str)):
			if(delay == 'disable' or delay == 'off'):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='Bias_DL_en',  data=0)
				else:     self.I2C.peri_write("Bias_DL_en", 0)
				self.bias_dl_enable = False
			elif(delay == 'enable'or delay == 'on'):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='Bias_DL_en',  data=1)
				else:     self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			elif(delay == 'keep'):
				pass
			else:
				exit(1)
		elif(isinstance(delay, int)):
			if (not self.bias_dl_enable):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='Bias_DL_en',  data=1)
				else:     self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			if(V>=2): self.I2C.peri_write(register='Delay_line', field='DL_ctrl',  data=delay)
			else:     self.I2C.peri_write("Bias_DL_ctrl", delay)
		return True


	def set_sampling_deskewing_coarse(self, value):
		word = value & 0b111
		if((tbconfig.VERSION['SSA'] >= 2) and onchip_mask):
			r = self.I2C.peri_write(register="ClockDeskewing_coarse", field=False,  data=word)
			r = self.I2C.peri_read( register="ClockDeskewing_coarse", field=False)
		else:
			self.I2C.peri_write("PhaseShiftClock", word)
			r = self.I2C.peri_read("PhaseShiftClock")
		if(r != word): return False
		else: return True


	def set_sampling_deskewing_fine(self, value, enable = True, bypass = False, onchip_mask=False):
		if((tbconfig.VERSION['SSA'] >= 2) and onchip_mask):
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_value',      data=value)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_chargepump', data=self.dll_chargepump)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_bypass',     data=bypass)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_Enable',     data=enable)
		else:
			word = (
				((value & 0b1111) << 0) |
				((self.dll_chargepump & 0b11) << 4) |
				((bypass & 0b1) << 6) |
				((enable & 0b1) << 7)
			)
			if((tbconfig.VERSION['SSA'] >= 2) and onchip_mask):
				self.I2C.peri_write(register="ClockDeskewing_fine", field = False, data = word)
				r = self.I2C.peri_read(register="ClockDeskewing_fine", field = False)
			else:
				self.I2C.peri_write("ClockDeskewing", word)
				r = self.I2C.peri_read("ClockDeskewing")
			if(r != word): return False
			else: return True


	def set_sampling_deskewing_chargepump(self, val):
		self.dll_chargepump = val & 0b11

		if((tbconfig.VERSION['SSA'] >= 2) and onchip_mask):
			r = self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_chargepump', data=self.dll_chargepump)
			r = self.I2C.peri_read( register="ClockDeskewing_fine", field='DLL_chargepump')
			return (r == val)
		else:
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
			print("\n->  Error in setting the e-fuses write buffer")
			return -1
		if(pulse):
			if confirm:  rp = 'Y'
			else:  rp = raw_input("\n->  Are you sure you want to write the e-fuses? [Y|n] : ")
			if (rp == 'Y'):
				time.sleep(0.1); self.I2C.peri_write('Fuse_Mode', 0b11110000)
				time.sleep(0.1); self.fc7.send_test(15)
				time.sleep(0.1); self.I2C.peri_write('Fuse_Mode', 0b00000000)
		r = self.read_fuses(pulse = True, display = display)
		if(r != val):
			print('->  E-Fuses write error: ')
			print('        Written:...{0:032b}'.format(val))
			print('        Read:......{0:032b}'.format(r))
			return False
		else:
			return True

	def read_seu_counter(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			rp = { 'A':{'peri':[0]*2, 'strip':[0]*8}, 'S':{'peri':[0]*2, 'strip':[0]*8} }
			rp['S']['peri'][0]  = self.I2C.peri_read(register = 'Sync_SEUcnt_blk0')
			rp['S']['peri'][1]  = self.I2C.peri_read(register = 'Sync_SEUcnt_blk1')
			rp['A']['peri'][0]  = self.I2C.peri_read(register = 'aseSync_SEUcnt_blk0')
			rp['A']['peri'][1]  = self.I2C.peri_read(register = 'aseSync_SEUcnt_blk1')
			for i in range(8):
				rp['S']['strip'][i] = 0 # TODO
				rp['A']['strip'][i] = 0 # TODO
		else:
			rp = self.I2C.peri_read('SEU_Counter')
		return rp

	def set_l1_latency(self, latency):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_3", field='L1_Latency_lsb', data = ((latency & 0x00ff) >> 0) )
			self.I2C.peri_write(register="control_1", field='L1_Latency_msb', data = ((latency & 0x0100) >> 8) )
		else:
			time.sleep(0.001)
			self.I2C.peri_write('L1_Latency_msb', (latency & 0xff00) >> 8)
			time.sleep(0.001)
			self.I2C.peri_write('L1_Latency_lsb', (latency & 0x00ff) >> 0)
			time.sleep(0.001)


	def try_i2c(self, repeat=5):
		r=[]; d=[]; w=[];
		Result = True
		utils.print_log_color_legend_i2c('\n\n')
		if(tbconfig.VERSION['SSA'] >= 2):
			reglist = ['Bias_TEST_msb','Bias_TEST_lsb', 'unused_register', 'Shift_pattern_st_0', 'Shift_pattern_st_1', 'Shift_pattern_st_2']
		else:
			reglist = ['OutPattern0','OutPattern1', 'OutPattern2', 'OutPattern3', 'OutPattern4', 'OutPattern5']

		for iter in range(repeat):
			for reg in reglist:
				data = randint(1,255)
				d.append( data )
				w.append( self.I2C.peri_write(register = reg, field = False, data = data))
				time.sleep(0.01)
			for reg in reglist:
				r.append( self.I2C.peri_read( register = reg, field = False))
				time.sleep(0.01)

		for i in range(len(d)):
			if(r[i] == 'Null'):
				utils.print_error('->  I2C Register check null  [{:8b}] - [NoReply]'.format(d[i]))
				Result = False
			elif( r[i] != d[i] ):
				utils.print_warning('->  I2C Register check error [{:8b}] - [{:8b}]'.format(d[i], r[i]) )
				Result = False
			else:
				utils.print_good('->  I2C Register check match [{:8b}] - [{:8b}]'.format(d[i], r[i]) )

		return Result

# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
