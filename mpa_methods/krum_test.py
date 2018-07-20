import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from mpa_methods.cal_utility import *
from mpa_methods.power_utility import *
from mpa_methods.bias_calibration import *
from myScripts.BasicMultimeter import *


def krummenacher_measure(krum = 1, gain_diff = 1, pre_amp = 1, pa_gain_diff = 1, step = 3):

###############################################################################
# Declare Variables                                                           #
###############################################################################
    k = 0
    n = 0
    block = 0
    krum_th_avg = np.zeros(31, dtype = np.float)
    krum_noise_avg = np.zeros(31, dtype = np.float)
    amp_noise_avg = np.zeros(31, dtype = np.float)
    krum_spread = np.zeros(31, dtype = np.float)
    pa_spread = np.zeros(31, dtype = np.float)
    th_array = np.zeros(2040, dtype = np.int)
    measured_voltage = 0
    noise_array = np.zeros(2040, dtype = np.float)
    krum_current = np.zeros(31, dtype = np.float)
    pa_current = np.zeros(31, dtype = np.float)
    krum_voltage = np.zeros(31, dtype = np.float)
    pa_voltage = np.zeros(31, dtype = np.float)
    x = np.zeros(31, dtype = np.int)
    th_array1 = np.zeros(2040, dtype = np.int)
    th_array2 = np.zeros(2040, dtype = np.int)
    th_array3 = np.zeros(2040, dtype = np.int)
    th_array4 = np.zeros(2040, dtype = np.int)
    thDAC = 0
    calDAC = 0
    thLSB = 0
    calLSB = 0
    gain_array1 = np.zeros(2040, dtype = np.float)
    gain_array2 = np.zeros(2040, dtype = np.float)


# Calibrate and Trim
    mpa_reset()
    gnd = measure_gnd()
    calibrate_chip(gnd)
    trimDAC_amplitude(20)
    trimming_chip(s_type = "CAL", ref_val = 150, nominal_DAC = 45, nstep = 1,      n_pulse = 200, iteration = 1, extract = 1, plot = 0, stop = 100, ratio = 2.36, print_file = 0)
# Reset Krummenacher and Pre Amp DAC values
    print "Resetting DAC"
    while block < 7:
        set_DAC(block, 0, 15)
        set_DAC(block, 1, 15)
        block += 1

# Initialize Multimeter
    multi = multimeter.init_keithley(avg = 5, address = 16)


###############################################################################
# Find Krummenacher Threshold Voltage                                         #
###############################################################################

    if krum == 1:
        print "\nCalculating Krummenacher Threshold Voltages"
        while k < 31 :
            block = 0
            while block < 7 :
                set_DAC(block, 0, k)
                block += 1
            print "Starting s-curve", k
            data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 20, row = range(1, 17), step = 1, start = 0, stop = 250,
            pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
            th_array = [a for a in th_array if a != 0]
            krum_th_avg[n] = np.mean(th_array[1:1920])
            krum_noise_avg[n] = np.mean(noise_array[1:1920])
            krum_spread[n] = np.std(th_array)
            krum_voltage[n] = multimeter.measure(multi) * 1000
            krum_current[n] = measure_current(print_file = 0)
            if k == 15:
                measured_voltage = krum_voltage[n]
            print "S curve ",k, "finished."
            print "Average Threshold: ",krum_th_avg[n]
            #print "Minimum Threshold: ", min(th_array)
            print "Threshold Spread: ", krum_spread[n]
            print "Average Noise: ",krum_noise_avg[n]
            print "Voltage: ", krum_voltage[n], "mV"
            x[n] = k
            k += step
            n += 1

