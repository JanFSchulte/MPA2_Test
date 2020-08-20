from PyChipsUser import *

# strip cluster
class SCluster:
    def __init__(self, address, width, mip_flag):
        self.address = address
        self.width = width
        self.mip_flag = mip_flag
    def __str__(self):
        return "\t" + '%15s' % self.address + '%15s' % self.width + '%15s' % self.mip_flag + "\n"

# pixel cluster
class PCluster:
    def __init__(self, address, width, zpos):
        self.address = address
        self.width = width
        self.zpos = zpos
    def __str__(self):
        return "\t" + '%15s' % self.address + '%15s' % self.width + '%15s' % self.zpos + "\n"

# stub
class Stub:
    def __init__(self, column, row, bend):
        self.column = column
        self.row = row
        self.bend = bend
    def __str__(self):
        return "\t" + '%15s' % self.column + '%15s' % self.row + '%15s' % self.bend + "\n"

# ps event defintion (includes parser and print methods)
class PSEvent(object):
    # init (includes parser)
    def __init__(self, data):
	# set base 
	self.event_header_size = 6
        self.data_raw = data
        
        ## parsing
        # event header
        tmp_event_size = (data[0] & 0x0000ffff) >> 0
        if(tmp_event_size != self.event_size):
            print "Error, wrong event size in event header"
            exit(1)
        tmp_fe_mask = (data[0] & 0x00ff0000) >> 16
        if(tmp_fe_mask != 1):
            print "Error, wrong fe mask"
            exit(1)
        self.fc7_l1_counter = (data[2] & 0x00ffffff) >> 0
        self.fc7_bx_counter = data[3]

        self.tdc = (data[4] & 0x000000ff) >> 0
	# fix the tdc value
	if self.tdc >= 5:
        	self.tdc-=5
        else:
        	self.tdc+=3


        self.tlu_trigger_id = (data[4] & 0x007fff00) >> 8
        tmp_chip_mask = (data[5] & 0xff000000) >> 24
        if(tmp_chip_mask != 1):
            print "Error, wrong chip mask"
            exit(1)        

    # get methods
    def GetRawData(self):
        return self.raw_data
    def GetFC7L1Counter(self):
        return self.fc7_l1_counter
    def GetFC7BXCounter(self):
        return self.fc7_bx_counter
    def GetTDC(self):
        return self.tdc
    def GetTriggerId(self):
        return self.tlu_trigger_id

    def GetMPAError(self):
        pass

    def GetMPAL1Counter(self):
        pass

    def GetNStripClusters(self):
        pass

    def GetStripClusters(self):
        pass

    def GetNPixelClusters(self):
        pass

    def GetPixelClusters(self):
        pass

    def GetSync1(self):
        pass
    def GetSync2(self):
        pass
    def GetBX1_NStubs(self):
        pass
    def GetStubs(self):
        pass

    # print event method
    def __str__(self):
        #return uInt32HexListStr(self.data_raw[0:self.event_size])
        event_header = "## Event Header \n\tEvent Size: " + str(self.event_size) + "\n\tL1 Counter: " + str(self.fc7_l1_counter) + "\n\tBX Counter: " + str(self.fc7_bx_counter) + "\n\tTDC: " + str(self.tdc) + "\n\tTLU Trigger ID: " + str(self.tlu_trigger_id) + "\n"
        mpa_header = "## MPA 0 Data \n\tError: " + str(self.GetMPAError()) + "\n\tL1 Counter: " + str(self.GetMPAL1Counter()) + "\n\tN Strip Clusters: " + str(self.GetNStripClusters()) + "\n\tN Pixel Clusters: " + str(self.GetNPixelClusters()) + "\n"
        sclusters = "## Strip Clusters: \n\t" + '%15s' % "Address" + '%15s' % "Width" + '%15s' % "MIP\n"
        for cluster in self.GetStripClusters():
            sclusters += cluster.__str__()
        pclusters = "## Pixel Clusters: \n\t" + '%15s' % "Address" + '%15s' % "Width" + '%15s' % "Z Position\n"
        for cluster in self.GetPixelClusters():
            pclusters += cluster.__str__()
        stubs = "## Stubs (sync1 = " + str(self.GetSync1()) + ", sync2 = " + str(self.GetSync2()) + ", bx1_nstubs = " + str(self.GetBX1_NStubs()) + "): \n\t" + '%15s' % "Column" + '%15s' % "Row" + '%15s' % "Bend\n"
        for stub in self.GetStubs():
            stubs += stub.__str__()
        return event_header + mpa_header + sclusters + pclusters + stubs

