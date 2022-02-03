#!/usr/bin/env python2
from sys import path
path.append('/home/readout/ILCSoft/v01-19-02/Eutelescope/master/external/eudaq/v1.7-dev/python')
from PyEUDAQWrapper import * # load the ctypes wrapper
from PSDAQ import *
import argparse

## simple eudaq producer class (fsm)
class EUDAQProducer:
    ## class init
    def __init__(self, ip = "localhost"):
        ## instance of the psdaq
        # init daq controller
        print "-> Creating the DAQController instance"
        self.DAQController = PSDAQ(EmulatorMode = False)

        ## start producer
        print "-> Initialising the EUDAQProducer"
        # create PyProducer instance
        self.pp = PyProducer("Ph2Event","tcp://"+ip+":44000")

        ## producer variables
        self.waittime = 1.0
        self.state = "Init"

        ## run settings
        # external clock enable
        self.ext_clock_en = 0
        # trigger source (1 - ttc, 2 - stubs, 3 - user frequency (1mhz), 4 - tlu, 5 - ext, 6 - cal pulse, 7 - consecutive, 8 - antenna)
        self.trigger_source = 4
        # external trigger delay (for both tlu and ext)
        self.ext_trigger_delay = 50
        # if disabled has to be treated by the tlu or trigger board
        self.backpressure_en = 1
        # no stubs on this beam test
        self.stub_trigger_delay = 200
        self.stub_veto_length = 50
	# latency is this plus 34
        self.readout_stub_delay = 28
        # npackets in the readout package
        self.npackets = 499
        # enable handshake
        self.handshake_en = 1
	# enable zero suppression
	self.zs_enable = 0
        # enable dio5/tlu
        self.dio5_tlu_enable = 1

    ## event converter (from d19c into eudaq)
    def ConvertEvent(self, d19cEvent):
        # find the full size of the event array
        array_size = 0
        numhits = 0
        # iterate over the clusters
        for pcluster in d19cEvent.GetPixelClusters():
            # iterate over the pixels in cluster
            for pixel in range(pcluster.width+1):
                numhits += 1
        # add header also(3 words)
        array_size = 3*numhits + 3
        # now create the array
        Ph2EventArray = np.zeros(array_size, dtype=np.uint16)

        # n columns
        Ph2EventArray[0] = 120
        # n rows
        Ph2EventArray[1] = 16
        # nhits
        Ph2EventArray[2] = (0x8000 | numhits)

        # array index iterator
        array_index = 3
        # iterate over the clusters
        for pcluster in d19cEvent.GetPixelClusters():
            # iterate over the pixels in cluster
            for pixel in range(pcluster.width+1):
                Ph2EventArray[array_index] = pcluster.address + pixel # 0-119
                Ph2EventArray[array_index+1] = pcluster.zpos #zpos is 0-15
                Ph2EventArray[array_index+2] = 1
                array_index += 3

        # return
        return Ph2EventArray

    ## setting the event tag data
    def SetTagData(self, d19cEvent):
        tagdata = np.zeros(13, dtype=np.uint32)

        tagdata[0] = d19cEvent.GetFC7L1Counter()
        tagdata[1] = d19cEvent.GetFC7BXCounter()
        tagdata[2] = d19cEvent.GetTDC()
        tagdata[3] = d19cEvent.GetTriggerId()
        tagdata[4] = d19cEvent.GetMPAError()
        tagdata[5] = d19cEvent.GetMPAL1Counter()
        tagdata[6] = d19cEvent.GetNStripClusters()
        tagdata[7] = d19cEvent.GetNPixelClusters()
	stubs = d19cEvent.GetStubs()
	nstubs = len(stubs)
	for s_id in range(0,5):
		if s_id < nstubs:
			tagdata[8+s_id] = (stubs[s_id].column & 0xFF) + ((stubs[s_id].row & 0x0F) << 8) + ((stubs[s_id].bend & 0x07) << 16)
		else:
			tagdata[8+s_id] = 0

        return tagdata

    ## defines the fsm (allowed states: Init, Configuring, Configured, Starting, Running, Stopping, Stopped, Error, Terminating)
    def RunFSM(self):
        # make sure the initial state is init
        self.state = "Init"
        # prev state for print out
        prev_state = "None"

        ## start the fsm
        while True:
            # printout
            if self.state != prev_state:
                print "-> State: " + self.state
            prev_state = self.state

            # fsm here
            if self.state == "Init":
                # wait for configure cmd from RunControl
                if self.pp.Configuring:
                    self.state = "Configuring"
                else:
                    sleep(self.waittime)

            elif self.state == "Configuring":
                # check if configuration received
                #print "Ready to configure, received config string 'Parameter'=",pp.GetConfigParameter("Parameter")
                # configure everything
                self.DAQController.ConfigureAll(self.ext_clock_en, self.trigger_source, self.ext_trigger_delay, self.backpressure_en, self.stub_trigger_delay, self.stub_veto_length, self.npackets, self.handshake_en, self.zs_enable, self.readout_stub_delay, self.dio5_tlu_enable)
                # send configuration done
                self.pp.Configuring = True
                # transit to the configured state
                self.state = "Configured"

            elif self.state == "Configured":
                # some ways to escape this state
                if self.pp.Configuring:
                    self.state = "Configuring"
                elif self.pp.StartingRun:
                    # check for start of run cmd from RunControl
                    self.state = "Starting"
                else:
                    sleep(self.waittime)

            elif self.state == "Starting":
		# init root file
		self.DAQController.InitROOT("run_" + str(self.pp.RunNumber))
                # start run (we will do our own run processing - so no one cares)
                self.DAQController.StartRun(runProcessor = False)
                self.pp.StartingRun = True # set status and send BORE
                # go to running state
		self.firstEvent = True
                self.state = "Running"

            elif self.state == "Running":
                # workloop
                # to preserve the logic of the FSM, we should use IF there, but then we would have to check the previous states every time,
                # which is a bit resource consuming, so let's create a second loop
                while not self.pp.Error and not self.pp.StoppingRun and not self.pp.Terminating:
                    if not self.DAQController.DataQueue.empty():
                        RAWData = self.DAQController.DataQueue.get()
                        if RAWData is None:
                            pass
                        else:
				if self.DAQController.ZSEnable == 0:
					nevents = len(RAWData)/self.DAQController.EventSize
					self.DAQController.EventCounter += nevents
					print "Got " + str(nevents) + " events package (total " + str(self.DAQController.EventCounter) + ")"
					for i in range(0, nevents):
						# create d19c event
						d19cEvent = PSEventVR(RAWData[i*self.DAQController.EventSize:(i+1)*self.DAQController.EventSize])
						# store into root file if needed
						if self.DAQController.SaveROOT:
						    self.DAQController.FillROOTTree(d19cEvent)
						# create eudaq event (Ph2Event)
						Ph2EventArray = self.ConvertEvent(d19cEvent)
						TagData = self.SetTagData(d19cEvent)
						# send event off
						self.pp.SendEvent(Ph2EventArray, TagData)
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
						if self.DAQController.SaveROOT:
							self.DAQController.FillROOTTree(d19cEvent)
						# create eudaq event (Ph2Event)
						Ph2EventArray = self.ConvertEvent(d19cEvent)
						TagData = self.SetTagData(d19cEvent)
						# send event off
						self.pp.SendEvent(Ph2EventArray, TagData)
					# end of packet					
					self.DAQController.EventCounter += nevents
					if not (nevents == self.DAQController.EventsInPacket):
						print "Warning!!! Packet size mismatch"	
					print "Got " + str(nevents) + " events package (total " + str(self.DAQController.EventCounter) + ")"
	
				
			self.DAQController.DataQueue.task_done()
                # when the loop is over - do the transition to stopped, which will be overrriden in case of error or terminating
                if self.pp.StoppingRun:
                    self.state = "Stopping"

            elif self.state == "Stopping":
                # stop run
                self.DAQController.StopRun()
		self.DAQController.WriteROOT()
                # send status
                self.pp.StoppingRun=True # set status and send EORE
                # change state
                self.state = "Stopped"

            elif self.state == "Stopped":
                # some ways to escape this state
                if self.pp.Configuring:
                    self.state = "Configuring"
                elif self.pp.StartingRun:
                    self.state = "Starting"
                else:
                    sleep(self.waittime)

            elif self.state == "Error":
                # go to terminating then
                self.state = "Terminating"
            elif self.state == "Terminating":
                ## finitoo!!!
                break
            else:
                # go to error state then
                self.state = "Error"

            ## override the state if terminating is called from outside
            if self.pp.Terminating:
                self.state = "Terminating"
            elif self.pp.Error:
                self.state = "Error"


## run
if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='EUDAQ Producer for PS Modules + d19c')
    parser.add_argument('--ip', required=False,default="localhost")
    args = parser.parse_args()

    # run producer
    producer = EUDAQProducer(ip = args.ip)
    producer.RunFSM()
    print "Execution DONE!!! Bye-bye"


