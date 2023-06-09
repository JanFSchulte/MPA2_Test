from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erfc
from scipy.special import erf
from scipy.stats import norm
from scipy.stats import chisquare
import matplotlib.cm as cm
import seaborn as sns
import math

# FNAL addition:
from myScripts.mpa_configurations import *

class mpa_cal_utility():
    """ """
    def __init__(self, mpa, I2C, fc7):
        # Class instantiation
        self.mpa = mpa
        self.I2C = I2C
        self.fc7 = fc7
        self.utils = utils

        # FNAL addition
        self.conf = conf
        # Local variables

    # Math functions
    def errorf(self, x, *p):
        """
        :param x:
        :param *p:
        """
        a, mu, sigma = p
        return 0.5*a*(1.0+erf((x-mu)/sigma))
    def line(self, x, *p):
        """
        :param x:
        :param *p:
        """
        g, offset = p
        return  np.array(x) *g + offset
    def gauss(self, x, *p):
        """
        :param x:
        :param *p:
        """
        A, mu, sigma = p
        return A*np.exp(-(x-mu)**2/(2.*sigma**2))
    def errorfc(self, x, *p):
        """
        :param x:
        :param *p:
        """
        a, mu, sigma = p
        return a*0.5*erfc((x-mu)/sigma)

    def extract_scurve(self, row, pixel, s_type, scurve, n_pulse, start, stop, extract):
        """takes scurve data and extracts threshold and noise data.

        :param row:
        :param pixel:
        :param s_type:
        :param scurve:
        :param n_pulse:
        :param start:
        :param stop:
        :param extract:

        """

        th_array = np.zeros(self.conf.npixsnom, dtype = np.int )
        noise_array = np.zeros(self.conf.npixsnom, dtype = np.float )
        chi2_array = np.zeros(self.conf.npixsnom, dtype = np.float )

        nfail = 0

        for r in row:
            for p in pixel:
                pixelid = self.conf.pixelidnom(r,p)

                # Noise and Spread study
                if extract:
                
                    try:
                
                        if s_type == "THR":
                            noise_peak = np.argmax(scurve[pixelid,:])
                            start_DAC = noise_peak + np.where(scurve[pixelid,noise_peak:] <= n_pulse)[0][0]
                            middle = noise_peak + np.argmin(np.abs(scurve[pixelid,noise_peak:]-0.5*n_pulse))
                            par, cov, info, mesg, ier = curve_fit(self.errorfc, list(range(start_DAC, stop)), scurve[pixelid,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, middle, 2], full_output = True, method='lm')

#                            observed = np.clip(scurve[pixelid,start_DAC+1:(stop-start_DAC)+1],1e-9,1000)
#                            fitted = np.clip(self.errorfc(list(range(start_DAC+1,stop-start_DAC+1)),*par),1e-9,1000)
#                            expected = np.sum(observed)/np.sum(fitted) * fitted

#                            c, p = chisquare(observed, expected, ddof=len(par))

                        elif s_type == "CAL":
                            start_DAC = start
                            middle = np.argmin(np.abs(scurve[pixelid,:]-0.5*n_pulse))
                            par, cov, info, mesg, ier = curve_fit(self.errorf, list(range(start_DAC, stop)), scurve[pixelid,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, middle, 2], full_output=True, method='lm')

#                            observed = np.clip(scurve[pixelid,start_DAC+1:(stop-start_DAC)+1],1e-9,1000)
#                            fitted = np.clip(self.errorf(list(range(start_DAC+1,stop-start_DAC+1)),*par),1e-9,1000)
#                            expected = np.sum(observed)/np.sum(fitted) * fitted

#                            c, p = chisquare(observed, expected, ddof=len(par))
                
                        th_array[pixelid] = int(round(par[1]))
                        noise_array[pixelid] = par[2]
#                        chi2_array[pixelid] = c

                        # some selection on p-value
                        if par[0] > 2*n_pulse:
                            nfail += 1
                            th_array[pixelid] = -2
                            noise_array[pixelid] = -2

                    # if the fit fails
                    except RuntimeError as e:
                        nfail += 1
                        th_array[pixelid] = -1
                        noise_array[pixelid] = -1
