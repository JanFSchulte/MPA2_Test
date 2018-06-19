#
import csv
import numpy
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
    def __init__(self, tag):
        self.start = time.time()
        self.tag = tag # UNIQUE ID
        self.DIR = "../ProbeStationResults/"+self.tag
        exists = False
        version = 0
        while not exists:
            if not os.path.exists(self.DIR+"_v"+str(version)):
                self.DIR = self.DIR+"_v"+str(version)
                os.makedirs(self.DIR)
                exists = True
            version += 1
        self.LogFile = open(self.DIR+"/LogFile.txt", "w")
        sys.stdout = open(self.DIR+"/VerboseLogFile.txt", "w")
        self.colprint("Creating new chip measurement: "+self.tag)
        try:
            PowerStatus = self.PowerOnCheck()
            self.colprint("Enabling MPA")
            MPAEnableCheck = self.MPAEnable()
            if self.CheckTotalPower(True):
                self.colprint("Power is OK!")
            DP2 = self.GetDigiPower()
            self.AlignTests()
            DP3 = self.GetDigiPower()
            with open(self.DIR+'/DigiPowerPoints.csv', 'wb') as csvfile:
                CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                DigP = [self.DP1, DP2, DP3, (DP2-self.DP1), (DP3-self.DP1)]
                CVwriter.writerow(DigP)
            n = 0
            ShiftM = "Shift Test Failed!"
            while n < 2:
                if self.Shift():
                    ShiftM = "Shift Test Passed!"
                    break
                else:
                    n += 1
            self.colprint(ShiftM)
            self.PixTests()
            self.Curves()
            self.colprint("DONE!")
            sleep(3)
        except: self.colprint("WE MESSED UP!!!")
        power_off()
        self.end = time.time()
        self.colprint("TOTAL TIME:")
        self.colprint(str((self.end - self.start)/60.))

    def colprint(self, text):
    	sys.stdout.write("\033[1;31m")
    	print(str(text))
    	sys.stdout.write("\033[0;0m")
        self.LogFile.write(str(text)+"\n")
    def Curves(self):
        self.colprint("Getting Curves")
        activate_I2C_chip()
        trimDAC_amplitude(20)
        self.colprint("Trimmed")
        data_array = trimming_chip_noise(nominal_DAC = 70, nstep = 2, plot = 0, start = 0, stop = 150, ratio = 3.92)
        self.colprint("Noised")
        data_array = trimming_chip_cal(nominal_DAC = 100, cal = 15, nstep = 2, plot = 0, data_array = data_array, ratio = 3.92)
        self.colprint("Caled")
        download_trimming(self.DIR+"/Trimming")
        s_curve_rbr_fr(n_pulse = 200, cal = 10, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 0, print_file =1, filename = self.DIR+"/Strobe10")
        self.colprint("CAL10")
        s_curve_rbr_fr(n_pulse = 200, cal = 20, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 0, print_file =1, filename = self.DIR+"/Strobe20")
        self.colprint("CAL20")
        s_curve_rbr_fr(n_pulse = 200, cal = 30, row = range(1,17), step = 1, start = 50, stop = 200, pulse_delay = 50, plot = 1, print_file =1, filename = self.DIR+"/Strobe30")
        self.colprint("CAL30")
    def PixTests(self):
        self.colprint("Doing Pixel Tests")
        activate_I2C_chip()
        digipix = []
        anapix = []
        digipix.append(digital_pixel_test(print_log=0))
        anapix.append(analog_pixel_test(print_log=0))
        if len(digipix[0]) > 0: digipix.append(digital_pixel_test(print_log=0))
        if len(anapix[0]) > 0: digipix.append(analog_pixel_test(print_log=0))
        BadPixD = self.GetActualBadPixels(digipix)
        self.colprint(str(BadPixD) + " << Bad Pixels (Digi)")
        BadPixA = self.GetActualBadPixels(anapix)
        self.colprint(str(BadPixA) + " << Bad Pixels (Ana)")
        with open(self.DIR+'/BadPixelsA.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixA: CVwriter.writerow(i)
        with open(self.DIR+'/BadPixelsD.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in BadPixD: CVwriter.writerow(i)
        strip_in_scan(n_pulse = 5, filename = self.DIR + "/striptest", probe=1)
        mem_test(filename = self.DIR + "/memtest.csv")
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
        activate_I2C_chip()
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
        activate_I2C_chip()
        activate_sync()
        self.colprint("Trying to Align...")
        align_out()
        align_MPA()
        self.ground = measure_gnd()
        self.colprint("GROUND IS " + str(self.ground))
        self.CV = calibrate_chip(self.ground, filename = self.DIR+"/Bias_DAC")
        set_nominal()
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
        self.DP1 = self.GetDigiPower()
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

        SetSlaveMap()
        if which == "PST":
            self.colprint("Turning on PST")
            Vlimit = 1.32
            if (VDDPST > Vlimit):
                VDDPST = Vlimit
            diffvoltage = 1.5 - VDDPST
            setvoltage = int(round(diffvoltage / Vc))
            if (setvoltage > 4095):
                setvoltage = 4095
            setvoltage = setvoltage << 4
            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
            Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x34, setvoltage)  # tx to DAC C
            sleep(2)

            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0)  #read VR on shunt
            VAL = (Vcshunt * ret)/Rshunt
            self.PVALS[0] = VAL
            if VAL > 30: return 0
        if which == "DIG":
            Vlimit = 1.32
            if (DVDD > Vlimit):
                DVDD = Vlimit
            diffvoltage = 1.5 - DVDD
            setvoltage = int(round(diffvoltage / Vc))
            if (setvoltage > 4095):
                setvoltage = 4095
            setvoltage = setvoltage << 4
            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
            Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x30, setvoltage)  # tx to DAC C
            sleep(2)

            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
            VAL = (Vcshunt * ret)/Rshunt
            self.PVALS[1] = VAL
            if VAL > 200:
                return 0
        if which == "ANA":
            Vlimit = 1.32
            if (AVDD > Vlimit):
                AVDD = Vlimit
            diffvoltage = 1.5 - AVDD
            setvoltage = int(round(diffvoltage / Vc))
            if (setvoltage > 4095):
                setvoltage = 4095
            setvoltage = setvoltage << 4
            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
            Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x32, setvoltage)  # tx to DAC C
            sleep(2)

            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
            sleep(1)
            ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0)  # read V on shunt
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
            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x01)  # to SCO on PCA9646
            Send_MPA_SSA_I2C_Command(dac7678, 0, write, 0x36, setvoltage)  # tx to DAC C
            sleep(2)
            val2 = (mpaid << 5) + 16 # reset bit for MPA
            Configure_MPA_SSA_I2C_Master(1, SLOW)
            Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x02)  # route to 2nd PCF8574
            Send_MPA_SSA_I2C_Command(pcf8574, 0, write, 0, val2)  # set reset bit
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
        SetSlaveMap()
        # readDVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
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
        SetSlaveMap()
        # readVDDPST
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_10, 0, read, 0x01, 0)  #read VR on shunt
        VPST = (Vcshunt * ret)/Rshunt
        message = "VDDPST current: " + str(VPST) + " mA"
        self.colprint(message)
        # readDVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
        VDIG = (Vcshunt * ret)/Rshunt
        message = "DVDD current: " + str(VDIG) + " mA"
        self.colprint(message)
        # readAVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0)  # read V on shunt
        VANA = (Vcshunt * ret)/Rshunt
        message = "AVDD current: " + str(VANA) + " mA"
        self.colprint(message)
        if (VPST < 10 or VDIG < 15 or VANA < 30) and enabled:
            return 0
        return 1

if __name__ == '__main__': # TEST
	TEST = ProbeMeasurement(sys.argv[1])
