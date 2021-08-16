from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
#from mpa_methods.mpa_i2c_conf import *
from mpa_methods.mpa_ctrl_base import *
from mpa_methods.mpa_ctrl_pix import *
from mpa_methods.mpa_inject_utility import *

import time

class MPA_ASIC:
	def __init__(self, I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map):
		self.i2c     	= I2C
		self.ctrl_base  = mpa_ctrl_base(I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map)
		self.ctrl_pix   = mpa_ctrl_pix(I2C, FC7, pwr, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map)
		self.inject  	= mpa_inject(I2C, FC7, self.ctrl_base, self.ctrl_pix)
		self.pwr     	= pwr
		self.fc7     	= FC7
	def reset(self, display=True):
		self.ctrl_base.reset(display = display)
	def resync(self):
		self.ctrl_base.resync()
	def disable(self, display=True):
		self.pwr._disable(display = display)
	def enable(self, display=True):
		self.pwr._enable(display = display)
#	def debug(self, value = True):
#		self.i2c.set_debug_mode(value)
#		self.i2c.set_readback_mode()
#
#	def save_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
#		self.ctrl.save_configuration(file = file, display = display)
#
#	def load_configuration(self, file = '../MPA_Results/Configuration.csv', display=True):
#		self.ctrl.load_configuration(file = file, display = display)
	def init(self, reset_board = False, reset_chip = False, slvs_current = 0b001, edge = "negative", display = True, read_current = False):
		if(display):
			sys.stdout.write("->  \tInitialising..\r")
			sys.stdout.flush()
		if(reset_board):
			self.fc7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1)
		if(reset_chip):
			self.ctrl_base.reset(display=False)
		utils.activate_I2C_chip(self.fc7)
		if(display): time.sleep(0.2)
		else: time.sleep(0.1)
		if(display):
			sys.stdout.write("->  \tTuning sampling phases..\r")
			sys.stdout.flush()
		self.ctrl_base.set_sampling_edge(edge); time.sleep(0.2)
		self.ctrl_base.init_slvs(slvs_current); time.sleep(0.2)
		rt = self.ctrl_base.align_out_all()
		if(display): time.sleep(0.2)
		else: time.sleep(0.1)
		self.ctrl_base.activate_sync()
		if(display):
			sys.stdout.write("->  \tReady!                  \r")
			sys.stdout.flush()
			time.sleep(0.2)
			sys.stdout.write("                              \r")
			sys.stdout.flush()
			if(reset_board): print("->  \tReset FC7 Firmware")
			if(reset_chip):  print("->  \tReset SSA Chip")
			print("->  \tInitialised SLVS pads and sampling edges")
			print("->  \tSampling phases tuned")
			print("->  \tActivated normal readout mode")
			if(read_current):
				self.pwr.get_power(display = True)
		return rt
	def init_all(self):
		self.init(reset_board = True, reset_chip = False)

	def init_probe(self, reset_chip = True, slvs_current = 0b001, edge = "negative"):
		sys.stdout.write("->  \tInitialising..\r")
		sys.stdout.flush()
		if(reset_chip):
			self.ctrl_base.reset(display=False)
		utils.activate_I2C_chip(self.fc7)
		sys.stdout.write("->  \tTuning sampling phases..\r")
		sys.stdout.flush()
		self.ctrl_base.set_sampling_edge(edge);
		self.ctrl_base.init_slvs(slvs_current);
		rt = self.ctrl_base.align_out_all()
		if (not rt):
			print("->  \tRepeating alignment...")
			rt = self.ctrl_base.align_out_all()
		self.ctrl_base.activate_sync()
		print("->  \tInitialised SLVS pads and sampling edges")
		print("->  \tSampling phases tuned")
		print("->  \tActivated normal readout mode")
		return rt
