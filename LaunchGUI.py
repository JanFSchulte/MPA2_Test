import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from guihelpers import *

logfilename = ""

scurvevals, thresholdvals, noisevals, trimvals, countvals = [], [], [], [], []

counter = 0

ispoweredon = False
isinitialized = False
workdirectory = os.getcwd()+"/"
print(workdirectory)

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.see("end")
        self.widget.configure(state="disabled")
#        self.add_timestamp()   

def quitanddestroy():
    gui.quit()
    gui.destroy()

def action_get_info_dialog():
	m_text = '\
************************\n\
Author:  Hannsjoerg Weber\n\
Inherited by: Jennet Dickinson\n\
Date:    2022/09/20\n\
Version: 1.0.0\n\
************************\n\
Rev: 1.0.0 - Jennet\'s first attempt for MPA2. \n\
Rev: 0.1.1 - working version with all tests but IV/bump bond.\n\
Rev: 0.0.1 - first attempt\n\
************************\n'
	messagebox.showinfo(message=m_text, title = "Infos")

def action_get_procedure_dialog():
	m_text = '\
The procedure for testing is:\n\
************************\n\
"Power on <-- Total ~ 200 +/- 40 mW\n\
Initialize <-- should give Chip is Initialized.\n\
(If these two steps [run also via Power On and (Test) Initialize] did not work well, you did not land well.)\n\
Measure ground <-- V_gnd = < 30 mV\n\
Run an SCurve THR.\n\
Run trimming.\n\
Run bump-bonding (not yet implemented).\n\
Run bias calibration (to be tested).\n\
Run pixel alive (to be implemented).\n\
Run register read/write test (to be tested).\n\
Run I-V curve (only once per chip, to be implemented).\n\
************************\n\
When finishing a test, power first OFF before moving to next chip.'
	messagebox.showinfo(message=m_text, title = "Procedure")

########################################################
##############  Here the gui is defined.  ##############
########################################################

gui = tk.Tk()
gui.geometry("950x450") #You want the size of the app to be 500x500
gui.resizable(0, 0) #Don't allow resizing in the x or y direction
#Open gui on front of all other windows
gui.lift()
gui.attributes('-topmost',True)
gui.after_idle(gui.attributes,'-topmost',False)

gui.title("MPA testing")

#canvas = tk.Canvas(gui, width=20, height=20, borderwidth=0, highlightthickness=0, bg="white")
#canvas.grid(row=0, column=0)
#def _create_circle(self, x, y, r, **kwargs):
#    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)
#tk.Canvas.create_circle = _create_circle
#canvas.create_circle(10, 10, 10, fill="blue", outline="#DDD", width=0)
#Color_flip(canvas)

# Horizontal menu bar at the top of GUI window
a_menu = tk.Menu(gui)

action_menu = tk.Menu(a_menu, tearoff=0)
action_menu.add_command(label="Runtime", command=dosomething)
#action_menu.add_separator() 
action_menu.add_command(label="Exit", command=quitanddestroy)

info_menu = tk.Menu(a_menu, tearoff=0)
info_menu.add_command(label="Program info", command=action_get_info_dialog)
info_menu.add_command(label="Instructions", command=action_get_procedure_dialog)

a_menu.add_cascade(label="Action", menu=action_menu)
a_menu.add_cascade(label="Help", menu=info_menu)
gui.config(menu=a_menu)

#left = tk.Frame(gui, borderwidth=2, relief="solid")
#left.grid(row=0, column=0, columnspan=7, rowspan=30)

myTerminal = tk.Text(gui, wrap="word")
#gui.text.pack(side="top", fill="both", expand=True)
myTerminal.grid(row=1, column=0, columnspan=7, rowspan=13)
#Terminal.grid(row=0, column=0)
myTerminal.tag_configure("stderr", foreground="#b22222")
vsb = tk.Scrollbar(orient="vertical", command=myTerminal.yview)
myTerminal.configure(yscrollcommand=vsb.set)
#gui.vsb.pack(side="right", fill="y")
sys.stdout = TextRedirector(myTerminal, "stdout")
sys.stderr = TextRedirector(myTerminal, "stderr")

#CommandLinel = tk.Label (gui,text="Commandline:", bg="white", fg="black")
#CommandLinel.grid(row=15, column=0, columnspan=2)

#myCommandLine = tk.Entry(gui)
#CommandLine.bind("<Key>", executecommand)
#myCommandLine.bind("<Return>", executecommand)
#myCommandLine.grid(row=15, column=1, columnspan=5)

