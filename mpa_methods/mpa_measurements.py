from os import fpathconf
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from main import *
#from myScripts.Instruments_Keithley_Sourcemeter_2410_GPIB import Instruments_Keithley_Sourcemeter_2410_GPIB

import seaborn as sns
import pickle
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class MPAMeasurements():
    """ ADC characterizations, additional FE measurements (time walk), power measurements..."""
    def __init__(self, mpa, bias):
        self.mpa = mpa
        self.bias = bias
#        try:
#            self.sourcemeter = Instruments_Keithley_Sourcemeter_2410_GPIB()
#            self.sourcemeter.connect()
#        except Exception as e:
#            self.sourcemeter = False
#            utils.print_error("-> Sourcemeter not accessible!")

    # from SSA methods
    def dnl_inl_histogram_sample(self, runtime=3600, freq=0.1, show=0, directory='../MPA2_Results/adc_measurements/', filename='ADC_samples.csv', continue_on_same_file=1):
        if(continue_on_same_file and os.path.exists(directory+'/'+filename)):
            adchist = CSV.csv_to_array(filename=directory+'/'+filename)[:,1]
        else:
            adchist = np.zeros(2**12+1, dtype=int)
        cnt  = 0; told = 0; wd = 0
        self.ext_pad()
        runtime = round(float(runtime)*freq)/freq #to have n copleate cycles
        #ret = self.ssa.analog.WVF.SetWaveform(func='ramp', freq=freq, offset=-0.1, vpp=1.1)
        #if ret is False: return False
        if(filename == False):
            filename = 'ADC_samples_'+str(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')+'.csv')
        timestart = time.time()
        while ((time.time()-timestart) < runtime):
            wd = 0
            while(wd < 3):
                try:
                    res = int(np.round(self.ext_pad(nsamples=1, reinit_if_error=False)))
                    utils.print_inline('{:8d}'.format(res) )
                    #time.sleep( randint(0,3)*0.0005 )
                    break
                except(KeyboardInterrupt):
                    return('User interrupt')
                except:
                    wd +=1;
                    utils.print_warning('Exception {:d}'.format(wd))
            if res is False: return False
            else: adchist[int(res)]+=1
            cnt+=1
            tcur = time.time()
            if ((tcur-told)>1.1): #update histogram every second
                told = tcur
                utils.print_inline('{:8d} ->  ADC collected {:d} samples'.format(res, cnt))
                #with open(filename, 'w') as fo:
                #	fo.write('{:8d},\n'.format(res))
                CSV.array_to_csv(adchist, filename=directory+'/'+filename)
        #f.close()
        utils.print_log('->  ADC total number of samples taken is '+str(cnt))
        dnlh, inlh = self.dnl_inl_histogram_plot(directory=directory, filename=filename, plot=show)
        return dnlh, inlh, adchist

    def dnl_inl_histogram_plot(self, minc=1, maxc=4095, directory='../SSA_Results/adc_measures/', filename='ADC_samples.csv', plot=True):
        dnlh = np.zeros(4096)
        inlh = np.zeros(4096)
        maxim = 0; inl=0.0;
        adchist = CSV.csv_to_array(directory+'/'+filename)[:,1]
        fo=open("../MPA2_Results//adc_dnl_inl.csv","w")
        stepsize = float(np.sum(adchist[minc:maxc]))/(maxc-minc)
        for i in range(minc,maxc+1):
            dnl = (float(adchist[i])/stepsize)-1.0
            dnlh[i] = dnl
            inl+=dnl
            inlh[i] = inl
            fo.write("{:8d}, {:9.6f}, {:9.6f}, {:9.6f}\n".format(i, dnl, inl, float(adchist[i])) )
        fo.close()

    def adc_linearity(self, pts = 100, init=1):
        if init:
            self.mpa.fc7.activate_I2C_chip()
            self.sourcemeter.config__voltage_source()
            self.sourcemeter.output_enable()
            self.bias.select_block(1,0,1)
        reference = np.linspace(0, 0.850, pts)
        codes = np.zeros(reference.size)
        for idx, ref in enumerate(reference):
            time.sleep(0.01)
            try:
                self.sourcemeter.set_voltage(ref)
                codes[idx] = self.bias.adc_measure()
            except Exception as inst:
                utils.print_error("Ext Pad measurement failed! Retrying")
                self.mpa.fc7.activate_I2C_chip()
                self.sourcemeter.set_voltage(ref)
                codes[idx] = self.bias.adc_measure()
        return codes

    def adc_vs_vref(self, pts = 100):
        self.mpa.fc7.activate_I2C_chip()
        self.sourcemeter.config__voltage_source()
        self.sourcemeter.output_enable()
        self.bias.select_block(1,0,1)
        res = np.zeros((32, pts))
        for dac in range(0,32):
            utils.print_info(f"-> Measuring ADC points for VREF DAC {dac}")
            self.mpa.ctrl_base.set_vref(dac)
            self.bias.select_block(1,0,1)
            res[dac] = self.adc_linearity(pts, init = 0)
        np.save(f"../MPA2_Results/adc_vs_vref_{pts}pts2.npy", res)

    def adc_vs_block(self, pts = 100):
        self.mpa.fc7.activate_I2C_chip()
        self.sourcemeter.config__voltage_source()
        self.sourcemeter.output_enable()
        self.mpa.ctrl_base.set_vref(11)
        res = np.zeros((11, pts))
        for block in range(0,11):
            self.bias.select_block(block,0,1)
            utils.print_info(f"-> Measuring ADC points for test block {block}")
            res[block] = self.adc_linearity(pts, init = 0)
        np.save(f"../MPA2_Results/adc_vs_block_{pts}pts.npy", res)

    def ext_pad(self):
        self.bias.select_block(1,0,0)
        val = self.bias.adc_measure()
        return val

    def adc_measure_all(self, DIR=0):
        data_bias_blocks = np.zeros((7, 8), dtype=np.int) # 7 bias blocks, 8 test points
        data_other_blocks = np.zeros((7,), dtype=np.float) # blocks 8 to 14

        self.mpa.ctrl_base.disable_test()
        for block in range(1,8):
            for test_point in range(0,8):
                self.bias.select_block(block, test_point, 0)
                time.sleep(0.01)
                try:
                    data_bias_blocks[block-1, test_point] = self.bias.adc_measure()
                except:
                    utils.print_error(f"-> ADC measurement error: Block {block}, TP {test_point}.")
                    data_bias_blocks[block-1, test_point] = -1000
                
        for block in range(8,15):
            self.bias.select_block(block, 0, 0)
            time.sleep(0.01)
            try:
                data_other_blocks[block-8] = self.bias.adc_measure()
            except:
                utils.print_error(f"-> ADC measurement error: Block {block}.")
                data_other_blocks[block-8] = -1000
        if(DIR):
            np.savetxt(f"{DIR}ADC_bias_blocks.csv", data_bias_blocks, delimiter=",")
            np.savetxt(f"{DIR}ADC_other_blocks.csv", data_other_blocks, delimiter=",")
        return data_bias_blocks, data_other_blocks

    def measure_gnd(self):
        """Measures and returns GND voltage averaged over all seven bias blocks. """
        self.mpa.ctrl_base.disable_test()
        data = np.zeros((7, ), dtype=np.float)
        for block in range(0,7):
            self.select_block(block+1, 7, 1) # 7 to select GND
            data[block] = self.multimeter.measure()
        self.mpa.ctrl_base.disable_test()
        utils.print_info(f"Measured Avg GND:{np.mean(data)}")
        return np.mean(data)
        
