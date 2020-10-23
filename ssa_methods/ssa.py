from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

from ssa_methods.ssa_i2c_conf import *
from ssa_methods.ssa_ctrl_base import *
from ssa_methods.ssa_ctrl_strip import *
from ssa_methods.ssa_ctrl_analog import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *
from ssa_methods.ssa_ctrl_builtin_selftest import *



class SSA_ASIC:

	def __init__(self, index, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.index   = index
		self.i2c     = I2C
		self.pwr     = pwr
		self.fc7     = FC7
		self.ctrl    = ssa_ctrl_base(index, self.i2c, self.fc7, self.pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map )
		self.strip   = ssa_ctrl_strip( self.i2c, self.fc7 )
		self.analog  = ssa_ctrl_analog(self.i2c, self.fc7, self.pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject  = SSA_inject( self.i2c, self.fc7, self.ctrl, self.strip )
		self.readout = SSA_readout(index, self.i2c, self.fc7, self.ctrl, self.strip )
		self.bist    = ssa_ctrl_builtin_selftest( self.i2c, self.fc7, self.ctrl, self.strip, self.pwr, self.inject, self.readout, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.generic_parameters = {}
		self.cap = 52E-15

	####### Initialize functions ###############

	def reset(self, display=True):
		if(display): utils.print_info('->  Sent Hard-Reset command')
		self.fc7.reset_chip(self.index)

	def resync(self):
		self.ctrl.resync()

	def disable(self, display=True):
		self.fc7.disable_chip(self.index)

	def enable(self, display=True):
		self.fc7.enable_chip(self.index)

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.save_configuration(file = file, display = display)
		utils.print_log("->  Config registers saved in {:s}.".format(file))

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.load_configuration(file = file, display = display)

	def on(self):
		self.ctrl.reset(display=True)
		utils.print_info("->  Reset SSA Chip")
		time.sleep(0.3);
		utils.activate_I2C_chip(self.fc7)
		time.sleep(0.2)

	def init(self, reset_board=False, reset_chip=False, resync=True, slvs_current=0b111, edge="rising", display=True, read_current=False, set_deskewing=False):
		for iteration in range(1):
			self.generic_parameters['cl_word_alignment'] = False
			if(display):
				sys.stdout.write("->  Initialising..\r")
				sys.stdout.flush()
			if(reset_board):
				self.fc7.write("ctrl_command_global_reset", 1)
				time.sleep(0.3);
				if(display): utils.print_info("->  Reset FC7 Firmware")
			if(reset_chip):
				self.ctrl.reset_and_set_sampling_edge(display=False)
				time.sleep(0.3);
				if(display): utils.print_info("->  Reset SSA Chip")
			utils.activate_I2C_chip(self.fc7)
			#time.sleep(0.2)
			self.ctrl.set_lateral_data(left=0, right=0)
			if(display):
				sys.stdout.write("->  Tuning sampling phases..\r")
				sys.stdout.flush()
			self.ctrl.set_t1_sampling_edge(edge)
			self.ctrl.init_slvs(slvs_current)
			rt = self.ctrl.phase_tuning()
			if(rt):
				if(display): utils.print_good("->  Shift register mode ok")
				if(display): utils.print_good("->  Sampling phases tuned")
			else:
				if(display): utils.print_error("->  Impossible to complete phase tuning")
			self.ctrl.activate_readout_normal()
			if(set_deskewing):
				self.ctrl.set_sampling_deskewing_coarse(value = 0)
				self.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
				self.ctrl.set_cal_pulse_delay(0)
			if(resync):
				self.ctrl.resync(display=False)
				utils.print_info("->  ReSync request");
			if(display):
				utils.print_info("->  Activated normal readout mode");
				sys.stdout.write("->  Ready!                  ")
				sys.stdout.flush()
				time.sleep(0.2)
				if(read_current):
					self.pwr.get_power(display = True)
			if(rt):
				break
			else:
				utils.print_warning('->  Error in alignment. Reiterating init procedure {:d}'.format(iteration))
		return rt

	def init_all(self):
		self.init(reset_board = True, reset_chip = False)




	####### Data alignment functions ################################

	def alignment_all(self, display = False, file = False):
		r1 = self.init(reset_board = True, reset_chip = False, display = display)
		time.sleep(0.1)
		r2 = self.alignment_cluster_data_word()
		time.sleep(0.1)
		r3, r4 = self.alignment_lateral_input(file = file)
		time.sleep(0.1)
		rpst = "initialize={:0b}, stub-data={:0b}, left={:0b}, right={:0b}".format(r1,r2,r3,r4)
		if(r1 and r2 and r3 and r4):
			utils.print_good("->  SSA alignment successfull (" + rpst+ ")")
		else:
			utils.print_error("->  SSA alignment error (" + rpst + ")")
		return r1,r2,r3,r4

	def alignment_cluster_data_phase(self):
		return self.ctrl.phase_tuning()

	def alignment_cluster_data_word(self, display=False):
		tv = [1,3,5,116,118,120]
		self.ctrl.set_lateral_data(left=0, right=0)
		sstatus = {'digital':False, 'analog':False}
		lstatus = {'digital':False, 'analog':False}
		for mode in ['digital', 'analog']:
			if(mode == 'digital'):
				self.inject.digital_pulse(initialise = True)
			elif(mode == 'analog'):
				self.inject.analog_pulse(initialise = True)
			self.readout.cluster_data(initialize = True)

			if(mode == 'digital'):
				self.inject.digital_pulse(tv, initialise = False)
			elif(mode == 'analog'):
				self.inject.analog_pulse(tv, initialise = False)

			for shift in range(-4,6):
				ext = False
				self.readout.cl_shift[mode] = shift
				rp = []
				for i in range(10):
					rp.append(self.readout.cluster_data(initialize = False, shift = 'default'))
					# with shift=='default', the shift value is the one set by "self.readout.cl_shift[mode]"
					if(display):
						print("->  Word alignment. Shift value = {:d}. Read Value = {:s}. Iteration = {:d}.".format(shift, str(list(map(float,rp[-1]))), i))
					if(rp[-4:] == rp[-5:-1]):
						if(list(map(float, rp[-1])) == list(map(float, tv))):
							utils.print_info('->  Stub-data word alignment {m:7s} successfull ({r:d})'.format(m=mode, r=self.readout.cl_shift[mode]))
							self.generic_parameters['cl_word_alignment_{m:s}'.format(m=mode)] = True
							sstatus[mode] = True
							ext = True
							break
						elif(list(map(float, rp[-1])) == list(map(float, []))):
							break
				if(ext): break
			for shift in range(-4,6):
				ext = False
				self.readout.lateral_shift[mode] = shift
				rp = []
				for i in range(10):
					rp.append(self.readout.lateral_data(initialize = False, shift = 'default'))
					# with shift=='default', the shift value is the one set by "self.readout.lateral_shift[mode]"
					if(display):
						print("->  Word alignment. Shift value = {:d}. Read Value = {:s}. Iteration = {:d}.".format(shift, str(list(map(float,rp[-1]))), i))
					if(rp[-4:] == rp[-5:-1]):
						if(list(map(float, rp[-1])) == list(map(float, tv))):
							utils.print_info('->  Lateral-data word alignment {m:7s} successfull ({r:d})'.format(m=mode, r=self.readout.lateral_shift[mode]))
							self.generic_parameters['cl_word_alignment_{m:s}'.format(m=mode)] = True
							lstatus[mode] = True
							ext = True
							break
						elif(list(map(float, rp[-1])) == list(map(float, []))):
							break
				if(ext): break
		if(not sstatus['digital']):
			utils.print_error('->  Stub-data word alignment digital injection error')
			self.generic_parameters['cl_word_alignment_{m:s}'.format(m='digital')] = True
		if(not sstatus['analog']):
			utils.print_error('->  Stub-data word alignment analog injection error')
			self.generic_parameters['cl_word_alignment_{m:s}'.format(m='analog')] = True
		if(not lstatus['digital']):
			utils.print_error('->  Lateral-data word alignment digital injection error')
			self.generic_parameters['lateral_word_alignment_{m:s}'.format(m='digital')] = True
		if(not lstatus['analog']):
			utils.print_error('->  Lateral-data word alignment analog injection error')
			self.generic_parameters['lateral_word_alignment_{m:s}'.format(m='analog')] = True

		#print(self.readout.cl_shift)
		return (sstatus['digital'] and sstatus['analog'])


	def alignment_lateral_input(self, display = False, timeout = 256*3, delay = 4, shift = 'default', init = False, file = "../SSA_Results/TestLogs/Chip-0", filemode = 'w', runname = ''):
		utils.activate_I2C_chip(self.fc7)
		if(not self.cl_word_aligned()):
			self.alignment_cluster_data_word()
		if(isinstance(file, str)):
			fo = open(file + "_Test_LateralInput.csv", filemode)
		if (init): self.init(reset_board = False, reset_chip = False, display = False)
		self.readout.cluster_data(initialize = True)
		alined_left  = False; alined_right = False; cnt = 0;
		self.fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay)
		self.inject.digital_pulse([100, 120, 123], initialise = True)
		#self.ctrl.set_lateral_data(0b00001001, 0)
		while ((alined_left == False) and (cnt < timeout)):
			clusters = self.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == 100 and clusters[1] == 120 and clusters[2] == 123):
					alined_left = True
			utils.ShowPercent(cnt, timeout+1, "Aligning left input line\t\t" + str(clusters) + "           ")
			####### time.sleep(0.1)
			#if  (cnt==256): self.fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+1)
			#elif(cnt==512): self.fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+2)
			self.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			cnt += 1
		utils.ShowPercent(1,1,''); sys.stdout.flush()
		if(alined_left == True):
			utils.print_info("->  Left input line alined                       ")
		else:
			utils.print_error("->  Impossible to align left input data line")
		#self.ctrl.set_lateral_data(0, 0b10100000)
		self.inject.digital_pulse([-2, 0, 10], initialise = True)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):
			clusters = self.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == -2 and clusters[1] == 0 and clusters[2] == 10):
					alined_right = True
			utils.ShowPercent(cnt, timeout+1, "Aligning right input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			self.ctrl.set_lateral_data_phase(5,0)
			time.sleep(0.001)
			cnt += 1
		utils.ShowPercent(1,1,''); sys.stdout.flush()
		if(alined_right == True):
			utils.print_info("->  Right input line alined                       ")
		else:
			utils.print_error("->  Impossible to align right input data line")
		if(isinstance(file, str)):
			fo.write(str(runname) + ' ; ' + str(alined_left) + " ; " + str(alined_right) + ' \n')
			fo.close()
		return [alined_left, alined_right]


	def cl_word_aligned(self):
		if ('cl_word_alignment_digital' in self.generic_parameters) and ('cl_word_alignment_analog' in self.generic_parameters):
			return self.generic_parameters['cl_word_alignment_digital'] and self.generic_parameters['cl_word_alignment_analog']
		else:
			return False

	def set_lateral_sampling_shift(self, left, right):
		SetLineDelayManual(0,0, 9,0,left)
		SetLineDelayManual(0,0,10,0,right)
		self.ctrl.phase_tuning()

	def try_i2c(self, repeat=5):
		return self.ctrl.try_i2c(repeat)

	def try_shift(self, pattern=0xaa):
		time.sleep(0.1); self.ctrl.set_shift_pattern_all(pattern)
		time.sleep(0.1); self.ctrl.activate_readout_shift()
		time.sleep(0.1); self.readout.all_lines(configure=False)
		time.sleep(0.1); self.ctrl.activate_readout_normal()
