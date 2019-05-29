import pandas as pd
import seaborn as sb
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
from itertools import product
from wafer_map import wm_app
from wafer_map import gen_fake_data
from matplotlib.patches import Ellipse

'''
Example:
results = np.array(np.random.poisson(3, 90))
wpt = waferplot()
wpt.plot(results)
'''

class waferplot():
    def __init__(self, wafermap='default'):
        self.set_wafer_map(wafermap)

    def plot(self, results, label='Percent'):
        ncol = np.shape(self.mask)[0]
        nrow = np.shape(self.mask)[1]
        data = iter( self.adapt_vector(results))
        wfmap = np.zeros(np.shape(self.mask), dtype=float)
        for x in range(np.shape(self.mask)[0]):
            for y in range(np.shape(self.mask)[1]):
                if(self.mask[x,y]):
                    d = data.next()
                    wfmap[x,y] = d
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
        waferedge = Ellipse(
            ((nrow-1.5)/2.0, (ncol-0.5)/2.0),
            nrow+1, ncol+1 ,
            facecolor='None', edgecolor='black',
            lw=1, zorder=10)
        waferimg = ax.imshow(
            wfmap,interpolation='none',
            aspect=(nrow/float(ncol)),
            vmin=wfmap.min(), vmax=wfmap.max(),
            cmap=cmap)
        #p = ax.pcolor(X/(2*np.pi), Y/(2*np.pi), Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max())
        fig.colorbar(waferimg, fraction=0.046/2, pad=0.04, label=label)
        ax.add_patch(waferedge)
        plt.show()


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
