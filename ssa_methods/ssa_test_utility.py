from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import seaborn as sns
import time
import sys
import inspect
import random
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread



class SSA_test_utility():

	def __init__(self, ssa, I2C, fc7, cal, pwr, seuutil):
		self.ssa = ssa;	self.I2C = I2C;	self.fc7 = fc7;
		self.cal = cal; self.pwr = pwr; self.seuutil = seuutil;
		self.striplist = []


	def cluster_data(self, mode = "digital",  nstrips = 5, min_clsize = 1, max_clsize = 4, nruns = 1000, shift = 0, display=False, init = False, hfi = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False):
		fo = open("../SSA_Results/" + file + "_Test_ClusterData2_" + mode + ".csv", filemode)
		stexpected = ''; stfound = '';
		utils.activate_I2C_chip()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = [0xff]*nstrips
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True, times = 8)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
			shift += 2
		else:
			return False
		self.ssa.readout.cluster_data(initialize = True)
		cnt = {'cl_sum': 0, 'cl_err' : 0};
		for i in range(0,nruns):
			#clrange = np.array( random.sample(range(1, 60), nstrips)) * 2
			cl_hits, cl_centroids = self._generate_clusters(nstrips, min_clsize, max_clsize)
			wd = 0;
			err = [False]*3
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(hit_list = cl_hits, initialise = False)
			elif(mode == "analog"):
				self.ssa.inject.analog_pulse( hit_list = cl_hits, initialise = False, cal_pulse_amplitude = 255)
			time.sleep(0.001)
			r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
			if(hfi):
				while(r==prev and len(prev)>0): #for firmware issure to be fix in D19C
					#time.sleep(0.1)
					#print 'HFI'
					if(mode == "digital"):
						self.ssa.inject.digital_pulse(hit_list = cl_hits, initialise = False)
					elif(mode == "analog"):
						self.ssa.inject.analog_pulse( hit_list = cl_hits, initialise = False)
					r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
					if(wd>5): break
					wd += 1;
			if (len(r) != len(cl_centroids)):
				err[0] = True
			else:
				for k in cl_centroids:
					if k not in r:
						err[0] = True
			stexpected = utils.cl2str(cl_centroids);
			stfound = utils.cl2str(r)
			stprev = utils.cl2str(prev)
			sthits = utils.cl2str(cl_hits)
			#dstr = stexpected + ';    ' + stfound + '; ' + ';    ' + sthits + ';    ' + "                                            "
			dstr = "->       REF:" + stexpected + ';         OUT:' + stfound + '; ' + ";                                            "
			if (err[0]):
				erlog = "Cluster-Data-Error;   " + dstr
				cnt['cl_err'] += 1
				if stop_on_error:
					fo.write(runname + ' ; ' + erlog + ' \n')
					print '\t' + erlog
					return 100*(1-cnt['cl_err']/float(cnt['cl_sum']))
			else:
				if(display == True):
					print   "\tPassed                " + dstr
			prev = r
			if True in err:
				fo.write(runname + ' ; ' + erlog + ' \n')
				print '\t' + erlog
			cnt['cl_sum'] += 1;
			utils.ShowPercent(cnt['cl_sum'], nruns, "Running clusters test based on digital test pulses")
		utils.ShowPercent(nruns, nruns, "Done                                                      ")
		fo.close()
		rt = 100*(1-cnt['cl_err']/float(cnt['cl_sum']))
		return rt



	def cluster_data_basic(self, mode = "digital", nruns = 5, shift = 0, shiftL = 0, display=False, lateral = True, init = False, hfi = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False):
		fo = open("../SSA_Results/" + file + "_Test_ClusterData_" + mode + ".csv", filemode)
		stexpected = ''; stfound = ''; stlateralout = '';
		#print "->  \tRemember to call test.lateral_input_phase_tuning() before to run this test"
		utils.activate_I2C_chip()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.ctrl.set_cal_pulse_delay(0)
		prev = 0xff
		if(mode == "digital"):
			self.ssa.inject.digital_pulse(hit_list = [], hip_list = [], initialise = True)
		elif(mode == "analog"):
			self.ssa.inject.analog_pulse(hit_list = [], initialise = True)
			shift += 2
		else:
			return False
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
			r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
			if(hfi):
				while(r==[prev]): ## for firmware bug in D19C
					#print 'HFI'
					if(mode == "digital"):
						self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
					elif(mode == "analog"):
						self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
					r, status = self.ssa.readout.cluster_data(initialize = False, shift = shift, getstatus = True)
					if(wd>5): break
					wd += 1;
			l = []
			if(i>0 and i < 121):
				if (len(r) != 1): err[0] = True
				elif (r[0] != i): err[0] = True
			else:
				cnt['li_sum'] += 1;
				if (mode == "digital"):
					if (len(r) != 1): err[1] = True
					elif (r[0] != i): err[1] = True
			if( ((i < 8 and i > 0) or (i > 112 and i < 121))):
				cnt['lo_sum'] += 1;
				if (mode == "digital"):
					l = self.ssa.readout.lateral_data(initialize = False, shift = shiftL)
					if (len(l) != 1): err[2] = True
					elif (l[0] != i): err[2] = True
			stexpected = utils.cl2str(i);
			stfound = utils.cl2str(r);
			stlateralout = utils.cl2str(l);
			stprev = utils.cl2str(prev)
			dstr = stexpected + ';    ' + stfound + ';    ' + stlateralout + ';    ' + stprev + ';    ' + "                                            "
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
					print   "\tPassed                " + dstr
			prev = i
			if True in err:
				fo.write(runname + ' ; ' + erlog + ' \n')
				print '\t' + erlog
				if(stop_on_error):
					return [0,0,0]
			utils.ShowPercent(cnt['cl_sum'], len(clrange), "Running clusters test based on " + mode + " test pulses")
		utils.ShowPercent( len(clrange),  len(clrange), "Done                                                      ")
		fo.close()
		rt = [100*(1-cnt['cl_err']/float(cnt['cl_sum'])) , 100*(1-cnt['li_err']/float(cnt['li_sum'])) , 100*(1-cnt['lo_err']/float(cnt['lo_sum'])) ]
		return rt


	def lateral_output_phase_tuning(self):
		for i in range(16):
			self.ssa.set_lateral_sampling_shift(i,0)
			self.ssa.inject.digital_pulse([1,2,3,4,5,6,7,8])
			a, b = self.ssa.readout.lateral_data(shift =-1, raw = True)
			print( bin(a) + '  ' + bin(b))
			a, b = self.ssa.readout.lateral_data(shift = 0, raw = True)
			print( bin(a) + '  ' + bin(b))
			a, b = self.ssa.readout.lateral_data(shift = 1, raw = True)
			print( bin(a) + '  ' + bin(b))

	def lateral_input_phase_tuning(self, display = False, timeout = 256*3, delay = 4, shift = 0, init = False, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + file + "_Test_LateralInput.csv", filemode)
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.readout.cluster_data(initialize = True)
		alined_left  = False; alined_right = False; cnt = 0; print "";
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay)
		self.ssa.inject.digital_pulse([100, 121, 124], initialise = True)
		#self.ssa.ctrl.set_lateral_data(0b00001001, 0)
		while ((alined_left == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == 100 and clusters[1] == 121 and clusters[2] == 124):
					alined_left = True
			utils.ShowPercent(cnt, timeout+1, "Allaining left input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			#if  (cnt==256): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+1)
			#elif(cnt==512): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+2)
			self.ssa.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			cnt += 1
		if(alined_left == True):
			utils.ShowPercent(100, 100, "Left Input line alined    \t\t" + str(clusters) + "           ")
		else:
			utils.ShowPercent(100, 100, "Impossible to align left input data line  ")
		#self.ssa.ctrl.set_lateral_data(0, 0b10100000)
		self.ssa.inject.digital_pulse([-2, 0, 10], initialise = True)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):
			clusters = self.ssa.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == -2 and clusters[1] == 0 and clusters[2] == 10):
					alined_right = True
			utils.ShowPercent(cnt, timeout+1, "Allaining right input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			self.ssa.ctrl.set_lateral_data_phase(5,0)
			time.sleep(0.001)
			cnt += 1
		if(alined_right == True):
			utils.ShowPercent(100, 100, "Right input line alined     \t\t" + str(clusters) + "           ")
		else:
			utils.ShowPercent(100, 100, "Impossible to align right input data line")
		fo.write(str(runname) + ' ; ' + str(alined_left) + " ; " + str(alined_right) + ' \n')
		return [alined_left, alined_right]



	def l1_data_basic(self, mode = "digital", nruns = 5, calpulse = [100, 200], threshold = [20, 150], shift = 0, display = False, latency = 50, init = False, hfi = True, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		fo = open("../SSA_Results/" + file + "_Test_L1_" + mode + ".csv", filemode)
		counter = [[0,0],[0,0]]
		utils.activate_I2C_chip()
		if (init): self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		if(mode == "analog"): shift += 2
		L1_counter_init, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency, multi = False)
		if(L1_counter_init < 0): return 'error'
		l1hitlistprev = []
		hiplistprev = []
		for H in range(0,2):
			if(mode == "digital"):
				self.ssa.inject.digital_pulse(initialise = True)
			else:
				self.ssa.inject.analog_pulse(initialise = True, mode = 'edge', threshold = threshold, cal_pulse_amplitude = calpulse[H])
			for i in random.sample(range(1, 121), 120)*nruns:
				err = [False, False]; wd = 0;
				if(mode == "digital"):
					self.ssa.inject.digital_pulse(hit_list = [i], hip_list = [i]*H, initialise = False)
				else:
					self.ssa.inject.analog_pulse(hit_list = [i], initialise = False)
				counter[H][0] += 1
				#self.ssa.inject.digital_pulse(hit_list = [i], initialise = False)
				time.sleep(0.001)
				L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(initialise = False, shift = shift, latency = latency, multi = False)
				if (hfi):
					while(l1hitlist == l1hitlistprev):
						#print 'HFI'
						sleep(0.001); L1_counter, BX_counter, l1hitlist, hiplist = self.ssa.readout.l1_data(shift = shift, latency = latency, initialise = False, multi = False)
						if(wd>5): break
						wd += 1
				if(L1_counter < 0): return 'error'
				if ((L1_counter & 0b1111) != ((L1_counter_init + 1) & 0b1111) ): err[H] = True
				if (len(l1hitlist) != 1): err[H] = True
				if (len(l1hitlist) > 0):
					if (l1hitlist[0] != i): err[H] = True
				if (len(hiplist) != H): err[H] = True
				if (len(hiplist) > 0):
					if (hiplist[0] != H): err[H] = True
				dstr = "expected: [%2d][%3s][%3s]\t  |  found: [%2d][%3s][%3s]"  % (
				        (L1_counter_init+1)&0b1111, i, H,
				        L1_counter,      ', '.join(map(str, l1hitlist)),       ', '.join(map(str, hiplist)))
				fstr = "[%2d][%3s][%3s];   \t[%2d][%3s][%3s]"  % (
				        (L1_counter_init+1)&0b1111, i, H,
				        L1_counter,      ', '.join(map(str, l1hitlist)),       ', '.join(map(str, hiplist)))
				l1hitlistprev = l1hitlist
				hiplistprev   = hiplist
				L1_counter_init = L1_counter
				if (err[H]):
					counter[H][1] += 1
					fo.write(runname + ' ; ' + fstr + ' \n')
					print "\tError -> " + dstr + "                                  "
				else:
					if(display == True):
						print "\tOk    -> " + dstr + "                                  "
				if(display): utils.ShowPercent(counter[0], 240, "")
				else: utils.ShowPercent(counter[0][0]+counter[1][0], 240, "Running L1 test")
		fo.close()
		result = [ (1.0 - float(counter[0][1])/float(counter[0][0]))*100.0  ,  (1.0 - float(counter[1][1])/float(counter[1][0]))*100.0  ]
		#return "%5.2f%%" % (result)
		return result



	def memory(self, memory = 1, delay = [10], shift = 0, latency = 199, display = 1, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		HIP = memory-1
		fo = open("../SSA_Results/" + file + "_Test_Memory_" + str(memory) + ".csv", filemode)
		#self.ssa.init(reset_board = False, reset_chip = False, display = False)
		self.ssa.ctrl.set_sampling_deskewing_coarse(value = 0)
		self.ssa.ctrl.set_sampling_deskewing_fine(value = 0, enable = True, bypass = True)
		self.ssa.readout.l1_data(initialise = True, shift = shift, latency = latency, multi = False)
		self.ssa.inject.digital_pulse(initialise = True)
		self.fc7.write("cnfg_fast_tp_fsm_fast_reset_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
		self.fc7.write("cnfg_fast_tp_fsm_l1a_en", 1)
		errlist = []
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
				#	print "\tCounter Error -> " + dstr + "                                  "
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
						print "\tMemory Error  -> " + dstr + "                                  "
				elif(display >= 2):
					print "\tOk            -> " + dstr + "                                  "
				cnt[0] += 1
		eff = ((1-(cnt[1]/float(cnt[0])))*100 )
		fo.write( "\n%s ; %7.2f%% ; %s ;" % (runname, eff, '; '.join(map(str, errlist)) ))
		fo.close()
		self.memerrlist = errlist
		return eff

	def memory_vs_voltage(self, memory = 1, step = 0.005, start = 1.25, stop = 0.9, latency = 200, shift = 0, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		fo = open("../SSA_Results/" + file + "_Test_Memory-Supply_" + str(memory) + ".csv", filemode)
		fo.write("\n    RUN ; DVDD;       EFFICIENCY;    ERROR LIST; \n")
		for dvdd in np.arange(start, stop, -step):
			self.pwr.set_dvdd( dvdd )
			rt = self.ssa.init(reset_board = True, reset_chip = False, display = False) #alignement
			if not rt:
				eff = 0; erlist = [];
			eff = self.memory(memory = memory, display = 0, latency = latency, shift = shift)
			erlist = self.memerrlist
			fo.write("%8s ; %4.3fV ;     %7.2f%% ;       %s ; \n" % (runname, dvdd, eff, erlist))
			print "->  \t%4.3fV ;  %7.2f%% ;" % (dvdd, eff)
			if eff == 0:
				break
		fo.close()


	def mem_test_gen(self, init = True, patternL = range(10,90,10), patternH = [30,40,50], sequence = 0xff, npulses = 1, shift = 0, delay = 10, l1_duration = 2, calpulse_duration = 1, latency = 0, fc_resync = 1, fc_test = 1, fc_l1 = 1, clean = True, display = False, display_raw = False, delay_before_next_pulse = 1, delay_between_consecutive_trigeers = 1):
		latency = latency + 2
		if clean:
			self.ssa.init(reset_board = True, reset_chip = False, display = False)
		if init:
			self.ssa.ctrl.activate_readout_normal()
			self.I2C.strip_write("DigCalibPattern_L", 0, 0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0)
			self.I2C.peri_write('L1-Latency_MSB', 0)
			self.I2C.peri_write('L1-Latency_LSB', latency)
			self.I2C.peri_write("CalPulse_duration", calpulse_duration)
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
			self.fc7.write("ctrl_fast_signal_duration", l1_duration) ### doesn't work
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
		print dstr
		#return dstr


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
#		utils.activate_I2C_chip()
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
#		print dstr

	def _generate_clusters(self, nclusters, min_clsize = 1, max_clsize = 4):
		hit = []; c = []; exc = [];
		for i in range(nclusters):
			size = random.sample(range(min_clsize, max_clsize), 1)[0]
			rangelist = list( set(range(1, 80-size)) - set(exc) )
			adr = random.sample(rangelist, 1)[0]
			cll = range(adr, adr+size)
			hit += cll
			c.append( np.mean(cll) )
			exc += range(min(cll)-max_clsize-1, max(cll)+2)
		hit.sort()
		c.sort()
		return hit, c


	def force_alinament(self, maxtime = 5*60):
		time_init = time.time()
		while ((time.time()-time_init) < maxtime):
			print '________________________________'
			rt = self.cluster_data(nruns = 50, stop_on_error = True)
			if(rt==100):
				rt1 = self.cluster_data(nruns = 1000, stop_on_error = True)
				if rt == 100: break
				fc7.write("ctrl_phy_fast_cmd_phase",3)
			else:
				fc7.write("ctrl_phy_fast_cmd_phase",24)
			print 'SHIFT = 20'
			print rt

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
			print('->  \t{0:5.3f}V -> {1:5.2f}'.format(tmp[0], tmp[1]*100.0))
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
		print striplist
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

	def measure_dynamic_power(self, NHits = 5, L1_rate = 1000, display_errors = False, slvs_current=7):
		self.striplist = random.sample([item for item in range(0,61) if item not in self.striplist], NHits)
		#self.striplist = random.sample(range(0,60), NHits)
		striplist = list(np.sort(self.striplist)*2)
		#print self.striplist
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

	def power_vs_occupancy(self, L1_rate = 1000, display_errors = False, slvs_current = 7):
		#self.pwr.set_supply(mode='on', d=DVDD, a=AVDD, p=PVDD, bg = 0.270, display = True)
		I = []
		for nclusters in range(0,32,1):
			[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip] = self.measure_dynamic_power(NHits = nclusters, L1_rate = L1_rate, display_errors = display_errors, slvs_current=slvs_current)
			I.append([nclusters, Id, Ia, Ip])
			print("->\tN Clusters %5.1f  -> Current = %7.3f - %7.3f - %7.3f" % (nclusters/2.0, Id, Ia, Ip ))
		return I


'''
def prova(i):
	ssa.inject.digital_pulse([i])
	r = ssa.readout.cluster_data(initialize = False)
	if([i] != r): print 'error ' + str(i) + '  ' +str(r)



while 1:
	for i in range(1,121): prova(i)
'''
