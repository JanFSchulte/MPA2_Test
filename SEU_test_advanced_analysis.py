
import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import ctypes
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import fnmatch
import re
import traceback
from scipy import stats

from collections import OrderedDict
from functools import reduce
from pandas.core.common import flatten as pandas_flatten
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate
from scipy.optimize import curve_fit
from scipy.special import erfc
from scipy.special import erf
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import exp, loadtxt, pi, sqrt
from lmfit import Model
from itertools import groupby
from operator import itemgetter
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from utilities.tbsettings import *


def Stub_Evaluate_Pattern(strip_list, cluster_cut = 5):

    strip = np.sort(strip_list[0:8])
    slist = np.zeros(8, dtype = ctypes.c_uint32)
    #### Lateral Data
    lateral_left = 0; lateral_right = 0;
    for i in range(np.size(strip)):
        if (strip[i] < 8) and (strip[i] > 0) :
            lateral_left += (0x1 << strip[i])
        elif (strip[i] < 120 and strip[i] >= 112):
            lateral_right += (0x1 << (strip[i]-112))


    #### Clustering
    centroids = []
    strip_list = np.array(strip_list[0:8])
    tmp = enumerate( strip_list[strip_list<=120][strip_list>0] )
    # for k, g in groupby( tmp , lambda (i, x) : i-x):
    for k, g in groupby( tmp , lambda z : z[0]-z[1] ):
        cluster = list(map( itemgetter(1), g))
        size = np.size(cluster)
        center  = np.mean(cluster)
        if(size < cluster_cut):
            centroids.append( center )


    for i in range(np.size(centroids)):
        if((centroids[i] <= 120) and (centroids[i] >= 1)):
            if(tbconfig.VERSION['SSA'] >= 2):
                slist[i] = int(((centroids[i] + 3.5) * 2)) & 0xff
            else:
                slist[i] = int(((centroids[i] + 3.0) * 2)) & 0xff


    #### Formatting
    p1 = (slist[0]<<0) | (slist[1]<<8) | (slist[2]<<16) | (slist[3]<<24)
    p2 = (slist[4]<<0) | (slist[5]<<8) | (slist[6]<<16) | (slist[7]<<24)
    p3 = ((lateral_right & 0xFF) << 8) + (lateral_left & 0xFF)
    return p1, p2, p3






def L1_Evaluate_Pattern(strip_list = [], hflag_list = [], display=0):
    strip = np.sort(strip_list[0:8])
    hfleg = np.sort(hflag_list)
    l1hit  = np.full(120, '0')
    for st in strip:
    	l1hit[ st-1 ] = '1'
    l1hit = list(l1hit)
    l1hit.reverse()
    l1flag = ['0']*24
    centroids = []
    strip_list = np.array(strip_list[0:8])
    tmp = enumerate( strip_list[strip_list<=120][strip_list>0] )
    for k, g in groupby( tmp , lambda z : z[0]-z[1] ):
    	cluster = list(map( itemgetter(1), g))
    	size = np.size(cluster)
    	center  = np.mean(cluster)
    	centroids.append( [center, cluster] )
    hiploc = []
    for h in hflag_list:
    	for cl in centroids:
    		if(h in cl[1]):
    			hiploc.append( int(np.floor(cl[0])))
    hiploc = np.unique(hiploc)
    for i in hiploc:
    	location = 0
    	for cl in centroids:
    		if(i == int(np.floor(cl[0]))):
    			l1flag[location] = '1'
    		else:
    			location += 1
    l1flag.reverse()
    l1hit  = ''.join(l1hit)
    l1flag = ''.join(l1flag)
    return l1hit, l1flag








