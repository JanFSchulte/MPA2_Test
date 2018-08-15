import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from myScripts.ArrayToCSV import *
from mpa_methods.cal_utility import *

def MemTestParse(wafer = "Wafer_N6T903-05C7_Digital", chips = range(1,89)):
    rx_dict = {
        '1': re.compile(r'Starting Test:\nTest Completed:\n')
    }
    mem_log = np.array([['Chip #', '1.2V', '1.0V']])
    for c in chips:
        try:
            with open('../cernbox/AutoProbeResults/' + str(wafer) + '/ChipN_' + str(c) + '_v0/LogMemTest_12') as file:
                data12 = file.read()
            with open('../cernbox/AutoProbeResults/' + str(wafer) + '/ChipN_' + str(c) + '_v0/LogMemTest_10') as file:
                data10 = file.read()
            for key, rx in rx_dict.items():
                match = rx.search(data12)
                if match:
                    match12 = key
                else:
                    match12 = 0
                match = rx.search(data10)
                if match:
                    match10 = key
                else:
                    match10 = 0
            mem_log = np.append(mem_log, [[c, match12, match10]], axis = 0)

        except IOError:
            mem_log = np.append(mem_log, [[c, "Err", "Err"]], axis = 0)

    CSV.ArrayToCSV(mem_log, "../cernbox/AutoProbeResults/" + str(wafer) + "MemoryTestParse_"+str(wafer)+".csv")
    return mem_log


def BandGapParse(max_dose = 100, filename = "/home/testMPA/cernbox/Irrad1_fix/"):
    i = 0
    bg = np.array(0)
    dose = np.array(0)
    while i <= max_dose:
        try:
            with open(filename + "Run_" + str(i) + "MRad/BandGap.txt") as file:
                x = file.read()
                for token in x.split():
                    bg = np.append(bg, token)
                dose = np.append(dose, i)
                i += 1
        except IOError:
            i += 1
    bg = bg.astype('float')
    plt.plot(dose[1:], bg[1:], 'yo')
    plt.title("BandGap vs. Dose")
    plt.xlabel("Dose (MRad)")
    plt.ylabel("BandGap")
    plt.show()


def PowerParse(max_dose = 100, filename = "/home/testMPA/cernbox/Irrad1_fix/"):
    i = 0
    power = np.array(0)
    dose = np.array(0)
    while i <= max_dose:
        try:
            with open(filename + "Run_" + str(i) + "MRad/PowerMeasurement.csv") as file:
                x = file.read()
                for token in x.split():
                    power = np.append(power, token)
                dose = np.append(dose, i)
                i +=1
        except IOError:
            i += 1
    power = power.astype('float')
    power = np.delete(power, 0, 0)
    dose = np.delete(dose, 0, 0)
    # Plot DP1
    plt.plot(dose, power[0::9], 'ro', label = "DP1")
    #Plot DP2
    plt.plot(dose, power[1::9], 'yo', label = "DP2")
    #Plot DP3
    plt.plot(dose, power[2::9], 'go', label = "DP3")
    #Plot AN1
    plt.plot(dose, power[3::9], 'b^', label = "AN1")
    #Plot AN2
    plt.plot(dose, power[4::9], 'm^', label = "AN2")
    #Plot AN3
    plt.plot(dose, power[5::9], 'k^', label = "AN3")
    #Plot PST1
    plt.plot(dose, power[6::9], 'cs', label = "PST1")
    #Plot PST2
    plt.plot(dose, power[7::9], 'rs', label = "PST2")
    #Plot PST3
    plt.plot(dose, power[8::9], 'gs', label = "PST3")
    plt.title("Power Measurements")
    plt.xlabel("Dose (MRad)")
    plt.ylabel("Power")
    plt.legend()
    plt.show()
    return power


def ScurveParse(max_dose = 100, filename = "/home/testMPA/cernbox/Irrad1_fix/"):
    i = 0
    th_avg = np.array(0)
    th_spread = np.array(0)
    noise_avg = np.array(0)
    dose = np.array(0)
    sum_avg = np.zeros(shape = (0,51))
    sum_array = np.zeros(51)
    th_array = np.zeros(2160, dtype = np.int)
    noise_array = np.zeros(2160, dtype = np.float)
    while i <= max_dose:
        try:
            data = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/Scurve15_CAL.csv")
            try:
                start_DAC = 0
                for r in range(1,17):
                    for p in range(1,120):
                        par, cov = curve_fit(errorf, range(start_DAC, 50), data[(r-1)*120+p,start_DAC + 1 : 51], p0= [200, 25, 2])
                        th_array[(r-1)*120+p] = int(round(par[1]))
                        noise_array[(r-1)*120+p] = par[2]
            except RuntimeError or TypeError:
                print "Fitting failed on pixel ", p , " row: " ,r
            th_avg = np.append(th_avg, np.mean(th_array))
            noise_avg = np.append(noise_avg, np.mean(noise_array))
            th_spread = np.append(th_spread, np.std(th_array))
            data = np.delete(data, 0, 0)
            data = np.delete(data, 0, 1)
            sum_array = np.sum(data, axis = 0)/1918
            sum_avg = np.append(sum_avg, [sum_array], axis = 0)
            dose = np.append(dose, i)
            i += 1
        except IOError:
            i += 1

    dose = np.delete(dose, 0, 0)
    th_avg = np.delete(th_avg, 0, 0)
    noise_avg = np.delete(noise_avg, 0, 0)
    sum_avg = sum_avg.astype(int)
    plt.figure(1)
    plt.plot(dose, th_avg, 'co')
    plt.title("Average Threshold")
    plt.xlabel("Dose (MRad)")
    plt.ylabel("Threshold")
    plt.figure(2)
    plt.plot(dose, th_spread[1:], 'mo')
    plt.title("Threshold Spread")
    plt.xlabel("Dose (MRad)")
    plt.ylabel("Spread")
    plt.figure(3)
    plt.plot(dose, noise_avg, 'ko')
    plt.title("Average Noise")
    plt.xlabel("Dose (MRad)")
    plt.ylabel("Noise")
    plt.figure(4)
    a = 0
    while a < len(dose):
        plt.plot(range(0,50), sum_avg[a, 0:50], label = "Dose = " + str(dose[a]))
        a += 1
    plt.title("Average Scurve")
    plt.legend()
    plt.show()
    #return sum_avg


