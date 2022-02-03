from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.logs_utility import *
from collections import OrderedDict
from main import *
import traceback

import time
import sys
import csv
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

'''
MPA2 Basic Testing Routine

Test routine for functionality verification of MPA2 ASICS

To run probe, e.g. for chip 187:

from mpa_methods.mpa_main_test import all
probe = MainTestsMPA(tag = 187, chip = mpa)
probe.RUN()

If no directory name passed to MainTestsMPA, results will be located in ../MPA2_Results/TEST/

'''
try:
    mpa
except:
    mpa = False

class MainTestsMPA():

    def __init__(self, tag="ChipN_0", runtest='default', directory='../MPA2_Results/TEST/', chip = mpa):
        if(chip):
            self._init(chip)
            self.summary = results()
            self.runtest = RunTest('default')
            self.die_number = tag
            self.tag = f"N_{tag}"
            self.wafer = False
            self.lot = False
            self.Configure(directory=directory, runtest=runtest)

    def Configure(self, directory = '../MPA2_Results/Wafer0/', runtest = 'default'):
        self.DIR = directory
        self.dvdd_curr = self.dvdd
        if(runtest == 'default'):
            self.runtest.set_enable('Power', 'ON')
            self.runtest.set_enable('Initialize', 'ON')
            self.runtest.set_enable('Shift', 'ON')
            self.runtest.set_enable('Calibrate Bias', 'ON')
            self.runtest.set_enable('Calibrate VREF', 'ON')
            self.runtest.set_enable('ADC Measure', 'ON')
            self.runtest.set_enable('DACs', 'ON')
            self.runtest.set_enable('S-Curve', 'ON')
            self.runtest.set_enable('Analog Pixel', 'ON')
            self.runtest.set_enable('Strip In', 'ON')
            self.runtest.set_enable('Memory', 'ON')
            self.runtest.set_enable('BIST', 'ON')
            self.runtest.set_enable('Ring Oscillators', 'ON')
            self.runtest.set_enable('DLL', 'ON')
        else:
            self.runtest = runtest

    def RUN(self, runname='default', write_header=True):       
        self.test_good = True
        ## Setup log files #####################
        #if(runname=='default'): chip_info = self.tag
        #else: chip_info = runname
        chip_info = self.tag
        time_init = time.time()
        version = 0
        while(True):
            fo = (self.DIR + "/Chip_{c:s}_v{v:d}/timetag.log".format(c=str(chip_info), v=version))
            if(os.path.isfile(fo)):
                version += 1
            else:
                curdir = fo[:fo.rindex(os.path.sep)]
                if not os.path.exists(curdir):
                    os.makedirs(curdir)
                fp = open(fo, 'w')
                fp.write( utils.date_time('csv') + '\n')
                fp.close()
                break
        fo = curdir + "/Test_"
        utils.close_log_files()
        utils.set_log_files(curdir+'/OperationLog.txt',curdir+'/ErrorLog.txt')
        utils.print_info('==============================================')
        utils.print_info('TEST ROUTINE {:s}\n'.format(str(runname)))
        utils.print_info("->  The log files are located in {:s}/ \n".format(curdir))
        #if(self.runtest.is_active('ADC', display=False)):
        #    self.ssa.biascal.SetMode('Keithley_Sourcemeter_2410_GPIB')
        ## Main test routine ##################
        self.pwr.set_supply(mode='on', display=False, d=self.dvdd, a=self.avdd, p=self.pvdd)
        # Init Tests
        self.pwr.disable_mpa()
        self.test_routine_power(filename=fo, mode='reset_mpa')
        self.pwr.enable_mpa()
        self.test_routine_power(filename=fo, mode='startup_mpa')
        self.test_routine_initialize(filename=fo)
        self.test_routine_shift(filename=fo)
        # Analog Tests
        self.test_routine_calibrate_bias(filename=fo)
        self.test_routine_calibrate_vref(filename=fo)
        self.test_routine_measure_adc(filename=fo)
        self.test_routine_dacs(filename=fo)
        self.test_routine_analog(filename=fo)
        # Digital Tests
        self.test_routine_analog_pixel(filename=fo)
        self.test_routine_strip_in(filename=fo)
        self.test_routine_memory(filename=fo)
        self.test_routine_bist(filename=fo)
        self.test_routine_ring_oscillators(filename=fo)
        self.test_routine_dll(filename=fo)
        # Save summary ######################
        self.summary.save(
            directory=self.DIR, filename=("Chip_{c:s}_v{v:d}/".format(c=str(chip_info), v=version)),
            runname=str(version), write_header = write_header)
        self.summary.display()
        time_end = time.time()
        utils.print_log(f"->  Total Time: {time_end - time_init}")
        utils.close_log_files()
        self.pwr.set_supply(mode='off', display=False)
        return self.test_good

    def test_routine_power(self, filename = 'default', runname = '', mode = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Power')
        while (en and wd < 3):
            try:
                [st, Id, Ia, Ip] = self.pwr.test_power(state=mode, display=True)
                self.summary.set('I_DVDD_'+mode, Id, 'mA', '',  runname)
                self.summary.set('I_AVDD_'+mode, Ia, 'mA', '',  runname)
                self.summary.set('I_PVDD_'+mode, Ip, 'mA', '',  runname)
                if(not st): self.test_good = False
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  power measurements error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('I_DVDD_'+mode, -1000, '', '',  runname)
                    self.summary.set('I_AVDD_'+mode, -1000, '', '',  runname)
                    self.summary.set('I_PVDD_'+mode, -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_initialize(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Initialize')
        while (en and wd < 3):
            try:
                time.sleep(1)
                r1 = self.mpa.init()
                self.summary.set('init', int(r1), '', '',  runname)
                if(not r1): self.test_good = False
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Initializing MPA error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('init', -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_shift(self, filename= "default", runname=''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Shift')
        while (en and wd < 3):
            try:
                time.sleep(1)
                r1 = self.test.shift(verbose = 1)
                self.summary.set('shift', int(r1), '', '',  runname)
                if(not r1): self.test_good = False
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Shift test error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('shift', -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_calibrate_bias(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Calibrate Bias')
        while (en and wd < 3):
            try:
                bg = self.bias.measure_bg()
                gnd = self.bias.measure_gnd()
                r1 = self.bias.calibrate_chip(gnd_corr = gnd, print_file = 1, filename = filename+"bias_calibration")
                r1 = round(np.mean(r1),1)
                self.summary.set('avg_GND',gnd*1000 ,'mV', '',  runname)
                self.summary.set('avg_VBG', bg*1000, 'mV', '',  runname)
                self.summary.set('avg_bias_DAC', round(r1,3), '', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("-> Calibration error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('avg_GND',-1000,'', '',  runname)
                    self.summary.set('avg_VBG',-1000, '', '',  runname)
                    self.summary.set('avg_bias_DAC', -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_calibrate_vref(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Calibrate VREF')
        while (en and wd < 3):
            try:
                self.vref_dac_val = self.bias.calibrate_vref(self.vref_nominal, 32)[1]
                self.summary.set('VREF_DAC', int(self.vref_dac_val), '', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("-> Calibration error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('VREF_DAC',-1000, '', '',  runname)
                    self.test_good = False


    def test_routine_measure_adc(self, filename = "default", runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('ADC Measure')
        while (en and wd < 3):
            try:
                adc_msr_good = 1
                utils.print_info("-> Measuring all ADC points.")
                bias_blocks, other_blocks = self.mpa.measure.adc_measure_all(filename)
                if (np.any(bias_blocks==0)) or (np.any(bias_blocks==-1000)) or (np.any(other_blocks==0)) or (np.any(other_blocks==-1000)):
                    adc_msr_good = 0
                    utils.print_error("-> ADC measurement failed.")
                else:
                    utils.print_good("-> ADC measurement passed.")
                self.summary.set('ADC_MSR', int(adc_msr_good), '', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("-> ADC measurement error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('ADC_MSR',-1000, '', '',  runname)
                    self.test_good = False


    def test_routine_save_config(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Configuration')
        while (en and wd < 3):
            try:
                self.ssa.chip.ctrl.save_configuration(filename + 'configuration' + str(runname) + '.csv', display=False)
                utils.print_good("->  Config registers readout via I2C and saved corrrectly.")
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Config registers save error. Reiterating...")
                wd +=1;
                if(wd>=3): self.test_good = False

    def test_routine_dacs(self, filename, runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('DACs')
        while (en and wd < 3):
            try:
                self.bias.trimDAC_amplitude(self.trim_amplitude)
                thDAC = self.bias.measure_DAC_testblocks(point = 5, bit = 8, step = 127, plot = 0, print_file = 1, filename = filename + "Th_DAC", verbose = 0)
                calDAC = self.bias.measure_DAC_testblocks(point = 6, bit = 8, step = 127, plot = 0, print_file = 1, filename = filename + "Cal_DAC", verbose = 0)
                self.thLSB = np.mean((thDAC[:,127] - thDAC[:,0])/127)*1000 #LSB Threshold DAC in mV
                self.calLSB = np.mean((calDAC[:,127] - calDAC[:,0])/127)*0.035/1.768*1000 #LSB Calibration DAC in fC
                self.summary.set('thLSB'    , self.thLSB, 'mV', '',  runname)
                self.summary.set('calLSB'    , self.calLSB, 'fC', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Measure DAC testblocks error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('thLSB'    , -1000, '', '',  runname)
                    self.summary.set('calLSB'    , -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_analog(self, filename='../SSA_Results/Chip0/', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        if (self.thLSB == False) or (self.calLSB == False):
            self.test_routine_dacs(filename=filename)
        en = self.runtest.is_active('S-Curve')
        while (en and wd < 3):
            try:
                th_H = int(round(self.high_th_DAC*self.thLSB/self.ideal_th_LSB))
                th_T = int(round(self.trim_th_DAC*self.thLSB/self.ideal_th_LSB))
                th_L = int(round(self.low_th_DAC*self.thLSB/self.ideal_th_LSB))
                cal_H = int(round(self.high_cl_DAC*self.ideal_cl_LSB/self.calLSB))
                cal_T = int(round(self.trim_cl_DAC*self.ideal_cl_LSB/self.calLSB))
                cal_L = int(round(self.low_cl_DAC*self.ideal_cl_LSB/self.calLSB))

                self.mpa.chip.ctrl_base.disable_test()
                self.mpa.init(display=0)
                self.fc7.activate_I2C_chip(verbose=0)

                data_array,cal_A, noise_A, trim, pix_out = self.cal.trimming_probe(
                    ref = th_H, low = cal_H - self.high_cl_ofs, 
                    req = cal_H, high = cal_H + self.high_cl_ofs, 
                    nominal_ref = th_T, 
                    nominal_req = cal_T, 
                    trim_ampl = self.trim_amplitude, 
                    rbr = 0, 
                    plot = 0)
                utils.print_info("->  Final scurve ...")
                scurve, cal_B, noise_B  = self.cal.s_curve(
                    n_pulse = 1000, 
                    s_type = "CAL", 
                    rbr = 0, 
                    ref_val = th_L, 
                    row = list(range(1,17)), 
                    step = 1, 
                    start = 0, 
                    stop = 100, 
                    pulse_delay = 500, 
                    extract_val = cal_L, 
                    extract = 1, 
                    plot = 0, 
                    print_file = 1, 
                    filename = filename + "Scurve15")

                gain = (th_T-th_L)/(np.mean(cal_A[1:1920]) - np.mean(cal_B[1:1920])) * self.thLSB / self.calLSB # Average
                thr_spread = np.std(cal_B[1:1919])
                noise = np.mean(noise_B[1:1919])
                self.summary.set('gain'    , gain, 'mV/fC', '',  runname)
                self.summary.set('noise'    , noise, '', '',  runname)
                self.summary.set('threshold_spread'    , thr_spread, '', '',  runname)

                if(scurve.any() and (thr_spread < 2.5) and (thr_spread > 0.5) and (noise < 2)):
                    utils.print_good(f"\n->  Scurve FE Gain:      {str(round(gain,1))} mV/fC")
                    utils.print_good(f"->  ThLSB:               {str(round(self.thLSB,3))}")
                    utils.print_good(f"->  CalLSB:              {str(round(self.calLSB,3))}")
                    utils.print_good(f"->  Noise:               {str(round(noise,3))}")
                    utils.print_good(f"->  Threshold Spread:    {str(round(thr_spread,3))}")
                    utils.print_log(  "->  Total Test time:     {:7.2f} s".format((time.time()-time_init))); time_init = time.time();
                else:
                    utils.print_error(f"\n->  Scurve FE Gain:      {str(round(gain,1))} mV/fC")
                    utils.print_error(f"->  ThLSB:               {str(round(self.thLSB,3))}")
                    utils.print_error(f"->  CalLSB:              {str(round(self.calLSB,3))}")
                    utils.print_error(f"->  Noise:               {str(round(noise,3))}")
                    utils.print_error(f"->  Threshold Spread:    {str(round(thr_spread,3))}")
                    utils.print_log(  "->  Total Test time:     {:7.2f} s".format((time.time()-time_init))); time_init = time.time();
                    utils.print_error( "->  Scurve trimming error.")
                    utils.print_error( "->  Scurve noise evaluation error.")
                    utils.print_error( "->  Scurve Gain and Offset evaluation error.")
                    self.test_good = False
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Scurve measures test error. Reiterating...")
                wd +=1;
                if(wd>=3): 
                    self.summary.set('gain'    , -1000, '', '',  runname)
                    self.summary.set('noise'    , -1000, '', '',  runname)
                    self.summary.set('threshold_spread'    , -1000, '', '',  runname)
                    self.test_good = False
        wd = 0
    
    def test_routine_analog_pixel(self, filename, runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Analog Pixel')
        anapix = []
        while (en and wd < 3):
            try:
                self.mpa.init(reset_board = 1, display = 0)
                self.mpa.chip.ctrl_pix.disable_pixel(0,0)
                anapix.append(self.test.analog_pixel_test(print_log=0, verbose = 0))

                if ((len(anapix[0]) > 0) & (len(anapix[0]) < 50)):
                    anapix.append(self.test.analog_pixel_test(print_log=0, verbose = 0))
                    BadPixA = self.GetActualBadPixels(anapix)
                else: BadPixA = anapix[0]
                with open(filename+'BadPixelsA.csv', 'w') as csvfile:
                    CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    for i in BadPixA: CVwriter.writerow(i)
                
                self.summary.set('pixel_errors', np.size(BadPixA), 'cnt', '', runname)
                if np.size(BadPixA) > 100:
                    utils.print_warning(str(np.size(BadPixA)) + " << Bad Pixels (Ana)")
                    self.test_good = False
                else: 
                    utils.print_info(str(np.size(BadPixA)) + " << Bad Pixels (Ana)")
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Analog Pixel test error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('pixel_errors',-1000, '', '', runname)
                    self.test_good = False
        wd = 0

    def test_routine_strip_in(self, filename, runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Strip In')
        anapix = []
        while (en and wd < 3):
            try:
                strip_in = self.test.strip_in_scan(print_file = 1, filename = filename + "strip_input_scan_rising", probe=0, verbose = 1)
                #Check if any row (latency) is all 1
                good_si = 0
                for i in range(0,8):
                    if (strip_in[i,:].all() > self.signal_integrity_limit): good_si = 1
                if good_si:
                    utils.print_good("Strip In Scan passed")
                    print(strip_in)
                    StripIn = 1
                else:
                    utils.print_info("Changing edge")
                    strip_in = self.test.strip_in_scan(print_file = 1, edge = "rising", filename = filename + "strip_input_scan_falling", probe=0, verbose = 1)
                    StripIn = 0
                    for i in range(0,8):
                        if (strip_in[i,:].all() > self.signal_integrity_limit): good_si = 1
                    if good_si:
                        utils.print_good("Strip In Scan passed (changing edge)")
                        StripIn = 1
                    else:
                        utils.print_error("Strip In Scan failed")
                        self.test_good = False
                        StripIn = 0
                self.summary.set('strip_in', StripIn, '', '', runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Strip Input test error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('strip_in', -1000, '', '', runname)
                    self.test_good = False
        wd = 0

    def test_routine_memory(self, filename, runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Memory')
        anapix = []
        while (en and wd < 3):
            try:
                #self.mpa.pwr.set_dvdd(voltage/100.0)
                self.mpa.init( reset_board = 1, reset_chip = 1, display = 0)
                bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = filename + "LogMemTest_100.txt", verbose = 0)
                mempix = []
                mempix.append(bad_pix)
                if ((len(mempix[0]) > 0) & (len(mempix[0]) < 20)):
                    bad_pix, error, stuck, i2c_issue, missing = self.test.mem_test(print_log=1, filename = filename + "LogMemTest_100_bis.txt", verbose = 0)
                    mempix.append(bad_pix)
                    BadPixM = self.GetActualBadPixels(mempix)
                else: BadPixM = mempix[0]
                # Write Failing Pixel
                with open(filename+"BadPixelsM_100.csv", 'w') as csvfile:
                    CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    for i in BadPixM: CVwriter.writerow(i)
                # Save Statistics
                with open(filename+"Mem100_Summary.csv", 'w') as csvfile:
                    CVwriter = csv.writer(csvfile, delimiter=' ',	quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    Memory12Flags = [len(BadPixM), stuck, i2c_issue, missing]
                    CVwriter.writerow(Memory12Flags)
                # Set Flags for final summary
                if ((len(BadPixM)<1) and (stuck <10) and (i2c_issue < 20) and (missing <10)): 
                    Mem10 = 1
                    utils.print_good(str(len(BadPixM)) + " << Bad Pixels (Mem)")
                else:
                    Mem10 = 0
                    utils.print_warning(str(len(BadPixM)) + " << Bad Pixels (Mem)")
                    self.test_good = False
                self.summary.set('memory_1V', Mem10, '', '', runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Memory test error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('memory_1V', -1000, '', '', runname)
                    self.test_good = False
        wd = 0

    def test_routine_bist(self, filename= "default", runname=''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('BIST')
        while (en and wd < 3):
            try:
                row_bist, sram_bist = self.test.row_bist(verbose=1)
                sram_bist_pass = 0; row_bist_pass = 0
                if np.all(sram_bist == 0): # sram bist passed if all elements are 0
                    sram_bist_pass = 1
                if np.all(row_bist == 5):  # row bist if all elements equal 5
                    utils.print_good(f"->  Row BIST passed with: {row_bist}")
                    row_bist_pass = 1
                else:
                    utils.print_error(f"->  Row BIST failed with: {row_bist}")
                    self.test_good = False
                self.summary.set('SRAM_BIST', sram_bist_pass, '', '', runname)
                self.summary.set('row_BIST', row_bist_pass, '', '', runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  BIST error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.test_good = False
                    self.summary.set('SRAM_BIST', -1000, '', '', runname)
                    self.summary.set('row_BIST', -1000, '', '', runname)

    def test_routine_ring_oscillators(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('Ring Oscillators')
        while (en and wd < 3):
            try:
                r0, r1=self.test.ro_scan(n_samples = 10)
                utils.print_info(f"->  RO Inverter: {r0[0]}")
                utils.print_info(f"->  RO Delay:    {r1[0]}")
                self.summary.set('ro_inverter'    , r0[0], '', '',  runname)
                self.summary.set('ro_delay'    , r1[0], '', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("->  Ring Oscillators error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('ro_inverter'    , -1000, '', '',  runname)
                    self.summary.set('ro_delay'    , -1000, '', '',  runname)
                    self.test_good = False

    def test_routine_dll(self, filename = 'default', runname = ''):
        filename = self.summary.get_file_name(filename)
        time_init = time.time()
        wd = 0
        en = self.runtest.is_active('DLL')
        while (en and wd < 3):
            try:
                dll_pass = self.test.dll_basic_test()
                if dll_pass==0: 
                    dll_pass=1
                else: 
                    dll_pass=0
                    self.test_good = False
                self.summary.set('DLL'    , dll_pass, '', '',  runname)
                break
            except(KeyboardInterrupt): break
            except:
                self.print_exception("-> DLL error. Reiterating...")
                wd +=1;
                if(wd>=3):
                    self.summary.set('DLL' , -1000, '', '',  runname)
                    self.test_good = False

    def print_exception(self, text='Exception'):
        utils.print_warning(text)
        self.exc_info = sys.exc_info()
        utils.print_warning("======================")
        exeptinfo = traceback.format_exception(*self.exc_info )
        for extx in exeptinfo:
            utils.print_warning(extx)
        utils.print_warning("======================")

    def finalize(self):
        while (wd < 3):
            try:
                self.pwr.set_dvdd(self.dvdd); time.sleep(1)
                self.ssa.reset(); time.sleep(1)
            except:
                wd +=1;
    
    def GetActualBadPixels(self, BPA):
        #print BPA
        badpix = BPA[0]
        goodpix = []
        for i in range(1, len(BPA)):
            for j in badpix:
                if j not in BPA[i]:
                    goodpix.append(j)
        for i in goodpix:
            badpix.remove(i)
        return badpix

    def idle_routine(self, filename = 'default', runname = '', duration=5, voltage=1.0):
        # run all functional test with STUB at BX rate, L1 data at 1MHz
        # if during X-ray irradiation, this is running all time except
        # of when the other tests are running
        utils.print_info('==============================================')
        utils.print_info('IDLE ROUTINE {:s}\n'.format(str(runname)))
        wd=0
        while (wd < 3):
            try:
                self.pwr.set_dvdd(voltage); time.sleep(1)
                self.ssa.reset(); time.sleep(1)
                pwr = self.pwr.get_power()

                striplist, centroids, hip_hits, hip_flags  = self.test.generate_clusters(
                    nclusters=8, min_clsize=1, max_clsize=2, smin=1,
                    smax=119, HIP_flags=True)

                print(striplist)

                results = self.ssa.seuutil.Run_Test_SEU(
                    check_stub=True, check_l1=True, check_lateral=False, create_errors = False, t1edge='falling',
                    strip = striplist, centroids=centroids, hipflags = hip_hits, delay = 75, run_time = duration,
                    cal_pulse_period = 1, l1a_period = 39, latency = 501, display = 1, stop_if_fifo_full = 1, show_every=-1)

                [CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, alignment] = results
                fo = open(filename+'.csv', 'a')
                fo.write('\n{:16s},{:8.3f},{:8.3f},{:8.3f},{:10d},{:10d},{:10d},{:10d},{:10d},{:10d},{:10.3f}'.format(
                    runname, pwr[0], pwr[1], pwr[2], CL_er, L1_er, LH_er, CL_ok, L1_ok, LH_ok, test_duration) )
                fo.close()
                break
            except(KeyboardInterrupt):
                utils.print_info("\n\n\nUser interrupt. The routine will stop at the end of the iteration.\n\n\n")
                return 'KeyboardInterrupt'
            except:
                self.print_exception(text="->  Error in Idle Routine.")
                wd +=1;
                if(wd>=3): self.test_good = False
        return 0

    def _init(self, chip):
        self.mpa = chip
        #self.i2c = chip.i2c
        self.fc7 = chip.chip.fc7
        self.cal = chip.cal
        self.pwr = chip.pwr
        self.bias = chip.bias
        self.test = chip.test
        self.dvdd = 1.00; #for the offset of the board
        self.pvdd = 1.20
        self.avdd = 1.20
        self.thLSB = False
        self.calLSB = False
        self.vref_dac_val = False
        # Nominal values
        # Analog Paramters
        self.vref_nominal = 0.850
        self.ideal_th_LSB = 1.456
        self.ideal_cl_LSB = 0.035
        self.high_th_DAC = 250
        self.high_cl_DAC = 90
        self.trim_th_DAC = 150
        self.trim_cl_DAC = 40
        self.low_th_DAC = 100
        self.low_cl_DAC = 15
        self.high_cl_ofs = 30
        self.trim_amplitude = 24
        # Digital Parameters
        self.signal_integrity_limit = 0.99
