#execfile('start_mpa_wafer.py')
from myScripts.wafer_probe_ctrl import *
AP = AUTOPROBER(wafer='N6Y215_01', mpa = mpa)

AP.ConnToPS()
AP.MSR_ALL()