def check_stub_data_fifos(directory, excluded_iterations=[]):
    for fifofile in os.listdir(directory):
        if(fifofile[-18:] == 'CLUSTER-FIFO__.csv'):
            iteration = re.findall(r'____(\d+)_', fifofile)
            if(len(iteration)>0):
                iteration = int(iteration[0])
                if(iteration not in excluded_iterations):
                    fifofilename = fifofile
                    fifodata = CSV.csv_to_array(directory+fifofile)
                    stub_erros = fifodata[:, 2:10]
                    bx_with_error = np.array(fifodata[:, 1], dtype=int)
                    bx_with_error = list(bx_with_error[bx_with_error>=0])
                    # find consecutive BXs with error
                    consecutive_bx =[]
                    ranges = sum((list(t) for t in zip(bx_with_error, bx_with_error[1:]) if t[0]+1 != t[1]), [])
                    iranges = iter(bx_with_error[0:1] + ranges + bx_with_error[-1:])
                    iranges = [str(n) + '-' + str(next(iranges)) for n in iranges]
                    for xcd in iranges:
                        xcdsp = np.array(xcd.split('-'), dtype=int)
                        if(len(np.unique(xcdsp))>1): consecutive_bx.append([xcdsp[1]-xcdsp[0], xcdsp[0], xcdsp[1] ])

                    if(len(consecutive_bx)>0):
                        utils.print_warning('    Stub data ({:3d}) -> errors in consecutive BX  -> {:s}'.format(iteration, str(consecutive_bx)))
                        #utils.print_log('    ' + str(consecutive_bx))
                        #for cbxc in consecutive_bx: utils.print_log('    {:s}'.format(str(cbxc)))
                        #a = bx_with_error
                #else:
                #    utils.print_warning('    Excluded iteration {:d}'.format(shortrun[1]))

def check_L1_data_fifos(directory, excluded_iterations=[], expected_vector=[]):

    cnt_l1counter_errors  = [0,0]
    cnt_l1_single_bit_seu = [0,0]
    cnt_l1_multi_bit_seu  = [0,0]
    cnt_l1_total_seu      = [0,0]
    cnt_l1_trailer_error  = [0,0]
    l1_trailers_errors  = [[],[]]


    for fifofile in os.listdir(directory+'/L1-FIFO/'):
        for mode in [0,1]:
            seachstr = 'latch' if mode else 'sram'
            if((fifofile[-18:] == 'L1-DATA-FIFO__.csv') and seachstr in fifofile):
                iteration = re.findall(r'____(\d+)_', fifofile)
                if(len(iteration)>0):
                    iteration = int(iteration[0])
                    if(iteration not in excluded_iterations):
                        # extract expected vectors
                        with open(directory+'/CONFIG/'+fifofile[:-23]+'configuration.scv', 'r') as fi:
                            ll = fi.readline(); ll = fi.readline()
                            #hits, hips = re.findall(r'\[(.+?)\]+', ll)
                            #hits = np.array( re.findall(r'([0-9]+)+', hits), dtype=int)
                            #hips = np.array( re.findall(r'([0-9]+)+', hips), dtype=int)
                            #l1hit_ref, l1flag_ref = L1_Evaluate_Pattern(strip_list=hits, hflag_list=hips)
                        # extract clean information from FIFO
                        fifofilename = fifofile
                        fifodata = CSV.csv_to_array(directory+'/L1-FIFO/'+fifofile)
                        l1fifodata = []
                        for fff in fifodata:
                            if(fff[1] != "b''"):
                                l1fifodata.append([j.strip("b\b\r\n\t\' ") for j in list(fff[1:])])
                        l1fifodata = np.array(l1fifodata, dtype=str)
                        # analyze it
                        for event in l1fifodata:
                            #L1-counter errors
                            if(event[1] != event[2]): cnt_l1counter_errors[mode] += 1
                            # trailer error
                            if(event[5][163:167] != '1111'):
                                cnt_l1_trailer_error[mode] += 1
                                l1_trailers_errors[mode].append(event[5][163:167])
                            #bitstream errors
                            #errors = bin( np.int(event[4], 2) ^ np.int(l1hit_ref, 2) ).count('1')


    for mode in [0,1]:
        if(cnt_l1counter_errors[mode]>0):
            utils.print_warning('    L1 data {:5s} -> L1 counter errors = {:d}'.format(seachstr, cnt_l1counter_errors[mode]))
        if(cnt_l1_trailer_error[mode]>0):
            utils.print_warning('    L1 data {:5s} -> L1 trailer errors = {:d} [{:s}]'.format(seachstr, cnt_l1_trailer_error[mode], str(l1_trailers_errors[mode])))


    return cnt_l1counter_errors


