import Gpib
import csv
import numpy
import sys
import os
import random
import time
import traceback
import datetime
#import mpa_methods.RadiationTest as RT
#import mpa_methods.mpa_fast_injection_test as FIT
from mpa_methods.mpa_testing_routine import MainTestsMPA

from myScripts.Utilities import Utilities

"""
from mpa_methods.AutomatedIrradiation import TID_control
TID = TID_control(1,mpa)
TID.MSR_ALL()
"""

#execfile('mpa_methods/AutomatedIrradiation.py')

#class ChipMeasurement:
#    def __init__(self, tag):
#        self.start = time.time()
#        self.tag = tag # UNIQUE ID
#        #self.DIR = "../../cernbox/RadiationResults/Chip_17/"+self.tag  # Insert Chip Number
#        self.DIR = "../TestFolder/" + self.tag
#        exists = False
#        version = 0
#        while not exists:
#            if not os.path.exists(self.DIR+"_v"+str(version)):
#                print self.DIR
#                self.DIR = self.DIR+"_v"+str(version)
#                os.makedirs(self.DIR)
#                exists = True
#            version += 1
#        print self.DIR + "<<< USING THIS"
#        self.TEST = RT.TIDMeasurement(self.DIR)
#    def RUN(self, chipinfo):
#        return self.TEST.Run(chipinfo)

class TID_control:
    def __init__(self, name, chip):
        self.name = name
        self.TID = str(0)
        self.interval = 1200 # in seconds
        info = "TID "+ self.TID + " MRad"
        self.chip = chip # pass mpa object
        self.log = Utilities()
        #self.NEWCHIPMSR(info)
        
    def colprint(self, text):
        sys.stdout.write("\033[1;34m")
        print((str(text)))
        sys.stdout.write("\033[0;0m")

    def MSR_ALL(self, TargetTID = 200, DoseRate = 1.34, TID_start = 0): # TID in MRAD and DoseRate in MRad/Hour
        self.TID = str(0)
        self.KeepOnStepping = True
        self.BadMeasurements = []
        self.chip.pwr.on()
        self.chip.init(reset_board =1, reset_chip =1)
        input("Press Enter when irradiation starts...")
        self.InitialTime = int(time.time())
        test_time = self.InitialTime
        first = 0
        self.log.set_log_files("../MPA2_TID_Testing/OperationLog.txt","../MPA2_TID_Testing/ErrorLog.txt")
        while self.KeepOnStepping:
            ## OLD
            #self.DIR = "../TestFolder/" + self.name + "_" + self.TID + "_FI"
            #os.makedirs(self.DIR)
            #FIM = FIT.MPAFastInjectionMeasurement(self.DIR)
            #FIM.RunRandomTest8p8s(n = 60, timer_data_taking = 60, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test")
            #self.TID = str(round((((int(time.time())- self.InitialTime) / 3600.0)* DoseRate),2))
            #ChipStatus = self.NEXT(TargetTID)
            #print(ChipStatus)
            #if ChipStatus == 0:
            #    self.BadMeasurements.append(self.TID) # bad points

            # Keep Logic busy, configure pixel, trigger, cal_pulse
            if (first):
                rnd_ret = self.chip.test.rnd_test(n_tests=500)
                self.log.print_info(f"RND_tests at {round((int(time.time())- self.InitialTime)/60,2)} min.: {rnd_ret}")
            # Run standard test procedure
            time_now=time.time()
            if (first == 0) | ((time_now - test_time)> self.interval): # 30 min passed?
                # reset fc7?
                first = 1
                self.chip.init(reset_board =1, reset_chip =1)
                self.TID = str(round((((int(time.time())- self.InitialTime) / 3600.0)* DoseRate),2))
                try:
                    ChipStatus = 0
                    ChipStatus = self.NEXT(TargetTID)
                    self.log.print_info(f"-> Measurement: {bool(ChipStatus)}")
                except:
                    self.log.print_error()
                    self.print_exception(f"-> Measurement error at {datetime.datetime.now()}")

                if ChipStatus == 0:
                    self.BadMeasurements.append(self.TID) # bad points
                test_time = time_now
                self.chip.pwr.on()
                self.chip.init(reset_board =1, reset_chip =1)
        self.log.print_error(f"-> Bad Measurements: {self.BadMeasurements}")
        self.log.print_info("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

    def NEWCHIPMSR(self, info):
        #PCM = ChipMeasurement(self.name + "_" + self.TID)
        #    def __init__(self, tag):
        self.start = time.time()
        self.tag = f"{self.name}_{self.TID}" # UNIQUE ID
        #self.DIR = "../../cernbox/RadiationResults/Chip_17/"+self.tag  # Insert Chip Number
        self.DIR = "../MPA2_TID_Testing/"
        #exists = False
        #version = 0
        #while not exists:
        #    if not os.path.exists(self.DIR+"_v"+str(version)):
        #        print(self.DIR)
        #        self.DIR = self.DIR+"_v"+str(version)
        #        os.makedirs(self.DIR)
        #        exists = True
        #    version += 1
        #self.log.print_info(self.DIR + "<<< USING THIS")
        self.log.print_info(f"-> New Measurement {info}")
        self.TEST = MainTestsMPA(tag=self.tag, directory=self.DIR, chip=self.chip)
        return self.RUN(info)

    def RUN(self, chipinfo):
        return self.TEST.RUN(runname=chipinfo)

    def NEXT(self, TargetTID):
        self.log.print_info("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        self.log.print_info(f"-> DOSE at {round((int(time.time())- self.InitialTime)/60,2)} min.: {self.TID}")
        info = "TID "+self.TID + "MRad"
        GoodNess = self.NEWCHIPMSR(info)
        if int(float(self.TID)) >= TargetTID:
            self.KeepOnStepping = False
        return GoodNess

    def print_exception(self, text='Exception'):
        self.log.print_warning(text)
        self.exc_info = sys.exc_info()
        self.log.print_warning("======================")
        exeptinfo = traceback.format_exception(*self.exc_info )
        for extx in exeptinfo:
            self.log.print_warning(extx)
        self.log.print_warning("======================")



if __name__ == '__main__': # TEST
    TID_control = TID_control("ChipN")
    TID_control.MSR_ALL(TargetTID = 10, DoseRate = 1)