# Place to write in MaPSA ID
MaPSAIDl = tk.Label (gui,text="MaPSA ID:", bg="white", fg="black")
MaPSAIDl.grid(row=0, column=0, columnspan=2)
MaPSAID = tk.Entry(gui)
MaPSAID.grid(row=0, column=2, columnspan=3)
MaPSAID.insert(0, '')

# Place to write in MPA ID
MPAIDl = tk.Label (gui,text="MPA:", bg="white", fg="black")
MPAIDl.grid(row=0, column=5)
MPAID = tk.Entry(gui)
MPAID.grid(row=0, column=6)
MPAID.insert(0, '')

#HelpPointer = tk.Label(gui, text = "For procedure see Help Menu.")
#HelpPointer.grid(row=0, column=1, columnspan=5)

# Functions that actuallly run tests
#labelButtons = tk.Label(gui,text="Functions")                                                                                                              
#labelButtons.grid(row=0, column=7, columnspan=2)    

# Load firmware
#buttonFirmware = tk.Button(gui,text='Load Firmware', command=loadFirmware)
#buttonFirmware.grid(row=1, column=7, columnspan=2)

buttonOn = tk.Button(gui,text='Power On', command=pon)
buttonOn.grid(row=1, column=7, columnspan=1)

buttonOff = tk.Button(gui,text='Power Off', command=poff)
buttonOff.grid(row=1, column=8, columnspan=1)

buttonPa = tk.Button(gui,text='Pixel Alive', command=pa)
buttonPa.grid(row=2, column=7, columnspan=1)

buttonIVScan = tk.Button(gui,text='IV Scan', command=lambda: IVScan(mapsaid=MaPSAID.get()))
buttonIVScan.grid(row=3, column=7, columnspan=1)

# Define checkboxes for MPA tests
labelTests = tk.Label(gui,text="Select MPA tests to run")
labelTests.grid(row=4, column=8, columnspan=2)

testRegister     = tk.IntVar()
testWaferRoutine = tk.IntVar()
testMaskPAlive   = tk.IntVar()
testPretrimS     = tk.IntVar()
testPosttrimS    = tk.IntVar()
testBB           = tk.IntVar()

testRegisterButton     = tk.Checkbutton(gui, text='Register Test', variable=testRegister,     onvalue=1, offvalue=0)
testWaferRoutineButton = tk.Checkbutton(gui, text='Wafer Test',    variable=testWaferRoutine, onvalue=1, offvalue=0)
testMaskPAliveButton   = tk.Checkbutton(gui, text='Mask/Alive',    variable=testMaskPAlive,   onvalue=1, offvalue=0)
testPretrimSButton     = tk.Checkbutton(gui, text='Pretrim S',     variable=testPretrimS,     onvalue=1, offvalue=0)
testPosttrimSButton    = tk.Checkbutton(gui, text='Posttrim S',    variable=testPosttrimS,    onvalue=1, offvalue=0)
testBBButton           = tk.Checkbutton(gui, text='Bad Bump',      variable=testBB      ,     onvalue=1, offvalue=0)

testRegisterButton.grid(row=5,column=7,columnspan=1)
testWaferRoutineButton.grid(row=5,column=8,columnspan=1)
testMaskPAliveButton.grid(row=5,column=9,columnspan=1)

testPretrimSButton.grid(row=6,column=7,columnspan=1)
testPosttrimSButton.grid(row=6,column=8,columnspan=1)
testBBButton.grid(row=6,column=9,columnspan=1)

# This button runs the MPA test according to chechboxes
buttonTestMPA = tk.Button(gui,text='Test 1 MPA', command=lambda: mpa_test(mapsaid=MaPSAID.get(),
                                                                       chipid=MPAID.get(),
                                                                       testregister=testRegister.get(),
                                                                       testwaferroutine=testWaferRoutine.get(),
                                                                       testmaskpalive=testMaskPAlive.get(),
                                                                       testpretrim=testPretrimS.get(),
                                                                       testtrim=testPosttrimS.get(),
                                                                       testposttrim=testPosttrimS.get(),
                                                                       testbb=testBB.get()))

buttonTestMPA.grid(row=4, column=7, columnspan=1)

#buttonAutomated = tk.Button(gui,text='Test 8 MPA', command=lambda: scan_side(mapsaid=MaPSAID.get()))                                                       
#buttonAutomated.grid(row=7, column=7, columnspan=1) 

#buttonStep = tk.Button(gui,text='Step 1 MPA', command=lambda: step(1))
#buttonStep.grid(row=9, column=7, columnspan=1)