###############################################################################
# Find Gain Difference for Krummenacher                                       #
###############################################################################

    if gain_diff == 1:
        print "\nCalculating Krummenacher Gain Difference"
        block = 0
        while block < 7 :
            set_DAC(block, 0, 6)
            block += 1

        thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 32, plot = 0, print_file = 0)
        calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 32, plot = 0, print_file = 0)
        thLSB = np.mean((thDAC[:,160] - thDAC[:,0])/160)*1000 #LSB Threshold DAC in mV
        calLSB = np.mean((calDAC[:,160] - calDAC[:,0])/160)*0.035/1.768*1000 #LSB Calibration DAC in fC


        print "Finding average threshold when k=6 for ref=15"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 15, row = range(1, 17), step = 1, start = 0, stop = 175,
        pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref15k6 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array1[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref15k6
        print "Threshold Spread: ", np.std(th_array)

        print "\nFinding average threshold when k=6 for ref=30"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 30, row = range(1, 17), step = 1, start = 0, stop = 250,
        pulse_delay = 500, extract_val = 130, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref30k6 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array2[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref30k6
        print "Threshold Spread: ", np.std(th_array)

        block = 0
        while block < 7 :
            set_DAC(block, 0, 24)
            block += 1

        print "\nFinding average when k=24 for ref=15"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 15, row = range(1, 17), step = 1, start = 0, stop = 175,
        pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref15k24 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array3[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref15k24
        print "Threshold Spread: ", np.std(th_array)

        print "\nFinding average when k=24 for ref=30"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 30, row = range(1, 17), step = 1, start = 0, stop = 250,
        pulse_delay = 500, extract_val = 130, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref30k24 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array4[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref30k24
        print "Threshold Spread: ", np.std(th_array)

        Q1 = calLSB * 15
        Q2 = calLSB * 30
        delta_Q = Q2 - Q1

        #gain1 = (ref30k6 - ref15k6) / delta_Q
        #gain2 = (ref30k24 - ref15k24) / delta_Q

        p = 0
        gain3 = 0
        gain4 = 0
        while p < 2040:
            gain_array1[p] = (th_array2[p] - th_array1[p])/delta_Q
            gain_array2[p]= (th_array4[p] - th_array3[p])/delta_Q
            p += 1
        gain3 = (np.mean(gain_array1) * thLSB)
        gain4 = (np.mean(gain_array2) * thLSB)

        #print "\nGain for k=6:", gain1, "[mV/fC]"
        #print "Gain for k=24:", gain2, "[mV/fC]"
        #print "Gain Difference:", gain1 - gain2, "[mV/fC]"
        #print "Other Gain Calculation:"
        print "thLSB:", thLSB
        print "calLSB", calLSB
        print "\nGain for k=6:", gain3, "[mV/fC]"
        print "Gain for k=24:", gain4, "[mV/fC]"
        print "Gain Difference:", gain4 - gain3, "[mV/fC]"


###############################################################################
# Find Power Consumption                                                      #
###############################################################################

    if pre_amp == 1:
        print "\nStarting Pre-Amp Noise, Current, and Voltage Measurement\n",
        block = 0
        k = 0
        n = 0
        while block < 7 :
            set_DAC(block, 0, 15)
            block += 1
        while k < 31 :
            block = 0
            while block < 7 :
                set_DAC(block, 1, k)
                block += 1
            print "Starting s-curve", k
            data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 20, row = range(1, 17), step = 1, start = 0, stop = 175,
            pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
            th_array = [a for a in th_array if a != 0]
            amp_noise_avg[n] = np.mean(noise_array[1:1920])
            pa_spread[n] = np.std(th_array)
            pa_current[n] = measure_current(print_file = 0)
            pa_voltage[n] = multimeter.measure(multi) * 1000
            print "\nAverage Noise: ", amp_noise_avg[n]
            print "Current Draw: ", pa_current[n], "mA"
            print "Voltage: ", pa_voltage[n], "mV\n"

            x[n] = k
            n += 1
            k += step


###############################################################################
# Find Gain Difference for Pre Amp                                            #
###############################################################################

    if pa_gain_diff == 1:
        print "\nCalculating Pre-Amp Gain Difference"
        block = 0
        while block < 7 :
            set_DAC(block, 1, 6)
            set_DAC(block, 0, 15)
            block += 1

        thDAC = measure_DAC_testblocks(point = 5, bit = 8, step = 32, plot = 0, print_file = 0)
        calDAC = measure_DAC_testblocks(point = 6, bit = 8, step = 32, plot = 0, print_file = 0)
        thLSB = np.mean((thDAC[:,160] - thDAC[:,0])/160)*1000 #LSB Threshold DAC in mV
        calLSB = np.mean((calDAC[:,160] - calDAC[:,0])/160)*0.035/1.768*1000 #LSB Calibration DAC in fC


        print "Finding average threshold when k=6 for ref=15"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 15, row = range(1, 17), step = 1, start = 0, stop = 175,
        pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref15k6 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array1[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref15k6
        print "Threshold Spread: ", np.std(th_array)

        print "\nFinding average threshold when k = 6 and ref = 30"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 30, row = range(1, 17), step = 1, start = 0, stop = 250,
        pulse_delay = 500, extract_val = 130, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref30k6 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array2[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref30k6
        print "Threshold Spread: ", np.std(th_array)


        block = 0
        while block < 7 :
            set_DAC(block, 1, 24)
            block += 1
        print "\nFinding average threshold when k=24 for ref=15"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 15, row = range(1, 17), step = 1, start = 0, stop = 175,
        pulse_delay = 500, extract_val = 110, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref15k24 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array3[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref15k24
        print "Threshold Spread: ", np.std(th_array)

        print "\nFinding average threshold when k = 24 and ref = 30"
        data_array, th_array, noise_array = s_curve_rbr_fr(n_pulse = 100, s_type = "THR", ref_val = 30, row = range(1, 17), step = 1, start = 0, stop = 250,
        pulse_delay = 500, extract_val = 130, extract = 1, plot = 0, print_file =0)
        th_array = [a for a in th_array if a != 0]
        ref30k24 = np.mean(th_array[1:1920])
        p=0
        while p < (len(th_array)):
            th_array4[p] = th_array[p] #* thLSB
            p += 1
        print "Average Threshold:", ref30k24
        print "Threshold Spread: ", np.std(th_array)

        Q1 = calLSB * 15
        Q2 = calLSB * 30
        delta_Q = Q2 - Q1

        p = 0
        gain5 = 0
        gain6 = 0
        while p < 2040:
            gain_array1[p] = (th_array2[p] - th_array1[p])/delta_Q
            gain_array2[p]= (th_array4[p] - th_array3[p])/delta_Q
            p += 1
        gain5 = (np.mean(gain_array1) * thLSB)
        gain6 = (np.mean(gain_array2) * thLSB)

        print "\nGain for k=6:", gain5, "[mV/fC]"
        print "Gain for k=24:", gain6, "[mV/fC]"
        print "Gain Difference:", gain6 - gain5, "[mV/fC]"


###############################################################################
# Plot                                                                        #
###############################################################################
    if krum == 1:
        plt.figure(1)
        plt.title("Threshold Variation for Krummenacher")
        plt.xlabel("Krummenacher Value")
        plt.ylabel("Threshold")
        plt.plot( x[0:n], krum_th_avg[0:n])

        plt.figure(2)
        plt.title("Current and Voltage for Krummenacher")
        plt.xlabel("Krummenacher Value")
        plt.ylabel("Voltage (mV), Current (mA)")
        standard_voltage = 82 + (1000 * gnd)
        plt.plot( 15, measured_voltage, 'o', 15, standard_voltage, 'o', x[0:n], krum_voltage[0:n], x[0:n], krum_current[0:n])
        plt.legend(('Measured k=15 Voltage', 'Theoretical k=15 Voltage', 'Voltage', 'Current'), loc='upper right')

        plt.figure(3)
        plt.title("Noise Variation for Krummenacher")
        plt.xlabel("Krummenacher Value")
        plt.ylabel("Noise")
        plt.plot( x[0:n], krum_noise_avg[0:n])

        plt.figure(4)
        plt.title("Average Threshold Spread for Krummenacher")
        plt.xlabel("Krummenacher Value")
        plt.ylabel("Threshold Spread")
        plt.plot(x[0:n], krum_spread[0:n])

    if gain_diff == 1:
        plt.figure(5)
        plt.title("Krummenacher Gain Difference")
        plt.ylabel("Gain (mV/fC)")
        plt.plot(1, gain3, 'o', 1, gain4, 'o')
        plt.legend(('k=6', 'k=24'), loc='upper right')


    if pre_amp == 1:
        plt.figure(6)
        plt.title("Noise Variation for Pre Amp")
        plt.xlabel("Pre Amp Value")
        plt.ylabel("Noise")
        plt.plot( x[0:n], amp_noise_avg[0:n])

        plt.figure(7)
        plt.title("Voltage and Current Variation for Pre Amp")
        plt.xlabel("Pre Amp Value")
        plt.plot( x[0:n], pa_voltage[0:n])
        plt.plot( x[0:n], pa_current[0:n])
        plt.legend(["Voltage (mV)", "Current (mA)"])

        plt.figure(8)
        plt.title("Average Threshold Spread for Pre Amp")
        plt.xlabel("Pre Amp Value")
        plt.ylabel("Threshold Spread")
        plt.plot(x[0:n], pa_spread[0:n])

    if pa_gain_diff == 1:
        plt.figure(9)
        plt.title("Pre Amp Gain Difference")
        plt.ylabel("Gain (mV/fC)")
        plt.plot(1, gain5, 'o', 1, gain6, 'o')
        plt.legend(('k=6', 'k=24'), loc='upper right')

    plt.show()
