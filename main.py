from utilities.configure_communication import *
from utilities.fc7_com import *
ipaddr, fc7_if, fc7AddrTable = configure_communication()
FC7 = fc7_com(fc7_if, fc7AddrTable)

from utilities.tbsettings import *
from utilities.i2c_conf import *
from utilities.power_utility import *

from myScripts.BasicADC import *
from myScripts.BasicMultimeter import *
from myScripts.keithley2410 import *

# MPA Utilities
from mpa_methods.mpa import *
from mpa_methods.mpa_cal_utility import *
from mpa_methods.mpa_test_utility import *

from mpa_methods.mpa_data_chain import *
from mpa_methods.mpa_bias_utility import *
from mpa_methods.mpa_scanchain_test import *
from mpa_methods.mpa_measurements import MPAMeasurements
#from mpa_methods.mpa_fast_injection_test import MPAFastInjectionMeasurement

from stepping import *

# MPA2 Test procedures
from mpa_methods.mpa_testing_routine import *

class MPAwp:
    def __init__(self, index = "MPA", address = 0):
        ##FC7.set_chip_id(index, address)
        self.index         = index
        self.i2c           = I2CConf(FC7, fc7AddrTable, index=index, address=address)

        self.peri_reg_map  = self.i2c.get_peri_reg_map()
        self.row_reg_map   = self.i2c.get_row_reg_map()
        self.pixel_reg_map = self.i2c.get_pixel_reg_map()

        self.pwr           = PowerUtility(self.i2c, FC7, index)
        self.chip          = MPA_ASIC(self.i2c, FC7, self.pwr, self.peri_reg_map, self.row_reg_map, self.pixel_reg_map)
        self.cal           = mpa_cal_utility(self.chip, self.i2c, FC7)

        # base functionality tests
        self.test          = mpa_test_utility(self.chip, self.i2c, FC7)

        self.init          = self.chip.init
        self.inject        = self.chip.inject

        # faster access to readout methods
        self.read_regs     = self.chip.rdo.read_regs
        self.read_L1       = self.chip.rdo.read_L1
        self.read_Stubs    = self.chip.rdo.read_stubs
#        self.data_dir = "../cernbox_anvesh/MPA_test_data/"
#        self.scanchain = MPA_scanchain_test(self.chip, self.i2c, FC7, self.pwr)

# FNAL doesn't have this set up
#        try:
#            multimeter = keithley_multimeter()
#            self.bias = mpa_bias_utility(self.chip, self.i2c, FC7, multimeter, self.peri_reg_map, self.row_reg_map, self.pixel_reg_map)
#        except ImportError:
#            self.bias = False
#            print("- Impossible to access GPIB instruments")

        self.bias = False                                                                                                            
        #print("- Impossible to access GPIB instruments")  

        # additional characterizations
        self.dc            = MPATestDataChain(self.chip, self.i2c, FC7)
        self.measure       = MPAMeasurements(self.chip, self.bias)

        # radiation testing
        #self.fastinj       = MPAFastInjectionMeasurement(self.chip, self.bias, self.test, "../MPA2_RadiationResults/.")

    def on(self):
        utils.activate_I2C_chip(FC7)
        time.sleep(0.1);  self.pwr.set_supply('on', display=False)
        time.sleep(0.1);  self.pwr.set_clock_source('internal')
        time.sleep(0.1);  self.chip.init(reset_board = True, reset_chip = True, display = True)

    def off(self):
        utils.activate_I2C_chip(FC7)
        self.pwr.set_supply('off')

    def init(self):
        return self.chip.init(reset_board = True, reset_chip = False, display = True)

    def reset_fc7(self):
        FC7.write("fc7_daq_ctrl.command_processor_block.global.reset", 1);

    def reset_mpa(self):
        self.chip.reset()

    def set_clock(self,val = 'internal'):
        self.pwr.set_clock_source(val)
        time.sleep(0.1);  self.chip.init(reset_board = False, reset_chip = False, display = True)

# global
mpa  = MPAwp(address = 0b000)

# FNAL code for testing MaPSA
def pon():
    mpa.reset_mpa()
    sleep(0.1)
    utils.activate_I2C_chip(FC7)
    sleep(0.1)
    mpa.pwr.mainpoweron()
    sleep(0.1)
    mpa.pwr.on()
    sleep(0.1)
    mpa.init()
    sleep(0.1)
    return mpa.test.shift()

def poff():
    utils.activate_I2C_chip(FC7)
    sleep(0.1)
    mpa.pwr.off()
    sleep(0.1)
    mpa.pwr.mainpoweroff()

