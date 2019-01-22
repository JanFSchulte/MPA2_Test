from mpa_methods import *
import random


class test_utility():

	def __init__(self, SSA, MPA, FC7, pwr, PS):
		self.SSA = SSA; self.MPA = MPA; self.FC7 = FC7;
		self.PS = PS; self.pwr = pwr;

	def OneStub_AllTxLines(self, nruns=1000, display=1):
		nerr=[0]*8
		for line in range(8):
			for i in range(nruns):
				rp = self.OneStub(display = display)
				if(not rp):	nerr[line] += 1
				utils.ShowPercent(i+1, nruns, "One stub test running")
			res = 1.0-(nerr[line]/np.float(nruns))
			print( "->\tStubs match with hit on SSA line {l:1d}: {r:5.2f}% correct".format(l=line, r=(res*100)) )


	def OneStub(self, ssa_line = 3, n_pixel_cl = 3, stub_bend = 0, display = 1):
		strips = []
		pixels = []
		#### 8 independent Strip Clusters ####
		sch = range(1,120)
		for i in range(8):
			tmp = random.sample(sch, 1)[0]
			sch = filter(lambda x: ((x < tmp-5) or (x > tmp+5)) , sch)
			strips.append(tmp)
		strips.sort()
		#### A single stub ####
		col = strips[ ssa_line ] + stub_bend
		row = random.randint(1,16)
		target_stub = [np.float(col), row, stub_bend]
		pixels.append([col, row])
		#### 8 Pixel Clusters that dont make a stub ####
		sch = range(1,120)
		for i in strips:
			sch = filter(lambda x: ((x<i-5) or (x>i+5)) , sch)
		tmp = random.sample(sch, (n_pixel_cl-1))
		for col in tmp:
			row = random.randint(1,16)
			pixels.append([col, row])
		pixels.sort()
		#### Inject strip and pixel hits ####
		self.PS.inj.stub(strips, pixels)
		#### readout stubs ####
		s, raw = self.PS.rdo.stubs(calpulse=1, raw=1)
		#### Verify ####
		Error = True
		for i in range(len(s)):
			s[i][0] = s[i][0]/2.0
			s[i][1] = s[i][1]+1
		if(len(s)==1):
			if(s[0] == target_stub):
				Error = False
		rtstr  = "  Expect = {:s}\n".format(target_stub)
		rtstr += "        Found  = {:s}\n".format(',\t'.join(map(str, s)))
		rtstr += "        Strips = {:s}\n".format(''.join( ["{:12s}".format(str([i])) for i in strips] ))
		rtstr += "        Pixels = {:s}\n".format(''.join( ["{:12s}".format(i) for i in pixels] ))
		if(Error):
			if(display>0): print( "-> ER " + rtstr )
			if(display>2): print raw
		else:
			if(display>1): print( "-> OK " + rtstr )
		return (not Error)


	def shiftreg_test(self, val = 'all', display = 1):
		cor = [0]*8; cnt = [0]*8;
		I2C.peri_write('ECM', 0b01000001) #MPA in SSA passthrough mode
		for line in range(0,8):
			for strip in range(1,120):
				vect = [0]*8
				value = val if (val != 'all') else (strip)
				vect[line] = value
				self.PS.inj.ssa_shiftreg(vect)
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
