#
import csv
import numpy
from d19cScripts import *
from myScripts import *
import time
ipaddr, fc7AddrTable, fc7 = SelectBoard('MPA')
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.fast_readout_utility import *
from mpa_methods.bias_calibration import *
from mpa_methods.power_utility import *

def colprint(text):
	sys.stdout.write("\033[1;31m")
	print(str(text))
	sys.stdout.write("\033[0;0m")

class ProbeMeasurement:
    def __init__(self, tag):
        self.start = time.time()
        self.tag = tag # UNIQUE ID
        colprint("Creating new chip measurement: "+self.tag)
        self.DIR = "ProbeStationResults/"+self.tag
        if not os.path.exists(self.DIR):	os.makedirs(self.DIR)
        try:
            PowerStatus = self.PowerOnCheck()
            MPAEnableCheck = self.MPAEnable()
            colprint(PowerStatus)

            self.AlignTests()
            if self.Shift():
                colprint("Shift Test Passed!")
            else:
                colprint("Shift Test Failed!")
            #self.PixTests(2)
            #self.Curves()
            #colprint("DONE!")
            sleep(4)
        except: colprint("WE MESSED UP!!!")
        power_off()
    def Curves(self):
        trimDAC_amplitude(20)
        data_array = trimming_chip_noise(nominal_DAC = 77, nstep = 16, plot = 1, start = 0, stop = 150, ratio = 3.92, print_file =1, filename = self.DIR+"/test1")
        data_array = trimming_chip_cal(nominal_DAC = 110, cal = 15, nstep = 4, plot = 1, data_array = data_array, ratio = 3.92, print_file =1, filename = self.DIR+"/test2")
        s_curve_rbr_fr(n_pulse = 1000, cal = 10, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 50, plot = 1, print_file =1, filename = self.DIR+"/test3")
        s_curve_rbr_fr(n_pulse = 1000, cal = 20, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 50, plot = 1, print_file =1, filename = self.DIR+"/test4")
        s_curve_rbr_fr(n_pulse = 1000, cal = 30, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 50, plot = 1, print_file =1, filename = self.DIR+"/test5")
    def PixTests(self, N):
        digipix = []
        anapix = []
        for i in range(N):
            digipix.append(digital_pixel_test(print_log=0))
            anapix.append(analog_pixel_test(print_log=0))
        BadPixD = self.GetActualBadPixels(digipix)
        colprint(str(BadPixD) + " << Bad Pixels (Digi)")
        BadPixA = self.GetActualBadPixels(anapix)
        colprint(str(BadPixA) + " << Bad Pixels (Ana)")
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
        activate_I2C_chip()
        I2C.peri_write("LFSR_data", 0b10101010)
        Check1 = I2C.peri_read("LFSR_data")
        colprint(bin(Check1))
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
        colprint("Trying to Align...")
        align_out()
        align_MPA()
        self.ground = measure_gnd()
        colprint("GROUND IS " + str(self.ground))
        self.CV = calibrate_chip(self.ground)
        with open(self.DIR+'/CAL_VDACs.csv', 'wb') as csvfile:
            CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in self.CV: CVwriter.writerow(i)
    def PowerOnCheck(self):
        self.DeltaDIG = 0.
        self.PVALS = ["0","0","0"]
        colprint("Checking Power-On...")
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
        if self.CheckTotalPower():
            return PowerMessage
        else: return "Power too low!"
    def MPAEnable(self):
        if self.Power("MPA"): colprint("MPA ENABLED!!")
        else: colprint("MPA NOT ENABLED :( ")
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
            colprint("Turning on PST")
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
            if not self.CheckTotalPower():
                return 0
        return 1
    def CheckTotalPower(self):
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
        colprint(message)
        # readDVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_9, 0, read, 0x01, 0)  # read V on shunt
        VDIG = (Vcshunt * ret)/Rshunt
        message = "DVDD current: " + str(VDIG) + " mA"
        colprint(message)
        # readAVDD
        Configure_MPA_SSA_I2C_Master(1, SLOW)
        Send_MPA_SSA_I2C_Command(i2cmux, 0, write, 0, 0x08)  # to SC3 on PCA9646
        sleep(1)
        ret=Send_MPA_SSA_I2C_Command(ina226_8, 0, read, 0x01, 0)  # read V on shunt
        VANA = (Vcshunt * ret)/Rshunt
        message = "AVDD current: " + str(VANA) + " mA"
        colprint(message)
        if VPST < 10 or VDIG < 15 or VANA < 30:
            return 0
        return 1




if __name__ == '__main__': # TEST
	TEST = ProbeMeasurement("TEST_at_DSF")
