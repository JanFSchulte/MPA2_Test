
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from threading import Thread

from utilities.tbsettings import *
from scipy import interpolate as scipy_interpolate
from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *


class SSA_test_utility():

	def __init__(self, ssa, I2C, fc7, cal, pwr, seuutil):
		self.ssa = ssa;	self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal; self.pwr = pwr; self.seuutil = seuutil;
		self.striplist = []

	##############################################################
	def cluster_data(self, mode = "digital",  nstrips = 'random', min_clsize = 1, max_clsize = 4, nruns = 100, shift = 'default', display=False, init = False, hfi = True, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False, lateral = True, word_alignment='auto'):
		fo = open(file + "readout_cluster-data_" + mode + ".csv", filemode)
		stexpected = ''; stfound = '';
		utils.activate_I2C_chip(self.fc7)
		SendCommand_CTRL("stop_trigger")
		if (init):
			self.ssa.init(reset_board = False, reset_chip = False, display = False)
		if( (word_alignment=='auto' and (not self.ssa.cl_word_aligned())) or (word_alignment==True) or (word_alignment==1)):
			self.ssa.alignment_cluster_data_word()
			self.ssa.alignment_lateral_input()
		time.sleep(0.1)
		#self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		#self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		#self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = [0xff]*8
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(initialise = True, times = 1)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', cal_pulse_amplitude = 250, threshold = [70, 120])
		else:
			return False
		time.sleep(0.01)
		self.ssa.readout.cluster_data(initialize = True)
		time.sleep(0.01)
		self.ssa.inject.digital_pulse(hit_list = [], initialise = False)
		self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
		time.sleep(0.01)
		cnt = {'cl_sum': 0, 'cl_err' : 0};
		timeinit = time.time()
		for i in range(0,nruns):
			#clrange = np.array( random.sample(range(1, 60), nstrips)) * 2
			if(isinstance(nstrips, int)):
				nclusters_generated = nstrips
			else:
				nclusters_generated = random.randint(1, 8)
			if(lateral):
				cl_hits, cl_centroids = self.generate_clusters(nclusters_generated, min_clsize, max_clsize, -2, 124)
			else:
				cl_hits, cl_centroids = self.generate_clusters(nclusters_generated, min_clsize, max_clsize, 1, 121)
			wd = 0;
			err = [False]*3
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = cl_hits, initialise = False)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse( hit_list = cl_hits, initialise = False)
			time.sleep(0.005) #### important at nstrips = 8 (I2C time)
			received, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
			if(hfi):
				while(received==prev and len(prev)>0): #for firmware issure to be fix in D19C
					#time.sleep(0.1)
					utils.print_warning('\n->  Seems that the data was not updated in the FC7. Reiterating this sample {:d}.'.format(wd+1))
					#if(mode == "digital"):
					#	self.ssa.inject.digital_pulse(hit_list = cl_hits, initialise = False)
					#elif(mode == "analog"):
					#	self.ssa.inject.analog_pulse( hit_list = cl_hits, initialise = False)
					time.sleep(0.001)
					received, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
					if(wd>5): break
					wd += 1;
			if (len(received) != len(cl_centroids)):
				err[0] = True
			#else:
			missing=[]; exceding=[];
			for k in cl_centroids:
				if k not in received:
					err[0] = True
					missing.append(k)
			for k in received:
				if k not in cl_centroids:
					err[0] = True
					exceding.append(k)
			stexpected = utils.cl2str(cl_centroids, flag=missing,  color_flagged='red', color_others='green');
			stfound    = utils.cl2str(received,     flag=exceding, color_flagged='red', color_others='green')
			stprev     = utils.cl2str(prev)
			sthits     = utils.cl2str(cl_hits)
			#dstr = stexpected + ';    ' + stfound + '; ' + ';    ' + sthits + ';    ' + "                                            "
			dstr = "->       REF:" + stexpected + ',\n' + ' '*39 + 'OUT:' + stfound + ', ' + ",                                            \n"
			if (err[0]):
				erlog = "Cluster-Data-Error,   " + dstr
				cnt['cl_err'] += 1
				if stop_on_error:
					fo.write(runname + ', ' + erlog + ' \n')
					utils.print_log('\t' + erlog)
					return 100*(1-cnt['cl_err']/float(cnt['cl_sum']))
			else:
				if(display == True):
					utils.print_log(   "\tPassed                " + dstr)
			prev = received.copy()

			cl_centroids.extend([0]*(8-len(cl_centroids)))
			received.extend([0]*(8-len(received)))
			savestr = "{:s}, REF, {:s}, OUT, {:s}".format(runname, ', '.join(map(str, cl_centroids)),  ', '.join(map(str, received)) )
			if True in err:
				fo.write('ER' + ', ' + savestr + ' \n')
				utils.print_log( '\t' + erlog)
			else:
				fo.write('OK' + ', ' + savestr + ' \n')
			cnt['cl_sum'] += 1;
			if(mode == 'digital'):  utils.ShowPercent(cnt['cl_sum'], nruns, "Running clusters test based on digital test pulses")
			elif(mode == 'analog'): utils.ShowPercent(cnt['cl_sum'], nruns, "Running clusters test based on analog test pulses")
		utils.ShowPercent(nruns, nruns, "Done                                                      ")
		fo.close()
		rt = 100.0*(1.0-float(cnt['cl_err'])/float(cnt['cl_sum']))
		fo = open(file + "readout_cluster-data_summary" + mode + ".csv", 'a')
		fo.write("->  Cluster data test with {mode:s} injection -> {res:5.3f}%".format(mode=mode, res=rt))
		if(rt == 100.0):
			utils.print_good("->  Cluster data test with {mode:s} injection -> 100%".format(mode=mode))
		else:
			utils.print_error("->  Cluster data test with {mode:s} injection -> {res:5.3f}%".format(mode=mode, res=rt))
		#print(time.time()-timeinit)
		return rt

	##############################################################
	def l1_data(self, mode = "digital", nstrips='random', nruns = 100, calpulse = [100, 200], threshold = [20, 150], shift = 0, display = False, latency = 50, init = False, hfi = True, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '',profile=False):
		fo = open(file + "readout_L1-data_" + mode + ".csv", filemode)
		counter = [[0,0],[0,0], [0,0]]
		utils.activate_I2C_chip(self.fc7)
		if(tbconfig.VERSION['SSA'] >= 2): l1_counter_mask = 0b111111111
		else: l1_counter_mask = 0b1111
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		if(mode == "analog"): shift += 2
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency, multi = False)
		if(L1_counter_init < 0):
			utils.print_log('-> L1 COUNTER INIT ERROR ----------------------->  ' + str(L1_counter_init))
			return [-1,-1,-1]
		l1hitlistprev = []
		hiplistprev = []
		if(profile):
			pr_start=time.time()
			pr_cnt=0
		for H in range(0,2):
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(initialise = True)
			else:
				self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])
			for i in range(0,nruns):
				if(profile): pr_cnt+=1
				err = [False, False, False]; wd = 0;
				is_error_l1counter = 0;
				if(isinstance(nstrips, int)): nclusters_generated = nstrips
				else: nclusters_generated = random.randint(1, 24)
				cl_hits, cl_centroids = self.generate_clusters(nclusters_generated, 1, 2, 1, 121)
				if(mode == "digital"):
					if(H): self.ssa.inject.digital_pulse(hit_list = cl_hits, hip_list = cl_hits, initialise = False)
					else:  self.ssa.inject.digital_pulse(hit_list = cl_hits, hip_list = [],      initialise = False)
				else:
					self.ssa.inject.analog_pulse(hit_list = cl_hits, initialise = False)
				counter[H][0] += 1
				counter[2][0] += 1
				time.sleep(0.005) ##important to wait complete I2C operations
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift, latency = latency, multi = False)
				if (hfi): # for FC7 firmware issue in sampling some times the fast command (very rare)
					while(l1hitlist == l1hitlistprev):
						time.sleep(0.001); wd += 1
						utils.print_warning('HFI!!!')
						L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift, latency = latency, multi = False)
						if(wd>5): break
				missing_hit=[]; exceding_hit=[];
				missing_hip=[]; exceding_hip=[];

				if(H): hip_hits = list(range(1,len(cl_hits)+1))
				else:  hip_hits = []

				if(L1_counter < 0):
					utils.print_log('-> L1 COUNTER < 0 -----------------------> ' + str(L1_counter_init))
					return [-1,-1,-1]
				#if(random.sample(range(1, 100), 1)[0]==1): err[2] = True
				if ((L1_counter & l1_counter_mask) != ((L1_counter_init + 1) & l1_counter_mask) ):
					err[2] = True
					is_error_l1counter = True
				#else:
				for k in cl_hits:
					if k not in l1hitlist:
						err[H] = True
						missing_hit.append(k)
				for k in l1hitlist:
					if k not in cl_hits:
						err[H] = True
						exceding_hit.append(k)
				for k in hip_hits:
					if k not in hiplist:
						err[H] = True
						missing_hip.append(k)
				for k in hiplist:
					if k not in hip_hits:
						err[H] = True
						exceding_hip.append(k)
				##if(H and (len(hiplist) != len(cl_hits))): err[H] = True
				#if(not H and (len(hiplist) != 0)): err[1] = True
				stexpected   = utils.cl2str(cl_hits,   flag=missing_hit,  color_flagged='red', color_others='green');
				stfound      = utils.cl2str(l1hitlist, flag=exceding_hit, color_flagged='red', color_others='green')
				flagexpected = utils.cl2str(hip_hits,  flag=missing_hip,  color_flagged='red', color_others='green');
				flagfound    = utils.cl2str(hiplist,   flag=exceding_hip, color_flagged='red', color_others='green')
				l1col = 'red' if(err[2]) else 'blue'
				l1counterref = utils.text_color('{:3d}'.format(L1_counter_init+1), l1col)
				l1counterout = utils.text_color('{:3d}'.format(L1_counter), l1col)
				dstr = "->       REF: {:s} {:s}{:s} \n{:s} OUT: {:s} {:s}{:s}".format(
					l1counterref, stexpected, flagexpected, ' '*26, l1counterout, stfound, flagfound
				)
				fstr = "[{:3d}][{:3s}][{:3s}];   \t[{:3d}][{:3s}][{:3s}]".format(
				        (L1_counter_init+1)&l1_counter_mask,  str(cl_hits),  str(H),
				        L1_counter,  ', '.join(map(str, l1hitlist)),  ', '.join(map(str, hiplist)))
				l1hitlistprev = l1hitlist
				hiplistprev   = hiplist
				L1_counter_init = L1_counter-1
				L1_counter_init +=1
				if(err[H]): counter[H][1] += 1
				if(err[2]): counter[2][1] += 1
				if(err[H] or err[2]):
					fo.write(runname + ' , ' + '    L1 data error ' + fstr + ' \n')
				else:
					fo.write(runname + ' , ' + '    L1 data ok    ' + fstr + ' \n')
				if (err[H] or err[2]):
					utils.print_log( "\n    L1 data error " + dstr + "                                  ")
				else:
					if(display == True):
						utils.print_log( "\n    L1 data Ok    " + dstr + "                                  ")
				if(display):
					utils.ShowPercent(counter[0][0]+counter[1][0], nruns, "")
				else:
					if(H): utils.ShowPercent(counter[0][0]+counter[1][0], nruns, "Running L1 test with HIP flags")
					else:  utils.ShowPercent(counter[0][0]+counter[1][0], nruns, "Running L1 test")
		fo.close()
		result = [
			(1.0 - float(counter[0][1])/float(counter[0][0]))*100.0  ,
			(1.0 - float(counter[1][1])/float(counter[1][0]))*100.0  ,
			(1.0 - float(counter[2][1])/float(counter[2][0]))*100.0  ]
		#return "%5.2f%%" % (result)
		print('\n')
		if(result[2] == 100.0):
			utils.print_good( "->  L1-data (Headers)   test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[2]))
		else:
			utils.print_error("->  L1-data (Headers)   test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[2]))
		if(result[0] == 100.0):
			utils.print_good( "->  L1-data (RAW DATA)  test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[0]))
		else:
			utils.print_error("->  L1-data (RAW DATA)  test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[0]))
		if(result[1] == 100.0):
			utils.print_good( "->  L1-data (HIP FLAGS) test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[1]))
		else:
			utils.print_error("->  L1-data (HIP FLAGS) test scan with {mode:s} injection -> {res0:7.3f}%".format(mode=mode, res0=result[1]))

		if(profile):
			tres = time.time()-pr_start
			utils.print_log('->  Test time = {:0.3f}s - Time per cycle = {:0.3f}ms'.format(tres, 1000*tres/float(pr_cnt)))
		return result

	##############################################################
	def cluster_data_basic(self, mode = "digital", nruns = 1, shift='default', shiftL='default' , display=False, lateral = True, init = False, hfi = True, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False):
		fo = open(file + "readout_cluster-data-basic_" + mode + ".csv", filemode)
		stexpected = ''; stfound = ''; stlateralout = '';
		#utils.print_log("->  Remember to call test.lateral_input_phase_tuning() before to run this test")
		utils.activate_I2C_chip(self.fc7)
		if(not self.ssa.cl_word_aligned()):
			self.ssa.alignment_cluster_data_word()
			self.ssa.alignment_lateral_input()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = 0xff
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
		else:
			return [-1,-1,-1]
		if(lateral):
			clrange = random.sample(range(-2, 125), 127)
		else:
			clrange = random.sample(range(1, 121), 120)
		clrange *= nruns
		self.ssa.readout.cluster_data(initialize = True, shift = shift)
		cnt = {'cl_sum': 0, 'cl_err' : 0, 'li_sum': 0, 'li_err' : 0, 'lo_sum': 0, 'lo_err' : 0};
		for i in clrange:
			cnt['cl_sum'] += 1; wd = 0;
			err = [False]*3
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
			time.sleep(0.001)
			received, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
			if(hfi):
				while(received==[prev]): ## for firmware bug in D19C
					#utils.print_log('HFI')
					if(mode == "digital"):
						self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
					elif(mode == "analog"):
						self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
					received, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
					if(wd>5): break
					wd += 1;
			l = []
			if(i>0 and i < 121):
				if (len(received) != 1): err[0] = True
				elif (received[0] != i): err[0] = True
			else:
				cnt['li_sum'] += 1;
				if (mode == "digital"):
					if (len(received) != 1): err[1] = True
					elif (received[0] != i): err[1] = True
			if( ((i < 8 and i > 0) or (i > 112 and i < 121))):
				cnt['lo_sum'] += 1;
				if (mode == "digital"):
					l = self.ssa.readout.lateral_data(initialize = False, shift = shiftL)
					if (len(l) != 1): err[2] = True
					elif (l[0] != i): err[2] = True
			stexpected = utils.cl2str(i);
			stfound = utils.cl2str(received);
			stlateralout = utils.cl2str(l);
			stprev = utils.cl2str(prev)
			dstr = 'ref=' + stexpected + ';    out=' + stfound + ';    lateral=' + stlateralout + ';    prev=' + stprev + ';    ' + "                                            "
			if (err[0]):
				erlog = "Cluster-Data-Error;   " + dstr
				cnt['cl_err'] += 1
			elif(err[1]):
				erlog = "Lateral-Input-Error;  " + dstr
				cnt['li_err'] += 1;
			elif(err[2]):
				erlog = "Lateral-Output-Error; " + dstr
				cnt['lo_err'] += 1;
			else:
				if(display == True):
					utils.print_log(  "\tPassed                " + dstr)
			prev = i
			if True in err:
				fo.write(runname + ' ; ' + erlog + ' \n')
				utils.print_log('\t' + erlog)
				if(stop_on_error):
					return [-1,-1,-1]
			utils.ShowPercent(cnt['cl_sum'], len(clrange), "Running clusters test based on " + mode + " test pulses")
		utils.ShowPercent( len(clrange),  len(clrange), "Done                                                      ")
		fo.close()
		rt = [100*(1-cnt['cl_err']/float(cnt['cl_sum'])) , 100*(1-cnt['li_err']/float(cnt['li_sum'])) , 100*(1-cnt['lo_err']/float(cnt['lo_sum'])) ]
		return rt

	##############################################################
	def lateral_input_phase_tuning(self, display = False, timeout = 256*3, delay = 4, shift = 'default', init = False, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = ''):
		return self.ssa.alignment_cluster_data_word(
			display = display, delay = delay,
			shift = shift, init = init, file = file,
			filemode = filemode, runname = runname)

	##############################################################
	def l1_data_basic(self, mode = "digital", nruns = 1, calpulse = [100, 200], threshold = [20, 150], shift = 0, display = False, latency = 50, init = False, hfi = True, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '',profile=False):
		fo = open(file + "readout_L1-data_" + mode + ".csv", filemode)
		counter = [[0,0],[0,0]]
		utils.activate_I2C_chip(self.fc7)
		if(tbconfig.VERSION['SSA'] >= 2): l1_counter_mask = 0b111111111
		else: l1_counter_mask = 0b1111
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		if(mode == "analog"): shift += 2
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency, multi = False)
		if(L1_counter_init < 0):
			utils.print_log(str(L1_counter_init))
			return 'error'
		l1hitlistprev = []
		hiplistprev = []
		if(profile):
			pr_start=time.time()
			pr_cnt=0
		for H in range(0,2):
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(initialise = True)
			else:
				self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])

			for i in random.sample(range(1, 121), 120)*nruns:
				if(profile): pr_cnt+=1
				err = [False, False]; wd = 0;
				if(mode == "digital"):
					self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = False)
				else:
					self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
				counter[H][0] += 1
				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				#time.sleep(0.001)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift, latency = latency, multi = False)
				if (hfi):
					while(l1hitlist == l1hitlistprev):
						#utils.print_log('HFI')
						#sleep(0.001);
						L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False, multi = False)
						if(wd>5): break
						wd += 1
				if(L1_counter < 0): return 'error'
				if ((L1_counter & l1_counter_mask) != ((L1_counter_init + 1) & l1_counter_mask) ): err[H] = True
				if (len(l1hitlist) != 1): err[H] = True
				if (len(l1hitlist) > 0):
					if (l1hitlist[0] != i): err[H] = True
				if (len(hiplist) != H): err[H] = True
				if (len(hiplist) > 0):
					if (hiplist[0] != H): err[H] = True
				dstr = "expected: [{:3d}][{:3s}][{:3s}]\t  |  found: [{:3d}][{:3d}][{:3s}][{:3s}]".format(
						(L1_counter_init+1)&l1_counter_mask,  str(i),  str(H),
						L1_counter, BX_counter, ', '.join(map(str, l1hitlist)),  ', '.join(map(str, hiplist)))
				fstr = "[{:3d}][{:3s}][{:3s}];   \t[{:3d}][{:3s}][{:3s}]".format(
				        (L1_counter_init+1)&l1_counter_mask,  str(i),  str(H),
				        L1_counter,  ', '.join(map(str, l1hitlist)),  ', '.join(map(str, hiplist)))
				l1hitlistprev = l1hitlist
				hiplistprev   = hiplist
				####### L1_counter_init = L1_counter
				L1_counter_init +=1
				if (err[H]):
					counter[H][1] += 1
					fo.write(runname + ' ; ' + fstr + ' \n')
					utils.print_log( "\tError -> " + dstr + "                                  ")
				else:
					if(display == True):
						utils.print_log( "\tOk    -> " + dstr + "                                  ")
				if(display): utils.ShowPercent(counter[0], 240, "")
				else: utils.ShowPercent(counter[0][0]+counter[1][0], 240, "Running L1 test")
		fo.close()
		result = [ (1.0 - float(counter[0][1])/float(counter[0][0]))*100.0  ,  (1.0 - float(counter[1][1])/float(counter[1][0]))*100.0  ]
		#return "%5.2f%%" % (result)
		if(result[0] == 100 and result[1] == 100):
			utils.print_good("->  L1 data test scan with {mode:s} injection -> 100%".format(mode=mode))
		else:
			utils.print_error("->  Cluster data test scan with {mode:s} injection -> {res0:5.3f}% hit - {res1:5.3f}% HIP flags".format(mode=mode, res0=result[0], res1=result[1]))
		if(profile):
			tres = time.time()-pr_start
			utils.print_log('->  Test time = {:0.3f}s - Time per cycle = {:0.3f}ms'.format(tres, 1000*tres/float(pr_cnt)))
		return result

	##############################################################
	def measure_dynamic_power(self, NHits = 5, L1_rate = 1000, display_errors = False, slvs_current=7):
		self.striplist = random.sample([item for item in range(0,61) if item not in self.striplist], NHits)
		#self.striplist = random.sample(range(0,60), NHits)
		striplist = list(np.sort(self.striplist)*2)
		#utils.print_log(self.striplist)
		hiplist = self.striplist
		display = 0 if display_errors else -1
		sleep(0.01); SendCommand_CTRL("global_reset")
		sleep(0.01);  SendCommand_CTRL("fast_fast_reset")
		sleep(0.01); self.seuutil.ssa.init(edge = 'negative', display = False, slvs_current=slvs_current)
		s1, s2, s3 = self.seuutil.Stub_Evaluate_Pattern(striplist)
		p1, p2, p3, p4, p5, p6, p7 = self.seuutil.L1_Evaluate_Pattern(striplist, hiplist)
		sleep(0.01); self.seuutil.Configure_Injection(strip_list = striplist, hipflag_list = hiplist, analog_injection = 0, latency = 501, create_errors = False)
		sleep(0.01); self.seuutil.Stub_loadCheckPatternOnFC7(pattern1 = s1, pattern2 = s2, pattern3 = 1, lateral = s3, display = 0)
		sleep(0.01); Configure_SEU(1, int(40000.0/L1_rate-1), number_of_cal_pulses = 0, initial_reset = 1)
		sleep(0.01); fc7.write("cnfg_fast_backpressure_enable", 0)
		sleep(0.01); self.seuutil.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", 73)
		sleep(0.01); SendCommand_CTRL("start_trigger")
		sleep(0.50); pw = self.pwr.get_power(display = False, return_all = True)
		sleep(0.01); SendCommand_CTRL("stop_trigger")
		return pw

	##############################################################
	def power_vs_occupancy(self, L1_rate = 1000, display_errors = False, slvs_current = 7):
		#self.pwr.set_supply(mode='on', d=DVDD, a=AVDD, p=PVDD, bg = 0.270, display = True)
		I = []
		for nclusters in range(0,32,1):
			[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.measure_dynamic_power(NHits = nclusters, L1_rate = L1_rate, display_errors = display_errors, slvs_current=slvs_current)
			I.append([nclusters, Id, Ia, Ip])
			utils.print_log("->  N Clusters %5.1f  -> Current = %7.3f - %7.3f - %7.3f" % (nclusters/2.0, Id, Ia, Ip ))
		return I

	##############################################################
	def shift(self, pattern = 0b00011000):
		self.ssa.ctrl.activate_readout_shift()
		self.ssa.ctrl.set_shift_pattern_all(pattern)
		self.ssa.readout.all_lines(trigger = True, configure = True, cluster = True, l1data = False, lateral = False)

	##############################################################
	def ring_oscillators_vs_dvdd(self,
		dvdd_step=0.05, dvdd_max=1.3, dvdd_min=0.8, plot=False,
		filename = '../SSA_Results/ring_oscillator_vs_dvdd/', filemode='w', runname = '', printmode='info'):
		result = []
		if not os.path.exists(filename): os.makedirs(filename)
		fout = filename + 'ring_oscillator_vs_dvdd.csv'
		with open(fout, filemode)  as fo:
			fo.write("    RUN ,   DVDD , INV BR , INV TR , INV BC , INV BL , DEL BR , DEL TR , DEL BC , DEL BL ,  \n")
		dvdd_range = np.arange(dvdd_min, dvdd_max, dvdd_step)
		for dvdd in dvdd_range:
			self.ssa.pwr.set_dvdd(dvdd)
			time.sleep(1)
			self.ssa.reset()
			time.sleep(0.5)
			res = self.ssa.bist.ring_oscilaltor(
				resolution_inv=127, resolution_del=127, printmode=printmode,
				raw=0, asarray=1, display=1, note=' at DVDD={:5.3f}V'.format(dvdd) )
			#rdv = self.ssa.pwr.get_dvdd()
			result.append( np.append(dvdd , res) )
			with open(fout, 'a')  as fo:
				fo.write("{:8s}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f},\n".format(
					runname, dvdd, res[0], res[1], res[2], res[3], res[4], res[5], res[6], res[7]))
		self.ssa.pwr.set_dvdd(1.0)
		time.sleep(0.5)
		self.ssa.reset()
		time.sleep(0.5)
		if(plot):
			self.ring_oscillators_vs_dvdd_plot()
		return result

	##############################################################
	def ring_oscillators_vs_dvdd_plot(self,
		filename = '../SSA_Results/ring_oscillator_vs_dvdd/', runname = '', label=''):

		fout = filename + "ring_oscillator_vs_dvdd.csv"
		res = CSV.csv_to_array(filename = fout)
		measurement = np.array(res[:,1:-1], dtype=float)
		measurement = measurement[np.argsort(measurement[:,0])]
		x = np.array( measurement[:,0], dtype=float)
		for mode in ['Inverter', 'Delay_cell']:
			fig = plt.figure(figsize=(12,8))
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(True)
			ax.spines["right"].set_visible(True)
			color = iter(sns.color_palette('deep'))
			for i in range(4):
				if(mode == 'Inverter'):
					y = np.array( measurement[:,1+i], dtype=float)
				else:
					y = np.array( measurement[:,5+i], dtype=float)
				xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
				helper_y = scipy_interpolate.make_interp_spline(x, y)
				ynew = helper_y(xnew)
				c = next(color);
				if  (i==0): lb = 'Bottom-Right'
				elif(i==1): lb = 'Top-Right'
				elif(i==2): lb = 'Bottom-Center (ref)'
				elif(i==3): lb = 'Bottom-Left'
				plt.plot(x, y, 'x', label=(label+lb), color=c)
				plt.plot(xnew, ynew , color=c, lw=1, alpha = 0.5)
			leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
			leg.get_frame().set_linewidth(1.0)
			ax.get_xaxis().tick_bottom()
			ax.get_yaxis().tick_left()
			plt.ylabel("Frequency [ MHz ]", fontsize=16)
			plt.xlabel("DVDD [V]", fontsize=16)
			plt.xticks(np.arange(0.75,1.3,0.05), fontsize=12)
			if(mode == 'Inverter'):
				plt.yticks(range(0,701,50), fontsize=12)
			else:
				plt.yticks(range(10,36,2), fontsize=12)
			plt.savefig(filename+'/ring_oscillator_vs_dvdd_{:s}.png'.format(mode), bbox_inches="tight");
		plt.show()

	##############################################################
	def SRAM_BIST(self, nruns=3, display=1, note=''):
		rv = np.array([0,0])
		for memory in [1,2]:
			for i in range(nruns):
				try:    result = self.ssa.bist.SRAM(memory_select=memory, configure=1, display=(display>=2))
				except:
					print('-> Impossible to read BIST registers')
					result = 0
				rv[memory-1] += result
		rv = rv/np.float(nruns)
		if(display>=1):
			if(rv[0]<100): utils.print_warning( "->  {:s}BIST memory 1 test : FAIL ({:6.3f}) ".format(note, rv[0]))
			else:          utils.print_good(    "->  {:s}BIST memory 1 test : PASS ({:6.3f}) ".format(note, rv[0]))
			if(rv[1]<100): utils.print_warning( "->  {:s}BIST memory 2 test : FAIL ({:6.3f}) ".format(note, rv[1]))
			else:          utils.print_good(    "->  {:s}BIST memory 2 test : PASS ({:6.3f}) ".format(note, rv[1]))
		return rv

	##############################################################
	def SRAM_BIST_vs_DVDD(self,
		step=0.001, dvdd_max=0.800, dvdd_min=0.700, nruns_per_point=1, plot=False,
		filename = '../SSA_Results/memory_bist_vs_dvdd/', filemode='w', runname = ''):

		self.ssa.pwr.set_dvdd(1.0)
		time.sleep(0.5)
		self.ssa.reset()
		result = {}
		if not os.path.exists(filename): os.makedirs(filename)
		fout = filename + "memory_bist_vs_dvdd.csv"
		with open(fout, filemode)  as fo:
			fo.write("\n     RUN ,   DVDD   , MEM0   , MEM1   , \n")
		#dvdd_range = np.linspace(dvdd_max, dvdd_min, npoints)
		fine_range = np.arange(dvdd_max, dvdd_min-step, (-1)*step)
		coarse_renge = np.arange(1.3, dvdd_max+step, -0.1)
		coarse_renge = []
		dvdd_range = np.append(coarse_renge, fine_range)

		for dvdd in dvdd_range:
			self.ssa.pwr.set_dvdd(dvdd)
			#self.ssa.reset()
			time.sleep(0.1)
			res = self.SRAM_BIST(nruns=nruns_per_point, note='[DVDD={:5.3f}] '.format(dvdd), display=True )
			if(res[0]<0): res[0]=0
			if(res[1]<0): res[1]=0
			#rdv = self.ssa.pwr.get_dvdd()
			result[np.round(dvdd, 4)] = [res[0], res[1]]
			with open(fout, 'a')  as fo:
				fo.write("{:8s} , {:7.3f} , {:7.3f}, {:7.3f}, \n".format(runname, dvdd, res[0], res[1]))
		self.ssa.pwr.set_dvdd(1.0)
		time.sleep(0.5)
		if(plot):
			self.SRAM_BIST_vs_DVDD_plot()
		return result

	##############################################################
	def SRAM_BIST_vs_DVDD_plot(self,
		filename = '../SSA_Results/memory_bist_vs_dvdd/', runname = '', label=''):

		fout = "../SSA_Results/" + filename + "memory_bist_vs_dvdd.csv"
		res = CSV.csv_to_array(filename = fout)
		measurement = np.array(res[:,1:-1], dtype=float)
		measurement = measurement[np.argsort(measurement[:,0])]
		x = np.array( measurement[:,0], dtype=float)
		y_m0 = np.array( measurement[:,1], dtype=float)
		y_m1 = np.array( measurement[:,2], dtype=float)
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(True)
		ax.spines["right"].set_visible(True)
		color = iter(sns.color_palette('deep'))
		xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
		helper_y_m0 = scipy_interpolate.make_interp_spline(x, y_m0)
		helper_y_m1 = scipy_interpolate.make_interp_spline(x, y_m1)
		y0new = helper_y_m0(xnew)
		y1new = helper_y_m1(xnew)
		c = next(color);
		plt.plot(x, y_m0, 'x', label=(label+"SRAM 1"), color=c)
		plt.plot(xnew, y0new , color='red', lw=1, alpha = 0.5)
		#c = next(color);
		#c = next(color);
		#plt.plot(x, y_m0, 'x', label=(label+"SRAM 2"), color=c)
		#plt.plot(xnew, y1new , color=c, lw=1, alpha = 0.5)
		plt.show()

	##############################################################
	def power_vs_occupancy_plot(self,
		maxclusters=8, l1rates=[250, 500, 750, 1000], save=1, show=1,
		filename='../SSA_Results/power_vs_occupancy', fit=12, label=''):

		results = {}
		color=iter(sns.color_palette('deep'))
		if(save or show):
			plt.clf()
			fig = plt.figure(figsize=(18,12))
		for lr in l1rates:
			res = CSV.csv_to_array(filename = (filename+'/power_vs_occupancy_l1rate_{:0.0f}MHz'.format(lr)) )
			results[lr] = res
			current = res[:,3]
			ax = plt.subplot(111)
			ax.spines["top"].set_visible(True)
			ax.spines["right"].set_visible(True)
			x = list(range(maxclusters+1))
			y = current[0:maxclusters+1]
			#plt.ylim(15, 25)
			if(fit>0):
				xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
				c = next(color);
				#y_smuth = interpolate.BSpline(x, np.array([y, xnew]))
				helper_y3 = interpolate.make_interp_spline(x, np.array(y) )
				y_smuth = helper_y3(xnew)
				y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 1001, polyorder = fit)
				plt.plot(xnew, y_smuth , color=c, lw=1, alpha = 0.5)
				#plt.plot(xnew, y_hat   , color=c, lw=1, alpha = 0.8)
				plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o', label=label + "(L1 rate = {:4d} kHz)".format(lr), color=c)
				#p = np.poly1d(np.polyfit(list(range(maxclusters+1)), current[0:maxclusters+1], fit))
				#t = np.linspace(0, 8, 1000)
				#plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o', t, p(t), '-')
			else:
				plt.plot(range(0,maxclusters+1,1), current[0:maxclusters+1], 'o')
		leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		plt.ylabel("Digital power consuption [ mA ]", fontsize=16)
		plt.xlabel("Strip Occupancy [Hit/Bx]", fontsize=16)
		plt.xticks(range(0,maxclusters+1,1), fontsize=12)
		plt.yticks(np.arange(19,24.5,0.5), fontsize=12)
		if(save): plt.savefig(filename+'/power_vs_occupancy.png', bbox_inches="tight");
		if(show): plt.show()
		return res

	##############################################################
	def memory_with_l1(self, memory = [1,2], delay = [10], shift = 0, latency = 199, display = 1, file = '../SSA_Results/Chip0/Chip_0', filemode = 'w', runname = '1.2V'):
		utils.activate_I2C_chip(self.fc7)
		if(isinstance(memory, int)):
			if(memory in [1,2]): HIPrun = [memory-1]
		else: HIPrun = [0,1]
		#self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency, multi = False)
		self.ssa.inject.digital_pulse(initialise = True)
		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
		errlist = []; efflist = [];
		for HIP in HIPrun:
			cnt = [0, 0, 0]
			for d in delay:
				Configure_TestPulse(
					delay_after_fast_reset = 512 + d,
					delay_after_test_pulse = (latency+3+shift),
					delay_before_next_pulse = 200,
					number_of_test_pulses = 1)
				for strip in range(1,121):
					if HIP: self.ssa.inject.digital_pulse(hit_list = [strip], hip_list = [strip], initialise = False)
					else:   self.ssa.inject.digital_pulse(hit_list = [strip], hip_list = [], initialise = False)
					L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(latency = latency, initialise = False, multi = False)
					while(l1hitlist == [strip-1]):
						L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(latency = latency, initialise = False, multi = False)
						if cnt[2] > 3: break;
						cnt[2] += 1
					dstr = "expected: [L1 =  1][BX =%3d][HIT =%3s][HIP =%3d]\t  |  found: [L1 =%3d][BX =%3d][HIT =%3s][HIP =%3s]" % (
							(d+1)%16, strip, HIP,     L1_counter,  BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)))
					#if(((L1_counter != 1) or (BX_counter != (d+1)%16)) ):
					#	print("\tCounter Error -> " + dstr + "                                  ")

					shitlist = l1hitlist + [' ']*(120-len(l1hitlist))
					shiplist = hiplist   + [' ']*(120-len(l1hitlist))
					sstr = "REF, {:d}, {:d}, {:d}, {:d}, OUT, {:d}, {:d}, {:s}, {:s}".format(
						1, (d+1)%16, strip, HIP, L1_counter, BX_counter, ', '.join(map(str,shitlist)), ', '.join(map(str,shiplist)) )
					error = False
					if not HIP:
						if(len(l1hitlist) != 1): error = True
						elif (l1hitlist[0] != strip): error = True
					else:
						if(len(hiplist) != 1): error = True
						elif (hiplist[0] != 1): error = True
					if(error):
						cnt[1] += 1
						errlist.append([[strip], l1hitlist])
						if(display >= 1):
							utils.print_log("\tMemory Error  -> " + dstr + "                                  ")
					elif(display >= 2):
						utils.print_log("\tOk            -> " + dstr + "                                  ")

					fo = open(file + "memory_log_{:s}.csv".format(runname), 'a')
					if (error):
						fo.write('ER' + ', ' + sstr + ' \n')
					else:
						fo.write('OK' + ', ' + sstr + ' \n')
					fo.close()
					cnt[0] += 1
					utils.ShowPercent(strip, 120, "Running Memory test")
				eff = ((1-(cnt[1]/float(cnt[0])))*100 )
				efflist.append(eff)
				fo = open(file + "memory_summary.csv", 'a')
				fo.write("\n{:8s}, {:0d}, {:0d}, {:7.3f} , {:s} ,".format(runname, (HIP+1), d, eff, (', '.join(map(str, errlist))) ))
				fo.close()
				strprint = ("->  Memory {:0d} test scan ({:1s}) -> {:5.3f}%".format((HIP+1), runname, eff))
				if(eff==100):
					utils.print_good(strprint)
				else:
					utils.print_error(strprint)

		self.memerrlist = errlist
		return efflist

	##############################################################
	def memory_with_l1_vs_voltage(self, memory = 1, step = 0.005, start = 1.25, stop = 0.9, latency = 200, shift = 0, file = '../SSA_Results/memory_bist_vs_dvdd/', filemode = 'w', runname = ''):
		utils.activate_I2C_chip(self.fc7)
		if not os.path.exists(file):
			os.makedirs(file)
		with open("../SSA_Results/" + file + "_Test_Memory-Supply_" + str(memory) + ".csv", filemode)  as fo:
			fo.write("\n    RUN ; DVDD;       EFFICIENCY;    ERROR LIST; \n")
		for dvdd in np.arange(start, stop, -step):
			self.pwr.set_dvdd( dvdd )
			time.sleep(0.5)
			rt = self.ssa.init(reset_board = True, reset_chip = False, display = False) #alignement
			if not rt:
				eff = 0; erlist = [];
			eff = self.memory(memory = memory, display = 0, latency = latency, shift = shift)
			erlist = self.memerrlist
			with open("../SSA_Results/" + file + "_Test_Memory-Supply_" + str(memory) + ".csv", 'a')  as fo:
				fo.write("%8s ; %4.3fV ;     %7.2f%% ;       %s ; \n" % (runname, dvdd, eff, erlist))
			utils.print_log("->  {:4.3f}V ;  {:7.2f}% ;".format(dvdd, eff))
			if eff == 0:
				break
		fo.close()

	##############################################################
	def mem_test_gen(self, init = True, patternL = range(10,90,10), patternH = [30,40,50], sequence = 0xff, npulses = 1, shift = 0, delay = 10, l1_duration = 2, calpulse_duration = 1, latency = 0, fc_resync = 1, fc_test = 1, fc_l1 = 1, clean = True, display = False, display_raw = False, delay_before_next_pulse = 1, delay_between_consecutive_trigeers = 1):
		latency = latency + 2
		if clean:
			self.ssa.init(reset_board = True, reset_chip = False, display = False)
		if init:
			self.ssa.ctrl.activate_readout_normal()
			if(tbconfig.VERSION['SSA'] >= 2):
				sleep(0.01); self.I2C.strip_write(register="DigCalibPattern_L", field=False, strip='all', data=0)
				sleep(0.01); self.I2C.strip_write(register="DigCalibPattern_H", field=False, strip='all', data=0)
				sleep(0.01); self.I2C.peri_write( register="control_1", field='L1_Latency_msb', data = 0 )
				sleep(0.01); self.I2C.peri_write( register="control_3", field='L1_Latency_lsb', data = latency )
			else:
				sleep(0.01); self.I2C.strip_write("DigCalibPattern_L", 0, 0)
				sleep(0.01); self.I2C.strip_write("DigCalibPattern_H", 0, 0)
				sleep(0.01); self.I2C.peri_write('L1_Latency_msb', 0)
				sleep(0.01); self.I2C.peri_write('L1_Latency_lsb', latency)
			self.ssa.ctrl.set_cal_pulse_duration(duration = calpulse_duration)
			if(tbconfig.VERSION['SSA'] >= 2):
				self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b01001)
			else:
				self.I2C.strip_write("ENFLAGS", 0, 0b01001)
			self.fc7.write("cnfg_fast_source", 6)
			self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
			self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", fc_test)
			self.fc7.write("cnfg_fast_tp_fsm_l1a_en", fc_l1)
			self.fc7.write("cnfg_fast_initial_fast_reset_enable", fc_resync) # initial fast reset which is sent once after start_trigger command
			self.fc7.write("cnfg_fast_delay_after_fast_reset", delay)
			self.fc7.write("cnfg_fast_delay_after_test_pulse", (latency+3+shift))
			self.fc7.write("cnfg_fast_delay_before_next_pulse", delay_before_next_pulse)
			self.fc7.write("cnfg_fast_delay_between_consecutive_trigeers", delay_between_consecutive_trigeers)
			self.fc7.write("cnfg_fast_triggers_to_accept", npulses)
			#self.fc7.write("ctrl_fast_signal_duration", l1_duration) ### doesn't work
			#sleep(0.1); self.fc7.write("ctrl_fast", fc7AddrTable.getItem("ctrl_fast_signal_duration").shiftDataToMask(l1_duration) ); sleep(0.1);
			sleep(0.1);	SendCommand_CTRL("load_trigger_config"); sleep(0.1);
		self.ssa.inject.digital_pulse(hit_list = patternL, hip_list = patternH, initialise = False, sequence = sequence)
		sleep(0.001)

		#send_trigger(0)
		SendCommand_CTRL("start_trigger")
		rt = self.ssa.readout.l1_data(display = display, initialise = False, mipadapterdisable = False, trigger = 0, multi = True, display_raw = display_raw)
		dstr = '';
		for res in rt:
			L1_counter, BX_counter, l1hitlist, hiplist = res;
			if(L1_counter != -1 and BX_counter != -1):
				dstr += "->      [%3d][%3d][%3s][%3s]\n" % (L1_counter, BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)))
			else:
				dstr = "->      [---][---][---][---]\n"
		utils.print_log(dstr)
		#return dstr

	##############################################################
	def mem_test_inputs(self, fix_adr = 0, fix_data_before = 0, fix_data_after = 0, fix_ren = 0, npulses = 5,  pattern = range(30,90,5), display = False, latency = 10, sequence = 0xff):
		self.ssa.init(reset_board = True, reset_chip = False, display = False)
		if fix_adr:  latency = 0
		else:        latency = latency
		if fix_ren:  l1_duration = 3; ## doesn't change the trigger duration...
		else:        l1_duration = 1;
		if fix_data_before:
			#if fix_data_after: calpulse_duration = 15;  shift = 7-latency;
			#else:              calpulse_duration =  4;  shift = 1;
			if fix_data_after: calpulse_duration =  6;  shift = 2;
			else:              calpulse_duration =  4;  shift = 1;
		else:
			if fix_data_after: calpulse_duration = 15;  shift = 0;
			else:              calpulse_duration =  1;  shift = 0;
		self.mem_test_gen(
			patternL = pattern, patternH = pattern, l1_duration = l1_duration,
			calpulse_duration = calpulse_duration,
			shift = shift, npulses = npulses,
			delay = 10, latency = latency, sequence = sequence,
			display = display, clean = False)

