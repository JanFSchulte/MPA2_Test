import numpy as np
import time
import sys
import os
import datetime
import threading

import pickle
test_data_path = "../cernbox_anvesh/MPA_test_data/"

if(sys.version_info[0] < 3):
    print('\n\n\x1b[1;37;41m The MPA-SSA Test bench requires python > 3.5. Compatibility with python 2.8 is not anymore guaranteed. \x1b[0m \n\n')

import tkinter
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.special import erfc
from scipy.special import erf
import matplotlib.cm as cm
from scipy.interpolate import BSpline as interpspline
from multiprocessing import Process
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
#from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from sympy.combinatorics.graycode import GrayCode
from myScripts.mpa_configurations import *

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
    def run(self):
        self._target(*self._args)

class curstate():
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class Utilities:

    def __init__(self):
        self.logfile = False
        self.errorlog = False
        self.generic_parameters = {}
        p = []
        self.conf = conf

    class cl_clustdispl(float):
        def __repr__(self):
            return "{:6.1f}".format(self)

    def rms(self, x, axis=None):
        return np.sqrt(np.mean(x**2, axis=axis))

    def eval_mean_std_rms(self, x):
        data = np.array(x)
        mean = np.mean(data)
        std = np.std(data)
        rms = self.rms(data, None)
        return mean, std, rms

    def set_log_files(self, logfile, errorlog):
        #if(self.logfile):  self.logfile.close()
        #if(self.errorlog): self.errorlog.close()
        self.logfile = logfile
        self.errorlog = errorlog
        fo = open(logfile, "a");  fo.close()
        fo = open(errorlog, "a"); fo.close()

    def close_log_files(self):
        #if(self.logfile): self.logfile.close()
        #if(self.errorlog): self.errorlog.close()
        self.logfile = False
        self.errorlog = False

    def reverse_bit_order(self, n, width = 32):
        b = '{:0{width}b}'.format(n, width=width)
        r = int(b[::-1], 2)
        return r

    def byte2int(self, b3=0, b2=0, b1=0, b0=0):
        return ((b3&0xff)<<24) | ((b2&0xff)<<16) | ((b1&0xff)<<8) | ((b0&0xff)<<0)

    def ShowPercent(self, val , max = 100, message = ""):
        i = int( (float(val)/max) * 100.0) - 1
        row = "\t" + message
        sys.stdout.write("%s\r%d%%" %(row, i + 1))
        sys.stdout.flush()
        #time.sleep(0.001)
        if (i == 99):
            sys.stdout.write('\n')

    def time_delta(self, time_init):
        sec = time.time()-time_init
        ret = str(datetime.timedelta(seconds=int(sec)))
        return ret

    def print_inline(self, message):
        sys.stdout.write("\r{:s}".format(message))

    def linear_fit(self, xdata, ydata):
        par, cov = curve_fit(
            f= f_line,
            xdata = np.array(xdata),
            ydata = np.array(ydata),
            p0 = [0, 0])
        gain = par[0]
        offset = par[1]
        sigma = np.sqrt(np.diag(cov))
        return gain, offset, sigma

    def smuth_plot(self, y, x, par = '', r=10):
        xnew = np.linspace(x[0],x[-1], (len(x)-1)*10+1)
        ynp  = np.transpose(np.array(y))
        dim  = len(ynp.shape)
        if(dim == 1):
            ynew = interpspline(x,y,xnew)
            plt.plot(xnew, ynew, par)
        elif(dim == 2):
            for i in ynp:
                ynew = interpspline(x,i,xnew)
                plt.plot(xnew, ynew, par)
        else:
            return False

    def cl2str(self, clist = [0], flag=[], color_flagged='red', color_others='null'):
        if isinstance(clist, list):
            if len(clist) > 0:
                rstr = '['
                for cl in clist:
                    if(cl in flag):
                        rstr += self.text_color("{:6.1f}".format(cl), color_flagged)
                    else:
                        rstr += self.text_color("{:6.1f}".format(cl), color_others)
                    if(cl == clist[-1]):
                        rstr += ']'
                    else:
                        rstr += ','
                #rstr = str(list(map(self.cl_clustdispl, clist)))
            else:
                rstr = "[      ]"
        else:
            rstr = str("[{:6.1f}]".format(clist))
        return rstr

    def __plot_graph(self, *args):
        plt.show()

    def PltPlot(self, data, show = True):
        plt.plot(data)
        self.p.append( Process(target=self.__plot_graph, args='') )
        self.p[-1].start()

    def PltShow(self):
        self.p.append( Process(target=self.__plot_graph, args='') )
        self.p[-1].start()

    def PltClose(self):
        for i in p:
            i.join()

    # FNAL addition
    def plot_2D_map_list(self, 
                         dataarray = [], 
                         data_label="", 
                         row = [],col = [],
                         nfig=5,hmin=-1,hmax=-1, 
                         plotAverage = True, 
                         identifier="", 
                         xlabel="column", ylabel="row",
                         isChip=True, israw = False, 
                         filename="../Results_MPATesting/plot_2D_map_list", 
                         show_plot=True, 
                         save_plot=True):

        if len(row)==0:
            row = self.conf.rowsnom
        if len(col)==0:
            col = self.conf.colsnom
        if isChip and israw:
            if row == self.conf.rowsnom: row = self.conf.rowsraw
            if col == self.conf.colsnom: col = self.conf.colsraw

        y = np.array([])
        x = np.array([])
        w = np.array([])
        #print type(dataarray)
        #print dataarray
        for c in col:
            for r in row:
                #print (r-1)*120+c
                y = np.append(y,r)
                x = np.append(x,c)
                pixelid = self.conf.pixelidraw(r,c) if israw else self.conf.pixelidnom(r,c)
                w = np.append(w,dataarray[pixelid])
                #y = np.append(y,np.arange(0, 17,1))
                #x = np.append(x,np.repeat(c,17))
        maximum = hmax if hmax >=0 else max(0,np.max(w))
        minimum = hmin if hmin >=0 else max(0,np.min(w))
        if plotAverage:
            minimum = max(0,np.mean(w) - 5*np.std(w))
            maximum = max(0,np.mean(w) + 5*np.std(w))
        #print "y",y
        #print "x",x
        #print "w",w
        if isChip:
            fig = plt.figure(nfig,figsize=(5,7.5))#just an identifier
        else:
            fig = plt.figure(nfig)#just an identifier
        plt.hist2d(x,y,weights=w,bins=(len(col),len(row)),cmin=minimum,cmax=maximum,range=[[col[0], col[-1]+1 ],[row[0], row[-1]+1 ] ] )
        cbar = plt.colorbar()
        cbar.set_label(data_label)
        yl = plt.ylabel(ylabel)
        xl = plt.xlabel(xlabel)
        #zl = plt.clabel(str(data_type))
        plt.text(1,122,identifier)#identifier is for chip ID
        if plotAverage:
            plt.text(10,122,"Average %.2f +/- %.2f" % (np.mean(w), np.std(w)))
        plt.grid()
        if save_plot: plt.savefig(filename+".png")
        if save_plot: plt.savefig(filename+".pdf")
        if show_plot: plt.show()
        if save_plot: plt.close()
        return True
        
    # FNAL addition
    def create_logfile(self,path="../Results_MPATesting/",mapsaid="mpa_test_AssemblyX_ChipY",logfile_prefix="log_"):
        log_filename = path+logfile_prefix+mapsaid+".log"
        if os.path.isfile(log_filename):
            copyfilename = path+"SafetyCopy_"+logfile_prefix+mapsaid+timestamp+".log"
            os.rename(log_filename, copyfilename)
        with open(log_filename,"w") as logfile:
            logfile.write("Start log for "+mapsaid+"\n")
        return log_filename

    # FNAL addition
    def write_to_logfile(self,message,logfilename="",printout=False):
        #print message
        #print logfilename
        #print printout
        if logfilename == "":
            print("logfilename was not specified.")
            return
        if not os.path.isfile(logfilename):
            print("logfile "+logfilename+" does not exist.")
            return
        with open(logfilename,"a+") as logfile:
            if printout: print(message)
            logfile.write(message+"\n")
        return




    def print_enable(self, ctr = True):
        if(ctr):
            sys.stdout = sys.__stdout__
        else:
            sys.stdout = open(os.devnull, "w")

    def activate_I2C_chip(self, fc7_if, pr = ''):
        verbose = (pr == 'debug')
        fc7_if.activate_I2C_chip(verbose=verbose)
        if(pr == 'print' or pr == 'debug'):
            print('->  \tEnabled I2C master for chips control')

    def date_time(self, format='print'):
        if(format == 'print'):
            return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        elif(format == 'csv'):
            return datetime.datetime.now().strftime("%Y, %m, %d, %H, %M, %S")
        elif(format == 'array'):
            return (datetime.datetime.now().strftime("%Y, %m, %d, %H, %M, %S")).split(', ')
        else:
            return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    def date_and_time(self, format='print'):
        if(format == 'print'):
            return (datetime.datetime.now().strftime("%Y-%m-%d,%H-%M-%S")).split(',')
        elif(format == 'csv'):
            return datetime.datetime.now().strftime("%Y, %m, %d, %H, %M, %S")
        elif(format == 'array'):
            return (datetime.datetime.now().strftime("%Y, %m, %d, %H, %M, %S")).split(', ')
        else:
            return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    def print_error(self, text, logfile = False):
        print(self.text_color(text, 'red'))
        if(self.logfile):
            with open(self.logfile, 'a') as fo:
                fo.write(str(text)+"\n")
        if(self.errorlog):
            with open(self.errorlog, 'a') as fo:
                fo.write(str(text)+"\n")

    def print_warning(self, text, logfile = False):
        print(self.text_color(text, 'yellow'))
        if(self.logfile):
            with open(self.logfile, 'a') as fo:
                fo.write(str(text)+"\n")

    def print_info(self, text, logfile = False):
        print(self.text_color(text, 'blue'))
        if(self.logfile):
            with open(self.logfile, 'a') as fo:
                fo.write(str(text)+"\n")

    def print_good(self, text, logfile = False):
        print(self.text_color(text, 'green'))
        if(self.logfile):
            with open(self.logfile, 'a') as fo:
                fo.write(str(text)+"\n")

    def print_log(self, text, logfile = False):
        print(self.text_color(text, 'CITALIC'))
        if(self.logfile):
            with open(self.logfile, 'a') as fo:
                fo.write(str(text)+"\n")

    def print(self, text, mode='log'):
        if  (mode=='log'):     self.print_log(text)
        elif(mode=='warning'): self.print_warning(text)
        elif(mode=='info'):    self.print_info(text)
        elif(mode=='good'):    self.print_good(text)
        elif(mode=='error'):   self.print_error(text)
        else:                  print(text)

    def text_color(self, text, color='none'):
        if(color=='green'):
            return "\033[1;32m" + str(text) + "\033[0;0m"
        elif(color=='yellow'):
            return "\033[1;93m" + str(text) + "\033[0;0m"
        elif(color=='red'):
            return "\033[1;31m" + str(text) + "\033[0;0m"
        elif(color=='blue'):
            return "\033[1;34m" + str(text) + "\033[0;0m"
        elif(color=='grey'):
            return "\033[1;34m" + str(text) + "\033[0;0m"
        elif(color=='HEADER'):
            return '\033[95m' + str(text) + "\033[0;0m"
        elif(color=='OKBLUE'):
            return '\033[94m' + str(text) + "\033[0;0m"
        elif(color=='OKGREEN'):
            return '\033[92m' + str(text) + "\033[0;0m"
        elif(color=='WARNING'):
            return '\033[93m' + str(text) + "\033[0;0m"
        elif(color=='FAIL'):
            return '\033[91m' + str(text) + "\033[0;0m"
        elif(color=='BOLD'):
            return '\033[1m'  + str(text) + "\033[0;0m"
        elif(color=='UNDERLINE'):
            return '\033[4m'  + str(text) + "\033[0;0m"
        elif(color=='CITALIC'):
            return '\33[3m'  + str(text) + "\033[0;0m"
        else:
            return str(text)

    def print_log_color_legend(self, text):
        sys.stdout.write('Color legend: ')
        sys.stdout.write("\033[1;31m")
        sys.stdout.write('error  ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write("\033[1;33m")
        sys.stdout.write('warning  ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write("\033[1;34m")
        sys.stdout.write('info  ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write("\033[1;32m")
        sys.stdout.write('good  ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write(text+'normal\n')

    def print_log_color_legend_i2c(self, text):
        sys.stdout.write('Color legend: ')
        sys.stdout.write("\033[1;31m")
        sys.stdout.write('(no reply) ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write("\033[1;33m")
        sys.stdout.write('(reply but wrong data) ')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write("\033[1;32m")
        sys.stdout.write('(correct result)')
        sys.stdout.write("\033[0;0m")
        sys.stdout.write(text)

    def gray_code(self, value):
        if  (value==0):  val = 0b0000
        elif(value==1):  val = 0b0001
        elif(value==2):  val = 0b0011
        elif(value==3):  val = 0b0010
        elif(value==4):  val = 0b0110
        elif(value==5):  val = 0b0111
        elif(value==6):  val = 0b0101
        elif(value==7):  val = 0b0100
        elif(value==8):  val = 0b1100
        elif(value==9):  val = 0b1101
        elif(value==10): val = 0b1111
        elif(value==11): val = 0b1110
        elif(value==12): val = 0b1010
        elif(value==13): val = 0b1011
        elif(value==14): val = 0b1001
        elif(value==15): val = 0b1000
        return val

def print_method(name):
    lines = inspect.getsourcelines(name)
    print("".join(lines[0]))

utils = Utilities()


def f_errorf(x, *p):
    a, mu, sigma = p
    #    print(x)
    return 0.5*a*(1.0+erf((x-mu)/sigma))

def f_line(x, *p):
    g, offset = p
    return  np.array(x) *g + offset

def f_gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def f_gauss1(x, A, mu, sigma):
    '''1-d gaussian: gaussian(x, A, mu, sigma)'''
    return A * np.exp(-(x-mu)**2 / (2.*sigma**2))

def f_errorfc(x, *p):
    a, mu, sigma = p
    return a*0.5*erfc((x-mu)/(sigma*np.sqrt(2)))

def f_weibull_cumulative(x, *p):
    s0, s, E0, W = p
    return s0*(1-np.exp( (-1)*(((x-E0)/W)**s) ))

def f_weibull_cumulative1(x, s0, s, E0, W):
    return np.double(s0)*(1-np.exp( (-1)*(((np.double(x)-np.double(E0))/np.double(W))**np.double(s)) ))

def save_data(data , title):
    pickle.dump(data, open(f"{test_data_path}{title}.pickle","wb"))

def try_fc7_com(fc7_if):
    for i in range(4):
        fc7_if.write("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq", i)
        time.sleep(0.001)
        r = fc7_if.read("fc7_daq_cnfg.mpa_ssa_board_block.i2c_freq")
        time.sleep(0.001)
        if(r == i): st = 'Pass'
        else: st = 'Fail'
        print('{:s}: {:d}-{:d}'.format(st, i, r))