#                        chi2_array[pixelid] = -1

        print("Pixel fit failures: ",nfail)
        if extract:
            return  th_array, noise_array#, chi2_array
    
    # Readout Counters current method
    def ReadoutCounters(self, raw_mode_en = 0):
        """

        :param raw_mode_en:  (Default value = 0)

        """
    # set the raw mode to the firmware
        self.fc7.write("fc7_daq_cnfg.physical_interface_block.ps_counters_raw_en", raw_mode_en)
        t0 = time.time()
        mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
    #time.sleep(0.1)
    #print "---> Sending Start and Waiting for Data"
    #StartCountersRead()
        self.fc7.start_counters_read()
        timeout = 0
        while ((mpa_counters_ready == 0) & (timeout < 50)):
            time.sleep(0.01)
            mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
            timeout += 1
        if (timeout >= 50):
            fails = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_fsm_state")
            utils.print_info(f"Fail: {fails}")
            failed = True;
            return failed, 0
    #print "---> MPA Counters Ready(should be one): ", mpa_counters_ready
        if raw_mode_en == 1:
            count = np.zeros((2040, ), dtype = np.uint16)
            cycle = 0
            for i in range(0,20000):
                fifo1_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.fifo1_data")
                #print(fifo1_word)
                fifo2_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.fifo2_data")
                #print(fifo2_word)
                line1 = to_number(fifo1_word,8,0)
                line2 = to_number(fifo1_word,16,8)
                line3 = to_number(fifo1_word,24,16)
                line4 = to_number(fifo2_word,8,0)
                line5 = to_number(fifo2_word,16,8)
                if (((line1 & 0b10000000) == 128) & ((line4 & 0b10000000) == 128)):
                    temp = ((line2 & 0b00100000) << 9) | ((line3 & 0b00100000) << 8) | ((line4 & 0b00100000) << 7) | ((line5 & 0b00100000) << 6) | ((line1 & 0b00010000) << 6) | ((line2 & 0b00010000) << 5) | ((line3 & 0b00010000) << 4) | ((line4 & 0b00010000) << 3) | ((line5 & 0b10000000) >> 1) | ((line1 & 0b01000000) >> 1) | ((line2 & 0b01000000) >> 2) | ((line3 & 0b01000000) >> 3) | ((line4 & 0b01000000) >> 4) | ((line5 & 0b01000000) >> 5) | ((line1 & 0b00100000) >> 5)
                    if (temp != 0):
                        count[cycle] = temp - 1
                        cycle += 1
        else:
            # here is the parsed mode, when the fpga parses all the counters
            count = np.array(self.fc7.blockRead("fc7_daq_ctrl.physical_interface_block.fifo2_data", 2040))
            for i in range(2040):
                count[i] = count[i] - 1
        time.sleep(0.001)
        mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
        failed = False
        # print(count)
        return failed, count
    
    def s_curve(self, n_pulse = 1000, s_type = "THR", rbr = 0, ref_val = 50, row = [], step = 1, start = 0, stop = 256, pulse_delay = 200, extract_val = 0, plot=0, extract = 1, print_file=1, filename = "../Results_MPATesting/scurve_fr_"):
        """[summary]

        Parameters
        ----------
        n_pulse : int, optional
            [description], by default 1000
        s_type : str, optional
            [description], by default "THR"
        rbr : int, optional
            [description], by default 0
        ref_val : int, optional
            [description], by default 50
        row : [type], optional
            [description], by default list(range(1,17))
        step : int, optional
            [description], by default 1
        start : int, optional
            [description], by default 0
        stop : int, optional
            [description], by default 256
        pulse_delay : int, optional
            [description], by default 200
        extract_val : int, optional
            [description], by default 0
        extract : int, optional
            [description], by default 1
        print_file : int, optional
            [description], by default 1
        filename : str, optional
            [description], by default "../cernbox/MPA_Results/scurve_fr_"

        Returns
        -------
        [type]
            [description]
        """

        t0 = time.time()
        self.fc7.clear_counters(8)
        row = self.conf.rowsnom
        nrow = self.conf.nrowsnom 
        nstep = int((stop-start)/step+1)
        data_array = np.zeros((self.conf.npixsnom, nstep), dtype = np.int16 )
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.activate_async()

        if s_type == "THR":     
            self.mpa.ctrl_base.set_calibration(ref_val)
        elif s_type == "CAL":  
            self.mpa.ctrl_base.set_threshold(ref_val)
        else: 
            return "DAC type not recognized"

        count = 0
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_L1 = 0, enable_rst = 0, enable_init_rst = 0)
        count = 0
        cur_val = start
        count_err = 0
        failed = 0
        while (cur_val < stop): # Temoporary: need to add clear counter fast command
            if s_type == "CAL":     
                self.mpa.ctrl_base.set_calibration(cur_val)
            elif s_type == "THR":   
                self.mpa.ctrl_base.set_threshold(cur_val)

            # show progress bar
            self.utils.ShowPercent(count, (stop-start)/step, "")
            if rbr:
                for r in row:
                    self.mpa.inject.send_pulses_fast(n_pulse, r, 0, cur_val)
            else: 
                self.mpa.inject.send_pulses_fast(n_pulse, 0, 0, cur_val)
            fail, temp = self.ReadoutCounters(raw_mode_en=0)
            if fail: 
                fail, temp = self.ReadoutCounters(raw_mode_en=0)
            tempnom = self.conf.convertRawToNomPixmap(temp)
            data_array [:, count]= tempnom
            count += 1
            cur_val += step
            if (count_err == 10):
                cur_val = stop
                failed = 1
            self.fc7.clear_counters(8)
            time.sleep(0.001)
            self.fc7.clear_counters(8)
        if failed == 1:
            print ("S-Curve extraction failed")
            return "exit at scurve"

        if extract:
            th_array, noise_array = self.extract_scurve(row = row, pixel = self.conf.colsnom, s_type = s_type, scurve = data_array , n_pulse = n_pulse, start = start, stop = stop, extract = extract)

        t1 = time.time()
        utils.print_log("->  S-Curve Elapsed Time: " + str(t1 - t0))
        if print_file:
            CSV.ArrayToCSV (data_array, str(filename) + "_" + s_type + ".csv")
            if extract:
                CSV.ArrayToCSV (th_array, str(filename) + "_" + s_type + "_Mean.csv")
                CSV.ArrayToCSV (noise_array, str(filename) + "_" + s_type + "_RMS.csv")

        if extract: 
            return data_array, th_array, noise_array
        else: 
            return data_array

    # pixel alive: FNAL addition
    def pixel_alive(self, 
                    n_pulse = 100, 
                    s_type = "CAL", 
                    ref_cal = 250, 
                    ref_thr = 250,
                    pulse_delay = 200,
                    filename = "",
                    plot = 0):

        t0 = time.time()
        self.fc7.clear_counters(8)
        data_array = np.zeros((2040,), dtype = np.int16 )
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.activate_async()

        if s_type == "THR":     
            self.mpa.ctrl_base.set_calibration(ref_cal)
        elif s_type == "CAL":   
            self.mpa.ctrl_base.set_threshold(ref_thr)
        else: 
            return "S-Curve type not recognized"
        count = 0
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_L1 = 0, enable_rst = 0, enable_init_rst = 0)
        failed = 0

        if s_type == "CAL":     
            self.mpa.ctrl_base.set_calibration(ref_cal)
        elif s_type == "THR":   
            self.mpa.ctrl_base.set_threshold(ref_thr)

        # INJECT CHARGE
        self.mpa.inject.send_pulses_fast(n_pulse, 0, 0, ref_cal)
        fail, temp = self.ReadoutCounters(raw_mode_en=0)
        if fail: fail, temp = self.ReadoutCounters(raw_mode_en=0)

        tempnom = self.conf.convertRawToNomPixmap(temp)
        data_array = tempnom

        self.fc7.clear_counters(8)
        time.sleep(0.001)
        self.fc7.clear_counters(8)
        if failed == 1:
            print ("Pixel alive failed")
            return "exit"

        deadpixels = []
        ineffpixels = []
        noisypixels = []
        for p in range(0,len(data_array)):
            if data_array[p]!=n_pulse:
                if data_array[p] == 0: 
                    deadpixels.append(p)
                elif data_array[p] < n_pulse: 
                    ineffpixels.append(p)
                elif data_array[p] > n_pulse:
                    noisypixels.append(p)

        if len(filename) > 0:
            CSV.ArrayToCSV (data_array, str(filename) + ".csv")

        if plot:
            self.utils.plot_2D_map_list(dataarray = data_array, 
                                        data_label="", 
                                        nfig=7,
                                        hmin=-1,hmax=-1, 
                                        plotAverage = True, 
                                        identifier="", 
                                        xlabel="row", ylabel="column",
                                        isChip=True,
                                        israw=False,
                                        show_plot=1, 
                                        save_plot=0)

        t1 = time.time()
        return data_array, deadpixels, ineffpixels, noisypixels

    # mask test: FNAL addition
    def mask_test(self,
                  n_pulse = 1,
                  s_type = "CAL",
                  ref_val = 200,
                  pulse_delay = 200,
                  filename = ""):
        
        t0 = time.time()
        self.fc7.clear_counters(8)
        data_array = np.zeros((2040,), dtype = np.int16 )
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.activate_async()
        if s_type == "THR":     self.mpa.ctrl_base.set_calibration(ref_val)
        elif s_type == "CAL":   self.mpa.ctrl_base.set_threshold(ref_val)
        else: return "S-Curve type not recognized"
        count = 0
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_L1 = 0, enable_rst = 0, enable_init_rst = 0)
        failed = 0

        if s_type == "CAL":
            self.mpa.ctrl_base.set_calibration(ref_val)
        elif s_type == "THR":
            self.mpa.ctrl_base.set_threshold(ref_val)

        # INJECT CHARGE                                                                                                  
        self.mpa.inject.send_pulses_fast_withMasking(n_pulse, 0, 0, ref_val)
        fail, temp = self.ReadoutCounters(raw_mode_en=0)
        if fail: fail, temp = self.ReadoutCounters(raw_mode_en=0)
        tempnom = self.conf.convertRawToNomPixmap(temp)
        data_array = tempnom

        self.fc7.clear_counters(8)
        time.sleep(0.001)
        self.fc7.clear_counters(8)
        if failed == 1:
            print ("Pixel mask test failed")
            return "exit"

        if len(filename) > 0:
            CSV.ArrayToCSV (data_array, str(filename) + ".csv")

        unmaskablepixels = []
        for p in range(0,len(data_array)):
            if data_array[p]!=0:
                unmaskablepixels.append(p)

        return data_array, unmaskablepixels

    def trimming_probe(self, ref = 250, low = 120, high = 60, second_step = 1, nominal_ref = 150, nominal_req = 40, rbr = 0, plot = 0):
        """
        :param ref:  (Default value = 250)
        :param low:  (Default value = 120) - initial mu param value for s-curve fit with low trim bits
        :param high:  (Default value = 60) - initial mu param vailue for s-curve fit with high trim bits
        :param second_step:  (Default value = 1)
        :param nominal_ref:  (Default value = 150)
        :param nominal_req:  (Default value = 40)
        :param rbr:  (Default value = 0)
        :param plot:  (Default value = 1)
        """

        t0 = time.time()
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)

        utils.print_info("->  Trimming DAC MIN scurve...")
        self.mpa.ctrl_pix.reset_trim(0)
        try:
            scurveL, thL, noiseL = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 250, pulse_delay = 500, extract_val = low, extract = 1, plot = plot, print_file =0 )
        except Exception as e:
            raise
        utils.print_info("->  Trimming DAC MAX scurve...")
        self.mpa.ctrl_pix.reset_trim(31)
        try:
            scurveH, thH, noiseH = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 250, pulse_delay = 500, extract_val = high, extract = 1, plot = plot, print_file =0 )
        except Exception as e:
            raise
        thL = np.array(thL); 
        thH = np.array(thH);

        # this is the value that we trim to
        req = (np.mean(thH) + np.mean(thL))/2
        
        print("req = ", req)

        trimLSB =(thH-thL)/32
        trim = np.round((req - thL*1.0)/trimLSB)
        trim = trim.astype(int)

        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            utils.print_info("->  Trimmed scurve...")
            utils.print_info(f"->  Not Trimmerable Pixel {count}")
            try:
                scurveT, thT, noiseT = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 250, pulse_delay = 500, extract_val = nominal_req, extract = 1)
            except Exception as e:
                raise
        else:
            print("Error")

        if second_step:
            thT = np.array(thT);

            trim_incr = np.round((nominal_req - thT)/trimLSB)
            trim_incr = trim_incr.astype(int)
            trim = trim + trim_incr

            if np.size(trim) == 1888:
                count = self.mpa.ctrl_pix.load_trim(trim)
                utils.print_info("->  Nominal scurve ...")
                utils.print_info(f"->  Not Trimmerable Pixel {count}")
                try:
                    scurve, th, noise = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 100, pulse_delay = 500, extract_val = nominal_req, extract = 1)
                except Exception as e:
                    raise
            else:
                print("Error")

        t1 = time.time()
        utils.print_log(f"->  Total Trimming Elapsed Time: {str(t1 - t0)}")
        return scurve, th, noise, trim, count

    def trimming_desy(self, ref = 40, low = 80, req = 130, high = 180, nominal_ref = 15, nominal_req = 85 , trim_ampl = -1, rbr = 0, plot = 0, filename = ""):
        """
        :param ref:  (Default value = 40)
        :param low:  (Default value = 80)
        :param req:  (Default value = 130)
        :param high:  (Default value = 180)
        :param nominal_ref:  (Default value = 15)
        :param nominal_req:  (Default value = 85)
        :param trim_ampl:  (Default value = -1)
        :param rbr:  (Default value = 0)
        :param plot:  (Default value = 1)
        """

        print("Trim using DESY implementation")

        t0 = time.time()
        row = self.conf.rowsnom

        if trim_ampl > -1:
            for block in range(0,7):
                self.I2C.peri_write("C"+str(block), trim_ampl)
        else: trim_ampl = int(self.I2C.peri_read("C"+str(0)))
        print("The current trim ampl is now: ", trim_ampl)
        trm_LSB = round(((0.172-0.048)/32.0*trim_ampl+0.048)/32.0*1000.0,2)
        print("Trimming LSB", trm_LSB, "mV")

        # Somewhat needed for setting trim dac value..... (added by DESY) Also done in Pretrim, was breaking when skipping pretrim
        # Oct. 24 2022 !!!! Now that we added it here. we can skip pretrim for testing.
        self.I2C.row_write('Mask', 0, 0b11111111)
        
        print("Trimming DAC 10 scurve...")
        self.mpa.ctrl_pix.reset_trim(10)
        scurveL, thL, noiseL = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = ref, row = row, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = low, extract = 1, plot = 0, print_file =1, filename=filename+'_trim10' )
        print("Trimming DAC 21 scurve...") # was "DAC MAX"
        self.mpa.ctrl_pix.reset_trim(21) # was 31 
        scurveH, thH, noiseH = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = ref, row = row, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = high, extract = 1, plot = 0, print_file =1, filename=filename+'_trim21' )

        thL = np.array(thL); thH = np.array(thH);
        print("Not Trimmerable Pixel", np.size(np.where(thL > req)) + np.size(np.where(thH < req)))
        trim = np.round((req - thL*1.0)/(thH - thL)*12.0) # was 32 before changing it to 22
        trim = trim.astype(int)
        trim[trim > 31] = 31
        trim[trim < 0] = 0
        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            print("Trimmed scurve...")
            print("Not Trimmerable Pixel", count)
            scurveT, thT, noiseT = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = nominal_ref, row = row, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = 0, print_file =0 )
        else:
            print("Error")
        # Incremental second step?
        thT = np.array(thT);
        trim_incr = np.round((nominal_req - thT)/trm_LSB)
        trim_incr = trim_incr.astype(int)
        trim = trim + trim_incr
        trim[trim > 31] = 31
        trim[trim < 0] = 0
        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            print("Nominal scurve...")
            print("Not Trimmerable Pixel", count)
            scurve, th, noise = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = nominal_ref, row = row, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = plot, print_file =0 )
        else:
            print("Error")
            
         # Incremental third step?
        thT = np.array(th);
        trim_incr = np.round((nominal_req - th)/trm_LSB)
        trim_incr = trim_incr.astype(int)
        trim = trim + trim_incr
        trim[trim > 31] = 31
        trim[trim < 0] = 0
        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            print("Nominal 2nd scurve...")
            print("Not Trimmerable Pixel", count)
            scurve, th, noise = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = nominal_ref, row = row, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = plot, print_file =0 )
        else:
            print("Error")

        CSV.ArrayToCSV (trim, str(filename) + "_trimbits.csv")
        
        t1 = time.time()
        print("Trimming Elapsed Time: " + str(t1 - t0))
        return scurve, th, noise, trim, count

    # Bad bump test: FNAL addition
    def BumpBonding(self, 
                    s_type="CAL", 
                    n_pulse=1000, 
                    ref_val = 250, 
                    rbr = 0, 
                    plot = 0,
                    print_out =False, 
                    returnAll = False, 
                    filename="../Results_MPATesting/bumpbonding_"):
        if print_out: 
            print("Bump Bonding Test at",s_type+"="+str(ref_val))

        extract_val = int(ref_val * 95./218.)
        scurvebb, thbb, noisebb = self.s_curve(n_pulse = n_pulse,  s_type = s_type, rbr = 0, ref_val = ref_val, step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val=extract_val, plot = 0, print_file =0)

        #remove bad pixels, defined pixels where extract_value is 3*std away from thbb mean
        #remove edge pixels

        badpixels = []
        edgepixels = []
        thbb_clean = [th for th in thbb if th != 0]
        for index in range(len(thbb_clean)):
            if self.conf.colfrompixnom(index)==0 or self.conf.colfrompixnom(index)==self.conf.ncolsnom-1:
                edgepixels.append(index)
            elif math.fabs(thbb[index]-np.mean(thbb))>3*np.std(thbb):
                badpixels.append(index)
            #elif math.fabs(noisebb[index])>30:#define fit range < 30 - am I allowed to do it
            #badpixels.append(index)

        noisebb_forfitting = [noisebb[index] for index in range(len(noisebb)) if (index not in badpixels and index not in edgepixels)]
        noisebb_edgefitting = [noisebb[index] for index in edgepixels]

        (nom_mu,nom_sigma) = norm.fit(noisebb_forfitting,loc=min(20.,np.mean(noisebb_forfitting)),scale=min(5.,np.std(noisebb_forfitting)))
        if print_out: print("Noise Peak:",nom_mu,    " (",np.mean(noisebb_forfitting),")")
        if print_out: print("Noise Width",nom_sigma, " (",np.std( noisebb_forfitting),")")

        (edge_mu,edge_sigma) = norm.fit(noisebb_edgefitting,loc=np.mean(noisebb_edgefitting),scale=np.std(noisebb_edgefitting))
        if print_out: print("Edge Noise Peak:",edge_mu,    " (",np.mean(noisebb_edgefitting),")")
        if print_out: print("Edge Noise Width",edge_sigma, " (",np.std( noisebb_edgefitting),")")

        badbumps = []
        badbumpsNonEdge = []
        badbumpmap = []

        for index in range(len(noisebb)):#maybe also define here edge pixels as good bumps ??
            if self.conf.colfrompixnom(index)==0 or self.conf.colfrompixnom(index)==(self.conf.ncolsnom-1):
                mu = edge_mu
                sigma = edge_sigma
            else:
                mu = nom_mu
                sigma = nom_sigma
            if math.fabs(noisebb[index]-mu)>5.*sigma:
                badbumps.append(index)
                if not (self.conf.colfrompixnom(index)==0 or self.conf.colfrompixnom(index)==(self.conf.ncolsnom-1)):
                    badbumpsNonEdge.append(index)
                badbumpmap.append(1)
            else:
                badbumpmap.append(0)

        # Write out all the files
        CSV.ArrayToCSV (badbumps, str(filename) + "_BadBumps" + ".csv")
        CSV.ArrayToCSV (badbumpmap, str(filename) + "_BadBumpMap" + ".csv")
        CSV.ArrayToCSV (noisebb, str(filename) + "_Noise_BadBump" + ".csv")
        CSV.ArrayToCSV (scurvebb, str(filename) + "_SCurve_BadBump" + ".csv")

        bin_width = 0.1
        bin_round = int(max(0,-math.log10(bin_width)))
        bin_min = max(0,round(min(noisebb_forfitting+noisebb_edgefitting)-bin_width,bin_round))
        bin_max = min(30,round(max(noisebb_forfitting+noisebb_edgefitting)+bin_width,bin_round))
        num_binsbb = np.arange(bin_min,bin_max,bin_width)

        if print_out:
            print("Total BadBumps fit non-edge:",len(badbumpsNonEdge),self.conf.getPercentage(badbumpsNonEdge))
            print("Total BadBumps fit:",len(badbumps),self.conf.getPercentage(badbumps))
#            print("Total BadBumps VCal < 3:",len(badbumpsVCal3),self.conf.getPercentage(badbumpsVCal3))
#            print("Total BadBumps VCal < 5:",len(badbumpsVCal5),self.conf.getPercentage(badbumpsVCal5))

        if returnAll:
            return badbumps, badbumpsNonEdge
        return badbumps


