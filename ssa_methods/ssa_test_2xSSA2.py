import time, sys, inspect, random, re
import numpy as np
from utilities.tbsettings import *
from scipy import interpolate as scipy_interpolate
import seaborn as sns
from myScripts.BasicD19c import *
from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
import itertools
from scipy import stats
from scipy import constants as ph_const
from scipy import signal as scypy_signal
from scipy import interpolate

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

	###########################################################################
	def initialize(self, nruns=50):
		self.ssa0.reset()
		self.ssa0.init()
		self.align_2xSSA()
		self.lateral_communication_select_phase()
		self.test_cluster_data(nruns=nruns)
		self.ssa0.test.l1_data(nruns=nruns)

	###########################################################################
	def climatic_chamber_digital_test(self, runname='Tp25', filename='../SSA_Results/test_2xSSA2/'):
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

	###########################################################################
	def climatic_chamber_digital_test_plot(self, directory='../SSA_Results/test_2xSSA2/'):
		### load data
		files = os.listdir(directory)
		summary_list = np.sort([s for s in files if "summary_" in s])
		memory_list = np.sort([s for s in files if "memory_bist_vs_dvdd_" in s])
		oscilaltor_list = np.sort([s for s in files if "ring_oscillator_vs_dvdd_" in s])
		power = []; lateral_com_phase = []
		stub_data = []; l1_strip = []; l1_hip_flags = []; l1_headers = [];
		temperature = []
		for ddd in summary_list:
			fnd = re.findall(".+_T(\w)(\d+).csv", ddd)
			if   (fnd[0][0]=='p'): T = np.float(fnd[0][1])
			elif (fnd[0][0]=='m'): T = (-1)*np.float(fnd[0][1])
			else: T = 'error'
			temperature.append(T)
			print('->  Analizing test results at {:5.1f}C'.format(T))
			with open(directory+'/'+ddd, 'r') as fi:
				data = fi.read().strip('\b[]').split(',')
			power.append(  np.append( [T], data[0:3] ))
			lateral_com_phase.append(data[4:6])
			stub_data.append( data[6] )
			l1_headers.append( data[7] )
			l1_strip.append( data[8] )
			l1_hip_flags.append( data[9] )

		### plot_lateral_communication_vs_temperature #####################################
		color=iter(sns.color_palette('deep')); cnt=0;
		for dataset in ['Left', 'Right']:
			temperature.sort()
			lateral_com_phase = np.array(lateral_com_phase, dtype=int)
			fig = plt.figure(figsize=(6,4))
			plt.plot(temperature, lateral_com_phase[:, cnt], 'x-',  color=next(color))
			ax = plt.subplot(111)
			ax.get_xaxis().tick_bottom(); ax.get_yaxis().tick_left()
			plt.xticks(fontsize=12)
			plt.yticks(list(range(0,12,1)), fontsize=12)
			plt.grid(True, which='major', axis='y')
			plt.ylabel('Phase select setting [{:s}]'.format(dataset), fontsize=16)
			plt.xlabel('Temperature [C]', fontsize=16)
			next(color); cnt+=1;
			fo = directory+'plot_lateral_communication_setting_{:s}_vs_temperature.png'.format(dataset)
			print('->  Plot saved as {:s}'.format(fo))
			plt.savefig(fo, bbox_inches="tight");

		### plot_power_vs_temperature #####################################
		color=iter(sns.color_palette('deep'))
		power = np.array(power, dtype=float)
		self.myplot(x=power[:,0], y=power[:,1]/2.0, type='x', color=next(color), dlabel='DVDD', xlabel='', ylabel='',newfig=True,  saveplot=False)
		self.myplot(x=power[:,0], y=power[:,2]/2.0, type='x', color=next(color), dlabel='AVDD', xlabel='', ylabel='',newfig=False, saveplot=False)
		self.myplot(x=power[:,0], y=power[:,3]/3.0, type='x', color=next(color), dlabel='PVDD', xlabel='Temperature [C]', ylabel='Current [mA]',newfig=False, saveplot=directory+'/plot_power_vs_temperature.png')

		### plot_sram_min_operating_voltage_vs_temperature ####################
		temperature = []
		memory_results={}
		memory_min_voltage = []
		for ddd in memory_list:
			fnd = re.findall(".+_T(\w)(\d+).csv", ddd)
			if   (fnd[0][0]=='p'): T = np.float(fnd[0][1])
			elif (fnd[0][0]=='m'): T = (-1)*np.float(fnd[0][1])
			else: T = 'error'
			print('->  Analizing Memory test results at {:5.1f}C'.format(T))
			temperature.append(T)
			data = CSV.csv_to_array(directory+'/'+ddd)
			voltage = np.array(data[:,0], dtype=float)
			color=iter(sns.color_palette('deep'))
			fig = plt.figure(figsize=(6,4))
			memory_results[T] = [[],[],[],[]]
			min_operating_voltage = [T]
			for i in [1,2]:
				memory_results[T][i] = np.array(data[:,i+1], dtype=float)
				#self.myplot(x=voltage, y=memory_results[T][i], type='x--', color=next(color), dlabel='DVDD', xlabel='', ylabel='',newfig=False,  saveplot=False)
				min_operating_voltage.append( data[:,0][ np.min(np.where(memory_results[T][i]<100)) ] )
				#print(min_operating_voltage[-1])
			memory_min_voltage.append(min_operating_voltage)

		### plot_sram_min_operating_voltage_vs_temperature ####################
		memory_min_voltage = np.array(memory_min_voltage, dtype=float)
		memory_min_voltage = memory_min_voltage[np.argsort(memory_min_voltage[:,0])]
		fig = plt.figure(figsize=(6,4))
		color=iter(sns.color_palette('deep'))
		for mem in [1,2]:
			x = memory_min_voltage[:,0]
			y = memory_min_voltage[:,mem]
			xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
			c = next(color);
			helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y) )
			y_smuth = helper_y3(xnew)
			y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 1001, polyorder = 5)
			plt.plot(xnew, y_hat , color=c, lw=1, alpha = 0.5)
			plt.plot(x, y, 'x', label='SRAM {:d}'.format(mem), color=c)

		ax = plt.subplot(111)
		leg = ax.legend(fontsize = 12, frameon=True ) #loc=('lower right')
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel('Min operating Voltage [V]', fontsize=16)
		plt.xlabel('Temperature [C]', fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		fo = directory+'plot_sram_min_operating_voltage_vs_temperature.png'
		print('->  Plot saved as {:s}'.format(fo))
		plt.savefig(fo, bbox_inches="tight");

		### plot_sram_vs_voltage_vs_temperature ####################
		color=iter(sns.color_palette('deep'))
		self.myplot(x=voltage, y=memory_results[25][1], type='x-', color=next(color), dlabel='T = {:3.1f}'.format(25), xlabel='', ylabel='',newfig=True,  saveplot=False)
		self.myplot(x=voltage, y=memory_results[-35][1], type='x-', color=next(color), dlabel='T = {:3.1f}'.format(-35), xlabel='DVDD [V]', ylabel='% correct data',newfig=False,  saveplot=False)
		plt.savefig(directory+'plot_sram_vs_voltage_vs_temperature.png', bbox_inches="tight");


		### plot_ring_oscillator__vs_voltage_vs_temperature ####################
		color=iter(sns.color_palette('deep'))
		self.myplot(x=voltage, y=memory_results[25][1], type='x-', color=next(color), dlabel='T = {:3.1f}'.format(25), xlabel='', ylabel='',newfig=True,  saveplot=False)
		self.myplot(x=voltage, y=memory_results[-35][1], type='x-', color=next(color), dlabel='T = {:3.1f}'.format(-35), xlabel='DVDD [V]', ylabel='% correct data',newfig=False,  saveplot=False)
		plt.savefig(directory+'plot_sram_vs_voltage_vs_temperature.png', bbox_inches="tight");
		temperature = []
		data = {}; voltage = {};
		for ddd in oscilaltor_list:
			fnd = re.findall(".+_T(\w)(\d+).csv", ddd)
			if   (fnd[0][0]=='p'): T = np.float(fnd[0][1])
			elif (fnd[0][0]=='m'): T = (-1)*np.float(fnd[0][1])
			else: T = 'error'
			print('->  Analizing Ring Oscillator test results at {:5.1f}C'.format(T))
			temperature.append(T)
			data[T] = CSV.csv_to_array(directory+'/'+ddd)
			voltage[T] = np.array(data[T][:,1], dtype=float)
			data[T] = data[T][:,2:-1]

		for oscillator in range(8):
			fig = plt.figure(figsize=(6,6))
			color=iter(sns.color_palette('deep')*3)
			ax = plt.subplot(111)
			for T in [-35,-25, -15, -5, 5,15,25,35,45,55]:
				x = voltage[T]
				y = data[T][:,oscillator]
				xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
				c = next(color);
				helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y) )
				y_smuth = helper_y3(xnew)
				y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 9, polyorder = 5)
				plt.plot(xnew, y_hat , color=c, lw=1, alpha = 0.8)
				plt.plot(x, y, 'x', label='T = {:3.1f}'.format(T), color=c)
			leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
			leg.get_frame().set_linewidth(1.0)
			ax.get_xaxis().tick_bottom();
			ax.get_yaxis().tick_left()
			plt.ylabel('Ring oscillator frequency [MHz]', fontsize=16)
			plt.xlabel('DVDD [V]', fontsize=16)
			plt.xticks(list(np.arange(0.8,1.3,0.1)), fontsize=12)
			plt.yticks(fontsize=12)
			plt.savefig(directory+'/plot_ring_oscillator_{:d}_vs_voltage_vs_temperature.png'.format(oscillator), bbox_inches="tight");

		for oscillator in range(8):
			fig = plt.figure(figsize=(6,6))
			color=iter(sns.color_palette('deep')*3)
			ax = plt.subplot(111)
			index = 0
			for V in voltage[temperature[0]]:
				x = np.array(np.sort(temperature), dtype=float)
				y = data[T][:,oscillator]
				y = []
				for T in x:
					y.append(data[T][index,oscillator])
				y = np.array(y, dtype=float)
				xnew = np.linspace(np.min(x), np.max(x), 1001, endpoint=True)
				c = next(color);
				helper_y3 = scipy_interpolate.make_interp_spline(x, np.array(y) )
				y_smuth = helper_y3(xnew)
				y_hat = scypy_signal.savgol_filter(x = y_smuth , window_length = 9, polyorder = 5)
				plt.plot(xnew, y_hat , color=c, lw=1, alpha = 0.8)
				plt.plot(x, y, 'x', label='V = {:3.1f}'.format(V), color=c)
				index += 1
			leg = ax.legend(fontsize = 10, frameon=True ) #loc=('lower right')
			leg.get_frame().set_linewidth(1.0)
			ax.get_xaxis().tick_bottom();
			ax.get_yaxis().tick_left()
			plt.ylabel('Ring oscillator frequency [MHz]', fontsize=16)
			plt.xlabel('Temperature [C]', fontsize=16)
			plt.xticks(list(np.arange(-40,90,10)), fontsize=12)
			plt.yticks(fontsize=12)
			plt.savefig(directory+'/plot_ring_oscillator_{:d}_vs_temperature_vs_voltage.png'.format(oscillator), bbox_inches="tight");

	###########################################################################
	def myplot(self, x, y, type, color, dlabel='', xlabel='', ylabel='', newfig=True, saveplot=False):
		if(newfig):
			fig = plt.figure(figsize=(6,4))
		plt.plot(x, y, type , label=dlabel, color=color)
		ax = plt.subplot(111)
		leg = ax.legend(fontsize = 12, loc=('lower right'), frameon=True )
		leg.get_frame().set_linewidth(1.0)
		ax.get_xaxis().tick_bottom();
		ax.get_yaxis().tick_left()
		plt.ylabel(ylabel, fontsize=16)
		plt.xlabel(xlabel, fontsize=16)
		plt.xticks(fontsize=12)
		plt.yticks(fontsize=12)
		if(saveplot):
			print('->  Plot saved as {:s}'.format(saveplot))
			plt.savefig(saveplot, bbox_inches="tight");