# ps event virgin raw defintion (includes parser and print methods)
class PSEventVR(PSEvent):
    # init (includes parser)
    def __init__(self, data):
        # raw and size
        self.event_size = len(data)
        
        ## call the parent header parsing
        super(PSEventVR, self).__init__(data)

        # mpa data
        self.mpa_data = data[self.event_header_size:self.event_size]

        ## stub header
        # the id of the first stub word
        stub_word0_id = 1 + 12 + 16
        sync1 = (self.mpa_data[stub_word0_id + 2] & 0x02000000) >> 25
        sync2 = (self.mpa_data[stub_word0_id + 2] & 0x01000000) >> 24
        if (sync1 != 1):
	    	print "Error! sync1 is not 1"
	    	print uInt32HexListStr(data[0:self.event_size])
	    	exit(1)
        if (sync2 != 0):
	    	print "Error! sync2 is not 0"
	    	print uInt32HexListStr(data[0:self.event_size])
	    	exit(1)

    ## override methods
    def GetMPAError(self):
        return (self.mpa_data[0] & 0x00000003) >> 0

    def GetMPAL1Counter(self):
        return (self.mpa_data[0] & 0x00001ff0) >> 4

    def GetNStripClusters(self):
        return (self.mpa_data[0] & 0x001f0000) >> 16

    def GetStripClusters(self):
        # strip clusters parsing
        scluster_list = []
        word_id = 0
        while(2*word_id < self.GetNStripClusters()):
            word = self.mpa_data[1 + word_id]
            # if the while above passed - this strip is for sure not zero
            address_0 = ((word & 0x0000007f) >> 0) - 1
            mip_0 = (word & 0x00000080) >> 7
            width_0 = (word & 0x00000700) >> 8
            scluster_list.append(SCluster(address_0, width_0, mip_0))
            # now let's check if the second cluster is here
            if((self.GetNStripClusters()-2*word_id) > 1):
                address_1 = ((word & 0x007f0000) >> 16) - 1
                mip_1 = (word & 0x00800000) >> 23
                width_1 = (word & 0x07000000) >> 24
                scluster_list.append(SCluster(address_1, width_1, mip_1))

            # increment
            word_id += 1

        # return
        return scluster_list

    def GetNPixelClusters(self):
        return (self.mpa_data[0] & 0x1f000000) >> 24

    def GetPixelClusters(self):
        # pixel clusters parser
        pcluster_list = []
        word_id = 0
        while(2*word_id < self.GetNPixelClusters()):
            word = self.mpa_data[1 + 12 + word_id]
            # if the while above passed - this strip is for sure not zero
            address_0 = ((word & 0x0000007f) >> 0) - 1
            width_0 = (word & 0x00000380) >> 7
            zpos_0 =  (word & 0x00003C00) >> 10
            pcluster_list.append(PCluster(address_0, width_0, zpos_0))
            # now let's check if the second cluster is here
            if((self.GetNPixelClusters()-2*word_id) > 1):
                address_1 = ((word & 0x007f0000) >> 16) - 1
                width_1 = (word & 0x03800000) >> 23
                zpos_1 =  (word & 0x3C000000) >> 26
                pcluster_list.append(PCluster(address_1, width_1, zpos_1))

            # increment
            word_id += 1

        return pcluster_list

    def GetSync1(self):
        # the id of the first stub word
        stub_word0_id = 1 + 12 + 16
        return (self.mpa_data[stub_word0_id + 2] & 0x02000000) >> 25
    def GetSync2(self):
        # the id of the first stub word
        stub_word0_id = 1 + 12 + 16
        return (self.mpa_data[stub_word0_id + 2] & 0x01000000) >> 24
    def GetBX1_NStubs(self):
        # the id of the first stub word
        stub_word0_id = 1 + 12 + 16
        return (self.mpa_data[stub_word0_id + 2] & 0x00070000) >> 16
    def GetStubs(self):
        # the id of the first stub word
        stub_word0_id = 1 + 12 + 16
        # stub parser
        stub_list = []
        for i in range(0,5):
            word_id = stub_word0_id + int(i/2)
            word = self.mpa_data[word_id]
            if(i%2 == 0):
                column = (word & 0x000000ff) >> 0
                row = (word & 0x00000f00) >> 8
                bend = (word & 0x00007000) >> 12
                if(column != 0):
                    stub_list.append(Stub(column,row,bend))
            if(i%2 == 1):
                column = (word & 0x00ff0000) >> 16
                row = (word & 0x0f000000) >> 24
                bend = (word & 0x70000000) >> 28
                if(column != 0):
                    stub_list.append(Stub(column,row,bend))

        return stub_list