def DACParse(max_dose = 100, filename = "/home/testMPA/cernbox/Irrad1_fix/"):
    i = 0
    DAC0 = np.zeros(shape = (0, 33))
    DAC1 = np.zeros(shape = (0, 33))
    DAC2 = np.zeros(shape = (0, 33))
    DAC3 = np.zeros(shape = (0, 33))
    DAC4 = np.zeros(shape = (0, 33))
    DAC5 = np.zeros(shape = (0, 257))
    DAC6 = np.zeros(shape = (0, 257))
    dose = np.array(0)
    while i <= max_dose:
        try:
            dac0 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/DAC0_TP0.csv")
            dac1 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/DAC1_TP1.csv")
            dac2 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/DAC2_TP2.csv")
            dac3 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/DAC3_TP3.csv")
            dac4 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/DAC4_TP4.csv")
            dac5 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/Th_DAC_TP5.csv")
            dac6 = CSV.csv_to_array(filename + "Run_" + str(i) + "MRad/Cal_DAC_TP6.csv")
            DAC0 = np.append(DAC0, dac0, axis = 0)
            DAC1 = np.append(DAC1, dac1, axis = 0)
            DAC2 = np.append(DAC2, dac2, axis = 0)
            DAC3 = np.append(DAC3, dac3, axis = 0)
            DAC4 = np.append(DAC4, dac4, axis = 0)
            DAC5 = np.append(DAC5, dac5, axis = 0)
            DAC6 = np.append(DAC6, dac6, axis = 0)
            dose = np.append(dose, i)
            i += 1
        except IOError:
            i += 1
    dose = np.delete(dose, 0, 0)
    #for a in range(0,len(dose)):
        #b = 0
    a = 0
    for b in range(0,7):
        plt.figure(1)
        plt.plot(range(0,32), DAC0[b, 1:33], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(2)
        plt.plot(range(0,32), DAC1[b, 1:33], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(3)
        plt.plot(range(0,32), DAC2[b, 1:33], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(4)
        plt.plot(range(0,32), DAC3[b, 1:33], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(5)
        plt.plot(range(0,32), DAC4[b, 1:33], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(6)
        plt.plot(range(0,256), DAC5[b, 1:257], 'bo', label = "Dose "+str(dose[a]))
        plt.figure(7)
        plt.plot(range(0,256), DAC6[b, 1:257], 'bo', label = "Dose "+str(dose[a]))
        # Choose Doses after zero
    a = len(dose) - 1
    for b in range(0,7):
        plt.figure(1)
        plt.plot(range(0,32), DAC0[b + 7*a, 1:33], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(2)
        plt.plot(range(0,32), DAC1[b + 7*a, 1:33], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(3)
        plt.plot(range(0,32), DAC2[b + 7*a, 1:33], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(4)
        plt.plot(range(0,32), DAC3[b + 7*a, 1:33], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(5)
        plt.plot(range(0,32), DAC4[b + 7*a, 1:33], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(6)
        plt.plot(range(0,256), DAC5[b + 7*a, 1:257], 'mo', label = "Dose "+str(dose[a]))
        plt.figure(7)
        plt.plot(range(0,256), DAC6[b + 7*a, 1:257], 'mo', label = "Dose "+str(dose[a]))
    #for b in range(1,7):
            #plt.figure(1)
            #plt.plot(range(0,32), DAC0[b + 7*a, 1:33], 'yo')
            #plt.figure(2)
            #plt.plot(range(0,32), DAC1[b + 7*a, 1:33], 'bo')
            #plt.figure(3)
            #plt.plot(range(0,32), DAC2[b + 7*a, 1:33], 'go')
            #plt.figure(4)
            #plt.plot(range(0,32), DAC3[b + 7*a, 1:33], 'mo')
            #plt.figure(5)
            #plt.plot(range(0,32), DAC4[b + 7*a, 1:33], 'co')
            #plt.figure(6)
            #plt.plot(range(0,256), DAC5[b + 7*a, 1:257], 'ko')
            #plt.figure(7)
            #plt.plot(range(0,256), DAC6[b + 7*a, 1:257], 'ro')
    plt.figure(1)
    plt.title("DAC0")
    plt.legend()
    plt.figure(2)
    plt.title("DAC1")
    plt.legend()
    plt.figure(3)
    plt.title("DAC2")
    plt.legend()
    plt.figure(4)
    plt.title("DAC3")
    plt.legend()
    plt.figure(5)
    plt.title("DAC4")
    plt.legend()
    plt.figure(6)
    plt.title("Th_DAC")
    plt.legend()
    plt.figure(7)
    plt.title("Cal_DAC")
    plt.legend()





    plt.show()
