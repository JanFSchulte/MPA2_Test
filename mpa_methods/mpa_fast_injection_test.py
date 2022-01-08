#
# Class for fast injection routine
# Up to 20 MHz injection (digital) and 1 MHz trigger
# Check directly done at FW level
#
# In order to test:
#   import mpa_methods.FastInjectionTest as FIT
#   FIM = FIT.FastInjectionMeasurement("../TestFolder")
#   FIM.RunRandomTest8p8s(n = 5, timer_data_taking = 5, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test")

import csv
import numpy
import time
import sys
import random
import matplotlib.pyplot as plt
import matplotlib.axes as ax
#from d19cScripts import *
#from myScripts import *
import time

from utilities.i2c_conf import *
from utilities.power_utility import *
from myScripts.Utilities import *
# from mpa_methods.fast_readout_utility import *
from mpa_methods.mpa_bias_utility import *

class MPAFastInjectionMeasurement:
    def __init__(self, mpa, bias, test, DIR):
        self.start = time.time()
        self.DIR = DIR
        self.LogFile = open(self.DIR+"/LogFile.txt", "w")
        self.GeneralLogFile = open(self.DIR+"/../LogFile.txt", "a")
        utils.print_info(f"->  Radiation test measurement results {self.DIR}")
        self.Flag = 1
        self.mpa = mpa
        self.test = test
        self.bias = bias

    def RunRandomTest8p8s(self, n = 5, timer_data_taking = 5, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test"):
        t0 = time.time()
        folder = self.DIR + "/" + str(runname) + "/"
        os.mkdir(folder)
        folder = self.DIR + "/" + str(runname) + "/Patterns/"
        os.mkdir(folder)
        folder = self.DIR + "/" + str(runname) + "/Error/"
        os.mkdir(folder)
        folder = self.DIR + "/" + str(runname) + "/"
        logname = folder + "RandomTest_8p8s.log"
        f = open(logname, 'w')
        wrong_tot = 	np.zeros(n, dtype = np.int )
        good_tot = 		np.zeros(n, dtype = np.int )
        wrong_tot_L1 = 	np.zeros(n, dtype = np.int )
        good_tot_L1 = 	np.zeros(n, dtype = np.int )
        plt.title("On-line check")
        plt.xlim(0, n)
        plt.ion()
        for i in range(0,n):
            print()
            print("-------------------------------- ITERATION ", str(i), " ---------------------------------------------")
            row_1 = random.sample(list(range(1,9)), 4)
            row_2 = random.sample(list(range(9,17)), 4)
            row = np.sort(np.append(row_1, row_2 ))
            llim = 1
            col = np.zeros(8, dtype = np.int )
            for j in range(0,8):
                temp = random.sample(list(range(llim,15*(j+1))), 1)
                col[j] = temp[0]
                llim = col[j] + 9
            corr = 0
            if (i%2 == 0): corr = 1
            #col = np.array(random.sample(range(1+corr,120,2), 8))
            width = 8*[1]
            strip_64 = np.sort(random.sample(list(range(1+corr,60,2)), 4))
            strip_128 = np.array(random.sample(list(range(61-corr,120,2)), 4))
            strip_128 = -np.sort(-strip_128)
            strip = [strip_64[0], strip_128[0], strip_64[1], strip_128[1], strip_64[2], strip_128[2], strip_64[3], strip_128[3]]

            #print col
            #print row
            #print strip
            
            wrong, good, wrong_L1, good_L1 = self.Run(col, row, width, strip, timer_data_taking = timer_data_taking, offset = 5, cal_pulse_period = cal_pulse_period, l1a_period = l1a_period, latency = latency, print_file = 1, runname = folder, iteration = i, verbose = 0)
            if ((wrong > 100) and (wrong_L1 > 100)): self.Flag = 0
            message = str(row) + ", "; f.write(message)
            message = str(col) + ", "; f.write(message)
            message = str(width) + ", "; f.write(message)
            message = str(strip) + ", "; f.write(message)
            message = str(wrong) + ", "; f.write(message)
            message = str(good) + ", "; f.write(message)
            message = str(wrong_L1) + ", "; f.write(message)
            message = str(good_L1) + ", "; f.write(message)

            wrong_tot[i] = wrong
            wrong_tot_L1[i] = wrong_L1
            good_tot[i] = good
            good_tot_L1[i] = good_L1
            plt.plot(list(range(0,i+1)), wrong_tot[0:i+1], "r*")
            plt.plot(list(range(0,i+1)), wrong_tot_L1[0:i+1], "bo")
            plt.draw()
            plt.pause(0.1)
            t1 = time.time()
            print("Elapsed Time: " + str(t1 - t0))
        f.close()
        self.end = time.time()
        self.colprint("TOTAL TIME:")
        self.colprint(str((self.end - self.start)/60.))
        self.colprint_general("TOTAL TIME:")
        self.colprint_general(str((self.end - self.start)/60.))
        return self.Flag

    def colprint(self, text):
        sys.stdout.write("\033[1;31m")
        print((str(text)))
        sys.stdout.write("\033[0;0m")
        self.LogFile.write(str(text)+"\n")

    def colprint_general(self, text):
        self.GeneralLogFile.write(str(text)+"\n")

    def configureChip(self, latency, offset = 5, analog_injection = 0):
        self.mpa.pwr.set_dvdd(1.2)
        #I2C configuration
        self.mpa.fc7.activate_I2C_chip(frequency = 4, verbose = 0)
        time.sleep(0.01)
        self.mpa.ctrl_pix.disable_pixel(0,0)
        time.sleep(0.01)
        self.mpa.i2c.row_write('MemoryControl_1', 0, latency)
        time.sleep(0.01)
        if (latency > 255):
            self.mpa.i2c.row_write('MemoryControl_2', 0, 1) ## Memory Gating bit 2?
        time.sleep(0.01)
        self.mpa.i2c.peri_write('EdgeSelT1Raw', 0)
        time.sleep(0.01)
        self.mpa.i2c.peri_write('EdgeSelTrig', 0) # 1 = rising
        time.sleep(0.01)
        #self.mpa.i2c.peri_write('ECM',  0)
        alignStub = 4
        alignL1 = 3
        align = 0b00000000 | (alignStub << 3) | alignL1
        self.mpa.i2c.peri_write('LatencyRx320', align)
        #self.mpa.i2c.peri_write('LatencyRx320', 0b00101111) # Trigger line aligned with FC7
        #self.mpa.i2c.peri_write('LatencyRx320', 0b00011010) # Setup Test Chip #17
        #self.mpa.i2c.peri_write('LatencyRx320', 0b00011111) # Setup Test Chip #20
        #self.mpa.i2c.peri_write('LatencyRx320', 0b00011111) # Setup Test Chip #20
        # Stub Strip Input
        time.sleep(0.01)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_gen.l1_data", 1)
        time.sleep(0.01)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.ssa_gen.trig_data_delay",7)
        time.sleep(0.01)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.l1_data.SSA_BX_cnt_format", 0)
        time.sleep(0.01)
        #self.mpa.fc7.write("ctrl_phy_ssa_gen_trig_phase",42)
        time.sleep(0.01)
        #self.mpa.i2c.peri_write("SSAOffset_1", offset)
        self.mpa.i2c.peri_write("ConfSLVS", 0b00111111)
        time.sleep(0.01)

        if (analog_injection):
            self.mpa.ctrl_base.set_calibration(100)
            self.mpa.ctrl_base.set_threshold(200)
        else:
            self.mpa.i2c.pixel_write('DigPattern', 0, 0,  0b00000001)
            #set_calibration(100)
            #set_threshold(200)
        time.sleep(0.01)
        utils.print_info("-> Chip configured for SEU")
        #activate_pp()

    def parse_to_bin32(self, input):
        return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)

    def parse_to_bin8(self, input):
        return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

    def parse_to_bin9(self, input):
        return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)

    def configurePixel(self, cluster_col, cluster_row, cluster_width, strip, runname, iteration, analog_injection = 0, verbose = 0, print_file = 0):
        #here define the way to generate stub/centroid data pattern on the MPA/SSA
        if print_file:
            filename = str(runname) + "Patterns/Iter_" + str(iteration)+ "pattern.txt"
            f = open(filename, "a")
            message = "\n"; f.write(message);
            message = "\n"; f.write(message);
        #Variables declaration
        pcluster = ""
        scluster = ""
        n_pclust = len(cluster_col)
        n_sclust = len(strip)

        word = np.zeros(16, dtype = np.uint8)
        row = np.zeros(16, dtype = np.uint8)
        pixel = np.zeros(16, dtype = np.uint8)
        l = np.zeros(10, dtype = np.uint8)
        count = 0
        self.mpa.ctrl_pix.disable_pixel(0,0)
        # Pixel activation
        for i in range(0, n_pclust):
            for j in range(0, cluster_width[i]):
                if (analog_injection):
                    self.mpa.ctrl_pix.enable_pix_EdgeBRcal(cluster_row[i], cluster_col[i] + j)
                else:
                    #self.mpa.i2c.pixel_write('DigPattern', cluster_row[i], cluster_col[i] + j,  0b00000001
                    self.mpa.i2c.pixel_write('PixelEnables', cluster_row[i], cluster_col[i] + j , 0x20) #self.I2C.pixel_write('PixelEnables', r, p, 0x20)
            if (n_pclust > 5):
                if (i != n_pclust-1):
                    row[n_pclust - i -2] = cluster_row[i] - 1
                    pixel[n_pclust - i -2] = cluster_col[i]*2 + cluster_width[i] - 1
                #row[n_pclust - i -1] = cluster_row[i] - 1
                #pixel[n_pclust - i -1] = cluster_col[i]*2 + cluster_width[i] - 1
            else:
                row[n_pclust - i -1] = cluster_row[i] - 1
                pixel[n_pclust - i -1] = cluster_col[i]*2 + cluster_width[i] - 1
            pcluster = pcluster + bin(cluster_col[i]).lstrip('-0b').zfill(7) + bin(cluster_width[i]-1).lstrip('-0b').zfill(3) + bin(cluster_row[i]-1).lstrip('-0b').zfill(4)
            count += 1

        if (strip != []):
            strip_0 = 0
            strip_1 = 0
            strip_2 = 0
            strip_3 = 0
            for i in range(0, n_sclust):
                self.test.strip_in_def( line = i ,strip = 8*[pixel[i]+8])
                if (strip[i] <= 32):
                    strip_3 = strip_3 | (1 << strip[i]-1)
                elif (strip[i] <= 64):
                    strip_2 = strip_2 | (1 << (strip[i]- 32 -1))
                elif (strip[i] <= 96):
                    strip_1 = strip_1 | ( 1 << (strip[i]- 64 - 1))
                elif ((strip[i] <= 120)):
                    strip_0 = strip_0 | ( 1 << (strip[i]- 96 - 1))
                else:
                    print("WARNING: Strip coordinate out of range!")
                scluster = scluster + bin(strip[i]).lstrip('-0b').zfill(7) + bin(0).lstrip('-0b').zfill(4)
            self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.l1_data.format_3", strip_3)
            self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.l1_data.format_2", strip_2)
            self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.l1_data.format_1", strip_1)
            self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.l1_data.format_0", strip_0)
        if (count > 5): count = 5

        # Pattern preparation stubs
        # BX0
        #count = 0
        if verbose:
            print(" Injected pixels: ", pixel)
            print(" Injected row: ", row)
            print(" Injected count: ",count)
            print(" Injected strip: ", strip)
        #print strip_3
        #print strip_2
        #print strip_1
        #print strip_0

        word0  = 0b10000 | ((0b00111 & count) << 1) | ((0b10000000 & pixel[0]) >> 7)
        word1 = ((0b01111100 & pixel[0]) >> 2)
        word2 = ((0b00000011 & pixel[0]) << 3) | 0b000 #Bending 0
        word3 = ((0b00001111 & row[0]) << 1) |((0b10000000 & pixel[1]) >> 7)
        word4 = ((0b01111100 & pixel[1]) >> 2)
        word5 = ((0b00000011 & pixel[1]) << 3) | 0b000 #Bending 0
        word6 = ((0b00001111 & row[1]) << 1) |((0b10000000 & pixel[2]) >> 7)
        word7 = ((0b01111100 & pixel[2]) >> 2)
        # BX1
        word8 = 0b00000 | ((0b00000011 & pixel[2]) << 2) | 0b00 #Bending 0
        word9 = 0b00000 | row[2]
        word10 = ((0b11111000 & pixel[3]) >> 3)
        word11 = ((0b00000111 & pixel[3]) << 2) | 0b00
        word12 = 0b00000 | row[3]
        word13 = ((0b11111000 & pixel[4]) >> 3)
        word14 = ((0b00000111 & pixel[4]) << 2) | 0b00
        word15 = 0b00000 | row[4]
        ###
        l0 = (word0 & 0b10000) << 3 | (word1 & 0b10000) << 2 | (word2 & 0b10000) << 1 | (word3 & 0b10000) << 0 |  (word4 & 0b10000) >> 1 | (word5 & 0b10000) >> 2 | (word6 & 0b10000) >> 3 | (word7 & 0b10000) >> 4
        l1 = (word0 & 0b01000) << 4 | (word1 & 0b01000) << 3 | (word2 & 0b01000) << 2 | (word3 & 0b01000) << 1 |  (word4 & 0b01000) << 0 | (word5 & 0b01000) >> 1 | (word6 & 0b01000) >> 2 | (word7 & 0b01000) >> 3
        l2 = (word0 & 0b00100) << 5 | (word1 & 0b00100) << 4 | (word2 & 0b00100) << 3 | (word3 & 0b00100) << 2 |  (word4 & 0b00100) << 1 | (word5 & 0b00100) << 0 | (word6 & 0b00100) >> 1 | (word7 & 0b00100) >> 2
        l3 = (word0 & 0b00010) << 6 | (word1 & 0b00010) << 5 | (word2 & 0b00010) << 4 | (word3 & 0b00010) << 3 |  (word4 & 0b00010) << 2 | (word5 & 0b00010) << 1 | (word6 & 0b00010) << 0 | (word7 & 0b00010) >> 1
        l4 = (word0 & 0b00001) << 7 | (word1 & 0b00001) << 6 | (word2 & 0b00001) << 5 | (word3 & 0b00001) << 4 |  (word4 & 0b00001) << 3 | (word5 & 0b00001) << 2 | (word6 & 0b00001) << 1 | (word7 & 0b00001) << 0
        l5 = (word8 & 0b10000) << 3 | (word9 & 0b10000) << 2 | (word10 & 0b10000) << 1 | (word11 & 0b10000) << 0 |  (word12 & 0b10000) >> 1 | (word13 & 0b10000) >> 2 | (word14 & 0b10000) >> 3 | (word15 & 0b10000) >> 4
        l6 = (word8 & 0b01000) << 4 | (word9 & 0b01000) << 3 | (word10 & 0b01000) << 2 | (word11 & 0b01000) << 1 |  (word12 & 0b01000) << 0 | (word13 & 0b01000) >> 1 | (word14 & 0b01000) >> 2 | (word15 & 0b01000) >> 3
        l7 = (word8 & 0b00100) << 5 | (word9 & 0b00100) << 4 | (word10 & 0b00100) << 3 | (word11 & 0b00100) << 2 |  (word12 & 0b00100) << 1 | (word13 & 0b00100) << 0 | (word14 & 0b00100) >> 1 | (word15 & 0b00100) >> 2
        l8 = (word8 & 0b00010) << 6 | (word9 & 0b00010) << 5 | (word10 & 0b00010) << 4 | (word11 & 0b00010) << 3 |  (word12 & 0b00010) << 2 | (word13 & 0b00010) << 1 | (word14 & 0b00010) << 0 | (word15 & 0b00010) >> 1
        l9 = (word8 & 0b00001) << 7 | (word9 & 0b00001) << 6 | (word10 & 0b00001) << 5 | (word11 & 0b00001) << 4 |  (word12 & 0b00001) << 3 | (word13 & 0b00001) << 2 | (word14 & 0b00001) << 1 | (word15 & 0b00001) << 0

        if (verbose):
            print(self.parse_to_bin8(l4))
            print(self.parse_to_bin8(l3))
            print(self.parse_to_bin8(l2))
            print(self.parse_to_bin8(l1))
            print(self.parse_to_bin8(l0))
            print(self.parse_to_bin8(l9))
            print(self.parse_to_bin8(l8))
            print(self.parse_to_bin8(l7))
            print(self.parse_to_bin8(l6))
            print(self.parse_to_bin8(l5))
        if print_file:
            f.write("Stub pattern check")
            message = self.parse_to_bin8(l4) + "\n"; f.write(message);
            message = self.parse_to_bin8(l3) + "\n"; f.write(message);
            message = self.parse_to_bin8(l2) + "\n"; f.write(message);
            message = self.parse_to_bin8(l1) + "\n"; f.write(message);
            message = self.parse_to_bin8(l0) + "\n"; f.write(message);
            message = self.parse_to_bin8(l9) + "\n"; f.write(message);
            message = self.parse_to_bin8(l8) + "\n"; f.write(message);
            message = self.parse_to_bin8(l7) + "\n"; f.write(message);
            message = self.parse_to_bin8(l6) + "\n"; f.write(message);
            message = self.parse_to_bin8(l5) + "\n"; f.write(message);

        pattern1 = self.parse_to_bin8(l3) + self.parse_to_bin8(l2) + self.parse_to_bin8(l1) + self.parse_to_bin8(l0)
        pattern2 = self.parse_to_bin8(l8) + self.parse_to_bin8(l7) + self.parse_to_bin8(l6) + self.parse_to_bin8(l5)
        pattern3 = self.parse_to_bin8(0)  + self.parse_to_bin8(0)  + self.parse_to_bin8(l9) + self.parse_to_bin8(l4)
        self.loadCheckPatternOnFC7(int(pattern1, 2), int(pattern2, 2), int(pattern3, 2))

        # Pattern preparation L1
        payload = bin(2).lstrip('-0b').zfill(2) +  bin(0).lstrip('-0b').zfill(9) + "0" + bin(n_sclust).lstrip('-0b').zfill(5) + bin(n_pclust).lstrip('-0b').zfill(5) + "0" + scluster + pcluster  + bin(cluster_col[n_pclust-1] & 0b1111110).lstrip('-0b').zfill(7)+ bin(0).lstrip('-0b').zfill(32)
        #+ bin(cluster_col[n_pclust-1] & 0b1111000).lstrip('-0b').zfill(7)
        if print_file:
            f.write("L1 pattern check:\n")
            f.write(payload)
        pattern7 = 0
        pattern6 = 0
        pattern5 = 0
        pattern4 = 0
        pattern3 = 0
        pattern2 = 0
        pattern1 = 0
        if (verbose): print(payload)
        try:
            pattern7 = int(payload[0:   32], 2)
            pattern6 = int(payload[32:  64], 2)
            pattern5 = int(payload[64:  96], 2)
            pattern4 = int(payload[96:  128], 2)
            pattern3 = int(payload[128: 160], 2)
            pattern2 = int(payload[160: 192], 2)
            pattern1 = int(payload[192: 224], 2)
        except ValueError:
            if (verbose): print("Empty Pattern")
        self.loadCheckPatternOnFC7L1(pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7)
        if print_file:	f.close()

    def loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, verbose = 0):
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.check_patterns1",pattern1)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.check_patterns2",pattern2)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.check_patterns3",pattern3)
        #time.sleep(0.5)
        if (verbose):
            print("Content of the patterns1 cnfg register: ",self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.check_patterns1"))
            print("Content of the patterns2 cnfg register: ",self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.check_patterns2"))
            print("Content of the patterns3 cnfg register: ",self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.check_patterns3"))

    def loadCheckPatternOnFC7L1(self, pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, verbose = 0):

        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns1",pattern1)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns2",pattern2)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns3",pattern3)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns4",pattern4)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns5",pattern5)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns6",pattern6)
        self.mpa.fc7.write("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns7",pattern7)
        #time.sleep(0.5)
        if (verbose):
            print("Content of the patterns1 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns1")))
            print("Content of the patterns2 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns2")))
            print("Content of the patterns3 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns3")))
            print("Content of the patterns4 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns4")))
            print("Content of the patterns5 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns5")))
            print("Content of the patterns6 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns6")))
            print("Content of the patterns7 cnfg register: ",self.parse_to_bin32(self.mpa.fc7.read("fc7_daq_cnfg.physical_interface_block.seu.l1_check_patterns7")))

    def delayDataTaking(self):
        #below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "self.mpa.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
        print("BX indicator for SSA centroid data:", self.mpa.fc7.read("stat_phy_slvs_compare_fifo_bx_indicator"))
        #self.mpa.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
        time.sleep(1)

    def printInfo(self, message):
        print()
        print(message)
        print("*** STUB ***")
        print("State of FSM: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
        print("FIFO almost full: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full"))
        print("number of events written to FIFO", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo"))
        print("Number of good 2xBX STUBS: ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare_number_good_data"))
        print()
        print("*** L1 ***")
        print("State of FSM: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.state_machine"))
        print("Fifo almost full: ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full"))
        print("Header # ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_l1_headers_found"))
        print("Trigger # ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_l1_triggers"))
        print("number of events written to FIFO", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_good_data"))
        print("number of matched events:", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_good_data"))
        print("*************************")

    def RunStateMachine(self, runname, iteration, print_file, timer_data_taking, latency):
        self.mpa.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.l1_start",1)
        self.mpa.fc7.SendCommand_CTRL("start_trigger")
        time.sleep(0.01)
        FSM = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
        if (FSM == 4):
            print("-----------------------------")
            print("-----------------------------")
            print("-----------------------------")
            print("Error in FSM")
            print("-----------------------------")
            print("-----------------------------")
            print("-----------------------------")
            return
        self.mpa.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.start",1)

        #start taking data and check the 80% full threshold of the FIFO (on FC7?)
        FIFO_almost_full = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full")
        FIFO_almost_full_L1 = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
        timer = 0
        time.sleep(1)
        self.mpa.fc7.activate_I2C_chip(verbose = 0)
        while(FIFO_almost_full != 1 and FIFO_almost_full_L1 != 1 and timer < timer_data_taking):
            FIFO_almost_full = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full")
            FIFO_almost_full_L1 = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
            timer = timer + 5
            message = "TIMER at: ", timer, "/", timer_data_taking
            self.printInfo(message)
            time.sleep(5)
        self.mpa.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.stop",1)
        time.sleep(0.01)
        self.mpa.fc7.SendCommand_CTRL("stop_trigger")
        FIFO_almost_full = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full")
        FIFO_almost_full_L1 = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")

        message = "-------------------------------- RESULTS ITERATION " + str(iteration) + " ---------------------------------------------"
        self.printInfo(message)
        n = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
        if (latency == 500): l1_limit = 12
        else: l1_limit = 7
        if ((n > 0) and print_file):
            filename = str(runname) + "Error/Iter_" + str(iteration) + "_STUB" + ".csv"
            self.writeFIFO(n, filename)
        n = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo")
        if ((n > l1_limit ) and print_file):
            filename = str(runname) + "Error/Iter_" + str(iteration)+ "_L1" +  ".csv"
            self.writeFIFO_L1(n, filename)
        return 	self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo"), self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare_number_good_data"), self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo"), self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_good_data")

    def writeFIFO(self, n = 16386, filename = "test.log"):
        f = open(filename, 'w')
        stat_phy_slvs_compare_data_ready = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.data_ready")
        for i in range (0,n):
            fifo1_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data1_fifo")
            fifo2_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo")
            fifo3_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data3_fifo")
            fifo4_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo")
            message = str(i) + ", "
            f.write(message); message = str(fifo4_word) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo3_word & 0x0000ff00)>>8)) + ", "
            f.write(message); message = str(self.parse_to_bin8(fifo3_word & 0x000000ff)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo2_word & 0xff000000)>>24)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8)) + ", "
            f.write(message); message = str(self.parse_to_bin8(fifo2_word & 0x000000ff)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo1_word & 0xff000000)>>24)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16)) + ", "
            f.write(message); message = str(self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8)) + ", "
            f.write(message); message = str(self.parse_to_bin8(fifo1_word & 0x000000ff)) + "\n"
            f.write(message)
        f.close

    def ReadFIFOs(self, chip, n = 16386):
        print("!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!")
        print("State of FSM before reading FIFOs: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
        print("Now printing the data in the FIFO:")
        stat_phy_slvs_compare_data_ready = self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.data_ready")
        i = 0

        """package2 = fc7.fifoRead("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo", 17000)
        p l5, l6, l7ackage4 = fc7.fifoRead("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo", 17000)
        for i in range(16384):
            print "Package2 #", i+1, ": ", package2[i]
            print "Package4 #", i+1, ": ", package4[i]
        print("State of FSM after reading FIFOs: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
        print("Fifo almost full: ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full"))"""

        for i in range (0,n):
                print("--------------------------")
                print(("Entry number: ", i ," in the FIFO:"))
                fifo1_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data1_fifo")
                fifo2_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo")
                fifo3_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data3_fifo")
                fifo4_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo")
                print("MPA: BX counter, 0x0000, BX0 data (l4, l3, l2, l1, l0) and  BX1 data (l4, l3, l2, l1, l0)")
                print("SSA: 0x0000, BX counter, 0x0000 and centroid data (l7, l6, l5, l4, l3, l2, l1, l0)")
                print((self.parse_to_bin32(fifo4_word),self.parse_to_bin32(fifo3_word),self.parse_to_bin32(fifo2_word),self.parse_to_bin32(fifo1_word)))
                print((fifo4_word,fifo3_word,fifo2_word,fifo1_word))

                print("BX counter:", fifo4_word)
                if(chip == "MPA"):
                    print("MPA stub BX0 l4: ", self.parse_to_bin8((fifo3_word & 0x0000ff00)>>8))
                    print("MPA stub BX0 l3: ", self.parse_to_bin8(fifo3_word & 0x000000ff))
                    print("MPA stub BX0 l2: ", self.parse_to_bin8((fifo2_word & 0xff000000)>>24))
                    print("MPA stub BX0 l1: ", self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16))
                    print("MPA stub BX0 l0: ", self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8))

                    print("MPA stub BX1 l4: ", self.parse_to_bin8(fifo2_word & 0x000000ff))
                    print("MPA stub BX1 l3: ", self.parse_to_bin8((fifo1_word & 0xff000000)>>24))
                    print("MPA stub BX1 l2: ", self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16))
                    print("MPA stub BX1 l1: ", self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8))
                    print("MPA stub BX1 l0: ", self.parse_to_bin8(fifo1_word & 0x000000ff))
                elif(chip == "SSA"):
                    print("SSA centroid l7: ", self.parse_to_bin8((fifo2_word & 0xff000000)>>24))
                    print("SSA centroid l6: ", self.parse_to_bin8((fifo2_word & 0x00ff0000)>>16))
                    print("SSA centroid l5: ", self.parse_to_bin8((fifo2_word & 0x0000ff00)>>8))
                    print("SSA centroid l4: ", self.parse_to_bin8(fifo2_word & 0x000000ff))

                    print("SSA centroid l3: ", self.parse_to_bin8((fifo1_word & 0xff000000)>>24))
                    print("SSA centroid l2: ", self.parse_to_bin8((fifo1_word & 0x00ff0000)>>16))
                    print("SSA centroid l1: ", self.parse_to_bin8((fifo1_word & 0x0000ff00)>>8))
                    print("SSA centroid l0: ", self.parse_to_bin8(fifo1_word & 0x000000ff))
                else:
                    print("CHIPTYPE UNKNOWN")

        print("State of FSM after reading FIFOs: " , self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
        print("Fifo almost full: ", self.mpa.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.fifo_almost_full"))

    def ReadFIFOsL1(self, n = 16386, verbose = 1):
        #print "!!!!!!!!!!!!!!!!!!!START READING FIFO NOW!!!!!!!!!!!!!!!!!!!!!!"
        #printInfo("BEFORE READING FIFO:")
        #print "Now printing the data in the FIFO:"
        t0 = time.time()
        i = 0
        for i in range (0,n):
                fifo1_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data1_fifo")
                fifo2_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data2_fifo")
                fifo3_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data3_fifo")
                fifo4_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data4_fifo")
                fifo5_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data5_fifo")
                fifo6_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data6_fifo")
                fifo7_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data7_fifo")
                fifo8_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data8_fifo")
                fifo9_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo")
                if (verbose):
                    print("--------------------------")
                    print(("Entry number: ", i ," in the FIFO:"))
                    print("Full l1 data package without the header (MSB downto LSB): ")
                    print((self.parse_to_bin32(fifo7_word),self.parse_to_bin32(fifo6_word),self.parse_to_bin32(fifo5_word),self.parse_to_bin32(fifo4_word),self.parse_to_bin32(fifo3_word),self.parse_to_bin32(fifo2_word),self.parse_to_bin32(fifo1_word)))
                    print("l1 counter: ", self.parse_to_bin9((fifo7_word & 0x3FE00000)>>21))
                    print("l1 counter: ", (fifo7_word & 0x3FE00000)>>21)
                    print("FC7 l1 mirror counter: ", (fifo9_word & 0x000001FF))
                    print("BX counter: ", fifo8_word)
        t1 = time.time()
        print("END")
        print("Elapsed Time: " + str(t1 - t0))
        #printInfo("AFTER READING FIFO:")

    def writeFIFO_L1(self, n = 16386, filename = "test_L1.csv"):
        f = open(filename, 'w')
        for i in range (0,n):
            fifo1_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data1_fifo")
            fifo2_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data2_fifo")
            fifo3_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data3_fifo")
            fifo4_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data4_fifo")
            fifo5_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data5_fifo")
            fifo6_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data6_fifo")
            fifo7_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data7_fifo")
            fifo8_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data8_fifo")
            fifo9_word = self.mpa.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo")
            message = str(fifo8_word) + ", " + str(fifo9_word & 0x000001FF) + ", " + str((fifo7_word & 0x3FE00000)>>21) + ", " + str(self.parse_to_bin32(fifo7_word) + self.parse_to_bin32(fifo6_word) + self.parse_to_bin32(fifo5_word) + self.parse_to_bin32(fifo4_word) + self.parse_to_bin32(fifo3_word) + self.parse_to_bin32(fifo2_word) + self.parse_to_bin32(fifo1_word)) +"\n"
            f.write(message);
        f.close


    def Run(self, col, row, width, strip, timer_data_taking = 5, offset = 5, cal_pulse_period = 10, l1a_period = 101, latency = 100, diff = 2, skip = 1, verbose = 0, print_file = 0, runname =  "../cernbox/SEU_results/", iteration = 0):
        self.mpa.reset()
        time.sleep(0.1)
        self.mpa.fc7.reset()
        time.sleep(0.1)
        self.mpa.fc7.SendCommand_CTRL("fast_fast_reset")
        time.sleep(0.1)
        self.configureChip( latency = latency - diff,  offset = offset, analog_injection = 0)
        time.sleep(0.1)
        #self.mpa.ctrl_base.align_out(verbose =1)
        self.mpa.ctrl_base.align_out_all(pattern = 0b10100000)
        if (skip == 0):
            Configure_TestPulse_MPA(delay_after_fast_reset = 512, delay_after_test_pulse = latency, delay_before_next_pulse = cal_pulse_period, number_of_test_pulses = 0, enable_L1 = 1, enable_rst = 0, enable_init_rst = 1)
        else:
            self.mpa.fc7.Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses = 0)
        self.configurePixel(col,  row, width, strip, runname = runname, iteration = iteration, print_file = print_file, analog_injection = 0, verbose = verbose)
        utils.print_info("-> Fast injection configuration completed")
        wrong, good, wrong_L1, good_L1 = self.RunStateMachine(runname = runname, iteration = iteration, print_file = print_file, timer_data_taking = timer_data_taking, latency = latency)
        return wrong, good, wrong_L1, good_L1

if __name__ == '__main__': # TEST
    TEST = MPAFastInjectionMeasurement(sys.argv[1])
    TEST.Run("words")
