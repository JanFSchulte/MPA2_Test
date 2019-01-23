from mpa_methods import *
from mpa_ssa_methods.inject_utility import *

class readout_utility():

	def __init__(self, SSA, MPA, FC7, i2c_mpa, i2c_ssa):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.i2c_mpa = i2c_mpa; self.i2c_ssa = i2c_ssa;

	def stubs(self, calpulse=1, raw=0):
		send_test(calpulse)
		sleep(0.001)
		rp = read_stubs()
		st = [list(rp[1][13]), list(rp[2][13]), list(rp[3][13])]
		stubslist = []
		for cycle in [13,14]:
			for i in range(0,5):
				tmp = [rp[1][cycle][i], rp[2][cycle][i], rp[3][cycle][i]]
				if(tmp[0]!=0):
					stubslist.append(tmp)
		#st = list(rp[1][13]) + list(rp[1][14])
		#st = filter(lambda x: x != 0, st)
		if(raw):
			return stubslist, rp
		else:
			return stubslist

	def L1(self, raw=0, init=1, latency = 500, shift = 0, verbose = 0):
		#### remember to call: FC7.send_resync()
		if(init): ## to speedup set to False after first usage
			self.FC7.write("cnfg_fast_tp_fsm_fast_reset_en", 0)
			self.FC7.write("cnfg_fast_tp_fsm_test_pulse_en", 1)
			self.FC7.write("cnfg_fast_tp_fsm_l1a_en", 1)
			Configure_TestPulse(
				delay_after_fast_reset = 0,
				delay_after_test_pulse = (latency+3+shift),
				delay_before_next_pulse = 0,
				number_of_test_pulses = 1)
			self.FC7.write("cnfg_fast_delay_between_consecutive_trigeers", 0)
			self.SSA.ctrl.set_l1_latency(latency)
		self.FC7.SendCommand_CTRL("start_trigger")
		l1data = read_L1(verbose = verbose)
		if(raw):
			return l1data
			
		str_clusters = []
		pix_clusters = []
		str_n, pix_n, str_row, str_width, str_hip, pix_row, pix_width, pix_col = l1data

		for i in range(str_n):
			str_clusters.append([str_row[i], 0, str_width[i]])
		for i in range(pix_n):
			pix_clusters.append([pix_row[i], pix_col[i], pix_width[i]])

		sorter = lambda x: (x[0], x[2], x[1]) #setup the sorter function
		str_clusters = sorted(str_clusters)
		pix_clusters = sorted(pix_clusters)
		return str_clusters, pix_clusters




		#print test_pp_digital(row, pixel) # send test pulse to defined row and pixel
