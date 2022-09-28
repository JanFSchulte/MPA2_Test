import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from tkinter import ttk

from utilities import *
from main import *
#from guihelpers import *

from stepping import *

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

def quitanddestroy(win):
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

#CommandLinel = tk.Label (gui,text="Commandline:", bg="white", fg="black")
#CommandLinel.grid(row=15, column=0, columnspan=2)

#myCommandLine = tk.Entry(gui)
#CommandLine.bind("<Key>", executecommand)
#myCommandLine.bind("<Return>", executecommand)
#myCommandLine.grid(row=15, column=1, columnspan=5)

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

#HelpPointer = tk.Label(gui, text = "For procedure see Help Menu.")
#HelpPointer.grid(row=0, column=1, columnspan=5)

# Functions that actuallly run tests
#labelButtons = tk.Label(gui,text="Functions")                                                                                                              
#labelButtons.grid(row=0, column=7, columnspan=2)    

# Load firmware
#buttonFirmware = tk.Button(gui,text='Load Firmware', command=loadFirmware)
#buttonFirmware.grid(row=1, column=7, columnspan=2)

right = tk.Frame(gui)
right.grid(row=0, column=7, columnspan=7, rowspan=20)

tabControl = ttk.Notebook(right)
tab1 = tk.Frame(tabControl)
tab2 = tk.Frame(tabControl)
tab3 = tk.Frame(tabControl)
tab4 = tk.Frame(tabControl)

tabControl.add(tab1, text="Manual MPA test")
tabControl.add(tab2, text="Automated MPA test")
tabControl.add(tab3, text="Debug S-Curves")
tabControl.add(tab4, text="Plotting")
tabControl.pack(expand=1, fill='both')

# First tab: single MPA test commands
#tab1.grid(row=1,column=0,columnspan=7,rowspan=19)

# Define our switch function for pon/poff                                                                       
def power_switch():

    global power_on

    # if on turn off                                                        
    if power_on:
        poff()
        power_on = False
        buttonOn.config(bg="green",text="Power On")

    # if off turn on                                                   
    else:
        power_on = pon()
        if power_on:
            buttonOn.config(bg="red",text="Power Off")

power_on = False

# power on button
buttonOn = tk.Button(tab1,text='Power On', bg="green", command=power_switch)                                  
buttonOn.grid(row=1, column=0, columnspan=1)                                                                        

# pixel alive button
buttonPa = tk.Button(tab1,text='Pixel Alive', command=pa)                                                     
buttonPa.grid(row=1, column=1, columnspan=1)                                                                        

# IV scan button
buttonIVScan = tk.Button(tab1,text='IV Scan', command=lambda: IVScan(mapsaid=MaPSAID.get()))                  
buttonIVScan.grid(row=1, column=2, columnspan=1)   

# Probe station motion                                                                                                                      
labelMotion = tk.Label(tab1,text="Probe station motion")                                                                                    
labelMotion.grid(row=2, column=0, columnspan=1)      

# Define our switch function for needles up/down                                                                                                 
def needles_switch():                                                                                                                             
    global needles_up                                                                                                                          
    # if up then lower                                                                                                                         
    if needles_up:                                                                                                                               
        buttonUp.config(bg="red",text="Raise Needles")                                                                                           
        lower_needles()
        labelHeight.config(text="At contact height")
        needles_up = False                                                                                                                   
                                                                                                                                             
    # if down then raise                                                                                                                     
    else:                                                                                                                                   
        buttonUp.config(bg="green",text="Lower needles")                                                                                     
        lift_needles()
        labelHeight.config(text="At separation height")
        needles_up = True                                                                                                                      

lift_needles()
labelHeight = tk.Label(tab1,text="At separation height")
labelHeight.grid(row=3,column=1,columnspan=3)
needles_up = True

buttonUp = tk.Button(tab1,text='Lower Needles',bg="green",command=needles_switch)                                                             
buttonUp.grid(row=3, column=0, columnspan=1) 

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
buttonStep.grid(row=4, column=0, columnspan=1)  

# Define checkboxes for MPA tests
labelTests = tk.Label(tab1,text="Select MPA tests to run")
labelTests.grid(row=5, column=0, columnspan=1)

testRegister     = tk.IntVar(value=1)
testWaferRoutine = tk.IntVar(value=1)
testMaskPAlive   = tk.IntVar(value=1)
testPosttrimS    = tk.IntVar(value=1)
testBB           = tk.IntVar(value=1)

testRegisterButton     = tk.Checkbutton(tab1, text='Registers', variable=testRegister,     onvalue=1, offvalue=0)
testWaferRoutineButton = tk.Checkbutton(tab1, text='Wafer Tests',    variable=testWaferRoutine, onvalue=1, offvalue=0)
testMaskPAliveButton   = tk.Checkbutton(tab1, text='Mask/Alive',    variable=testMaskPAlive,   onvalue=1, offvalue=0)
testPosttrimSButton    = tk.Checkbutton(tab1, text='Posttrim S',    variable=testPosttrimS,    onvalue=1, offvalue=0)
testBBButton           = tk.Checkbutton(tab1, text='Bad Bump',      variable=testBB      ,     onvalue=1, offvalue=0)

testRegisterButton.grid(row=6,column=0,columnspan=1)
testWaferRoutineButton.grid(row=6,column=1,columnspan=1)
testMaskPAliveButton.grid(row=6,column=2,columnspan=1)

testPosttrimSButton.grid(row=7,column=1,columnspan=1)
testBBButton.grid(row=7,column=2,columnspan=1)

# This button runs the MPA test according to chechboxes
buttonTestMPA = tk.Button(tab1,text='Test 1 MPA', bg="green", command=lambda: mpa_test(mapsaid=MaPSAID.get(),
                                                                                       chipid=MPAID.get(),
                                                                                       testregister=testRegister.get(),
                                                                                       testwaferroutine=testWaferRoutine.get(),
                                                                                       testmaskpalive=testMaskPAlive.get(),
                                                                                       testpretrim=False,
                                                                                       testtrim=testPosttrimS.get(),
                                                                                       testposttrim=testPosttrimS.get(),
                                                                                       testbb=testBB.get()))

buttonTestMPA.grid(row=8, column=0, columnspan=1)

# Second tab: automated stepping across one side
buttonAutomated = tk.Button(tab2,text='Test 8 MPA', bg="green", command=lambda: scan_side(mapsaid=MaPSAID.get()))
buttonAutomated.grid(row=1, column=1, columnspan=1)

# Third tab: debugging using S-curves


# Fourth tab: drawing 1D plots


#### ACTUALLY RUNNNING  #####
gui.mainloop()
