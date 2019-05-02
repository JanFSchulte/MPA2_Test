from d19cScripts.fc7_daq_methods import *
from d19cScripts.MPA_SSA_BoardControl import *
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *

from ssa_methods.ssa_i2c_conf import *
from ssa_methods.ssa_ctrl_base import *
from ssa_methods.ssa_ctrl_strip import *
from ssa_methods.ssa_readout_utility import *
from ssa_methods.ssa_inject_utility import *


class SSA_ASIC:

	def __init__(self, I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map):
		self.i2c     = I2C
		self.ctrl    = ssa_ctrl_base(I2C, FC7, pwr, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.strip   = ssa_ctrl_strip(I2C, FC7, ssa_peri_reg_map, ssa_strip_reg_map, analog_mux_map)
		self.inject  = SSA_inject(I2C, FC7, self.ctrl, self.strip)
		self.readout = SSA_readout(I2C, FC7, self.ctrl, self.strip)
		self.pwr     = pwr
		self.fc7     = FC7
		self.generic_parameters = {}

	####### Initialize functions ###############

	def reset(self, display=True):
		self.ctrl.reset(display = display)

	def resync(self):
		self.ctrl.resync()

	def disable(self, display=True):
		self.pwr._disable_ssa(display = display)

	def enable(self, display=True):
		self.pwr._enable_ssa(display = display)

	def debug(self, value = True):
		self.i2c.set_debug_mode(value)
		self.i2c.set_readback_mode()

	def save_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.save_configuration(file = file, display = display)

	def load_configuration(self, file = '../SSA_Results/Configuration.csv', display=True):
		self.ctrl.load_configuration(file = file, display = display)

	def init(self, reset_board = False, reset_chip = False, slvs_current = 0b111, edge = "negative", display = True, read_current = False):
		self.generic_parameters['cl_word_alignment'] = False
		if(display):
			sys.stdout.write("->  \tInitialising..\r")
			sys.stdout.flush()
		if(reset_board):
			fc7.write("ctrl_command_global_reset", 1)
			sleep(0.3);
			if(display): utils.print_info("->  \tReset FC7 Firmware")
		if(reset_chip):
			self.ctrl.reset(display=False)
			sleep(0.3);
			if(display): utils.print_info("->  \tReset SSA Chip")
		utils.activate_I2C_chip()
		sleep(0.2)
		self.ctrl.set_lateral_data(left=0, right=0)
		if(display):
			sys.stdout.write("->  \tTuning sampling phases..\r")
			sys.stdout.flush()
		sleep(0.1); self.ctrl.set_t1_sampling_edge(edge)
		sleep(0.1); self.ctrl.init_slvs(slvs_current)
		sleep(0.1); rt = self.ctrl.phase_tuning()
		if(rt):
			if(display): utils.print_good("->  \tShift register mode ok")
			if(display): utils.print_good("->  \tSampling phases tuned")
		else:
			if(display): utils.print_error("->  \tImpossible to complete phase tuning")
		sleep(0.2); self.ctrl.activate_readout_normal()
		sleep(0.1); self.ctrl.activate_readout_normal()
		if(display):
			utils.print_info("->  \tActivated normal readout mode");
			sys.stdout.write("->  \tReady!                  \r")
			sys.stdout.flush()
			sleep(0.2)
			if(read_current):
				self.pwr.get_power(display = True)
		return rt

	def init_all(self):
		self.init(reset_board = True, reset_chip = False)


	####### Data alignment functions ################################

	def alignment_all(self, display = False):
		r1 = self.init(reset_board = True, reset_chip = False, display = display)
		r2 = self.alignment_cluster_data_word()
		r3, r4 = self.alignment_lateral_input()
		if(not(r1 and r2 and r3 and r4)):
			utils.print_error("X>\tAlignment error.")
		return r1,r2,r3,r4

	def alignment_cluster_data_phase(self):
		return self.ctrl.phase_tuning()

	def alignment_cluster_data_word(self, display=False):
		tv = [10,20,30,40,50,60,70,80]
		self.ctrl.set_lateral_data(left=0, right=0)
		status = {'digital':False, 'analog':False}
		for mode in ['digital', 'analog']:
			if(mode == 'digital'):
				self.inject.digital_pulse(initialise = True)
			elif(mode == 'analog'):
				self.inject.analog_pulse(initialise = True)
			self.readout.cluster_data(initialize = True)
			for shift in range(-5,6):
				ext = False
				self.readout.cl_shift[mode] = shift
				if(mode == 'digital'):
					self.inject.digital_pulse(tv, initialise = False)
				elif(mode == 'analog'):
					self.inject.analog_pulse(tv, initialise = False)
				time.sleep(0.1)
				rp = []
				for i in range(20):
					rp.append(self.readout.cluster_data(initialize = False))
					if(display): print(rp[-1])
					if(rp[-4:] == rp[-5:-1]):
						if(map(float, rp[-1]) == map(float, tv)):
							utils.print_info('->\tCluster-data word alignment {m:s} successfull ({r:d})'.format(m=mode, r=self.readout.cl_shift[mode]))
							self.generic_parameters['cl_word_alignment_{m:s}'.format(m=mode)] = True
							status[mode] = True
							ext = True
							break
				if(ext): break
		if(not status['digital']):
			utils.print_error('->\tCluster-data word alignment digital injection error')
			self.generic_parameters['cl_word_alignment_{m:s}'.format(m='digital')] = True
		if(not status['analog']):
			utils.print_error('->\tCluster-data word alignment analog injection error')
			self.generic_parameters['cl_word_alignment_{m:s}'.format(m='analog')] = True
		print self.readout.cl_shift
		return (status['digital'] and status['analog'])


	def alignment_lateral_input(self, display = False, timeout = 256*3, delay = 4, shift = 'default', init = False, file = 'TestLogs/Chip-0', filemode = 'w', runname = ''):
		utils.activate_I2C_chip()
		if(not self.cl_word_aligned()):
			self.alignment_cluster_data_word()
		fo = open("../SSA_Results/" + file + "_Test_LateralInput.csv", filemode)
		if (init): self.init(reset_board = False, reset_chip = False, display = False)
		self.readout.cluster_data(initialize = True)
		alined_left  = False; alined_right = False; cnt = 0;
		fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay)
		self.inject.digital_pulse([100, 121, 124], initialise = True)
		#self.ctrl.set_lateral_data(0b00001001, 0)
		while ((alined_left == False) and (cnt < timeout)):
			clusters = self.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == 100 and clusters[1] == 121 and clusters[2] == 124):
					alined_left = True
			utils.ShowPercent(cnt, timeout+1, "Allaining left input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			#if  (cnt==256): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+1)
			#elif(cnt==512): fc7.write("cnfg_phy_SSA_gen_delay_lateral_data", delay+2)
			self.ctrl.set_lateral_data_phase(0,5)
			time.sleep(0.001)
			cnt += 1
		utils.ShowPercent(1,1,''); sys.stdout.flush()
		if(alined_left == True):
			utils.print_info("->\tLeft input line alined                       ")
		else:
			utils.print_error("->\tImpossible to align left input data line")
		#self.ctrl.set_lateral_data(0, 0b10100000)
		self.inject.digital_pulse([-2, 0, 10], initialise = True)
		cnt = 0
		while ((alined_right == False) and (cnt < timeout)):
			clusters = self.readout.cluster_data(initialize = False, shift = shift)
			if len(clusters) == 3:
				if(clusters[0] == -2 and clusters[1] == 0 and clusters[2] == 10):
					alined_right = True
			utils.ShowPercent(cnt, timeout+1, "Allaining right input line\t\t" + str(clusters) + "           ")
			time.sleep(0.001)
			self.ctrl.set_lateral_data_phase(5,0)
			time.sleep(0.001)
			cnt += 1
		utils.ShowPercent(1,1,''); sys.stdout.flush()
		if(alined_right == True):
			utils.print_info("->\tRight input line alined                       ")
		else:
			utils.print_error("->\tImpossible to align right input data line")
		fo.write(str(runname) + ' ; ' + str(alined_left) + " ; " + str(alined_right) + ' \n')
		return [alined_left, alined_right]

	def cl_word_aligned(self):
		if ('cl_word_alignment_digital' in self.generic_parameters) and ('cl_word_alignment_analog' in self.generic_parameters):
			return self.generic_parameters['cl_word_alignment_digital'] and self.generic_parameters['cl_word_alignment_analog']
		else:
			return False

	def set_lateral_sampling_shift(self, left, right):
		SetLineDelayManual(0,0, 9,0,left)
		SetLineDelayManual(0,0,10,0,right)
		self.ctrl.phase_tuning()
