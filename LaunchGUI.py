import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from tkinter import ttk

from utilities import *
from main import *
from plotter import *

import beepy
from stepping import *

logfilename = ""

scurvevals, thresholdvals, noisevals, trimvals, countvals = [], [], [], [], []

counter = 0

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

def quitanddestroy(win):
    poff()
    lift_needles()
    win.quit()
    win.destroy()

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
gui.geometry("1000x450") #You want the size of the app to be 500x500
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
#action_menu.add_command(label="Runtime", command=dosomething)
#action_menu.add_separator() 
action_menu.add_command(label="Exit", command=lambda: quitanddestroy(gui))

info_menu = tk.Menu(a_menu, tearoff=0)
info_menu.add_command(label="Program info", command=action_get_info_dialog)
info_menu.add_command(label="Instructions", command=action_get_procedure_dialog)

a_menu.add_cascade(label="Action", menu=action_menu)
a_menu.add_cascade(label="Help", menu=info_menu)
gui.config(menu=a_menu)

left = tk.Frame(gui)
left.grid(row=0, column=0, columnspan=7, rowspan=20)

myTerminal = tk.Text(left, wrap="word")
myTerminal.grid(row=3, column=0, columnspan=7, rowspan=13)
myTerminal.tag_configure("stderr", foreground="#b22222")

vsb = tk.Scrollbar(orient="vertical", command=myTerminal.yview)
myTerminal.configure(yscrollcommand=vsb.set)
sys.stdout = TextRedirector(myTerminal, "stdout")
sys.stderr = TextRedirector(myTerminal, "stderr")

def executecommand(event):
    exec(str(myCommandLine.get()))
    print("Command executed.")

CommandLinel = tk.Label (left,text="Commandline:", bg="white", fg="black")
CommandLinel.grid(row=18, column=0, columnspan=1)

myCommandLine = tk.Entry(left)
myCommandLine.bind("<Return>", executecommand)
myCommandLine.grid(row=18, column=1, columnspan=3)

# Place to write in MaPSA ID
MaPSAIDl = tk.Label (left,text="MaPSA ID:", bg="white", fg="black")
MaPSAIDl.grid(row=1, column=0, columnspan=2)
MaPSAID = tk.Entry(left)
MaPSAID.grid(row=1, column=2, columnspan=3)
MaPSAID.insert(0, '')

# Place to write in MPA ID
MPAIDl = tk.Label (left,text="MPA:", bg="white", fg="black")
MPAIDl.grid(row=1, column=5)
MPAID = tk.Entry(left)
MPAID.grid(row=1, column=6)
MPAID.insert(0, '')

right = tk.Frame(gui)
right.grid(row=0, column=7, columnspan=7, rowspan=20)

tabControl = ttk.Notebook(right)
tab1 = tk.Frame(tabControl)
tab2 = tk.Frame(tabControl)
tab3 = tk.Frame(tabControl)
tab4 = tk.Frame(tabControl)

tabControl.add(tab1, text="Manual MPA test")
tabControl.add(tab2, text="Automated MPA test")
tabControl.add(tab3, text="Plotting")
tabControl.add(tab4, text="Debug S-Curves")
tabControl.pack(expand=1, fill='both')

# First tab: single MPA test commands

height = 'UNKNOWN'
powered = False

# Define our switch function for needles up/down                                                                             
def needles_switch():                                                                                       

    # if up then lower                                                                                        
    if check_height() != 'CONTACT':
        lower_needles()
        buttonUp.config(bg="red",text="Raise Needles")

    # if down then raise                                                                                       
    else:
        if powered:
            poff()
        lift_needles()
        buttonUp.config(bg="green",text="Lower needles")

buttonUp = tk.Button(tab1,text='Lower Needles',bg="green",command=needles_switch)
buttonUp.grid(row=3, column=0, columnspan=1)

