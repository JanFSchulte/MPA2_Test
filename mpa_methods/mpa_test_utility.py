
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

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
        self.I2C = I2C
        self.fc7 = fc7

    def shift(self, verbose = 0):
        """

        :param verbose:  (Default value = 0)

        """
        if verbose: print("Doing Shift Test")
        self.I2C.peri_write("LFSR_data", 0b10101010)
        checkI2C = self.I2C.peri_read("LFSR_data")
        if verbose: print("Writing:", str(bin(checkI2C)))
        self.mpa.ctrl_base.activate_shift()
        time.sleep(0.1)
        self.fc7.send_test()
        time.sleep(0.1)
        self.fc7.send_trigger()
        time.sleep(0.1)
        check = read_regs(verbose = verbose)
        OK = True
        for i,C in enumerate(check):
            if bin(C) != "0b10101010101010101010101010101010" and i < 50: OK = False
            if bin(C) != "0b0" and i > 49: OK = False
        if verbose:
            if OK: print("Test Passed")
            else: print("Test Failed")
        return OK

    def test_pp_digital(self, row, pixel):
        """
        :param row:
        :param pixel:
        """
        self.I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
        self.fc7.send_test(8)
        return read_stubs(fast = 1)

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
        self.mpa.ctrl_base.activate_sync()
        time.sleep(0.1)
        self.mpa.ctrl_base.activate_pp()
        time.sleep(0.1)
        self.I2C.pixel_write('DigPattern', 0, 0,  0b10000000)
        time.sleep(0.1)
        self.I2C.peri_write('RetimePix', 1)
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
        print("END")
        print("Elapsed Time: " + str(t1 - t0))
        return OutputBadPix

    def test_pp_analog(self, row, pixel):
        """

        :param row:
        :param pixel:

        """
        self.mpa.ctrl_pix.enable_pix_EdgeBRcal(row, pixel)
        #time.sleep(0.001)
        self.fc7.send_test(8)
        return read_stubs(fast = 1)

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
        print("END")
        print("Elapsed Time: " + str(t1 - t0))
        return OutputBadPix

    def reset_strip_in(self,  line = list(range(0,8)), strip = [0, 0, 0, 0, 0, 0, 0, 0]):
        """STRIP Input test

        :param line:  (Default value = list(range(0)
        :param strip:  (Default value = [0)

        """
        value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
        for l in line:
            reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(l) + "_0"
            self.fc7.write(reg, value)
            value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
            reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(l) + "_1"
            self.fc7.write(reg, value)

    def strip_in_def( self, line ,strip = 8*[128]):
        """

        :param line:
        :param strip:  (Default value = 8*[128])

        """
        value = strip[0] << 24 | strip[1] << 16 | strip[2] << 8 | strip[3]
        reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(line) + "_0"
        self.fc7.write(reg, value)
        value = strip[4] << 24 | strip[5] << 16 | strip[6] << 8 | strip[7]
        reg = "cnfg_phy_SSA_gen_stub_data_format_" +str(line) + "_1"
        self.fc7.write(reg, value)

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
        self.I2C.peri_write('EdgeSelTrig',edge) # 1 = rising
        self.I2C.peri_write('LatencyRx320', latency) # Trigger line aligned with FC7
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
                    nst, pos, Z, bend = read_stubs()
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

        Parameters
        ----------
        n_pulse : int, optional
            [description], by default 1
        edge : str, optional
            [description], by default "falling"
        probe : int, optional
            1 if using wafer prober, by default 0 (carrier board)
        print_file : int, optional
            [description], by default 0
        filename : str, optional
            [description], by default "../cernbox/MPA_Results/strip_in_scan"
        verbose : int, optional
            [description], by default 1

        Returns
        -------
        data_array: 8x8 np.array
            [description]
        """
        t0 = time.time()
        self.mpa.ctrl_base.activate_ss()
        data_array = np.zeros((8, 8 ), dtype = np.float16 )
        if probe:
            self.I2C.peri_write("InSetting_0",0)
            self.I2C.peri_write("InSetting_1",1)
            self.I2C.peri_write("InSetting_2",2)
            self.I2C.peri_write("InSetting_3",3)
            self.I2C.peri_write("InSetting_4",4)
            self.I2C.peri_write("InSetting_5",5)
            self.I2C.peri_write("InSetting_6",6)
            self.I2C.peri_write("InSetting_7",7)
            self.I2C.peri_write("InSetting_8",8)
        time.sleep(0.1)
        
        for i in range(0,8):
            latency = (i  << 3)
            if verbose: print("Testing Latency ", i)
            if (edge == "falling" ): temp = self.strip_in_test(n_pulse = n_pulse, latency = latency , edge = 0)
            elif (edge == "rising" ): temp = self.strip_in_test(n_pulse = n_pulse, latency = latency , edge = 255)
            else: print("edge not recognized"); return
            for line in range(0,8):
                data_array[i, line ] = np.average(temp[line])/(n_pulse*8)
        if print_file:
            CSV.ArrayToCSV (data_array, str(filename) + "_npulse_" + str(n_pulse) + ".csv")
        t1 = time.time()
        print("END")
        print("Elapsed Time: " + str(t1 - t0))
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
            self.I2C.pixel_write('ENFLAGS', row, pixel, 0x20)
        else:
            self.mpa.ctrl_pix.enable_pix_LevelBRcal(row,pixel, polarity = "rise")
        #time.sleep(0.001)
        self.fc7.SendCommand_CTRL("start_trigger")
        #time.sleep(0.001)
        return read_L1(verbose)


    def rnd_pixel(self, row = [1,16], pixel = [1,120], dig_inj = 1, verbose = 1):
        """ Returns one random pixel coordinate in given range and passes it to memory_test

        :param row:
        :param pixel:

        """
        r_rnd = random.randint(min(row), max(row))
        p_rnd = random.randint(min(pixel), max(pixel))

        if verbose : utils.print_info(f"Pixel: {p_rnd} of Row: {r_rnd}")

        self.mpa.ctrl_pix.disable_pixel(0,0)
        if dig_inj:
            self.I2C.pixel_write('ENFLAGS', r_rnd, p_rnd, 0x20)
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
        self.I2C.row_write('L1Offset_1', 0,  latency - diff)
        self.I2C.row_write('L1Offset_2', 0,  0)
        self.I2C.row_write('MemGatEn', 0,  gate)
        self.I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
        self.fc7.write("cnfg_fast_backpressure_enable", 0)
        self.mpa.ctrl_pix.disable_pixel(0,0)

        stuck = 0; i2c_issue = 0; error = 0

        Configure_TestPulse_MPA(delay_after_fast_reset = delay[0] + 512, delay_after_test_pulse = latency, delay_before_next_pulse = 200, number_of_test_pulses = 1, enable_L1 = 1, enable_rst = 1, enable_init_rst = 1)

        for n in range(0, n_tests):
            #time.sleep(0.1)

            # trigger test pulse for random pixel and get injection coordinate
            p, r = self.rnd_pixel(dig_inj = 1)

            strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = read_L1(verbose)
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

        print("-------------------------------------")
        print("-------------------------------------")
        print(" Number of tests: ", n_tests)
        print(" Number of error: ", error)
        print(" Number of stucks: ", stuck)
        print(" Number of I2C issues: ", i2c_issue)

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
        print(" Elapsed Time: " + str(t1 - t0))
        print("-------------------------------------")
        print("-------------------------------------")

        return bad_pix, error, stuck, i2c_issue

    def mem_test(self, latency = 255, delay = [10], row = list(range(1,17)), pixel = list(range(1,121)), diff = 2, print_log = 0, filename =  "../cernbox/MPA_Results/digital_mem_test.log", dig_inj =1, gate = 0, verbose = 1):
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
        print("Running Test:")
        if print_log:
            f = open(filename, 'w')
            f.write("Starting Test:\n")
        self.mpa.ctrl_base.activate_sync()
        self.mpa.ctrl_base.activate_pp()
        self.I2C.row_write('L1Offset_1', 0,  latency - diff)
        self.I2C.row_write('L1Offset_2', 0,  0)
        self.I2C.row_write('MemGatEn', 0,  gate)
        self.I2C.pixel_write('DigPattern', 0, 0,  0b00000001)
        self.fc7.write("cnfg_fast_backpressure_enable", 0)
        self.mpa.ctrl_pix.disable_pixel(0,0)
        stuck = 0; i2c_issue = 0; error = 0; missing = 0
        for d in delay:
            Configure_TestPulse_MPA(delay_after_fast_reset = d + 512, delay_after_test_pulse = latency, delay_before_next_pulse = 200, number_of_test_pulses = 1, enable_L1 = 1, enable_rst = 1, enable_init_rst = 1)
            time.sleep(0.1)
            ## Automatic change of sampling edge on error
            #try:
            #	strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = memory_test(latency = latency, row = 10, pixel = 5, diff = diff, dig_inj = dig_inj, verbose = 0)
            #except TypeError:
            #	print "Header not Found! Changing sampling phase of T1"
            #	I2C.peri_write('EdgeSelT1Raw', 0)
            #time.sleep(1)
            for r in row:
                for p in pixel:
                    #try:
                    strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z  = self.memory_test(latency = latency, row = r, pixel = p, diff = diff, dig_inj = dig_inj, verbose = 0)
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
        print("-------------------------------------")
        print("-------------------------------------")
        print(" Number of error: ", error)
        print(" Number of stucks: ", stuck)
        print(" Number of I2C issues: ", i2c_issue)
        print(" Number of missing: ", missing)
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
        print(" Elapsed Time: " + str(t1 - t0))
        print("-------------------------------------")
        print("-------------------------------------")

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
