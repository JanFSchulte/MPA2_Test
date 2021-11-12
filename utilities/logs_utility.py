from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.logs_utility import *
from collections import OrderedDict
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt


class results():

    class logpar():
        def __init__(self, name, value, unit = '', descr = '', run = ''):
            self.name = name
            self.unit = unit
            self.value = value
            self.descr = descr
            self.run = run

    def __init__(self):
        self.d = OrderedDict()
        self.summary = ["", "", "", ""]
        #self.clean()

    def set(self, name, value, unit = '', descr = '', run = 'Run-0'):
        self.d[name] = self.logpar(name, value, unit, descr, run)

    def update(self, runname = 'Run-0'):
        self.summary[0] = '\n%s, %s, %s, %s, %s\n'  % ('RunName', 'Test', 'Results', 'Unit', 'Description' )
        self.summary[1] = '\n%32s   %12s %4s %24s\n'  % ('Test', 'Results', 'Unit', '' )
        self.summary[2] = ''
        for i in self.d:
            if (isinstance(self.d[i].value, bool)):
                temp = 'True' if self.d[i].value else 'False'
            elif( isinstance(self.d[i].value, int) or isinstance(self.d[i].value, float)):
                temp = '%8.3f' % (self.d[i].value)
            elif( isinstance(self.d[i].value, str)):
                temp = self.d[i].value
            elif( isinstance(self.d[i].value, np.ndarray) or isinstance(self.d[i].value, list)):
                temp = str(self.d[i].value)
            else:
                temp = 'conversion error'
            self.summary[0] += '%s, %s, %s, %s, %s\n'  % (self.d[i].run,   self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)
            self.summary[1] += '%32s : %12s %4s %24s\n'  % (self.d[i].name,   temp,  self.d[i].unit,  self.d[i].descr)
            self.summary[2] += '%32s, ' % (temp)
            self.summary[3] += '%32s, ' % (i)
        self.summary[2] += '\n'
        self.summary[3] += '\n'

    def display(self, runname = 'Run-0'):
        utils.print_info("\n___________________________________________________")
        utils.print_info("Test summary:")
        self.update(runname = runname)
        utils.print_log(self.summary[1])

    def save(self, directory='../SSA_Results/Chip0/', filename='default', runname='', write_header=False):
        utils.print_info("\n___________________________________________________")
        utils.print_info("Saving summary:")
        self.update(runname = runname)
        fn = (directory+'/'+self.get_file_name(filename)+"Logfile.csv"    )
        fo = open(fn, 'w');  fo.write(self.summary[0]);  fo.close();
        utils.print_log("->  Log saved in {:s}".format(fn))

        fn =  (directory+'/'+self.get_file_name(filename)+"Summary.csv")
        fo = open(fn, 'w');
        fo.write(self.summary[3]);
        fo.write(self.summary[2]);
        fo.close();
        utils.print_log("->  Summary saved in {:s}".format(fn))

        fn = (directory+'/'+"GlobalSummary.csv")
        fo = open( fn, 'a');
        if(write_header):
            fo.write("{:32s}, {:32s},".format('directory', 'runname') + self.summary[3]);
        fo.write("{:32s}, {:32s},".format(filename, runname) + self.summary[2]);
        fo.close();
        utils.print_log("->  Global summary saved in {:s}".format(fn))


    def get_file_name(self, filename):
        if(filename == 'default' or not isinstance(filename, str) ):
            fo = '../SSA_Results/Chip0/' + utils.date_time() + '_'
        else:
            fo = filename
        return fo




class RunTest():

    def __init__(self, configname = 'default'):
        self.test = {}
        self.configname = configname
        if(configname != 'default'):
            print('->  Test Configuration object [' + str(self.configname) + '] created.')

    def enable(self, name):
        self.test[name] = True

    def disable(self, name):
        self.test[name] = False

    def set_enable(self, name, mode):
        if(mode in [0, 'off', 'OFF', 'disable']):
            self.test[name] = False
        elif(mode in [1, 'on', 'ON', 'enable']):
            self.test[name] = True
        else:
            print('Error configuring test-mode set_enable. Configuration not changed.')

    def is_active(self, name, display=True):
        if(not name in self.test):
            return False
        else:
            r = self.test[name]
            if(r and display):
                utils.print_info("\n___________________________________________________")
                utils.print_info("Running test: {:s}\n".format(name))
            return r

    def __del__(self):
        print('->  Test Configuration object [' + str(self.configname) + '] replaced.')