labelHeight = tk.Label(tab1,text="At "+height+" height")
labelHeight.grid(row=3,column=1,columnspan=3)
# once every second refresh the height                                                                                     
def refresh_height():
    current_height = check_height()
    height = current_height
    labelHeight.config(text="At "+height+" height")

    if height != 'CONTACT':
        buttonUp.config(text='Lower Needles',bg="green")
    else:
        buttonUp.config(bg="red",text="Raise Needles")

    gui.after(1000, refresh_height) # run itself again after 1000 ms                                                          
refresh_height()

# refresh the flag
def refresh_flag():
    with open('gui_flag.txt','r') as flag_file:
        flag = int(flag_file.read())
        print("Checking flag. Flag = ",flag)
    return flag

# Start with needles up always
lift_needles()

# Define our switch function for pon/poff                                                                       
def power_switch():

    global powered

    # if on turn off
    if powered:
        poff()
        powered = False
        buttonOn.config(bg="green",text="Power On")

    # if off turn on                                                   
    else:
        if check_height() != 'CONTACT':
            print('Only power MPA if probe needles are in contact')
        else:
            if pon():
                powered = True
                buttonOn.config(bg="red",text="Power Off")
            else:
                powered = False
                poff()
                buttonOn.config(bg="green",text="Power On")

# power on button
buttonOn = tk.Button(tab1,text='Power On', bg="green", command=power_switch)                                  
buttonOn.grid(row=1, column=0, columnspan=1)                                                                        

# pixel alive button
buttonPa = tk.Button(tab1,text='Pixel Alive', command=pa)                                                     
buttonPa.grid(row=1, column=1, columnspan=1)                                                                        

# IV scan button
buttonIVScan = tk.Button(tab1,text='IV Scan', command=lambda: IVScan(mapsaid=MaPSAID.get(),delay=5.0))                  
buttonIVScan.grid(row=1, column=2, columnspan=1)   

# Probe station motion                                                                                       
labelMotion = tk.Label(tab1,text="Probe station motion")                                                        
labelMotion.grid(row=2, column=0, columnspan=1)      

# stepping function
def step_one_mpa():

    start_chip = MPAID.get()

    if len(start_chip) < 1:
        print("MPA ID " + start_chip + " is too short.")
        return
        
    end_chip = step_nMPA(start_chip,1)
    MPAID.delete(0,len(start_chip))
    MPAID.insert(0,str(end_chip))
    needles_switch()    

buttonStep = tk.Button(tab1,text='Step 1 MPA', command=step_one_mpa)
buttonStep.grid(row=11, column=1, columnspan=1)  

# Define checkboxes for MPA tests
labelTests = tk.Label(tab1,text="Select MPA tests to run")
labelTests.grid(row=5, column=0, columnspan=1)

testWaferRoutine = tk.IntVar(value=1)
testMaskPAlive   = tk.IntVar(value=1)
testPretrimS     = tk.IntVar(value=1)
testPosttrimS    = tk.IntVar(value=1)
testBB           = tk.IntVar(value=1)

testWaferRoutineButton = tk.Checkbutton(tab1, text='Wafer Tests',    variable=testWaferRoutine, onvalue=1, offvalue=0)
testMaskPAliveButton   = tk.Checkbutton(tab1, text='Mask/Alive',    variable=testMaskPAlive,   onvalue=1, offvalue=0)
testPretrimSButton     = tk.Checkbutton(tab1, text='Pretrim S',     variable=testPretrimS,     onvalue=1, offvalue=0)
testPosttrimSButton    = tk.Checkbutton(tab1, text='Posttrim S',    variable=testPosttrimS,    onvalue=1, offvalue=0)
testBBButton           = tk.Checkbutton(tab1, text='Bad Bump',      variable=testBB      ,     onvalue=1, offvalue=0)

