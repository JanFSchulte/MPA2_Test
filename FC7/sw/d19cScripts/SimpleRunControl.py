## for the i2c control we need to import scripts of Davide
from sys import path
path.append('/home/harankom/Soft/MPA_Test')

from PSDAQ import *
from mpa_methods.mpa_i2c_conf import *
import numpy as np
import matplotlib.pyplot as plt

## methods

def ConvertLatencyTDC(latency, tdc):
	return float(tdc/8.) + latency

# 0 - stub, 1 - trigger
def FindLatency(npoints = 5000, latency_type = "hit"):

	# overwrite the number of triggers
	fc7.write("fc7_daq_cnfg.fast_command_block.triggers_to_accept", npoints)
	# also disable resync
	fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.en_fast_reset", 0)
	# some delays
	fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_fast_reset", 50)
  	fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_after_test_pulse", 60)
  	fc7.write("fc7_daq_cnfg.fast_command_block.test_pulse.delay_before_next_pulse", 200)
	sleep(0.01)
        fc7.write("fc7_daq_ctrl.fast_command_block.control.load_config", 1)

	if latency_type == "stub":
		SCANTYPE = 0
	elif latency_type == "hit":
		SCANTYPE = 1
	else:
		print "Error. Wrong Scan type"
		exit(1)

	# latency range
	if SCANTYPE == 0:
		latency_min = 27
		latency_range = 3
	else:
		latency_min = 58
		latency_range = 7


        #latency_min = 24
	#latency_range = 10
	#latency = 62
	#stub_latency = 28

	TDC_bins = 8
	n_pixel_clusters = [0]*(latency_range*TDC_bins)
	n_strip_clusters = [0]*(latency_range*TDC_bins)
	n_stubs = [0]*(latency_range*TDC_bins)
	latency_list = []
	
	for latency in range(latency_min,latency_min+latency_range):
		if SCANTYPE == 0:
			# stub latency
			fc7.write("cnfg_readout_common_stubdata_delay", latency)
		else:
			# set the latency
			I2C.row_write("L1Offset_1", 0, (0x00FF & latency) >> 0)
			I2C.row_write("L1Offset_2", 0, (0x0100 & latency) >> 8)

		# start run
		runData = ""
		if SCANTYPE == 0:
			runData += "stub_latency_"
		else:
			runData += "data_latency_"
		runData += str(latency)
		DAQController.StartRun(runProcessor = False, runData = runData)

		# process data
		npixel_clusters = 0
		nstrip_clusters = 0
		nstubs = 0
		while (DAQController.EventCounter < npoints):
		    if not DAQController.DataQueue.empty():
			RAWData = DAQController.DataQueue.get()
			if RAWData is None:
			    pass
			else:
			    if DAQController.ZSEnable == 0:
				nevents = len(RAWData)/DAQController.EventSize
				DAQController.EventCounter += nevents
				print "Got " + str(nevents) + " events package (total " + str(DAQController.EventCounter) + ")"
				for i in range(0, nevents):
					# create d19c event
					d19cEvent = PSEventVR(RAWData[i*DAQController.EventSize:(i+1)*DAQController.EventSize])
					# store into root file if needed
					if DAQController.SaveROOT:
					    DAQController.FillROOTTree(d19cEvent)
					# process latency
					npixel_clusters += d19cEvent.GetNPixelClusters()
					nstrip_clusters += d19cEvent.GetNStripClusters()
					TDC = d19cEvent.GetTDC()
					nstubs += len(d19cEvent.GetStubs())
					time = (latency-latency_min)*25+TDC*3.125
					n_pixel_clusters[int(time/3.125)] = n_pixel_clusters[int(time/3.125)] + d19cEvent.GetNPixelClusters()
					n_strip_clusters[int(time/3.125)] = n_strip_clusters[int(time/3.125)] + d19cEvent.GetNStripClusters()			
					n_stubs[int(time/3.125)] = n_stubs[int(time/3.125)] + len(d19cEvent.GetStubs())	
					if SCANTYPE == 0: 			
						for i in range(0, len(d19cEvent.GetStubs())):
							latency_list.append(ConvertLatencyTDC(latency, TDC))
					else:
						for i in range(0, d19cEvent.GetNPixelClusters()):
							latency_list.append(ConvertLatencyTDC(latency, TDC))
			    else:
				nevents = 0
				word_id = 0
				while(word_id < len(RAWData)):
					# get the event size from header
					header = RAWData[word_id]
					this_event_size = (header & 0x0000ffff) >> 0
					# construct the event and increment the word id
					d19cEvent = PSEventZS(RAWData[word_id:word_id+this_event_size])
					word_id += this_event_size
					# increment event counter
					nevents += 1
					# write tuple
					if DAQController.SaveROOT:
						DAQController.FillROOTTree(d19cEvent)	
					# process latency
					npixel_clusters += d19cEvent.GetNPixelClusters()
					nstrip_clusters += d19cEvent.GetNStripClusters()
					TDC = d19cEvent.GetTDC()
					nstubs += len(d19cEvent.GetStubs())
					time = (latency-latency_min)*25+TDC*3.125
					n_pixel_clusters[int(time/3.125)] = n_pixel_clusters[int(time/3.125)] + d19cEvent.GetNPixelClusters()
					n_strip_clusters[int(time/3.125)] = n_strip_clusters[int(time/3.125)] + d19cEvent.GetNStripClusters()			
					n_stubs[int(time/3.125)] = n_stubs[int(time/3.125)] + len(d19cEvent.GetStubs())	
					if SCANTYPE == 0: 			
						for i in range(0, len(d19cEvent.GetStubs())):
							latency_list.append(ConvertLatencyTDC(latency, TDC))
					else:
						for i in range(0, d19cEvent.GetNPixelClusters()):
							latency_list.append(ConvertLatencyTDC(latency, TDC))			

				DAQController.EventCounter += nevents
				if not (nevents == DAQController.EventsInPacket):
					print "Warning!!! Packet size mismatch"	
			DAQController.DataQueue.task_done()
		# print the latency
		if SCANTYPE == 0:
			print "Stub Latency: ", latency, ", N Pixel Clusters: ", npixel_clusters, ", N Strip Clusters: ", nstrip_clusters, " N Stubs: ", nstubs
		else:
			print "Trigger Latency: ", latency, ", N Pixel Clusters: ", npixel_clusters, ", N Strip Clusters: ", nstrip_clusters, " N Stubs: ", nstubs

		# stop run	
		DAQController.StopRun()
	latency_and_TDC = np.arange(latency_min*25,(latency_min+latency_range)*25,3.125)
	plt.figure(1)
	plt.hist(latency_list, bins=np.arange(latency_min, latency_min+latency_range, 0.125))
	plt.grid(True)
	plt.figure(2)
	if SCANTYPE == 0:
		plt.ylabel("N Stub")
		plt.plot(latency_and_TDC,n_stubs, 'b-')
		np.savetxt('stub_latency_scan.out', np.c_[latency_and_TDC, n_stubs]) 
	else:
		plt.ylabel("N Pixel Clusters")
		plt.plot(latency_and_TDC,n_pixel_clusters, 'b-')
		np.savetxt('trigger_latency_scan.out', np.c_[latency_and_TDC, n_pixel_clusters]) 
	plt.xlabel("latency (ns)")
	print latency_and_TDC
	plt.show()

		
