import time
import sys
import inspect
import numpy as np
import matplotlib.pyplot as plt
import ctypes
from itertools import groupby
from operator import itemgetter

from utilities.tbsettings import *
from utilities.fc7_daq_methods import *
#from d19cScripts.MPA_SSA_BoardControl import *
#from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *


class SSA_SEU_utilities():

	''' Top Methods:
		> Run_Test_SEU()
		> Lateral_ReadFIFOs()
		> Stub_ReadFIFOs()
		> L1_ReadFIFOs()
	'''

	##############################################################
	def __init__(self, ssa, I2C, FC7, pwr):
		self.ssa = ssa; self.I2C = I2C; self.fc7 = FC7; self.pwr = pwr;
		self.seu_check_time = -1; self.last_test_duration = 0;

	##############################################################
	def Run_Test_SEU(self,
			check_stub=True, check_l1=True, check_lateral=False,
			strip =[10,20,30,40], centroids=[10,20,30,40], hipflags = [10,30], cal_pulse_period = 1, l1a_period = 39,
			latency = 101, run_time = 5, display = 1, filename = '', runname = '',
			delay = 74, create_errors = False, stop_if_fifo_full = True,
			read_seu_counter=True, delay_after_fast_reset=50, pattern3=0, show_every=1, reset_fc7=True, align=True, t1edge='falling'):

		CL_ok=0; L1_ok=0; LH_ok=0; iter_counter=0;

		while((CL_ok==0 or L1_ok==0 or LH_ok==0) and iter_counter<3):
			if(iter_counter!=0):
				utils.print_warning('->  Reiterating test after just re-running the phase alignment on the FPGA. ')
				utils.print_warning('    It seems to be the usual firmware alignment issue.')

			results = self.run_seu_test(
				check_stub=check_stub, check_l1=check_l1, check_lateral=check_lateral, create_errors = create_errors,
				strip = strip, centroids=centroids, hipflags = hipflags, delay = delay, run_time = run_time,
				cal_pulse_period = cal_pulse_period, l1a_period = l1a_period, latency = latency, t1edge=t1edge,
				display = display, stop_if_fifo_full = stop_if_fifo_full, reset_fc7=reset_fc7, align=align)

			[CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, fc7_alignment_status]  = results
			iter_counter += 1
		return results

	##############################################################
	def run_seu_test(self,
			check_stub=True, check_l1=True, check_lateral=False,
			strip =[10,20,30,40], centroids=[10,20,30,40], hipflags = [10,30], cal_pulse_period = 1, l1a_period = 39,
			latency = 101, run_time = 5, display = 1, filename = '', runname = '',
			delay = 74, create_errors = False, stop_if_fifo_full = True,
			read_seu_counter=True, delay_after_fast_reset=50, pattern3=0, show_every=1, reset_fc7=True, align=True, t1edge='falling'):

		if(reset_fc7): self.fc7.SendCommand_CTRL("global_reset");    time.sleep(0.1);
		self.fc7.SendCommand_CTRL("fast_fast_reset"); time.sleep(0.1);
		self.fc7.write("fc7_daq_ctrl.fast_command_block", 0x10000)
		if(align): self.ssa.init(edge = t1edge, display = True)
		self.ssa.resync()
		fc7_alignment_status = self.fc7.get_lines_alignment_status()
		#print(tbconfig.VERSION['SSA'])

		s1, s2, s3 = self.Stub_Evaluate_Pattern(strip)
		p1, p2, p3, p4, p5, p6, p7 = self.L1_Evaluate_Pattern(strip, hipflags)

		self.Configure_Injection(
			strip_list = strip, hipflag_list = hipflags, analog_injection = 0,
			latency = latency, create_errors = create_errors)

		self.Stub_loadCheckPatternOnFC7(pattern1 = s1, pattern2 = s2, pattern3 = 1, lateral = s3, display = display)

		self.L1_loadCheckPatternOnFC7(p1, p2, p3, p4, p5, p6, p7, display = display)
		 # Configure_SEU(cal_pulse_period, l1a_period, number_of_cal_pulses = 0, initial_reset = 1)
		 # Configure_SEU(1, 39,0,1)
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 1) #1
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", cal_pulse_period)
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.seu_ntriggers_to_skip", l1a_period)
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", 0)
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", delay_after_fast_reset)
		time.sleep(0.01); self.fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 9)
		time.sleep(0.01); self.fc7.write('cnfg_fast_timeout_enable', 0)
		time.sleep(0.1);  self.fc7.SendCommand_CTRL("load_trigger_config")
		time.sleep(0.1)
		time.sleep(0.01); self.fc7.write('cnfg_fast_timeout_enable', 0)

		self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
		self.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", delay)

		test_duration, fifo_full_stub, fifo_full_L1 = self.RunStateMachine_L1_and_Stubs(
			check_stub=check_stub, check_l1=check_l1, check_lateral=check_lateral,
			timer_data_taking=run_time, display=display, stop_if_fifo_full=stop_if_fifo_full, show_every=show_every)

		correction = int(latency/(l1a_period+1))
		if(display==0): display=1
		CL_ok, CL_er = self.Stub_printinfo(display = display, header = 1, message = "SUMMARY", logmode='info')
		LA_ok, LA_er = self.Lateral_printinfo(display = 0, logmode='info', enable=check_lateral)
		L1_ok, L1_er, LH_ok, LH_er = self.L1_printInfo(display = display, correction = correction)
		if(CL_er==0): utils.print_good('->  Stub data comparison  -> No errors due to SEEs')
		else:      utils.print_warning('->  Stub data comparison  -> Found errors due to SEEs')
		if(L1_er==0): utils.print_good('->  L1 data comparison    -> No errors due to SEEs')
		else:      utils.print_warning('->  L1 data comparison    -> Found errors due to SEEs')
		if(LH_er==0): utils.print_good('->  L1 headers comparison -> No errors due to SEEs')
		else:        utils.print_error('->  L1 headers comparison -> Found errors due to SEEs')
		return [CL_ok, LA_ok, L1_ok, LH_ok, CL_er, LA_er, L1_er, LH_er, test_duration, fifo_full_stub, fifo_full_L1, fc7_alignment_status]

	##############################################################
	def last_test_duration(self):
		return self.last_test_duration

	##############################################################
	def RunStateMachine_L1_and_Stubs(self, check_stub=True, check_l1=True, check_lateral=True, timer_data_taking = 30, display = 2, stop_if_fifo_full = True, show_every=1):
		time.sleep(0.1)
		FSM = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		time.sleep(0.01); self.fc7.write('cnfg_fast_timeout_enable', 0)
		if(display > 1):
			print("State of FSM before starting: "   + str( FSM))
			print("Almost full flag of FIFO before starting: "   + str( self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")))
		if (FSM == 4):
			print("Error in FSM")
			return
		if(check_l1):
			self.fc7.write("ctrl_phy_l1_SLVS_compare_start",1)
		if(check_stub):
			self.fc7.write("ctrl_phy_SLVS_compare_start",1)
		timer_init = time.time()
		self.fc7.SendCommand_CTRL("start_trigger")
		state = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		FIFO_almost_full_stub = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		if(display > 1):
			print("State of FSM after starting: "   + str( state ))
			print("Almost full flag of FIFO after starting: "   + str( FIFO_almost_full ))
		#start taking data and check the 80% full threshold of the FIFO
		FIFO_almost_full_stub = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		FIFO_almost_full_L1   = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
		timer = 0
		timer_prev = 0
		stop_condition = True
		while(stop_condition):
			time.sleep(0.01) # to check condition more or less every 10 ms
			timer = time.time()-timer_init
			message = "Time: {:3.3f}s / {:3.3f}".format(timer, timer_data_taking)
			FIFO_almost_full_stub = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			FIFO_almost_full_L1 = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")

			if(stop_if_fifo_full):
				stop_condition_stub = ((FIFO_almost_full_stub == 1) and check_stub)
				stop_condition_l1 = ((FIFO_almost_full_L1 == 1) and check_l1)
				stop_condition = ((not stop_condition_stub) and (not stop_condition_l1) and (timer < timer_data_taking))
			else:
				stop_condition = (timer < timer_data_taking)

			if(show_every>0):
				if((timer-timer_prev)>=show_every):
					timer_prev = timer
					self.print_all_info(
						check_stub=check_stub, check_l1=check_l1, check_lateral=check_lateral,
						message=message, display=display, header=1)
					seucounter = self.ssa.ctrl.read_seu_counter(display=True, printmode='log', sync=1, async=0)

		self.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.stop",1)
		timer = time.time()-timer_init
		self.fc7.SendCommand_CTRL("stop_trigger")
		if(show_every>0):
			self.print_all_info(
				check_stub=check_stub, check_l1=check_l1, check_lateral=check_lateral,
				message=message, display=display, header=1)
		#time.sleep(0.1); self.fc7.SendCommand_CTRL("stop_trigger")
		#print("State of FSM after stopping: " , self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
		if(display>-1):
			utils.print_log("________________________________________________________________________________________\n")
			if(timer >= timer_data_taking and FIFO_almost_full_stub == 0):
				utils.print_good("->  STUB DATA: data taking stopped because reached the adequate time")
				utils.print_good("->  L1 DATA:   data taking stopped because reached the adequate time")
			elif(FIFO_almost_full_stub == 1 and FIFO_almost_full_L1 == 0 and timer < timer_data_taking ):
				utils.print_warning("->  STUB DATA: data taking stopped because the STUB DATA FIFO is full")
				utils.print_warning("->  L1 DATA:   data taking stopped because the STUB DATA FIFO is full")
			elif(FIFO_almost_full_stub == 0 and FIFO_almost_full_L1 == 1 and timer < timer_data_taking ):
				utils.print_warning("->  STUB DATA: data taking stopped because the L1 DATA FIFO is full")
				utils.print_warning("->  L1 DATA:   data taking stopped because the L1 DATA FIFO is full")
			elif(FIFO_almost_full_stub == 1 and FIFO_almost_full_L1 == 1 and timer < timer_data_taking ):
				utils.print_warning("->  STUB DATA: data taking stopped because the both STUB and L1 DATA FIFO reached the 80%")
				utils.print_warning("->  L1 DATA:   data taking stopped because the both STUB and L1 DATA FIFO reached the 80%")
			else:
				utils.print_error("->  STUB DATA: data taking stopped because the FIFO is full and the timer also just reached the last step (something really strange)")
				utils.print_error("->  L1 DATA:   data taking stopped because the FIFO is full and the timer also just reached the last step (something really strange)")
		return timer, FIFO_almost_full_stub, FIFO_almost_full_L1

	##############################################################
	def Configure_Injection(self, strip_list = [], hipflag_list = [], lateral = [], analog_injection = 0, latency = 100, create_errors = False):
		strip_list = np.sort(strip_list)
		hipflag_list = np.sort(hipflag_list)
		#here define the way to generate stub/centroid data pattern on the MPA/SSA
		utils.activate_I2C_chip(self.fc7)
		self.ssa.ctrl.activate_readout_normal(mipadapterdisable = 1)
		self.ssa.ctrl.set_cal_pulse_duration(duration = 1)
		#time.sleep(0.01); self.I2C.strip_write("ENFLAGS", 0, 0b01001)
		if(tbconfig.VERSION['SSA'] >= 2):
			self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip='all', data=0b00000)
			self.I2C.strip_write(register="DigCalibPattern_L", field=False, strip='all', data=0x0)
			self.I2C.strip_write(register="DigCalibPattern_H", field=False, strip='all', data=0x0)
			self.I2C.peri_write( register="control_1", field='L1_Latency_msb', data = ((latency & 0x0100)>>8) )
			self.I2C.peri_write( register="control_3", field='L1_Latency_lsb', data = ((latency & 0x00ff)>>0) )
		else:
			self.I2C.strip_write("ENFLAGS", 0, 0b00000)
			self.I2C.strip_write("DigCalibPattern_L", 0, 0x0)
			self.I2C.strip_write("DigCalibPattern_H", 0, 0x0)
			self.I2C.peri_write('L1_Latency_msb', (latency & 0xff00) >> 8)
			self.I2C.peri_write('L1_Latency_lsb', (latency & 0x00ff) >> 0)
		#SetLineDelayManual(0, 0, 9, 0, 2)
		#SetLineDelayManual(0, 0,10, 0, 2)
		word = np.zeros(16, dtype = np.uint8)
		row = np.zeros(16, dtype = np.uint8)
		pixel = np.zeros(16, dtype = np.uint8)
		l = np.zeros(10, dtype = np.uint8)
		for st in strip_list:
			if(st>0 and st<121):
				if(tbconfig.VERSION['SSA'] >= 2):
					self.I2C.strip_write(register="StripControl1", field='ENFLAGS', strip=st, data=0b01001)
					self.I2C.strip_write( register="DigCalibPattern_L", field=False, strip=st, data=0b00000001)
				else:
					self.I2C.strip_write("ENFLAGS", st, 0b01001)
					self.I2C.strip_write("DigCalibPattern_L", st, 0x1)
		for st in hipflag_list:
			if(st>0 and st<121):
				self.I2C.strip_write("DigCalibPattern_H", st, 0x1)

		#### injet strip reset error case
		if(create_errors):
			for i in range(81, 89):
				if(tbconfig.VERSION['SSA'] >= 2):
					self.I2C.strip_write( register="StripControl1",     field='ENFLAGS', strip=i, data=0b00101)
					self.I2C.strip_write( register="DigCalibPattern_L", field=False,     strip=i, data=170)
					self.I2C.strip_write( register="DigCalibPattern_H", field=False,     strip=i, data=170)
				else:
					self.I2C.strip_write("ENFLAGS", i, 0b00101)
					self.I2C.strip_write("DigCalibPattern_L", i, 170)
					self.I2C.strip_write("DigCalibPattern_H", i, 170)
		time.sleep(0.01)
		self.ssa.ctrl.set_all_config_masks(0x00, 0x00, 0x00)


	##############################################################
	def Stub_Evaluate_Pattern(self, strip_list, cluster_cut = 5):
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
		#### print(slist)
		#### Formatting
		p1 = (slist[0]<<0) | (slist[1]<<8) | (slist[2]<<16) | (slist[3]<<24)
		p2 = (slist[4]<<0) | (slist[5]<<8) | (slist[6]<<16) | (slist[7]<<24)
		p3 = ((lateral_right & 0xFF) << 8) + (lateral_left & 0xFF)
		return p1, p2, p3


	##############################################################
	def L1_Evaluate_Pattern(self, strip_list = [3,7,12,13,18], hflag_list = [3,7,12,13,18], display=0):
		strip = np.sort(strip_list[0:8])
		hfleg = np.sort(hflag_list)
		l1hit  = np.full(120, '0')
		l1flag = np.full( 24, '0')
		for st in strip:
			l1hit[ st-1 ] = '1'
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
		if(tbconfig.VERSION['SSA'] >= 2):
			p1 = 0x00000000
			#p2 = 0x00000000
			#p3 = int( '0b' + ( ''.join((l1hit[0:26])[::-1])  + '111100'    ) , 2)
			#p4 = int( '0b' + ( ''.join((l1hit[26:58])[::-1])  ) , 2)
			#p5 = int( '0b' + ( ''.join((l1hit[58:90])[::-1])  ) , 2)
			#p6 = int( '0b' + ( ''.join((l1flag[0:2])[::-1])   + ''.join((l1hit[90:120])[::-1])  ) , 2)
			#p7 = int( '0b' + ( '0'*6 + ''.join((l1flag[2:24])[::-1])  ) , 2)
			p2 = int( '0b' + ( '11' + '0'*30    ) , 2)
			p3 = int( '0b' + ( ''.join((l1hit[0:30])[::-1])  + '11'    ) , 2)
			p4 = int( '0b' + ( ''.join((l1hit[30:62])[::-1])  ) , 2)
			p5 = int( '0b' + ( ''.join((l1hit[62:94])[::-1])  ) , 2)
			p6 = int( '0b' + ( ''.join((l1flag[0:6])[::-1])   + ''.join((l1hit[94:120])[::-1])  ) , 2)
			p7 = int( '0b' + ( '0'*10 + ''.join((l1flag[6:24])[::-1])  ) , 2)
		else:
			p1 = 0x00000000
			p2 = 0x00000000
			p3 = int( '0b' + ( ''.join((l1hit[0:30])[::-1])  + '10'    ) , 2)
			p4 = int( '0b' + ( ''.join((l1hit[30:62])[::-1])  ) , 2)
			p5 = int( '0b' + ( ''.join((l1hit[62:94])[::-1])  ) , 2)
			p6 = int( '0b' + ( ''.join((l1flag[0:6])[::-1])   + ''.join((l1hit[94:120])[::-1])  ) , 2)
			p7 = int( '0b' + ( '0'*10 + ''.join((l1flag[6:24])[::-1])  ) , 2)
			#if(display>3):
		#print("{:32b}-{:32b}-{:32b}-{:32b}-{:32b}-{:32b}-{:32b}".format(p7, p6, p5, p4, p3, p2, p1))
		return p1, p2, p3, p4, p5, p6, p7


	##############################################################
	def Stub_loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, lateral = 0, display = 2):
		self.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns1",pattern1); time.sleep(0.01)
		self.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns2",pattern2); time.sleep(0.01)
		self.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",pattern3); time.sleep(0.01)
		self.fc7.write("cnfg_phy_lateral_MPA_SSA_SEU_check_patterns1",lateral); time.sleep(0.01)
		###### time.sleep(0.5)
		if(display>1):
			utils.print_log("->  Content of the patterns1 cnfg register: " + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns1"))))
			utils.print_log("->  Content of the patterns2 cnfg register: " + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns2"))))
			utils.print_log("->  Content of the patterns3 cnfg register: " + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_MPA_SSA_SEU_check_patterns3"))))


	##############################################################
	def Stub_delayDataTaking(self, display = 2):
		#below register can be used to check in which BX the centroid data is coming (even or odd) and can be used later in "self.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)" to configure if the state machine has to wait 1 clk cycle
		if(display>1):
			print("BX indicator for SSA centroid data:" + str(self.fc7.read("stat_phy_slvs_compare_fifo_bx_indicator")))
		#self.fc7.write("cnfg_phy_MPA_SSA_SEU_check_patterns3",0 or 1)
		time.sleep(1)

	##############################################################
	def Stub_RunStateMachine(self, display = 2, run_time = 10):
		FSM = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		if(display>1): print("  \tState of FSM before starting: " + str(FSM))
		if (FSM == 4):
			print("-X  \tError in FSM")
			return
		rp = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		if(display>1):
			print("->  Almost full flag of FIFO before starting: " + str( rp ))
		self.fc7.write("ctrl_phy_SLVS_compare_start",1)
		state = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")
		full = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		if(display>1):
			print("->  State of FSM after starting: " + str(state))
			print("->  Almost full flag of FIFO after starting: " + str(full))
		self.fc7.SendCommand_CTRL("start_trigger")
		timer = 0
		FIFO_almost_full = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
		while(FIFO_almost_full != 1 and timer < run_time):
			FIFO_almost_full = self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")
			timer = timer + 1
			if(display>0):
				self.Stub_printinfo(display = display, header = 1)
				self.Lateral_printinfo(display = display)
			time.sleep(1)
		if(display>0): print("____________________________________________________________________________")
		self.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.stop",1)
		if(display>1): print("State of FSM after stopping: " + str(self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")))
		if(timer == run_time and FIFO_almost_full == 0):
			utils.print_log("->  SEU Stub-Data     -> data taking stopped because reached the adequate time")
		elif(self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare_number_good_data") > (2**31-3)):
			utils.print_log("->  SEU Stub-Data     -> data taking stopped because reached the good-clusters counter size")
		elif(FIFO_almost_full == 1 and timer < run_time ):
			utils.print_log("-X  \tSEU Stub-Data     -> data taking stopped because the FIFO reached the 80%")
		else:
			utils.print_log("-X  \tSEU Stub-Data     -> data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)")


	##############################################################
	def Lateral_ReadFIFOs(self, nevents = 'all', filename = "SEU_TMP/SEU", runname = '', display = 0):
		print("State of FSM before reading FIFOs: " + str(self.fc7.read("stat_phy_lateral_slvs_compare_state_machine")))
		stat_phy_slvs_compare_data_ready = self.fc7.read("stat_phy_lateral_slvs_compare_data_ready")
		FIFO = np.full( [16386,3],'', dtype ='|S32')
		if(not isinstance(nevents, int)):
			FIFO_depth = self.fc7.read("stat_phy_lateral_slvs_compare_numbere_events_written_to_fifo")
		else:
			FIFO_depth = nevents
		for i in range(0, FIFO_depth):
				fifo1_word = self.fc7.read("ctrl_phy_lateral_SLVS_compare_read_data1_fifo")
				fifo2_word = self.fc7.read("ctrl_phy_lateral_SLVS_compare_read_data2_fifo")
				FIFO[i,0]  = (fifo2_word)
				FIFO[i,1]  = self.parse_to_bin32((fifo1_word & 0x00ff) >> 0)
				FIFO[i,2]  = self.parse_to_bin32((fifo1_word & 0xff00) >> 8)
				if(display):
					print("--------------------------")
					print("Entry number: ", i ," in the FIFO:")
					print(self.parse_to_bin32(fifo2_word) + self.parse_to_bin32(fifo1_word))
					print(str(fifo2_word) + str(fifo1_word))
					print("BX counter:" + str(fifo1_word))
					print("SSA Lateral 1: " + str(FIFO[i,1]))
					print("SSA Lateral 2: " + str(FIFO[i,2]))
		print("State of FSM after reading FIFOs: "  + str( self.fc7.read("stat_phy_lateral_slvs_compare_state_machine") ))
		print("Fifo almost full: " + str( self.fc7.read("stat_phy_lateral_slvs_compare_fifo_almost_full") ))
		fo = ("../SSA_Results/" + filename + "__SEU__LATERAL-FIFO__" + runname + ".csv")
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir): os.makedirs(dir)
		CSV.ArrayToCSV(FIFO, fo)


	##############################################################
	def Stub_ReadFIFOs(self, nevents = 'all', filename = "SEU_TMP/SEU", runname = '', display = 0):
		utils.print_info("->  Reading stub-data mismatches FIFO")
		if(display>1): print("State of FSM before reading FIFOs: "  + str(self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")))
		stat_phy_slvs_compare_data_ready = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.data_ready")
		FIFO = np.full( [16386,10], np.NaN)
		if(not isinstance(nevents, int)):
			FIFO_depth = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
		else:
			FIFO_depth = nevents
		for i in range(0, FIFO_depth):
				fifo1_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data1_fifo")
				fifo2_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data2_fifo")
				fifo3_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data3_fifo")
				fifo4_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.slvs_compare_read_data4_fifo")
				FIFO[i,0]  = fifo4_word #BX
				FIFO[i,8]  = (fifo2_word & 0xff000000)>>24
				FIFO[i,7]  = (fifo2_word & 0x00ff0000)>>16
				FIFO[i,6]  = (fifo2_word & 0x0000ff00)>>8
				FIFO[i,5]  =  fifo2_word & 0x000000ff
				FIFO[i,4]  = (fifo1_word & 0xff000000)>>24
				FIFO[i,3]  = (fifo1_word & 0x00ff0000)>>16
				FIFO[i,2]  = (fifo1_word & 0x0000ff00)>>8
				FIFO[i,1]  = (fifo1_word & 0x000000ff)
				if(display > 0):
					print("--------------------------")
					print("Entry number: ", i ," in the FIFO:")
					print(self.parse_to_bin32(fifo4_word), self.parse_to_bin32(fifo3_word), self.parse_to_bin32(fifo2_word), self.parse_to_bin32(fifo1_word))
					print(fifo4_word, fifo3_word, fifo2_word, fifo1_word)
					print("BX counter:" + str( fifo4_word))
					print("SSA centroid l7: " + str( FIFO[i,8] ))
					print("SSA centroid l6: " + str( FIFO[i,7] ))
					print("SSA centroid l5: " + str( FIFO[i,6] ))
					print("SSA centroid l4: " + str( FIFO[i,5] ))
					print("SSA centroid l3: " + str( FIFO[i,4] ))
					print("SSA centroid l2: " + str( FIFO[i,3] ))
					print("SSA centroid l1: " + str( FIFO[i,2] ))
					print("SSA centroid l0: " + str( FIFO[i,1] ))
		if(display>0):
			print("State of FSM after reading FIFOs: "  + str( self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine")))
			print("Fifo almost full: "  + str( self.fc7.read("stat_phy_slvs_compare_fifo_almost_full")))
		fo = ("../SSA_Results/" + filename + "__SEU__CLUSTER-FIFO__" + runname + ".csv")
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir): os.makedirs(dir)
		CSV.ArrayToCSV(FIFO, fo)

	#####################################################################################################################
	def L1_ReadFIFOs(self, nevents = 'all', filename = "SEU_TMP/SEU", runname = '', display = 0):
		#self.L1_printInfo("BEFORE READING FIFO:")
		utils.print_info("->  Reading L1-data mismatches FIFO")
		if(display>1): print("Now printing the data in the FIFO:")
		FIFO = np.full( [16386,7], '', dtype ='|S256')
		if(not isinstance(nevents, int)):
			FIFO_depth = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo")
		else:
			FIFO_depth = nevents
		for i in range(0, FIFO_depth):
				if(display>0): print("Entry number: ", i ," in the FIFO:")
				#it increments location of the FIFO reading fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo
				fifo1_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data1_fifo")
				fifo2_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data2_fifo")
				fifo3_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data3_fifo")
				fifo4_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data4_fifo")
				fifo5_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data5_fifo")
				fifo6_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data6_fifo")
				fifo7_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data7_fifo")
				fifo8_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data8_fifo")
				fifo9_word = self.fc7.read("fc7_daq_ctrl.physical_interface_block.l1_slvs_compare_read_data9_fifo")
				if(display>1):
					print("Full l1 data package without the header (MSB downto LSB): ")

				event_array = (
					self.parse_to_bin32(fifo7_word) + self.parse_to_bin32(fifo6_word) +
					self.parse_to_bin32(fifo5_word) + self.parse_to_bin32(fifo4_word) +
					self.parse_to_bin32(fifo3_word) + self.parse_to_bin32(fifo2_word) )

				#l1_counter  = '{:5d}'.format((fifo7_word>>22)&0x1ff)
				bx_counter  = fifo8_word & 0x1ff
				l1_counter  = int(event_array[1:10], 2)
				mirrow      = fifo9_word & 0x1ff
				flags_array = event_array[19:43]
				hits_array  = event_array[43:163]
				trailer     = event_array[163: 167]
				FIFO[i,0] = '{:5d}'.format(bx_counter) #BX
				FIFO[i,1] = '{:5d}'.format(mirrow) #mirrrow
				FIFO[i,2] = '{:5d}'.format(l1_counter) # (fifo7_word >>27) & 0xf
				FIFO[i,3] = '{:25s}'.format(flags_array)
				FIFO[i,4] = '{:121s}'.format(hits_array)
				FIFO[i,5] = '{:5s}'.format(trailer)
				FIFO[i,5] = '{:193s}'.format(event_array)

				if(display>0):
					#print("->  L1 counter  "  + str(  bin(fifo7_word)  ))
					#print("->  L1 mirrow:  "  + str(  bin(fifo9_word)  ))
					#print("->  BX counter: "  + str(  fifo8_word ))
					#print("->  Packet:     "  + str( FIFO[i,3] ))
					print("->  r9: "  + str(  self.parse_to_bin32(fifo9_word) )) #mirrrow
					print("->  r8: "  + str(  self.parse_to_bin32(fifo8_word) )) #BX
					print("->  r7: "  + str(  self.parse_to_bin32(fifo7_word) )) #L1 counter
					print("->  r6: "  + str(  self.parse_to_bin32(fifo6_word) ))
					print("->  r5: "  + str(  self.parse_to_bin32(fifo5_word) ))
					print("->  r4: "  + str(  self.parse_to_bin32(fifo4_word) ))
					print("->  r3: "  + str(  self.parse_to_bin32(fifo3_word) ))
					print("->  r2: "  + str(  self.parse_to_bin32(fifo2_word) ))
					print("->  r1: "  + str(  self.parse_to_bin32(fifo1_word) ))
		fo = ("../SSA_Results/" + filename + "__SEU__L1-DATA-FIFO__" + runname + ".csv")
		dir = fo[:fo.rindex(os.path.sep)]
		if not os.path.exists(dir): os.makedirs(dir)
		CSV.ArrayToCSV(FIFO, fo)
		#self.L1_printInfo("AFTER READING FIFO:")


	#####################################################################################################################
	def L1_phase_tuning_MPA_emulator(self):
		time.sleep(0.1)
		self.fc7.write("fc7_daq_ctrl.physical_interface_block.control.cbc3_tune_again", 1)
		count_waiting = 0
		while(self.fc7.read("fc7_daq_ctrl.physical_interface_block.phase_tuning_ctrl_done") == 0):
			time.sleep(0.5)
			print("Phase tuning in state: "  + str( self.fc7.read("stat_phy_phase_fsm_state_chip0") ))
			print("Waiting for the phase tuning")
			self.fc7.write("fc7_daq_ctrl.physical_interface_block.control.cbc3_tune_again", 1)
			print("resend phase tuning signal")


	##############################################################
	def L1_loadCheckPatternOnFC7(self, pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, display):
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1",pattern1)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2",pattern2)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3",pattern3)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4",pattern4)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5",pattern5)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6",pattern6)
		self.fc7.write("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7",pattern7)
		##### time.sleep(0.5)
		if(display > 1):
			utils.print_log("->  Content of the patterns7 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns7")) ))
			utils.print_log("->  Content of the patterns6 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns6")) ))
			utils.print_log("->  Content of the patterns5 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns5")) ))
			utils.print_log("->  Content of the patterns4 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns4")) ))
			utils.print_log("->  Content of the patterns3 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns3")) ))
			utils.print_log("->  Content of the patterns2 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns2")) ))
			utils.print_log("->  Content of the patterns1 cnfg register: "  + str( self.parse_to_bin32(self.fc7.read("cnfg_phy_l1_MPA_SSA_SEU_check_patterns1")) ))


	##############################################################
	def L1_printInfo(self, message = '', display = 2, header = 0, correction = 0, intermediate=0):
		state      = self.fc7.read("stat_phy_l1_slvs_compare_state_machine")
		full       = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
		n_in_fifo  = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo") - correction
		n_correct  = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_good_data")
		n_triggers = self.fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers") - 1
		n_headers  = self.fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")

		if(intermediate):
			logmode = 'log'
			n_in_fifo -= 2
		else:
			logmode = 'info'
		trig_diff = n_triggers-n_headers
		if(trig_diff==(-1)): trig_diff=0
		if(header and display>0):
			utils.print("________________________________________________________________________________________", logmode)
		if(display==2):
			utils.print("->  SEU L1-Data       -> State of FSM:       %12d "           % (state), logmode)
			utils.print("->  SEU L1-Data       -> Full Flag:          %12d "           % (full), logmode)
			utils.print("->  SEU L1-Data       -> Correct events:     %12d (%10.6f%%)" % (n_correct, 100*np.float(n_correct)/(n_triggers)), logmode)
			utils.print("->  SEU L1-Data       -> Packets with Error: %12d (%10.6f%%)" % (n_in_fifo,  100*np.float(n_in_fifo)/(n_triggers)), logmode)
			utils.print("->  SEU L1-Data       -> Packets Missing:    %12d (%10.6f%%)" % ((trig_diff),  (100*np.float(trig_diff))/n_triggers), logmode)
		elif(display==1):
			utils.print("->  SEU L1-Data       -> %12d (%10.6f%%)  |  %12d (%10.6f%%)" % (n_correct, (100*np.float(n_correct)/(n_correct+n_in_fifo+1E-9)), n_in_fifo,  (100*np.float(n_in_fifo)/(n_correct+n_in_fifo+1E-9)) ), logmode)
			utils.print("->  SEU L1-Headers    -> %12d (%10.6f%%)  |  %12d (%10.6f%%)" % (n_headers, 100*(1-np.float(trig_diff)/(n_triggers+1E-9)) , (n_triggers - n_headers), 100*(np.float(n_triggers - n_headers)/(n_triggers+1E-9)) ) , logmode)
		return [n_correct, n_in_fifo, n_headers, (trig_diff)]

	##############################################################
	def Stub_printinfo(self, message = '', display = 2, header = 0, logmode='log'):
		CntBad  = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
		CntGood = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare_number_good_data")
		state   = (self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.state_machine"))
		full    = (self.fc7.read("stat_phy_slvs_compare_fifo_almost_full"))
		if(header and display>0):
			utils.print("________________________________________________________________________________________", logmode)
			utils.print("%18s                      CORRECT                         ERROR " % message, logmode)
		if(display==2):
			utils.print("->  SEU Stub-Data     -> State of FSM:      %12d" % (state), logmode)
			utils.print("->  SEU Stub-Data     -> FIFO almost full:  %12d" % (full), logmode)
			utils.print("->  SEU Stub-Data     -> Number of good BX: %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad)), logmode)
			utils.print("->  SEU Stub-Data     -> Number of bad  BX: %12d (%10.6f%%)" % (CntBad,  100*np.float(CntBad)/(CntGood+CntBad)), logmode)
		elif(display==1):
			utils.print("->  SEU Stub-Data     -> %12d (%10.6f%%)  |  %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad+1E-9), CntBad,  100*np.float(CntBad)/(CntGood+CntBad+1E-9)), logmode)
		return [CntGood, CntBad]


	##############################################################
	def Lateral_printinfo(self, display = 2, header = 0, logmode='log', enable=True):
		if(enable):
			CntBad  = self.fc7.read("stat_phy_lateral_slvs_compare_numbere_events_written_to_fifo")
			CntGood = self.fc7.read("stat_phy_lateral_slvs_compare_number_good_data")
			state   = self.fc7.read("stat_phy_lateral_slvs_compare_state_machine")
			full    = self.fc7.read("stat_phy_lateral_slvs_compare_fifo_almost_full")
			if(header and display>0):
				utils.print("________________________________________________________________________________________")
			if(display==2):
				utils.print("->  SEU Lateral-Data  -> State of FSM:      %12d" % (state), logmode)
				utils.print("->  SEU Lateral-Data  -> FIFO almost full:  %12d" % (full), logmode)
				utils.print("->  SEU Lateral-Data  -> Number of good BX: %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad)), logmode)
				utils.print("->  SEU Lateral-Data  -> Number of bad  BX: %12d (%10.6f%%)" % (CntBad,  100*np.float(CntBad)/(CntGood+CntBad)), logmode)
			if(display==1):
				utils.print("->  SEU Lateral-Data  -> %12d (%10.6f%%)  |  %12d (%10.6f%%)" % (CntGood, 100*np.float(CntGood)/(CntGood+CntBad+1E-9), CntBad,  100*np.float(CntBad)/(CntGood+CntBad+1E-9)), logmode)
		else:
			CntGood	, CntBad = 0, 0
		return [CntGood, CntBad]

	##############################################################
	def print_all_info(self, check_stub=True, check_l1=True, check_lateral=True, message = '', display = 2, header = 1):
		if(check_stub):
			self.Stub_printinfo(display=display, header=header, message=message)
		if(check_lateral):
			self.Lateral_printinfo(display = display)
		if(check_l1):
			self.L1_printInfo(display = display, intermediate=1)

	##############################################################
	def L1_RunStateMachine(self, timer_data_taking = 5, display = 0):
		if(display > 1):
			self.L1_printInfo("BEFORE STATE MACHINE RUNNING:")
		self.fc7.write("ctrl_phy_l1_SLVS_compare_start",1)
		if(display > 1):
			self.L1_printInfo("AFTER START STATE MACHINE:")
		#start the triggering
		#Configure_Fast(0, 1000, 3, 0, 0)
		#self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable",0)
		#time.sleep(0.5)
		self.fc7.SendCommand_CTRL("start_trigger")
		if(display > 1):
			self.L1_printInfo("AFTER START TRIGGER:")
		#start taking data and check the 80% full threshold of the FIFO
		FIFO_almost_full = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
		timer = 0
		while(FIFO_almost_full != 1 and timer < timer_data_taking):
			FIFO_almost_full = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.fifo_almost_full")
			timer = timer + 1
			message =  "Timer at: ", timer, "/", timer_data_taking
			self.L1_printInfo(message)
			time.sleep(1)
		self.fc7.SendCommand_CTRL("stop_trigger")
		time.sleep(1)
		self.fc7.write("fc7_daq_ctrl.physical_interface_block.slvs_compare.stop",1)
		self.L1_printInfo("STATE MACHINE AND TRIGGER STOPPED:")
		if(timer == timer_data_taking and FIFO_almost_full == 0):
			utils.print_log("data taking stopped because reached the adequate time")
		elif(FIFO_almost_full == 1 and timer < timer_data_taking ):
			utils.print_log("data taking stopped because the FIFO reached the 80%")
		else:
			utils.print_log("data taking stopped because the FIFO is full and the timer also just reached the last step (really strange)")


	##############################################################
	def Run_Test_SEU_ClusterData_old(self, strip =[10,20,30,40,50,60,70], hipflags = [], delay_after_fast_reset = 0, run_time = 5, display = 1, filename = '', runname = '', delay = 70):
		self.fc7.SendCommand_CTRL("global_reset")
		p1, p2, p3 = self.Stub_Evaluate_Pattern(strip)
		time.sleep(0.1); self.Stub_loadCheckPatternOnFC7(pattern1 = p1, pattern2 = p2, pattern3 = 1, lateral = p3, display = display)
		time.sleep(0.1); self.Configure_Injection(strip_list = strip, hipflag_list = hipflags, analog_injection = 0)
		time.sleep(0.1); self.fc7.write("cnfg_phy_SSA_SEU_CENTROID_WAITING_AFTER_RESYNC", delay)
		time.sleep(0.1); Configure_TestPulse_SSA(delay_after_fast_reset = 0, delay_after_test_pulse = 1, delay_before_next_pulse = 0, number_of_test_pulses = 0, enable_rst_L1 = 0, enable_initial_reset = 1)
		time.sleep(0.1); self.Stub_delayDataTaking()
		time.sleep(0.1); self.Stub_RunStateMachine(run_time = run_time, display = display)
		time.sleep(0.1); self.fc7.SendCommand_CTRL("stop_trigger")
		time.sleep(0.1);
		CntBad  = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare.numbere_events_written_to_fifo")
		CntGood = self.fc7.read("fc7_daq_stat.physical_interface_block.slvs_compare_number_good_data")
		self.Stub_printinfo('SUMMARY', display = display, header = 1)
		self.Lateral_printinfo(display = display)
		return [CntGood, CntBad]


	##############################################################
	def Run_Test_SEU_L1_old(self, strip = [1,9,17,25,33,17,118,119,120], hipflags = [], run_time = 5, delay_after_fast_reset = 512, latency = 500, shift = 0, cal_pulse_period = 100, display = 1, filename = '', runname = '', delay = 71, cnt_shift = 0):
		chip = 'SSA'
		self.fc7.SendCommand_CTRL("global_reset")
		time.sleep(1)
		p1, p2, p3, p4, p5, p6, p7 = self.L1_Evaluate_Pattern(strip, hipflags)
		self.Configure_Injection(strip_list = strip, hipflag_list = hipflags, analog_injection = 0, latency = latency)
		self.L1_loadCheckPatternOnFC7(p1, p2, p3, p4, p5, p6, p7, display = display)
		#Configure_TestPulse_MPA(delay_after_fast_reset = 512, delay_after_test_pulse = latency+3+offset, delay_before_next_pulse = cal_pulse_period, number_of_test_pulses = 0, enable_rst_L1 = 1)
		#Configure_TestPulse_SSA(delay_after_fast_reset = delay_after_fast_reset,delay_after_test_pulse = latency+3+shift,	delay_before_next_pulse = cal_pulse_period,	number_of_test_pulses = 0,	enable_rst_L1 = 0,	enable_L1 = 1)
		self.fc7.SendCommand_CTRL('fast_fast_reset')
		time.sleep(0.1)
		for i in range(cnt_shift):
			send_trigger()
		self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", 0)
		self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 0 )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset",  delay_after_fast_reset )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse",   latency+3+shift )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse",  cal_pulse_period)
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset",  0 )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_test_pulse",  1)
		self.fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_l1a",  1 )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept",  0 )
		self.fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", 6)
		self.fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable",  0 )
		time.sleep(0.1)
		self.fc7.SendCommand_CTRL("load_trigger_config")
		time.sleep(0.1)
		self.L1_RunStateMachine(timer_data_taking = run_time)
		## self.fc7.SendCommand_CTRL("stop_trigger")
		#self.L1_ReadFIFOs(nevents = 5)878
		self.L1_printInfo('        SUMMARY        ')
		n_in_fifo  = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare.numbere_events_written_to_fifo")
		n_correct  = self.fc7.read("fc7_daq_stat.physical_interface_block.l1_slvs_compare_number_good_data")
		n_triggers = self.fc7.read("stat_phy_l1_slvs_compare_number_l1_triggers")
		n_headers  = self.fc7.read("stat_phy_l1_slvs_compare_number_l1_headers_found")
		return [n_correct, n_in_fifo, (n_triggers-n_headers)]

	##############################################################
	def parse_to_bin32(self, input):
		return bin(to_number(input,32,0)).lstrip('-0b').zfill(32)


	##############################################################
	def parse_to_bin8(self, input):
		return bin(to_number(input,8,0)).lstrip('-0b').zfill(8)

	##############################################################
	def parse_to_bin9(self, input):
		return bin(to_number(input,9,0)).lstrip('-0b').zfill(9)


# seuutil.L1_RunStateMachine()

#  seuutil.Run_Test_SEU_ClusterData()
#  seuutil.Stub_ReadFIFOs()

#  ssa.inject.digital_pulse([1,2,3,4,5, 116,117,118,119,120])
#
#  seuutil.Run_Test_SEU_L1(cal_pulse_period = 100)
#  seuutil.L1_ReadFIFOs(nevents = 10)