# Place to write in trim threshold 
Triml = tk.Label (tab1,text="Trim to [DAC]:", bg="white", fg="black")
Triml.grid(row=9, column=1)
trim_to = tk.Entry(tab1)
trim_to.grid(row=9, column=2)
trim_to.insert(0, '100')

testWaferRoutineButton.grid(row=6,column=0,columnspan=1)
testMaskPAliveButton.grid(row=7,column=0,columnspan=1)
testPretrimSButton.grid(row=8,column=0,columnspan=1)
testPosttrimSButton.grid(row=9,column=0,columnspan=1)
testBBButton.grid(row=10,column=0,columnspan=1)

# This button runs the MPA test according to chechboxes
buttonTestMPA = tk.Button(tab1,text='Test 1 MPA', bg="green", command=lambda: mpa_test(mapsaid=MaPSAID.get(),
                                                                                       chipid=MPAID.get(),
                                                                                       testregister=False,
                                                                                       testwaferroutine=testWaferRoutine.get(),
                                                                                       testmaskpalive=testMaskPAlive.get(),
                                                                                       testpretrim=testPretrimS.get(),
                                                                                       testtrim=int(trim_to.get()),
                                                                                       testposttrim=testPosttrimS.get(),
                                                                                       testbb=testBB.get()))

buttonTestMPA.grid(row=11, column=0, columnspan=1)

# Second tab: automated stepping across one side
def scan_side(basepath="../Results_MPATesting/",
              #mapsaid="AssemblyX",
              #chipid="ChipY",
              timestamp=True,
              testregister=True,
              testwaferroutine=True,
              testmaskpalive=True,
              testpretrim=False,
              testtrim=100,
              testposttrim=True,
              testbb=True):

    mapsaid=MaPSAID.get()
    print("Testing MaPSA " + mapsaid)

    start_chip = int(MPAID.get())

    nchip = start_chip
    test_tries = 0
    max_tries = 1

    end_chip = 8
    if start_chip > 8:
        end_chip = 16

    flag = refresh_flag()
    while flag > 0:

        chipid = MPAID.get()
        nchip = int(chipid)

        print("Beginning test of MPA " + str(nchip))

        lower_needles()
        good_contact = pon()

        if not good_contact:
            print(bcolors.FAIL + "Could not get good contact on MPA " + str(nchip) + bcolors.RESET)
            beepy.beep(3)
            test_tries += 1
            poff()
            if test_tries < max_tries:
                lift_needles()
                lower_needles()
                continue
            else:
                # step to next
                # continue
                return

        try:
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
        except TypeError:
            print("Lost contact")
            beepy.beep(3)
            test_tries += 1
            poff()
            if test_tries < max_tries:
                lift_needles()
                lower_needles()
                continue
            else:
                # step to next                                                                                                              
                # continue                                                                                                          
                return

        if successful_test:
#            beepy.beep(6)
            print("Test succeeded on MPA " + str(nchip))
        else:
            print("Test failed on MPA " + str(nchip))
            beepy.beep(3)
            test_tries += 1
            poff()
            if test_tries < max_tries:
                lift_needles()
                lower_needles()
                continue
            else:
                # step to next                                                                                                
                # continue                                                                                          
                return

        if nchip == 1:

            IVScan(mapsaid=MaPSAID.get(),delay=5.0)

            # Add in here some quick analysis of IV scan
            good_iv = True


            if good_iv:
                print(bcolors.OK + "IV Scan succeeded on MPA " + str(nchip) + bcolors.RESET)
            else:
                print(bcolors.FAIL + "IV Scan failed on MPA " + str(nchip) + bcolors.RESET)
                beepy.beep(3)
                #                break          

        flag = refresh_flag()

        if flag:
            if end_chip == nchip:
                beepy.beep(6)
                break
            else:
                lift_needles()
                step_one_mpa()
                test_tries = 0

    return



# Define checkboxes for MPA tests                                                                             
labelTests2 = tk.Label(tab2,text="Select MPA tests to run")
labelTests2.grid(row=1, column=0, columnspan=1)