## run program

## settings
# external clock enable
ext_clock_en = 0
# trigger source (1 - ttc, 2 - stubs, 3 - user frequency (1mhz), 4 - tlu, 5 - ext, 6 - cal pulse, 7 - consecutive, 8 - antenna)
trigger_source = 3
# external trigger delay (for both tlu and ext)
ext_trigger_delay = 50
# if disabled has to be treated by the tlu or trigger board
backpressure_en = 1
# no stubs on this beam test
stub_trigger_delay = 60
stub_veto_length = 50
readout_stub_delay = 28
# npackets in the readout package
npackets = 499
# enable handshake
handshake_en = 1
# enable zs
zs_enable = 0
# enable dio5/tlu
dio5_tlu_enable = 0

## start
# init daq controller
DAQController = PSDAQ(EmulatorMode = False)
# configure everything
DAQController.ConfigureAll(ext_clock_en, trigger_source, ext_trigger_delay, 
                           backpressure_en, stub_trigger_delay, 
                           stub_veto_length, npackets, handshake_en, zs_enable, 
                           readout_stub_delay, dio5_tlu_enable)
DAQController.InitROOT("scan")
#raw_input("\n\nConfigured. Press enter to continue...\n\n")

# run find latency
FindLatency()

## write root file
#DAQController.WriteROOT()
#FindLatency(npoints = 100)


