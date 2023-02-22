import pandas as pd
import argparse
import matplotlib.pyplot as plt
import numpy as np
from math import erfc
from pathlib import Path
import sys, os, csv

from mpa_configurations import *

# Jennet has stolen most of this from Ginger and Andreas

def get_recent(cmd):

        files = os.popen(cmd).read().split()
        
        if len(files) < 1:
                print("Error: no files specified")
                return "0"

        elif len(files) == 1:
                return files[0]

        else:
                maxnbr = 0
                maxidx = -1
                for j, f in enumerate(files):
                        numbers_from_string = int(''.join(list(filter(str.isdigit, f))))
                        if numbers_from_string > maxnbr:
                                maxnbr = numbers_from_string
                                maxidx = j
                return files[maxidx]


def draw_IVScan(mapsaid):

        cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/IVScan_'+mapsaid+'*.csv'
        filename = get_recent(cmd)

        df = pd.read_csv(filename, header=0)
        df.plot.scatter(x=0,y=1)
        plt.xlabel('Voltage [V]')
        plt.ylabel('Current [uA]')
        plt.show()

# Plot Chip maps + 1d histogram
def draw_2D(mapsaid, chipid, keys, cmd = ""):

        if len(mapsaid) < 1 or len(chipid) < 1:
                print("Device ID is too short")
                return

        for i, key in enumerate(keys):

                print("Plotting 2D map of " + key)

                cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/mpa_test_'+mapsaid+'_' + chipid + '_*_' + key + '.csv'
                filename = get_recent(cmd)
                print(filename)

                df = pd.read_csv(filename, index_col=0)
                a = df.to_numpy().reshape(16,118)

                fig, ax = plt.subplots(1, 1)
                im1 = ax.imshow(a, cmap='viridis', interpolation='none', aspect='auto', origin="lower")
                ax.set_xlabel('column')
                ax.set_ylabel('row')
                plt.colorbar(im1, ax=ax, label=key)
                plt.suptitle(mapsaid + ' chip ' + chipid)

        plt.show()

def draw_1D(mapsaid, chipid, keys, cmd = ""):

        if len(mapsaid) < 1 or len(chipid) < 1:
                print("Device ID is too short")
                return

        for i, key in enumerate(keys):

                print("Plotting 1D map of " + key)

                if cmd=="":
                        cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/mpa_test_'+mapsaid+'_' + chipid + '_*_' + key + '.csv'
                filename = get_recent(cmd)

                df = pd.read_csv(filename, index_col=0)
                values = df.to_numpy()

                fig, ax = plt.subplots(1, 1)
                ax.hist(values,bins=25) #np.linspace(0,256,256))
                ax.set_xlabel(key)
                plt.suptitle(mapsaid + ' chip ' + chipid)

                # Draw mean value + labels
                mean_value = np.mean(values)
                rms_value = np.std(values)
                ax.text(0.1,0.8,f"Mean: {np.round(mean_value,2)}",transform = ax.transAxes)
                ax.text(0.1,0.7,f"RMS: {np.round(rms_value,2)}",transform = ax.transAxes)
        plt.show()

def draw_SCurve(mapsaid, chipid, key, single=-1, cmd = ""):

        if len(mapsaid) < 1 or len(chipid) < 1:
                print("Device ID is too short")
                return

        print("Plotting S-curve " + key)

        if cmd == "":
                cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/mpa_test_'+mapsaid+'_' + chipid + '_*_' + key + '.csv'
        filename = get_recent(cmd)
        print(filename)

        df = pd.read_csv(filename,index_col=0,header=0)
        x =range(0,257)

        if single < 0:
                for index, row in df.iterrows():
                        plt.plot(x,row)
                plt.suptitle(key)
        else:
                plt.plot(x,df.iloc[single])
                plt.suptitle(key + " pix " + str(single))
                meanpath = filename.split('.csv')[0]+'_Mean.csv'
                rmspath = filename.split('.csv')[0]+'_RMS.csv'
                print(meanpath, rmspath)                                           
