from utilities.configure_communication import *
from utilities.fc7_com import *
ipaddr, fc7_if, fc7AddrTable = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)
#FC7.activate_I2C_chip(verbose=0)

#from utilities.tbconfig import *
from utilities.tbsettings import *
from utilities.i2c_conf import *
from utilities.power_utility import *

from myScripts.BasicADC import *
from myScripts.BasicMultimeter import *
#from myScripts.keithley2410 import *

#from myScripts.Instruments_Keithley_Multimeter_2000_GPIB import *
#from myScripts.Instruments_Keithley_Multimeter_7510_LAN import *
#from myScripts.Instruments_Keithley_Sourcemeter_2410_GPIB import *

# SSA Utilities
#from ssa_methods.ssa import *
#from ssa_methods.ssa_cal_utility import *
#from ssa_methods.ssa_test_utility import *
#from ssa_methods.ssa_readout_utility import *
#from ssa_methods.ssa_inject_utility import *
#from ssa_methods.ssa_measurements import *
#from ssa_methods.ssa_analise_utility import *
#from ssa_methods.ssa_calibration import *
#from ssa_methods.ssa_seu_utility import *

# SSA Test procedures
#from ssa_methods.ssa_test_climatic_chamber import *
#from ssa_methods.main_ssa_test_1_old import *
#from ssa_methods.main_ssa_test_2_old import *
#from ssa_methods.main_ssa_test_slow  import *
#from ssa_methods.main_ssa_test_fast  import *
#from ssa_methods.ssa_test_2xSSA2 import *
#from ssa_methods.ssa_scanchain_test import *
#from ssa_methods.ssa_test_xray import *
#from ssa_methods.ssa_wp_analyze import *
#from ssa_methods.ssa_test_seu import *

# MPA Utilities
#from mpa_methods.mpa import *
from mpa_methods.mpa import *
from mpa_methods.mpa_cal_utility import *
from mpa_methods.mpa_test_utility import *
from mpa_methods.mpa_data_chain import *
from mpa_methods.mpa_bias_utility import *
from mpa_methods.mpa_scanchain_test import *
#from mpa_methods.mpa_measurements import MPAMeasurements
#from mpa_methods.mpa_fast_injection_test import MPAFastInjectionMeasurement

# MPA2 Test procedures
from mpa_methods.mpa_testing_routine import *

class MPAwp:
    def __init__(self, index = "MPA", address = 0):
        ##FC7.set_chip_id(index, address)
        self.index         = index
        self.i2c           = I2CConf(FC7, fc7AddrTable, index=index, address=address)

        self.peri_reg_map  = self.i2c.get_peri_reg_map()
        self.row_reg_map   = self.i2c.get_row_reg_map()
        self.pixel_reg_map = self.i2c.get_pixel_reg_map()

        self.pwr           = PowerUtility(self.i2c, FC7, index)
        self.chip          = MPA_ASIC(self.i2c, FC7, self.pwr, self.peri_reg_map, self.row_reg_map, self.pixel_reg_map)
        self.cal           = mpa_cal_utility(self.chip, self.i2c, FC7)

        # base functionality tests
        self.test          = mpa_test_utility(self.chip, self.i2c, FC7)

        self.init          = self.chip.init
        self.inject        = self.chip.inject

        # faster access to readout methods
        self.read_regs     = self.chip.rdo.read_regs
        self.read_L1       = self.chip.rdo.read_L1
        self.read_Stubs    = self.chip.rdo.read_stubs
        self.data_dir = "../cernbox_anvesh/MPA_test_data/"
        self.scanchain = MPA_scanchain_test(self.chip, self.i2c, FC7, self.pwr)

        try:
            multimeter = keithley_multimeter()
            self.bias = mpa_bias_utility(self.chip, self.i2c, FC7, multimeter, self.peri_reg_map, self.row_reg_map, self.pixel_reg_map)
        except ImportError:
            self.bias = False
            print("- Impossible to access GPIB instruments")

        # additional characterizations
#        self.dc            = MPATestDataChain(self.chip, self.i2c, FC7)
#        self.measure       = MPAMeasurements(self.chip, self.bias)

        # radiation testing
        #self.fastinj       = MPAFastInjectionMeasurement(self.chip, self.bias, self.test, "../MPA2_RadiationResults/.")

    def on(self):
        utils.activate_I2C_chip(FC7)
        time.sleep(0.1);  pwr.set_supply('on', display=False)
        time.sleep(0.1);  pwr.set_clock_source('internal')
        time.sleep(0.1);  self.chip.init(reset_board = True, reset_chip = True, display = True)

    def off(self):
        utils.activate_I2C_chip(FC7)
        self.pwr.set_supply('off')

    def init(self):
        return self.chip.init(reset_board = True, reset_chip = False, display = True)

    def reset_fc7(self):
        FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

    def reset_mpa(self):
        self.chip.reset()

    def set_clock(self,val = 'internal'):
        self.pwr.set_clock_source(val)
        time.sleep(0.1);  self.chip.init(reset_board = False, reset_chip = False, display = True)

#ssa0 = SSAwp(0, 0b000)
#ssa1 = SSAwp(1, 0b111)
#ssa  = ssa0
mpa  = MPAwp(address = 0b000)
print("Start reset")
mpa.reset_mpa()
print("Stop reset")

#read_regs     = mpa.chip.rdo.read_regs
#read_L1       = mpa.chip.rdo.read_L1
#read_stubs    = mpa.chip.rdo.read_stubs

#t2xSSA2 = Test_2xSSA2(ssa0, ssa1, FC7)

def reset_fc7():
    FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

def set_clock(val = 'internal'):
    ssa0.pwr.set_clock_source(val)
    #sleep(0.1);
    #ssa0.chip.init(reset_board = False, reset_chip = False, display = True)
