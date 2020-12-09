
#from utilities.tbconfig import *
from utilities.tbsettings import *
from utilities.configure_communication import *
from utilities.fc7_com import *
from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.ssa_test_xray import *
from ssa_methods.ssa_analise_utility import *
from ssa_methods.ssa_calibration import *
from ssa_methods.ssa_seu_utility import *
from ssa_methods.ssa_test_seu import *
from myScripts.BasicADC import *
from ssa_methods.ssa_wp_analyze import *
from ssa_methods.main_ssa_test_1 import *
from ssa_methods.main_ssa_test_2 import *
from ssa_methods.main_ssa_test_3 import *
from ssa_methods.ssa_test_2xSSA2 import *
from ssa_methods.ssa_scanchain_test import *


ipaddr, fc7AddrTable, fc7_if = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)

class SSAwp:
	def __init__(self, index = 0, address = 0):
		self.index   = index
		FC7.set_chip_id(index, address)
		self.i2c           = ssa_i2c_conf(FC7, fc7AddrTable, index=index, address=address)
		self.strip_reg_map = self.i2c.get_strip_reg_map()
		self.peri_reg_map  = self.i2c.get_peri_reg_map()
		self.ana_mux_map   = self.i2c.get_analog_mux_map()
		self.pwr           = ssa_power_utility(self.i2c, FC7)
		self.chip          = SSA_ASIC(index, self.i2c, FC7, self.pwr, self.peri_reg_map, self.strip_reg_map, self.ana_mux_map)
		self.cal           = SSA_cal_utility(self.chip, self.i2c, FC7)
		self.pcbadc        = onboard_adc()
		self.biascal       = ssa_calibration(self.chip, self.i2c, FC7, self.pcbadc, self.peri_reg_map, self.strip_reg_map, self.ana_mux_map)
		self.seuutil       = SSA_SEU_utilities(self.chip, self.i2c, FC7, self.pwr)
		self.measure       = SSA_measurements(self.chip, self.i2c, FC7, self.cal, self.ana_mux_map, self.pwr, self.seuutil, self.biascal)
		self.test          = SSA_test_utility(self.chip, self.i2c, FC7, self.cal, self.pwr, self.seuutil)
		self.toptest       = SSA_test_top(self.chip, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.anl           = SSA_Analise_Test_results(self.toptest, self.test, self.measure, self.biascal)  ## TOP FUNCTION TO CARACTERISE THE SSA
		self.seu           = SSA_SEU(self.chip, self.seuutil, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.init          = self.chip.init
		self.resync        = self.chip.resync
		self.debug         = self.chip.debug
		self.inject        = self.chip.inject
		self.readout       = self.chip.readout
		self.main_test     = SSA_Measurements_All(chip=self, tag="ChipN_{:d}".format(self.index), directory='../SSA_Results/temp/', mode_2xSSA=self.index)
		self.main_test_3   = main_ssa_test_3(chip=self, tag="ChipN_{:d}".format(self.index), directory='../SSA_Results/temp/', mode_2xSSA=self.index)
		self.xray          = SSA_test_xray(self.main_test_3, self.chip, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.scanchain     = SSA_scanchain_test(self.chip, self.i2c, FC7, self.pwr)

	def enable(self):  FC7.enable_chip(self.index)
	def disable(self): FC7.disable_chip(self.index)
	def reset(self, display=True): self.chip.reset(display=display)

ssa0 = SSAwp(0, 0b001)
ssa1 = SSAwp(1, 0b111)
ssa  = ssa0

t2xSSA2 = Test_2xSSA2(ssa0, ssa1, FC7)

def reset_fc7():
	FC7.write("ctrl_command_global_reset", 1);

def set_clock(val = 'internal'):
	ssa0.pwr.set_clock_source(val)
	#sleep(0.1);
	#ssa0.chip.init(reset_board = False, reset_chip = False, display = True)

def ssa_on():
	utils.activate_I2C_chip(FC7)
	sleep(0.1);  ssa_pwr.set_supply('on', display=False)
	sleep(0.1);  ssa_pwr.set_clock_source('internal')
	sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)