#        mean_df = pd.read_csv(meanpath, index_col=0).iloc[args.pixel]          
#        rms_df = pd.read_csv(rmspath, index_col=0).iloc[args.pixel]            
#        mean=mean_df[0]                                                        
#        rms=rms_df[0]                                                          
#        rr = np.arange(0, 255, 0.1)                                            
#        if "THR" in args.filename:                                             
#            ampl=1000                                                          
#            offset=0                                                           
#        elif ("CAL" in args.filename or                                        
#            "BumpBonding_SCurve" in args.filename):                            
#            ampl=-1000                                                         
#            offset=1000                                                        
#        yy = [ errorfc_woffset(r,ampl,mean,rms,offset) for r in rr]            
#        plt.plot(rr, yy, linestyle='--', label='Fit')                          
#        plt.text(0.8,0.7,f"Mean: {np.round(mean,2)}\nRMS: {np.round(rms,2)}", transform=plt.gca().transAxes)        

        plt.xlabel('DAC units')
        plt.show()


    # Count out-of-range trimbits
#    if "trimbits" in args.filename:
#        out_of_range = df.loc[(df['0'] < 0 ) | (df['0'] >31)]
#        plt.text(0.1,1.12,f"Untrimmable pixels: {len(out_of_range)}", transform=ax2.transAxes)

#else: # Plot raw scurves
#    df = pd.read_csv(args.filename, index_col=0)
#    if args.pixel:
#        df = df.iloc[args.pixel]
#    elif args.n:
#        df = df.iloc[:args.n]

    # Draw 2d "Ph2-ACF style" scurves
#    if args.map:
#        a = df.transpose().values
#        plt.imshow(a, aspect=4, cmap='viridis', vmax=2000, interpolation='none', origin='lower')
#        plt.colorbar()
#    else: # Draw set of 1d curves
#        df.transpose().plot()

    # Overlay fitting result

#    if args.pixel and args.overlay:
#        p = Path(args.filename)
#        if "BumpBonding_SCurve_BadBump" in args.filename:
#            meanpath = args.filename.replace("SCurve","Mean")
#            rmspath = args.filename.replace("SCurve","Noise")
#        else:
#            meanpath = Path.joinpath(p.parent,p.stem+'_Mean'+ p.suffix)
#            rmspath = Path.joinpath(p.parent,p.stem+'_RMS'+ p.suffix)
#            print(meanpath, rmspath)
#        mean_df = pd.read_csv(meanpath, index_col=0).iloc[args.pixel]
#        rms_df = pd.read_csv(rmspath, index_col=0).iloc[args.pixel]
#        mean=mean_df[0]
#        rms=rms_df[0]
#        rr = np.arange(0, 255, 0.1)
#        if "THR" in args.filename:
#            ampl=1000
#            offset=0
#        elif ("CAL" in args.filename or
#            "BumpBonding_SCurve" in args.filename):
#            ampl=-1000
#            offset=1000
#        yy = [ errorfc_woffset(r,ampl,mean,rms,offset) for r in rr]
#        plt.plot(rr, yy, linestyle='--', label='Fit')
#        plt.text(0.8,0.7,f"Mean: {np.round(mean,2)}\nRMS: {np.round(rms,2)}", transform=plt.gca().transAxes)


#plt.legend()
##plt.show(block=True)

