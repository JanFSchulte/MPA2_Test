from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

from ssa_methods.ssa_i2c_conf import *
from ssa_methods.ssa_ctrl_base import *
from ssa_methods.ssa_ctrl_strip import *
from ssa_methods.ssa_readout_utility import *


class SSA_ASIC:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.i2c     = I2C
		self.ctrl    = ssa_ctrl_base(I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.strip   = ssa_ctrl_strip(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject  = SSA_inject(I2C, FC7, self.ctrl, self.strip)
		self.readout = SSA_readout(I2C, FC7, self.ctrl, self.strip)
		self.pwr     = pwr
		self.fc7     = FC7

	def reset(self):
		self.ctrl.reset(display=True)

	def resync(self):
		self.ctrl.resync()

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.save_configuration(file = file, display = display)

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.load_configuration(file = file, display = display)

	def init(self, reset_board = False, reset_chip = False, slvs_current = 0b111, edge = "negative", display = True):
		if(display):
			sys.stdout.write("->  \tInitialising..\r")
			sys.stdout.flush()
		if(reset_board):
			fc7.write("ctrl_command_global_reset", 1)
		if(reset_chip):
			self.ctrl.reset(display=False)
		if(display): sleep(0.2)
		else: sleep(0.1)
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			sys.stdout.write("->  \tTuning sampling phases..\r")
			sys.stdout.flush()
		self.ctrl.set_t1_sampling_edge(edge)
		self.ctrl.init_slvs(slvs_current)
		self.ctrl.phase_tuning()
		if(display): sleep(0.2)
		else: sleep(0.1)
		self.ctrl.activate_readout_normal()
		if(display):
			sys.stdout.write("->  \tReady!                  \r")
			sys.stdout.flush()
			sleep(0.2)
			sys.stdout.write("                              \r")
			sys.stdout.flush()
			if(reset_board): print "->  \tReset FC7 Firmware"
			if(reset_chip):  print "->  \tReset SSA Chip"
			print "->  \tInitialised SLVS pads and sampling edges"
			print "->  \tSampling phases tuned"
			print "->  \tActivated normal readout mode"
			self.pwr.get_power(display = True)


	def init_all(self):
		self.init(reset_board = True, reset_chip = False)
