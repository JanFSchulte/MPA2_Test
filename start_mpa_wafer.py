#execfile('start_mpa_wafer.py')
from myScripts.wafer_probe_ctrl import *
AP = AUTOPROBER(wafer='N6Y215_05', mpa = True, mode = "scanchain")

AP.ConnToPS()
AP.MSR_ALL()