directory='../SSA_Results/SEU_Results/'
use_run_precise_info = True
let_map = {'C':1.3, 'Al':5.7, 'Ar':9.9, 'Cr':16.1, 'Ni':20.4, 'Kr':32.4, 'Rh':46.1, 'Xe':62.5}
fluence_limit_all_ions = 0;fluence_limit_xe = 0;
flusence_per_let = {}
if(use_run_precise_info):
        run_info = CSV.csv_to_array(directory+'see_test_ions_flux.csv')
        ion_info = [[],[]]
        for info in run_info:
                ion_info[0].append( (re.split('-', info[10])[0]).strip() ) # run ion
                ion_info[1].append( info[5] ) # run number
        ion_info = np.array(ion_info)
dirs = os.listdir(directory)
dirs = [s for s in dirs if "Ion-" in s]
dirs.sort()
global_summary = {'latch_500':[], 'latch_100':[], 'sram_500':[], 'sram_100':[], 'stub':[],'sram_stub':[],'latch_stub':[] }
for ddd in dirs:
        for f in os.listdir( directory +'/'+ ddd ):
                run_summary = re.findall("SEU_SSA.+_summary.csv", f)
                if(len(run_summary)>0):
                        run_summary = directory +'/'+ ddd +'/'+ run_summary[0]
                        rfn = re.findall("SEU_SSA.+Ion-(.+)__Tilt-(.+)__Flux-(.+)_run(.+)____summary.csv", f)
                        if(len(rfn)>0):
                                utils.print_info("->  Elaborating data: " + str(ddd))
                                [ion, angle, memory, run] = rfn[0]
                                run_data = CSV.csv_to_array(  run_summary )
                                if(use_run_precise_info):
                                        index = np.where( (ion_info[0, :] == ion) & (ion_info[1, :] == run) )
                                        if(len(index[0])>1):
                                                utils.print_warning('    Found repeated test: ion={:s}, run={:s}, index={:s}'.format(ion, run, str(index)))
                                        dose = run_info[index][0][9]
                                        LET = run_info[index][0][11]
                                        mean_flux = run_info[index][0][8]
                                        run_time = np.sum( run_data[:, 5] )
                                        fluence = mean_flux * run_time
                                else:
                                        dose = 0
                                        LET = let_map[ ion ] / np.cos(np.radians(float(angle)) )
                                        mean_flux = 15000 * np.cos(np.radians(float(angle)) )
                                        run_time = np.sum( run_data[:, 5] )
                                        fluence = mean_flux * run_time
                                fluence_limit_all_ions += fluence
                                if(ion=='Xe'): fluence_limit_xe += fluence
                                if(LET in flusence_per_let): flusence_per_let[LET] += fluence
                                else: flusence_per_let[LET] = fluence
                                error_l1_sum = [0]*2; good_l1_sum = [0]*2; time_l1_sum = [0]*2 ; error_rate_l1_sum = [0]*2;
                                error_rate_l1_sum_normalised = [0]*2; error_rate_stub_sum_normalised = 0;
                                error_stub_sum = 0; good_stub_sum = 0; error_rate_stub_sum = 0; counters_a = 0; counters_s = 0;
                                excluded_iterations = []
                                for shortrun in run_data:
                                        shortrun_duration = shortrun[5]
                                        if(shortrun_duration>1): #exclude early stopped runs
                                                error_stub_sum += shortrun[12]
                                                good_stub_sum += shortrun[8]
                                                if(shortrun[6]>250): #high latency run
                                                        error_l1_sum[1] += shortrun[14]
                                                        good_l1_sum[1] += shortrun[10]
                                                else:
                                                        error_l1_sum[0] += shortrun[14]
                                                        good_l1_sum[0] += shortrun[10]
                                        else:
                                            excluded_iterations.append(int(shortrun[1]))
                                error_rate_l1_sum[0] = error_l1_sum[0] / fluence
                                error_rate_l1_sum[1] = error_l1_sum[1] / fluence
                                error_rate_stub_sum  = error_stub_sum  / fluence
                                try: error_rate_l1_sum_normalised[1] = (error_l1_sum[1]/(error_l1_sum[1]+good_l1_sum[1]))/ mean_flux
                                except ZeroDivisionError: error_rate_l1_sum_normalised[1] = -1
                                try: error_rate_l1_sum_normalised[0] = (error_l1_sum[0]/(error_l1_sum[0]+good_l1_sum[0]))/ mean_flux
                                except ZeroDivisionError: error_rate_l1_sum_normalised[0] = -1
                                try: error_rate_stub_sum_normalised  = (error_stub_sum/(error_stub_sum+good_stub_sum))/ mean_flux
                                except ZeroDivisionError: error_rate_stub_sum_normalised = -1
                                #print(mean_flux)
                                if(memory=='latch' ):
                                        global_summary['latch_500'].append([ion, angle, LET, good_l1_sum[1], error_l1_sum[1], error_rate_l1_sum[1], error_rate_l1_sum_normalised[1], run_time, mean_flux, fluence])
                                        global_summary['latch_100'].append([ion, angle, LET, good_l1_sum[0], error_l1_sum[0], error_rate_l1_sum[0], error_rate_l1_sum_normalised[0], run_time, mean_flux, fluence ])
                                        global_summary['latch_stub'].append([ion, angle, LET, good_stub_sum, error_stub_sum, error_rate_stub_sum, error_rate_stub_sum_normalised, run_time, mean_flux, fluence])
                                elif(memory=='sram'):
                                        global_summary['sram_500'].append( [ion, angle, LET, good_l1_sum[1], error_l1_sum[1], error_rate_l1_sum[1], error_rate_l1_sum_normalised[1], run_time, mean_flux, fluence ])
                                        global_summary['sram_100'].append( [ion, angle, LET, good_l1_sum[0], error_l1_sum[0], error_rate_l1_sum[0], error_rate_l1_sum_normalised[0], run_time, mean_flux, fluence ])
                                        global_summary['sram_stub'].append([ion, angle, LET, good_stub_sum, error_stub_sum, error_rate_stub_sum, error_rate_stub_sum_normalised, run_time, mean_flux, fluence] )

                                check_stub_data_fifos(directory=(directory+'/'+ddd+'/CL-FIFO/'), excluded_iterations=excluded_iterations)
                                check_L1_data_fifos(  directory=(directory+'/'+ddd), excluded_iterations=excluded_iterations)





