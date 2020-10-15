import time
import sys
import inspect
import random
import numpy as np
from utilities.tbsettings import *
from scipy import interpolate as scipy_interpolate
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import itertools

class Test_2xSSA2():

	def __init__(self, ssa0, ssa1, fc7):
		self.fc7 = fc7;
		self.ssa0 = ssa0
		self.ssa1 = ssa1

	def init(self):
		self.align_2xSSA()
		self.lateral_communication_select_phase()

	def align_2xSSA(self):
		self.ssa0.chip.ctrl.set_t1_sampling_edge('rising')
		self.ssa0.chip.ctrl.init_slvs(0b111)
		self.ssa1.chip.ctrl.set_t1_sampling_edge('rising')
		self.ssa1.chip.ctrl.init_slvs(0b111)
		self.ssa0.chip.ctrl.activate_readout_shift()
		self.ssa1.chip.ctrl.activate_readout_shift()
		self.ssa0.chip.ctrl.set_shift_pattern_all(0b10000000)
		self.ssa1.chip.ctrl.set_shift_pattern_all(0b10000000)
		rt = self.ssa0.chip.ctrl.align_out()
		self.ssa0.chip.ctrl.reset_pattern_injection()
		self.ssa0.chip.ctrl.activate_readout_normal()
		self.ssa1.chip.ctrl.reset_pattern_injection()
		self.ssa1.chip.ctrl.activate_readout_normal()
		if(rt): utils.print_good( "->  Phase alignment successfull")
		else:   utils.print_error("->  Phase alignment error")
		return rt

	def lateral_communication_select_phase(self):
		self.ssa0.inject.digital_pulse(hit_list=[], initialise=True)
		self.ssa1.inject.digital_pulse(hit_list=[], initialise=True)
		testvect_L2R = [10, 20, 30, 117, 119]
		testvect_R2L = [1, 3, 5, 15, 25, 35]
		aligned = [False, False]
		self.ssa0.inject.digital_pulse(testvect_L2R)
		self.ssa1.inject.digital_pulse(testvect_R2L)
		for i in range(7,0,-1):
			self.ssa0.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_R_PhaseData', data=i)
			rt0 = self.ssa0.readout.cluster_data(shift = -2)
			if(rt0 == [10.0, 20.0, 30.0, 117.0, 119.0, 121.0, 123.0]):
				aligned[0] = True
				break
		for j in range(7,3,-1):
			self.ssa1.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_L_PhaseData', data=j)
			rt1 = self.ssa1.readout.cluster_data(shift = -2)
			if(rt1 == [-3.0, -1.0, 1.0, 3.0, 5.0, 15.0, 25.0]):
				aligned[1] = True
				break
		if(aligned[0]):
			if(i==7): utils.print_good("->  Lateral communication ok. Phase value = {:d} -> as expected.".format(i))
			else: utils.print_warning("->  Lateral communication ok. Phase value = {:d} -> not as expected but it is fine.".format(i))
		else:
			utils.print_error("->  Lateral communication not working properly")
		if(aligned[1]):
			if(j==7): utils.print_good("->  Lateral communication ok. Phase value = {:d} -> as expected.".format(j))
			else: utils.print_warning("->  Lateral communication ok. Phase value = {:d} -> not as expected but it is fine.".format(j))
		else:
			utils.print_error("->  Lateral communication not working properly")
		return [i, j]

	def lateral_communication_set_phase(self, p0, p1):
		self.ssa0.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_R_PhaseData', data=p0)
		self.ssa1.i2c.peri_write(register='LateralRX_sampling', field='LateralRX_L_PhaseData', data=p1)

