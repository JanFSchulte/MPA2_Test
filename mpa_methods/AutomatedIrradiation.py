import Gpib
import csv
import numpy
import sys
import os
import random
import time
import mpa_methods.RadiationTest as RT
import mpa_methods.FastInjectionTest as FIT
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
    def __init__(self, name):
        self.name = name
        self.TID = str(0)
        info = "TID "+ self.TID + " MRad"
        self.NEWCHIPMSR(info)
    def colprint(self, text):
        sys.stdout.write("\033[1;34m")
    	print((str(text)))
    	sys.stdout.write("\033[0;0m")

    def MSR_ALL(self, TargetTID = 500, DoseRate = 1.0): # TID in MRAD and DoseRate in MRad/Hour
        self.TID = str(0)
        self.KeepOnStepping = True
        self.BadMeasurements = []
        input("Press Enter when irradiation starts...")
        self.InitialTime = int(time.time())
        while self.KeepOnStepping:
            self.DIR = "../TestFolder/" + self.name + "_" + self.TID + "_FI"
            os.makedirs(self.DIR)
            FIM = FIT.FastInjectionMeasurement(self.DIR)
            FIM.RunRandomTest8p8s(n = 60, timer_data_taking = 60, cal_pulse_period = 1, l1a_period = 39, latency = 500, runname = "Test")
            self.TID = str(round((((int(time.time())- self.InitialTime) / 3600.0)* DoseRate),2))
            ChipStatus = self.NEXT(TargetTID)
            print(ChipStatus)
            if ChipStatus == 0:
                self.BadMeasurements.append(self.TID) # bad points
        print(self.BadMeasurements)
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

    def NEWCHIPMSR(self, info):
        #PCM = ChipMeasurement(self.name + "_" + self.TID)
        #    def __init__(self, tag):
        self.start = time.time()
        self.tag = self.name + "_" + self.TID # UNIQUE ID
        #self.DIR = "../../cernbox/RadiationResults/Chip_17/"+self.tag  # Insert Chip Number
        self.DIR = "../TestFolder/" + self.tag
        exists = False
        version = 0
        while not exists:
            if not os.path.exists(self.DIR+"_v"+str(version)):
                print(self.DIR)
                self.DIR = self.DIR+"_v"+str(version)
                os.makedirs(self.DIR)
                exists = True
            version += 1
        print(self.DIR + "<<< USING THIS")
        self.TEST = RT.TIDMeasurement(self.DIR)
        return self.RUN(info)

    def RUN(self, chipinfo):
        return self.TEST.Run(chipinfo)

    def NEXT(self, TargetTID):
        self.colprint("DOSE:" + self.TID)
        info = "TID "+self.TID + "MRad"
        GoodNess = self.NEWCHIPMSR(info)
        if int(float(self.TID)) >= TargetTID:
            self.KeepOnStepping = False
        return GoodNess

if __name__ == '__main__': # TEST
    TID_control = TID_control("ChipN")
    TID_control.MSR_ALL(TargetTID = 10, DoseRate = 1)
