from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

from mpa_methods.mpa_i2c_conf import *
from mpa_methods.mpa_ctrl_base import *
from mpa_methods.mpa_ctrl_strip import *
from mpa_methods.mpa_readout_utility import *


class MPA_ASIC:

	def __init__(self, I2C, FC7, pwr, mpa_peri_reg_map, mpa_strip_reg_map):
		self.i2c     	= I2C
		self.ctrl_base  = mpa_ctrl_base(I2C, FC7, pwr, mpa_peri_reg_map, mpa_strip_reg_map)
		self.ctrl_pix   = mpa_ctrl_pix(I2C, FC7, pwr, mpa_peri_reg_map, mpa_strip_reg_map)
		self.inject  	= mpa_inject(I2C, FC7, self.ctrl_base, self.ctrl_pix)
		self.readout 	= mpa_readout(I2C, FC7, self.ctrl_base, self.ctrl_pix)
		self.pwr     	= pwr
		self.fc7     	= FC7

	def reset(self, display=True):
		self.ctrl.reset(display = display)

	def resync(self):
		self.ctrl.resync()

	def disable(self, display=True):
		self.pwr._disable(display = display)

	def enable(self, display=True):
		self.pwr._enable(display = display)

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def save_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
		self.ctrl.save_configuration(file = file, display = display)

	def load_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
		self.ctrl.load_configuration(file = file, display = display)

	def init(self, reset_board = False, reset_chip = False, slvs_current = 0b111, edge = "negative", display = True, read_current = False):
		if(display):
			sys.stdout.write("->  \tInitialising..\r")
			sys.stdout.flush()
		if(reset_board):
			fc7.write("ctrl_command_global_reset", 1)
		if(reset_chip):
			self.ctrl.reset(display=False)
		utils.activate_I2C_chip()
		if(display): sleep(0.2)
		else: sleep(0.1)
		if(display):
			sys.stdout.write("->  \tTuning sampling phases..\r")
			sys.stdout.flush()
		self.ctrl.set_t1_sampling_edge(edge)
		self.ctrl.init_slvs(slvs_current)
		rt = self.ctrl.phase_tuning()
		if(display): sleep(0.2)
		else: sleep(0.1)
		self.ctrl.activate_readout_normal()
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
			if(read_current):
				self.pwr.get_power(display = True)
		return rt


	def init_all(self):
		self.init(reset_board = True, reset_chip = False)