#  min_clsize = 1; max_clsize = 4; nruns = 5; shift = -2; nstrips = 2

	def test_l1_data(self, mode="digital", nstrips='random', nruns=100, calpulse=[100, 200], threshold=[20, 150], shift=0, display=False, latency=50, init=False, hfi=True, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = ''):
		rt = []
		rt.extend( self.ssa0.test.l1_data(mode=mode, nstrips=nstrips, nruns=nruns, calpulse=calpulse, threshold=threshold, shift=shift, display=display, latency=latency, init=init, hfi=hfi, file=file, filemode=filemode, runname=runname ,profile=False) )
		rt.extend( self.ssa1.test.l1_data(mode=mode, nstrips=nstrips, nruns=nruns, calpulse=calpulse, threshold=threshold, shift=shift, display=display, latency=latency, init=init, hfi=hfi, file=file, filemode=filemode, runname=runname ,profile=False) )
		return rt

	def test_cluster_data(self, mode = "digital",  nstrips = 'random', min_clsize = 1, max_clsize = 4, nruns = 100, shift = -2, display=False, init = False, file = '../SSA_Results/TestLogs/Chip-0', filemode = 'w', runname = '', stop_on_error = False, lateral = True):
		fo = open(file + "readout_cluster-data_" + mode + ".csv", filemode)
		stexpected = ''; stfound = '';
		SendCommand_CTRL("stop_trigger")
		prev = [0xff]*8
		if(mode == "digital"):
			self.ssa0.inject.digital_pulse(initialise = True, times = 1)
			self.ssa1.inject.digital_pulse(initialise = True, times = 1)
		elif(mode == "analog"):
			self.ssa0.inject.analog_pulse(initialise = True, mode = 'edge', cal_pulse_amplitude = 130, threshold = [100, 150])
			self.ssa1.inject.analog_pulse(initialise = True, mode = 'edge', cal_pulse_amplitude = 130, threshold = [100, 150])
		else:
			return False
		cnt = {'cl_sum': 0, 'cl_err' : 0};
		timeinit = time.time()
		for i in range(0,nruns):
			if(isinstance(nstrips, int)): nclusters_generated = nstrips
			else: nclusters_generated = random.randint(1, 7) # 7 becouse the last line is not connected on the 2xSSA PCB
			cl_hits, cl_centroids = self.ssa0.test.generate_clusters(nclusters_generated, min_clsize, max_clsize, 1, 240)
			wd = 0; err = [False]*3

			ssa0_list = [i for i in (np.array(cl_hits)) if i < 121] or []
			ssa1_list = [i for i in (np.array(cl_hits)-120) if i > 0] or []
			if(mode == "digital"):
				self.ssa0.inject.digital_pulse(hit_list = ssa0_list, initialise = False)
				self.ssa1.inject.digital_pulse(hit_list = ssa1_list, initialise = False)
			elif(mode == "analog"):
				self.ssa0.inject.analog_pulse(hit_list = ssa0_list, initialise = False)
				self.ssa1.inject.analog_pulse(hit_list = ssa1_list, initialise = False)
			time.sleep(0.005) #### important at nstrips = 8 (I2C time)
			received0, status0 = self.ssa0.readout.cluster_data(initialize = False, shift = shift, getstatus = True, set_chip=True)
			received1, status1 = self.ssa1.readout.cluster_data(initialize = False, shift = shift, getstatus = True, set_chip=True)
			received = []
			received.extend(received0)
			received.extend(list(np.array(received1)+120))
			missing=[]; exceding=[];
			received_tmp = received.copy()
			cl_centroids_tmp = cl_centroids.copy()
			for cldupl in cl_centroids:
				if(cldupl>=117 and  cldupl<=124):
					cl_centroids_tmp.append(cldupl)
			for k in cl_centroids:
				if k not in received_tmp:
					err[0] = True
					missing.append(k)
				else:
					received_tmp.remove(k)
			for k in received:
				if k in cl_centroids_tmp:
					cl_centroids_tmp.remove(k)
			exceding = cl_centroids_tmp
			if(len(exceding)>0): err[0] = True
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

	def test_ring_oscillators_vs_dvdd(self,
		dvdd_step=0.05, dvdd_max=1.3, dvdd_min=0.8, plot=False,
		filename = '../SSA_Results/test_2xSSA2/ring_oscillator_vs_dvdd/', filemode='w', runname = '', printmode='info'):
		result = []
		if not os.path.exists(filename): os.makedirs(filename)
		fout = filename + 'ring_oscillator_vs_dvdd_' + runname + ".csv"
		with open(fout, filemode)  as fo:
			fo.write("    RUN ,   DVDD , INV BR , INV TR , INV BC , INV BL , DEL BR , DEL TR , DEL BC , DEL BL ,  \n")
		dvdd_range = np.arange(dvdd_min, dvdd_max, dvdd_step)
		for dvdd in dvdd_range:
			self.ssa0.pwr.set_dvdd(dvdd)
			time.sleep(0.5)
			res = self.ssa0.chip.bist.ring_oscilaltor(
				resolution_inv=127, resolution_del=127, printmode=printmode,
				raw=0, asarray=1, display=1, note=' at DVDD={:5.3f}V'.format(dvdd) )
			#rdv = self.ssa.pwr.get_dvdd()
			result.append( np.append(dvdd , res) )
			with open(fout, 'a')  as fo:
				fo.write("{:8s}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f}, {:7.3f},\n".format(
					runname, dvdd, res[0], res[1], res[2], res[3], res[4], res[5], res[6], res[7]))
		self.ssa0.pwr.set_dvdd(1.0)
		time.sleep(0.5)
		if(plot):
			self.ring_oscillators_vs_dvdd_plot()
		return result

	def test_SRAM_BIST_vs_DVDD(self,
		step=0.001, dvdd_max=0.800, dvdd_min=0.750, nruns_per_point=1, plot=False,
		filename = '../SSA_Results/test_2xSSA2/memory_bist_vs_dvdd/', filemode='w', runname = ''):
		self.ssa0.pwr.set_dvdd(1.0)
		time.sleep(0.5)
		self.ssa0.reset()
		self.ssa1.reset()
		result = {}
		if not os.path.exists(filename): os.makedirs(filename)
		fout = filename + "memory_bist_vs_dvdd_" + runname + ".csv"
		with open(fout, filemode)  as fo:
			fo.write("\n     RUN ,   DVDD   , 0-MEM0   , 0-MEM1   , 1-MEM0   , 1-MEM1    \n")
		#dvdd_range = np.linspace(dvdd_max, dvdd_min, npoints)
		fine_range = np.arange(dvdd_max, dvdd_min-step, (-1)*step)
		coarse_renge = np.arange(1.3, dvdd_max+step, -0.1)
		#coarse_renge = []
		dvdd_range = np.append(coarse_renge, fine_range)
		for dvdd in dvdd_range:
			self.ssa0.pwr.set_dvdd(dvdd)
			#self.ssa.reset()
			time.sleep(0.1)
			res0 = self.ssa0.test.SRAM_BIST(nruns=nruns_per_point, note='Chip {:d} [DVDD={:5.3f}] '.format(0, dvdd), display=True )
			res1 = self.ssa1.test.SRAM_BIST(nruns=nruns_per_point, note='Chip {:d} [DVDD={:5.3f}] '.format(1, dvdd), display=True )
			if(res0[0]<0): res0[0]=0;
			if(res0[1]<0): res0[1]=0;
			if(res1[0]<0): res1[0]=0;
			if(res1[1]<0): res1[1]=0;
			#rdv = self.ssa.pwr.get_dvdd()
			result[np.round(dvdd, 4)] = [res0[0], res0[1], res1[0], res1[1]]
			with open(fout, 'a')  as fo:
				fo.write("{:8s} , {:7.3f} , {:7.3f} , {:7.3f} , {:7.3f} , {:7.3f} , \n".format(runname, dvdd, res0[0], res0[1], res1[0], res1[1]))
		self.ssa0.pwr.set_dvdd(1.0)
		time.sleep(0.1)
		if(plot):
			self.SRAM_BIST_vs_DVDD_plot()
		return result


	def initialize(self, nruns=50):
		self.ssa0.reset()
		self.ssa0.init()
		self.align_2xSSA()
		self.lateral_communication_select_phase()
		self.test_cluster_data(nruns=nruns)
		self.ssa0.test.l1_data(nruns=nruns)

	def run(self, runname='Tp25', filename='../SSA_Results/test_2xSSA2/'):
		rt = []
		time.sleep(0.1); rt.extend( self.ssa0.pwr.get_power() )
		time.sleep(0.1); rt.append( self.align_2xSSA() )
		time.sleep(0.1); rt.extend( self.lateral_communication_select_phase() )
		time.sleep(0.1); rt.append( self.test_cluster_data(nruns=1000) )
		time.sleep(0.1); rt.extend( self.ssa0.test.l1_data(nruns=1000) )
		self.test_SRAM_BIST_vs_DVDD(runname = runname, filename = filename+'/memory_bist_vs_dvdd/')
		self.test_ring_oscillators_vs_dvdd(runname = runname, filename = filename+'/memory_bist_vs_dvdd/')
		with open(filename + 'summary_' + runname + '.csv', 'w') as fo:
			fo.write(str(rt))
		self.ssa0.pwr.set_dvdd(1.0)
		return rt
