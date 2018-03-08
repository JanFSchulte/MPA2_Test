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
		self.ctrl              = ssa_ctrl_base(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.strip             = ssa_ctrl_strip(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject            = SSA_inject(I2C, FC7, self.ctrl, self.strip)
		self.readout           = SSA_readout(I2C, FC7, self.ctrl, self.strip)
	
	def init_all(self, slvs_current = 1, edge = "negative"):
		sys.stdout.write("->  Initialising..\r")
		sys.stdout.flush()
		reset()
		utils.print_enable(False)
		activate_I2C_chip()
		utils.print_enable(True)
		sys.stdout.write("->  Tuning sampling phases..\r")
		sys.stdout.flush()
		self.ctrl.set_t1_sampling_edge(edge)
		self.ctrl.init_slvs(slvs_current)
		self.ctrl.phase_tuning()
		time.sleep(0.5)
		self.ctrl.activate_readout_normal()
		sys.stdout.write("->  Ready!                  \r")
		sys.stdout.flush()
		time.sleep(0.5)
		sys.stdout.write("                            \n")
		sys.stdout.flush()














