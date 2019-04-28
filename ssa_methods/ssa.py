from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

from ssa_methods.ssa_i2c_conf import *
from ssa_methods.ssa_ctrl_base import *
from ssa_methods.ssa_ctrl_strip import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *


class SSA_ASIC:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.i2c     = I2C
		self.ctrl    = ssa_ctrl_base(I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.strip   = ssa_ctrl_strip(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject  = SSA_inject(I2C, FC7, self.ctrl, self.strip)
		self.readout = SSA_readout(I2C, FC7, self.ctrl, self.strip)
		self.pwr     = pwr
		self.fc7     = FC7

	def reset(self, display=True):
		self.ctrl.reset(display = display)

	def resync(self):
		self.ctrl.resync()

	def disable(self, display=True):
		self.pwr._disable_ssa(display = display)

	def enable(self, display=True):
		self.pwr._enable_ssa(display = display)

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.save_configuration(file = file, display = display)

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.load_configuration(file = file, display = display)

	def init(self, reset_board = False, reset_chip = False, slvs_current = 0b111, edge = "negative", display = True, read_current = False):
		if(display):
			sys.stdout.write("->  \tInitialising..\r")
			sys.stdout.flush()
		if(reset_board):
			fc7.write("ctrl_command_global_reset", 1)
			sleep(0.3);
			if(display): utils.print_info("->  \tReset FC7 Firmware")
		if(reset_chip):
			self.ctrl.reset(display=False)
			sleep(0.3);
			if(display): utils.print_info("->  \tReset SSA Chip")
		utils.activate_I2C_chip()
		sleep(0.2)
		if(display):
			sys.stdout.write("->  \tTuning sampling phases..\r")
			sys.stdout.flush()
		sleep(0.1); self.ctrl.set_t1_sampling_edge(edge)
		sleep(0.1); self.ctrl.init_slvs(slvs_current)
		sleep(0.1); rt = self.ctrl.phase_tuning()
		if(rt):
			if(display): utils.print_good("->  \tShift register mode ok")
			if(display): utils.print_good("->  \tSampling phases tuned")
		else:
			if(display): utils.print_error("->  \tImpossible to complete phase tuning")
		sleep(0.2); self.ctrl.activate_readout_normal()
		sleep(0.1); self.ctrl.activate_readout_normal()
		if(display):
			utils.print_info("->  \tActivated normal readout mode");
			sys.stdout.write("->  \tReady!                  \r")
			sys.stdout.flush()
			sleep(0.2)
			if(read_current):
				self.pwr.get_power(display = True)
		return rt


	def init_all(self):
		self.init(reset_board = True, reset_chip = False)

	def set_lateral_sampling_shift(self, left, right):
		SetLineDelayManual(0,0, 9,0,left)
		SetLineDelayManual(0,0,10,0,right)
		self.ctrl.phase_tuning()

	def cl_word_alignment(self):
		tv = [10,20,30,40,50,60,70,80]
		for shift in range(-4,5):
			self.readout.cl_shift = shift
			self.inject.digital_pulse(tv)
			rp = self.readout.cluster_data()
			if(rp == tv):
				utils.print_info('->\tCluster-data word alignment successfull ({:d})'.format(self.readout.cl_shift))
				return True
		utils.print_error('->\tCluster-data word alignment error')
		return False