def mpa_test(basepath="../Results_MPATesting/",
             mapsaid="AssemblyX",
             chipid="ChipY",
             timestamp=True,
             testregister=True,
             testwaferroutine=True, 
             testmaskpalive=True,
             testpretrim=False, 
             testtrim=100, 
             testposttrim=True, 
             testbb=True, 
             vbias=-300, 
             bbvbias=-2,
             doIVscan=False):

    print("Start testing.")
    print("At the end of the test, a summary is printed out.")

    if len(mapsaid) < 1:
        print("MaPSA ID " + mapsaid + " is too short.")
        return

    if len(chipid) < 1:
        print("MPA ID " + chipid + " is too short.")
        return

    mapsabaseid = mapsaid
    t0 = time.time()

    print("Reading EFuse")
    efuse = mpa.chip.ctrl_base.read_fuses(verbose=1)
    print(efuse)

    outputdir = basepath[:basepath.rfind("/")]+"/"+mapsaid
    path = outputdir + "/"
    if not os.path.isdir(outputdir): os.makedirs(outputdir)
    mapsaid = "mpa_test_"+mapsaid+"_"+chipid
    if timestamp: 
        mapsaid += "_" + time.strftime("%Y_%m_%d_%H_%M_%S")
    logfilename = utils.create_logfile(path,mapsaid)
    print(logfilename)

    powerresults = mpa.pwr.get_power(False,True)
    utils.write_to_logfile("Power reading:", logfilename, True)
    utils.write_to_logfile('P_dig: %7.3f mW  [V= %7.3f V - I= %7.3f mA]' % (powerresults[0], powerresults[3], powerresults[6]), logfilename, True)
    utils.write_to_logfile('P_ana: %7.3f mW  [V= %7.3f V - I= %7.3f mA]' % (powerresults[1], powerresults[4], powerresults[7]), logfilename, True)
    utils.write_to_logfile('P_pad: %7.3f mW  [V= %7.3f V - I= %7.3f mA]' % (powerresults[2], powerresults[5], powerresults[8]), logfilename, True)
    utils.write_to_logfile('Total: %7.3f mW  [I= %7.3f mA]' % (powerresults[0]+powerresults[1]+powerresults[2], powerresults[6]+powerresults[7]+powerresults[8] ), logfilename, True)

    hvsupply = keithley2410()
    status = hvsupply.enableOutput()
    
    status = hvsupply.setVoltageSlow(vbias,-10,0.25)
    utils.write_to_logfile("Bias voltage set to BV="+str(int(hvsupply.getData()[0]))+"V, I = "+str(hvsupply.getData()[1]*1000000)+" muA", logfilename, True)
    # status = hvsupply.startReadout()

    if testwaferroutine:    
        # Anvesh
        probe = MainTestsMPA(tag = mapsaid, chip = mpa, directory=outputdir)
        probe.RUN()

    # Register test ##################################
    chip_errors  = -1
    row_errors   = -1
    pixel_errors = -1
    total_errors = -1
    
    if testregister: 
        utils.write_to_logfile("Test I2C communication (write/read registers):", logfilename, True)
        chip_errors  = mpa.test.writeread_allregs_peri()
        row_errors   = mpa.test.writeread_allregs_row()
        pixel_errors = mpa.test.writeread_allregs_pixel()
        total_errors = chip_errors + row_errors + pixel_errors
        
        utils.write_to_logfile("Total MPA errors:   "+str(chip_errors)  , logfilename, True)
        utils.write_to_logfile("Total row errors:   "+str(row_errors)   , logfilename, True)
        utils.write_to_logfile("Total pixel errors: "+str(pixel_errors) , logfilename, True)
        utils.write_to_logfile("Total errors:       "+str(total_errors) , logfilename, True)
    
    else:
        utils.write_to_logfile("Skipped test of I2C communication (registers)", logfilename, True)
    
    # Test masking and pixel alive ##################################

    pixel_mask, unmaskablepixels = [],[]
    pixel_alive, deadpixels, ineffpixels, noisypixels = [], [], [], []
    if testmaskpalive:
        utils.write_to_logfile("Test pixel masking:", logfilename, True)
        pixel_mask, unmaskablepixels = mpa.cal.mask_test(ref_val=250, filename=path+mapsaid+"_mask_test")
        utils.write_to_logfile( "Unmaskable Pixels:  "+str(len(unmaskablepixels))+" ("+conf.getPercentage(unmaskablepixels)+")", logfilename, True)
        utils.write_to_logfile("Test pixel alive:", logfilename, True)

        pixel_alive, deadpixels, ineffpixels, noisypixels = mpa.cal.pixel_alive(ref_cal=250, ref_thr=250, filename=path+mapsaid+"_pixelalive")
        utils.write_to_logfile( "Dead Pixels:        "+str(len(deadpixels ))+" ("+conf.getPercentage(deadpixels )+")", logfilename, True)
        utils.write_to_logfile( "Inefficient Pixels: "+str(len(ineffpixels))+" ("+conf.getPercentage(ineffpixels)+")", logfilename, True)
        utils.write_to_logfile( "Noisy Pixels:       "+str(len(noisypixels))+" ("+conf.getPercentage(noisypixels)+")", logfilename, True)
    else:
        utils.write_to_logfile("Skipped pixelalive", logfilename, True)
        utils.write_to_logfile("Skipped masking", logfilename, True)

    # Pre-trim S-curves ################################## 
    if testpretrim:
        THR_pre = mpa.cal.s_curve(s_type="THR", ref_val = 15, filename=path+mapsaid+"_PreTrim_THR",extract=1)
        utils.write_to_logfile('Pre- Trim THR Mean:  %7.2f +/- %7.2f' % (np.mean(THR_pre [1]), np.std(THR_pre [1])), logfilename, True)
        utils.write_to_logfile('Pre- Trim THR Noise: %7.2f +/- %7.2f' % (np.mean(THR_pre [2]), np.std(THR_pre [2])), logfilename, True)
        
        CAL_pre = mpa.cal.s_curve(s_type="CAL", ref_val = 100, filename=path+mapsaid+"_PreTrim_CAL",extract=1)
        utils.write_to_logfile('Pre- Trim CAL Mean:  %7.2f +/- %7.2f' % (np.mean(CAL_pre [1]), np.std(CAL_pre [1])), logfilename, True)
        utils.write_to_logfile('Pre- Trim CAL Noise: %7.2f +/- %7.2f' % (np.mean(CAL_pre [2]), np.std(CAL_pre [2])), logfilename, True)

    else:
        utils.write_to_logfile("Skipped scurves pre trimming", logfilename, True)

    # Perform trimming ################################## 
    if testtrim > 0:
        trim_bits = mpa.cal.trimming_desy(nominal_req=testtrim)
    else:
        utils.write_to_logfile("Skipped trimming", logfilename, True)
        
    # Post-trim S-curves ################################## 
    if testtrim > 0 and testposttrim:
        THR_post = mpa.cal.s_curve(s_type="THR", ref_val = 15, filename=path+mapsaid+"_PostTrim_THR",extract=1)
        utils.write_to_logfile('Post-Trim THR Mean:  %7.2f +/- %7.2f' % (np.mean(THR_post[1]), np.std(THR_post[1])), logfilename, True)
        utils.write_to_logfile('Post-Trim THR Noise: %7.2f +/- %7.2f' % (np.mean(THR_post[2]), np.std(THR_post[2])), logfilename, True)

        CAL_post = mpa.cal.s_curve(s_type="CAL", ref_val = 100, filename=path+mapsaid+"_PostTrim_CAL",extract=1)
        utils.write_to_logfile('Post-Trim CAL Mean:  %7.2f +/- %7.2f' % (np.mean(CAL_post[1]), np.std(CAL_post[1])), logfilename, True)
        utils.write_to_logfile('Post-Trim CAL Noise: %7.2f +/- %7.2f' % (np.mean(CAL_post[2]), np.std(CAL_post[2])), logfilename, True)

    else:
        utils.write_to_logfile("Skipped scurves post trimming", logfilename, True)

    # Bad bump test ################################## 
    badbumps, badbumpsNonEdge = [], []

    status = hvsupply.disableReadout()
    hvdata = hvsupply.getReadoutData()
    CSV.ArrayToCSV(hvdata, logfilename.replace(".log","_HV.csv"))

    if testbb:
        status = hvsupply.setVoltageSlow(bbvbias,10,0.25)
        utils.write_to_logfile("Bias voltage set to BV="+str(int(hvsupply.getData()[0]))+"V, I = "+str(hvsupply.getData()[1]*1000000)+" muA", logfilename, True)
        utils.write_to_logfile("Bad bump test at V = "+str(int(bbvbias))+"V:", logfilename, True)
        badbumps, badbumpsNonEdge = mpa.cal.BumpBonding(filename=path+mapsaid+"_BumpBonding", print_out=False, returnAll = True)
        utils.write_to_logfile("Total BadBumps (org) fit:          " + str(len(badbumps       ))+" ("+conf.getPercentage(badbumps       )+")", logfilename, True)
        utils.write_to_logfile("Total BadBumps fit (org) non-edge: " + str(len(badbumpsNonEdge))+" ("+conf.getPercentage(badbumpsNonEdge)+")", logfilename, True)
    else:
        utils.write_to_logfile("Skipped bump bonding", logfilename, True)

    status = hvsupply.setVoltageSlow(0,10,0.25)
    utils.write_to_logfile("Bias voltage set to BV="+str(int(hvsupply.getData()[0]))+"V, I = "+str(hvsupply.getData()[1]*1000000)+" muA", logfilename, True)
    status = hvsupply.disableOutput()
    if not doIVscan:
        poff()
        
    os.system("chown -R fnaltest "+ path)
    t1 = time.time()
    print("Elapsed Time: " + str(t1 - t0))

    print("Write out results for copy and pasting (this is for "+chipid+"):")
    print('%7.3f \t%7.3f' % (powerresults[0],powerresults[6]))
    print('%7.3f \t%7.3f' % (powerresults[1],powerresults[7]))
    print('%7.3f \t%7.3f' % (powerresults[2],powerresults[8]))
    print('%7.3f \t%7.3f' % (powerresults[0]+powerresults[1]+powerresults[2],powerresults[6]+powerresults[7]+powerresults[8]))

    if testregister:
        print(chip_errors)
        print(row_errors)
        print(pixel_errors)
        print(total_errors)

    if testmaskpalive:
        print(str(len(unmaskablepixels))+" \t"+conf.getPercentage(unmaskablepixels))
        print(str(len(deadpixels ))+" \t"+conf.getPercentage(deadpixels ))
        print(str(len(ineffpixels))+" \t"+conf.getPercentage(ineffpixels))
        print(str(len(noisypixels))+" \t"+conf.getPercentage(noisypixels))

    if testpretrim:
        print('%7.2f \t%7.2f' % (np.mean(THR_pre [1]), np.std(THR_pre [1])))
        print('%7.2f \t%7.2f' % (np.mean(THR_pre [2]), np.std(THR_pre [2])))
        print('%7.2f \t%7.2f' % (np.mean(CAL_pre [1]), np.std(CAL_pre [1])))
        print('%7.2f \t%7.2f' % (np.mean(CAL_pre [2]), np.std(CAL_pre [2])))

    if testtrim > 0 and testposttrim:
        print('%7.2f \t%7.2f' % (np.mean(THR_post[1]), np.std(THR_post[1])))
        print('%7.2f \t%7.2f' % (np.mean(THR_post[2]), np.std(THR_post[2])))
        print('%7.2f \t%7.2f' % (np.mean(CAL_post[1]), np.std(CAL_post[1])))
        print('%7.2f \t%7.2f' % (np.mean(CAL_post[2]), np.std(CAL_post[2])))

    if testbb:
        print(str(len(badbumps     ))+" \t"+conf.getPercentage(badbumps     ))

    if doIVscan:
        print("You chose to do an IV scan - doing it now")
        IVScan(basepath=basepath,mapsaid=mapsabaseid,writecsv=True)
        poff()

    return True

