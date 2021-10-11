from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
import seaborn as sns

class mpa_cal_utility():
    """ """
    def __init__(self, mpa, I2C, fc7):
        # Class instantiation
        self.mpa = mpa
        self.I2C = I2C
        self.fc7 = fc7
        self.utils = utils
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
    def plot_extract_scurve(self, row, pixel, s_type, scurve, n_pulse, nominal_DAC, start, stop, extract, plot):
        """takes scurve data and extracts threshold and noise data. If
        plot = 1, it also plots scurves and histograms

        :param row:
        :param pixel:
        :param s_type:
        :param scurve:
        :param n_pulse:
        :param nominal_DAC:
        :param start:
        :param stop:
        :param extract:
        :param plot:

        """
        th_array = np.zeros(2040, dtype = np.int )
        noise_array = np.zeros(2040, dtype = np.float )
        for r in row:
            for p in pixel:
                if plot:
                    plt.plot(list(range(start,stop)), scurve[(r-1)*120+p,0:(stop-start)],'-')
            # Noise and Spread study
                if extract:
                    try:
                        if s_type == "THR":
                            start_DAC = np.argmax(scurve[(r-1)*120+p,:]) + 10
                            par, cov = curve_fit(self.errorfc, list(range(start_DAC, (stop-start))), scurve[(r-1)*120+p,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, nominal_DAC, 2])
                        elif s_type == "CAL":
                            start_DAC = 0
                            par, cov = curve_fit(self.errorf, list(range(start_DAC, (stop-start))), scurve[(r-1)*120+p,start_DAC + 1 :(stop-start) + 1], p0= [n_pulse, nominal_DAC, 2])
                        th_array[(r-1)*120+p] = int(round(par[1]))
                        noise_array[(r-1)*120+p] = par[2]
                    except RuntimeError or TypeError:
                        utils.print_error(f"Fitting failed on pixel {p}  row: {r}")
                        th_array[(r-1)*120+p] = nominal_DAC
        th_array = [a for a in th_array if a != 0]
        noise_array = [b for b in noise_array if b != 0]
        if plot:
            if s_type == "THR":     plt.xlabel('Threshold DAC value')
            if s_type == "CAL":     plt.xlabel('Calibration DAC value')
            plt.ylabel('Counter Value')
            if extract:
                plt.figure(2)
                if len(th_array) == 1:
                    plt.title("Threshold")
                    plt.plot(pixel, th_array, 'o')
                else:
                    plt.hist(th_array, bins=list(range(min(th_array), max(th_array) + 1, 1)))
                plt.figure(3)
                if len(noise_array) == 1:
                    plt.title("Noise")
                    plt.plot(pixel, noise_array, 'o')
                else:
                    plt.hist(noise_array, bins=np.arange(min(noise_array), max(noise_array) + 1 , 0.1))
                print("Threshold Average: ", np.mean(th_array), " Spread SD: ", np.std(th_array))
                print("Noise Average: ", np.mean(noise_array), " Spread SD: ", np.std(noise_array))
        if extract:
            return  th_array, noise_array
    
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
    
    # Test S-curve (~10 secs):
    # a = cal.s_curve( n_pulse = 1000, s_type = "CAL", rbr = 0, ref_val = 150, row = range(1,17), step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = 0, extract = 0, plot = 1, print_file =0 )
    # NB: product n_pulse*pulse_delay > 500e3 to avoid communication problem (IP bus related?)
    def s_curve(self, n_pulse = 1000, s_type = "THR", rbr = 0, ref_val = 50, row = list(range(1,17)), step = 1, start = 0, stop = 256, pulse_delay = 200, extract_val = 0, extract = 1, plot = 1, print_file =1, filename = "../cernbox/MPA_Results/scurve_fr_"):
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
        plot : int, optional
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
        row = np.array(row)
        nrow = int(row.shape[0])
        nstep = int((stop-start)/step+1)
        data_array = np.zeros((2040, nstep), dtype = np.int16 )
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)
        self.mpa.ctrl_base.activate_async()
        if s_type == "THR":     self.mpa.ctrl_base.set_calibration(ref_val)
        elif s_type == "CAL":   self.mpa.ctrl_base.set_threshold(ref_val)
        else: return "S-Curve type not recognized"
        count = 0
        self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
        Configure_TestPulse_MPA(200, int(pulse_delay/2), int(pulse_delay/2), n_pulse, enable_L1 = 0, enable_rst = 0, enable_init_rst = 0)
        count = 0
        cur_val = start
        count_err = 0
        failed = 0
        while (cur_val < stop): # Temoporary: need to add clear counter fast command
            if s_type == "CAL":     self.mpa.ctrl_base.set_calibration(cur_val)
            elif s_type == "THR":   self.mpa.ctrl_base.set_threshold(cur_val)
            #self.utils.ShowPercent(count, (stop-start)/step, "")
            if rbr:
                for r in row:
                    self.mpa.inject.send_pulses_fast(n_pulse, r, 0, cur_val)
            else: self.mpa.inject.send_pulses_fast(n_pulse, 0, 0, cur_val)
            fail, temp = self.ReadoutCounters(raw_mode_en=0)
            if fail: fail, temp = self.ReadoutCounters(raw_mode_en=0)
            data_array [:, count]= temp
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
        if print_file:
            #CSV.ArrayToCSV (data_array, str(filename) + "_" + s_type + str(ref_val) + ".csv")
            CSV.ArrayToCSV (data_array, str(filename) + "_" + s_type + ".csv")
        if extract:
            if extract_val == 0:
                if s_type == "THR":     extract_val = ref_val*1.66+70
                elif s_type == "CAL":   extract_val = ref_val/1.66-40
            th_array, noise_array = self.plot_extract_scurve(row = row, pixel = list(range(2,120)), s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, plot = plot, extract = extract)
        elif plot:
            self.plot_extract_scurve(row = row, pixel = list(range(2,120)), s_type = s_type, scurve = data_array , n_pulse = n_pulse, nominal_DAC = extract_val, start = start, stop = stop, extract = 0, plot = plot)
        t1 = time.time()
        if plot or extract:
            plt.show()
            utils.print_log("->  S-Curve Elapsed Time: " + str(t1 - t0))
        if extract: return data_array, th_array, noise_array
        else: return data_array

    ### Trimming routine
    def trimming_step(self, pix_out = [["Row", "Pixel", "DAC"]], n_pulse = 1000, s_type = "THR", ref_val = 10, iteration = 1, nominal_DAC = 110, data_array = np.zeros(2040, dtype = np.int ), plot = 1,  stop = 150, ratio = 3.90, row = list(range(1,17)), pixel = list(range(1,120))):
        """

        :param pix_out:  (Default value = [["Row")
        :param "Pixel":
        :param "DAC"]]:
        :param n_pulse:  (Default value = 1000)
        :param s_type:  (Default value = "THR")
        :param ref_val:  (Default value = 10)
        :param iteration:  (Default value = 1)
        :param nominal_DAC:  (Default value = 110)
        :param data_array:  (Default value = np.zeros(2040)
        :param dtype:  (Default value = np.int ))
        :param plot:  (Default value = 1)
        :param stop:  (Default value = 150)
        :param ratio:  (Default value = 3.90)
        :param row:  (Default value = range(1)
        :param 17):
        :param pixel:  (Default value = range(1)
        :param 120):

        """
        t0 = time.time()
        self.mpa.ctrl_pix.load_trim(data_array)
        try: scurve_init = self.s_curve(n_pulse = n_pulse,  s_type = s_type, rbr = 0, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 500, extract = 0, plot = 0, print_file =0)
        except TypeError: return
        scurve = scurve_init
        for i in range(0,iteration):
            print("")
            print("Parameter Extraction ", i+1, ":")
            for r in row:
                for p in pixel:
                    try:
                        if s_type == "THR":
                            start_DAC = np.argmax(scurve[(r-1)*120+p,:]) + 10
                            par, cov = curve_fit(self.errorfc, list(range(start_DAC, stop)), scurve[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, nominal_DAC, 2])
                        elif s_type == "CAL":
                            start_DAC = 0
                            par, cov = curve_fit(self.errorf, list(range(start_DAC, stop)), scurve[(r-1)*120+p,start_DAC + 1 :stop + 1], p0= [n_pulse, nominal_DAC, 2])
                        init_DAC = int(round(par[1]))
                        trim_DAC = int(round((nominal_DAC - init_DAC)/ratio))
                        curr_dac = self.I2C.pixel_read("TrimDAC",r,p)
                        if s_type == "THR": new_DAC = curr_dac + trim_DAC
                        elif s_type == "CAL": new_DAC = curr_dac - trim_DAC
                        if (new_DAC > 31):
                            if (i == iteration - 1): pix_out.append([r, p , new_DAC])
                            new_DAC = 31
                            print("High TrimDAC limit for pixel: ", p, " Row: ", r)
                        if (new_DAC < 0):
                            if (i == iteration - 1): pix_out.append([r, p , new_DAC])
                            new_DAC = 0
                            print("Low TrimDAC limit for pixel: ", p, " Row: ", r)
                        self.I2C.pixel_write("TrimDAC", r, p, new_DAC)
                        data_array[(r-1)*120+p] = new_DAC
                    except RuntimeError or TypeError:
                        utils.print_error(f"Fitting failed on pixel {p}  row: {r}")
            if (i != iteration - 1):
                try: scurve = self.s_curve(n_pulse = n_pulse, s_type = s_type, rbr = 0, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
                except TypeError: return
        if plot:
            for r in row:
                for p in pixel:
                    self.I2C.pixel_write("TrimDAC",r,p,data_array[(r-1)*120+p])
            try: scurve_final = self.s_curve(n_pulse = n_pulse,  s_type = s_type, rbr = 0, ref_val = ref_val, row = row, step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
            except TypeError: return
            plt.figure(1)
            th_array, noise_array = self.plot_extract_scurve(row = row, pixel = list(range(2,120)),s_type = s_type, scurve = scurve , n_pulse = n_pulse, nominal_DAC = nominal_DAC, start = start, stop = stop, plot = 1, extract = 1)
            t1 = time.time()
            print("END")
            print("Trimming Elapsed Time: " + str(t1 - t0))
            plt.show()
            return data_array, th_array, noise_array, pix_out
        return data_array, pix_out

    def trimming_chip(self, s_type = "THR", ref_val = 10, nominal_DAC = 110, nstep = 4, data_array = np.zeros(2040, dtype = np.int ), n_pulse = 300, iteration = 2, extract = 1, plot = 1, stop = 256, ratio = 3.68, print_file = 0, filename = "../cernbox/MPA_Results/Test"):
        """

        :param s_type:  (Default value = "THR")
        :param ref_val:  (Default value = 10)
        :param nominal_DAC:  (Default value = 110)
        :param nstep:  (Default value = 4)
        :param data_array:  (Default value = np.zeros(2040)
        :param dtype:  (Default value = np.int ))
        :param n_pulse:  (Default value = 300)
        :param iteration:  (Default value = 2)
        :param extract:  (Default value = 1)
        :param plot:  (Default value = 1)
        :param stop:  (Default value = 256)
        :param ratio:  (Default value = 3.68)
        :param print_file:  (Default value = 0)
        :param filename:  (Default value = "../cernbox/MPA_Results/Test")

        """
        t0 = time.time()
        pix_out = [["Row", "Pixel", "DAC"]]
        for i in range(1,nstep+1):
            self.I2C.pixel_write("TrimDAC",0,0,0)
            row = list(range(i, 17, nstep))
            print("Doing Rows: ", row)
            data_array, pix_out = self.trimming_step(pix_out = pix_out, n_pulse = n_pulse, s_type = s_type, ref_val = ref_val, iteration = iteration, nominal_DAC = nominal_DAC, data_array = data_array, plot = 0, stop = stop, ratio = ratio, row = row)
        self.mpa.ctrl_pix.load_trim(data_array)
        if print_file:
            CSV.ArrayToCSV (data_array, str(filename) + "_ScCal" + ".csv")
        if extract:
            scurve = self.s_curve(n_pulse = n_pulse,  s_type = s_type, rbr = 0, ref_val = ref_val, row = list(range(1,17)), step = 1, start = 0, stop = stop, pulse_delay = 200, extract = 0, plot = 0, print_file =0)
            th_array, noise_array = self.plot_extract_scurve(row = list(range(1,17)), pixel = list(range(2,120)), s_type = s_type, scurve = scurve , n_pulse = n_pulse, nominal_DAC = nominal_DAC, start = 0, stop = stop, plot = plot, extract = 1)
            print("Pixel not trimmerable: " ,np.size(pix_out)/3-1)
            t1 = time.time()
            print("END")
            print("Trimming Elapsed Time: " + str(t1 - t0))
            plt.show()
            if print_file:
                CSV.ArrayToCSV (data_array, str(filename) + "_trimVal" + ".csv")
                CSV.ArrayToCSV (scurve, str(filename) + "_scurve" + ".csv")
                CSV.ArrayToCSV (th_array, str(filename) + "_th_array" + ".csv")
                CSV.ArrayToCSV (noise_array, str(filename) + "_noise_array" + ".csv")
                CSV.ArrayToCSV (pix_out, str(filename) + "_pix_out" + ".csv")
            return data_array, th_array, noise_array, pix_out
        t1 = time.time()
        print("END")
        print("Trimming Elapsed Time: " + str(t1 - t0))
        return data_array, pix_out
# scurve, th, noise, trim, count = cal.trimming_new()
    def trimming_new(self, ref = 40, low = 80, req = 130, high = 180, nominal_ref = 15, nominal_req = 85 , trim_ampl = -1, rbr = 0, plot = 1):
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
        t0 = time.time()
        if trim_ampl > -1:
            for block in range(0,7):
                self.I2C.peri_write("C"+str(block), trim_ampl)
        else: trim_ampl = int(self.I2C.peri_read("C"+str(0)))
        trm_LSB = round(((0.172-0.048)/32.0*trim_ampl+0.048)/32.0*1000.0,2)
        print("Trimming LSB", trm_LSB, "mV")
        print("Trimming DAC MIN scurve...")
        self.mpa.ctrl_pix.reset_trim(0)
        scurveL, thL, noiseL = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = low, extract = 1, plot = 0, print_file =0 )
        print("Trimming DAC MAX scurve...")
        self.mpa.ctrl_pix.reset_trim(31)
        scurveH, thH, noiseH = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = high, extract = 1, plot = 0, print_file =0 )
        thL = np.array(thL); thH = np.array(thH);
        print("Not Trimmerable Pixel", np.size(np.where(thL > req)) + np.size(np.where(thH < req)))
        trim = np.round((req - thL*1.0)/(thH - thL)*32.0)
        trim = trim.astype(int)
        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            print("Trimmed scurve...")
            print("Not Trimmerable Pixel", count)
            scurveT, thT, noiseT = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = 0, print_file =0 )
        else:
            print("Error")
        # Incremental second step?
        thT = np.array(thT);
        trim_incr = np.round((nominal_req - thT)/trm_LSB)
        trim_incr = trim_incr.astype(int)
        trim = trim + trim_incr
        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            print("Nominal scurve...")
            print("Not Trimmerable Pixel", count)
            scurve, th, noise = self.s_curve( n_pulse = 1000, s_type = "THR", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 256, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = plot, print_file =0 )
        else:
            print("Error")
        t1 = time.time()
        print("Trimming Elapsed Time: " + str(t1 - t0))
        return scurve, th, noise, trim, count

    # scurve, th, noise, trim, count = cal.trimming_new()
    def trimming_probe(self, ref = 250, low = 120, req = 90, high = 60, second_step = 1, nominal_ref = 150, nominal_req = 40, trim_ampl = -1, rbr = 0, plot = 1):
        """

        :param ref:  (Default value = 250)
        :param low:  (Default value = 120)
        :param req:  (Default value = 90)
        :param high:  (Default value = 60)
        :param second_step:  (Default value = 1)
        :param nominal_ref:  (Default value = 150)
        :param nominal_req:  (Default value = 40)
        :param trim_ampl:  (Default value = -1)
        :param rbr:  (Default value = 0)
        :param plot:  (Default value = 1)

        """
        t0 = time.time()
        self.I2C.peri_write('Mask', 0b11111111)
        self.I2C.row_write('Mask', 0, 0b11111111)
        if trim_ampl > -1:
            for block in range(0,7):
                self.I2C.peri_write("C"+str(block), trim_ampl)
        else: trim_ampl = int(self.I2C.peri_read("C"+str(0)))

        trm_LSB = round(((0.172-0.048)/32.0*trim_ampl+0.048)/32.0*1000.0,2)
        utils.print_info(f"->  Trimming LSB {trm_LSB} mV, code: {trim_ampl}")

        utils.print_info("->  Trimming DAC MIN scurve...")
        self.mpa.ctrl_pix.reset_trim(0)
        scurveL, thL, noiseL = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 200, pulse_delay = 500, extract_val = low, extract = 1, plot = plot, print_file =0 )
        
        utils.print_info("->  Trimming DAC MAX scurve...")
        self.mpa.ctrl_pix.reset_trim(31)
        scurveH, thH, noiseH = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = ref, row = list(range(1,17)), step = 1, start = 0, stop = 150, pulse_delay = 500, extract_val = high, extract = 1, plot = plot, print_file =0 )
        thL = np.array(thL); thH = np.array(thH);
        trimLSB =(thH-thL)/32
        trim = np.round((req - thL*1.0)/trimLSB)
        trim = trim.astype(int)

        if np.size(trim) == 1888:
            count = self.mpa.ctrl_pix.load_trim(trim)
            utils.print_info("->  Trimmed scurve...")
            utils.print_info(f"->  Not Trimmerable Pixel {count}")
            scurveT, thT, noiseT = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 100, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = plot, print_file =0 )
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
                scurve, th, noise = self.s_curve( n_pulse = 1000, s_type = "CAL", rbr = rbr, ref_val = nominal_ref, row = list(range(1,17)), step = 1, start = 0, stop = 100, pulse_delay = 500, extract_val = nominal_req, extract = 1, plot = plot, print_file =0 )
            else:
                print("Error")

        t1 = time.time()
        utils.print_log(f"->  Total Trimming Elapsed Time: {str(t1 - t0)}")
        return scurve, th, noise, trim, count
