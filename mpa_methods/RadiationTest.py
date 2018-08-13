import csv
import numpy as np
import sys
import os
import random
import time
import ProbeCardTest
from cal_utility import *
from fast_readout_utility import *
from power_utility import *
from fysom import Fysom


def RadTest(total_time = 100, rest_time = 30, filename = "Test/Run_"):

    i = 1
    test_fin = 1
    scurve = 0
    t1 = time.time()
    t4 = time.time()

    def oninit(e):
        print "Initializing"
        activate_I2C_chip()
    	Configure_TestPulse_MPA(delay_after_fast_reset = 10, delay_after_test_pulse = 10, delay_before_next_pulse = 10, number_of_test_pulses = 1000, enable_rst_L1 = 1)



    def ontest(e):
        print "Starting Test"
        start_time = int(time.time())
        print "Time is", start_time
        DIR = str(filename) + str(start_time)
        os.makedirs(DIR)
        TEST = ProbeCardTest.ProbeMeasurement(DIR)
        TEST.Run("MPA 13 Run" + str(i))

    def oninject(e):
        print "Sleeping"
        t2 = time.time()
        t3 = time.time()
        mpa_reset()
        activate_I2C_chip()
        set_calibration(250)
        set_threshold(200)
        activate_pp()
        while t3 - t2 < rest_time and t3 - t1 < total_time:
            #inject randomly
            disable_pixel(0,0)
            print "Injecting the following random pixels:"
            for x in range(1,6):
                r = random.randint(1,16)
                p = random.randint(1,120)
                enable_pix_EdgeBRcal(r,p, polarity = "rise")
                print "Pixel", p, "on row", r
            t5 = time.time()
            while t3 - t5 < 10:
                SendCommand_CTRL("start_trigger")
                t3 = time.time()


    def onend(e):
        print "Time's up. Powering off"
        power_off()


    fsm = Fysom({
      'initial': 'init',
      'events': [
        {'name': 'start',  'src': 'init',  'dst': 'test'},
        {'name': 'sleep',  'src': 'test',  'dst': 'inject'},
        {'name': 'repeat', 'src': 'inject', 'dst': 'test'},
        {'name': 'complete',  'src': ['test', 'inject'],    'dst': 'end'},
      ],
      'callbacks': {
            'oninit': oninit,
            'ontest':  ontest,
            'oninject':   oninject,
            'onend':  onend
        }
    })

    ### Test
    fsm.start()
    while t4 - t1 < total_time:
        if test_fin == 1 and scurve == 0:
            fsm.sleep()
            test_fin = 0
            scurve = 1
            t4 = time.time()
        elif test_fin == 0 and scurve == 1:
            i += 1
            fsm.repeat()
            test_fin = 1
            scurve = 0
            t4 = time.time()
    fsm.complete()
