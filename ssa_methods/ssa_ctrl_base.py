import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import copy
from random import randint

from utilities.tbsettings import *
#from d19cScripts.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from d19cScripts.phase_tuning_control import *



class ssa_ctrl_base:

	def __init__(self, index, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.ssa_strip_reg_map = ssa_strip_reg_map;
		self.analog_mux_map = analog_mux_map;
		self.ssa_peri_reg_map = ssa_peri_reg_map;
		self.I2C = I2C;
		self.fc7 = FC7;
		self.pwr = pwr
		self.dll_chargepump = 0b00;
		self.bias_dl_enable = False
		self.seu_check_time = -1
		self.testpad_is_enable = -1
		self.seu_cntr = { 'A':{'peri':[0]*2, 'strip':[0]*15, 'all':0}, 'S':{'peri':[0]*2, 'strip':[0]*15, 'all':0} }
		self.index = index
		self.r = []

	#####################################################################
	def setup_readout_chip_id(self, display=True):
		self.fc7.set_active_readout_chip(self.index, display=display)

	#####################################################################
	def resync(self, display=True):
		self.fc7.SendCommand_CTRL("fast_fast_reset");
		if(display):
			utils.print_log('->  Sent Re-Sync command')
		#sleep(0.001)

	#####################################################################
	def reset_and_set_sampling_edge(self, display=True):
		rp = self.pwr.reset(display=display)
		self.set_t1_sampling_edge("negative")
		return rp

	#####################################################################
	def reset(self, display=True):
		rp = self.pwr.reset(display=display)
		return rp

	#####################################################################
	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True, rtarray = False, strip_list = 'all', notes = [['note','','']]):
		if(strip_list=='all'):
			strip_list = range(1,121)
		registers = []; rm = []
		peri_reg_map  = self.ssa_peri_reg_map.copy()
		for i in peri_reg_map:
			if(tbconfig.VERSION['SSA'] >= 2):
				if('W' not in peri_reg_map[i]['permissions']):
					rm.append(i)
			else:
				if('Fuse' in i): rm.append(i)
				if('SEU' in i): rm.append(i)
		for k in rm:
			peri_reg_map.pop(k, None)
		strip_reg_map = self.ssa_strip_reg_map.copy()
		for i in strip_reg_map:
			if(tbconfig.VERSION['SSA'] >= 2):
				if('W' not in strip_reg_map[i]['permissions']):
					rm.append(i)
			else:
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
		for n in notes:
			registers.insert(0, n)
		if display:
			for i in registers:
				utils.print_log(i)
		dir = file[:file.rindex(os.path.sep)]
		if not os.path.exists(dir): os.makedirs(dir)

		CSV.ArrayToCSV(registers, file)
		if(rtarray):
			return np.array(registers[1:])

	#####################################################################
	def load_configuration(self, file = '../SSA_Results/Configuration.csv', strips = 'all', peri=True, display=True, upload_on_chip = True, rtarray = False):
		if(strips=='all'): strips = range(1,121)
		registers = CSV.CsvToArray(file)[1:,1:4]
		if(upload_on_chip):
			for tmp in registers:
				if((int(tmp[0]) == -1) and peri):
					if ((not 'Fuse' in tmp[1]) and (not 'mask' in tmp[1])):
						self.I2C.peri_write(tmp[1], int(tmp[2]))
						if display: utils.print_log([tmp[0], tmp[1], int(tmp[2])])
					else:
						if display: utils.print_log(str([tmp[0], tmp[1], int(tmp[2])]) + ' -> skipped')
				elif((int(tmp[0])>=1) and (int(tmp[0])<=120) and (int(tmp[0]) in strips) ):
					if ((not 'ReadCounter' in tmp[1]) and (not 'mask' in tmp[1]) and ((not 'Fuse' in tmp[1]))):
						self.I2C.strip_write(tmp[1], int(tmp[0]), int(tmp[2]))
						if display: utils.print_log([tmp[0], tmp[1], int(tmp[2])])
					else:
						if display: utils.print_log(str([tmp[0], tmp[1], int(tmp[2])]) + ' -> skipped')

			utils.print_log("->  Configuration Loaded from file")
		if(rtarray):
			return registers

	def load_basic_calib_configuration(self, strips = 'all', peri=True, display=True):
		self.set_all_config_masks(0xff,0xff,0xff)
		conf_ref = self.load_configuration(
			rtarray = True, display=display, upload_on_chip = True, strips = strips, peri=peri,
			file = 'ssa_methods/Configuration/ssa_configuration_base_calib_v{:d}.csv'.format(tbconfig.VERSION['SSA']))
		self.set_all_config_masks(0x00,0x00,0x00)
		return conf_ref


	#####################################################################
	def compare_configuration(self, conf, conf_ref, display = True):
		error = [0]*121
		#checklist = np.unique(conf[:,0])
		for i in range(len(conf)):
			if(int(conf[i,0]) == -1):
				if(conf[i,2]=='Null'):
					error[0] += 1
					if(display):
						utils.print_error("->  Configuration comparison error. Periphery Reg: {:32s} -> Expected: {:8b} Found: NULL".format(str(conf[i,1]), int(conf_ref[i,2]) ) )
				elif(int(conf[i,2]) != int(conf_ref[i,2])):
					error[0] += 1
					if(display):
						utils.print_error("->  Configuration comparison error. Periphery Reg: {:32s} -> Expected: {:8b} Found: {:8b}".format(str(conf[i,1]), int(conf_ref[i,2]), int(conf[i,2]) ) )
			elif(int(conf[i,0]) > 0):
				if(conf[i,2]=='Null'):
					error[int(conf[i,0])] += 1
					if(display):
						utils.print_error("->  Configuration comparison error. Strip {:3d} Reg: {:32s} -> Expected: {:8b} Found: NULL".format(int(conf[i,0]), str(conf[i,1]), int(conf_ref[i,2]) ) )
				elif(int(conf[i,2]) != int(conf_ref[i,2])):
					error[int(conf[i,0])] += 1
					if(display):
						utils.print_error("->  Configuration comparison error. Strip {:3d} Reg: {:32s} -> Expected: {:8b} Found: {:8b}".format(int(conf[i,0]), str(conf[i,1]), int(conf_ref[i,2]), int(conf[i,2])) )
		if(error==[0]*121):
			if(display):
				utils.print_good("->  Configuration comparison match.")
		return error

	def _change_config_value(self, conf, strips, field, new_value):
		for strip in strips:
			conf_loc = np.where(( conf[:,0:2] == ( '{:d}'.format(strip) , field )).all(axis=1))[0]
			for line in conf_loc:
				conf[line] = ['{:d}'.format(strip), field, new_value]
		return conf

	#####################################################################
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

	#####################################################################
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

	######################################################################
	#def set_pattern_injection(self, pattern_L=0b00000001, pattern_H=0b00000001):
	#	if(tbconfig.VERSION['SSA'] >= 2):
	#		self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip='all', data=pattern_L)
	#		self.I2C.strip_write( register="DigCalibPattern_H", field=False, strip='all', data=pattern_H)
	#	else:
	#		self.I2C.strip_write("DigCalibPattern_L", 0, pattern_L)
	#		self.I2C.strip_write("DigCalibPattern_H", 0, pattern_H)

	#####################################################################
	def get_pattern_injection(self, strip=10):
		if(tbconfig.VERSION['SSA'] >= 2):
			r1 = self.I2C.strip_read( register="DigCalibPattern_L", field=False, strip=strip)
			r2 = self.I2C.strip_read( register="DigCalibPattern_H", field=False, strip=strip)
		else:
			self.I2C.strip_read("DigCalibPattern_L", 0)
			self.I2C.strip_read("DigCalibPattern_H", 0)
		return [r1, r2]

	#####################################################################
	def reset_pattern_injection(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write("StripControl1", 'all', 0b01001)
			self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip='all', data=0)
			self.I2C.strip_write( register="DigCalibPattern_H", field=False, strip='all', data=0)
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)

	#####################################################################
	def __do_phase_tuning(self):
		self.setup_readout_chip_id()
		cnt = 0; done = True
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		send_test(15)
		#print(self.fc7.read("stat_phy_phase_tuning_done"))
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0 and cnt < 5):
			time.sleep(0.1)
			utils.print_log("Waiting for the phase tuning")
			cnt += 1
		if cnt>4:
			done = False
		return  done

	def phase_tuning(self, method = 'new'):
		self.activate_readout_shift()
		if(self.fc7.invert):
			self.set_shift_pattern_all(0b01111111)
		elif(method == 'old'):
			self.set_shift_pattern_all(0b10000000)
		else:
			self.set_shift_pattern_all(0b10100000) #0b10100000

		time.sleep(0.01)
		self.set_lateral_lines_alignament()
		time.sleep(0.01)
		if(method == 'old' or self.fc7.invert):
			rt = self.align_out()
		else:
			rt = self.TuneSSA(0b10100000) #0b10100000
		if(tbconfig.VERSION['SSA']==1):
			self.I2C.peri_write('OutPattern7/FIFOconfig', 7)
		self.reset_pattern_injection()
		self.activate_readout_normal()
		return rt

	#####################################################################
	def align_out(self):
		self.fc7.write("ctrl_phy_phase_tune_again", 1)
		timeout_max = 3
		timeout = 0
		time.sleep(0.1)
		while(self.fc7.read("stat_phy_phase_tuning_done") == 0):
			time.sleep(0.1)
			utils.print_warning("->  Waiting for the phase tuning")
			#self.fc7.write("ctrl_phy_phase_tune_again", 1)
			timeout+=1
			if (timeout == timeout_max):
				return False
		#self.fc7.write("ctrl_phy_phase_tune_again", 1)
		return True

	#####################################################################
	def set_line_mode(self,
		line        = 0,
		pMode       = 0,
		pDelay      = 0,
		pBitSlip    = 0,
		pEnableL1   = 0,
		pMasterLine = 0 ):
		# select FE
		pHybrid = 0
		pChip   = 0
		fHybrid = (pHybrid & 0xF) << 28;
		fChip   = (pChip & 0xF) << 24;
		fLine   = (line & 0xF) << 20;
		# command
		command_type = 2
		fCommand = (command_type & 0xF) << 16;
		# shift payload
		mode_raw = (pMode & 0x3) << 12
		# set defaults
		l1a_en_raw         = ((pEnableL1 & 0x1) << 11)  if (pMode == 0) else 0
		master_line_id_raw = ((pMasterLine & 0xF) << 8) if (pMode == 1) else 0
		delay_raw          = ((pDelay & 0x1F) << 3)     if (pMode == 2) else 0
		bitslip_raw        = ((pBitSlip & 0x7) << 0)    if (pMode == 2) else 0

		command_final = fHybrid + fChip + fLine + fCommand + mode_raw + l1a_en_raw + master_line_id_raw + delay_raw + bitslip_raw
		utils.print_info(  "Line " + str(line) + " setting line mode to " + str(command_final) )
		self.fc7.write("ctrl_phy_phase_tuning", command_final)

	#####################################################################
	def set_line_shift_stubs(self, value, line='all'):
		if(line == 'all'): linesel = range(1,9)
		elif(isinstance(line, int)): linesel = [line]
		else: return False
		for ll in linesel:
			self.set_line_mode(line=ll, pMode=2, pDelay=0, pBitSlip=value, pEnableL1=0, pMasterLine=0)
		return True

		#	def set_l1_shift(self, delay=0 ):
		#		cMode = 2
		#		cDelay = delay
		#		cEnableL1 = 0
		#
		#		cBitslip = pTuner.fBitslip + (uint8_t)(fFirmwareFrontEndType == FrontEndType::SSA || fFirmwareFrontEndType == FrontEndType::MPA);
		#
		#		self.set_line_mode(pMode=cMode, pDelay=cDelay, pBitSlip=cBitslip, pMasterLine=0)

	#####################################################################
	def TuneSSA(self, pattern=0b10100011):
		self.setup_readout_chip_id()
		state = True
		for line in range(0,9):
			self.fc7.TuneLine(line, np.array(pattern),1,True,False)
			if self.fc7.CheckLineDone(0,0,line) != 1:
				utils.print_warning("Failed tuning line {:d}".format(line))
				state = False
		return state

	#####################################################################
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
			utils.print_error("Error! The edge name is wrong")

	#####################################################################
	def activate_readout_normal(self, mipadapterdisable = 0):
		val = 0b100 if (mipadapterdisable) else 0b000
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=val)
			rep = self.I2C.peri_read( register="control_1", field='ReadoutMode')
		else:
			self.I2C.peri_write('ReadoutMode',val)
			rep = self.I2C.peri_read("ReadoutMode")
		if(rep != val):
			utils.print_error("Error! I2C did not work properly in activate_readout_normal")
			#exit(1)

	#####################################################################
	def activate_readout_async(self, ssa_first_counter_delay = 8, correction = 0):
		self.setup_readout_chip_id()
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=0b001)
		else:
			self.I2C.peri_write('ReadoutMode',0b01)
		if(isinstance(ssa_first_counter_delay, int)):
			self.set_async_readout_start_delay(delay=ssa_first_counter_delay, fc7_correction=correction)

	#####################################################################
	def set_async_readout_start_delay(self, delay='keep', fc7_correction=0):
		self.I2C.peri_write("AsyncRead_StartDel_MSB", ((delay >> 8) & 0x01))
		self.I2C.peri_write("AsyncRead_StartDel_LSB", (delay & 0xff))
		if (self.I2C.peri_read("AsyncRead_StartDel_LSB") != delay & 0xff):
			utils.print_error("Error! I2C did not work properly")
		# ssa set delay of the counters
		fwdel = delay + 20 + fc7_correction
		if(fwdel >= 255):
			utils.print_error('->  The counters delay value selected is not supposrted by the firmware [> 255]')
		self.fc7.write("cnfg_phy_slvs_ssa_first_counter_del", fwdel & 0xff)

	#####################################################################
	def activate_readout_shift(self):
		self.setup_readout_chip_id()
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_1", field='ReadoutMode', data=0b010)
		else:
			self.I2C.peri_write('ReadoutMode',0b10)

	#####################################################################
	def set_shift_pattern_all(self, pattern):
		self.set_shift_pattern( ST = [pattern]*8, L1 = pattern, Left = pattern, Right = pattern)

	#####################################################################
	def set_shift_pattern(self, ST=[0xaa]*8, L1=0x80, Left=0x80, Right=0x80):
		if(tbconfig.VERSION['SSA'] >= 2):
			R_ST = [-1]*7
			self.I2C.peri_write(register="Shift_pattern_st_0",      field=False, data = ST[0])
			self.I2C.peri_write(register="Shift_pattern_st_1",      field=False, data = ST[1])
			self.I2C.peri_write(register="Shift_pattern_st_2",      field=False, data = ST[2])
			self.I2C.peri_write(register="Shift_pattern_st_3",      field=False, data = ST[3])
			self.I2C.peri_write(register="Shift_pattern_st_4_st_5", field=False, data = ST[4])
			self.I2C.peri_write(register="Shift_pattern_st_6_st_7", field=False, data = ST[6])# ST[6]
			self.I2C.peri_write(register="Shift_pattern_Left",      field=False, data = Left)
			self.I2C.peri_write(register="Shift_pattern_Right",     field=False, data = Right)
			self.I2C.peri_write(register="Shift_pattern_L1",        field=False, data = L1) # L1
			R_ST[0] = self.I2C.peri_read(register="Shift_pattern_st_0",      field=False )
			R_ST[1] = self.I2C.peri_read(register="Shift_pattern_st_1",      field=False )
			R_ST[2] = self.I2C.peri_read(register="Shift_pattern_st_2",      field=False )
			R_ST[3] = self.I2C.peri_read(register="Shift_pattern_st_3",      field=False )
			R_ST[4] = self.I2C.peri_read(register="Shift_pattern_st_4_st_5", field=False )
			R_ST[6] = self.I2C.peri_read(register="Shift_pattern_st_6_st_7", field=False )
			R_Left  = self.I2C.peri_read(register="Shift_pattern_Left",      field=False )
			R_Right = self.I2C.peri_read(register="Shift_pattern_Right",     field=False )
			R_L1    = self.I2C.peri_read(register="Shift_pattern_L1",        field=False )
			#print(ST)
			if(R_ST[0] != ST[0] ): utils.print_error('->  Shift pattern set R_ST[0] I2C error: {:8b}'.format(R_ST[0] ))
			if(R_ST[1] != ST[1] ): utils.print_error('->  Shift pattern set R_ST[1] I2C error: {:8b}'.format(R_ST[1] ))
			if(R_ST[2] != ST[2] ): utils.print_error('->  Shift pattern set R_ST[2] I2C error: {:8b}'.format(R_ST[2] ))
			if(R_ST[3] != ST[3] ): utils.print_error('->  Shift pattern set R_ST[3] I2C error: {:8b}'.format(R_ST[3] ))
			if(R_ST[4] != ST[4] ): utils.print_error('->  Shift pattern set R_ST[4] I2C error: {:8b}'.format(R_ST[4] ))
			if(R_ST[6] != ST[6] ): utils.print_error('->  Shift pattern set R_ST[6] I2C error: {:8b}'.format(R_ST[6] ))
			if(R_Left  != Left  ): utils.print_error('->  Shift pattern set R_Left  I2C error: {:8b}'.format(R_Left  ))
			if(R_Right != Right ): utils.print_error('->  Shift pattern set R_Right I2C error: {:8b}'.format(R_Right ))
			if(R_L1    != L1    ): utils.print_error('->  Shift pattern set R_L1    I2C error: {:8b}'.format(R_L1    ))
		else:
			self.I2C.peri_write('OutPattern0', ST[0])
			self.I2C.peri_write('OutPattern1', ST[1])
			self.I2C.peri_write('OutPattern2', ST[2])
			self.I2C.peri_write('OutPattern3', ST[3])
			self.I2C.peri_write('OutPattern4', ST[4])
			self.I2C.peri_write('OutPattern5', ST[5])
			self.I2C.peri_write('OutPattern6', ST[6])
			self.I2C.peri_write('OutPattern7/FIFOconfig',ST[7])

	#####################################################################
	def set_async_delay(self, value):
		msb = (value & 0xFF00) >> 8
		lsb = (value & 0x00FF) >> 0
		self.I2C.peri_write('AsyncRead_StartDel_MSB', msb)
		self.I2C.peri_write('AsyncRead_StartDel_LSB', lsb)

	#####################################################################
	def set_threshold(self, value):
		self.I2C.peri_write("Bias_THDAC", value)
		#time.sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDAC")
		if(test_read != value):
			utils.print_error("Was writing: ", value, ", got: ", test_read)
			utils.print_error("Error. Failed to set the threshold")
			error(1)

	#####################################################################
	def set_threshold_H(self, value):
		self.I2C.peri_write("Bias_THDACHIGH", value)
		#time.sleep(0.01)
		test_read = self.I2C.peri_read("Bias_THDACHIGH")
		if(test_read != value):
			utils.print_error("Was writing: ", value, ", got: ", test_read)
			utils.print_error("Error. Failed to set the threshold")
			error(1)

	#####################################################################
	def init_default_thresholds(self):
		# init thersholds
		self.I2C.peri_write("Bias_THDAC", 35)
		self.I2C.peri_write("Bias_THDACHIGH", 120)

	#####################################################################
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
			utils.print_error("Error. Failed to set the trimming")

	#####################################################################
	def set_cal_pulse(self, amplitude = 255, duration = 5, delay = 'keep'):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write("Bias_CALDAC", amplitude)
			self.I2C.peri_write(register="control_2", field='CalPulse_duration', data=duration)
			self.set_cal_pulse_delay(delay)
		else:
			self.I2C.peri_write("Bias_CALDAC", amplitude) # init cal pulse itself
			self.I2C.peri_write("CalPulse_duration", duration) # set cal pulse duration
			self.set_cal_pulse_delay(delay) # init the cal pulse digital delay line

	#####################################################################
	def set_cal_pulse_amplitude(self, amplitude = 255):
		self.I2C.peri_write("Bias_CALDAC", amplitude)

	#####################################################################
	def set_cal_pulse_duration(self, duration = 5):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_2", field='CalPulse_duration', data=duration)
		else:
			self.I2C.peri_write("CalPulse_duration", duration)

	#####################################################################
	def set_cluster_cut(self, value = 5):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_2", field='ClusterCut', data=value)
		else:
			self.I2C.peri_write("ClusterCut", value)

	#####################################################################
	def get_cluster_cut(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			rp = self.I2C.peri_read(register="control_2", field='ClusterCut')
		else:
			rp = self.I2C.peri_read("ClusterCut", value)
		return rp

	#####################################################################
	def set_hit_phase_compensation(self, value = 5):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="Config_HitDelay", field='Config_HitDelay', data=value)
		else:
			utils.print_log('Request not available for SSAv1')

	#####################################################################
	def get_hit_phase_compensation(self):
		if(tbconfig.VERSION['SSA'] >= 2):
			rp = self.I2C.peri_read(register="Config_HitDelay", field='Config_HitDelay')
		else:
			utils.print_log('Request not available for SSAv1')
			rp = 0
		return rp

	#####################################################################
	def set_cal_pulse_delay(self, delay):
		V = tbconfig.VERSION['SSA']
		if(isinstance(delay, str)):
			if(delay == 'disable' or delay == 'off'):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='DL_en',  data=0)
				else:     self.I2C.peri_write("Bias_DL_en", 0)
				self.bias_dl_enable = False
			elif(delay == 'enable'or delay == 'on'):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='DL_en',  data=1)
				else:     self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			elif(delay == 'keep'):
				pass
			else:
				exit(1)
		elif(isinstance(delay, int)):
			if (not self.bias_dl_enable):
				if(V>=2): self.I2C.peri_write(register='Delay_line', field='DL_en',  data=1)
				else:     self.I2C.peri_write("Bias_DL_en", 1)
				self.bias_dl_enable = True
			if(V>=2): self.I2C.peri_write(register='Delay_line', field='DL_ctrl',  data=delay)
			else:     self.I2C.peri_write("Bias_DL_ctrl", delay)
		return True

	#####################################################################
	def set_sampling_deskewing_coarse(self, value):
		word = value & 0b111
		if((tbconfig.VERSION['SSA'] >= 2)):
			r = self.I2C.peri_write(register="ClockDeskewing_coarse", field=False,  data=word)
			r = self.I2C.peri_read( register="ClockDeskewing_coarse", field=False)
		else:
			self.I2C.peri_write("PhaseShiftClock", word)
			r = self.I2C.peri_read("PhaseShiftClock")
		if(r != word): return False
		else: return True

	#####################################################################
	def set_sampling_deskewing_fine(self, value, enable = True, bypass = False):
		if((tbconfig.VERSION['SSA'] >= 2)):
			dllcode = utils.gray_code(value)
			dllen = 0b1 if enable else 0b0
			dllby = 0b0 if bypass else 0b1
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_value',      data=dllcode)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_chargepump', data=self.dll_chargepump)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_bypass',     data=dllby)
			self.I2C.peri_write(register="ClockDeskewing_fine", field='DLL_Enable',     data=dllen)
		else:
			word = (
				((value & 0b1111) << 0) |
				((self.dll_chargepump & 0b11) << 4) |
				((bypass & 0b1) << 6) |
				((enable & 0b1) << 7)
			)
			if((tbconfig.VERSION['SSA'] >= 2)):
				self.I2C.peri_write(register="ClockDeskewing_fine", field = False, data = word)
				r = self.I2C.peri_read(register="ClockDeskewing_fine", field = False)
			else:
				self.I2C.peri_write("ClockDeskewing", word)
				r = self.I2C.peri_read("ClockDeskewing")
			if(r != word): return False
			else: return True

	#####################################################################
	def set_sampling_deskewing_chargepump(self, val):
		self.dll_chargepump = val & 0b11

		if((tbconfig.VERSION['SSA'] >= 2)):
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

	#####################################################################
	def set_lateral_data_phase(self, left, right):
		self.setup_readout_chip_id()
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_1", right)
		self.fc7.write("ctrl_phy_ssa_gen_lateral_phase_2", left)

	#####################################################################
	def set_lateral_data(self, left, right):
		self.setup_readout_chip_id()
		self.fc7.write("cnfg_phy_SSA_gen_right_lateral_data_format", right)
		self.fc7.write("cnfg_phy_SSA_gen_left_lateral_data_format", left)

	#####################################################################
	def read_fuses(self, pulse = True, display = True):
		if(pulse):
			self.I2C.peri_write('Fuse_Mode', 0b00001111)
			self.I2C.peri_write('Fuse_Mode', 0b00000000)
		r0 = self.I2C.peri_read('Fuse_Value_b0')
		r1 = self.I2C.peri_read('Fuse_Value_b1')
		r2 = self.I2C.peri_read('Fuse_Value_b2')
		r3 = self.I2C.peri_read('Fuse_Value_b3')
		if display:
			utils.print_info( "{0:02x}-{1:02x}-{2:02x}-{3:02x}".format(r3, r2, r1, r0) )
		else:
			r = (r3<<24) | (r2<<16) | (r1<<8) | (r0<<0)
			return r

	#####################################################################
	def write_fuses(self, val = 0, pulse = True, display = False, confirm = False):
		self.setup_readout_chip_id()
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
			utils.print_error("\n->  Error in setting the e-fuses write buffer")
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
			utils.print_error('->  E-Fuses write error: ')
			utils.print_error('        Written:...{0:032b}'.format(val))
			utils.print_error('        Read:......{0:032b}'.format(r))
			return False
		else:
			return True

	#####################################################################
	def read_seu_counter(self, display=True, return_rate=False, return_short_array=False, printmode='info', sync=1, async=1, filename=False):
		if(tbconfig.VERSION['SSA'] >= 2):
			## read counters ##############
			seu_rate = {}
			check_time = time.time()
			prev = copy.deepcopy(self.seu_cntr)
			if(sync):  self.seu_cntr['S']['peri'][0]  = self.I2C.peri_read(register = 'Sync_SEUcnt_blk0',  field = False)
			if(sync):  self.seu_cntr['S']['peri'][1]  = self.I2C.peri_read(register = 'Sync_SEUcnt_blk1',  field = False)
			if(async): self.seu_cntr['A']['peri'][0]  = self.I2C.peri_read(register = 'Async_SEUcnt_blk0', field = False)
			if(async): self.seu_cntr['A']['peri'][1]  = self.I2C.peri_read(register = 'Async_SEUcnt_blk1', field = False)
			for i in range(0,15):
				if(sync):  self.seu_cntr['S']['strip'][i] = self.I2C.peri_read('Sync_SEUcnt_StripBlock{:d}'.format(i) )
				if(async): self.seu_cntr['A']['strip'][i] = self.I2C.peri_read('Async_SEUcnt_StripBlock{:d}'.format(i) )
			################################
			self.seu_cntr['time_since_last_check'] = (check_time - self.seu_check_time)
			self.seu_check_time = check_time
			try:
				self.seu_cntr['S']['peri_all']  = np.sum(self.seu_cntr['S']['peri'])
				self.seu_cntr['A']['peri_all']  = np.sum(self.seu_cntr['A']['peri'])
				self.seu_cntr['S']['strip_all'] = np.sum(self.seu_cntr['S']['strip'])
				self.seu_cntr['A']['strip_all'] = np.sum(self.seu_cntr['A']['strip'])
				self.seu_cntr['S']['all'] = self.seu_cntr['S']['peri_all'] + self.seu_cntr['S']['strip_all']
				self.seu_cntr['A']['all'] = self.seu_cntr['A']['peri_all'] + self.seu_cntr['A']['strip_all']
				seu_rate['A'] = np.float(self.seu_cntr['A']['all']-prev['A']['all'])/(self.seu_cntr['time_since_last_check'])
				seu_rate['S'] = np.float(self.seu_cntr['S']['all']-prev['S']['all'])/(self.seu_cntr['time_since_last_check'])

				if(display):
					utils.print("->  SEU Counter       ->  S: rate ={:8.3f}seu/s | new =[{:5d}] | total =[{:5d}]".format(
						seu_rate['S'], self.seu_cntr['S']['all']-prev['S']['all'], self.seu_cntr['S']['all']), printmode)

					utils.print("->  SEU Counter       ->  A: rate ={:8.3f}seu/s | new =[{:5d}] | total =[{:5d}]".format(
						seu_rate['A'], self.seu_cntr['A']['all']-prev['A']['all'], self.seu_cntr['A']['all']), printmode)
			except:
				#means that was impossible to read the counters via I2C, so some of the values are null
				utils.print_error('->  Impossible to read SEU counters')
				if(return_short_array):
					return [-0xff,-0xff,-0xff,-0xff, self.seu_cntr['time_since_last_check']  ]
		else:
			self.seu_cntr = self.I2C.peri_read('SEU_Counter')
			seu_rate = np.float(self.seu_cntr)/(time.time() - self.seu_check_time)
			self.seu_check_time = time.time()
			if(display):
				utils.print_info("->  SEU Counter       ->  Value: " + str(seucounter) + " Rate: " + str(seurate) + " 1/s", printmode)
		if(return_short_array):
			rt = [int(self.seu_cntr['A']['peri_all']), int(self.seu_cntr['A']['strip_all']), int(self.seu_cntr['S']['peri_all']), int(self.seu_cntr['S']['strip_all']), self.seu_cntr['time_since_last_check']  ]
		else:
			if(return_rate): rt = self.seu_cntr, seu_rate
			else: rt = self.seu_cntr
		if(filename):
			dir = filename[:filename.rindex(os.path.sep)]
			if not os.path.exists(dir): os.makedirs(dir)
			with open(filename, 'a') as fo:
				fo.write(str( self.seu_cntr['A']['peri'] ))
				fo.write(',\t')
				fo.write(str( self.seu_cntr['A']['strip'] ))
				fo.write(',\t')
				fo.write(str( self.seu_cntr['S']['peri'] ))
				fo.write(',\t')
				fo.write(str( self.seu_cntr['S']['strip'] ))
				fo.write(',\t')

				fo.write('\n')
		return rt

	##############################################################
	def set_l1_latency(self, latency):
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.peri_write(register="control_3", field='L1_Latency_lsb', data = ((latency & 0x00ff) >> 0) )
			self.I2C.peri_write(register="control_1", field='L1_Latency_msb', data = ((latency & 0x0100) >> 8) )
		else:
			self.I2C.peri_write('L1_Latency_msb', (latency & 0xff00) >> 8)
			self.I2C.peri_write('L1_Latency_lsb', (latency & 0x00ff) >> 0)

	def set_all_config_masks(self, digital=0xff, analog=0xff, strips=0xff ):
		self.I2C.peri_write(register = 'mask_strip',  field = False, data=strips)
		self.I2C.peri_write(register = 'mask_peri_D', field = False, data=digital)
		self.I2C.peri_write(register = 'mask_peri_A', field = False, data=analog)

	#####################################################################
	def try_i2c(self, repeat=4):
		r=[]; d=[]; w=[];
		Result = True
		utils.print_log_color_legend_i2c('\n\n')
		if(tbconfig.VERSION['SSA'] >= 2):
			reglist = ['Bias_TEST_msb','Bias_TEST_lsb', 'configuration_test', 'Shift_pattern_st_0', 'Shift_pattern_st_1', 'Shift_pattern_st_2']
		else:
			reglist = ['OutPattern0','OutPattern1', 'OutPattern2', 'OutPattern3', 'OutPattern4', 'OutPattern5']
		self.I2C.peri_write(register = 'mask_strip',  field = False, data=0xff)
		self.I2C.peri_write(register = 'mask_peri_D', field = False, data=0xff)
		self.I2C.peri_write(register = 'mask_peri_A', field = False, data=0xff)
		for iter in range(repeat):
			for reg in reglist:
				data = randint(1,255)
				d.append( data )
				w.append( self.I2C.peri_write(register = reg, field = False, data = data))
				#time.sleep(0.01)
			for reg in reglist:
				r.append( self.I2C.peri_read( register = reg, field = False))
				#time.sleep(0.01)

		if((tbconfig.VERSION['SSA'] >= 2)):
			for iter in range(repeat):
				for k in range(6):
					data = randint(1,7)
					d.append( data )
					field = 'mod{:0d}'.format(k)
					w.append( self.I2C.peri_write(register = 'configuration_test', field = field, data = data))
					#time.sleep(0.01)
					r.append( self.I2C.peri_read( register = 'configuration_test', field = field))
					#time.sleep(0.01)

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

	#####################################################################
	def set_active_memory(self, L, H):
		sel=[0,0]
		if(  L in [0, 'sram',  'SRAM']):
			utils.print_info('->  Selected SRAM memory  for the hit memory')
			sel[0]=0
		elif(L in [1, 'latch', 'LATCH']):
			utils.print_info('->  Selected LATCH memory for the hit memory')
			sel[0]=1
		else:
			sel[0]=0
		if(  H in [0, 'sram',  'SRAM']):
			utils.print_info('->  Selected SRAM memory  for the HIP flags memory')
			sel[1]=0
		elif(H in [1, 'latch', 'LATCH']):
			utils.print_info('->  Selected LATCH memory for the HIP flags memory')
			sel[1]=1
		select = sel[0]&0b1 | (sel[1]&0b1)<<1
		self.I2C.peri_write(register = 'control_1', field = 'memory_select', data=select)
		rp = self.get_active_memory()
		return rp

	#####################################################################
	def get_active_memory(self):
		active = ['','']
		rp = self.I2C.peri_read( register = 'control_1', field = 'memory_select_0')
		if(rp): active[0] = 'LATCH'
		else  : active[0] = 'SRAM'
		rp = self.I2C.peri_read( register = 'control_1', field = 'memory_select_1')
		if(rp): active[1] = 'LATCH'
		else  : active[1] = 'SRAM'
		return active

	#####################################################################
	def set_clockgating_magic_number(self, value):
		if((tbconfig.VERSION['SSA'] >= 2)):
			rt = self.I2C.peri_write(register = 'ClkTreeMagicNumber', field = 'ClkTreeMagicNumber', data=value)
			rp = self.I2C.peri_read( register = 'ClkTreeMagicNumber', field = 'ClkTreeMagicNumber')
			ret = True if(rp == value) else False
		else:
			utils.print_log('Request not available for SSAv1')
			rp = False
		return ret

	def set_clockgating_magic_control(self, val='disable'):
		if(val == 'enable'): value = 0b01010101
		else: value = 0b10101010
		self.set_clockgating_magic_number(value)

	def get_clockgating_magic_number(self):
		if((tbconfig.VERSION['SSA'] >= 2)):
			ret = self.I2C.peri_read( register = 'ClkTreeMagicNumber', field = 'ClkTreeMagicNumber')
		else:
			utils.print_log('Request not available for SSAv1')
			ret = False
		return ret

	#####################################################################
	def set_clockgating_enable(self, clock_A=1, clock_B=1, clock_C=1):
		if((tbconfig.VERSION['SSA'] >= 2)):
			if(clock_A): rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_A', data=0b01)
			else:        rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_A', data=0b10)
			if(clock_B): rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_B', data=0b01)
			else:        rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_B', data=0b10)
			if(clock_C): rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_C', data=0b01)
			else:        rt = self.I2C.peri_write(register = 'ClkTree_control', field = 'ClkTree_C', data=0b10)
		else:
			utils.print_log('Request not available for SSAv1')

	def get_clockgating_enable(self):
		ret = [-1,-1,-1]
		if((tbconfig.VERSION['SSA'] >= 2)):
			ret[0] = self.I2C.peri_read( register = 'ClkTree_control', field = 'ClkTree_A')
			ret[1] = self.I2C.peri_read( register = 'ClkTree_control', field = 'ClkTree_B')
			ret[2] = self.I2C.peri_read( register = 'ClkTree_control', field = 'ClkTree_C')
		else:
			utils.print_log('Request not available for SSAv1')
			ret = False
		return ret

	#####################################################################
	def get_L1_FIFO_overflow_counter(self):
		if((tbconfig.VERSION['SSA'] >= 2)):
			msb = self.I2C.peri_read( register = 'L1_FIFO_Overflow_Cnt_H', field = False)
			lsb = self.I2C.peri_read( register = 'L1_FIFO_Overflow_Cnt_L', field = False)
			ret = ((msb&0xff)<<9) | (lsb&0xff)
		else:
			utils.print_log('Request not available for SSAv1')
			ret = 0
		return ret

	#####################################################################
	def set_t1_clock_output_select(self, mode='T1'):
		if((tbconfig.VERSION['SSA'] >= 2)):
			if(mode == 'clock'): value = 1
			elif(mode == 'T1'):  value = 0
			else: return False
			rt = self.I2C.peri_write(register = 'control_1', field = 'T1_or_CLK_select', data=value)
			rp = self.I2C.peri_read( register = 'control_1', field = 'T1_or_CLK_select')
			ret = True if(rp == value) else False
		else:
			utils.print_log('Request not available for SSAv1')
			rp = False
		return ret


	#####################################################################
	def set_stub_data_offset(self, block_L=0, block_1_30=0, block_31_60=0, block_61_90=0, block_91_120=0, block_R=0):
		#elf.I2C.peri_write( register = 'StripOffset_byte0', field='StripOffset_L'       data = (block_L      & 0b11111)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte0', field='StripOffset_1_30'    data = (block_1_30   & 0b11100)>>2 )
		#elf.I2C.peri_write( register = 'StripOffset_byte1', field='StripOffset_1_30'    data = (block_1_30   & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte1', field='StripOffset_31_60'   data = (block_31_60  & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte1', field='StripOffset_61_90'   data = (block_61_90  & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte2', field='StripOffset_61_90'   data = (block_61_90  & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte2', field='StripOffset_91_120'  data = (block_91_120 & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte3', field='StripOffset_91_120'  data = (block_91_120 & 0b00000)>>0 )
		#elf.I2C.peri_write( register = 'StripOffset_byte3', field='StripOffset_R'       data = (block_R      & 0b00000)>>0 )

		data0 = ((block_L      & 0b11111)<<3) | ((block_1_30   & 0b11100)>>2)
		data1 = ((block_1_30   & 0b00011)<<6) | ((block_31_60  & 0b11111)<<1) | ((block_61_90 & 0b10000)>>4)
		data2 = ((block_61_90  & 0b01111)<<4) | ((block_91_120 & 0b11110)>>1)
		data3 = ((block_91_120 & 0b00001)<<7) | ((block_R      & 0b11111)<<2)

		self.I2C.peri_write( register = 'StripOffset_byte0', field=False, data = data0 )
		self.I2C.peri_write( register = 'StripOffset_byte1', field=False, data = data1 )
		self.I2C.peri_write( register = 'StripOffset_byte2', field=False, data = data2 )
		self.I2C.peri_write( register = 'StripOffset_byte3', field=False, data = data3 )

	def set_termination_enable(self, clock=1, T1=1, lateral=1):
		p1 = self.I2C.peri_write( register = 'SLVS_pad_current_Clk_T1',  field='SLVS_termination_clock',       data = clock )
		p2 = self.I2C.peri_write( register = 'SLVS_pad_current_Clk_T1',  field='SLVS_termination_T1',          data = T1 )
		p3 = self.I2C.peri_write( register = 'SLVS_pad_current_Lateral', field='SLVS_pad_termination_lateral', data = lateral )
		r1 = self.I2C.peri_read(  register = 'SLVS_pad_current_Clk_T1',  field='SLVS_termination_clock')
		r2 = self.I2C.peri_read(  register = 'SLVS_pad_current_Clk_T1',  field='SLVS_termination_T1')
		r3 = self.I2C.peri_read(  register = 'SLVS_pad_current_Lateral', field='SLVS_pad_termination_lateral')
		if(r1==clock and r2==T1 and r3==lateral): return True
		else: return False




	#def set_clockgating_enable(self, clock_A=1, clock_A=2, clock_A=3):

# ssa_peri_reg_map['Fuse_Mode']              = 43
# ssa_peri_reg_map['Fuse_Prog_b0']           = 44
# ssa_peri_reg_map['Fuse_Prog_b1']           = 45
# ssa_peri_reg_map['Fuse_Prog_b2']           = 46
# ssa_peri_reg_map['Fuse_Prog_b3']           = 47
# ssa_peri_reg_map['Fuse_Value_b0']          = 48
# ssa_peri_reg_map['Fuse_Value_b1']          = 49
# ssa_peri_reg_map['Fuse_Value_b2']          = 50
# ssa_peri_reg_map['Fuse_Value_b3']          = 51
