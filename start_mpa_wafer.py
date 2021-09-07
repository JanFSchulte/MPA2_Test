#execfile('start_mpa_wafer.py')
from myScripts.wafer_probe_ctrl import *
AP = AUTOPROBER(wafer='N6Y215_06', name = 'Chip_N', mpa = mpa.chip, i2c = mpa.i2c, fc7 = FC7, cal = mpa.cal, test = mpa.test, bias = mpa.bias)
AP.ConnToPS()
AP.MSR_ALL()
