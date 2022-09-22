from utilities import *
from main import *
from guihelpers import *

import itertools

logfilename = ""

scurvevals, thresholdvals, noisevals, trimvals, countvals = [], [], [], [], []

counter = 0

ispoweredon = False
isinitialized = False
workdirectory = os.getcwd()+"/"
print(workdirectory)

# This works for creating new plots, so we should be safe
def testshowplot():
    a = b = np.arange(0, 20, .02)
    c = 1e6*(np.exp(-0.75*a-1.75*np.sqrt(a)+0.01*a*a))
    fig = plt.figure()
    #fig = Figure.Figure(figsize=(6, 4))
    fig, ax = plt.subplots()
    #ax = fig.add_subplot(111)
    ax.plot(a, c, 'k', label='Background')
    #ax.plot(a, c, 'k', label='Background')
    ax.axvline(x=14, ymin=0.02, ymax = 1e6, linewidth=2, color='Red')
    ax.set_yscale('log')
    fig.show()

def ispoweredandinitialized(showdisplay=True):
    global ispoweredon
    global isinitialized
    if not (ispoweredon and isinitialized) and showdisplay:
        print("You need to power and initialize MPA chip.")
    return (ispoweredon and isinitialized)

def confirmMapSAID():
    if PassMaPSAID():
        log_filename()
        print("Created logfile"+logfilename+".")
        return True
    print("Couldn't create a logfile.")
    return False

def loadFirmware(showdisplay=True):
    #if logfilename == "":
    #    log_filename()
    os.system('source '+workdirectory+'loadfirmware.sh')
    if showdisplay:
        print("You opted to load the firmware.")
    logfile.write("You opted to load the firmware.")

def writeCSVfile_processedresults(thelist,typename):
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    mydate = datestring()
    filename = basedir+"ResultLists_"+TestMaPSAID()+".csv"
    with open(filename, "a") as f:
        writer = csv.writer(f,delimiter=',')
        newlist = thelist
        newlist.insert(0,datestring())
        newlist.insert(0,typename)
        writer.writerow(newlist)

