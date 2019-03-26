#
# Class for radiation test routine
#
#
#
# In order to test:
#   import mpa_methods.RadiationTest as RT
#   TM = RT.TIDMeasurement("../TestFolder")
#   TM.Run("")

import csv
import numpy
import time
import sys
from d19cScripts import *
from myScripts import *
import time
ipaddr, fc7AddrTable, fc7 = SelectBoard('MPA')
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.fast_readout_utility import *
from mpa_methods.bias_calibration import *
from mpa_methods.power_utility import *

class TIDMeasurement:
    def __init__(self, DIR):
        self.start = time.time()
        self.DIR = DIR
        self.LogFile = open(self.DIR+"/LogFile.txt", "w")
        self.GeneralLogFile = open(self.DIR+"/../LogFile.txt", "a")
        self.colprint("Creating new chip measurement: "+self.DIR)
        self.Flag = 1
    def Run(self, chipinfo):
        self.colprint(chipinfo)
        self.colprint_general(chipinfo)
        try:
            # Power in reset state:
            self.colprint("Disabling MPA")
            mpa_disable()
            sleep(1)
            PST1, DP1, AP1 =  measure_current()
            message = "I/O current: " + str(PST1) + " mA"
            message = "Digital current: " + str(DP1) + " mA"
            message = "Analog current: " + str(AP1) + " mA"
            self.colprint(message)
            sleep(1)
            self.colprint("Enabling MPA")
            mpa_enable()
            sleep(1)
            PST2, DP2, AP2 =  measure_current()
            if ( (PST2 < 30) and (DP2 < 200) and (AP2 < 100)): self.colprint("Power within limit")
            self.AlignTests()
            PST3, DP3, AP3 =  measure_current()
            with open(self.DIR+'/PowerMeasurement.csv', 'wb') as csvfile:
                CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                DigP = [DP1, DP2, DP3, AN1, AN2, AN3, PST1, PST2, PST3]
                CVwriter.writerow(DigP)
        except:
            self.colprint("Issue with Power Measurement")
            self.Flag = 0
        try:
            n = 0
            ShiftM = "Shift Test Failed!"
            while n < 2:
                if self.Shift():
                    ShiftM = "Shift Test Passed!"
                    break
                else:
                    n += 1
            if ShiftM == "Shift Test Failed!":
                self.Flag = 0
            self.colprint(ShiftM)
        except:
            self.colprint("Issue with Shift test")
            self.Flag = 0
        sleep(1)
        #try: self.Flag = self.AnalogMeasurement()
        #except:
        #    self.colprint("Issue with Analog Measurement")
        #    self.Flag = 0
        sleep(1)
        try: self.PixTests()
        except:
            self.colprint("Issue with Pixel test")
            self.Flag = 0
        sleep(1)
        try: self.StripInTest()
        except:
            self.colprint("Issue with StripIn test")
            self.Flag = 0
        sleep(1)
        try: self.MemoryTest()
        except:
            self.colprint("Issue with Memory test")
            self.Flag = 0
        self.colprint("DONE!")
        self.end = time.time()
        self.colprint("TOTAL TIME:")
        self.colprint(str((self.end - self.start)/60.))
        self.colprint_general("TOTAL TIME:")
        self.colprint_general(str((self.end - self.start)/60.))
        return self.Flag

    def colprint(self, text):
    	sys.stdout.write("\033[1;31m")
    	print(str(text))
    	sys.stdout.write("\033[0;0m")
        self.LogFile.write(str(text)+"\n")

    def colprint_general(self, text):
        self.GeneralLogFile.write(str(text)+"\n")

    def start_measurement(self, reset = 1):
        if reset: mpa_reset()
        sleep(0.1)
        activate_I2C_chip(frequency = 4, verbose = 0)
        sleep(0.1)
        I2C.peri_write('EdgeSelT1Raw', 0)
        sleep(0.1)
        I2C.peri_write('EdgeSelTrig', 0)

    def AnalogMeasurement(self):
        self.colprint("Getting Curves")
        activate_I2C_chip(verbose = 0)

        self.colprint("DAC measurement")
        measure_DAC_testblocks(point = 0, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC0")
        for block in range(0,7):
            set_DAC(block, 0, 15)
        measure_DAC_testblocks(point = 1, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC1")
        for block in range(0,7):
            set_DAC(block, 1, 15)
        measure_DAC_testblocks(point = 2, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC2")
        for block in range(0,7):
            set_DAC(block, 2, 15)
        measure_DAC_testblocks(point = 3, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC3")
        for block in range(0,7):
            set_DAC(block, 3, 15)
        measure_DAC_testblocks(point = 4, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC4")
        for block in range(0,7):
            set_DAC(block, 4, 15)
        thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/Th_DAC")
        calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/Cal_DAC")
        disable_test()
        mpa_reset()
        activate_I2C_chip()
        I2C.peri_write("ConfSLVS", 0b00111111)
        disable_pixel(0,0)
        align_out()
        trimDAC_amplitude(20)
        thLSB = np.mean((thDAC[:,248] - thDAC[:,0])/248)*1000 #LSB Threshold DAC in mV
        calLSB = np.mean((calDAC[:,248] - calDAC[:,0])/248)*0.035/1.768*1000 #LSB Calibration DAC in fC
        self.colprint("S curve measurement")
        th_H = int(round(150*thLSB/1.456))
        th_L = int(round(110*thLSB/1.456))
        cal_H = int(round(40*0.035/calLSB))
        cal_L = int(round(24*0.035/calLSB))
        sleep(1)
        try:
            sleep(1)
            data_array,th_A, noise_A, pix_out = trimming_chip(s_type = "CAL", ref_val = th_H, nominal_DAC = cal_H, nstep = 1, n_pulse = 200, iteration = 1, extract = 1, plot = 0, stop = 100, ratio = 2.36, print_file = 1, filename = self.DIR+ "/Trim15")
            scurve, th_B, noise_B = s_curve_rbr_fr(n_pulse = 200,  s_type = "CAL", ref_val = th_L, row = range(1,17), step = 1, start = 0, stop = 50, pulse_delay = 200, extract = 1, extract_val = cal_L, plot = 0, print_file = 1, filename = self.DIR+ "/Scurve15")
            gain = (th_H-th_L)/(np.mean(th_A[1:1920]) - np.mean(th_B[1:1920])) * thLSB / calLSB # Average
            self.colprint("The average gain is: " + str(gain))
            self.colprint("The thLSB is: " + str(thLSB))
            self.colprint("The calLSB is: " + str(calLSB))
            self.colprint("The noise is: " + str(np.mean(noise_B)))
            self.colprint("The threshold spread is: " + str(np.std(th_B)))
            self.colprint_general("SCURVE EXTRACTION SUCCESSFUL")
            with open(self.DIR+'/AnalogMeasurement.csv', 'wb') as csvfile:
                CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                AnalogValues = [thLSB, calLSB, noise_B, th_A, gain]
                CVwriter.writerow(AnalogValues)
            return 1
        except TypeError:
            self.colprint("SCURVE EXTRACTION FAILED")
            self.colprint_general("SCURVE EXTRACTION FAILED")
            return 0
        #self.colprint("Trimmed")
        #data_array = trimming_chip_noise(nominal_DAC = 70, nstep = 2, plot = 0, start = 0, stop = 150, ratio = 3.92)
        #self.colprint("Noised")
        #data_array = trimming_chip_cal(nominal_DAC = 100, cal = 15, nstep = 2, plot = 0, data_array = data_array, ratio = 3.92)
        #self.colprint("Caled")
        #download_trimming(self.DIR+"/Trimming")
        #s_curve_rbr_fr(n_pulse = 200, cal = 10, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 0, print_file =1, filename = self.DIR+"/Strobe10")
        #self.colprint("CAL10")
        #s_curve_rbr_fr(n_pulse = 200, cal = 20, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 0, print_file =1, filename = self.DIR+"/Strobe20")
        #self.colprint("CAL20")
        #s_curve_rbr_fr(n_pulse = 200, cal = 30, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 1, print_file =1, filename = self.DIR+"/Strobe30")
        #self.colprint("CAL30")

    def PixTests(self):
        self.colprint("Doing Pixel Tests")
        activate_I2C_chip(verbose = 0)
        #digipix = []
        anapix = []
        #digipix.append(digital_pixel_test(print_log=0))
        anapix.append(analog_pixel_test(print_log=0))
        #if len(digipix[0]) > 0: digipix.append(digital_pixel_test(print_log=0))
        if len(anapix[0]) > 0:
            reset()
            align_out()
            anapix.append(analog_pixel_test(print_log=0))
        #BadPixD = self.GetActualBadPixels(digipix)
        #self.colprint(str(BadPixD) + " << Bad Pixels (Digi)")
        BadPixA = self.GetActualBadPixels(anapix)
        self.colprint(str(BadPixA) + " << Bad Pixels (Ana)")
        self.colprint_general(str(BadPixA) + " << Bad Pixels (Ana)")
        with open(self.DIR+'/BadPixelsA.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixA: CVwriter.writerow(i)
        #with open(self.DIR+'/BadPixelsD.csv', 'wb') as csvfile:
        #    CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
        #    for i in BadPixD: CVwriter.writerow(i)

    def StripInTest(self):
        reset()
        self.start_measurement()
        align_out()
        sleep(0.1)
        strip_in = strip_in_scan(n_pulse = 5, filename = self.DIR + "/striptest", probe=0)
        good_si = 0
        for i in range(0,16):
            if (np.mean(strip_in[i,:] > 0.9) == 1):
                good_si = 1
        if good_si:
            self.colprint("Strip Input scan passed")
            self.colprint_general("Strip Input scan passed")
        else:
            self.colprint("Strip Input scan failed")
            self.colprint_general("Strip Input scan failed")

    def MemoryTest(self):
        mempix = []
        bad_pix, error, stuck, i2c_issue, missing = mem_test(print_log=1, filename = self.DIR + "/LogMemTest_10", gate = 0, verbose = 0)
        mempix.append(bad_pix)
        if len(mempix[0]) > 0:
            sleep(1)
            bad_pix, error, stuck, i2c_issue, missing = mem_test(print_log=1, filename = self.DIR + "/LogMemTest_10_rpt", gate = 0, verbose = 0)
            mempix.append(bad_pix)
        BadPixM = self.GetActualBadPixels(mempix)
        self.colprint(str(BadPixM) + " << Bad Pixels (Mem)")
        with open(self.DIR+'/BadPixelsM_10.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixM: CVwriter.writerow(i)

    def GetActualBadPixels(self, BPA):
        print BPA
        badpix = BPA[0]
        goodpix = []
        for i in range(1, len(BPA)):
            for j in badpix:
                if j not in BPA[i]:
                    goodpix.append(j)
        for i in goodpix:
            badpix.remove(i)
        return badpix

    def Shift(self):
        self.colprint("Doing Shift/Mem Tests")
        self.start_measurement()
        I2C.peri_write("LFSR_data", 0b10101010)
        Check1 = I2C.peri_read("LFSR_data")
        self.colprint("Writing: "+str(bin(Check1)))
        activate_shift()
        sleep(0.1)
        send_test()
        read_regs()
        Check2 = read_regs()
        send_trigger()
        Check3 = read_regs()
        OK = True
        for i,C in enumerate(Check3):
            if bin(C) != "0b10101010101010101010101010101010" and i < 50:
                OK = False
            if bin(C) != "0b0" and i > 49:
                OK = False
        return OK

    def AlignTests(self):
        self.start_measurement()
        #mpa_reset()
        #activate_I2C_chip()
        #I2C.peri_write("ConfSLVS", 0b00111111)
        #disable_pixel(0,0)
        self.colprint("Trying to Align...")
        align_out()
        self.ground = measure_gnd()
        self.colprint("GROUND IS " + str(self.ground))
        self.CV = calibrate_chip(self.ground, filename = self.DIR+"/Bias_DAC")
        print self.CV

        #self.bg = measure_bg()
        #self.BandGapFile = open(self.DIR+"/BandGap.txt", "a")
        #self.BandGapFile.write(str(self.bg))
        #set_nominal()
        #self.colprint("nominal set after calibrate_chip")
        n = 0
        Sum = 0
        Min = 99999
        Max = 0
        for j in self.CV:
            for i in j:
                n += 1
                Sum = Sum + i
                if i < Min: Min = i
                if i > Max: Max = i
        avg = Sum/n
        self.colprint("Alignment DAC Values (avg, min, max)")
        self.colprint(str(avg) +", "+ str(Min) +", "+ str(Max))

if __name__ == '__main__': # TEST
    TEST = TIDMeasurement(sys.argv[1])
    TEST.Run("words")
