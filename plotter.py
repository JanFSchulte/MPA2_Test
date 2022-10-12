import pandas as pd
import argparse
import matplotlib.pyplot as plt
import numpy as np
from math import erfc
from pathlib import Path
import sys, os

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
        filename = "../Results_MPATesting/"+mapsaid+"/IVScan_"+mapsaid+".csv"
        df = pd.read_csv(filename, header=0)
        df.plot.scatter(x=0,y=1)
        plt.xlabel('Voltage [V]')
        plt.ylabel('Current [uA]')
        plt.show()

def errorfc_woffset(x, *p):
        a, mu, sigma, offset = p
        return a*0.5*erfc((x-mu)/sigma)+offset

#parser = argparse.ArgumentParser()
#parser.add_argument('filename')
#parser.add_argument('-n', type=int, help="Number of pixels to plot (1d plots only)")
#parser.add_argument('-p', '--pixel', type=int, help="Only select specific pixel")
#parser.add_argument('-o', '--overlay', action="store_true", help="Overlay fit result. Requires -p")
#parser.add_argument('-m', '--map', action="store_true", help="Plot 2d")
#parser.add_argument('--log', action="store_true", help="Log plot")
#parser.add_argument('-g','--greater-zero', action="store_true", help="Restrict histogram statistics to pixel values greater 0.")
#parser.add_argument('-l','--linear', action="store_true", help="Show linear plot instead of 1d histogram")
#parser.add_argument('-st','--scatter-trim', action="store_true", help="Scatter plot: baseline vs. trim bits, filename should be the threshold scan")


#args = parser.parse_args()

#if args.scatter_trim:

#    l = [
#        "PostTrim_THR_THR_Mean.csv",
#        "PreTrim_THR_THR_Mean.csv",
#        "PreTrim_CAL_CAL_Mean.csv",
#        "PostTrim_CAL_CAL_Mean.csv"
#        ]
#    for plottype in l:
#        if plottype in args.filename:
#            trimpath = args.filename.replace(plottype,"Trim_trimbits.csv")
#            break
#    else:
#        print("Not plottable, exit...")
#        sys.exit(0)
#    df = pd.read_csv(args.filename, index_col=0)
#    df2 = pd.read_csv(trimpath, index_col=0)
#    df = df.join(df2["0"],rsuffix='_right')

#    ax = df.plot.scatter(x="0", y="0_right", xlabel=plottype[:-4], ylabel="Trim bits")
#    ax.hlines(y=0, xmin=df['0'].min(), xmax=df['0'].max(), linewidth=1, color='r')
#    ax.hlines(y=31, xmin=df['0'].min(), xmax=df['0'].max(), linewidth=1, color='r')


# Plot Chip maps + 1d histogram
def draw_2D(mapsaid, chipid, key, cmd = ""):

        if len(mapsaid) < 1 or len(chipid) < 1:
                print("Device ID is too short")
                return

        print("Plotting 2D map of " + key)

        if cmd == "":
                cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/mpa_test_'+mapsaid+'_' + chipid + '_*_' + key + '.csv'
        filename = get_recent(cmd)

        df = pd.read_csv(filename, index_col=0)
        a = df.to_numpy().reshape(16,118)
        fig, ax = plt.subplots(1, 1)
        im1 = ax.imshow(a, cmap='viridis', interpolation='none',aspect = 1446/100., origin="lower")
        plt.set_xlabel('column')
        plt.set_ylabel('row')
        plt.suptitle(mapsaid + ' chip ' + chipid)
        plt.colorbar(im1, ax=ax, label=key)
        plt.show()

def draw_1D(mapsaid, chipid, key, cmd = ""):

        if len(mapsaid) < 1 or len(chipid) < 1:
                print("Device ID is too short")
                return

        print("Plotting 1D map of " + key)

        if cmd=="":
                cmd = 'ls ../Results_MPATesting/'+ mapsaid + '/mpa_test_'+mapsaid+'_' + chipid + '_*_' + key + '.csv'
        filename = get_recent(cmd)

        df = pd.read_csv(filename, index_col=0)
        values = df.to_numpy()

        fig, ax = plt.subplots(1, 1)
        ax.hist(values,bins=100) #np.linspace(0,256,256))
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