def loadResultFromCSV(csvfilename,whattoload="",when=-1):
    #writeCSVfile_processedresults(prl,"poweronreadout")
    #writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveTHR")
    #writeCSVfile_processedresults(noisevals,"NoiseSCurveTHR")
    #writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveCAL")
    #writeCSVfile_processedresults(noisevals,"NoiseSCurveCAL")
    #writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveTrim")
    #writeCSVfile_processedresults(noisevals,"NoiseSCurveTrim")
    #writeCSVfile_processedresults(trimvals,"TrimDACSCurveTrim")
    #writeCSVfile_processedresults(countvals,"CountSCurveTrim")
    #writeCSVfile_processedresults(biasdata,"BiasData")
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    output = []
    latestresult = 20000101010101 #date way in the past
    with open(basedir+csvfilename, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            mylist = list(map(int, row))
            typename = mylist[0]
            timestamp = mylist[1]
            mylist.pop(0)
            mylist.pop(0)
            if typename != whattoload:
                continue
            if when<0 and (timestamp > latestresult): #to be tested
                latestresult = timpstamp
                output = mylist
            elif when>=0 and (abs(latestresult-when) > abs(timestamp-when)):
                latestresult = timestamp
                output = mylist
    return output

def loadResultCSV(whattoload="",when=-1):
    filename = "ResultLists_"+TestMaPSAID()+".csv"
    return loadResultFromCSV(filename,whattoload,when)

def loadSCurveFromCSV_dict(csvfilename):
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    #print(csvfilename)
    dictionaryofvalues = dict()
    with open(basedir+csvfilename, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if row[0] == '' or row[0]=='0':
                continue
            mylist = list(map(int, row))
            pixelid = mylist[0] #(r-1)*120+p = pixelid
            #mycolumn = (pixelid)%120
            #myrow    = (pixelid-mycolumn)/120 + 1
            #pixeltuple = (myrow,mycolumn)
            mylist.pop(0)
            dictionaryofvalues[pixeltuple] = mylist
            #print(pixelid,pixeltuple)
    return dictionaryofvalues

def createnewfile(showdisplay = True):
    global logfilename
    mydate, mytime = datestring(), thetime()
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    logfilename = "Log_"+TestMaPSAID()+"_"+mydate+".txt"
    logfilename = "Log_"+TestMaPSAID()+".txt"
    #logfilename = "Log"+TestMaPSAID()+"_"+mydate+".txt"
    #logfilename = "Log"+TestMaPSAID()+".txt"
    if os.path.isfile(logfilename):
        copyfilename = "SafetyCopy_" + mydate+"__Log_"+TestMaPSAID()+".txt"
        os.rename(basedir+logfilename, basedir+copyfilename)
    with open(basedir+logfilename,"a+") as logfile:
        logfile.write("Start log for "+TestMaPSAID()+" at " + mytime+" in file "+basedir+logfilename+"\n")

def append_filename(showdisplay = True):
    global logfilename
    mydate, mytime = datestring(), thetime()
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    logfilename = "Log_"+TestMaPSAID()+"_"+mydate+".txt"
    logfilename = "Log_"+TestMaPSAID()+".txt"
    #logfilename = "Log"+TestMaPSAID()+"_"+mydate+".txt"
    #logfilename = "Log"+TestMaPSAID()+".txt"
    with open(basedir+logfilename,"a+") as logfile:
        logfile.write("Start log for "+TestMaPSAID()+" at " + mytime+" in file "+basedir+logfilename+"\n")

def log_filename(createnew=True, showdisplay = True):
    if createnew:
        createnewfile(showdisplay)
    else:
        append_filename(showdisplay)

def writelog(message, twoline = False, showdisplay = True):
    global logfilename
    basedir = workdirectory + "../Logs/MPA_Results/TestResults/"
    if logfilename == "":
        if showdisplay:
            print("Log file was not created yet.")
        return
    if twoline:
        with open(basedir+logfilename,"a+") as logfile:
            logfile.write(thetime()+":\n" + message+"\n")
    else:
        with open(basedir+logfilename,"a+") as logfile:
            logfile.write(thetime()+": " + message+"\n")    

def thetime():
    try:
        return datetime.datetime.now().strftime("%Y/%m/%d  %H:%M")
    except AttributeError:
        return datetime.now().strftime("%Y/%m/%d  %H:%M")

def datestring():
    try:
        currentDT = datetime.datetime.now()
        return str('%04d' % currentDT.year)+str('%02d' % currentDT.month)+str('%02d' % currentDT.day)+str('%02d' % currentDT.hour)+str('%02d' % currentDT.minute)+str('%02d' % currentDT.second)
    except AttributeError:
        currentDT = datetime.now()
        return str('%04d' % currentDT.year)+str('%02d' % currentDT.month)+str('%02d' % currentDT.day)+str('%02d' % currentDT.hour)+str('%02d' % currentDT.minute)+str('%02d' % currentDT.second)

color_iteration = itertools.cycle(('blue', 'magenta'))
def Color_flip(canvas):
  def count():
    global counter
    counter += 1
    canvas.create_circle(10, 10, 10, fill=next(color_iteration), outline="#DDD", width=0)
    #countlabel.config(text=str(counter))
    canvas.after(1000, count)
  count()

def plot_2D_map_list(data, data_type,nfig=random.randint(5,9999999), row = range(1,17),column=range(2,120)):
    identifier = TestMaPSAID()
    average = np.mean(data)
    spread  = np.std(data)
    hmin = average - 3.0 * spread
    hmax = average + 3.0 * spread
    y = np.array([])
    x = np.array([])
    w = np.array([])
    for c in column:
        for r in row:
            y = np.append(y,c)
            x = np.append(x,r)
            w = np.append(w,data[(r-1)*120+c])
            #y = np.append(y,np.arange(0, 17,1))
            #x = np.append(x,np.repeat(c,17))
    #print y
    #print x
    #print w
    fig = plt.figure(nfig)
    plt.hist2d(x,y,weights=w,bins=(row[-1],column[-1]),cmin=hmin,cmax=hmax,range=[[row[0], row[-1]+1],[column[0], column[-1]+1]])
    cbar = plt.colorbar()
    cbar.set_label(data_type)
    yl = plt.ylabel('pixel in row')
    xl = plt.xlabel('row')
    plt.text(row[0],column[-1]+3,identifier)
    plt.text(int((row[0]+row[-1])/2+1),column[-1]+3,"Average %.2f +/- %.2f" % (average, spread))
    plt.grid()
    plt.show()
    return True

def TestMaPSAID():
    MaPSAidentifier = MaPSAID.get()
    MPAidentifier = MPAID.get()
    MPAintID = -1
    if MPAidentifier.isdigit():
        MPAintID = int(MPAidentifier)
    if MPAintID == -1:
        return ""
    if MaPSAidentifier == '':
        return ""
    return "MaPSA_"+MaPSAidentifier+"_"+MPAidentifier

def PassMaPSAID(showdisplay=True):
    if TestMaPSAID()=="":
        if showdisplay:
            print("You need to give a MaPSA and MPA identifiers first.")
        return False
    #if logfilename == "":
    #    log_filename()
    return True

def PassIDandPower(showdisplay=True):
    test_mapsa_id = PassMaPSAID(showdisplay)
    test_power_init = ispoweredandinitialized(showdisplay)
    return (test_mapsa_id and test_power_init)

def executecommand(event):
    #c.configure(text = str(CommandLine.get()))
    #print(1,CommandLine)
    #print(1,CommandLine.get())
    exec(str(myCommandLine.get()))

def dosomething():
    print("Hello. You're testing program is active for "+str(counter)+" seconds.")

def testinitialize(display=True):
    global isinitialized
    if not PassMaPSAID(True):
        return
    initializeMPA()
    testshift = shift()
    if not testshift:
        if display:
            print("Failed shift test during initialization")
        labelIsInitialized.config(text="Chip is Not Initialized.")
        isinitialized = False
    else:
        if display:
            print("Shift test during initialization Succesful.")
        labelIsInitialized.config(text="Chip is Initialized.")
        writelog("Chip is Initialized.")
        isinitialized = True
        #log_filename()
    return testshift

def testpoweron(showdisplay = True):
    global isinitialized
    global ispoweredon
    if not PassMaPSAID(True):
        return
    prl = poweron()
    if (prl[0]+prl[1]+prl[2])<75.:
        poweroff()
        ispoweredon = False
        isinitialized = False
        if showdisplay:
            print("Too low power - turned off power to the chip")
        return
    testshift = testinitialize(display = False)
    if not testshift:
        poweroff()
        ispoweredon = False
        isinitialized = False
        if showdisplay:
            print("Failed shift test during initialization - turned off power to the chip")
        return
    else:
        if showdisplay:
            print("Successful power-on and initialization of the chip.")
        writelog("Successful power-on and initialization of the chip.")
        ispoweredon = True
        isinitialized = True
        writeCSVfile_processedresults(prl,"poweronreadout")
        #log_filename()


def poweron(showdisplay = True):
    global ispoweredon
    if not PassMaPSAID(True):
        return
    reset()
    sleep(0.5)
    utils.activate_I2C_chip()
    sleep(0.5)
    mpa.pwr.set_supply(mode='on',display=showdisplay)
    prl = mpa.pwr.get_power(display=showdisplay,return_all=True) #[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip]
    #Pd,Pa,Pp = random.uniform(0.,100.),random.uniform(0.,100.),random.uniform(0.,100.)
    #prl = [Pd,Pa,Pp,1.0,1.2,1.2,Pd,Pa/1.2,Pp/1.2]
    labeldigpow.config(text='%7.3f mW' % prl[0])
    labeldigvol.config(text='%7.3f V'  % prl[3])
    labeldigcur.config(text='%7.3f mA' % prl[6])
    labelanapow.config(text='%7.3f mW' % prl[1])
    labelanavol.config(text='%7.3f V'  % prl[4])
    labelanacur.config(text='%7.3f mA' % prl[7])
    labelpadpow.config(text='%7.3f mW' % prl[2])
    labelpadvol.config(text='%7.3f V'  % prl[5])
    labelpadcur.config(text='%7.3f mA' % prl[8])
    labeltotpow.config(text='%7.3f mW' % (prl[0]+prl[1]+prl[2]))
    labeltotcur.config(text='%7.3f mA' % (prl[6]+prl[7]+prl[8]))
    labelIsPowered.config(text='Power is On.')
    writelog("Powered ON:\n"+ \
    "P_dig: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[0], prl[3], prl[6]) + "\n"+ \
    "P_ana: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[1], prl[4], prl[7]) + "\n"+ \
    "P_pad: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[2], prl[5], prl[8]) + "\n"+ \
    "P_tot: %7.3fmW  [I=%7.3fmA]" % (prl[0]+prl[1]+prl[2], prl[6]+prl[7]+prl[8]),True)
    #writelog("Powered on:")
    #writelog("P_dig: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[0], prl[3], prl[6]))
    #writelog("P_ana: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[1], prl[4], prl[7]))
    #writelog("P_pad: %7.3fmW  [V=%7.3fV - I=%7.3fmA]" % (prl[2], prl[5], prl[8]))
    #writelog("P_tot: %7.3fmW  [I=%7.3fmA]" % (prl[0]+prl[1]+prl[2], prl[6]+prl[7]+prl[8]))
    ispoweredon = True
    return prl

def poweroff(showdisplay = True):
    global ispoweredon
    global isinitialized
    utils.activate_I2C_chip()
    sleep(0.05)
    mpa.pwr.set_supply(mode='off',display=showdisplay)
    prl = mpa.pwr.get_power(display=showdisplay,return_all=True) #[Pd, Pa, Pp, Vd, Va, Vp, Id, Ia, Ip]
    #Pd,Pa,Pp = random.uniform(0.,0.1),random.uniform(0.,0.1),random.uniform(0.,0.1)
    #prl = [Pd,Pa,Pp,1.0,1.2,1.2,Pd,Pa/1.2,Pp/1.2]
    labeldigpow.config(text='%7.3f mW' % prl[0])
    labeldigvol.config(text='%7.3f V'  % prl[3])
    labeldigcur.config(text='%7.3f mA' % prl[6])
    labelanapow.config(text='%7.3f mW' % prl[1])
    labelanavol.config(text='%7.3f V'  % prl[4])
    labelanacur.config(text='%7.3f mA' % prl[7])
    labelpadpow.config(text='%7.3f mW' % prl[2])
    labelpadvol.config(text='%7.3f V'  % prl[5])
    labelpadcur.config(text='%7.3f mA' % prl[8])
    labeltotpow.config(text='%7.3f mW' % (prl[0]+prl[1]+prl[2]))
    labeltotcur.config(text='%7.3f mW' % (prl[6]+prl[7]+prl[8]))
    labelIsPowered.config(text='Power is Off.')
    writelog("Powered OFF:\n"+ \
    "P_dig: %7.3fmW  [V=%7.3fV - I= %7.3fmA]" % (prl[0], prl[3], prl[6]) + "\n"+ \
    "P_ana: %7.3fmW  [V=%7.3fV - I= %7.3fmA]" % (prl[1], prl[4], prl[7]) + "\n"+ \
    "P_pad: %7.3fmW  [V=%7.3fV - I= %7.3fmA]" % (prl[2], prl[5], prl[8]) + "\n"+ \
    "P_tot: %7.3fmW  [I= %7.3fmA]" % (prl[0]+prl[1]+prl[2], prl[6]+prl[7]+prl[8]),True)
    ispoweredon = False
    isinitialized = False

def shift():
    if not PassMaPSAID(True):
        return
    sleep(0.1)
    return test.shift()
    #return bool(random.getrandbits(1))

def initializeMPA():
    if not PassMaPSAID(True):
        return
    sleep(0.1)
    mpa.init()
    return

def measureground():
    if not PassIDandPower(True):
        return
    groundmeasure = bias.measure_ground()
    #groundmeasure = random.uniform(0.,0.1)
    labelmeasuregnd.config(text='%7.3f V' % groundmeasure)
    writelog("Ground measurement - V=%7.3fV" % groundmeasure,True)

def doSCurve(stype="THR"):
    global scurvevals
    global thresholdvals
    global noisevals
    if not PassIDandPower(True):
        return
    reference_value = entryrefval.get()
    if not reference_value.isdigit():
        print ("Reference value must be an integer.")
        return
    extract_value = entryextrval.get()
    if not extract_value.isdigit():
        print ("Extract value must be an integer.")
        return
    scurvevals, thresholdvals, noisevals = cal.s_curve(s_type = stype,ref_val = int(reference_value), extract_val = int(extract_value), filename = "../Logs/MPA_Results/TestResults/SCurve_"+TestMaPSAID()+"_"+datestring()+"_", extract = True, print_file = True)
    return scurvevals, thresholdvals, noisevals
    

def doSCurveTHR():
    global scurvevals
    global thresholdvals
    global noisevals
    if not PassIDandPower(True):
        return
    scurvevals, thresholdvals, noisevals = doSCurve("THR")
    writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveTHR")
    writeCSVfile_processedresults(noisevals,"NoiseSCurveTHR")
    plot_2D_map_list(thresholdvals, "Threshold THR")
    plot_2D_map_list(noisevals, "Noise THR")
    writelog("Performed THR s-curve.")

def doSCurveCAL():
    global scurvevals
    global thresholdvals
    global noisevals
    if not PassIDandPower(True):
        return
    scurvevals, thresholdvals, noisevals = doSCurve("CAL")
    writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveCAL")
    writeCSVfile_processedresults(noisevals,"NoiseSCurveCAL")
    plot_2D_map_list(thresholdvals, "Threshold CAL")
    plot_2D_map_list(noisevals, "Noise CAL")
    writelog("Performed CAL s-curve.")

def doTrimming():
    global scurvevals
    global thresholdvals
    global noisevals
    global trimvals
    global countvals
    if not PassIDandPower(True):
        return

    scurvevals, thresholdvals, noisevals, trimvals, countvals = cal.trimming_new()
    writeCSVfile_processedresults(thresholdvals,"ThresholdSCurveTrim")
    writeCSVfile_processedresults(noisevals,"NoiseSCurveTrim")
    writeCSVfile_processedresults(trimvals,"TrimDACSCurveTrim")
    writeCSVfile_processedresults(countvals,"CountSCurveTrim")
    plot_2D_map_list(thresholdvals, "Threshold THR post trim")
    plot_2D_map_list(noisevals, "Noise THR post trim")
    plot_2D_map_list(countvals, "Noise THR post trim")
    plot_2D_map_list(trimvals, "Extracted trim values")
    writelog("Performed Trimming.")

def doCalibBias():
    global biasdata
    if not PassIDandPower(True):
        return
    biasdata = bias.calibrate_chip2(filename = "../Logs/MPA_Results/TestResults/BiasCalib_"+TestMaPSAID()+"_"+datestring()+"_", print_file = True)
    #writeCSVfile_processedresults(biasdata,"BiasData")
    #plot_2D_map_list(biasdata, "Extracted bias settings")
    writelog("Performed Bias Calibration.")

def doRegisterTest():
    errorcount = mpa.i2c.test_chip()
    if errorcount == 0:
        writelog("Performed successfully read/write register test.")
        print("Performed successfully read/write register test.")
    else:
        writelog("The read/write register test was not fully succesful. Found"+str(errorcount)+" errors.")
        print("The read/write register test was not fully succesful. Found"+str(errorcount)+" errors.")

