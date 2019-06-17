import pandas as pd
import seaborn as sb
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
from itertools import product
from matplotlib.patches import Ellipse
import matplotlib as mpl


'''
Example:
results = np.array(np.random.poisson(3, 90))
wpt = waferplot()
wpt.plot(results)
'''

class waferplot():
    def __init__(self, wafermap='default'):
        self.set_wafer_map(wafermap)

    def plot_wafer(self, results, label='Percent', minv='min', maxv='max', reverse=0):
        ncol = np.shape(self.mask)[0]
        nrow = np.shape(self.mask)[1]
        data = iter( self.adapt_vector(results))
        wfmap = np.zeros(np.shape(self.mask), dtype=float)
        for x in range(np.shape(self.mask)[0]):
            for y in range(np.shape(self.mask)[1]):
                if(self.mask[x,y]):
                    d = data.next()
                    wfmap[x,y] = d
        if(reverse):
            cmap = plt.cm.RdYlGn.reversed()
        else:
            cmap = plt.cm.RdYlGn
        cmap.set_bad(color='white')
        wfmap = np.ma.masked_where(self.mask==0, wfmap)
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_subplot(1, 1, 1)
        plt.xlim(-1.5,nrow+1)
        plt.ylim(-1.5,ncol+1)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.axis('off')
        #cbar.set_label(label, rotation=270)
        if(isinstance(minv, str)):
            minval = wfmap.min()
        else:
            minval = minv
        if(isinstance(maxv, str)):
            maxval = wfmap.max()
        else:
            maxval = maxv
        waferedge = Ellipse(
            ((nrow-1.5)/2.0, (ncol-0.5)/2.0),
            nrow+1, ncol+1 ,
            facecolor='None', edgecolor='black',
            lw=1, zorder=10)
        waferimg = ax.imshow(
            wfmap,interpolation='none',
            aspect=(nrow/float(ncol)),
            vmin=minval, vmax=maxval,
            cmap=cmap)
        #p = ax.pcolor(X/(2*np.pi), Y/(2*np.pi), Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max())
        fig.colorbar(waferimg, fraction=0.046/2, pad=0.04, label=label)
        ax.add_patch(waferedge)


    def plot_data(self, results, label='Percent', minv='min', maxv='max', reverse=0, newfigure=1):
        data =  self.adapt_vector(results)
        if(reverse): cmap = plt.cm.RdYlGn.reversed()
        else: cmap = plt.cm.RdYlGn
        if(newfigure):
            fig = plt.figure(figsize=(10,10))
            ax = fig.add_subplot(1, 1, 1)
        #ax.spines["top"].set_visible(False)
        #ax.spines["right"].set_visible(False)
        #plt.axis('off')
        plt.xticks(range(0, len(data), 5), fontsize=16)
        plt.yticks(fontsize=16)
        plt.ylabel(label, fontsize=16)
        plt.xlabel('Chip', fontsize=16)
        if(isinstance(minv, str)): minval = np.min(data)
        else: minval = minv
        if(isinstance(maxv, str)): maxval = np.max(data)
        else: maxval = maxv
        plt.plot(data, 'or' )

    def set_wafer_map(self, map='default'):
        if(map=='default'):
            self.mask = np.array(
                [[0,0,0,0,0,1,1,0,0,0,0,0],
                 [0,0,1,1,1,1,1,1,1,0,0,0],
                 [0,1,1,1,1,1,1,1,1,1,1,0],
                 [1,1,1,1,1,1,1,1,1,1,1,0],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,0],
                 [0,0,1,1,1,1,1,1,1,1,0,0],
                 [0,0,0,0,1,1,1,1,1,0,0,0]])
        elif( len(np.shape(map)) != 2 ):
            print("->\tIncompatible wafer map")

    def adapt_vector(self, vin):
        ncol = np.shape(self.mask)[1]
        nrow = np.shape(self.mask)[0]
        data = iter(vin)
        d = [0]*10
        d[0] = np.sum(self.mask[nrow-1])
        d[1] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2])
        d[2] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3])
        d[3] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4])
        d[4] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5])
        d[5] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5]) + np.sum(self.mask[nrow-6])
        d[6] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5]) + np.sum(self.mask[nrow-6]) + np.sum(self.mask[nrow-7])
        d[7] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5]) + np.sum(self.mask[nrow-6]) + np.sum(self.mask[nrow-7]) + np.sum(self.mask[nrow-8])
        d[8] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5]) + np.sum(self.mask[nrow-6]) + np.sum(self.mask[nrow-7]) + np.sum(self.mask[nrow-8]) + np.sum(self.mask[nrow-9])
        d[9] = np.sum(self.mask[nrow-1]) + np.sum(self.mask[nrow-2]) + np.sum(self.mask[nrow-3]) + np.sum(self.mask[nrow-4]) + np.sum(self.mask[nrow-5]) + np.sum(self.mask[nrow-6]) + np.sum(self.mask[nrow-7]) + np.sum(self.mask[nrow-8]) + np.sum(self.mask[nrow-9]) + np.sum(self.mask[nrow-10])
        vout = []
        vout.extend( vin[0    : d[0]] )
        vout.extend( vin[d[0] : d[1]][::-1] )
        vout.extend( vin[d[1] : d[2]] )
        vout.extend( vin[d[2] : d[3]][::-1] )
        vout.extend( vin[d[3] : d[4]])
        vout.extend( vin[d[4] : d[5]][::-1] )
        vout.extend( vin[d[5] : d[6]] )
        vout.extend( vin[d[6] : d[7]][::-1] )
        vout.extend( vin[d[7] : d[8]] )
        vout.extend( vin[d[8] : d[9]][::-1] )
        return vout

    def reverse_colourmap(cmap, name = 'mycmapr'):
        reverse = []
        k = []
        for key in cmap._segmentdata:
            k.append(key)
            channel = cmap._segmentdata[key]
            data = []
            for t in channel:
                data.append((1-t[0],t[2],t[1]))
            reverse.append(sorted(data))
        LinearL = dict(zip(k,reverse))
        my_cmap_r = mpl.colors.LinearSegmentedColormap(name, LinearL)
        return my_cmap_r