def IVScan(basepath="../Results_MPATesting/",mapsaid="AssemblyX",writecsv=True,VStart=0,VStop=-801,VStep=-10,delay=0.5,currentlimit=.0005):

    if len(mapsaid) < 1:
        print("MaPSA ID is too short")
        return

    if mapsaid == "AssemblyX": 
        writecsv_ = False
        print("Not saving output: invalid MaPSA ID")

    csvfilename = basepath[:basepath.rfind("/")]+"/"+mapsaid + "/IVScan_"+mapsaid+".csv"
    hvsupply = keithley2410()
    status = hvsupply.enableOutput()
    status = hvsupply.setVoltageSlow(0)
    status = hvsupply.setCurrentProtection(currentlimit)
    results = hvsupply.IVScan(VStart=VStart,VStop=VStop,VStep=VStep,delay=delay)
    status = hvsupply.setVoltageSlow(0)
    status = hvsupply.disableOutput()

    print("IV Scan Results")

    for measurement in results:
        print('%7.2f \t%7.2f' % (measurement[0], measurement[1]))
        if writecsv:
            outputdir = basepath[:basepath.rfind("/")]+"/"+mapsaid
            path = outputdir + "/"
            if not os.path.isdir(outputdir): os.makedirs(outputdir)
            with open(csvfilename,mode="a+") as HVfile:
                HVwriter = csv.writer(HVfile)
                HVwriter.writerow([measurement[0], measurement[1]])
    return

