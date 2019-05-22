import Gpib
import csv
import numpy
import sys
import os
import random
import time
# from mpa_methods import ProbeCardTest
from ssa_methods.ssa_test_waferprobing import *


class AUTOPROBER:

    def __init__(self, wafer, name, chip='MPA', dryRun = False, exclude = [1,2,3,4,5]):
        self.name = name
        self.wafer = wafer
        self.ProbeStation = Gpib.Gpib(1, 22)
        time.sleep(0.1)
        self.ProbeStation.write("*RST")
        time.sleep(0.1)
        self.ConnToPS()
        self.dryRun = dryRun
        self.chip = chip
        self.DieNumber = 0
        self.exclude = exclude

    def colprint(self, text):
        sys.stdout.write("\033[1;34m")
    	print(str(text))
    	sys.stdout.write("\033[0;0m")

    def ConnToPS(self):
        self.colprint("\n\n===== PROBE STATION INITIALIZED: =====")
        self.ProbeStation.write("*IDN?")
        self.colprint(self.ProbeStation.read(100))
        time.sleep(0.25)
        self.ProbeStation.write("StepFirstDie") # Start from 1
        #self.ProbeStation.write("StepNextDie 5 7") # Starts from specific (Numbering is automatic)
        self.colprint("Stepped to first die: " + self.ProbeStation.read(100))
        time.sleep(0.25)
        self.ProbeStation.write("ReadChuckPosition")
        self.colprint("Initial Chuck Position: " + self.ProbeStation.read(100))
        time.sleep(0.25)

    def MSR_ALL(self, N=88):
        self.DieNumber = 0
        self.DieR = 0
        self.DieC = 0
        self.KeepOnStepping = True
        self.BadChips = []
        # first pass at all chips
        while self.KeepOnStepping:
            ChipStatus = self.NEXT(N)
            print ChipStatus
            if ChipStatus == 0:
                badR = self.DieR
                badC = self.DieC
                self.BadChips.append([badR, badC]) # bad chips will be scanned again
        print self.BadChips
        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        # set overtravel a little higher for second pass
        self.ProbeStation.write("SetChuckHeight O V Y 0")
        self.colprint("Increasing overtravel: " + self.ProbeStation.read(100))
        time.sleep(0.25)
        # go over bad chips
        #for C in self.BadChips:
        #    ChipStatus = self.PROBESPECIFIC(C[0],C[1])
        #    print ChipStatus
        self.ProbeStation.write("SetChuckHeight O V Y 0")
        self.colprint("Resetting overtravel: " + self.ProbeStation.read(100))
        time.sleep(0.25)

    def NEWCHIPMSR(self, inf):
        if  (self.chip == 'MPA'):
            PCM = ChipMeasurement(  self.name + "_" + self.DieNumber)
        elif(self.chip == 'SSA'):
            PCM = SSA_Measurements(
                tag = (self.name+"_"+str(self.DieNumber)),
                runtest = 'default',
                directory = '../SSA_Results/Wafer_' + str(self.wafer) )
        return PCM.RUN(inf)

    def NEXT(self, N):
        self.ProbeStation.write("GetDieDataAsNum")
        DieData = self.ProbeStation.read(100)
        time.sleep(0.25)
        Dparse = DieData.split()
        self.DieNumber = Dparse[1]
        self.DieR = Dparse[2]
        self.DieC = Dparse[3]
        self.colprint("ON DIE #" + self.DieNumber)
        if( int(self.DieNumber) in self.exclude):
            self.colprint("DIE EXCLUDED #" + self.DieNumber + " Moving to next")
            GoodNess = True
        else:
            #self.ProbeStation.write("MoveChuck 0 -40 R Y") #Change position of probing respect first Run
            #self.ProbeStation.read(100)
            if(not self.dryRun):
                self.ProbeStation.write("MoveChuckContact")
                self.colprint("going into contact: " + self.ProbeStation.read(100))
            time.sleep(0.5)
            self.ProbeStation.write("ReadChuckPosition")
            inf = "Chip #"+self.DieNumber + " Col " + self.DieC + ", Row " + self.DieR + " POS = " + self.ProbeStation.read(100)
            if(not self.dryRun):
                GoodNess = self.NEWCHIPMSR(inf)
                self.ProbeStation.write("MoveChuckSeparation")
                self.colprint("coming out of contact: " + self.ProbeStation.read(100))
                time.sleep(0.25)
                if(not GoodNess):
                    self.colprint("Test failed, trying again: ")
                    self.ProbeStation.write("MoveChuckContact")
                    self.colprint("going into contact: " + self.ProbeStation.read(100))
                    GoodNess = self.NEWCHIPMSR(inf)
                    self.ProbeStation.write("MoveChuckSeparation")
                    self.colprint("coming out of contact: " + self.ProbeStation.read(100))
                    time.sleep(0.25)
            else:
                time.sleep(1)
                GoodNess = False
        if not int(self.DieNumber) == N:
            self.ProbeStation.write("StepNextDie")
            self.ProbeStation.read(100)
            time.sleep(0.25)
        else:
            self.KeepOnStepping = False
        return GoodNess

    def PROBESPECIFIC(self,R,C):
        self.ProbeStation.write("StepNextDie "+ R + " " + C)
        self.ProbeStation.read(100)
        time.sleep(0.25)
        self.ProbeStation.write("GetDieDataAsNum")
        DieData = self.ProbeStation.read(100)
        time.sleep(0.25)
        Dparse = DieData.split()
        self.DieNumber = Dparse[1]
        self.DieR = Dparse[2]
        self.DieC = Dparse[3]
        self.colprint("ON DIE #" + self.DieNumber)
        self.ProbeStation.write("MoveChuckContact")
        self.colprint("going into contact: " + self.ProbeStation.read(100))
        time.sleep(0.5)
        self.ProbeStation.write("ReadChuckPosition")
        inf = "Chip #"+self.DieNumber + " Col " + self.DieC + ", Row " + self.DieR + " POS = " + self.ProbeStation.read(100)
        time.sleep(0.25)
        GoodNess = self.NEWCHIPMSR(inf)
        self.ProbeStation.write("MoveChuckSeparation")
        self.colprint("coming out of contact: " + self.ProbeStation.read(100))
        return GoodNess

#if __name__ == '__main__': # TEST
#    AutoProbe = AUTOPROBER("ChipN")
#    AutoProbe.MSR_ALL(N=88)
