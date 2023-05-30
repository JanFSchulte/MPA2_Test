import _thread
import time
import pyvisa

class keithley2410:
    def __init__(self,device='ASRL5::INSTR',voltage=0,currentlimit=1E-4,speed=10):
        self.rm = pyvisa.ResourceManager() #Always create a resource manager. Don't question. Just do.
        print(self.rm.list_resources()) #Identify the address of your instrument.
        #self.keithley = self.rm.open_resource('ASRL5::INSTR') #Name and open a connection with your instrument.
        self.keithley = self.rm.open_resource(str(self.rm.list_resources()[-1]),read_termination = '\r',write_termination = '\r')
        self.keithley.timeout = 10000
        print(self.keithley.query('*IDN?')) #Check that the instrument is the right one.

        self.keithley.write('*RST')
        self.keithley.write(':OUTP:STAT OFF')
        self.keithley.write(':SENS:CURR:RANG '+str(currentlimit))
        self.keithley.write(':SENS:CURR:PROT:LEV '+str(currentlimit))
        self.keithley.write(':SENS:CURR:NPLC '+str(speed))
        self.keithley.write(':SOUR:VOLT:MODE FIX')
        self.keithley.write(':SOUR:VOLT:RANG 800')
        self.keithley.write(':SOUR:VOLT:LEV:IMM '+str(voltage))
        self.readout = True
        self.readoutdata = []

    def __del__(self):
        self.disableOutput()
        self.readout = False

    def setVoltage(self,voltage=0):
        return int(self.keithley.write(':SOUR:VOLT:LEV:IMM '+str(voltage)))

    def setVoltageSlow(self,voltage=0,step=10,delay=0.25):
        data = self.getData()
        currentvoltage = data[0]
        mystep = step
        status = 0
        #print("Vcurr="+str(currentvoltage)+" Vgol="+str(voltage))
        if mystep == 0: mystep = 10.
        if (voltage < currentvoltage) and mystep>0: mystep = -1*mystep
        if (voltage > currentvoltage) and mystep<0: mystep = -1*mystep
        while abs(voltage-currentvoltage)>abs(mystep):
            #print(voltage,currentvoltage+mystep,currentvoltage,mystep)
            status = self.setVoltage(currentvoltage+mystep)
            data = self.getData()
            time.sleep(delay)
            #print("Vcurr="+str(data[0])+" Vset="+str(currentvoltage+mystep)+" Vgol="+str(voltage))
            currentVoltage = data[0]
            currentvoltage = currentvoltage+step
            if self.checkCompliance(): break
        #if (currentvoltage+mystep)!=voltage:
        status = self.setVoltage(voltage)
        #print("V="+str(self.getData()[0]))
        return status

    def setVoltageRange(self,voltage=1000):
        return int(self.keithley.write(':SOUR:VOLT:RANG '+str(voltage)))

    def getData(self):
        listData = self.keithley.query(':READ?').split(',')
        Data = [float(i) for i in listData]
        return Data

    def setCurrentProtection(self,value=.0001):
        compliance = int(self.keithley.write(':SENS:CURR:PROT:LEV '+str(value)))
        limit = int(self.keithley.write(':SENS:CURR:RANG '+str(0.0005)))
        return (compliance | limit)

    def checkCompliance(self):
        return int(self.keithley.query(':SENS:CURR:PROT:TRIP?'))

    def enableOutput(self):
        return int(self.keithley.write(':OUTP:STAT ON'))

    def disableOutput(self):
        return int(self.keithley.write(':OUTP:STAT OFF'))

    def IVScan(self,VStart=0,VStop=-801,VStep=-10,delay=0.25):
        IVdata=[]
        self.setVoltageSlow(VStart)
        for voltage in range(VStart,VStop,VStep):
            status = self.setVoltage(voltage)
            time.sleep(delay)
            data = self.getData()
            IVdata.append([data[0],data[1]*1000000])
            if self.checkCompliance(): break
        self.setVoltageSlow(0)
        return IVdata

    def disableReadout(self):
        self.readout = False

    def __continuousReadout(self, delay):
        start = time.time()
        while self.readout:
            data = self.getData()
            self.readoutdata.append([time.time()-start, data[0], data[1]*1000000])
            time.sleep(delay)

    def getReadoutData(self):
        return self.readoutdata

    def startReadout(self, delay=5):
        self.readout = True
        thread.start_new_thread(self.__continuousReadout, (delay, ))
        return thread.get_ident()
