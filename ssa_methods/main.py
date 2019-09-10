from ssa_methods.ssa import *
from ssa_methods.ssa_power_utility import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.main_ssa_test_1 import *
from ssa_methods.ssa_test_xray import *
from ssa_methods.ssa_analise_utility import *
from ssa_methods.ssa_fc7_com import *
from ssa_methods.ssa_calibration import *
from ssa_methods.ssa_seu_utility import *
from ssa_methods.ssa_test_seu import *
from myScripts.BasicADC import *
from ssa_wp_analyze import *

try:
	multimeter = keithley_multimeter()
except ImportError:
	multimeter = False
	print "- Impossible to access GPIB instruments"

class SSAwp:
	def __init__(self, index = 0):
		self.index   = index
		self.FC7     = ssa_fc7_com(fc7)
		self.i2c     = ssa_i2c_conf(index=index)
		self.pwr     = ssa_power_utility(self.i2c, self.FC7)
		self.chip    = SSA_ASIC(index, self.i2c, self.FC7, self.pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.cal     = SSA_cal_utility(self.chip, self.i2c, self.FC7)
		self.pcbadc  = onboard_adc()
		self.biascal = ssa_calibration(self.chip, self.i2c, self.FC7, multimeter, self.pcbadc, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.measure = SSA_measurements(self.chip, self.i2c, self.FC7, self.cal, analog_mux_map, self.pwr, self.biascal)
		self.seuutil = SSA_SEU_utilities(self.chip, self.i2c, self.FC7, self.pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.test    = SSA_test_utility(self.chip, self.i2c, self.FC7, self.cal, self.pwr, self.seuutil)
		self.toptest = SSA_test_top(self.chip, self.i2c, self.FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.xray    = SSA_test_xray(self.toptest, self.chip, self.i2c, self.FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.anl     = SSA_Analise_Test_results(self.toptest, self.test, self.measure, self.biascal)  ## TOP FUNCTION TO CARACTERISE THE SSA
		self.seu     = SSA_SEU(self.chip, self.seuutil, self.i2c, self.FC7, self.cal, self.biascal, self.pwr, self.test, self.measure)
		self.init    = self.chip.init
		self.reset   = self.chip.reset
		self.resync  = self.chip.resync
		self.enable  = self.chip.enable
		self.disable = self.chip.disable
		self.debug   = self.chip.debug

ssa0 = SSAwp(0)
ssa1 = SSAwp(1)
ssa = ssa0

def reset_fc7():
	FC7.write("ctrl_command_global_reset", 1);

def set_clock(val = 'internal'):
	SSA0.pwr.set_clock_source(val)
	sleep(0.1);
	SSA0.ssa.init(reset_board = False, reset_chip = False, display = True)

def ssa_on():
	utils.activate_I2C_chip()
	sleep(0.1);  ssa_pwr.set_supply('on', display=False)
	sleep(0.1);  ssa_pwr.set_clock_source('internal')
	sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)


#utils.activate_I2C_chip()
