
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from main import *

import seaborn as sns
import pickle
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class MPATestDataChain():
    """Procedures class to test and characterize MPA FIFO behaviour."""
    def __init__(self, mpa, I2C, fc7):
        self.mpa = mpa
        self.i2c = I2C
        self.fc7 = fc7

    def l1_bx_delay(self, ntests, print_log = 0, scan = 0):
        #self.mpa.init()
        if print_log: utils.set_log_files("l1_delay.log", "l1_delay_error.log")
        t0 = time.time()
        time.sleep(0.01)
        exp = 188
        r_size = 5
        record = np.array([np.full(r_size, exp),np.zeros(r_size)])
        utils.print_info("-> Running L1 Delay Test...")
        test_pass =1
        rate_fail = 0
        for i in range(1,ntests+1):
            print(f"Loop {i}", end='\r')
            if (i%500 == 0):
                # Reset L1 ID every 500, since it's size is 9 bit
                #time.sleep(0.01)
                self.fc7.send_resync()
            if not record[0,2] == exp:
                # if middle entry is an error, print record
                utils.print_info(f"\nLoop {i}")
                utils.print_info(f"Error after {round(time.time()-t0, 2)}s")
                utils.print_error(record)
                test_pass = 0
                rate_fail +=1
            delay = random.randint(38,187)
            self.fc7.write("fc7_daq_cnfg.physical_interface_block.slvs_debug.SSA_first_counter_del", delay)
            #time.sleep(0.01)
            self.fc7.send_trigger()
            #time.sleep(0.01)
            try:
                bx, l1_id = self.mpa.rdo.read_L1(verbose=0)[-2:] # returns bx and l1_id
                if (bx + delay == exp):
                    res = exp
                else:
                    res = delay
            except: 
                utils.print_error("Error: Header not found!")
                res = delay
                l1_id = 0
            # record 5 values (2 preceding, 2 following and unexpected bx read)
            record = np.pad(record,((0,0),(0,1)), mode='constant')[:,-r_size:] # essentially shift the record left
            record[:,-1] = res, l1_id # record new entry
        t1 = time.time()
        utils.print_info(f"-> Elapsed Time {t1-t0}s")
        if print_log: utils.close_log_files()
        rate_pass= 1-(rate_fail/ntests)
        return test_pass, rate_pass
        # SSA_first_counter_del | expected BX
        # 188 | 	header not found
        # 187 | 	BX 1
        # 150 | 	BX 38
        # 100 | 	BX 88
        # 50  | 	BX 138
        # 38  | 	BX 150 
        # 37  |     header not found

    def l1_delay_scan(self, n_samples = 10, dvdd_scan = np.linspace(1.0, 0.75, 6), pvdd_scan = np.linspace(1.2, 0.95, 6), verbose =1):
        "Voltage scan along pvdd and dvdd to generate shmoo plot for l1_delay integrity."
        res = np.zeros((len(dvdd_scan),len(pvdd_scan)))
        self.mpa.init(display = 0)
        for y, dvdd in np.ndenumerate(dvdd_scan):
            for x, pvdd in np.ndenumerate(pvdd_scan):
                print(f"p:{pvdd},d:{dvdd} ")
                self.mpa.pwr.set_pvdd(pvdd, chip = "MPA")
                self.mpa.pwr.set_dvdd(dvdd, chip = "MPA")
                res[x,y] = self.l1_bx_delay(10000, print_log = 0)[0]
        self.mpa.pwr.set_dvdd(1)
        self.mpa.pwr.set_pvdd(1.2)

        #for i in range(0, 16):
        #    plt.plot(voltages, res[:,i], label = str(i))
        #plt.title('BIST results')
        #plt.xlabel('Voltage [mV]')
        #plt.ylabel('Success rate')
        #plt.legend()
        #plt.show()
        return res
    
    def gen_SSA_trig_data():
        return True 