#buttonAutomated = tk.Button(gui,text='Automated', command=lambda: IVScan(mapsaid=MaPSAID.get()))
#buttonAutomated.grid(row=7, column=8, columnspan=1)


# S curve functions for troubleshooting
#labelButtons = tk.Label(gui,text="S-curves only")
#labelButtons.grid(row=10, column=7, columnspan=2)

#buttonInit = tk.Button(gui,text='(Test) Initialize', command=testinitialize)
#buttonInit.grid(row=1, column=9, columnspan=2)

#labelIsPowered = tk.Label(gui,text="Power is Off.")
#labelIsPowered.grid(row=2, column=7, columnspan=3)
#labelIsInitialized = tk.Label(gui,text="Chip is Idle.")
#labelIsInitialized.grid(row=2, column=10, columnspan=3)
"""
labeldigpowl = tk.Label(gui,text="P_dig: ")
labeldigpowl.grid(row=3, column= 7, sticky=tk.E)
labeldigpow  = tk.Label(gui,text=" 0.000 mW")
labeldigpow .grid(row=3, column= 8, sticky=tk.E)
labeldigvoll = tk.Label(gui,text="V_dig: ")
labeldigvoll.grid(row=3, column= 9, sticky=tk.E)
labeldigvol  = tk.Label(gui,text="0.000 V")
labeldigvol .grid(row=3, column=10, sticky=tk.E)
labeldigcurl = tk.Label(gui,text="I_dig: ")
labeldigcurl.grid(row=3, column=11, sticky=tk.E)
labeldigcur  = tk.Label(gui,text=" 0.000 mA")
labeldigcur .grid(row=3, column=12, sticky=tk.E)
labelanapowl = tk.Label(gui,text="P_ana: ")
labelanapowl.grid(row=4, column= 7, sticky=tk.E)
labelanapow  = tk.Label(gui,text=" 0.000 mW")
labelanapow .grid(row=4, column= 8, sticky=tk.E)
labelanavoll = tk.Label(gui,text="V_ana: ")
labelanavoll.grid(row=4, column= 9, sticky=tk.E)
labelanavol  = tk.Label(gui,text="0.000 V")
labelanavol .grid(row=4, column=10, sticky=tk.E)
labelanacurl = tk.Label(gui,text="I_ana: ")
labelanacurl.grid(row=4, column=11, sticky=tk.E)
labelanacur  = tk.Label(gui,text=" 0.000 mA")
labelanacur .grid(row=4, column=12, sticky=tk.E)
labelpadpowl = tk.Label(gui,text="P_pad: ")
labelpadpowl.grid(row=5, column= 7, sticky=tk.E)
labelpadpow  = tk.Label(gui,text=" 0.000 mW")
labelpadpow .grid(row=5, column= 8, sticky=tk.E)
labelpadvoll = tk.Label(gui,text="V_pad: ")
labelpadvoll.grid(row=5, column= 9, sticky=tk.E)
labelpadvol  = tk.Label(gui,text="0.000 V")
labelpadvol .grid(row=5, column=10, sticky=tk.E)
labelpadcurl = tk.Label(gui,text="I_pad: ")
labelpadcurl.grid(row=5, column=11, sticky=tk.E)
labelpadcur  = tk.Label(gui,text=" 0.000 mA")
labelpadcur .grid(row=5, column=12, sticky=tk.E)
labeltotpowl = tk.Label(gui,text="P_tot: ")
labeltotpowl.grid(row=6, column= 7, sticky=tk.E)
labeltotpow  = tk.Label(gui,text="  0.000 mW")
labeltotpow .grid(row=6, column= 8, sticky=tk.E)
labeltotcurl = tk.Label(gui,text="I_tot: ")
labeltotcurl.grid(row=6, column=11, sticky=tk.E)
labeltotcur  = tk.Label(gui,text="  0.000 mA")
labeltotcur .grid(row=6, column=12, sticky=tk.E)
"""

