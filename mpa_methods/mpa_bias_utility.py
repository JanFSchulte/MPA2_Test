from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

class mpa_bias_utility():

    def __init__(self, mpa, I2C, fc7, multimeter, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map):
        self.mpa = mpa
        self.I2C = I2C
        self.fc7 = fc7
        self.multimeter = multimeter
        self.mpa_peri_reg_map = mpa_peri_reg_map
        self.mpa_row_reg_map = mpa_row_reg_map
        self.mpa_pixel_reg_map = mpa_pixel_reg_map
        self.initialised = False
        self.nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
        self.DAC_val = [15, 15, 15, 15, 15]
        self.exp_val = [0.082, 0.082, 0.108, 0.082, 0.082]
        self.cal_precision = 0.05
        self.measure_avg = 1

        self.set_gpib_address(16)
        self.__multimeter_gpib_initialise()

    def set_gpib_address(self, address):
        self.gpib_address = address

    def __multimeter_gpib_initialise(self):
        # self.multimeterinst = self.multimeter.init_keithley(avg = self.measure_avg, address = self.gpib_address)
        self.multimeterinst = self.multimeter.connect(avg = self.measure_avg, address = self.gpib_address)
        self.initialised = True

    def DAC_linearity(self, block, point, bit, inst, step = 1, plot = 1, verbose = 1):
        DAC = self.nameDAC[point] + str(block)
        test = "TEST" + str(block)
        self.I2C.peri_write('TESTMUX',0b00000001 << block)
        self.I2C.peri_write(test, 0b00000001 << point)
        data = np.zeros(1 << bit, dtype=np.float)
        if verbose: print("DAC: ", DAC)
        for i in range(0, 1 << bit, step):
            self.I2C.peri_write(DAC, i)
            data[i] = self.multimeter.measure()
            if (i % 10 == 0):
                if verbose: print("Done point ", i, " of ", 1 << bit)
        if plot:
            plt.plot(list(range(0,1 << bit)), data,'o')
            plt.xlabel('DAC voltage [LSB]'); plt.ylabel('DAC value [mV]'); plt.show()
        return data

    def measure_DAC_testblocks(self, point, bit, step = 1, plot = 1,print_file = 0, filename = "../cernbox/MPA_Results/DAC_", verbose = 1):
        inst = self.multimeter.init_keithley(avg = self.measure_avg, address = self.gpib_address)
        data = np.zeros((7, 1 << bit), dtype=np.float)
        for i in range(0,7):
            data[i] = self.DAC_linearity(block = i, point = point, bit = bit, inst = inst,step = step, plot = 0, verbose = verbose)
            if plot: plt.plot(list(range(0,1 << bit)), data[i, :],'o', label = "Test Block #" + str(i))
        if plot: plt.xlabel('DAC voltage [LSB]'); plt.ylabel('DAC value [mV]');plt.legend(); plt.show()
        if print_file: CSV.ArrayToCSV (data, str(filename) + "_TP" + str(point) + ".csv")
        return data

    def measure_DAC_chip(self, chip = "Test", print_file = 1, filename = "../cernbox/MPA_Results/ChipDAC_"):
        for i in range(0,7):
            if (i < 5): bit = 5
            else: 		bit = 8
            measure_DAC_testblocks(i, bit, plot = 0,print_file = 1, filename = filename + "_" + chip);

    def calibrate_bias(self,point, block, DAC_val, exp_val, inst, gnd_corr):
        DAC = self.nameDAC[point] + str(block)
        test = "TEST" + str(block)
        self.I2C.peri_write('TESTMUX',0b00000001 << block)
        self.I2C.peri_write(test, 0b00000001 << point)
        self.I2C.peri_write(DAC, 0)
        #time.sleep(0.1)
        off_val = self.multimeter.measure()
        #time.sleep(0.1)
        self.I2C.peri_write(DAC, DAC_val)
        #time.sleep(0.1)
        act_val = self.multimeter.measure()
        LSB = (act_val - off_val) / DAC_val
        DAC_new_val = DAC_val- int(round((act_val - exp_val - gnd_corr)/LSB))
        if DAC_new_val < 0:
            DAC_new_val = 0
        elif DAC_new_val > 31:
            DAC_new_val = 31
        self.I2C.peri_write(DAC, DAC_new_val)
        new_val = self.multimeter.measure()
        if (new_val - gnd_corr < exp_val + exp_val*self.cal_precision  )&(new_val - gnd_corr > exp_val - exp_val*self.cal_precision ):
            print("Calibration bias point ", point, "of test point", block, "--> Done (", new_val, "V for ", DAC_new_val, " DAC)")
        else:
            print("Calibration bias point ", point, "of test point", block, "--> Failed (", new_val, "V for ", DAC_new_val, " DAC)")
        return DAC_new_val

    def calibrate_chip(self, gnd_corr = 0, print_file = 1, filename = "test"):
        inst = self.multimeter.init_keithley(avg = self.measure_avg, address = self.gpib_address)
        data = np.zeros((5, 7), dtype = np.int16 )
        self.mpa.ctrl_base.disable_test()
        for point in range(0,5):
            calrowval = []
            for block in range(0,7):
                data[point, block] = self.calibrate_bias(point, block, self.DAC_val[point], self.exp_val[point], inst, gnd_corr)
        self.mpa.ctrl_base.disable_test()
        if print_file: CSV.ArrayToCSV (data, str(filename) + ".csv"); print("Saved!")
        return data

    def measure_gnd(self):
        self.mpa.ctrl_base.disable_test()
        data = np.zeros((7, ), dtype=np.float)
        for block in range(0,7):
            test = "TEST" + str(block)
            self.I2C.peri_write('TESTMUX',0b00000001 << block)
            self.I2C.peri_write(test, 0b10000000)
            #time.sleep(0.1)
            data[block] = self.multimeter.measure()
        self.mpa.ctrl_base.disable_test()
        print("Measured Analog Ground:", np.mean(data))
        return np.mean(data)

    def measure_bg(self):
        inst = self.multimeter.init_keithley(avg = self.measure_avg, address = self.gpib_address)
        time.sleep(1)
        self.mpa.ctrl_base.disable_test()
        self.I2C.peri_write('TESTMUX',0b10000000)
        time.sleep(1)
        data = self.multimeter.measure()
        self.mpa.ctrl_base.disable_test()
        print(data)
        return data

    def trimDAC_amplitude(self, value):
        for block in range(0,7):
        #curr = I2C.peri_read("C"+str(block))
        #new_value = curr + value
            self.I2C.peri_write("C"+str(block), value)
        trm_LSB = round(((0.172-0.048)/32.0*value+0.048)/32.0*1000.0,2)
        return trm_LSB

    def upload_bias(self, filename = "bias.csv"):
        array = CSV.csv_to_array(filename)
        for point in range(0,5):
            for block in range(0,7):
                DAC = self.nameDAC[point] + str(block)
                self.I2C.peri_write(DAC, array[point, block+1])
                time.sleep(0.001)
