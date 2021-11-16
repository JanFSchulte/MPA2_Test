#from utilities.tbconfig import *
from utilities.tbsettings import *
from utilities.configure_communication import *
from utilities.fc7_com import *
from utilities.i2c_conf import *
from utilities.power_utility import *
from myScripts.BasicADC import *

from myScripts.Instruments_Keithley_Multimeter_2000_GPIB import *
from myScripts.Instruments_Keithley_Multimeter_7510_LAN import *
from myScripts.Instruments_Keithley_Sourcemeter_2410_GPIB import *

# SSA Utilities
from ssa_methods.ssa import *
from ssa_methods.ssa_cal_utility import *
from ssa_methods.ssa_test_utility import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *
from ssa_methods.ssa_measurements import *
from ssa_methods.ssa_analise_utility import *
from ssa_methods.ssa_calibration import *
from ssa_methods.ssa_seu_utility import *

# SSA Test procedures
from ssa_methods.ssa_test_climatic_chamber import *
from ssa_methods.main_ssa_test_1 import *
from ssa_methods.main_ssa_test_2 import *
from ssa_methods.main_ssa_test_3 import *
from ssa_methods.ssa_test_2xSSA2 import *
from ssa_methods.ssa_scanchain_test import *
from ssa_methods.ssa_test_xray import *
from ssa_methods.ssa_wp_analyze import *
from ssa_methods.ssa_test_seu import *

# MPA Utilities
#from mpa_methods.mpa import *
from mpa_methods.mpa import *
from mpa_methods.mpa_cal_utility import *
from mpa_methods.mpa_test_utility import *
from mpa_methods.mpa_data_chain import *
from mpa_methods.mpa_bias_utility import *
from mpa_methods.mpa_scanchain_test import *

# MPA2 Test procedures
from mpa_methods.mpa_main_test import *


ipaddr, fc7AddrTable, fc7_if = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)
#FC7.activate_I2C_chip(verbose=0)

class SSAwp:
    def __init__(self, index = 0, address = 0):
        self.index   = index

        # init comms to testbench components (FC7, I2C register access)
        FC7.set_chip_id(index, address)
        self.i2c           = I2CConf(FC7, fc7AddrTable, index="SSA{:0d}".format(index), address=address)
        self.strip_reg_map = self.i2c.get_strip_reg_map()
        self.peri_reg_map  = self.i2c.get_peri_reg_map()
        self.ana_mux_map   = self.i2c.get_analog_mux_map()

        # init base chip config, utilities and s_curve measuring
        self.pwr           = PowerUtility(self.i2c, FC7, "SSA")
        self.chip          = SSA_ASIC(index, self.i2c, FC7, self.pwr, self.peri_reg_map, self.strip_reg_map, self.ana_mux_map)
        self.cal           = SSA_cal_utility(self.chip, self.i2c, FC7)
        self.pcbadc        = onboard_adc()

        # init test injection methods
        self.biascal       = ssa_calibration(self.chip, self.i2c, FC7, self.pcbadc, self.peri_reg_map, self.strip_reg_map, self.ana_mux_map)
        self.seuutil       = SSA_SEU_utilities(self.chip, self.i2c, FC7, self.pwr)
        self.test          = SSA_test_utility(self.chip, self.i2c, FC7, self.cal, self.pwr, self.seuutil)

        # measure inits ssa_measurements_adc/fe/pwr
        self.measure       = SSA_measurements(self.chip, self.i2c, FC7, self.cal, self.ana_mux_map, self.pwr, self.seuutil, self.biascal)

        # init top level test suites
        self.main_test_1   = main_ssa_test_1(self.chip, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test, self.measure.fe)
        self.seu           = SSA_SEU(self.chip, self.seuutil, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test)
        self.main_test_2   = main_ssa_test_2(chip=self, tag="ChipN_{:d}".format(self.index), directory='../SSA_Results/temp/', mode_2xSSA=self.index)
        self.main_test_3   = MainTests(chip=self, tag="ChipN_{:d}".format(self.index), directory='../SSA_Results/temp/', mode_2xSSA=self.index)
        self.xray          = SSA_test_xray(self.main_test_3, self.chip, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test)
        self.climatic      = SSA_test_climatic_chamber(self.main_test_3, self.chip, self.i2c, FC7, self.cal, self.biascal, self.pwr, self.test)
        self.scanchain     = SSA_scanchain_test(self.chip, self.i2c, FC7, self.pwr)

        # init top function to characterise SSA
        self.anl           = SSA_Analise_Test_results(self.main_test_1, self.test, self.measure.fe, self.biascal)

        self.init          = self.chip.init
        self.resync        = self.chip.resync
        self.debug         = self.chip.debug
        self.inject        = self.chip.inject
        self.readout       = self.chip.readout
        self.ctrl          = self.chip.ctrl
        self.analog        = self.chip.analog

    def enable(self):  FC7.enable_chip(self.index)
    def disable(self): FC7.disable_chip(self.index)
    def reset(self, display=True): self.chip.reset(display=display)



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
        self.test          = mpa_test_utility(self.chip, self.i2c, FC7)
        self.dc            = MPATestDataChain(self.chip, self.i2c, FC7)

        self.init          = self.chip.init
        self.inject        = self.chip.inject
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
            
    def on():
        utils.activate_I2C_chip(FC7)
        time.sleep(0.1);  pwr.set_supply('on', display=False)
        time.sleep(0.1);  pwr.set_clock_source('internal')
        time.sleep(0.1);  ssa.init(reset_board = True, reset_chip = True, display = True)

    def off():
        utils.activate_I2C_chip(FC7)
        self.pwr.set_supply('off')

    def init():
        return self.chip.init(reset_board = True, reset_chip = False, display = True)

    def reset_fc7():
        FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

    def reset_mpa():
        self.chip.reset()

    def set_clock(val = 'internal'):
        self.pwr.set_clock_source(val)
        time.sleep(0.1);  ssa.init(reset_board = False, reset_chip = False, display = True)

ssa0 = SSAwp(0, 0b000)
#ssa1 = SSAwp(1, 0b111)
ssa  = ssa0
mpa  = MPAwp(address = 0b000)

read_regs     = mpa.chip.rdo.read_regs
read_L1       = mpa.chip.rdo.read_L1
read_stubs    = mpa.chip.rdo.read_stubs

#t2xSSA2 = Test_2xSSA2(ssa0, ssa1, FC7)

def reset_fc7():
    FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

def set_clock(val = 'internal'):
    ssa0.pwr.set_clock_source(val)
    #sleep(0.1);
    #ssa0.chip.init(reset_board = False, reset_chip = False, display = True)
