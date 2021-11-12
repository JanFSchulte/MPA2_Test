
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from main import *

import seaborn as sns
import pickle
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class mpa_test_utility():
    """ """
    def __init__(self, mpa, I2C, fc7):
        self.mpa = mpa
        self.i2c = I2C
        self.fc7 = fc7

    def shift(self, verbose = 0):
        """

        :param verbose:  (Default value = 0)

        """
        if verbose: utils.print_info("->  Doing Shift Test")
        self.i2c.peri_write("LFSR_data", 0b10101010)
        checkI2C = self.i2c.peri_read("LFSR_data")
        if verbose: utils.print_info(f"->  Writing: {str(bin(checkI2C))}")
        self.mpa.ctrl_base.activate_shift()
        time.sleep(0.1)
        self.fc7.send_test()
        time.sleep(0.1)
        self.fc7.send_trigger()
        time.sleep(0.1)
        check = self.mpa.rdo.read_regs(verbose = 0)[1] #return stubs
        
        OK = True
        for i,C in enumerate(check):
            if bin(C) != "0b10101010101010101010101010101010" and i < 50: OK = False
            if bin(C) != "0b0" and i > 49: OK = False
        if verbose:
            if OK: utils.print_good("->  Shift Test Passed")
            else: utils.print_error("->  Shift Test Failed")
        return OK

    def test_pp_digital(self, row, pixel):
        """
        :param row:
        :param pixel:
        """
        self.i2c.pixel_write('PixelEnables', row, pixel, 0x20)
        self.fc7.send_test(8)
        return self.mpa.rdo.read_stubs(fast = 1)

    def digital_pixel_test(self, row = list(range(1,17)), pixel = list(range(1,121)), print_log = 1, filename =  "../cernbox/MPA_Results/digital_pixel_test.log"):
        """

        :param row:  (Default value = list(range(1)
        :param pixel:  (Default value = list(range(1)
        :param print_log:  (Default value = 1)
        :param filename:  (Default value = "../cernbox/MPA_Results/digital_pixel_test.log")

        """
        OutputBadPix = []
        t0 = time.time()
        if print_log:
            f = open(filename, 'w')
            f.write("Starting Test:\n")
        self.i2c.peri_write('Mask', 0b11111111)
        self.i2c.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.activate_sync()
        time.sleep(0.1)
        self.mpa.ctrl_base.activate_pp()
        time.sleep(0.1)
        self.i2c.pixel_write('DigPattern', 0, 0,  0b10000000)
        time.sleep(0.1)
        self.i2c.peri_write('Mask', 0b00001100)
        self.i2c.peri_write('Control', 0b00000100)
        self.i2c.peri_write('Mask', 0b11111111)
        time.sleep(0.1)
        for r in row:
            for p in pixel:
                self.mpa.ctrl_pix.disable_pixel(0,0)
                nst, pos, Z, bend = self.test_pp_digital(r, p)
                check_pix = 0
                check_row = 0
                err = 0
                for centr in pos[:,0]:
                    if (centr == p*2): check_pix += 1
                    elif (centr != 0): err =+ 1
                for row in Z[:,0]:
                    if (row == r-1):
                        if (r-1 == 0): 	check_row = 1
                        else: check_row += 1
                    elif (row != 0): err =+ 1
                if ((check_pix != 1) or (check_row != 1) or (err != 0)):
                    error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(check_pix) + " " +  str(check_row) + " " + str(err) + "\n"
                    OutputBadPix.append([p,r])
                    print(error_message)
                    if print_log:
                        f.write(error_message)
        self.mpa.ctrl_pix.disable_pixel(0,0)
        if print_log:
            f.write("Test Completed")
            f.close()
        t1 = time.time()
        utils.print_log("->  Digital Pixel Test Elapsed Time: " + str(t1 - t0))
        return OutputBadPix

    def test_pp_analog(self, row, pixel):
        """

        :param row:
        :param pixel:

        """
        self.mpa.ctrl_pix.enable_pix_EdgeBRcal(row, pixel)
        #time.sleep(0.001)
        self.fc7.send_test(8)
        return self.mpa.rdo.read_stubs(fast = 1)

    def analog_pixel_test(self, row = list(range(1,17)), pixel = list(range(2,120)), print_log = 1, filename =  "../cernbox/MPA_Results/analog_pixel_test.log0", verbose = 1):
        """

        :param row:  (Default value = list(range(1)
        :param pixel:  (Default value = list(range(2)
        :param print_log:  (Default value = 1)
        :param filename:  (Default value = "../cernbox/MPA_Results/analog_pixel_test.log0")
        :param verbose:  (Default value = 1)

        """
        t0 = time.time()
        OutputBadPix = []
        if print_log:
            f = open(filename, 'w')
            f.write("Starting Test:\n")
        self.i2c.peri_write('Mask', 0b11111111)
        self.i2c.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.set_calibration(200)
        self.mpa.ctrl_base.set_threshold(200)
        self.mpa.ctrl_base.activate_sync()
        self.mpa.ctrl_base.activate_pp()
        time.sleep(0.1)
        for r in row:
            for p in pixel:
                self.mpa.ctrl_pix.disable_pixel(0,0)
                nst, pos, Z, bend = self.test_pp_analog(r, p)
                check_pix = 0
                check_row = 0
                err = 0
                for centr in pos[:,0]:
                    if (centr == p*2): check_pix += 1
                    elif (centr != 0): err =+ 1
                for row in Z[:,0]:
                    if (row == r-1):
                        if (r-1 == 0): check_row = 1
                        else: check_row += 1
                    elif (row != 0): err =+ 1
                if ((check_pix != 1) or (check_row != 1) or (err != 0)):
                    error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(check_pix) + " " +  str(check_row) + " " + str(err) + "\n"
                    OutputBadPix.append([p,r])
                    if verbose: print(error_message)
                    if print_log: f.write(error_message)
        self.mpa.ctrl_pix.disable_pixel(0,0)
        if print_log:
            f.write("Test Completed")
            f.close()
        t1 = time.time()
        utils.print_log("->  Analog Pixel Test Elapsed Time: " + str(t1 - t0))
        return OutputBadPix

    def reset_strip_in(self,  line = list(range(0,8)), strip = [0, 0, 0, 0, 0, 0, 0, 0]):
        """STRIP Input test

        :param line:  (Default value = list(range(0)
        :param strip:  (Default value = [0)

        """
        value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
        for l in line:
            reg = "fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_" +str(l) + "_0"
            #print(f"Regsiter:{reg}, Value:{bin(value)}")
            self.fc7.write(reg, value)
            value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
            reg = "fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_" +str(l) + "_1"
            #print(f"Regsiter:{reg}, Value:{bin(value)}")
            self.fc7.write(reg, value)

    def strip_in_def( self, line ,strip = 8*[128]):
        """

        :param line:
        :param strip:  (Default value = 8*[128])

        """
        value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
        reg = "fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_" +str(line) + "_0"
        #print(f"Regsiter:{reg}, Value:{bin(value)}")
        self.fc7.write(reg, value)
        value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
        reg = "fc7_daq_cnfg.physical_interface_block.ssa_stub_data.format_" +str(line) + "_1"
        self.fc7.write(reg, value)
        #print(f"Regsiter:{reg}, Value:{bin(value)}")


    def strip_in_test(self, n_pulse = 10, line = list(range(0,8)),  value = [128, 64, 32, 16, 8, 4, 2, 1], latency = 0b00111011, edge = 0):
        """

        Parameters
        ----------
        n_pulse : int, optional
            [description], by default 10
        line : [type], optional
            [description], by default list(range(0,8))
        value : list, optional
            [description], by default [128, 64, 32, 16, 8, 4, 2, 1]
        latency : [int], optional
            [description], by default 0b00111011
        edge : int, optional
            [description], by default 0

        Returns
        -------
        line_check : line x value array
            Each field cointains count of correct matches for respective line and test value
        """
        self.i2c.peri_write('EdgeSelTrig',edge) # 1 = rising
        self.i2c.peri_write('LatencyRx320', latency) # Trigger line aligned with FC7
        line = np.array(line)
        value = np.array(value)
        nline = int(line.shape[0])
        nvalue = int(value.shape[0])
        line_check = np.zeros((nline,nvalue), dtype = np.int)
        count_line = 0
        for l in line:
            count_val = 0
            for val in value:
                self.reset_strip_in()
                self.strip_in_def(l, 8*[val])
                check = 0
                for i in range(0, n_pulse):
                    self.fc7.send_test()
                    nst, pos, Z, bend = self.mpa.rdo.read_stubs()
                    for centr in pos[6:14,0]:
                        if (centr == val): check += 1
                    for centr in pos[6:14,1]:
                        if (centr == val): check += 1
                line_check[count_line, count_val ] = check
                count_val += 1
            count_line += 1

        return line_check

    def strip_in_scan(self, n_pulse = 1, edge = "falling", probe = 0, print_file = 0, filename =  "../cernbox/MPA_Results/strip_in_scan", verbose = 1):
        """During strip test strip centroids are used as stub seeds and compared to output.
        Test is done for all lines, different latencies, patterns.

        Args:
            n_pulse (int, optional): [description]. Defaults to 1.
            edge (str, optional): [description]. Defaults to "falling".
            probe (int, optional): [description]. Defaults to 0.
            print_file (int, optional): [description]. Defaults to 0.
            filename (str, optional): [description]. Defaults to "../cernbox/MPA_Results/strip_in_scan".
            verbose (int, optional): [description]. Defaults to 1.

        Returns:
            [type]: [description]
        """        
        t0 = time.time()
        self.mpa.ctrl_base.activate_ss()
        data_array = np.zeros((8, 8 ), dtype = np.float16 )
        if probe:
            self.i2c.peri_write("InSetting_0",0)
            self.i2c.peri_write("InSetting_1",1)
            self.i2c.peri_write("InSetting_2",2)
            self.i2c.peri_write("InSetting_3",3)
            self.i2c.peri_write("InSetting_4",4)
            self.i2c.peri_write("InSetting_5",5)
            self.i2c.peri_write("InSetting_6",6)
            self.i2c.peri_write("InSetting_7",7)
            self.i2c.peri_write("InSetting_8",8)
        time.sleep(0.1)

        for i in range(0,8):
            latency = (i  << 3)
            if verbose: utils.print_info("->  Testing Latency ", i)
            if (edge == "falling" ): temp = self.strip_in_test(n_pulse = n_pulse, latency = latency , edge = 0)
            elif (edge == "rising" ): temp = self.strip_in_test(n_pulse = n_pulse, latency = latency , edge = 255)
            else: utils.print_info("->  Edge not recognized"); return
            for line in range(0,8):
                data_array[i, line ] = np.average(temp[line])/(n_pulse*8)
        if print_file:
            CSV.ArrayToCSV (data_array, str(filename) + "_npulse_" + str(n_pulse) + ".csv")
        t1 = time.time()
        utils.print_log("-> Strip In Test Elapsed Time: " + str(t1 - t0))
        return data_array

    def memory_test(self, latency, row, pixel, diff, dig_inj = 1, verbose = 1): # Diff = 2
        """Memory Test

        :param latency:
        :param row:
        :param pixel:
        :param diff:
        :param dig_inj: 'True' for digital pulse, 'False' for analog (Default value = 1)
        :param verbose:  (Default value = 1)

        """
        self.mpa.ctrl_pix.disable_pixel(0,0)
        if dig_inj:
            self.i2c.pixel_write('PixelEnables', row, pixel, 0x20)
        else:
            self.mpa.ctrl_pix.enable_pix_LevelBRcal(row,pixel, polarity = "rise")
        time.sleep(0.001)
        self.fc7.SendCommand_CTRL("start_trigger")
        time.sleep(0.001)
        return self.mpa.rdo.read_L1(verbose)


    def rnd_pixel(self, row = [1,16], pixel = [1,120], dig_inj = 1, verbose = 1):
        """ Returns one random pixel coordinate in given range and passes it to memory_test

        :param row:
        :param pixel:

        """
        r_rnd = random.randint(min(row), max(row))
        p_rnd = random.randint(min(pixel), max(pixel))

        if verbose : utils.print_info(f"->  Pixel: {p_rnd} of Row: {r_rnd}")

        self.mpa.ctrl_pix.disable_pixel(0,0)
        if dig_inj:
            self.i2c.pixel_write('PixelEnables', r_rnd, p_rnd, 0x20)
        else:
            self.mpa.ctrl_pix.enable_pix_LevelBRcal(r_rnd ,p_rnd, polarity = "rise")
        #time.sleep(0.001)
        self.fc7.SendCommand_CTRL("start_trigger")

        return p_rnd, r_rnd

    def rnd_test(self, n_tests = 1000, latency = 255, delay = [10], diff = 2, print_log = 0, filename =  "../cernbox_anvesh/MPA_Results/rnd_test.log", dig_inj = 1, gate = 0, verbose = 1):
        """

        :param n_tests: Number of random pixel tests  (Default value = 1000)
        :param latency:  (Default value = 255)
        :param delay:  (Default value = [10])
        :param row:  (Default value = list(range(1)
        :param pixel:  (Default value = list(range(1)
        :param diff:  (Default value = 2)
        :param print_log:  (Default value = 0)
        :param filename:  (Default value = "../cernbox/MPA_Results/digital_mem_test.log")
        :param dig_inj:  (Default value = 1)
        :param gate:  (Default value = 0)
        :param verbose:  (Default value = 1)

        """

        t0 = time.time()
        bad_pix = []
        print("Running Random Pixel Test:")

        if print_log:
            f = open(filename, 'w')
            f.write("Starting Test:\n")

        self.mpa.ctrl_base.activate_sync()
        self.mpa.ctrl_base.activate_pp()
        self.i2c.row_write('L1Offset_1', 0,  latency - diff)
        self.i2c.row_write('L1Offset_2', 0,  0)
        self.i2c.row_write('MemGatEn', 0,  gate)
        self.i2c.pixel_write('DigPattern', 0, 0,  0b00000001)
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        self.mpa.ctrl_pix.disable_pixel(0,0)

        stuck = 0; i2c_issue = 0; error = 0

        Configure_TestPulse_MPA(delay_after_fast_reset = delay[0] + 512, delay_after_test_pulse = latency, delay_before_next_pulse = 200, number_of_test_pulses = 1, enable_L1 = 1, enable_rst = 1, enable_init_rst = 1)

        for n in range(0, n_tests):
            #time.sleep(0.1)

            # trigger test pulse for random pixel and get injection coordinate
            p, r = self.rnd_pixel(dig_inj = 1)

            strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = self.mpa.rdo.read_L1(verbose)
            found = 0

            for i in range(0, int(pixel_counter)):
                if (pos_pixel[i] == p) and (Z[i] == r):
                    found = 1
                elif (pos_pixel[i] == p-1) and (Z[i] == r):
                    found = 1
                    i2c_issue += 1

            if (pixel_counter > 1): stuck += 1

            if (not found):
                bad_pix.append([p,r])
                error += 1
                error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error Delay " + str(delay[0]) + " " + str(pixel_counter) + " " +  str(pos_pixel) + " " + str(Z) + "\n"
                if verbose: print(error_message)
                if print_log: f.write(error_message)

        utils.print_info("->  Number of tests: ", n_tests)
        utils.print_info("->  Number of error: ", error)
        utils.print_info("->  Number of stucks: ", stuck)
        utils.print_info("->  Number of I2C issues: ", i2c_issue)

        if print_log:
            f.write("Test Completed:\n")
            f.write("-------------------------------------\n")
            f.write("-------------------------------------\n")
            line = " Number of tests: " + str(n_tests) + "\n"; f.write(line)
            line = " Number of error: " + str(error) + "\n"; f.write(line)
            line = " Number of stucks: " + str(stuck) + "\n"; f.write(line)
            line = " Number of I2C issues: " + str(i2c_issue) + "\n"; f.write(line)
            f.write("-------------------------------------\n")
            f.write("-------------------------------------\n")
            f.close()

        t1 = time.time()
        utils.print_log("->  Elapsed Time: " + str(t1 - t0))
        return bad_pix, error, stuck, i2c_issue

    def mem_test(self, latency = 255, delay = [10], row = list(range(1,17)), pixel = list(range(1,121)), diff = 3, print_log = 0, filename =  "../cernbox/MPA_Results/digital_mem_test.log", dig_inj =1, gate = 0, verbose = 1):
        """

        :param latency:  (Default value = 255)
        :param delay:  (Default value = [10])
        :param row:  (Default value = list(range(1)
        :param pixel:  (Default value = list(range(1)
        :param diff:  (Default value = 2)
        :param print_log:  (Default value = 0)
        :param filename:  (Default value = "../cernbox/MPA_Results/digital_mem_test.log")
        :param dig_inj:  (Default value = 1)
        :param gate:  (Default value = 0)
        :param verbose:  (Default value = 1)

        """
        t0 = time.time()
        bad_pix = []
        if print_log:
            f = open(filename, 'w')
            f.write("Starting Test:\n")
        self.fc7.write("fc7_daq_cnfg.physical_interface_block.slvs_debug.SSA_first_counter_del", 100)
        self.fc7.activate_I2C_chip(verbose=0)
        self.mpa.ctrl_base.activate_sync()
        self.mpa.ctrl_base.activate_pp()
        self.i2c.row_write('Mask', 0,  0b11111111)
        self.i2c.row_write('MemoryControl_1', 0,  latency - diff)
        self.i2c.row_write('Mask', 0,  0b00000001)
        self.i2c.row_write('MemoryControl_2', 0,  0)
        self.i2c.row_write('Mask', 0,  0b00000010)
        self.i2c.row_write('MemoryControl_2', 0,  gate)
        self.i2c.row_write('Mask', 0,  0b11111111)
        self.i2c.pixel_write('DigPattern', 0, 0,  0b00000001)
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        self.mpa.ctrl_pix.disable_pixel(0,0)
        stuck = 0; i2c_issue = 0; error = 0; missing = 0
        for d in delay:
            Configure_TestPulse_MPA(delay_after_fast_reset = d + 512, delay_after_test_pulse = latency, delay_before_next_pulse = 200, number_of_test_pulses = 1, enable_L1 = 1, enable_rst = 0, enable_init_rst = 0)
            time.sleep(0.1)
            ## Automatic change of sampling edge on error
            #try:
            #	strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = memory_test(latency = latency, row = 10, pixel = 5, diff = diff, dig_inj = dig_inj, verbose = 0)
            #except TypeError:
            #	print "Header not Found! Changing sampling phase of T1"
            #	I2C.peri_write('EdgeSelT1Raw', 0)
            #time.sleep(1)
            for r in row:
                self.fc7.SendCommand_CTRL("fast_fast_reset")
                for p in pixel:
                    #try:
                    strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z, bx, l1_id  = self.memory_test(latency = latency, row = r, pixel = p, diff = diff, dig_inj = dig_inj, verbose = 0)
                    found = 0
                    for i in range(0, pixel_counter):
                        if (pos_pixel[i] == p) and (Z[i] == r):
                            found = 1
                        elif (pos_pixel[i] == p-1) and (Z[i] == r):
                            found = 1
                            i2c_issue += 1
                    if (pixel_counter > 1): stuck += 1
                    if (not found):
                        bad_pix.append([p,r])
                        error += 1
                        error_message = "ERROR in Pixel: " + str(p) + " of Row: " + str(r) + ". Error " + str(d) + " " + str(pixel_counter) + " " +  str(pos_pixel) + " " + str(Z) + "\n"
                        if verbose: print(error_message)
                        if print_log: f.write(error_message)
                    #except TypeError:
                    #	missing += 1
                    #	error_message = "Header not Found in Pixel: " + str(p) + " of Row: " + str(r) + "\n"
                    #	if verbose: print error_message
                    #	if print_log: f.write(error_message)
        utils.print_info(f"->  Number of error:        {error}")
        utils.print_info(f"->  Number of stucks:       {stuck}")
        utils.print_info(f"->  Number of I2C issues:   {i2c_issue}")
        utils.print_info(f"->  Number of missing:      {missing}")
        if print_log:
            f.write("Test Completed:\n")
            f.write("-------------------------------------\n")
            f.write("-------------------------------------\n")
            line = " Number of error: " + str(error) + "\n"; f.write(line)
            line = " Number of stucks: " + str(stuck) + "\n"; f.write(line)
            line = " Number of I2C issues: " + str(i2c_issue) + "\n"; f.write(line)
            line = " Number of missing: " + str(missing) + "\n" ;f.write(line)
            f.write("-------------------------------------\n")
            f.write("-------------------------------------\n")
            f.close()
        t1 = time.time()
        utils.print_log("->  Elapsed Time: " + str(t1 - t0))

        return bad_pix, error, stuck, i2c_issue, missing

    def plot_chip_errors(self, bad_pix = []):
        """ Plots a 2D histogramm count of pixel error on a heatmap

        :bad_pix: List of bad pixels

        """
        chip_map = np.zeros((122,18))
        np.add.at(chip_map, tuple(zip(*bad_pix)), 1)
        np.rot90(chip_map)

        # generate 2 2d grids for the x & y bounds
        x,y = np.meshgrid(np.linspace(1, 121, 121), np.linspace(1, 17, 17))
        # x and y are bounds, so z should be the value *inside* those bounds.
        z = chip_map.transpose()

        # reduce matrix size to correct pixel indices
        z = np.delete(z, 0, 1) # delete 0 column
        z = np.delete(z, 0, 0) # delete 0 row

        # Therefore, remove the last value from the z array.
        #z = z[:-1, :-1]
        z_min, z_max = np.abs(z).min(), np.abs(z).max()
        fig, ax = plt.subplots()

        c = ax.pcolormesh(x, y, z, cmap='YlOrRd', vmin=z_min, vmax=z_max, shading = 'auto')
        ax.set_title('MPA Pixel Error Map')

        # set the limits of the plot to the limits of the data
        ax.axis([x.min(), x.max(), y.min(), y.max()])
        ax.set_yticks(np.linspace(1, 17, 17))
        ax.set_xticks([1,20,40,60,80,100,121])

        fig.colorbar(c, ax=ax)
        fig.set_figheight(8)
        fig.set_figwidth(5)

        plt.show()

    def ro_scan (self, duration = 127, n_samples = 1):
        r0 = np.zeros((17))
        r1 = np.zeros((17))
        self.fc7.activate_I2C_chip(verbose = 0)
        for j in range(0, n_samples):
            res0, res1 = self.mpa.ctrl_base.ro_peri(duration = duration)
            r0[0] += res0 
            r1[0] += res1
        for i in range(1,17):
            for j in range(0, n_samples):
                res0, res1 = self.mpa.ctrl_base.ro_row( row = i, duration = duration)
                r0[i] += res0 
                r1[i] += res1
        r0 = r0 / n_samples
        r1 = r1 / n_samples        
        return r0, r1

    def ro_scan_voltage (self, duration = 127, n_samples = 1, voltages = range(800, 1300, 50)):
        r0 = []
        r1 = []
        for i in range(0, len(voltages)):
            print("Testing at voltage", voltages[i]/1000)
            self.mpa.pwr.set_dvdd(voltages[i]/1000)
            res0, res1 = self.ro_scan(duration, n_samples)
            r0.append(res0)
            r1.append(res1)
        self.mpa.pwr.set_dvdd(1)     
        r0 = np.array(r0)
        r1 = np.array(r1)
        for i in range(0, 17):
            plt.plot(voltages, r0[:,i])
        plt.title('Ring Oscillator Inverter')
        plt.xlabel('Voltage [mV]')
        plt.ylabel('Count')
        plt.show()
        for i in range(0, 17):
            plt.plot(voltages, r1[:,i])
        plt.title('Ring Oscillator Delay')
        plt.xlabel('Voltage [mV]')
        plt.ylabel('Count')
        plt.show()
        return r0, r1

    def dll_basic_test(self):
        self.fc7.activate_I2C_chip(verbose = 0)
        self.mpa.ctrl_base.set_peri_mask()
        self.mpa.i2c.peri_write('BypassMode', 0b00000100)
        self.mpa.i2c.peri_write('ConfDLL', 0b00110001)
        self.fc7.send_trigger()
        l1, stub = self.mpa.rdo.read_regs(verbose = 0)
        fail = 0
        if ( l1[0] == 4042322160): utils.print_good("->  DLL at 0 - test passed")
        else: utils.print_error("->  DLL at 1 - test failed", print(l1[0])); fail = 1
        self.mpa.i2c.peri_write('ConfDLL', 0b00111111)
        self.fc7.send_trigger()
        l1, stub = self.mpa.rdo.read_regs(verbose = 0)
        if ( l1[0] == 2021161080): utils.print_good("->  DLL at 31 - test passed")
        else: utils.print_error("->  DLL at 31 - test failed",  print(l1[0])); fail = 1
        self.mpa.i2c.peri_write('ConfDLL', 0b00110001)
        self.mpa.i2c.peri_write('BypassMode', 0b00000000)
        return fail

    def sram_bist_test(self, verbose = 1, rbr = 1):
        """SRAM row blocks include a BIST module, which can be controlled and monitored
        with I2C-registers "SRAM_BIST", "SRAM_BIST_done" and "bist_fail". The result
        can be read out with register "BIST_SRAM_output_x".

        Args:
            verbose (int, optional): [description]. Defaults to 1.
            rbr (int, optional): Test Row-By-Row if 1. Defaults to 1.

        Returns:
            [type]: [description]
        """        
        #self.fc7.activate_I2C_chip(verbose = 0)
        #self.mpa.ctrl_base.set_row_mask()
        fail = np.zeros(16)
        # Set SRAM-BIST_Mode bits to test mode.

        #start timing here
        t0 = time.time()
        self.mpa.i2c.row_write('SRAM_BIST', 0 , 0b00001111 )
        for i in range (1,17):
            if (self.mpa.i2c.row_read('SRAM_BIST_done', i)): utils.print_info("->  Test for row {i} already run!")
        if (rbr==0): self.mpa.i2c.row_write('SRAM_BIST', 0 , 0b11111111 ); time.sleep(0.1)
        for i in range (1,17):
            # Set SRAM_BIST-Start bits to 0b1111 to start. Wait at least 7ms before read. 
            if rbr: self.mpa.i2c.row_write('SRAM_BIST', i , 0b11111111 ); time.sleep(0.1)
            if (self.mpa.i2c.row_read('SRAM_BIST_done', i)):
                if verbose: utils.print_info(f"->  SRAM BIST for row {i} done!")
                if (self.mpa.i2c.row_read('SRAM_BIST_fail', i)):
                    if verbose:
                        sys.stdout.write("\033[1;31m")
                        utils.print_log(f"->  SRAM BIST for row {i} failed")
                        sys.stdout.write("\033[0;0m")
                    fail[i-1] = 1
            else: 
                if verbose:
                    sys.stdout.write("\033[1;31m")
                    print(f"Test for row {i} not run")
                    sys.stdout.write("\033[0;0m")
                fail[i-1] = 1
        t1 = time.time()
        utils.print_log(f"->  SRAM Bist Time:{str(t1-t0)}")
        return fail

    def sram_bist_voltage_scan(self, n_samples = 1, voltages = range(700, 1000, 50), rbr = 1, verbose =0):
        res = []
        for i in range(0, len(voltages)):
            fail = np.zeros(16)
            print("Testing at voltage", voltages[i]/1000)
            self.mpa.pwr.set_dvdd(voltages[i]/1000)
            self.mpa.pwr.reset_mpa(display=False)
            self.fc7.activate_I2C_chip(verbose = 0)
            self.mpa.ctrl_base.set_row_mask()
            print("Start...")
            for n in range(0, n_samples):
                fail += self.sram_bist_test(verbose=verbose, rbr=rbr)
            res.append(n_samples - fail)
            print("Success_rate:", res)
        self.mpa.pwr.set_dvdd(1)     
        res = np.array(res)/n_samples
        for i in range(0, 16):
            plt.plot(voltages, res[:,i], label = str(i))
        plt.title('BIST results')
        plt.xlabel('Voltage [mV]')
        plt.ylabel('Success rate')
        plt.legend()
        plt.show()
        return res

    def row_bist(self, row = range(1,17), vector_fail=0, verbose = 0, sram_test = 1):
        t0 = time.time()
        self.mpa.init(reset_chip=1, display= 0)
        self.fc7.activate_I2C_chip(verbose = 0)
        self.mpa.ctrl_base.set_row_mask()
        fail = np.zeros(16)
        fail_row = np.zeros(16)
        miscompare = np.zeros(16)
        if sram_test:
            bist_fail = self.sram_bist_test(verbose = verbose)
            if bist_fail.any():
                utils.print_error("->  SRAM BIST Failed! Exiting ROW BIST!")
                return fail_row, bist_fail
            utils.print_good(f"->  SRAM BIST passed")
        else:
            # Set SRAM BIST into test mode to force correct inputs for ROW BIST
            bist_fail = 0
            self.mpa.ctrl_base.set_row_mask(0b1111)
            self.mpa.i2c.row_write('SRAM_BIST', 0 , 0b1111)
        t1 = time.time()
        self.mpa.ctrl_base.set_row_mask()
        self.mpa.i2c.row_write('MemoryControl_1', 0 , 0 )
        self.mpa.i2c.row_write('MemoryControl_2', 0 , 0 )
        self.mpa.i2c.row_write('PixelControl', 0 , 0 )

        # This block tests reset assertion for the BIST block
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , 0b00000001 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 , 0b00000000 )
        # Set to test mode with RowLogic_BIST-Mode bit to 1
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
        for i in row:
            # Start test with RowLogic_BIST-Start and RowLogic_BIST-Mode bits to 1
            self.mpa.i2c.row_write('RowLogic_BIST', i , 0b00000011 )
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                utils.print_info(f"->  Test for row {i} failed")
                fail[i-1]=1; miscompare[i-1] += r
        utils.print_info(f"->  Reset test finished. Number of error: {np.sum(fail)}")

        # This block tests the ScanChain block
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000101 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b01100110 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b01100110 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , 0b11111111 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 , 0b11111111 )
        fail = np.zeros(16)
        for i in row:
            self.mpa.i2c.row_write('RowLogic_BIST', i , 0b00000111 )
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                utils.print_info(f"->  Test for row {i} failed")
                fail[i-1]=1; miscompare[i-1] += r
        utils.print_info(f"->  Scan test 1 finished. Number of error: {np.sum(fail)}")

        # Sanity check of BIST hardware
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000101 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b00000000 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b00000000 )
        fail = np.zeros(16)
        for i in row:
            self.mpa.i2c.row_write('RowLogic_BIST', i , 0b00000111 )
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                utils.print_info(f"->  Test for row {i} failed")
                fail[i-1]=1; miscompare[i-1] += r
        utils.print_info(f"->  Scan test 2 finished. Number of error: {np.sum(fail)}")

        # Finally, perform BIST with provided test vectors
        count=0
        f=open('mpa_methods/Configuration/row_bist_vector.txt','r')
        for l in range(1,306):
            line = int(f.readline(),2)
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
            self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , line & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST_input_2', 0 ,(line >> 8) & 0xFF )
            line = int(f.readline(),2)
            self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , line & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 ,(line >> 8) & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000011 )
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
            if (vector_fail):
                for i in row:
                    r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                    if (r == None): 
                        self.fc7.activate_I2C_chip(verbose = 0)
                        time.sleep(0.001)
                        r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                        utils.print_info(f"->  repeat read operation for row {r} at vector {l}")
                    if (r != miscompare[i-1]):
                        if verbose: utils.print_info(f"->  Row: {i}, N of miscomparisons at vector: {l}")
                        #print("Input Vector: ", self.mpa.i2c.row_read('RowLogic_BIST_input_2', i ), self.mpa.i2c.row_read('RowLogic_BIST_input_1', i ) )
                        #print("Output Vector: ", self.mpa.i2c.row_read('RowLogic_BIST_ref_output_2', i ), self.mpa.i2c.row_read('RowLogic_BIST_ref_output_1', i ) )
                        miscompare[i-1] = r
            line = f.readline()
        t2 = time.time()
        for i in row:
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r == None): 
                self.fc7.activate_I2C_chip(verbose = 0)
                time.sleep(0.001)
                r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                if verbose: utils.print_info(f"->  repeat read operation for row {r}, at vector {l}")
            if verbose: utils.print_info(f"->  Row: {i}, N of miscomparisons at vector: {r}")
            fail_row[i-1] = r
        utils.print_log("->  Init + SRAM BIST Elapsed Time: " + str(t1 - t0))
        utils.print_log("->  Row BIST Elapsed Time: " + str(t2 - t1))
        return fail_row, bist_fail
    
    def row_bist_all(self, row = range(1,17), vector_fail=0, verbose = 0, sram_test = 1):
        """Runs also Reset and Scan test stages of ROW BIST for all rows at once.
        This method was created to collect some addtional data on ROW BIST with voltage sweeps

        Args:
            row ([type], optional): [description]. Defaults to range(1,17).
            vector_fail (int, optional): [description]. Defaults to 0.
            verbose (int, optional): [description]. Defaults to 0.
            sram_test (int, optional): [description]. Defaults to 1.

        Returns:
            [type]: [description]
        """        
        t0 = time.time()
        self.mpa.init(reset_chip=1)
        self.fc7.activate_I2C_chip(verbose = 0)
        self.mpa.ctrl_base.set_row_mask()
        fail = np.zeros(16)
        fail_row = np.zeros(16)
        miscompare = np.zeros(16)
        bist_fail = 0
        if sram_test:
            bist_fail = self.sram_bist_test()
            if bist_fail.any():
                bist_fail = 1
                print("SRAM BIST Failed! Exiting ROW BIST!")
                return fail_row, bist_fail
        else:
            # Set SRAM BIST into test mode to force correct inputs for ROW BIST
            self.mpa.ctrl_base.set_row_mask(0b1111)
            self.mpa.i2c.row_write('SRAM_BIST', 0 , 0b1111)

        t1 = time.time()
        if sram_test:
            print("Init + SRAM BIST Elapsed Time: " + str(t1 - t0))
        else:
            print("Init Elapsed Time: " + str(t1 - t0))

        self.mpa.ctrl_base.set_row_mask()
        self.mpa.i2c.row_write('MemoryControl_1', 0 , 0 )
        self.mpa.i2c.row_write('MemoryControl_2', 0 , 0 )
        self.mpa.i2c.row_write('PixelControl', 0 , 0 )
        
        # This block tests reset assertion for the BIST block
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , 0b00000001 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 , 0b00000000 )
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 ) # set to test mode
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000011 )
        for i in row:
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                print("Test for row", i, "failed")
                fail[i-1]=1; miscompare[i-1] += r
                bist_fail = 1
        print("Reset test finished. Number of error:", np.sum(fail))

        # This block tests the ScanChain block
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000101 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b01100110 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b01100110 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , 0b11111111 )
        self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 , 0b11111111 )
        fail = np.zeros(16)
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000111 )
        for i in row:
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                print("Test for row", i, "failed")
                fail[i-1]=1; miscompare[i-1] += r
                bist_fail = 1
        print("Scan test 1 finished. Number of error:", np.sum(fail))
        
        # Sanity check of BIST hardware
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000101 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b00000000 )
        self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , 0b00000000 )
        fail = np.zeros(16)
        self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000111 )
        for i in row:
            time.sleep(0.001)
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r != miscompare[i-1]):
                print("Test for row", i, "failed")
                fail[i-1]=1; miscompare[i-1] += r
                bist_fail = 1
        print("Scan test 2 finished. Number of error:", np.sum(fail))

        # Finally, perform BIST with provided test vectors
        count=0
        utils.print_info("->  Doing Row BIST ...")
        f=open('mpa_methods/row_bist_vector.txt','r')
        for l in range(1,306):
            line = int(f.readline(),2)
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
            self.mpa.i2c.row_write('RowLogic_BIST_input_1', 0 , line & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST_input_2', 0 ,(line >> 8) & 0xFF )
            line = int(f.readline(),2)
            self.mpa.i2c.row_write('RowLogic_BIST_ref_output_1', 0 , line & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST_ref_output_2', 0 ,(line >> 8) & 0xFF )
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000011 )
            self.mpa.i2c.row_write('RowLogic_BIST', 0 , 0b00000001 )
            if (vector_fail):
                for i in row:
                    r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                    if (r == None): 
                        self.fc7.activate_I2C_chip(verbose = 0)
                        time.sleep(0.001)
                        r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                        print("repeat read operation for row", r, "at vector", l )
                    if (r != miscompare[i-1]):
                        print("Row:", i, ", N of failed at vector: " , l)
                        #print("Input Vector: ", self.mpa.i2c.row_read('RowLogic_BIST_input_2', i ), self.mpa.i2c.row_read('RowLogic_BIST_input_1', i ) )
                        #print("Output Vector: ", self.mpa.i2c.row_read('RowLogic_BIST_ref_output_2', i ), self.mpa.i2c.row_read('RowLogic_BIST_ref_output_1', i ) )
                        miscompare[i-1] = r
            line = f.readline()  
        t2 = time.time()
        print("Row BIST Elapsed Time: " + str(t2 - t1))
        for i in row:
            r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
            if (r == None): 
                self.fc7.activate_I2C_chip(verbose = 0)
                time.sleep(0.001)
                r = self.mpa.i2c.row_read('RowBIST_summary_reg', i)
                if verbose: print("repeat read operation for row", r, "at vector", l )
            if verbose: print("Row:", i, ", N of failed at vector: " , r)
            fail_row[i-1] = r
        return fail_row, bist_fail

    def row_bist_voltage_scan(self, n_samples = 10, voltages = range(780, 830, 5), rbr = 1, verbose =1):
        "Used to make nice ROW BIST vs Voltage plots."
        res = []
        bist_rows = np.zeros(16)
        for i in range(0, len(voltages)):
            fail = 0
            print(">>>>>> Testing at voltage", voltages[i]/1000)
            self.mpa.pwr.set_dvdd(voltages[i]/1000)
            self.mpa.pwr.reset_mpa(display=False)
            self.fc7.activate_I2C_chip(verbose = 0)
            self.mpa.ctrl_base.set_row_mask()
            print("Start...")
            for n in range(0, n_samples):
                row_bist_compare = np.zeros(16)
                try:
                    row_bist_compare, bist_fail = self.row_bist_all(sram_test = 0)
                    check5 = (row_bist_compare == 5)
                    print(row_bist_compare)
                except:
                    check5 = False
                    bist_fail =1
                bist_rows = np.vstack((bist_rows, row_bist_compare))
                if (not np.all(check5)) or bist_fail: 
                    fail += 1 
            res.append(n_samples - fail)
            print("Success_rate:", res)
        self.mpa.pwr.set_dvdd(1)     
        res = np.array(res)/n_samples
        #for i in range(0, 16):
        #    plt.plot(voltages, res[:,i], label = str(i))
        #plt.title('BIST results')
        #plt.xlabel('Voltage [mV]')
        #plt.ylabel('Success rate')
        #plt.legend()
        #plt.show()
        return res, bist_rows
    
    def l1_bx_delay(self, ntests):
        #self.mpa.init()
        utils.set_log_files("l1_delay.log", "l1_delay_error.log")
        t0 = time.time()
        time.sleep(0.01)
        exp = 188
        r_size = 5
        record = np.array([np.full(r_size, exp),np.zeros(r_size)])
        utils.print_info("-> Running L1 Delay Test...")
        for i in range(1,ntests+1):
            print(f"Loop {i}", end='\r')
            if (i%500 == 0):
                # Reset L1 ID every 500, since it's size is 9 bit
                #time.sleep(0.01)
                self.fc7.send_resync()
            if not record[0,2] == exp:
                # if middle entry is an error, print record
                utils.print_info(f"\nLoop {i}")
                utils.print_info(f"Error after {round(time.time()-t0, 2)}s")
                utils.print_error(record)
            delay = random.randint(38,187)
            self.fc7.write("fc7_daq_cnfg.physical_interface_block.slvs_debug.SSA_first_counter_del", delay)
            #time.sleep(0.01)
            self.fc7.send_trigger()
            #time.sleep(0.01)
            try:
                bx, l1_id = self.mpa.rdo.read_L1(verbose=0)[-2:] # returns bx and l1_id
                if (bx + delay == exp):
                    res = exp
                else:
                    res = delay
            except: 
                utils.print_error("Error: Header not found!")
                res = delay
                l1_id = 0
            # record 5 values (2 preceding, 2 following and unexpected bx read)
            record = np.pad(record,((0,0),(0,1)), mode='constant')[:,-r_size:] # essentially shift the record left
            record[:,-1] = res, l1_id # record new entry
        t1 = time.time()
        utils.print_info(f"-> Elapsed Time {t1-t0}s")
        utils.close_log_files()
        return True
        # SSA_first_counter_del | expected BX
        # 188 | 	header not found
        # 187 | 	BX 1
        # 150 | 	BX 38
        # 100 | 	BX 88
        # 50  | 	BX 138
        # 38  | 	BX 150 
        # 37  |     header not found