testWaferRoutine2 = tk.IntVar(value=1)
testMaskPAlive2   = tk.IntVar(value=1)
testPretrimS2     = tk.IntVar(value=1)
testPosttrimS2    = tk.IntVar(value=1)
testBB2           = tk.IntVar(value=1)

testWaferRoutineButton2 = tk.Checkbutton(tab2, text='Wafer Tests',    variable=testWaferRoutine2, onvalue=1, offvalue=0)
testMaskPAliveButton2   = tk.Checkbutton(tab2, text='Mask/Alive',    variable=testMaskPAlive2,   onvalue=1, offvalue=0)
testPretrimSButton2     = tk.Checkbutton(tab2, text='Pretrim S',     variable=testPretrimS2,     onvalue=1, offvalue=0)
testPosttrimSButton2    = tk.Checkbutton(tab2, text='Posttrim S',    variable=testPosttrimS2,    onvalue=1, offvalue=0)
testBBButton2           = tk.Checkbutton(tab2, text='Bad Bump',      variable=testBB2      ,     onvalue=1, offvalue=0)

# Place to write in trim threshold                                                                                          
Triml2 = tk.Label (tab2,text="Trim to [DAC]:", bg="white", fg="black")
Triml2.grid(row=5, column=1)
trim_to2 = tk.Entry(tab2)
trim_to2.grid(row=5, column=2)
trim_to2.insert(0, '100')

testWaferRoutineButton2.grid(row=2,column=0,columnspan=1)
testMaskPAliveButton2.grid(row=3,column=0,columnspan=1)
testPretrimSButton2.grid(row=4,column=0,columnspan=1)
testPosttrimSButton2.grid(row=5,column=0,columnspan=1)
testBBButton2.grid(row=6,column=0,columnspan=1)

buttonAutomated = tk.Button(tab2,text='Test 8 MPA', bg="green", command=lambda: scan_side(
                                                                                          testregister=False,
                                                                                          testwaferroutine=testWaferRoutine2.get(),         
                                                                                          testmaskpalive=testMaskPAlive2.get(),              
                                                                                          testpretrim=testPretrimS2.get(),   
                                                                                          testtrim=int(trim_to2.get()),
                                                                                          testposttrim=testPosttrimS2.get(),   
                                                                                          testbb=testBB2.get()))   

buttonAutomated.grid(row=7, column=1, columnspan=1)

# Third tab: draw summary plots

buttonDrawIVScan = tk.Button(tab3,text='Draw IV', command=lambda: draw_IVScan(mapsaid=MaPSAID.get()))
buttonDrawIVScan.grid(row=1, column=0, columnspan=1)

allkeys = ["pixelalive","mask_test","PostTrim_THR_THR_RMS", "PostTrim_THR_THR_Mean", "PostTrim_CAL_CAL_RMS","PostTrim_CAL_CAL_Mean","BumpBonding_Noise_BadBump","BumpBonding_BadBumpMap"]

buttonDrawAll2D = tk.Button(tab3,text='Draw 2D summary plots', command=lambda: summary_plots(MaPSAID.get(),bases=allkeys), bg="green")
buttonDrawAll2D.grid(row=2, column=0, columnspan=1)

# Alive and mask                                                                                                                                      
#buttonDrawPixelAlive2D = tk.Button(tab3,text='Draw Pixel Alive 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["pixelalive"]))
#buttonDrawPixelAlive2D.grid(row=3, column=0, columnspan=1)
#buttonDrawPixelMask2D = tk.Button(tab3,text='Draw Pixel Mask 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["mask_test"]))
#buttonDrawPixelMask2D.grid(row=3, column=1, columnspan=1)

