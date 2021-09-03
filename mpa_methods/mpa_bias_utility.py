from os import EX_OSFILE, stat
from numpy.core.defchararray import _to_string_or_unicode_array

from numpy.lib.twodim_base import _trilu_dispatcher
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from scipy import stats

import time
import sys
import inspect
import random
import numpy as np

import matplotlib.pyplot as plt

class mpa_bias_utility():

    def __init__(self, mpa, I2C, fc7, multimeter, mpa_peri_reg_map, mpa_row_reg_map, mpa_pixel_reg_map):
        self.mpa = mpa
        self.i2c= I2C
        self.fc7 = fc7
        self.multimeter = multimeter
        self.mpa_peri_reg_map = mpa_peri_reg_map
        self.mpa_row_reg_map = mpa_row_reg_map
        self.mpa_pixel_reg_map = mpa_pixel_reg_map
        self.initialised = False
        self.nameDAC = ["A", "B", "C", "D", "E", "ThDAC", "CalDAC"]
        self.DAC_val = [15, 15, 15, 15, 15] # 0x0f, default DAC value for PVT adjustment, max 32
        self.exp_val = [0.082, 0.082, 0.108, 0.082, 0.082] # 
        self.exp_VREF = 0.85
        self.cal_precision = 0.05
        self.measure_avg = 1

        self.set_gpib_address(16)
        self.__multimeter_gpib_initialise()

    def set_gpib_address(self, address):
        self.gpib_address = address

    def __multimeter_gpib_initialise(self):
        self.multimeterinst = self.multimeter.connect(avg = self.measure_avg, address = self.gpib_address)
        self.initialised = True

    def DAC_linearity(self, block, point, bit, step = 1, plot = 1, verbose = 1):
        DAC = self.nameDAC[point] + str(block)
        self.select_block(block + 1, point, 1)
        data = np.zeros(1 << bit, dtype=np.float)
        if verbose: print("DAC: ", DAC)
        for i in range(0, 1 << bit, step):
            self.i2c.peri_write(DAC, i)
            data[i] = self.multimeter.measure()
            if (i % 10 == 0):
                if verbose: print("Done point ", i, " of ", 1 << bit)
        if plot:
            plt.plot(list(range(0,1 << bit)), data,'o')
            plt.xlabel('DAC voltage [LSB]'); plt.ylabel('DAC value [mV]'); plt.show()
        return data

    def measure_DAC_testblocks(self, point, bit, step = 1, plot = 1,print_file = 0, filename = "../cernbox/MPA_Results/DAC_", verbose = 1):
        data = np.zeros((7, 1 << bit), dtype=np.float)
        for i in range(0,7):
            data[i] = self.DAC_linearity(block = i, point = point, bit = bit ,step = step, plot = 0, verbose = verbose)
            if plot: plt.plot(list(range(0,1 << bit)), data[i, :],'o', label = "Test Block #" + str(i))
        if plot: plt.xlabel('DAC voltage [LSB]'); plt.ylabel('DAC value [mV]');plt.legend(); plt.show()
        if print_file: CSV.ArrayToCSV (data, str(filename) + "_TP" + str(point) + ".csv")
        return data

    def measure_DAC_chip(self, chip = "Test", print_file = 1, filename = "../cernbox/MPA_Results/ChipDAC_"):
        for i in range(0,7):
            if (i < 5): bit = 5
            else: 		bit = 8
            measure_DAC_testblocks(i, bit, plot = 0,print_file = 1, filename = filename + "_" + chip);

    
    def calculate_ADC_LSB(self, vref_exp):
        self.mpa.ctrl_base.set_peri_mask()

        #self.calibrate_vref(vref_exp)

        self.select_block(1, 7 ,0)
        offset = self.adc_measure()
        LSB = vref_exp/(4095 - offset)
        return LSB
    
    def calibrate_vref(self, vref_exp, lin_pts, plot = 0, verbose = 0):
        """Calibrates 5-bit DAC in Monitoring Block to set ADCREF to vref_exp (typically 0.850V). 
        Voltage range is usually between 0.750V to 0.950V. Calibration done by sweeping DAC input
        output values and finding linear relation for the measured points.

        Args:
            vref_exp (float): Target voltage for ADCREF, Range of 0.750V to 0.950V
            lin_pts (int): Number of measurement points to be collected. 1 to 32
            plot (int, optional): [description]. Defaults to 0.
            verbose (int, optional): [description]. Defaults to 0.

        Returns:
            [list]: ret, vref_dac_new, vref_dac_vals
        """        
        # init
        self.mpa.ctrl_base.disable_test()
        self.mpa.ctrl_base.set_peri_mask()
        self.i2c.peri_write("ADCtrimming", 0b01000000) # Bit 7 "trim_sel" to 1 selects I2C ctrl of VREF DAC
        self.select_block(10, 0 ,1)
        self.mpa.ctrl_base.set_peri_mask(0b00011111)
        if lin_pts < 1:
            lin_pts = 1
        elif lin_pts > 32:
            lin_pts = 32
        vref_dac_vals = np.zeros((2, lin_pts))
        iterable = np.ndenumerate(np.around(np.linspace(0, 31, lin_pts),0))
        # step through all DAC values, measure and capture VREF
        for index, dac_val in iterable:
            self.i2c.peri_write("ADCcontrol", int(dac_val))
            vref_val = self.multimeter.measure()
            vref_dac_vals[0:,index[0]] = (dac_val, vref_val)
            if verbose:
                print(f"VREF DAC val {int(dac_val)} : {round(vref_val, 4)}V")
        # linear regression
        slope = round(stats.linregress(vref_dac_vals)[0], 5) # return first value of linregress, which is the calculated slope
        # slope from two points
        #slope = (vref_val - vref_dac_vals[1].flat[0]) / 31
        # calculate new DAC value
        offset = vref_dac_vals[1].flat[0]
        vref_dac_new = int(round((vref_exp - offset) / slope,0))
        if (vref_dac_new > 31): vref_dac_new = 31
        # measure corrected VREF
        self.i2c.peri_write("ADCcontrol", int(vref_dac_new))
        vref_act = self.multimeter.measure()
        if (vref_act < (vref_exp + vref_exp*0.01)) & (vref_act > (vref_exp - vref_exp*0.01)):
            print(f"Calibration of VREF DAC --> Done ({vref_act}V for {vref_dac_new})")
            ret = 1
        else:
            print(f"Calibration of VREF DAC --> Failed ({vref_act}V for {vref_dac_new})")
            ret =-1
        if verbose:
            print(f"Slope = {slope}, Offset = {round(offset, 4)}V, vref_dac_new = {vref_dac_new}, VREF = {round(vref_act, 4)}V")
        self.mpa.ctrl_base.set_peri_mask()
        if plot:
            plt.plot(vref_dac_vals[0], vref_dac_vals[1])
            plt.xlabel('VREF code [LSB]'); plt.ylabel('VREF value [mV]'); plt.show()
    
        return ret, vref_dac_new, vref_dac_vals

    def calibrate_chip(self, gnd_corr = 0, print_file = 1, filename = "test"):
        """Runs calibrate_bias for all seven bias blocks and test points A-E.

        Args:
            gnd_corr (int, optional): Correction for shifted GND value. Defaults to 0.
            print_file (int, optional): [description]. Defaults to 1.
            filename (str, optional): [description]. Defaults to "test".

        Returns:
            np.array: Array of all new DAC values
        """        
        data = np.zeros((5, 7), dtype = np.int16)
        self.mpa.ctrl_base.disable_test()
        self.mpa.ctrl_base.set_peri_mask()
        # for the DAC points A to E
        for point in range(0,5):
            # for all seven bias blocks
            for block in range(0,7):
                data[point, block] = self.calibrate_bias(point, block, self.DAC_val[point], self.exp_val[point], gnd_corr)
        self.mpa.ctrl_base.disable_test()
        if print_file: CSV.ArrayToCSV (data, str(filename) + ".csv"); print("Saved!")
        return data

    def calibrate_bias(self, point, block, DAC_val, exp_val, gnd_corr):
        """Calibrates DAC bias values for a given test point. Calibration necessary to compensate for PVT variations local to that test point.

        Estimates new DAC value between 0 to 32, starts at 15. 
        Fails if resulting voltage falls outside of given precision margin.

        Args:
            point (int): Selects test point
            block (int): Selects block bias block
            DAC_val (int): DAC value
            exp_val (int): Reference voltage
            gnd_corr (int): Correction for shifted GND value

        Returns:
            int: calibrated DAC_val
        """        
        DAC = self.nameDAC[point] + str(block) # Careful to set string to correct DAC
        # enable a specific bias block and test point. add +1 as blocks are indexed 1-7 in register "ADC_TEST_Selection"
        self.select_block(block + 1, point, 1)
        # set adjustment of specific DAC to 0 initially
        self.i2c.peri_write(DAC, 0) 
        #time.sleep(0.1)
        off_val = self.multimeter.measure()
        #time.sleep(0.1)
        self.i2c.peri_write(DAC, DAC_val)
        #time.sleep(0.1)
        act_val = self.multimeter.measure()
        LSB = (act_val - off_val) / DAC_val
        DAC_new_val = DAC_val- int(round((act_val - exp_val - gnd_corr)/LSB))
        if DAC_new_val < 0:
            DAC_new_val = 0
        elif DAC_new_val > 31:
            DAC_new_val = 31

        self.i2c.peri_write(DAC, DAC_new_val)
        new_val = self.multimeter.measure()
        if (new_val - gnd_corr < exp_val + exp_val*self.cal_precision  )&(new_val - gnd_corr > exp_val - exp_val*self.cal_precision ):
            print("Calibration bias point ", point, "of bias block", block, "--> Done (", new_val, "V for ", DAC_new_val, " DAC)")
        else:
            print("Calibration bias point ", point, "of bias block", block, "--> Failed (", new_val, "V for ", DAC_new_val, " DAC)")
        return DAC_new_val

    def select_block(self, block, test_point = 0, sw_en = 0):
        """Enables test point for given block for measurement by external multimeter. Done by i2c writing to "ADC_TEST_selection" multiplexing register. 
        See MPA2 ADC/Bias Register Description for more detail.

        Args:
            block (int): Select block; [0] disable all,  [1-7] – Bias Blocks 0 to 6, [8] – BG, [9] – VDAC_REF, [10] - VREF, [11]- TEMP
            test_point (int): Select test point; [1-7] for DAC A-E.
            sw_en (int): [0] for ADC, [1] for external multimeter measurement
        """        

        sw_enable = sw_en << 7
        block_selection = block
        value_selection = test_point << 4
        command = sw_enable + block_selection + value_selection

        self.mpa.ctrl_base.set_peri_mask()
        self.i2c.peri_write('ADC_TEST_selection', command)

    def adc_measure(self, nsamples=1):
        r1 = []
        for i in range(nsamples):
            self.i2c.peri_write( "ADCcontrol", 0b11100000 )
            self.i2c.peri_write( "ADCcontrol", 0b11000000 )
            time.sleep(0.001)
            msb = self.i2c.peri_read( "ADC_output_MSB")
            lsb = self.i2c.peri_read( "ADC_output_LSB")
            res = ((msb<<8) | lsb)
            r1.append(res)
        if(nsamples>1): r = np.sum(r1) / float(nsamples)
        else: r = r1[0]
        return r

    def measure_gnd(self):
        """Measures and returns GND voltage averaged over all seven bias blocks. """
        self.mpa.ctrl_base.disable_test()
        data = np.zeros((7, ), dtype=np.float)
        for block in range(0,7):
            self.select_block(block+1, 7, 1) # 7 to select GND 
            data[block] = self.multimeter.measure()
        self.mpa.ctrl_base.disable_test()
        print("Measured Analog Ground:", np.mean(data))
        print(data)
        return np.mean(data)

    def measure_bg(self):
        time.sleep(1)
        self.mpa.ctrl_base.disable_test()
        self.i2c.peri_write('TESTMUX',0b10000000)
        time.sleep(1)
        data = self.multimeter.measure()
        self.mpa.ctrl_base.disable_test()
        print(data)
        return data

    def trimDAC_amplitude(self, value):
        for block in range(0,7):
        #curr = I2C.peri_read("C"+str(block))
        #new_value = curr + value
            self.i2c.peri_write("C"+str(block), value)
        trm_LSB = round(((0.172-0.048)/32.0*value+0.048)/32.0*1000.0,2)
        return trm_LSB

    def upload_bias(self, filename = "bias.csv"):
        array = CSV.csv_to_array(filename)
        for point in range(0,5):
            for block in range(0,7):
                DAC = self.nameDAC[point] + str(block)
                self.i2c.peri_write(DAC, array[point, block+1])
                time.sleep(0.001)