#def IVoff():
#    IVScan(VStart=-150,VStop=0,VStep=15,delay=0.2)
#    return

#def IVpoff():
#    IVoff()
#    poff()
#    return

def pa(cal=250, thr=250, delay=200, hv=-10):

    hvsupply = keithley2410()
    status = hvsupply.enableOutput()
    status = hvsupply.setVoltageSlow(hv,-10,0.25)

    pixel_alive = mpa.cal.pixel_alive(ref_cal=cal, ref_thr=thr, pulse_delay=delay, plot=1)

    status = hvsupply.setVoltageSlow(0,10,0.25)
    status = hvsupply.disableOutput()

    return

def bare_mpa_test():

    mpa_test(basepath="../Results_MPATesting/",
             mapsaid="Single",
             chipid="Chip183",
             timestamp=True,
             testregister=True,
             testwaferroutine=True,
             testmaskpalive=True,
             testpretrim=True,
             testtrim=100,
             testposttrim=True,
             testbb=False,
             vbias=0,
             bbvbias=0,
             doIVscan=False)

    return


# Jennet's code for the automated stepping
# This part is specific to the probe station at SiDet
# You will need to make edits for another site

def do_IV():
    # send command to run iv
    # If IV is really awful, quit
    return True

def reset_contact():  
    good_contact = False
    tries = 0
    while not good_contact and tries < 3:
        good_contact = test_contact()
        tries += 1

    return good_contact