#return global_summary
global_summary['latch_500'] = np.array(global_summary['latch_500'])
global_summary['latch_500'] = global_summary['latch_500'][np.argsort(np.array(global_summary['latch_500'][:,2],dtype=float ))]
global_summary['latch_100'] = np.array(global_summary['latch_100'])
global_summary['latch_100'] = global_summary['latch_100'][np.argsort(np.array(global_summary['latch_100'][:,2],dtype=float ))]
global_summary['sram_500'] = np.array(global_summary['sram_500'])
global_summary['sram_500'] = global_summary['sram_500'][np.argsort(np.array(global_summary['sram_500'][:,2],dtype=float ))]
global_summary['sram_100'] = np.array(global_summary['sram_100'])
global_summary['sram_100'] = global_summary['sram_100'][np.argsort(np.array(global_summary['sram_100'][:,2],dtype=float ))]
CSV.array_to_csv( np.array(global_summary['latch_500']), directory+'latch_500.csv')
CSV.array_to_csv( np.array(global_summary['latch_100']), directory+'latch_100.csv')
CSV.array_to_csv( np.array(global_summary['sram_500']), directory+'sram_500.csv')
CSV.array_to_csv( np.array(global_summary['sram_100']), directory+'sram_100.csv')
tmpvect = {}
global_summary['stub'] = global_summary['latch_stub'].copy()
for idx in range(len(global_summary['stub'])):
        if(global_summary['latch_stub'][idx][0:2] == global_summary['sram_stub'][idx][0:2]):
                global_summary['stub'][idx][3] = global_summary['sram_stub'][idx][3] + global_summary['latch_stub'][idx][3] #good_stub_sum
                global_summary['stub'][idx][4] = global_summary['sram_stub'][idx][4] + global_summary['latch_stub'][idx][4] #error_stub_sum
                global_summary['stub'][idx][5] = (global_summary['sram_stub'][idx][5] + global_summary['latch_stub'][idx][5])/2.0 #error_rate_stub_sum
                global_summary['stub'][idx][6] = (global_summary['sram_stub'][idx][6] + global_summary['latch_stub'][idx][6])/2.0	#error_rate_stub_sum_normalised
                global_summary['stub'][idx][7] = global_summary['sram_stub'][idx][7] + global_summary['latch_stub'][idx][7] #error_stub_sum
                global_summary['stub'][idx][8] = (global_summary['sram_stub'][idx][8] + global_summary['latch_stub'][idx][8])/2.0	#error_rate_stub_sum_normalised
                global_summary['stub'][idx][9] = global_summary['sram_stub'][idx][9] + global_summary['latch_stub'][idx][9] #error_stub_sum
        else:
                print('ERROR')