# THR S-curves
#buttonDrawTHRNoisePosttrim2D = tk.Button(tab3,text='Draw posttrim THR noise 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_THR_THR_RMS"]))
#buttonDrawTHRNoisePosttrim2D.grid(row=4, column=0, columnspan=1)
#buttonDrawTHRMeanPosttrim2D = tk.Button(tab3,text='Draw posttrim THR mean 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_THR_THR_Mean"]))
#buttonDrawTHRMeanPosttrim2D.grid(row=4, column=1, columnspan=1)

# CAL S-curves  
#buttonDrawCALNoisePosttrim2D = tk.Button(tab3,text='Draw posttrim CAL noise 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_CAL_CAL_RMS"]))
#buttonDrawCALNoisePosttrim2D.grid(row=5, column=0, columnspan=1)
#buttonDrawCALMeanPosttrim2D = tk.Button(tab3,text='Draw posttrim CAL mean 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_CAL_CAL_Mean"]))
#buttonDrawCALMeanPosttrim2D.grid(row=5, column=1, columnspan=1)

# Bad bump
#buttonDrawBadBumpNoise2D = tk.Button(tab3,text='Draw CAL noise at -2V 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["BumpBonding_Noise_BadBump"]))
#buttonDrawBadBumpNoise2D.grid(row=6, column=0, columnspan=1)
#buttonDrawBadBumpMap2D = tk.Button(tab3,text='Draw bad bump map 2D', command=lambda: draw_2D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["BumpBonding_BadBumpMap"]))
#buttonDrawBadBumpMap2D.grid(row=6, column=1, columnspan=1)

# THR S-curves 1D                                                                                                            
buttonDrawTHRNoisePosttrim1D = tk.Button(tab3,text='Draw posttrim THR noise 1D', command=lambda: draw_1D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_THR_THR_RMS"]))
buttonDrawTHRNoisePosttrim1D.grid(row=7, column=0, columnspan=1)
buttonDrawTHRMeanPosttrim1D = tk.Button(tab3,text='Draw posttrim THR mean 1D', command=lambda: draw_1D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_THR_THR_Mean"]))
buttonDrawTHRMeanPosttrim1D.grid(row=7, column=1, columnspan=1)

# CAL S-curves 1D                                                                                                    
buttonDrawCALNoisePosttrim1D = tk.Button(tab3,text='Draw posttrim CAL noise 1D', command=lambda: draw_1D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_CAL_CAL_RMS"]))
buttonDrawCALNoisePosttrim1D.grid(row=8, column=0, columnspan=1)
buttonDrawCALMeanPosttrim1D = tk.Button(tab3,text='Draw posttrim CAL mean 1D', command=lambda: draw_1D(mapsaid=MaPSAID.get(),chipid=MPAID.get(),keys=["PostTrim_CAL_CAL_Mean"]))
buttonDrawCALMeanPosttrim1D.grid(row=8, column=1, columnspan=1)

# Fourth tab: draw S-Curves
buttonTHR = tk.Button(tab4,text='Draw THR', command=lambda: draw_SCurve(MaPSAID.get(), MPAID.get(), "PreTrim_THR_THR"))
buttonTHR.grid(row=1, column=0, columnspan=1)

buttonCAL = tk.Button(tab4,text='Draw CAL', command=lambda: draw_SCurve(MaPSAID.get(), MPAID.get(), "PreTrim_CAL_CAL"))
buttonCAL.grid(row=2, column=0, columnspan=1)

buttonTHR2 = tk.Button(tab4,text='Draw THR posttrim', command=lambda: draw_SCurve(MaPSAID.get(), MPAID.get(), "PostTrim_THR_THR"))
buttonTHR2.grid(row=3, column=0, columnspan=1)

buttonCAL2 = tk.Button(tab4,text='Draw CAL posttrim', command=lambda: draw_SCurve(MaPSAID.get(), MPAID.get(), "PostTrim_CAL_CAL"))
buttonCAL2.grid(row=4, column=0, columnspan=1)

#### ACTUALLY RUNNNING  #####
gui.mainloop()
