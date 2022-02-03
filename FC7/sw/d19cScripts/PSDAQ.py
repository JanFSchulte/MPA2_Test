from inspect import getsourcefile
import os.path as path, sys
current_dir = path.dirname(path.abspath(getsourcefile(lambda:0)))
sys.path.insert(0, current_dir[:current_dir.rfind(path.sep)])

import time
import Queue
import threading
import ROOT
from fc7_daq_methods import *
from PSDataTypes import *
from mpa_methods.mpa_i2c_conf import *
from mpa_methods.cal_utility import *
#from myScripts.BasicD19c import *

class PSDAQ:
    def __init__(self, EmulatorMode = False):
        self.EventSize = 38
        self.EmulatorMode = EmulatorMode
	self.SaveROOT = False
        self.processorRunning = False
	self.EventsInPacket = 0
	self.ZSEnable = 0
        self.IsDDR3Readout = 0
        self.DDR3Offset = 0
    # reset d19c
    def ResetBoard(self):
        SendCommand_CTRL("global_reset")
        sleep(1)
        print "--> d19c was reset"

    # configures the emulator
    def ConfigureMPAEmulator(self, nSClusters = 1, nPClusters = 1):
        #SendCommand_I2C(command type, hybrid_id, chip_id, page, read, register_address, data, ReadBack)
        # command type: 0 - write to certain chip, hybrid; 1 - write to all chips on hybrid; 2 - write to all chips/hybrids (same for READ)
        #write to register 1 16 as data (number of sclusters)
        SendCommand_I2C(            0,         0,       0,    0,     0,               1,    nSClusters,       0)
        #write to register 2 1 as data (scluster address)
        SendCommand_I2C(            0,         0,       0,    0,     0,               2,    1,        0)
        #write to register 4 (number of pclusters)
        SendCommand_I2C(            0,         0,       0,    0,     0,               4,    nPClusters,       0)
        # address and width of the pclusters
        SendCommand_I2C(            0,         0,       0,    0,     0,               5,    5,       0)
        SendCommand_I2C(            0,         0,       0,    0,     0,               6,    1,       0)

        print "--> emulator was succesfully configured"

    # setting the optimal data taking configuration
    def ConfigureBoard(self, ext_clock_en, trigger_source, ext_trigger_delay, backpressure_en, stub_trigger_delay, stub_veto_length, npackets, handshake_en, zs_enable, readout_stub_delay, dio5_tlu_enable):
        # also check the readout type
        self.IsDDR3Readout = fc7.read("stat_ddr3_readout")
        print "Is readout DDR3: ", self.IsDDR3Readout
        if (self.IsDDR3Readout):
            # because d19c adds dummy words in case of ddr3
            self.EventSize += (8 - self.EventSize % 8)

        # set an external clock
        fc7.write("cnfg_clock_ext_clk_en", ext_clock_en)
        # ttc should be disabled dy default, but let's make sure
        fc7.write("cnfg_ttc_enable", 0)

        # set fast commands
        # trigger to accept 0
        fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", 0)
        # user frequency set to 1000 just in case we want to use
        fc7.write("cnfg_fast_user_frequency", 100)
        # trigger source
        fc7.write("fc7_daq_cnfg.fast_command_block.trigger_source", trigger_source)
        # stubs mask - from chip 0
        fc7.write("cnfg_fast_stub_mask", 1)
        # stub trigger delay
        fc7.write("cnfg_fast_stub_trigger_delay", stub_trigger_delay)
        # stub veto length
        fc7.write("cnfg_fast_stub_veto_length", stub_veto_length)
        # external trigger delay
        fc7.write("cnfg_fast_ext_trigger_delay_value", ext_trigger_delay)
        # backpressure enable
        fc7.write("fc7_daq_cnfg.fast_command_block.misc.backpressure_enable", backpressure_en)
        # initial fast reset
        fc7.write("fc7_daq_cnfg.fast_command_block.misc.initial_fast_reset_enable", 1)
        # load config
        sleep(0.01)
        fc7.write("fc7_daq_ctrl.fast_command_block.control.load_config", 1)

        # readout block
        # number of events in package
	self.EventsInPacket = npackets + 1
        fc7.write("cnfg_readout_packet_nbr", npackets)
        # enable data handshake
        fc7.write("cnfg_readout_data_handshake_enable", handshake_en)
        # stub data delay in readout
        fc7.write("cnfg_readout_common_stubdata_delay", readout_stub_delay)
        # misc emulator settings and zs
	if zs_enable == 1:
		print "Running in ZS Mode!"
	self.ZSEnable = zs_enable
        fc7.write("cnfg_readout_zero_suppression_enable", zs_enable)
        fc7.write("cnfg_readout_int_trig_enable", 0)
        fc7.write("cnfg_readout_int_trig_rate", 0)
        fc7.write("cnfg_readout_trigger_type", 0)
        fc7.write("cnfg_readout_data_type", 0)

        # dio5
        fc7.write("cnfg_dio5_en", dio5_tlu_enable)
        if dio5_tlu_enable:
		DIO5Tester("fmc_l8")
        # tlu
        fc7.write("cnfg_tlu_enabled", dio5_tlu_enable)
        # fc7.write("cnfg_tlu_trigger_id_delay", 1)
        # andreas
	fc7.write("cnfg_tlu_trigger_id_delay", 2)
        fc7.write("cnfg_tlu_handshake_mode", 2)

        print "--> d19c was succesfully configured"

    # reset readout
    def ReadoutReset(self):
        fc7.write("fc7_daq_ctrl.readout_block.control.readout_reset",1)
        sleep(0.1)
        fc7.write("fc7_daq_ctrl.readout_block.control.readout_reset",0)
        sleep(0.5)

        self.DDR3Offset = 0
        if (self.IsDDR3Readout):
            i = 0
            while(not fc7.read("stat_ddr3_initial_calibration_done")):
                if (i==0):
                    print "Waiting for DDR3 to finish initial calibration"
                    i = 1
                sleep(0.1)

    # start worker thread
    def ConfigureAll(self, ext_clock_en = 0, trigger_source = 3, ext_trigger_delay = 50, backpressure_en = 1, stub_trigger_delay = 200, stub_veto_length = 50, npackets = 99, handshake_en = 1, zs_enable = 0, readout_stub_delay = 200, dio5_tlu_enable = 0):
        self.ResetBoard()
        if self.EmulatorMode:
            # configure emulator
            self.ConfigureMPAEmulator(nSClusters = 3, nPClusters = 1)
            # then configutr board
            self.ConfigureBoard(ext_clock_en, trigger_source, ext_trigger_delay, backpressure_en, stub_trigger_delay, stub_veto_length, npackets, handshake_en, zs_enable, readout_stub_delay, dio5_tlu_enable)
        else:
            # configure d19c itself
            self.ConfigureBoard(ext_clock_en, trigger_source, ext_trigger_delay, backpressure_en, stub_trigger_delay, stub_veto_length, npackets, handshake_en, zs_enable, readout_stub_delay, dio5_tlu_enable)
            # configure MPA chip
            self.ConfigureMPA(l1_latency = (readout_stub_delay+34))
        print "--> DAQ configuration Done"

    # start trigger
    def StartRun(self, runProcessor = True, runData = "eurun"):
        # create event queue
        self.DataQueue = Queue.Queue()
        # create the worker thread
        if runProcessor:
            self.processorRunning = True
            self.ProcessingThread = threading.Thread(target=self.DataProcessing)
            self.ProcessingThread.daemon = True
            self.ProcessingThread.start()

        # init root tree
        if self.SaveROOT:
		self.InitTREE(runData)		

        # reset readout
        self.ReadoutReset()
        # resetting processed event counter
        self.EventCounter = 0

        # enable runner
        self.run_stop_requested = False

        # start triggering
        SendCommand_CTRL("start_trigger")

        # create read data thread
        self.ReadDataThread = threading.Thread(target=self.GetData)
        self.ReadDataThread.daemon = True
        self.ReadDataThread.start()

        print "--> run started"

    # stop trigger
    def StopRun(self):

        print "--> waiting for daq to stop"

        # wait for the thread to stop
        self.run_stop_requested = True
        self.ReadDataThread.join()

        # stop receiving triggers
        SendCommand_CTRL("stop_trigger")

        print "--> daq and triggering stopped, waiting for processing queue"

        # once daq is done wait till data being stored
        self.DataQueue.join()

        # write root file
        if self.SaveROOT:
        	self.tree.Write()

        # then stop workers
        if self.processorRunning:
            self.DataQueue.put(None)
            self.ProcessingThread.join()
            self.processorRunning = False

        print "--> run stopped (got " + str(self.EventCounter) + " events)"

    # here should be the phase tuning, and the i2c config... # readout_mode or "level" or "edge"
    def ConfigureMPA(self, l1_latency = 196, readout_mode = "edge"):
	# activate I2C chip
	activate_I2C_chip()
	# sampling edge
	I2C.peri_write("EdgeSelT1Raw", 0)
	# put chip in some mode
	if readout_mode == "edge":
		I2C.pixel_write('ModeSel', 0, 0, 0b00)
		I2C.pixel_write("ENFLAGS", 0, 0, 0b00000111)
	elif readout_mode == "level":
		I2C.pixel_write('ModeSel', 0, 0, 0b01)
		I2C.pixel_write("ENFLAGS", 0, 0, 0b00001011)
	else:
		print "Error! Wrong readout mode"
		exit(1)
	# mask noisy pixel (REMOVE ME WHEN YOU GO FOR OTHER MODULE)
	# assembly 1: 
	#I2C.pixel_write("ENFLAGS", 11, 91, 0)
	# assembly 2:
	#I2C.pixel_write("ENFLAGS", 8, 5, 0)
	#I2C.pixel_write("ENFLAGS", 8, 7, 0)
	# phase shift (decided based on the latency scan for threshold 110)
	#I2C.peri_write("PhaseShift",1)
	# set the latency
	print "---> MPA Latency is set to : ", l1_latency
	I2C.row_write("L1Offset_1", 0, (0x00FF & l1_latency) >> 0)
	I2C.row_write("L1Offset_2", 0, (0x0100 & l1_latency) >> 8)
	# activate sync mode
	activate_sync()
	# stub pixel strip (for tuning)
	activate_ps()
	sleep(0.01)
        # align output
	align_out()
	# stub pixel pixel
	activate_pp()	
	# here load the trimmed configuration (!!!)
	##

    # init root file
    def InitROOT(self, runName):
	## then the root is initialized
	self.SaveROOT = True
        ## create the root file
        timestr = time.strftime("%Y%m%d-%H%M%S")
	filename = "data/" + runName +"_" + timestr + ".root"
	self.file = ROOT.TFile(filename, "recreate")
	print "Root file was created: ", filename
	# the tree will be initialized later

     # init tree
    def InitTREE(self, runData):
	# init tree
	self.tree = ROOT.TTree(runData, runData)

        ## create 1 dimensional float arrays (python's float datatype corresponds to c++ doubles)
        # event header
        self.fc7_l1_counter = np.zeros(1, dtype=int)
        self.fc7_bx_counter = np.zeros(1, dtype=int)
        self.tdc = np.zeros(1, dtype=int)
        self.tlu_trigger_id = np.zeros(1, dtype=int)
        # mpa header
        self.mpa_error = np.zeros(1, dtype=int)
        self.mpa_l1_counter = np.zeros(1, dtype=int)
        self.mpa_nsclusters = np.zeros(1, dtype=int)
        self.mpa_npclusters = np.zeros(1, dtype=int)
        # sclusters
        self.mpa_scluster_address = ROOT.std.vector("int")()
        self.mpa_scluster_width = ROOT.std.vector("int")()
        self.mpa_scluster_mip = ROOT.std.vector("int")()
        # pclusters
        self.mpa_pcluster_address = ROOT.std.vector("int")()
        self.mpa_pcluster_width = ROOT.std.vector("int")()
        self.mpa_pcluster_zpos = ROOT.std.vector("int")()
        # stubs
        self.mpa_stub_sync1 = np.zeros(1, dtype=int)
        self.mpa_stub_sync2 = np.zeros(1, dtype=int)
        self.mpa_stub_bx1_nstubs = np.zeros(1, dtype=int)
        self.mpa_stub_column = ROOT.std.vector("int")()
        self.mpa_stub_row = ROOT.std.vector("int")()
        self.mpa_stub_bend = ROOT.std.vector("int")()

        ## create the branches and assign the fill-variables to them
        self.tree.Branch('fc7_l1_counter', self.fc7_l1_counter, 'fc7_l1_counter/I')
        self.tree.Branch('fc7_bx_counter', self.fc7_bx_counter, 'fc7_bx_counter/I')
        self.tree.Branch('tdc', self.tdc, 'tdc/I')
        self.tree.Branch('tlu_trigger_id', self.tlu_trigger_id, 'tlu_trigger_id/I')
        # mpa header
        self.tree.Branch('mpa_error', self.mpa_error, 'mpa_error/I')
        self.tree.Branch('mpa_l1_counter', self.mpa_l1_counter, 'mpa_l1_counter/I')
        self.tree.Branch('mpa_nsclusters', self.mpa_nsclusters, 'mpa_nsclusters/I')
        self.tree.Branch('mpa_npclusters', self.mpa_npclusters, 'mpa_npclusters/I')
        # sclusters
        self.tree.Branch('mpa_scluster_address', self.mpa_scluster_address)
        self.tree.Branch('mpa_scluster_width', self.mpa_scluster_width)
        self.tree.Branch('mpa_scluster_mip', self.mpa_scluster_mip)
        # pclusters
        self.tree.Branch('mpa_pcluster_address', self.mpa_pcluster_address)
        self.tree.Branch('mpa_pcluster_width', self.mpa_pcluster_width)
        self.tree.Branch('mpa_pcluster_zpos', self.mpa_pcluster_zpos)
        # stubs
        self.tree.Branch('mpa_stub_sync1', self.mpa_stub_sync1, 'mpa_stub_sync1/I')
        self.tree.Branch('mpa_stub_sync2', self.mpa_stub_sync2, 'mpa_stub_sync2/I')
        self.tree.Branch('mpa_stub_bx1_nstubs', self.mpa_stub_bx1_nstubs, 'mpa_stub_bx1_nstubs/I')
        self.tree.Branch('mpa_stub_column', self.mpa_stub_column)
        self.tree.Branch('mpa_stub_row', self.mpa_stub_row)
        self.tree.Branch('mpa_stub_bend', self.mpa_stub_bend)

    # fill tuple (event)
    def FillROOTTree(self, event):
        # event header
        self.fc7_l1_counter[0] = event.GetFC7L1Counter()
        self.fc7_bx_counter[0] = event.GetFC7BXCounter()
        self.tdc[0] = event.GetTDC()
        self.tlu_trigger_id[0] = event.GetTriggerId()
        # mpa header
        self.mpa_error[0] = event.GetMPAError()
        self.mpa_l1_counter[0] = event.GetMPAL1Counter()
        self.mpa_nsclusters[0] = event.GetNStripClusters()
        self.mpa_npclusters[0] = event.GetNPixelClusters()
        # scluster
        for cluster in event.GetStripClusters():
            self.mpa_scluster_address.push_back(cluster.address)
            self.mpa_scluster_width.push_back(cluster.width)
            self.mpa_scluster_mip.push_back(cluster.mip_flag)
        # pcluster
        for cluster in event.GetPixelClusters():
            self.mpa_pcluster_address.push_back(cluster.address)
            self.mpa_pcluster_width.push_back(cluster.width)
            self.mpa_pcluster_zpos.push_back(cluster.zpos)
        # stubs
        self.mpa_stub_sync1[0] = event.GetSync1()
        self.mpa_stub_sync2[0] = event.GetSync2()
        self.mpa_stub_bx1_nstubs[0] = event.GetBX1_NStubs()
        for stub in event.GetStubs():
            self.mpa_stub_column.push_back(stub.column)
            self.mpa_stub_row.push_back(stub.row)
            self.mpa_stub_bend.push_back(stub.bend)

        ## fill now
        self.tree.Fill()
        ## clear vectors
        self.mpa_scluster_address.clear()
        self.mpa_scluster_width.clear()
        self.mpa_scluster_mip.clear()
        self.mpa_pcluster_address.clear()
        self.mpa_pcluster_width.clear()
        self.mpa_pcluster_zpos.clear()
        self.mpa_stub_column.clear()
        self.mpa_stub_row.clear()
        self.mpa_stub_bend.clear()

    # write root
    def WriteROOT(self):
	if self.SaveROOT:
		# write the file
		self.file.Close()

    # async data processor
    def DataProcessing(self):
        while True:
            data = self.DataQueue.get()
            if data is None:
                break
            else:
		if self.ZSEnable == 0:
		        nevents = len(data)/self.EventSize
		        self.EventCounter += nevents
		        print "Got " + str(nevents) + " events package (total " + str(self.EventCounter) + ")"
		        for i in range(0, nevents):
		    	    event = PSEventVR(data[i*self.EventSize:(i+1)*self.EventSize])
		            if self.SaveROOT:
		                self.FillROOTTree(event)
		else:
			nevents = 0
			word_id = 0
			while(word_id < len(data)):
				# get the event size from header
				header = data[word_id]
				this_event_size = (header & 0x0000ffff) >> 0
				# construct the event and increment the word id
				event = PSEventZS(data[word_id:word_id+this_event_size])
				word_id += this_event_size
				# increment event counter
				nevents += 1
				# write tuple
				if self.SaveROOT:
		                	self.FillROOTTree(event)				

			self.EventCounter += nevents
			if not (nevents == self.EventsInPacket):
				print "Warning!!! Packet size mismatch"			
				
            self.DataQueue.task_done()

    # data readout
    def GetData(self):
            # read hansahake enable
            handshake_en = fc7.read("cnfg_readout_data_handshake_enable")
	    # read zs enable
	    zs_enable = fc7.read("cnfg_readout_zero_suppression_enable")
	    if(zs_enable != self.ZSEnable):
		print "Error ZS does not the equal the one on board"
		exit(1)

	    # timers
	    timer = 0
	    time_start = time.time()
	    spill_events = 0
	    since_timeout_time = 0

            # no handshake mode
            if handshake_en == 0:
		# fail
		if zs_enable == 1:
			print "Error ZS mode only in handshake enabled mode"
			exit(1)
                # wait for events
                while(True):
                    # break when requested run stop
                    if self.run_stop_requested:
                        return
		    # print out
                    if timer >= 100:
                        timer = 0
			spill_time = time.time()-time_start-1.0-since_timeout_time*0.01
                        print "Waiting for data (spill time = ", ("%0.2f" % spill_time), ", spill events = ", ("%0.2f" % spill_events), ", spill rate = ", ("%0.2f" % (spill_events/spill_time/1000) ), "kHz)"
			spill_events = 0
			since_timeout_time = 0
			time_start = time.time()
                    else:
			sleep(0.01)
                        timer += 1
                    # read data
                    nwords = fc7.read("words_cnt")
                    nevents = (int)(nwords/self.EventSize)
                    if nevents > 0:
                        # reset print timer and time (since timeout is used to set more precise frequency measurement)
			if since_timeout_time == 0:
				since_timeout_time += timer	
                        timer = 0
			spill_events += nevents
                        # read events
                        if self.IsDDR3Readout:
                            if(self.DDR3Offset+nevents*self.EventSize > 134217727):
                                self.DDR3Offset = 0
                            REC_DATA = fc7.blockRead("ddr3_readout", nevents*self.EventSize, self.DDR3Offset)
                        else:
                            REC_DATA = fc7.fifoRead("ctrl_readout_run_fifo", nevents*self.EventSize)
                        # process data
                        self.DataQueue.put(REC_DATA)
            # data handshake mode
            else:                

                while(True):
                    # break when requested run stop
                    if self.run_stop_requested:
                        return
                    # print out
                    if timer >= 100:
                        timer = 0
			# 0.4 is tolerance of timer+=1
			spill_time = time.time()-time_start-1.0-since_timeout_time*0.01
                        print "Waiting for data (spill time = ", ("%0.2f" % spill_time), ", spill events = ", ("%0.2f" % spill_events), ", spill rate = ", ("%0.2f" % (spill_events/spill_time/1000) ), "kHz)"
			spill_events = 0
			since_timeout_time = 0
			time_start = time.time()
                    else:
			sleep(0.01)
                        timer += 1

                    # data readout
                    if(fc7.read("readout_req") == 1):
                        # reset print timer and time (since timeout is used to set more precise frequency measurement)
			if since_timeout_time == 0:
				since_timeout_time += timer	
                        timer = 0
                        # get data
                        nwords = fc7.read("words_cnt")
			nevents = self.EventsInPacket
                        if self.IsDDR3Readout:
                            REC_DATA = fc7.blockRead("ddr3_readout", nwords, 0)
                        else:
                            REC_DATA = fc7.fifoRead("ctrl_readout_run_fifo", nwords)
			spill_events += nevents
                        # process data
                        self.DataQueue.put(REC_DATA)