for stubdata in global_summary['stub']:
        if(stubdata[2] in tmpvect):
                tmpvect[stubdata[2]][3] += stubdata[3]
                tmpvect[stubdata[2]][4] += stubdata[4]
                tmpvect[stubdata[2]][5] += stubdata[5]
        else:
                tmpvect[stubdata[2]] = stubdata
global_summary['stub'] = []
for i in tmpvect:
        global_summary['stub'].append(tmpvect[i])
global_summary['stub'] = np.array(global_summary['stub'])
global_summary['stub'] = global_summary['stub'][np.argsort(np.array(global_summary['stub'][:,2],dtype=float ))]
CSV.array_to_csv( np.array(global_summary['stub']), directory+'stub.csv')
utils.print_good('Total fluence for all ions -> {:9.6f}E+6'.format(fluence_limit_all_ions*1E-6))
#utils.print_good('Total fluence for Xe       -> {:9.6f}E+6'.format(fluence_limit_xe*1E-6))
for fLET in sorted(flusence_per_let):
    utils.print_good('Total fluence per LET = {:5.1f} -> {:9.6f}E+6'.format(fLET, flusence_per_let[fLET]*1E-6))



#return global_summary



##############################################################
def fit_and_evaluate_error_rate(name_list, dataset_list, corr_list=[[0,0,0,0]], sensitive_depth=1E-6, directory = '../SSA_Results/SEU_Results/'):
	si_density   = [2.3290E3, 'mg/cm3']
	sens_volume  = [1*1*sensitive_depth, 'um^3']
	rate_tracker = CSV.csv_to_array( directory+'seu_rate_lhc_tracker.csv')
	total_crossection = {};
	hadron_flux  = CSV.csv_to_array( directory+'fluka_hadrons_gt20MeV_central_region_data.csv', noheader=True)
	fig = plt.figure(figsize=(12,8))
	color=iter(sns.color_palette('deep'))
	dataselect = 0; filename = '';
	for data in dataset_list:
		#data = data_set[name_list]
		LET  = np.array(data[:,3], dtype=np.double)
		Edep = LET * (sensitive_depth  * 1E2 * si_density[0] )
		cross_section = np.array(data[:,6], dtype=np.double)
		c = next(color)
		y = np.array(data[:,6], dtype=np.double)
		param_bounds =([0,0,0,0],[1E-1,1E2,1E2,1E5])
		init_param   = [corr_list[dataselect][0], corr_list[dataselect][1], corr_list[dataselect][2], corr_list[dataselect][3]]
		par, cov = curve_fit(f = f_weibull_cumulative, xdata = Edep, ydata = cross_section,  p0 = init_param, bounds=param_bounds)
		perr = np.sqrt(np.diag(cov))
		s0, s, E0, W = par
		s0_e, s_e, E0_e, W_e = perr
		utils.print_good('\nCumulative weibull fitting parameters: \n            Value   |  Error')
		utils.print_good('    W  = {:10.6e} | {:10.6e}'.format(W, W_e))
		utils.print_good('    s  = {:10.6e} | {:10.6e}'.format(s, s_e))
		utils.print_good('    s0 = {:10.6e} | {:10.6e}'.format(s0, s0_e))
		utils.print_good('    E0 = {:10.6e} | {:10.6e}\n'.format(E0, E0_e))
		plt.semilogy(Edep, cross_section,'o--', color = c)
		xl = np.linspace(-5,Edep[-1], 10000)
		plt.semilogy(xl, f_weibull_cumulative1(xl, s0, s, E0, W) , color = c)
		total_crossection[dataselect] = [0, '[cm^2]']
		for i in range(len(rate_tracker)-1):
			delta = (f_weibull_cumulative1(rate_tracker[i+1,0], s0,s,E0,W) - f_weibull_cumulative1(rate_tracker[i,0], s0,s,E0,W))/s0
			if(delta >0): total_crossection[dataselect][0] += (s0 / 1E-8) * rate_tracker[i,1] * delta
		utils.print_good('\nCross-section for CMS tracker environment: ')
		utils.print_good("    cs = {:10.6e}  | {:10.6e}\n".format(total_crossection[dataselect][0], 0))
		filename += '_{:s}'.format(name_list[dataselect])
		dataselect += 1
	ax = plt.subplot(111)
	leg = ax.legend(fontsize = 16, loc=('lower right'), frameon=True )
	leg.get_frame().set_linewidth(1.0)
	ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
	plt.ylabel("$ \sigma [cm^{2}] $", fontsize=20)
	plt.xlabel("$ E_{DEP} [MeV] $", fontsize=20)
	plt.xticks(fontsize=16)
	plt.yticks(fontsize=16)
	plt.savefig(directory+'/see_plot_cross_section_fit_{:s}.png'.format(filename), bbox_inches="tight");
	dataselect = 0
	for data in dataset_list:
		fig = plt.figure(figsize=(12,8))
		color=iter(sns.color_palette('deep'))
		for r in [22, 40, 60]:
			r_index = np.where(hadron_flux[:,0]==r)[0][0]
			z_index = [hadron_flux[0,1:], '[cm]']
			z_flux = [hadron_flux[r_index, 1:], '[cm^{-2} s^{-1}]']
			upset_rate = [z_flux[0]*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
			c = next(color)
			plt.plot(z_index[0], upset_rate[0], '.', label='r = {:6.1f}'.format(r))
			ax = plt.subplot(111)
			leg = ax.legend(fontsize=16, loc=('lower right'), frameon=True )
			leg.get_frame().set_linewidth(1.0)
			ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
			plt.ylabel("Upset rate "+upset_rate[1], fontsize=20)
			plt.xlabel("z "+z_index[1], fontsize=20)
			plt.xticks(fontsize=16)
			plt.yticks(fontsize=16)
			errors_expected = upset_rate[0][ np.where(z_index[0]==(r))[0][0] ]
			#self.r = r; self.b = z_flux[0]; self.c = errors_expected
			#utils.print_good('Expected errorr at r={:d} z=- flux={:7.3e} -> {:9.6e} errors/(s*chip)'.format(r, z_flux[0], errors_expected))
		#self.total_crossection =  total_crossection
		plt.savefig(directory+'/see_plot_error_rate_tracker_{:s}.png'.format(name_list[dataselect]), bbox_inches="tight");
		max_flux_compare_cic = 4.3E7
		upset_rate = [max_flux_compare_cic*total_crossection[dataselect][0], '[s^{-1} chip^{-1}]']
		dataselect += 1
		utils.print_good('Expected errorr at flux = {:7.3e} -> {:9.6e} errors/(s*chip)'.format(max_flux_compare_cic, upset_rate[0]))

##############################################################
def evaluate_error_rate(directory = '../SSA_Results/SEU_Results/'):
	data_set = {};
	#self.compile_logs(	directory=directory,	use_run_precise_info = True)
	data_set['stub_data'] = CSV.csv_to_array( directory+'stub.csv')
	data_set['sram_500']  = CSV.csv_to_array( directory+'sram_500.csv')
	data_set['latch_500'] = CSV.csv_to_array( directory+'latch_500.csv')
	# s0_e, s_e, E0_e, W_e
	fit_and_evaluate_error_rate(
		name_list    = ['stub_data'],
		dataset_list = [data_set['stub_data']],
		corr_list    = [[1E-3,1E-1,1E-2,1E3]] )
	fit_and_evaluate_error_rate(
		name_list = ['sram_500', 'latch_500'],
		dataset_list = [data_set['sram_500'], data_set['latch_500']],
		corr_list = [[1E-4,1E-2,1E-1,100] ,[1E-4,1E-2,1E-1,100]]  )
	fit_and_evaluate_error_rate(
		name_list = ['stub_data', 'sram_500'],
		dataset_list = [data_set['stub_data'], data_set['sram_500']],
		corr_list = [[1E-3,1E-1,1E-2,1E3],[1E-4,1E-2,1E-1,100] ] )



print('ciao')
