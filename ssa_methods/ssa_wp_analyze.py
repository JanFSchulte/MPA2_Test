from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from collections import OrderedDict
from myScripts.wafer_plot import *

'''
sa = ssa_wp_analyze()
sa.import_data()
sa.plot_wafer('all')
'''

class ssa_wp_analyze():
    def __init__(self):
        pass

    def import_data(self, wafername = 'Wafer_W3_v3', folder = '../SSA_Results/'):
        summary = CSV.csv_to_array(folder+'/'+wafername+'/GlobalSummary.csv', noheader=True)
        expvect = CSV.csv_to_array('ssa_methods/Configuration/expected_values.csv')
        for version in range(8,0,-1):
            strm = "_v{:d}".format(version)
            v1 = [i for (i,v) in enumerate(summary[:,0]) if strm in v]
            v0 = np.array(v1)-1
            summary= np.delete(summary, v0, axis=0)

        self.expected = OrderedDict()
        self.measured = OrderedDict()
        self.results = OrderedDict()
        self.chipsum = {
            'memory_1V0': np.ones(len(summary)),
            'memory_1V2': np.ones(len(summary)),
            'stub'      : np.ones(len(summary)),
            'analog'    : np.ones(len(summary)),
            'all'       : np.ones(len(summary)),
            'all-m'     : np.ones(len(summary)),
            'all-m1v0'  : np.ones(len(summary))}
        resor = abs
        cnt = 2;
        for inst in expvect:
            self.expected[ inst[0] ] = inst[1:]
            self.measured[ inst[0] ] = summary[:, cnt]
            tmp = []
            chipn = 0;
            for i in summary[:, cnt]:
                if( (i>=inst[1]) and (i<=inst[2])):
                    tmp.append(1)
                else:
                    self.chipsum['all'][chipn] = 0
                    if(  inst[0] in ['Memory1_1050V', 'Memory2_1050V', 'L1_data']):
                        self.chipsum['memory_1V0'][chipn] = 0
                    elif(inst[0] in ['Memory2_1200V', 'Memory2_1200V', 'HIP_flags']):
                        self.chipsum['memory_1V2'][chipn] = 0
                    elif(inst[0] in ['ClusterData_DigitalPulses', 'ClusterData_ChargeInjection',
                                     'alignment_cluster_data', 'alignment_lateral_left, alignment_lateral_right']):
                        self.chipsum['stub'][chipn] = 0
                    else:
                        self.chipsum['analog'][chipn] = 0
                    #print chipn, inst, i
                    tmp.append(0)
                    self.chipsum['all-m']    = np.logical_and( self.chipsum['analog'], self.chipsum['stub'] )
                    self.chipsum['all-m1v0'] = np.logical_and( self.chipsum['analog'], self.chipsum['stub'], self.chipsum['memory_1V2'])
                chipn += 1
            self.results[ inst[0] ] = tmp
            cnt += 1

    def plot_wafer(self, mode = 'all-m'):
        #self.results = np.array(np.random.poisson(3, 90))
        wpt = waferplot()
        wpt.plot(self.chipsum[mode])
