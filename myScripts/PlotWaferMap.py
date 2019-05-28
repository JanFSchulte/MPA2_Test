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
        data = iter(results)
        wfmap = np.zeros(np.shape(self.mask), dtype=float)
        for x in range(np.shape(self.mask)[0]):
            for y in range(np.shape(self.mask)[1]):
                if(self.mask[x,y]):
                    d = data.next()
                    wfmap[x,y] = d
        cmap = plt.cm.RdBu
        cmap.set_bad(color='white')
        wfmap = np.ma.masked_where(self.mask==0, wfmap)
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.axis('off')
        #cbar.set_label(label, rotation=270)
        i = ax.imshow(wfmap,interpolation='none', vmin=wfmap.min(), vmax=wfmap.max(),cmap=cmap)
        #p = ax.pcolor(X/(2*np.pi), Y/(2*np.pi), Z, cmap=cm.RdBu, vmin=abs(Z).min(), vmax=abs(Z).max())
        fig.colorbar(i)  # note that colorbar is a method of the figure, not the axes
        plt.show()


    def set_wafer_map(self, map='default'):
        if(map=='default'):
            self.mask = np.array(
                [[0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,1,1,1,1,1,0,0,0],
                 [0,0,1,1,1,1,1,1,1,1,0,0],
                 [1,1,1,1,1,1,1,1,1,1,1,0],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,1,1,1,1,1,1,1,1,1,1,0],
                 [0,1,1,1,1,1,1,1,1,1,1,0],
                 [0,0,1,1,1,1,1,1,1,0,0,0],
                 [0,0,0,0,0,1,1,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0]])
        elif( len(np.shape(map)) != 2 ):
            print("->\tIncompatible wafer map")