# ps event zero suppressed defintion (includes parser and print methods)
class PSEventZS(PSEvent):
    # init (includes parser)
    def __init__(self, data):
        # raw and size
        self.event_size = len(data)        
        
        ## call the parent header parsing
        super(PSEventZS, self).__init__(data)

        # mpa data
        self.mpa_data = data[self.event_header_size:self.event_size]

        ## stub header
        # the id of the first stub word (header + nStrip Words + nPixel Words)
        stub_word0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters()) + self.DivideBy2RoundUp(self.GetNPixelClusters())
        sync1 = (self.mpa_data[stub_word0_id + 2] & 0x02000000) >> 25
        sync2 = (self.mpa_data[stub_word0_id + 2] & 0x01000000) >> 24
        if (sync1 != 1):
	    	print "Error! sync1 is not 1"
	    	print uInt32HexListStr(data[0:self.event_size])
	    	exit(1)
        if (sync2 != 0):
	    	print "Error! sync2 is not 0"
	    	print uInt32HexListStr(data[0:self.event_size])
	    	exit(1)

    ## divide by 2 round up (for word id)
    def DivideBy2RoundUp(self, value):
	return (value + value%2)/2

    ## override methods
    def GetMPAError(self):
        return (self.mpa_data[0] & 0x00000003) >> 0

    def GetMPAL1Counter(self):
        return (self.mpa_data[0] & 0x00001ff0) >> 4

    def GetNStripClusters(self):
        return (self.mpa_data[0] & 0x001f0000) >> 16

    def GetStripClusters(self):
        # strip clusters parsing
        scluster_list = []
	strip_word_0_id = 1
        word_id = 0
        while(2*word_id < self.GetNStripClusters()):
            word = self.mpa_data[strip_word_0_id + word_id]
            # if the while above passed - this strip is for sure not zero
            address_0 = ((word & 0x0000007f) >> 0) - 1
            mip_0 = (word & 0x00000080) >> 7
            width_0 = (word & 0x00000700) >> 8
            scluster_list.append(SCluster(address_0, width_0, mip_0))
            # now let's check if the second cluster is here
            if((self.GetNStripClusters()-2*word_id) > 1):
                address_1 = ((word & 0x007f0000) >> 16) - 1
                mip_1 = (word & 0x00800000) >> 23
                width_1 = (word & 0x07000000) >> 24
                scluster_list.append(SCluster(address_1, width_1, mip_1))

            # increment
            word_id += 1

        # return
        return scluster_list

    def GetNPixelClusters(self):
        return (self.mpa_data[0] & 0x1f000000) >> 24

    def GetPixelClusters(self):
        # pixel clusters parser
        pcluster_list = []
	pixel_word_0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters())
        word_id = 0
        while(2*word_id < self.GetNPixelClusters()):
            word = self.mpa_data[pixel_word_0_id + word_id]
            # if the while above passed - this strip is for sure not zero
            address_0 = ((word & 0x0000007f) >> 0) - 1
            width_0 = (word & 0x00000380) >> 7
            zpos_0 =  (word & 0x00003C00) >> 10
            pcluster_list.append(PCluster(address_0, width_0, zpos_0))
            # now let's check if the second cluster is here
            if((self.GetNPixelClusters()-2*word_id) > 1):
                address_1 = ((word & 0x007f0000) >> 16) - 1
                width_1 = (word & 0x03800000) >> 23
                zpos_1 =  (word & 0x3C000000) >> 26
                pcluster_list.append(PCluster(address_1, width_1, zpos_1))

            # increment
            word_id += 1

        return pcluster_list

    def GetSync1(self):
        # the id of the first stub word
        stub_word0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters()) + self.DivideBy2RoundUp(self.GetNPixelClusters())
        return (self.mpa_data[stub_word0_id + 2] & 0x02000000) >> 25
    def GetSync2(self):
        # the id of the first stub word
        stub_word0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters()) + self.DivideBy2RoundUp(self.GetNPixelClusters())
        return (self.mpa_data[stub_word0_id + 2] & 0x01000000) >> 24
    def GetBX1_NStubs(self):
        # the id of the first stub word
        stub_word0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters()) + self.DivideBy2RoundUp(self.GetNPixelClusters())
        return (self.mpa_data[stub_word0_id + 2] & 0x00070000) >> 16
    def GetStubs(self):
        # the id of the first stub word
        stub_word0_id = 1 + self.DivideBy2RoundUp(self.GetNStripClusters()) + self.DivideBy2RoundUp(self.GetNPixelClusters())
        # stub parser
        stub_list = []
        for i in range(0,5):
            word_id = stub_word0_id + int(i/2)
            word = self.mpa_data[word_id]
            if(i%2 == 0):
                column = (word & 0x000000ff) >> 0
                row = (word & 0x00000f00) >> 8
                bend = (word & 0x00007000) >> 12
                if(column != 0):
                    stub_list.append(Stub(column,row,bend))
            if(i%2 == 1):
                column = (word & 0x00ff0000) >> 16
                row = (word & 0x0f000000) >> 24
                bend = (word & 0x70000000) >> 28
                if(column != 0):
                    stub_list.append(Stub(column,row,bend))

        return stub_list

