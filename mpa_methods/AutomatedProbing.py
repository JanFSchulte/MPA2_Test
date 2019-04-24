import Gpib
import csv
import numpy
import sys
import os
import random
import time
import ProbeCardTest


class ChipMeasurement:
    def __init__(self, tag):
        self.start = time.time()
        self.tag = tag # UNIQUE ID
        #self.DIR = "../AutoProbeResults/"+self.tag # Commented by DC to run test in different folder
        self.DIR = "../../cernbox/AutoProbeResults/Wafer_N6T903-05C7/"+self.tag
        exists = False
        version = 0
        while not exists:
            if not os.path.exists(self.DIR+"_v"+str(version)):
                print self.DIR
                self.DIR = self.DIR+"_v"+str(version)
                os.makedirs(self.DIR)
                exists = True
            version += 1
        print self.DIR + "<<< USING THIS"
        self.TEST = ProbeCardTest2.ProbeMeasurement(self.DIR)
    def RUN(self, chipinfo):
        return self.TEST.Run(chipinfo)

class AUTOPROBER:
    def __init__(self, name):
        self.name = name
        self.ProbeStation = Gpib.Gpib(1, 22)
        time.sleep(0.1)
        self.ProbeStation.write("*RST")
        time.sleep(0.1)
        self.ConnToPS()
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
        for C in self.BadChips:
            ChipStatus = self.PROBESPECIFIC(C[0],C[1])
            print ChipStatus
        self.ProbeStation.write("SetChuckHeight O V Y 0")
        self.colprint("Resetting overtravel: " + self.ProbeStation.read(100))
        time.sleep(0.25)
    def NEWCHIPMSR(self, inf):
        PCM = ChipMeasurement(self.name + "_" + self.DieNumber)
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
        #self.ProbeStation.write("MoveChuck 0 -40 R Y") #Change position of probing respect first Run
        #self.ProbeStation.read(100)
        self.ProbeStation.write("MoveChuckContact")
        self.colprint("going into contact: " + self.ProbeStation.read(100))
        time.sleep(0.5)
        self.ProbeStation.write("ReadChuckPosition")
        inf = "Chip #"+self.DieNumber + " Col " + self.DieC + ", Row " + self.DieR + " POS = " + self.ProbeStation.read(100)
        GoodNess = self.NEWCHIPMSR(inf)
        self.ProbeStation.write("MoveChuckSeparation")
        self.colprint("coming out of contact: " + self.ProbeStation.read(100))
        time.sleep(0.25)
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

if __name__ == '__main__': # TEST
    AutoProbe = AUTOPROBER("ChipN")
    AutoProbe.MSR_ALL(N=88)
