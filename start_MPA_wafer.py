#execfile('start_MPA_wafer.py')
from myScripts.wafer_probe_ctrl import *
AP = AUTOPROBER(wafer='N2XM21_21E0', name = 'Chip_N')
AP.MSR_ALL()