def test_contact():
    # send command to raise and lower
    # run pon and check output
    return pon()

def scan_side(basepath="../Results_MPATesting/",
             mapsaid="AssemblyX",
             chipid="ChipY",
             timestamp=True,
             testregister=True,
             testwaferroutine=True,
             testmaskpalive=True,
             testpretrim=False,
             testtrim=100,
             testposttrim=True,
             testbb=True):

    if len(mapsaid) < 1:
        print("MaPSA ID " + mapsaid + " is too short.")
        return

    if len(chipid) < 1:
        print("MPA ID " + chipid + " is too short.")
        return

    import beepy

    # mapsa name = input argument 
    mapsa_name = mapsaid
    print("Testing MaPSA " + mapsa_name)

    # which side = input argument
    start_MPA = int(chipid)

    # Open connection to message server

    nMPA = start_MPA
    test_tries = 0

    end_MPA = 8
    if start_MPA > 8:
        end_MPA = 16

    while nMPA <= end_MPA:
        print("Beginning test of MPA " + str(nMPA))

        lower_needles()
        good_contact = test_contact()
        
#        if not good_contact:
#            print(bcolors.FAIL + "Could not get good contact on MPA " + str(nMPA) + bcolors.RESET)
#            beepy.beep(1)
#            step(1)
#            nMPA += 1
#            continue
          
        successful_test = mpa_test(basepath=basepath,
                                   mapsaid=mapsaid,
                                   chipid=chipid,
                                   testregister=testregister,
                                   testwaferroutine=testwaferroutine,
                                   testmaskpalive=testmaskpalive,
                                   testpretrim=testpretrim,
                                   testtrim=testtrim,
                                   testposttrim=testposttrim,
                                   testbb=testbb)

        if successful_test:
            print("Test succeeded on MPA " + str(nMPA))
        else:
            print("Test failed on MPA " + str(nMPA))

#        if not successful_test and test_tries < 1:
#            print(bcolors.FAIL + "Test failed on MPA " + str(nMPA) + bcolors.RESET)
#            test_tries += 1
#            beepy.beep(1)
#            continue
#        elif not successful_test:
#            print(bcolors.FAIL + "Test failed again on MPA " + str(nMPA) + bcolors.RESET)
#            beepy.beep(1)
#            step(1)
#            nMPA += 1
#            test_tries = 0
#            continue

        if nMPA == 1:
            print("Here would do IV scan")
#            good_iv = do_IV()
#            if good_iv:
#                print(bcolors.OK + "IV Scan succeeded on MPA " + str(nMPA) + bcolors.RESET)
#            else:
#                print(bcolors.FAIL + "IV Scan failed on MPA " + str(nMPA) + bcolors.RESET)
#                beepy.beep(1)
#                break

        lift_needles()

        step_nMPA(nMPA,1)
        nMPA += 1
        test_tries = 0

    return

