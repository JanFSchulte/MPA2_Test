from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.logs_utility import *
from collections import OrderedDict

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class main_mpa_test():

    def __init__(self, chip, I2C, fc7, cal, biascal, pwr, test, measure, dir_path = False):
        self.chip = chip;	  self.I2C = I2C;	self.fc7 = fc7;
        self.cal = cal;   self.pwr = pwr;
        self.test = test;

        self.summary = results()
        self.runtest = RunTest('default')
        self.config_file = ''; self.dvdd = 1.05; self.pvdd = 1.20; #for the offset of the board
        self.filename = False

        if dir_path: self.dir_path = dir_path
        if measure: self.measure = measure
        if biascal: self.biascal = biascal

        self.configure_tests()

    ##############################################################################
    def run_characterization(self):
        self.initialise(filename)
        self.test_routine_main(filename, "")

    ##############################################################################
    def configure_tests(self, runtest = 'default'):

        if(runtest == 'default'):
            self.runtest.set_enable('memory_vs_voltage', 'ON')
            self.runtest.set_enable('Power', 'ON')
        #if(runtest == 'default'):
        #    self.runtest.set_enable('Lateral_In', 'ON')
        #    self.runtest.set_enable('Cluster_Data', 'ON')
        #    self.runtest.set_enable('Pulse_Injection', 'ON')
        #    self.runtest.set_enable('Cluster_Data2', 'ON')
        #    self.runtest.set_enable('Memory_1', 'ON')
        #    self.runtest.set_enable('Memory_2', 'ON')
        #    self.runtest.set_enable('L1_data', 'ON')
        #    self.runtest.set_enable('memory_vs_voltage', 'OFF')
        #    self.runtest.set_enable('noise_baseline', 'OFF')
        #    self.runtest.set_enable('trim_gain_offset_noise', 'ON')
        #    self.runtest.set_enable('gain_offset_noise', 'OFF')
        #    self.runtest.set_enable('threshold_spread', 'OFF')
        #    self.runtest.set_enable('Power', 'ON')
        #    self.runtest.set_enable('Bias', 'ON')
        #    self.runtest.set_enable('Bias_THDAC', 'ON')
        #    self.runtest.set_enable('Bias_CALDAC', 'ON')
        #    self.runtest.set_enable('Configuration', 'ON')
        #else:
        #    self.runtest = runtest

    ##############################################################################

    def initialise(self, file = False, plot = False):
        if (isinstance(file, str)):
            self.filename = file
        filename = self.filename
        if (not isinstance(filename, str)):
            print("Log file name not setup. Format ssa_toptest.initialise(filename, [plot])")
            return
        filename = self.dir_path + filename
        dir = filename[:filename.rindex(os.path.sep)]
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.chip.init(reset_board = True, reset_chip = True)
        
        self.biascal.calibrate_to_nominals(naverages=1)
        self.measure.scurve_trim(plot = plot, filename = file + '_Init')
        self.config_file = filename + '_Configuration_Init.scv'
        self.chip.save_configuration(self.config_file, display=False)

    ##############################################################################
    def test_routine_main(self, filename, runname = 'RUN1'):
        print('\n\n\n\n')
        print('========================================================')
        print('     STARTING TEST   ' + str(runname))
        print('========================================================')
        print('\n\n')
        time_init = time.time()
        #fo = "../SSA_Results/X-Ray/" + runname + '_' + utils.date_time() + '_X-Ray_'
        #if(self.config_file == ''):
        fo = self.dir_path + filename
        dir = fo[:fo.rindex(os.path.sep)]
        if not os.path.exists(dir):
            os.makedirs(dir)
        #self.config_file = fo + '_Configuration_Init.scv'
        
        self.pwr.set_dvdd(self.dvdd)
        self.pwr.set_pvdd(self.pvdd)
        self.chip.init(reset_board = True, reset_chip = False)

        #self.chip.load_configuration(self.config_file, display = False)
        #self.test_routine_parameters(filename = fo, runname = runname)
        #self.test_routine_analog(filename = fo, runname = runname)
        self.test_routine_digital(filename = fo, runname = runname)
        #self.test_routine_dacs(filename = fo, runname = runname)

        self.summary.display(runname)
        self.summary.save(fo, runname)
        
        print('\n\n')
        print('========================================================')
        print("->  END TEST \tRun time = {:7.2f}".format( (time.time()-time_init) ) )
        print('========================================================')
        print('\n\n\n\n')
        #self.chip.init(reset_board = True, reset_chip = True)
        #self.chip.load_configuration(self.config_file, display = False)
        
        self.chip.init(reset_board = True, reset_chip = False, display = False)

    ##############################################################################
    def test_routine_parameters(self, filename = 'default', runname = '  0Mrad'):
        filename = self.summary.get_file_name(filename)
        wd = 0
        while self.runtest.is_active('Power') and wd < 3:
            try:
                [Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.pwr.get_power(display=True, return_all = True)
                self.summary.set('P_DVDD', Pd, 'mW', '',  runname)
                self.summary.set('P_AVDD', Pa, 'mW', '',  runname)
                self.summary.set('P_PVDD', Pp, 'mW', '',  runname)
                self.summary.set('V_DVDD', Vd, 'mW', '',  runname)
                self.summary.set('V_AVDD', Va, 'mW', '',  runname)
                self.summary.set('V_PVDD', Vp, 'mW', '',  runname)
                self.summary.set('I_DVDD', Id, 'mW', '',  runname)
                self.summary.set('I_AVDD', Ia, 'mW', '',  runname)
                self.summary.set('I_PVDD', Ip, 'mW', '',  runname)
                break
            except:
                print("X>  \tError in Power test. Reiterating.")
                wd +=1
        wd = 0

        #while self.runtest.is_active('Bias') and wd < 3:
        #    try:
        #        r1 = self.biascal.measure_bias(return_data=True)
        #        for i in r1:
        #            self.summary.set( i[0], i[1], 'mV', '',  runname)
        #        break
        #    except:
        #        print("X>  \tError in Bias test. Reiterating.")
        #        wd +=1
        #wd = 0
        #while self.runtest.is_active('Configuration') and wd < 3:
        #    try:
        #        self.chip.save_configuration(self.dir_path + filename + '_Configuration_' + str(runname) + '.scv', display=False)
        #        break
        #    except:
        #        print("X>  \tError in reading Config regs. Reiterating.")
        #        wd +=1
        #wd = 0
#

    def print_exception(self, text='Exception'):
        utils.print_warning(text)
        self.exc_info = sys.exc_info()
        utils.print_warning("======================")
        exeptinfo = traceback.format_exception(*self.exc_info )
        for extx in exeptinfo:
            utils.print_warning(extx)
        utils.print_warning("======================")
