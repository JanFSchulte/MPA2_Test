#
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

class ProbeMeasurement:
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
            PowerStatus = self.PowerOnCheck()
            #self.CheckTotalPower()
            DP1 = self.Dig
            AN1 = self.Ana
            PST1 = self.PST
            self.colprint("Enabling MPA")
            MPAEnableCheck = self.MPAEnable()
            if self.CheckTotalPower(True):
                self.colprint("Power after enable is OK!")
                self.colprint_general("Power after enable is OK!")
            DP2 = self.Dig
            AN2 = self.Ana
            PST2 = self.PST
            self.AlignTests()
            if self.CheckTotalPower(True):
                self.colprint("Power after align is OK!")
                self.colprint_general("Power after align is OK!")
            DP3 = self.Dig
            AN3 = self.Ana
            PST3 = self.PST
            with open(self.DIR+'/PowerMeasurement.csv', 'wb') as csvfile:
                CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                DigP = [DP1, DP2, DP3, AN1, AN2, AN3, PST1, PST2, PST3]
                CVwriter.writerow(DigP)
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
            self.Flag = self.Curves()
            mpa_reset()
            self.PixTests()
            self.colprint("DONE!")
            sleep(3)
        except:
            self.colprint("WE MESSED UP!!!")
            self.Flag = 0
        #power_off()
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

    def Curves(self):
        self.colprint("Getting Curves")
        activate_I2C_chip(verbose = 0)

        self.colprint("DAC measurement")
        measure_DAC_testblocks(point = 0, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC0")
        measure_DAC_testblocks(point = 1, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC1")
        measure_DAC_testblocks(point = 2, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC2")
        measure_DAC_testblocks(point = 3, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC3")
        measure_DAC_testblocks(point = 4, bit = 5, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/DAC4")
        thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/Th_DAC")
        calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 1, plot = 0, print_file = 1, filename = self.DIR+"/Cal_DAC")
        disable_test()
        mpa_reset()
        trimDAC_amplitude(20)
        thLSB = np.mean((thDAC[:,248] - thDAC[:,0])/248)*1000 #LSB Threshold DAC in mV
        calLSB = np.mean((calDAC[:,248] - calDAC[:,0])/248)*0.035/1.768*1000 #LSB Calibration DAC in fC
        self.colprint("S curve measurement")
        th_H = int(round(150*thLSB/1.456))
        th_L = int(round(110*thLSB/1.456))
        cal_H = int(round(40*0.035/calLSB))
        cal_L = int(round(22*0.035/calLSB))
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
            self.colprint("The threshold spread is: " + str(np.std(th_A)))
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

        #strip_in = strip_in_scan(n_pulse = 5, filename = self.DIR + "/striptest", probe=1)
        #good_si = 0
        #for i in range(0,16):
        #    if (np.mean(strip_in[i,:] > 0.9) == 1):
        #        good_si = 1
        #if good_si:
        #    self.colprint("Strip Input scan passed")
        #    self.colprint_general("Strip Input scan passed")
        #else:
        #    self.colprint("Strip Input scan failed")
        #    self.colprint_general("Strip Input scan failed")

        set_DVDD(1.2)
        sleep(0.2)
        mpa_reset()
        sleep(0.2)
        reset()
        sleep(0.2)
        align_out()
        sleep(0.2)
        mempix = []
        mempix.append(mem_test(print_log=1, filename = self.DIR + "/LogMemTest_12", gate = 0, verbose = 0))
        if len(mempix[0]) > 0: mempix.append(mem_test(print_log=1, filename = self.DIR + "/LogMemTest_12", gate = 0, verbose = 0))
        BadPixM = self.GetActualBadPixels(mempix)
        self.colprint(str(BadPixM) + " << Bad Pixels (Mem)")
        with open(self.DIR+'/BadPixelsM_12.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixM: CVwriter.writerow(i)

        #if len(BadPixM) > 100 or len(BadPixA) > 100:
        #    self.Flag = 0

        set_DVDD(1.0)
        sleep(0.2)
        mpa_reset()
        sleep(0.2)
        reset()
        sleep(0.2)
        align_out()
        sleep(0.2)
        mempix = []
        mempix.append(mem_test(print_log=1, filename = self.DIR + "/LogMemTest_10", gate = 0, verbose = 0))
        if len(mempix[0]) > 0: mempix.append(mem_test(print_log=1, filename = self.DIR + "/LogMemTest_10", gate = 0, verbose = 0))
        BadPixM = self.GetActualBadPixels(mempix)
        self.colprint(str(BadPixM) + " << Bad Pixels (Mem)")
        with open(self.DIR+'/BadPixelsM_10.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixM: CVwriter.writerow(i)
        set_DVDD(1.2)
        sleep(0.2)
        mpa_reset()
        sleep(0.2)
        reset()
        sleep(0.2)
        align_out()
        sleep(0.2)
        #mem_test(filename = self.DIR + "/memtest.csv")
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
        activate_I2C_chip(verbose = 0)
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
        activate_I2C_chip(verbose = 0)
        activate_sync()
        self.colprint("Trying to Align...")
        align_out()
        align_MPA()
        self.ground = measure_gnd()
        self.colprint("GROUND IS " + str(self.ground))
        self.CV = calibrate_chip(self.ground, filename = self.DIR+"/Bias_DAC")
        print self.CV

        self.bg = measure_bg()
        self.BandGapFile = open(self.DIR+"/BandGap.txt", "a")
        self.BandGapFile.write(str(self.bg))
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
    def PowerOnCheck(self):
        self.DeltaDIG = 0.
        self.PVALS = ["0","0","0"]
        self.colprint("Checking Power-On...")
        PowerMessage = ""
        if self.Power("PST"):
            PowerMessage += "PST power OK! ("+str(self.PVALS[0])+")  "
        else:
            return "PST power too high! ("+str(self.PVALS[0])+")"
        if self.Power("DIG"):
            PowerMessage += "DIG power OK! ("+str(self.PVALS[1])+")  "
        else:
            return "DIG power too high! ("+str(self.PVALS[1])+")"
        if self.Power("ANA"):
            PowerMessage += "ANA power OK! ("+str(self.PVALS[2])+")  "
        else:
            return "ANA power too high! ("+str(self.PVALS[2])+")"
        if self.CheckTotalPower(False):
            return PowerMessage
        else: return "Power too low!"
    def MPAEnable(self):
        if self.Power("MPA"): self.colprint("MPA ENABLED!!")
        else: self.colprint("MPA NOT ENABLED :( ")
    def Power(self, which):
        VDDPST = 1.25
        DVDD = 1.2
        AVDD = 1.25
        VBG = 0.3
        read = 1
    	write = 0
    	cbc3 = 15
    	FAST = 4
    	SLOW = 2
    	mpaid = 0 # default MPa address (0-7)
    	ssaid = 0 # default SSa address (0-7)
    	i2cmux = 0
    	pcf8574 = 1 # MPA and SSA address and reset 8 bit port
    	powerenable = 2    # i2c ID 0x44
    	dac7678 = 4
    	ina226_5 = 5
    	ina226_6 = 6
    	ina226_7 = 7
    	ina226_8 = 8
    	ina226_9 = 9
    	ina226_10 = 10
    	ltc2487 = 3
    	Vc = 0.0003632813 # V/Dac step
    	#Vcshunt = 5.0/4000
    	Vcshunt = 0.00250
    	Rshunt = 0.1

        SetSlaveMap(verbose = 0)
        if which == "PST":
            self.colprint("Turning on PST")
            set_VDDPST()

            Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0, verbose = 0)  #read VR on shunt
            VAL = (Vcshunt * ret)/Rshunt
            self.PVALS[0] = VAL
            if VAL > 30: return 0
        if which == "DIG":
            set_DVDD(V = 1.2)

            Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
            VAL = (Vcshunt * ret)/Rshunt
            self.PVALS[1] = VAL
            if VAL > 200:
                return 0
        if which == "ANA":
            set_AVDD()

            Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
            VAL = (Vcshunt * ret)/Rshunt
            self.PVALS[2] = VAL
            if VAL > 100:
                return 0
        if which == "MPA":
            Vlimit = 0.5
            if (VBG > Vlimit):
                VBG = Vlimit
            Vc2 = 4095/1.5
            setvoltage = int(round(VBG * Vc2))
            setvoltage = setvoltage << 4
            Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01, verbose = 0)  # to SCO on PCA9646
            Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x36, setvoltage, verbose = 0)  # tx to DAC C
            sleep(2)
            val2 = (mpaid << 5) + 16 # reset bit for MPA
            Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02, verbose = 0)  # route to 2nd PCF8574
            Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2, verbose = 0)  # set reset bit
            if not self.CheckTotalPower(True):
                return 0
        return 1
    def GetDigiPower(self):
        read = 1
        write = 0
        cbc3 = 15
        FAST = 4
        SLOW = 2
        mpaid = 0 # default MPa address (0-7)
        ssaid = 0 # default SSa address (0-7)
        i2cmux = 0
        pcf8574 = 1 # MPA and SSA address and reset 8 bit port
        powerenable = 2    # i2c ID 0x44
        dac7678 = 4
        ina226_5 = 5
        ina226_6 = 6
        ina226_7 = 7
        ina226_8 = 8
        ina226_9 = 9
        ina226_10 = 10
        ltc2487 = 3
        Vc = 0.0003632813 # V/Dac step
        #Vcshunt = 5.0/4000
        Vcshunt = 0.00250
        Rshunt = 0.1
        SetSlaveMap(verbose = 0)
        # readDVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
        VDIG = (Vcshunt * ret)/Rshunt
        return VDIG
    def CheckTotalPower(self, enabled):
        read = 1
        write = 0
        cbc3 = 15
        FAST = 4
        SLOW = 2
        mpaid = 0 # default MPa address (0-7)
        ssaid = 0 # default SSa address (0-7)
        i2cmux = 0
        pcf8574 = 1 # MPA and SSA address and reset 8 bit port
        powerenable = 2    # i2c ID 0x44
        dac7678 = 4
        ina226_5 = 5
        ina226_6 = 6
        ina226_7 = 7
        ina226_8 = 8
        ina226_9 = 9
        ina226_10 = 10
        ltc2487 = 3
        Vc = 0.0003632813 # V/Dac step
        #Vcshunt = 5.0/4000
        Vcshunt = 0.00250
        Rshunt = 0.1
        SetSlaveMap(verbose = 0)
        # readVDDPST
        Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0, verbose = 0)  #read VR on shunt
        VPST = (Vcshunt * ret)/Rshunt
        message = "VDDPST current: " + str(VPST) + " mA"
        self.PST = VPST
        self.colprint(message)
        # readDVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
        VDIG = (Vcshunt * ret)/Rshunt
        message = "DVDD current: " + str(VDIG) + " mA"
        self.Dig = VDIG
        self.colprint(message)
        # readAVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW, verbose = 0)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08, verbose = 0)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0, verbose = 0)  # read V on shunt
        VANA = (Vcshunt * ret)/Rshunt
        message = "AVDD current: " + str(VANA) + " mA"
        self.Ana = VANA
        self.colprint(message)
        if (VPST < 10 or VDIG < 15 or VANA < 30) and enabled:
            return 0
        return 1

if __name__ == '__main__': # TEST
    TEST = ProbeMeasurement(sys.argv[1])
    TEST.Run("words")
