#from mpa_methods.set_calibration import *
#send_cal_pulse(127, 150, range(1,2), range(1,5))
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from mpa_methods.mpa_i2c_conf import *

def send_cal_pulse(n_pulse, CalDAC, row, pixel):
    I2C.peri_write('ReadoutMode',0b01)
    for r in row:
        for p in pixel:
            I2C.pixel_write('ENFLAGS', r, p, 0x53)
    I2C.peri_write('CalDAC0',CalDAC)
    I2C.peri_write('CalDAC1',CalDAC)
    I2C.peri_write('CalDAC2',CalDAC)
    I2C.peri_write('CalDAC3',CalDAC)
    I2C.peri_write('CalDAC4',CalDAC)
    I2C.peri_write('CalDAC5',CalDAC)
    I2C.peri_write('CalDAC6',CalDAC)
    sleep(1)
    print "start_test"
    open_shutter()
    for i in range(0, n_pulse):
        sleep(0.001)
        send_test()
    close_shutter()
    #I2C.pixel_read('ReadCounter_LSB',2,2)
