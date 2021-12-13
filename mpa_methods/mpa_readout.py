import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt

from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.tbsettings import *

'''
fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
mpa_l1_data = fc7.blockRead("fc7_daq_stat.physical_interface_block.l1a_debug", 50, 0)
mpa_stub_data = fc7.blockRead("fc7_daq_stat.physical_interface_block.stub_debug", 80, 0)
lateral_data = fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
'''

class MPAReadout():

    def __init__(self, I2C, FC7, ctrl ,ctrl_pix):
        self.ctrl = ctrl
        self.I2C = I2C;	self.fc7 = FC7; self.ctrl_pix = ctrl_pix;

    def status(self, display=True):
        """
        :param display:  (Default value = True)
        """
        status = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
        l1_data_ready   = ((status & 0x1) >> 0)
        stub_data_ready = ((status & 0x2) >> 1)
        counters_ready  = ((status & 0x4) >> 2)
        if(display):
            utils.print_log('->  L1 data ready:   {:d}'.format(l1_data_ready))
            utils.print_log('->  Stub data ready: {:d}'.format(stub_data_ready))
            utils.print_log('->  Counters ready:  {:d}'.format(counters_ready))
        return [l1_data_ready, stub_data_ready, counters_ready]

    def read_regs(self, verbose =  1 ):
        status = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
        mpa_l1_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.l1a_debug", 50, 0)
        mpa_stub_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.stub_debug", 80, 0)
        if verbose:
            print("--> Status: ")
            print("---> MPA L1 Data Ready: " +str((status & 0x00000001) >> 0))
            print("---> MPA Stub Data Ready: " +str((status & 0x00000002) >> 1))
            print("---> MPA Counters Ready: " +str((status & 0x00000004) >> 2))

            print("\n--> L1 Data: ")
            print("--->")
            for word in mpa_l1_data:
                #print("--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8))
                print(
                    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
            print("\n--> Stub Data: ")
            for i, word in enumerate(mpa_stub_data):

                if not i % 10:
                    print(f'\nLine {np.floor(i/10)+1:.0f}:')

                print(
                    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
        return mpa_l1_data, mpa_stub_data

    def read_stubs(self, raw = 0, fast = 0):
        status = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
        mpa_stub_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.stub_debug", 80, 0)
        stubs = np.zeros((5,40), dtype = np.uint8)
        line = 0
        cycle = 0
        for word in mpa_stub_data[0:50]:
            #print("--->", '%10s' % bin(to_number(reverse_mask(word),32,24)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),24,16)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),16,8)).lstrip('-0b').zfill(8), '%10s' % bin(to_number(reverse_mask(word),8,0)).lstrip('-0b').zfill(8))
            for i in range(0,4):
                #stubs[line, cycle] = to_number(reverse_mask(word),32-i*8,24-i*8)
                stubs[line, cycle] = to_number(word,(i+1)*8,i*8)
                #print(bin(stubs[line, cycle]))
                cycle += 1
                if cycle == 40:
                    line += 1
                    cycle = 0
        nst = np.zeros((20,), dtype = np.uint8)
        pos = np.zeros((20,5), dtype = np.uint8)
        row = np.zeros((20,5), dtype = np.uint8)
        cur = np.zeros((20,5), dtype = np.uint8)
        cycle = 0

        if raw:
            return stubs
        elif fast:
            for i in range(0,39):
                if ((stubs[0,i] & 0b10000000) == 128):
                    j = i+1
                    nst[cycle]   = ((stubs[1,i] & 0b10000000) >> 5) | ((stubs[2,i] & 0b10000000) >> 6) | ((stubs[3,i] & 0b10000000) >> 7)
                    pos[cycle,0] = ((stubs[4,i] & 0b10000000) << 0) | ((stubs[0,i] & 0b01000000) << 0) | ((stubs[1,i] & 0b01000000) >> 1) | ((stubs[2,i] & 0b01000000) >> 2) | ((stubs[3,i] & 0b01000000) >> 3) | ((stubs[4,i] & 0b01000000) >> 4) | ((stubs[0,i] & 0b00100000) >> 4) | ((stubs[1,i] & 0b00100000) >> 5)
                    pos[cycle,1] = ((stubs[4,i] & 0b00010000) << 3) | ((stubs[0,i] & 0b00001000) << 3) | ((stubs[1,i] & 0b00001000) << 2) | ((stubs[2,i] & 0b00001000) << 1) | ((stubs[3,i] & 0b00001000) << 0) | ((stubs[4,i] & 0b00001000) >> 1) | ((stubs[0,i] & 0b00000100) >> 1) | ((stubs[1,i] & 0b00000100) >> 2)
                    pos[cycle,2] = ((stubs[4,i] & 0b00000010) << 6) | ((stubs[0,i] & 0b00000001) << 6) | ((stubs[1,i] & 0b00000001) << 5) | ((stubs[2,i] & 0b00000001) << 4) | ((stubs[3,i] & 0b00000001) << 3) | ((stubs[4,i] & 0b00000001) << 3) | ((stubs[1,j] & 0b10000000) >> 6) | ((stubs[2,j] & 0b10000000) >> 7)
                    pos[cycle,3] = ((stubs[0,j] & 0b00100000) << 2) | ((stubs[1,j] & 0b00100000) << 1) | ((stubs[2,j] & 0b00100000) << 0) | ((stubs[3,j] & 0b00100000) >> 1) | ((stubs[4,j] & 0b00100000) >> 2) | ((stubs[0,j] & 0b00010000) >> 2) | ((stubs[1,j] & 0b00010000) >> 3) | ((stubs[2,j] & 0b00010000) >> 4)
                    pos[cycle,4] = ((stubs[0,j] & 0b00000100) << 5) | ((stubs[1,j] & 0b00000100) << 4) | ((stubs[2,j] & 0b00000100) << 3) | ((stubs[3,j] & 0b00000100) << 2) | ((stubs[4,j] & 0b00000100) << 1) | ((stubs[0,j] & 0b00000010) << 1) | ((stubs[1,j] & 0b00000010) << 0) | ((stubs[2,j] & 0b00000010) >> 1)
                    row[cycle,0] = ((stubs[0,i] & 0b00010000) >> 1) | ((stubs[1,i] & 0b00010000) >> 2) | ((stubs[2,i] & 0b00010000) >> 3) | ((stubs[3,i] & 0b00010000) >> 4)
                    row[cycle,1] = ((stubs[0,i] & 0b00000010) << 2) | ((stubs[1,i] & 0b00000010) << 1) | ((stubs[2,i] & 0b00000010) << 0) | ((stubs[3,i] & 0b00000010) >> 1)
                    row[cycle,2] = ((stubs[1,j] & 0b01000000) >> 3) | ((stubs[2,j] & 0b01000000) >> 4) | ((stubs[3,j] & 0b01000000) >> 5) | ((stubs[4,j] & 0b01000000) >> 6)
                    row[cycle,3] = ((stubs[1,j] & 0b00001000) >> 0) | ((stubs[2,j] & 0b00001000) >> 1) | ((stubs[3,j] & 0b00001000) >> 2) | ((stubs[4,j] & 0b00001000) >> 3)
                    row[cycle,4] = ((stubs[1,j] & 0b00000001) << 3) | ((stubs[2,j] & 0b00000001) << 2) | ((stubs[3,j] & 0b00000001) << 1) | ((stubs[4,j] & 0b00000001) << 0)
                    cycle += 1
            return nst,  pos, row, cur
        else:
            for i in range(0,39):
                if ((stubs[0,i] & 0b10000000) == 128):
                    j = i+1
                    nst[cycle]   = ((stubs[1,i] & 0b10000000) >> 5) | ((stubs[2,i] & 0b10000000) >> 6) | ((stubs[3,i] & 0b10000000) >> 7)
                    pos[cycle,0] = ((stubs[4,i] & 0b10000000) << 0) | ((stubs[0,i] & 0b01000000) << 0) | ((stubs[1,i] & 0b01000000) >> 1) | ((stubs[2,i] & 0b01000000) >> 2) | ((stubs[3,i] & 0b01000000) >> 3) | ((stubs[4,i] & 0b01000000) >> 4) | ((stubs[0,i] & 0b00100000) >> 4) | ((stubs[1,i] & 0b00100000) >> 5)
                    pos[cycle,1] = ((stubs[4,i] & 0b00010000) << 3) | ((stubs[0,i] & 0b00001000) << 3) | ((stubs[1,i] & 0b00001000) << 2) | ((stubs[2,i] & 0b00001000) << 1) | ((stubs[3,i] & 0b00001000) << 0) | ((stubs[4,i] & 0b00001000) >> 1) | ((stubs[0,i] & 0b00000100) >> 1) | ((stubs[1,i] & 0b00000100) >> 2)
                    pos[cycle,2] = ((stubs[4,i] & 0b00000010) << 6) | ((stubs[0,i] & 0b00000001) << 6) | ((stubs[1,i] & 0b00000001) << 5) | ((stubs[2,i] & 0b00000001) << 4) | ((stubs[3,i] & 0b00000001) << 3) | ((stubs[4,i] & 0b00000001) << 3) | ((stubs[1,j] & 0b10000000) >> 6) | ((stubs[2,j] & 0b10000000) >> 7)
                    pos[cycle,3] = ((stubs[0,j] & 0b00100000) << 2) | ((stubs[1,j] & 0b00100000) << 1) | ((stubs[2,j] & 0b00100000) << 0) | ((stubs[3,j] & 0b00100000) >> 1) | ((stubs[4,j] & 0b00100000) >> 2) | ((stubs[0,j] & 0b00010000) >> 2) | ((stubs[1,j] & 0b00010000) >> 3) | ((stubs[2,j] & 0b00010000) >> 4)
                    pos[cycle,4] = ((stubs[0,j] & 0b00000100) << 5) | ((stubs[1,j] & 0b00000100) << 4) | ((stubs[2,j] & 0b00000100) << 3) | ((stubs[3,j] & 0b00000100) << 2) | ((stubs[4,j] & 0b00000100) << 1) | ((stubs[0,j] & 0b00000010) << 1) | ((stubs[1,j] & 0b00000010) << 0) | ((stubs[2,j] & 0b00000010) >> 1)
                    row[cycle,0] = ((stubs[0,i] & 0b00010000) >> 1) | ((stubs[1,i] & 0b00010000) >> 2) | ((stubs[2,i] & 0b00010000) >> 3) | ((stubs[3,i] & 0b00010000) >> 4)
                    row[cycle,1] = ((stubs[0,i] & 0b00000010) << 2) | ((stubs[1,i] & 0b00000010) << 1) | ((stubs[2,i] & 0b00000010) << 0) | ((stubs[3,i] & 0b00000010) >> 1)
                    row[cycle,2] = ((stubs[1,j] & 0b01000000) >> 3) | ((stubs[2,j] & 0b01000000) >> 4) | ((stubs[3,j] & 0b01000000) >> 5) | ((stubs[4,j] & 0b01000000) >> 6)
                    row[cycle,3] = ((stubs[1,j] & 0b00001000) >> 0) | ((stubs[2,j] & 0b00001000) >> 1) | ((stubs[3,j] & 0b00001000) >> 2) | ((stubs[4,j] & 0b00001000) >> 3)
                    row[cycle,4] = ((stubs[1,j] & 0b00000001) << 3) | ((stubs[2,j] & 0b00000001) << 2) | ((stubs[3,j] & 0b00000001) << 1) | ((stubs[4,j] & 0b00000001) << 0)
                    cur[cycle,0] = ((stubs[2,i] & 0b00100000) >> 3) | ((stubs[3,i] & 0b00100000) >> 4) | ((stubs[4,i] & 0b00100000) >> 5)
                    cur[cycle,1] = ((stubs[2,i] & 0b00000100) >> 0) | ((stubs[3,i] & 0b00000100) >> 1) | ((stubs[4,i] & 0b00000100) >> 2)
                    cur[cycle,2] = ((stubs[3,j] & 0b10000000) >> 5) | ((stubs[4,j] & 0b10000000) >> 6) | ((stubs[0,j] & 0b01000000) >> 6)
                    cur[cycle,3] = ((stubs[3,j] & 0b00010000) >> 2) | ((stubs[4,j] & 0b00010000) >> 3) | ((stubs[0,j] & 0b00001000) >> 3)
                    cur[cycle,4] = ((stubs[3,j] & 0b00000010) << 1) | ((stubs[4,j] & 0b00000010) >> 0) | ((stubs[0,j] & 0b00000001) >> 0)
                    cycle += 1
        return nst,  pos, row, cur

    def read_L1(self, verbose = 1):
        status = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
        mpa_l1_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.l1a_debug", 50, 0)
        l1 = np.zeros((200,), dtype = np.uint8)
        cycle = 0
        for word in mpa_l1_data:
            for i in range(0,4):
                l1[cycle] = to_number(word,(i+1)*8,i*8)
                cycle += 1
        found = 0
        for i in range(1,200):
            if ((l1[i] == 255)&(l1[i-1] == 255)&(~found)):
                if verbose:
                    print("Header found at BX:")
                    print(i)
                header = l1[i-1] << 11 | l1[i-1] << 3 | ((l1[i+1] & 0b11100000) >> 5)
                error = ((l1[i+1] & 0b00011000) >> 3)
                L1_ID = ((l1[i+1] & 0b00000111) << 6) | ((l1[i+2] & 0b11111100) >> 2)
                strip_counter = ((l1[i+2] & 0b00000001) << 4) | ((l1[i+3] & 0b11110000) >> 4)
                pixel_counter = ((l1[i+3] & 0b00001111) << 1) | ((l1[i+4] & 0b10000000) >> 7)
                pos_strip = ((l1[i+4] & 0b00111111) << 1) | ((l1[i+5] & 0b10000000) >> 7) # Pos 1
                width_strip = (l1[i+5] & 0b01110000) >> 4
                MIP = (l1[i+5] & 0b00001000) >> 3
                payload = bin(l1[i+4] & 0b00111111).lstrip('-0b').zfill(6)
                for j in range(5,50):
                    payload = payload + bin(l1[i+j]).lstrip('-0b').zfill(8)
                found = 1
                bx = i
        if found:
            strip_data = payload[0:strip_counter*11]
            pixel_data = payload[strip_counter*11: strip_counter*11 + pixel_counter*14]
            strip_cluster = np.zeros((strip_counter,), dtype = np.int)
            pixel_cluster = np.zeros((pixel_counter,), dtype = np.int)
            pos_strip = np.zeros((strip_counter,), dtype = np.int)
            width_strip = np.zeros((strip_counter,), dtype = np.int)
            MIP = np.zeros((strip_counter,), dtype = np.int)
            if verbose:
                print("Header: " + bin(header))
                print("error: " + bin(error))
                print("L1_ID: " + str(L1_ID))
                print("strip_counter: " + str(strip_counter))
                print("pixel_counter: " + str(pixel_counter))
                print("Strip Cluster:")
            for i in range(0, strip_counter):
                try:
                    strip_cluster[i]     =  int(strip_data[11*i:11*(i+1)], 2)
                    pos_strip[i]         = (int(strip_data[11*i:11*(i+1)], 2) & 0b11111110000) >> 4
                    width_strip[i]         = (int(strip_data[11*i:11*(i+1)], 2) & 0b00000001110) >> 1
                    MIP[i]                 = (int(strip_data[11*i:11*(i+1)], 2) & 0b00000000001)
                except ValueError:
                    print("\nParsing problem - Strip")
                    print("Header: " + bin(header))
                    print("error: " + bin(error))
                    print("L1_ID: " + str(L1_ID))
                    print("strip_counter: " + str(strip_counter))
                    print("pixel_counter: " + str(pixel_counter))
                if verbose: print("Position: " + str(pos_strip[i]) + " Width: " + str(width_strip[i]) + " MIP: " + str(MIP[i]))
            if verbose: print("Pixel Cluster:")
            pos_pixel = np.zeros((pixel_counter,), dtype = np.int)
            width_pixel = np.zeros((pixel_counter,), dtype = np.int)
            Z = np.zeros((pixel_counter,), dtype = np.int)
            for i in range(0, pixel_counter):
                try:
                    pixel_cluster[i] = int(pixel_data[14*i:14*(i+1)], 2)
                    pos_pixel[i]     = (int(pixel_data[14*i:14*(i+1)], 2) & 0b11111110000000) >> 7
                    width_pixel[i]     = (int(pixel_data[14*i:14*(i+1)], 2) & 0b00000001110000) >> 4
                    Z[i]             = (int(pixel_data[14*i:14*(i+1)], 2) & 0b00000000001111) + 1
                except ValueError:
                    print("\nParsing problem - Pixel")
                    print("Header: " + bin(header))
                    print("error: " + bin(error))
                    print("L1_ID: " + str(L1_ID))
                    print("strip_counter: " + str(strip_counter))
                    print("pixel_counter: " + str(pixel_counter))
                if verbose: print("Position: " + str(pos_pixel[i]) + " Width: " + str(width_pixel[i]) + " Row Number: " + str(Z[i]))
            return strip_counter, pixel_counter, pos_strip, width_strip, MIP, pos_pixel, width_pixel, Z, bx, L1_ID
        else:
            print("Header not found!")

    def counters_fast(self, striplist = range(1,121), raw_mode_en = 0, shift = 'auto', initialize = True, silent=0):
        """

        :param striplist:  (Default value = range(1)
        :param 121):
        :param raw_mode_en:  (Default value = 0)
        :param shift:  (Default value = 'auto')
        :param initialize:  (Default value = True)
        :param silent:  (Default value = 0)

        """
        #t = time.time()
        if(initialize):
            self.ctrl.setup_readout_chip_id()
            self.fc7.write("fc7_daq_cnfg.physical_interface_block.ps_counters_raw_en", raw_mode_en)# set the raw mode to the firmware
            #self.I2C.peri_write('AsyncRead_StartDel_LSB', (11 + shift) )
        if(isinstance(shift, int) and (shift != self.countershift['value'])):
            self.ctrl.set_async_readout_start_delay(delay=8, fc7_correction=shift)
            self.countershift['state'] = True
            self.countershift['value'] = shift
            if(not silent): utils.print_log('->  Updating the counters alignment value to {:d}'.format(shift))
        else:
            if(self.countershift['state']):
                self.ctrl.set_async_readout_start_delay(delay=8, fc7_correction=self.countershift['value'])
            else:
                self.align_counters_readout()
        mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
        #self.I2C.peri_write('AsyncRead_StartDel_LSB', (8) )
        self.fc7.start_counters_read(1)
        timeout = 0
        failed = False
        while ((mpa_counters_ready == 0) & (timeout < 100)):
            #### time.sleep(0.01)
            timeout += 1
            mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
            time.sleep(0.001)
        if(timeout >= 50):
            failed = True;
            return failed, -1
        if raw_mode_en == 0:
            count = self.fc7.fifoRead("fc7_daq_ctrl.physical_interface_block.fifo2_data", 120)
            if(tbconfig.VERSION['SSA'] == 1):
                if(119 in striplist): ## BUG IN SSA CHIP (STRIP 120 COUNTER READABLE ONLY VIA I2C) FIXED in SSAv2
                    count[119] = (self.I2C.strip_read("ReadCounter_MSB",120) << 8) | self.I2C.strip_read("ReadCounter_LSB",120)
        else:
            count = np.zeros((20000, ), dtype = np.uint16)
            for i in range(0,20000):
                fifo1_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.fifo1_data")
                fifo2_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.fifo2_data")
                line1 = to_number(fifo1_word,8,0)
                line2 = to_number(fifo1_word,16,8)
                count[i] = (line2 << 8) | line1
                if (i%1000 == 0): utils.print_log("Reading BX #" + str(i))
        #### time.sleep(0.1)
        #### mpa_counters_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug.ps_counters_ready")
        for s in range(0,120):
            if (not (s+1) in striplist):
                count[s] = 0
        #utils.print_log((time.time()-t)*1E3)
        return failed, count

    def align_counters_readout(self, threshold=50, amplitude=150, duration=1):
        """

        :param threshold:  (Default value = 50)
        :param amplitude:  (Default value = 150)
        :param duration:  (Default value = 1)

        """
        utils.print_log('->  Running counters readout alignment procedure')
        self.fc7.SendCommand_CTRL("stop_trigger")
        self.cluster_data(initialize=True)
        self.ctrl.activate_readout_async(ssa_first_counter_delay='keep')
        time.sleep(0.001)
        Configure_TestPulse_SSA(50,50,500,1000,0,0,0)
        self.strip.set_cal_strips(mode = 'counter', strip = 'all')
        self.ctrl.set_cal_pulse(amplitude=amplitude, duration=duration, delay='keep')
        self.ctrl.set_threshold(threshold);  # set the threshold
        self.fc7.clear_counters(1)
        self.fc7.open_shutter(1, 1)
        self.fc7.SendCommand_CTRL("start_trigger")
        time.sleep(0.1)
        self.fc7.close_shutter(1,1)
        successfull = False
        for countershift in range(-5,5):
            failed, counters = self.counters_fast(range(1,121), shift = countershift, initialize = 1, silent=True)
            mean = np.mean(counters)
            print('->  ' + str([countershift, mean]))
            if((not failed) and (mean>990) and (mean<1100)):
                successfull = True
                break
        self.countershift['state'] = True
        self.countershift['value'] = countershift
        return [successfull, countershift, mean]


    def counters_via_i2c(self, striplist = range(1,120)):
        """

        :param striplist:  (Default value = range(1)
        :param 120):

        """
        count = [0]*120
        for s in striplist:
            if(tbconfig.VERSION['SSA'] >= 2):
                rmsb  = self.I2C.strip_read(register="AC_ReadCounterMSB", field=False, strip=s)
                rlsb  = self.I2C.strip_read(register="AC_ReadCounterLSB", field=False, strip=s)
                count[s-1] = ((rmsb << 8) | rlsb)
            else:
                count[s-1] = (self.I2C.strip_read("ReadCounter_MSB", s) << 8) | self.I2C.strip_read("ReadCounter_LSB", s)
        return False, count

    def all_lines_debug(self, trigger = True, configure = True, cluster = True, l1data = True, lateral = False, configuration=[199, 50, 400, 1]):
        """

        :param trigger:  (Default value = True)
        :param configure:  (Default value = True)
        :param cluster:  (Default value = True)
        :param l1data:  (Default value = True)
        :param lateral:  (Default value = False)

        """
        if(configure):
            self.ctrl.setup_readout_chip_id()
            self.fc7.SendCommand_CTRL("fast_test_pulse")
            self.fc7.SendCommand_CTRL("fast_trigger")
            self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", 0)
            self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse", 1)
            self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a", 0)
            Configure_TestPulse(configuration[0],configuration[1],configuration[2], configuration[3])

            #Configure_TestPulse_SSA(    number_of_test_pulses = 1, delay_before_next_pulse = 500, delay_after_test_pulse = 0, delay_after_fast_reset = 0, enable_rst_L1 = 0)

            time.sleep(0.001)
        if(trigger):
            self.fc7.SendCommand_CTRL("start_trigger")
            time.sleep(0.001)
        status = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_debug")
        ssa_l1_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.l1a_debug", 50, 0)
        ssa_stub_data = self.fc7.blockRead("fc7_daq_stat.physical_interface_block.stub_debug", 80, 0)
        lateral_data = self.fc7.blockRead("stat_slvs_debug_lateral_0", 20, 0)
        utils.print_log("--> Status: ")
        utils.print_log("---> MPA L1 Data Ready: " + str((status & 0x00000001) >> 0))
        utils.print_log("---> MPA Stub Data Ready: " + str((status & 0x00000002) >> 1))
        utils.print_log("---> MPA Counters Ready: " +str((status & 0x00000004) >> 2))
        utils.print_log("---> Lateral Data Counters Ready: "  + str((status & 0x00000008) >> 3))
        if(l1data):
            utils.print_log("\n--> L1 Data: ")
            for word in ssa_l1_data:
                utils.print_log(
                    '    \t->' +
                    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
        if(cluster):
            counter = 0
            utils.print_log("\n--> Stub Data: ")
            for word in ssa_stub_data:
                if (counter % 10 == 0):
                    utils.print_log("Line: " + str(counter/10))
                utils.print_log(
                    '    \t->' +
                    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
                counter += 1
        if(lateral):
            utils.print_log("\n--> Lateral Data: ")
            for word in lateral_data:
                utils.print_log(
                    '    \t->' +
                    '{:10s}'.format( bin(to_number(word, 8, 0)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,16, 8)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,24,16)).lstrip('-0b').zfill(8) ) +
                    '{:10s}'.format( bin(to_number(word,32,24)).lstrip('-0b').zfill(8) ) )
    def reverse_mask(x):
        #x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
        #x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
        #x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
        #x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
        #x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
        return x

    def __apply_offset_correction(self, val, enable = True):
        if(not enable):
            if(tbconfig.VERSION['SSA'] >= 2):
                cr = val - 3.5
            else:
                cr = val - 3.0
        else:
            if(not self.ofs_initialised):
                self.ofs[0] = self.I2C.peri_read('Offset0')
                self.ofs[1] = self.I2C.peri_read('Offset1')
                self.ofs[2] = self.I2C.peri_read('Offset2')
                self.ofs[3] = self.I2C.peri_read('Offset3')
                self.ofs[4] = self.I2C.peri_read('Offset4')
                self.ofs[5] = self.I2C.peri_read('Offset5')
                self.ofs_initialised = True
            ## TO BE IMPLEMENTED
            cr = val - 3
            ## TO BE IMPLEMENTED
        return cr


#	def alignment_slvs(align_word = 128, step = 10):
#	    t0 = time.time()
#	    utils. activate_I2C_chip(self.fc7)
#	    I2C.peri_write('LFSR_data', align_word)
#	    activate_shift()
#	    phase = 0
#	    fc7.write("ctrl_phy_fast_cmd_phase",phase)
#	    aligned = 0
#	    count = 0
#	    while ((not aligned) or (count <= (168/step))):
#	        send_test()
#	        send_trigger()
#	        array_stubs = read_stubs(1)
#	        array_l1 = read_L1()
#	        aligned = 1
#	        for word in array_stubs[:,0]: # CHheck stub lines alignment
#	            if (word != align_word):
#	                aligned = 0
#	        if (array_l1[0,0] != align_word): # CHheck L1 lines alignment
#	            aligned = 0
#	        if (not aligned): # if not alignment change phase with T1
#	            phase += step
#	            fc7.write("ctrl_phy_fast_cmd_phase",phase)
#	        count += 1
#	    if (not aligned):
#	        utils.print_log("Try with finer step")
#	    else:
#	        utils.print_log("All stubs line aligned!")
#	    t1 = time.time()
#	    utils.print_log("Elapsed Time: " + str(t1 - t0))