#buttonmeasuregnd = tk.Button(gui,text='Measure ground', command=measureground)
#buttonmeasuregnd.grid(row=7, column=7, columnspan=2)
#labelmeasuregndl = tk.Label(gui,text="V_gnd: ")
#labelmeasuregndl.grid(row=7, column=9, sticky=tk.E)
#labelmeasuregnd  = tk.Label(gui,text=" 0.000 V")
#labelmeasuregnd .grid(row=7, column=10, sticky=tk.E)
"""
buttonSCurveTHR = tk.Button(gui,text='SCurve THR', command=doSCurveTHR)
buttonSCurveTHR.grid(row=8, column=7, columnspan=2)
buttonSCurveCAL = tk.Button(gui,text='SCurve CAL', command=doSCurveCAL)
buttonSCurveCAL.grid(row=8, column=9, columnspan=2)
buttonTrim = tk.Button(gui,text='Trim', command=doTrimming)
buttonTrim.grid(row=8, column=11, columnspan=2)

labelrefvall = tk.Label (gui,text="Reference:", bg="white", fg="black")
labelrefvall.grid(row=9, column=8, columnspan=1)
entryrefval = tk.Entry(gui)
entryrefval.insert(0, 15)
entryrefval.grid(row=9, column=10, columnspan=3)
labelextrvall = tk.Label (gui,text="Extract:", bg="white", fg="black")
labelextrvall.grid(row=10, column=8, columnspan=1)
entryextrval = tk.Entry(gui)
entryextrval.insert(0, 85)
entryextrval.grid(row=10, column=10, columnspan=3)

buttonCalibBias = tk.Button(gui,text='Bias Calibration', command=doCalibBias)
buttonCalibBias.grid(row=11, column=7, columnspan=2)
buttonIVCurve = tk.Button(gui,text='IV Curve', command=dosomething)
buttonIVCurve.grid(row=11, column=9, columnspan=2)
buttonPixAlive = tk.Button(gui,text='Pixel Alive', command=dosomething)
buttonPixAlive.grid(row=11, column=11, columnspan=2)

buttonRegisterTest = tk.Button(gui,text='Test Registers', command=doRegisterTest)
buttonRegisterTest.grid(row=12, column=7, columnspan=2)
"""

### Some random stuff - helps me getting alingment right
zxca  = tk.Label(gui,text="")
zxca .grid(row=7, column=13, sticky=tk.E)
zxcb  = tk.Label(gui,text="")
zxcb .grid(row=8, column=13, sticky=tk.E)
zxcc  = tk.Label(gui,text="")
zxcc .grid(row=9, column=13, sticky=tk.E)
zxcd  = tk.Label(gui,text="")
zxcd .grid(row=10, column=13, sticky=tk.E)
zxce  = tk.Label(gui,text="")
zxce .grid(row=11, column=13, sticky=tk.E)
zxcf  = tk.Label(gui,text="")
zxcf .grid(row=12, column=13, sticky=tk.E)
zxcg  = tk.Label(gui,text="")
zxcg .grid(row=13, column=13, sticky=tk.E)
zxch  = tk.Label(gui,text="")
zxch .grid(row=14, column=13, sticky=tk.E)
zxci  = tk.Label(gui,text="")
zxci .grid(row=15, column=13, sticky=tk.E)
zxcj  = tk.Label(gui,text="")
zxcj .grid(row=16, column=13, sticky=tk.E)
zxck  = tk.Label(gui,text="")
zxck .grid(row=17, column=13, sticky=tk.E)
zxcl  = tk.Label(gui,text="")
zxcl .grid(row=18, column=13, sticky=tk.E)
zxcm  = tk.Label(gui,text="")
zxcm .grid(row=19, column=13, sticky=tk.E)
zxcn  = tk.Label(gui,text="")
zxcn .grid(row=20, column=13, sticky=tk.E)
zxco  = tk.Label(gui,text="")
zxco .grid(row=21, column=13, sticky=tk.E)
zxcp  = tk.Label(gui,text="")
zxcp .grid(row=22, column=13, sticky=tk.E)
zxcq  = tk.Label(gui,text="")
zxcq .grid(row=23, column=13, sticky=tk.E)
zxcr  = tk.Label(gui,text="")
zxcr .grid(row=24, column=13, sticky=tk.E)
zxcs  = tk.Label(gui,text="")
zxcs .grid(row=25, column=13, sticky=tk.E)
zxct  = tk.Label(gui,text="")
zxct .grid(row=26, column=13, sticky=tk.E)
zxcu  = tk.Label(gui,text="")
zxcu .grid(row=27, column=13, sticky=tk.E)
zxcv  = tk.Label(gui,text="")
zxcv .grid(row=28, column=13, sticky=tk.E)
zxcw  = tk.Label(gui,text="")
zxcw .grid(row=29, column=13, sticky=tk.E)
zxcx  = tk.Label(gui,text="")
zxcx .grid(row=30, column=13, sticky=tk.E)
zxcy  = tk.Label(gui,text="")
zxcy .grid(row=31, column=13, sticky=tk.E)
zxcz  = tk.Label(gui,text="")
zxcz .grid(row=32, column=13, sticky=tk.E)

#### ACTUALLY RUNNNING  #####
gui.mainloop()
