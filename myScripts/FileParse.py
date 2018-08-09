import re
import pandas as pd
import numpy as np
from myScripts.ArrayToCSV import *

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
