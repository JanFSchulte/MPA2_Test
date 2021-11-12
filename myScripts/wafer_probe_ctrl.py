import csv
import numpy
import sys
import os
import random
from numpy.core.overrides import verify_matching_signatures
import pandas as pd
import numpy as np
import time
from mpa_methods.mpa_main_test import *
from ssa_methods.main_ssa_test_2 import *

'''
It runs the automatic wafer probing procedure

Example:
AP = AUTOPROBER(
    wafer='WaferName',
    name='TestName' ,
    chip=['SSA'|'SSA'],
    exclude=[])
AP.MSR_ALL()
'''

try:
    import Gpib
except:
    print("->  Impossible to access Wafer Prober Machine via GPIB. Missing gpib.")


class tmperrgpib:
    def write(self):
        pass

class AUTOPROBER():

    def __init__(self, wafer, chip='MPA', mpa=False, dryRun = False, exclude = [], efuse = False):
        self.wafer = wafer
        try:
            self.ProbeStation = Gpib.Gpib(1, 22)
        except:
            print("- Impossible to access WAFER PROBER via GPIB")
            self.ProbeStation = tmperrgpib()
        time.sleep(0.1)
        self.ProbeStation.write("*RST")
        time.sleep(0.1)
        #self.ConnToPS()
        self.mpa = mpa
        self.dryRun = dryRun
        self.chip = chip
        self.DieNumber = 0
        self.exclude = exclude
        self.efuse = efuse
        try:
            os.mkdir(f"../MPA2_AutoProbe_results/Wafer_{self.wafer}")
        except:
            print("Output Folder already exist")

    def colprint(self, text):
        sys.stdout.write("\033[1;34m")
        print(str(text))
        sys.stdout.write("\033[0;0m")

    def read(self, len):
        return self.ProbeStation.read(len).decode("utf-8")

    def write(self, str):
        self.ProbeStation.write(str)

    def ConnToPS(self):
        print("\n\n===== PROBE STATION INITIALIZED: =====")
        self.ProbeStation.write("*IDN?")
        print(self.read(100))
        time.sleep(0.25)
        self.ProbeStation.write("StepFirstDie") # Start from 1
        #self.ProbeStation.write("StepNextDie -1 6") # Starts from specific (Numbering is automatic)
        print(f"Stepped to first die: {self.read(100)}")
        time.sleep(0.25)
        self.ProbeStation.write("ReadChuckPosition")
        print(f"Initial Chuck Position: {self.read(100)}")
        time.sleep(0.25)

    def MSR_ALL(self, N='default'):
        if(N=='default'):
            if(self.chip=='SSA'): nchips = 90
            elif(self.chip=='MPA'): nchips = 187
        else: nchips = N
        self.DieNumber = 0
        self.DieR = 0
        self.DieC = 0
        self.KeepOnStepping = True
        self.BadChips = []
        # first pass at all chips
        while self.KeepOnStepping:
            ChipStatus = self.NEXT(nchips)
            print(ChipStatus)
            if ChipStatus == 0:
                badR = self.DieR
                badC = self.DieC
                self.BadChips.append([badR, badC]) # bad chips will be scanned again
        print(self.BadChips)
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        # set overtravel a little higher for second pass
        #self.ProbeStation.write("SetChuckHeight O V Y 0")
        #print("Increasing overtravel: " + self.read(100))
        #time.sleep(0.25)
        ## go over bad chips
        ##for C in self.BadChips:
        ##    ChipStatus = self.PROBESPECIFIC(C[0],C[1])
        ##    print(ChipStatus)
        #self.ProbeStation.write("SetChuckHeight O V Y 0")
        #print("Resetting overtravel: " + self.read(100))
        #time.sleep(0.25)

    def NEWCHIPMSR(self, inf):
        if (self.chip == 'MPA'):
            if self.efuse:  # Efuse Block#
                print(f"### Efuse write procedure: {inf}")
                df = pd.read_csv('yield3.csv', sep=',')
                row=df[df['chip'] == int(self.DieNumber)]
                print(row)
                vref = row['VREF_DAC'].values[0]
                yd = row['yield'].values[0]
                status = 0
                if yd == 0:
                    status = 0b01
                elif yd == 1:
                    status = 0b10
                adc_ref = vref
                if vref == -1000:
                    adc_ref = 0
                self.mpa.pwr.set_supply(mode='on', display=False, d=1.0, a=1.2, p=1.2)
                self.mpa.init()
                #### Change according to wafer number !!!!!
                mpa.chip.ctrl_base.fuse_write(lot=1, wafer_n=3, pos=int(self.DieNumber), process=0, adc_ref = int(adc_ref), status = status, pulse=1 , confirm=1)
                self.mpa.pwr.set_supply(mode='off', display=False)
                return True

            else: # Standard functionality test block
                PCM = MainTestsMPA(directory = f"../MPA2_AutoProbe_results/Wafer_{self.wafer}/", tag = self.DieNumber, chip = self.mpa)
                if self.efuse:
                    PCM.runtest.set_enable('efuse', 'ON')
                    PCM.wafer = 2
                    PCM.lot = 1 
                else:
                    PCM.runtest.set_enable('efuse', 'OFF')
                #PCM= MPAProbeTest("../MPA2_Results/Lot1_Wafer6/", self.chip, self.i2c, FC7, self.cal, self.test, self.bias)
                return PCM.RUN(runname = inf, write_header=False)

        #elif(self.chip == 'SSA'):
            # WIP
            #PCM = SSA_Measurements(
            #tag = (self.name+"_"+str(self.DieNumber)),
            #runtest = 'default',
            #directory = '../SSA_Results/Wafer_' + str(self.wafer)
            #return PCM.RUN(inf)

    def NEXT(self, N):
        self.ProbeStation.write("GetDieDataAsNum")
        DieData = self.read(100)
        time.sleep(0.25)
        Dparse = DieData.split()
        self.DieNumber = Dparse[1]
        self.DieR = Dparse[2]
        self.DieC = Dparse[3]
        print(f"ON DIE # {self.DieNumber}")
        if( int(self.DieNumber) in self.exclude):
            print(f"DIE EXCLUDED # {self.DieNumber} Moving to next")
            GoodNess = True
        else:
            #self.ProbeStation.write("MoveChuck 0 -40 R Y") #Change position of probing respect first Run
            #self.read(100)
            if(not self.dryRun):
                self.ProbeStation.write("MoveChuckContact")
                print(f"going into contact: {self.read(100)}")
            time.sleep(0.5)
            self.ProbeStation.write("ReadChuckPosition")
            inf = f"Chip # {self.DieNumber} Col {self.DieC} Row {self.DieR} POS = {self.read(100)}"
            if(not self.dryRun):
                GoodNess = self.NEWCHIPMSR(inf)
                self.ProbeStation.write("MoveChuckSeparation")
                print(f"coming out of contact: {self.read(100)}")
                time.sleep(0.25)
                if(not GoodNess):
                    print("Test failed, trying again: ")
                    self.ProbeStation.write("MoveChuckContact")
                    print(f"going into contact: {self.read(100)}")
                    GoodNess = self.NEWCHIPMSR(inf)
                    self.ProbeStation.write("MoveChuckSeparation")
                    print(f"coming out of contact: {self.read(100)}")
                    time.sleep(0.25)
            else:
                time.sleep(1)
                GoodNess = False
        if not int(self.DieNumber) == N:
            self.ProbeStation.write("StepNextDie")
            self.read(100)
            time.sleep(0.25)
        else:
            self.KeepOnStepping = False
        return GoodNess

    def PROBESPECIFIC(self,R,C):
        self.ProbeStation.write(f"StepNextDie {R} {C}")
        self.read(100)
        time.sleep(0.25)
        self.ProbeStation.write("GetDieDataAsNum")
        DieData = self.read(100)
        time.sleep(0.25)
        Dparse = DieData.split()
        self.DieNumber = Dparse[1]
        self.DieR = Dparse[2]
        self.DieC = Dparse[3]
        print(f"ON DIE # {self.DieNumber}")
        self.ProbeStation.write("MoveChuckContact")
        print(f"going into contact: {self.read(100)}")
        time.sleep(0.5)
        self.ProbeStation.write("ReadChuckPosition")
        inf = f"Chip # {self.DieNumber} Col {self.DieC} Row {self.DieR} POS = {self.read(100)}"
        time.sleep(0.25)
        GoodNess = self.NEWCHIPMSR(inf)
        self.ProbeStation.write("MoveChuckSeparation")
        print(f"coming out of contact: {self.read(100)}")
        return GoodNess

#if __name__ == '__main__': # TEST
#    AutoProbe = AUTOPROBER("ChipN")
#    AutoProbe.MSR_ALL(N=88)
