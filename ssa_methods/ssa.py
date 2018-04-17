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

	def __init__(self, I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.i2c               = I2C
		self.ctrl              = ssa_ctrl_base(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.strip             = ssa_ctrl_strip(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject            = SSA_inject(I2C, FC7, self.ctrl, self.strip)
		self.readout           = SSA_readout(I2C, FC7, self.ctrl, self.strip)

	def reset(self):
		self.ctrl.reset()
		self.ctrl.set_t1_sampling_edge("negative")

	def resync(self):
		self.ctrl.resync()

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def init(self):
		activate_I2C_chip()
		self.ctrl.init_slvs(0b110)
		self.ctrl.set_t1_sampling_edge("negative")
		self.ctrl.phase_tuning()
		print "->  \tInitialised SLVS pads and sampling edges"

	def init_all(self, slvs_current = 0b110, edge = "negative", display = True):
		if(display):
			sys.stdout.write("->  Initialising..\r")
			sys.stdout.flush()
		fc7.write("ctrl_command_global_reset", 1)
		if(display):
			sleep(0.5)
		else:
			sleep(0.1)
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		if(display):
			sys.stdout.write("->  Tuning sampling phases..\r")
			sys.stdout.flush()
		self.ctrl.set_t1_sampling_edge(edge)
		self.ctrl.init_slvs(slvs_current)
		self.ctrl.phase_tuning()
		if(display):
			sleep(0.5)
		else:
			sleep(0.1)
		self.ctrl.activate_readout_normal()
		if(display):
			sys.stdout.write("->  Ready!                  \r")
			sys.stdout.flush()
			sleep(0.5)
			sys.stdout.write("                            \r")
			sys.stdout.flush()
		else:
			sleep(0.1)
		if(display):
			print "->  \tReset FC7 Firmware"
			print "->  \tInitialised SLVS pads and sampling edges"
			print "->  \tSampling phases tuned"
			print "->  \tActivated normal readout mode"
			#sys.stdout.write("                            \n")
			#sys.stdout.flush()