def loadValuesFromCSV(csvfilename):
    #print(csvfilename)                                                                                                                
    #valuedict = dict()                                                                                                                
    values = []
    with open(csvfilename, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if row[0] == '':
                continue
            pixedid = int(row[0])
            value = float(row[1])
            #valuedict[pixedid] = value                                                                                                
            values.append(value)
    #return valuedict                                                                                                                  
    return values

def getRowOfMPAinMaPSAs(mpa,row):#this y                                                                                                                 
    #returns row id in a 2D map of a full MaPSA                                                                                                           
    if mpa <  8: return row #keep this notation for more intuition                                                                                  
    if mpa >= 8: return (conf.nrowsnom+1)*2-1 - row-1 #keep this notation for more intuition                                                           
    ###if mpa <  8: return     mpa  * (conf.nrowsnom+1) + (row+1) - 1 #keep this notation for more intuition                                           
    ###if mpa >= 8: return (16-mpa) * (conf.nrowsnom+1) - (row+1) - 1 #keep this notation for more intuition                                         
    return -1 #haha                                                                                                                                   

def getColOfMPAinMaPSAs(mpa,col):
    #returns row id in a 2D map of a full MaPSA                                                                                                          
    ###if mpa <  8: return col #keep this notation for more intuition                                                                                   
    ###if mpa >= 8: return ((conf.ncolsnom+2)*2) - col #keep this notation for more intuition                                                           
    #double chip spacing due to bad graphics                                                                                                              
    #if mpa <  8: return     mpa  * (conf.ncolsnom+2) + col #keep this notation for more intuition                                                         
    #if mpa >= 8: return (16-mpa) * (conf.ncolsnom+2)-2 - col-1 #keep this notation for more intuition - the last chip has not an empty column              
    #nominal                                                                                                                                                
    if mpa <  8: return     mpa  * (conf.ncolsnom+1) + col #keep this notation for more intuition                                                          
    if mpa >= 8: return (16-mpa) * (conf.ncolsnom+1)-1 - col-1 #keep this notation for more intuition - the last chip has not an empty column              
    return -1 #haha                                                                                                                                           

def Plot_Module(inpath="./",mapsa="MaPSA",base="pixelalive",chips=[],s_type="THR",n_pulse=1000,nominal_DAC=-1,plotAverage = False, \
hmax=-1,hmin=-1, percentile = 0.05, identifier="ID-Test",data_label="Label-Test",test_label="Label-Test"):

    if len(chips) < 1:
        chips = [str(i) for i in range(1,17)]

    inputs = []
    for m in chips:
        cmd = 'ls '+ inpath + 'mpa_test_' + mapsa + '_' + m + '_*_'+base + '.csv'
        print(m)
        the_file = get_recent(cmd)
        print(the_file)
        if the_file != '0':
            inputs.append(get_recent(cmd))
        else:
            inputs.append("./dummy.csv")

    if(len(inputs)!=16):
        print("There should be 16 inputs, not "+str(len(inputs))+"!")
    data_arrays = []
    for i in inputs:
            data_temp = loadValuesFromCSV(i)
            data_arrays.append(data_temp)

    MakeModulePlot(arrays_of_data= data_arrays, row = [],col = [],hmin=hmin,hmax=hmax, percentile = percentile, plotAverage = plotAverage, identifier=identifier, data_label=data_label, test_label=test_label)

def MakeModulePlot(arrays_of_data= [ [] ], row = [],col = [],hmin=-1,hmax=-1, percentile = 0.05, plotAverage = True, identifier="", xlabel="columns", data_label="", test_label=""):
                                                                                                                                     
    if len(arrays_of_data)!=16:
        print("A module consists out of 16 MPAs, not "+str(len(arrays_of_data))+"!")
        return
    nmpa = 0
    for data in arrays_of_data:
        if len(data)!=1888:
            print("MPA"+str(nmpa)+" consists out of 1888 pixels, not "+str(len(data))+"!")
            return
        nmpa += 1
    print("Plotting "+test_label+" for "+identifier)
    if len(row)==0:
        row = range(0,conf.nrowsnom+1)
    if len(col)==0:
        #col = range(0,conf.ncolsnom+2)   #due to bad graphics                                                                                                 
        col = range(0,conf.ncolsnom+1)   #nominal                                                                                                              

    #picx = (conf.ncolsnom+2)*8-2#the last chip has not an empty column #double chip spacing - due to poor graphics                                            
    picx = (conf.ncolsnom+1)*8-1#the last chip has not an empty column #nominal                                                                                
    picy = (conf.nrowsnom+1)*2-1
    x = np.zeros( 0, dtype = np.int16 )
    y = np.zeros( 0, dtype = np.int16 )
    w = np.zeros( 0, dtype = np.int16 )
    wa = np.zeros( 0, dtype = np.int16 )
    #print("picdimensions",picx,picy)                                                                                                                          
    for n in range(0,16):
        for r in row:
            for c in col:
                if ((n==7 or n==15) and c >= conf.ncolsnom):
                    continue
                x = np.append(x,getColOfMPAinMaPSAs(n,c))
                y = np.append(y,getRowOfMPAinMaPSAs(n,r))
                if r >=conf.nrowsnom or  c >= conf.ncolsnom:
                    w = np.append(w,-2)
                else:
                    pixelid = conf.pixelidnom(r,c)
                    w = np.append(w,arrays_of_data[n][pixelid])
                    wa = np.append(w,arrays_of_data[n][pixelid])

    wa_sorted = wa
    wa_sorted.sort()
    indexpos = int(next(x for x in wa_sorted if x >= 0))
    precentilepos = int(conf.npixsnom*percentile)
    targetMinValue = wa_sorted[indexpos+precentilepos]*0.75
    targetMaxValue = wa_sorted[-precentilepos]*1.25
    maximum = hmax if hmax >=0 else max(0,targetMaxValue)
    minimum = hmin if hmin >=0 else max(0,targetMinValue)
    if hmax<0 and hmin<0:
        minimum = max(0,max(np.mean(wa) - 4*np.std(wa),0.333*np.mean(wa)))
        maximum = max(0,min(np.mean(wa) + 4*np.std(wa),3.000*np.mean(wa)))
    for index in range(len(w)):
        if w[index]>maximum: w[index] = maximum
        if w[index]>0 and w[index]<minimum: w[index] = minimum

    fig = plt.figure(figsize=(10,5))#just an identifier 5*16, 7.5*2 80 15    10   3                                                                       
    axy = fig.add_subplot(111)
    plt.subplots_adjust(left=0.12, bottom=0.11, right=0.98, top=0.80, wspace=0.2, hspace=0.2)
    plt.hist2d(x,y,weights=w,bins=[picx,picy],cmin=minimum,cmax=maximum,range=[[0,picx],[0,picy] ] )
    cbar = plt.colorbar()
    cbar.set_label(data_label,fontweight='bold',labelpad=15)
    #now start hard-coding stuff for visualization of a MaPSA                                                                                                         

    axy.set_xticks([0,60,119,179,238,298,357,417,476,536,595,655,714,774,833,893,951])
    axy.set_xticklabels(['0','60','0','60','0','60','0','60','0','60','0','60','0','60','0','60','118'])
    axy.set_ylabel("rows", labelpad=15,fontweight='bold')
    axy.set_yticks([0,5,10,15,18,23,28,33])
    axy.set_yticklabels(['0','5','10','15','15','10','5','0'])
    ax2 = axy.twiny()

    ax2.set_xticks([picx-0,picx-60,picx-119,picx-179,picx-238,picx-298,picx-357,picx-417,picx-476,picx-536,picx-595,picx-655,picx-714,picx-774,picx-833,picx-893,picx-951])
    ax2.set_xticklabels(['0','60','0','60','0','60','0','60','0','60','0','60','0','60','0','60','118'])
    ay2 = axy.twinx()

    ay2.set_yticks([0,5,10,15,18,23,28,33])
    ay2.set_yticklabels(['0','5','10','15','15','10','5','0'])
    plt.text(0,40,identifier,fontweight='bold')#identifier is for MaPSA                                                                                    
    plt.text(951,40,test_label,horizontalalignment='right',fontweight='bold')#identifier is for what is plotted                                              
    plt.text(-150,34.3,"columns",fontweight='bold')
    plt.text(-150,36.5,"chip number",color='blue',fontweight='bold')
    plt.text(  60,36.5,'16',color='blue',fontweight='bold')#identifier is for chip ID                                                                         
    plt.text( 179,36.5,'15',color='blue',fontweight='bold')#identifier is for chip ID                                                                     
    plt.text( 298,36.5,'14',color='blue',fontweight='bold')#identifier is for chip ID                                                                      
    plt.text( 417,36.5,'13',color='blue',fontweight='bold')#identifier is for chip ID                                                                          
    plt.text( 536,36.5,'12',color='blue',fontweight='bold')#identifier is for chip ID                                                                                 
    plt.text( 655,36.5,'11',color='blue',fontweight='bold')#identifier is for chip ID                                                                         
    plt.text( 774,36.5,'10',color='blue',fontweight='bold')#identifier is for chip ID                                                                           
    plt.text( 893,36.5,' 9',color='blue',fontweight='bold')#identifier is for chip ID                                                                           
    plt.text(-150,-2.0,"columns",fontweight='bold')
    plt.text(-150,-4.5,"chip number",color='blue',fontweight='bold')
    plt.text(  60,-4.5,' 1',color='blue',fontweight='bold')#identifier is for chip ID                                                                         
    plt.text( 179,-4.5,' 2',color='blue',fontweight='bold')#identifier is for chip ID                                                                        
    plt.text( 298,-4.5,' 3',color='blue',fontweight='bold')#identifier is for chip ID                                                                          
    plt.text( 417,-4.5,' 4',color='blue',fontweight='bold')#identifier is for chip ID                                                                          
    plt.text( 536,-4.5,' 5',color='blue',fontweight='bold')#identifier is for chip ID                                                                          
    plt.text( 655,-4.5,' 6',color='blue',fontweight='bold')#identifier is for chip ID                                                                       
    plt.text( 774,-4.5,' 7',color='blue',fontweight='bold')#identifier is for chip ID                                                                        
    plt.text( 893,-4.5,' 8',color='blue',fontweight='bold')#identifier is for chip ID                                                                           

    if plotAverage:
        plt.text(951,38,"Average %.2f +/- %.2f" % (np.mean(wa), np.std(wa)),horizontalalignment='right')
        plt.grid()

    return 

def summary_plots(mapsaid, bases):

    allkeys = ["pixelalive","mask_test","PostTrim_THR_THR_RMS", "PostTrim_THR_THR_Mean", "PostTrim_CAL_CAL_RMS","PostTrim_CAL_CAL_Mean","BumpBonding_Noise_BadBump","BumpBonding_BadBumpMap"]

    label = {}
    label["pixelalive"] = "Pixel alive test"
    label["mask_test"] = "Pixel masking test"
    label["PostTrim_THR_THR_RMS"] = "rms of THR S Curve (post trimming)"
    label["PostTrim_THR_THR_Mean"] = "mean of THR S Curve (post trimming)"
    label["PostTrim_CAL_CAL_RMS"] = "rms of CAL S Curve (post trimming)"
    label["PostTrim_CAL_CAL_Mean"] = "rms of THR S Curve (post trimming)"
    label["BumpBonding_Noise_BadBump"] = "Bad Bump Test (through noise at BV = -2V)"
    label["BumpBonding_BadBumpMap"] = "Identified abnormal pixel noise (at BV = -2V)"

    zlabel = {}
    zlabel["pixelalive"] = "recorded pulses"
    zlabel["mask_test"] = "recorded pulses"
    zlabel["PostTrim_THR_THR_RMS"] = "rms [THR]"
    zlabel["PostTrim_THR_THR_Mean"] = "mean [THR]"
    zlabel["PostTrim_CAL_CAL_RMS"] = "rms [CAL]"
    zlabel["PostTrim_CAL_CAL_Mean"] = "mean [CAL]"
    zlabel["BumpBonding_Noise_BadBump"] = "noise [CAL] (at BV = -2V)"
    zlabel["BumpBonding_BadBumpMap"] = "is bad bump"
    
    Averaged =  [False,False,False,False, True, True, True, True]

    for b in bases:
        mymax = -1
        if "Noise_BadBump" in b: mymax = 10.
        elif "_Noise_" in b: mymax = 30.
        elif "BadBump" in b: mymax = 1.

        doAverage=False
        if "RMS" in b or "Mean" in b:
            doAverage=True

        Plot_Module(inpath="../Results_MPATesting/"+mapsaid+"/",
                    mapsa=mapsaid,
                    base=b,
                    data_label=zlabel[b],
                    test_label=label[b],
                    identifier=mapsaid,
                    plotAverage=doAverage,
                    hmax=mymax)

    plt.show()
