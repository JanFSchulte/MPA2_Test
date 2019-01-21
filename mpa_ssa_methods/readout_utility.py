from mpa_methods import *
from mpa_ssa_methods.inject_utility import *

class readout_utility():

	def __init__(self, SSA, MPA, FC7, i2c_mpa, i2c_ssa):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.i2c_mpa = i2c_mpa; self.i2c_ssa = i2c_ssa;

	def stubs(self, calpulse=1):
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
		return stubslist


		#print test_pp_digital(row, pixel) # send test pulse to defined row and pixel