#	def mem_test2(self, delay = 10, shift = 0, latency = 200, pattern = [50, 51,52,53,54,55]):
#		utils.activate_I2C_chip(self.fc7)
#		self.ssa.init(reset_board = False, reset_chip = False, display = False)
#		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
#		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True, multi = False)
#		self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency)
#		self.ssa.inject.digital_pulse(initialise = True, times = 15)
#		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
#		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
#		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
#		Configure_TestPulse(
#			delay_after_fast_reset = 512 + delay,
#			delay_after_test_pulse = (latency+3+shift),
#			delay_before_next_pulse = 0,
#			number_of_test_pulses = 1)
#		self.ssa.inject.digital_pulse(hit_list = pattern, hip_list = [], initialise = False)
#		L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(latency = latency, initialise = False, multi = False)
#		dstr = "[%3d][%3d][%3s][%3s]" % (L1_counter, BX_counter, ', '.join(map(str, l1hitlist)), ', '.join(map(str, hiplist)))
#		utils.print_log(dstr)

	def generate_clusters(self, nclusters, min_clsize = 1, max_clsize = 4, smin=-2, smax=124, HIP_flags=False):
		hits = []; centroids = [];
		hips = []; flags = []; exc = [];
		for i in range(nclusters):
			size = random.sample(range(min_clsize, max_clsize), 1)[0]
			rangelist = list( set(range(smin, smax-size)) - set(exc) )
			adr = random.sample(rangelist, 1)[0]
			cll = range(adr, adr+size)
			hits += cll
			centroids.append( np.mean(cll) )
			exc += range(min(cll)-max_clsize-1, max(cll)+2)
			iship = random.randint(0,1)
			if(iship):
				hips.append(adr)
				flags.append(np.mean(cll))
		hits.sort()
		centroids.sort()
		hips.sort()
		flags.sort()
		if(HIP_flags):
			return hits, centroids, hips, flags
		else:
			return hits, centroids

	def force_alinament(self, maxtime = 5*60):
		time_init = time.time()
		while ((time.time()-time_init) < maxtime):
			utils.print_log('________________________________')
			rt = self.cluster_data(nruns = 50, stop_on_error = True)
			if(rt==100):
				rt1 = self.cluster_data(nruns = 1000, stop_on_error = True)
				if rt == 100: break
				fc7.write("ctrl_phy_fast_cmd_phase",3)
			else:
				fc7.write("ctrl_phy_fast_cmd_phase",24)
			utils.print_log('SHIFT = 20')
			utils.print_log(rt)

	def efuses_read_errorrate(self, vstep = 0.005, expected = 0x12345678, npoints = 1000):
		rate = []
		for dvdd in np.arange(0.95, 1.25, vstep):
			self.pwr.set_dvdd(dvdd)
			cnt = 0
			for i in range(npoints):
				value = self.ssa.ctrl.read_fuses(display = False)
				if(value == expected):
					cnt += 1
			tmp = [dvdd, np.float(cnt)/npoints]
			rate.append( tmp )
			utils.print_log('->  {0:5.3f}V -> {1:5.2f}'.format(tmp[0], tmp[1]*100.0))
		rate = np.array(rate)
		x = rate[:,0]; y = rate[:,1];
		w, h = plt.figaspect(1/2.0)
		fig = plt.figure(figsize=(w,h))
		ax = plt.subplot(111)
		ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
		plt.xticks(np.arange(0.95, 1.25, vstep), fontsize=16)
		plt.yticks(range(0,120,10), fontsize=16)
		plt.ylabel("% of correct read operations", fontsize=16)
		#plt.ylim(10, 35)
		plt.xlabel("DVDD [V]", fontsize=16)
		color=iter(sns.color_palette('deep'))
		c = next(color);
		plt.plot(x, y*100.0, color=c, lw=3, alpha = 0.8)
		plt.plot(x, y*100.0, 'o')
		plt.show()
		return rate

	def measure_dynamic_power_old(self, NHits = 5, L1_rate = 1000, display_errors = False):
		striplist = random.sample(range(1,60), NHits)
		striplist = list(np.sort(striplist)*2)
		utils.print_log(striplist)
		hiplist = striplist
		display = 0 if display_errors else -1
		t1 = FuncThread(
			self.seuutil.Run_Test_SEU,
			striplist, hiplist, 1, int(40000.0/L1_rate-1),
			501, 7, display, '', '', 73, False, False)
		time.sleep(0.5)
		t1.start();
		time.sleep(10)
		while(True):
			try:
				[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.pwr.get_power(display = False, return_all = True)
				break
			except:
				pass
		t1.join()
		return [Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip]

	##############################################################
	def fast_digital_test(self, run='0'):
		self.fc7.reset()
		time.sleep(0.5)
		self.ssa.pwr.on()
		self.ssa.reset()
		time.sleep(1)
		self.ssa.init()
		time.sleep(0.5)
		self.cluster_data( word_alignment=True )
		time.sleep(0.5)
		self.l1_data()
		self.SRAM_BIST_vs_DVDD(
			step=0.1, dvdd_max=1.3, dvdd_min=0.7, nruns_per_point = 5,
			filename = ('../SSA_Results/fast_digital_test/'+run+'/') )
		self.ssa.pwr.off()

	##############################################################
#	def quick_test_cluster_cut(self, nruns = 10):
#
#		self.ssa.ctrl.set_cluster_cut(0)
#		cluster_size = 2
#		self.cluster_data(mode = "digital",  nstrips = 8, min_clsize = cluster_size-1, max_clsize = cluster_size, nruns = 100, lateral=False)


'''
def prova(i):
	ssa.inject.digital_pulse([i])
	received = ssa.readout.cluster_data(initialize = False)
	if([i] != received): utils.print_log('error ' + str(i) + '  ' +str(received))



while 1:
	for i in range(1,121): prova(i)
'''
