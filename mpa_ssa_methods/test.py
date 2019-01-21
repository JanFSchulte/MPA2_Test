from mpa_methods import *


class test_utility():

	def __init__(self, SSA, MPA, FC7, pwr, inj):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.inj = inj; self.pwr = pwr;

	def shiftreg_test(self, val = 'all', display = 1):
		cor = [0]*8; cnt = [0]*8;
		I2C.peri_write('ECM', 0b01000001) #MPA in SSA passthrough mode
		for line in range(0,8):
			for strip in range(1,120):
				vect = [0]*8
				value = val if (val != 'all') else (strip)
				vect[line] = value
				self.inj.ssa_shiftreg(vect)
				time.sleep(0.001)
				self.FC7.send_test()
				#time.sleep(0.001)
				stubs = read_stubs()
				cnt[line] += 1
				if (stubs[1][0][0] != value):
					if(display>0): print("->\tER line ={l:2d}:    expected = {ex:3d} - {ex:8b};    found = {fn:3d} - {fn:8b};".format(l=line, ex=value, fn=stubs[1][2][0]))
				else:
					if(display>1): print("->\tOK line ={l:2d}:    expected = {ex:3d} - {ex:8b};    found = {fn:3d} - {fn:8b};".format(l=line, ex=value, fn=stubs[1][2][0]))
					cor[line] += 1
		res = (np.array(cor, dtype=float)/np.array(cnt, dtype=float))*100
		ret = ["{0:0.2f}%".format(i) for i in res]
		return ret

	def shiftreg_vs_vdd(self, SLVS_Current=0b110, vstep = 0.1):
		pvdd_list = np.arange(0.9, 1.4, vstep)
		dvdd_list = np.arange(0.8, 1.4, vstep)
		pvdd_list = [1.0]
		self.shvd_results = []
		for pvdd in list(pvdd_list):
			for dvdd in list(dvdd_list):
				try:
					self.pwr.set_supply(mode='on', d=dvdd, a=1.25, p=pvdd, bg=0.280, display=False)
					time.sleep(0.1)
					self.pwr.reset(display=False)
					time.sleep(0.1)
					self.SSA.ctrl.init_slvs(SLVS_Current)
					time.sleep(0.1)
					align_MPA()
					time.sleep(0.1)
					ret = self.shiftreg_test(val='all', display=0)
				except:
					ret = [0]*8
				print("->\tPVDD = {pvdd:4.2f}, DVDD = {dvdd:4.2f}, Results = {r:s}".format(pvdd=pvdd, dvdd=dvdd, r=' '.join(ret) ))
				res = [pvdd, dvdd] + ret
				self.shvd_results.append(res)
		return self.shvd_results
