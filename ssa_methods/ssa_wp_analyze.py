'''
You can use:
>   analyze_all_wafers(LogSuffix='', plot=False)
OR
>   sa = ssa_wp_analyze() # Create object
>   sa.plot_stats('WaferName') # Plot main set of statistics about the selected wafer
OR
>   sa = ssa_wp_analyze()
>   sa.import_data('Wafer_W4', verboselevel=0)
>   sa.plot_wafer_scale('VAL', 'unit', 'min', 'max', reverse=1)

Possible values for 'VAL':
    'I_DVDD_reset' , 'I_AVDD_reset' , 'I_PVDD_reset' , 'I_DVDD_startup' , 'I_AVDD_startup' , 'I_PVDD_startup' , 'Initialize' , 'I_DVDD_uncalibrated' , 'I_AVDD_uncalibrated' , 'I_PVDD_uncalibrated
    'GND_uncalibrated' , 'VBG_uncalibrated' , 'Bias_BOOSTERBASELINE_uncalibrated' , 'Bias_D5BFEED_uncalibrated' , 'Bias_D5PREAMP_uncalibrated' , 'Bias_D5TDR_uncalibrated
    'Bias_D5ALLV_uncalibrated' , 'Bias_D5ALLI_uncalibrated' , 'Bias_D5DAC8_uncalibrated' , 'Bias_THDAC_uncalibrated' , 'Bias_THDACHIGH_uncalibrated' , 'Bias_CALDAC_uncalibrated
    'Calibration' , 'I_DVDD_calibrated' , 'I_AVDD_calibrated' , 'I_PVDD_calibrated' , 'GND_calibrated' , 'VBG_calibrated' , 'Bias_BOOSTERBASELINE_calibrated' , 'Bias_D5BFEED_calibrated
    'Bias_D5PREAMP_calibrated' , 'Bias_D5TDR_calibrated' , 'Bias_D5ALLV_calibrated' , 'Bias_D5ALLI_calibrated' , 'Bias_D5DAC8_calibrated' , 'Bias_THDAC_calibrated Bias_THDACHIGH_calibrated' , 'Bias_CALDAC_calibrated' , '
    'Bias_THDAC_GAIN' , 'Bias_CALDAC_GAIN' , 'Bias_THDAC_OFFS' , 'Bias_CALDAC_OFFS
    'threshold_std_init threshold_std_trim' , 'threshold_std_test' , 'threshold_mean_trim' , 'threshold_mean_test
    'noise_mean_trim' , 'noise_mean_test
    'fe_gain_mean' , 'fe_offs_mean
    'alignment_cluster_data' , 'alignment_lateral_left' , 'alignment_lateral_right' , 'ClusterData_DigitalPulses' , 'ClusterData_ChargeInjection
    'Memory1_1050V' , 'Memory2_1050V' , 'Memory1_1200V' , 'Memory2_1200V' , 'L1_data' , 'HIP_flags
'''


from myScripts.ArrayToCSV import *
from myScripts.Utilities import *
from collections import OrderedDict
from myScripts.wafer_plot import *
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

class ssa_wp_analyze():

    def __init__(self, folder = '../SSA_Results/WaferProbing/', display=False):
        self.folder = folder
        if(display):
            print("->  Available wafers info:")
            for wp in os.listdir(self.folder):
                print("  \t-  "+wp)

    def import_data(self, wafername = 'Wafer_W3_v3', verboselevel = 0):
        self.wafer = wafername
        try:
            summary = CSV.csv_to_array(self.folder+'/'+wafername+'/GlobalSummary.csv', noheader=True)
            expvect = CSV.csv_to_array('ssa_methods/Configuration/expected_values.csv')
        except:
            print("x>  \tSkipping directory " + wafername)
            return False
        if not os.path.exists(self.folder+'/'+wafername+'/plots'):
            os.makedirs(self.folder+'/'+wafername+'/plots')
        for version in range(8,0,-1):
            strm = "_v{:d}".format(version)
            v1 = [i for (i,v) in enumerate(summary[:,0]) if strm in v]
            v0 = np.array(v1)-1
            summary= np.delete(summary, v0, axis=0)
        self.expected = OrderedDict()
        self.measured = OrderedDict()
        self.results = OrderedDict()
        self.chipsum = OrderedDict()
        self.chipsum['power'     ] = np.ones(len(summary))
        self.chipsum['digital'   ] = np.ones(len(summary))
        self.chipsum['lateral'   ] = np.ones(len(summary))
        self.chipsum['bias'      ] = np.ones(len(summary))
        self.chipsum['frontend'  ] = np.ones(len(summary))
        self.chipsum['memory_1V0'] = np.ones(len(summary))
        self.chipsum['memory_1V2'] = np.ones(len(summary))
        self.chipsum['others'    ] = np.ones(len(summary))
        self.chipsum['all'       ] = np.ones(len(summary))
        self.chipsum['all-m1v0'  ] = np.ones(len(summary))
        self.chipsum['all-m'     ] = np.ones(len(summary))

        resor = abs
        cnt = 2;
        for inst in expvect:
            self.expected[ inst[0] ] = inst[1:]
            self.measured[ inst[0] ] = summary[:, cnt]
            tmp = []
            chipn = 0;
            for i in summary[:, cnt]:
                if( (float(i)>=inst[1]) and (float(i)<=inst[2])):
                    tmp.append(1)
                    if(verboselevel>=2):
                        print("->  chip="+str(chipn)+"  "+str(inst[0])+"  value="+str(i)+"  range=["+str(inst[1])+","+str(inst[2])+"]")
                else:
                    if(verboselevel>=1):
                        print("X>\tchip="+str(chipn)+"  "+str(inst[0])+"  value="+str(i)+"  range=["+str(inst[1])+","+str(inst[2])+"]")
                    #self.chipsum['all'][chipn] = 0

                    if(  inst[0] in ['Memory1_1050V', 'Memory2_1050V']):
                        self.chipsum['memory_1V0'][chipn] = 0

                    elif(inst[0] in ['Memory1_1200V', 'Memory2_1200V', 'L1_data', 'HIP_flags']):
                        self.chipsum['memory_1V2'][chipn] = 0

                    elif(inst[0] in ['ClusterData_DigitalPulses', 'ClusterData_ChargeInjection', 'alignment_cluster_data']):
                        self.chipsum['digital'][chipn] = 0

                    elif(inst[0] in ['alignment_lateral_left', 'alignment_lateral_right']):
                        self.chipsum['lateral'][chipn] = 0

                    elif(inst[0] in ['threshold_std_init threshold_std_trim' , 'threshold_std_test' , 'threshold_mean_trim' ,
                                     'threshold_mean_test', 'noise_mean_trim' , 'noise_mean_test', 'fe_gain_mean' , 'fe_offs_mean', 'threshold_std_trim', 'threshold_std_init' ]):
                        self.chipsum['frontend'][chipn] = 0

                    elif(inst[0] in ['Initialize', 'I_DVDD_reset', 'I_AVDD_reset', 'I_PVDD_reset', 'I_DVDD_startup', 'I_AVDD_startup',
                                     'I_PVDD_startup', 'I_DVDD_uncalibrated', 'I_AVDD_uncalibrated', 'I_PVDD_uncalibrated']):
                        self.chipsum['power'][chipn] = 0

                    elif(inst[0] in ['Bias_BOOSTERBASELINE_uncalibrated' , 'Bias_D5BFEED_uncalibrated' , 'Bias_D5PREAMP_uncalibrated' , 'Bias_D5TDR_uncalibrated' ,
                                     'Bias_D5ALLV_uncalibrated' , 'Bias_D5ALLI_uncalibrated' , 'Bias_D5DAC8_uncalibrated' , 'Bias_THDAC_uncalibrated' ,
                                     'Bias_THDACHIGH_uncalibrated' , 'Bias_CALDAC_uncalibrated', 'Calibration' , 'I_DVDD_calibrated' , 'I_AVDD_calibrated' ,
                                     'I_PVDD_calibrated' , 'GND_calibrated' , 'VBG_uncalibrated', 'VBG_calibrated' , 'Bias_BOOSTERBASELINE_calibrated' , 'Bias_D5BFEED_calibrated' ,
                                     'Bias_D5PREAMP_calibrated' , 'Bias_D5TDR_calibrated' , 'Bias_D5ALLV_calibrated' , 'Bias_D5ALLI_calibrated' ,
                                     'Bias_D5DAC8_calibrated' , 'Bias_THDAC_calibrated Bias_THDACHIGH_calibrated' , 'Bias_CALDAC_calibrated' , 'Bias_THDAC_GAIN' ,
                                     'Bias_CALDAC_GAIN' , 'Bias_THDAC_OFFS' , 'Bias_CALDAC_OFFS']):
                        self.chipsum['bias'][chipn] = 0
                    else:
                        print("Missing category: "+ str(inst[0]))
                        self.chipsum['others'][chipn] = 0 #empty category
                    tmp.append(0)

                    self.chipsum['all-m'] = np.logical_and(
                            np.logical_and( self.chipsum['bias'], self.chipsum['power']),
                            np.logical_and( self.chipsum['frontend'], self.chipsum['digital']) )

                    self.chipsum['all-m1v0'] = np.logical_and(
                            self.chipsum['all-m'], self.chipsum['memory_1V2'])

                    self.chipsum['all'] = np.logical_and(
                            self.chipsum['all-m1v0'], self.chipsum['memory_1V0'])
                chipn += 1

            self.results[ inst[0] ] = tmp
            cnt += 1
        fy = open(self.folder+"/"+wafername+"/yield.csv", 'w')
        fg = open(self.folder+"/"+wafername+"/PassFail_Summary.csv", 'w')
        fg.write("N, ID,")
        for cs in self.chipsum:
            fy.write("{:s}, {:7.3f}, \n".format(cs, 100.0*sum(self.chipsum[cs])/90.0 ))
            fg.write("{:s}, ".format( cs ))
        fy.close()
        fg.write(", PASS/FAIL")
        for chip in range(len(self.chipsum['all'])):
            fg.write("\n{:d}, ".format(chip+1))
            chipiamtec = self.remap_chip_number_according_aimtec(chip+1)
            fg.write("{:s}, ".format(chipiamtec))
            for cs in self.chipsum:
                fg.write("{:d}, ".format( int(self.chipsum[cs][chip])) )
            fg.write(", {:d}, ".format( int(self.chipsum['all'][chip])) )
            try:
                self.summarylog.write("\n{:s}, {:d}, {:s}, {:d}, ".format(wafername, (chip+1), chipiamtec,  int(self.chipsum['all'][chip]) ))
            except:
                pass
        fg.write("\n , , ")
        for cs in self.chipsum:
            fg.write("{:7.3f}, ".format(100.0*sum(self.chipsum[cs])/90.0 ))
        fg.write(", {:7.3f}, ".format(100.0*sum(self.chipsum['all'])/90.0 ))
        fg.close()

        return True
        # self = analyze_all_wafers(LogSuffix='', plot=False)

    def plot_stats(self, wafer = 'Wafer_W4'):
        #self.import_data(wafer, verboselevel=0)
        self.plot_wafer_scale(
            property='I_DVDD_calibrated', unit=r'mA', minv=20, maxv=40, reverse=1, show = 0)
        self.plot_data(
            dlist=['I_DVDD_calibrated','I_AVDD_calibrated','I_PVDD_calibrated'],
            unit = 'mA', minv=15, maxv=60, npoints=10, reverse=0, show=0)
        self.plot_wafer_scale(
            property='noise_mean_trim', unit=r'${ThDAC_{LSB}}$', minv=1.0, maxv=2.5, reverse=1, show = 0)
        self.plot_wafer_scale(
            property='noise_mean_test', unit=r'${ThDAC_{LSB}}$', minv=1.0, maxv=2.5, reverse=1, show = 0)
        self.plot_data(
            dlist=['noise_mean_trim',  'noise_mean_test'],
            unit = r'${ThDAC_{LSB}}$', minv=0, maxv=1.8, npoints=9, reverse=0, show=0,
            datalabels = [r'Average FE noise for 2.0 fC input charge', r'Average FE noise for 0.8 fC input charge'])
        self.plot_data(
            dlist=['threshold_std_init', 'threshold_std_trim',  'threshold_std_test'] ,
            unit = r'${ThDAC_{LSB}}$', minv=0, maxv=5.0, npoints=11, reverse=0, show=0,
            datalabels = [r'$\sigma_{Th}$ - not calibrated', r'$\sigma_{Th}$ - trim at 2 fC - meas at 2 fC', r'$\sigma_{Th}$ - trim at 2.0 fC - meas at 0.8 fC'])
        self.plot_wafer_scale(
            property='threshold_std_trim', unit=r'percent', minv=0, maxv=2, reverse=1, show = 0)
        self.plot_data(
            dlist=['Bias_THDAC_GAIN'] ,
            unit = r'$mV/\overline{ThDAC_{LSB}}$', minv=-2.5, maxv=-1.5, npoints=11, reverse=0, show=0,
            datalabels = [r'$\overline{G_{THDAC}}$'])
        self.plot_data(
            dlist=['fe_gain_mean' ] ,
            unit = r'$mV/fC$', minv=40, maxv=70, npoints=10, reverse=0, show=0,
            datalabels = [r'$\overline{G_{FE}}$'])
        self.plot_wafer_scale(
            property='ClusterData_DigitalPulses', unit=r'percent', minv=0, maxv=100, reverse=0, show = 0)
        self.plot_data(
            dlist=['ClusterData_DigitalPulses'],
            unit = 'Fraction of passed tests', minv=0, maxv=100, npoints=11, reverse=0, show=0)
        self.plot_data(
            dlist=['Memory1_1200V' , 'Memory2_1200V', 'Memory1_1050V' , 'Memory2_1050V' ],
            unit = 'Fraction of passed tests', minv=0, maxv=110, npoints=12, reverse=0, show=0, dimension=[10,7],
            datalabels = ['1.2 V Memory L1' , '1.2 V Memory HIP', '1.0 V Memory L1' , '1.0 V Memory HIP'])
        self.plot_wafer_scale(
            property='Memory1_1200V', unit=r'percent', minv=0, maxv=100, reverse=0, show = 0)
        self.plot_wafer_scale(
            property='Memory1_1050V', unit=r'percent', minv=0, maxv=100, reverse=0, show = 0)
        self.plot_wafer_scale(
            property='Memory2_1200V', unit=r'percent', minv=0, maxv=100, reverse=0, show = 0)
        self.plot_wafer_scale(
            property='Memory2_1050V', unit=r'percent', minv=0, maxv=100, reverse=0, show = 0)

    def plot_wafer_pass_fail(self, mode = 'all-m', unit=''):
        #self.results = np.array(np.random.poisson(3, 90))
        wpt = waferplot()
        wpt.plot(self.chipsum[mode], unit)

    def plot_wafer_scale(self, property = 'L1_data', unit='Percent', minv='min', maxv='max', reverse=0, show = 1):
        wpt = waferplot()
        wpt.plot_wafer(self.measured[property], unit, minv, maxv, reverse)
        fpl = self.folder + '/Plots/' + self.wafer + '__wafermap__' + property + '.png'
        plt.savefig(fpl, bbox_inches="tight");
        print("->  Plot saved in %s" % (fpl))
        if(show):
            plt.show()

    def remap_chip_number_according_aimtec(self, idi):
        if   (idi <= 3): ido = str(idi)
        elif (idi == 4): ido = 'A'
        elif (idi == 5): ido = 'B'
        elif (idi == 6): ido = 'C'
        elif (idi <=13): ido = str(idi-3)
        elif (idi <=23): ido = str(idi-2)
        elif (idi ==24): ido = 'D'
        elif (idi ==25): ido = 'E'
        elif (idi <=36): ido = str(idi-4)
        elif (idi <=47): ido = str(idi-3)
        elif (idi ==48): ido = 'F'
        elif (idi ==49): ido = 'G'
        elif (idi <=60): ido = str(idi-5)
        elif (idi <=71): ido = str(idi-4)
        elif (idi ==72): ido = 'H'
        elif (idi <=81): ido = str(idi-5)
        elif (idi <=90): ido = str(idi-3)
        return ido

    def plot_data(self, dlist=['I_DVDD_calibrated','I_AVDD_calibrated','I_PVDD_calibrated'], unit = 'mA', minv='0', maxv='max', npoints=9, reverse=0, datalabels='auto', show=1, dimension=[10,10]):
        fig = plt.figure(figsize=(dimension[0],dimension[1]))
        ax = fig.add_subplot(1, 1, 1)
        plt.xticks(range(0, len(self.measured['I_DVDD_reset'])+1, 5), fontsize=16)
        plt.ylabel(unit, fontsize=16)
        plt.xlabel('Chip', fontsize=16)
        color=iter(sns.color_palette('Set1'))
        minval = np.inf; maxval = -np.inf; cnt = 0;
        for d in dlist:
            c = next(color)
            data = self.measured[d]
            if(isinstance(datalabels, list)):  lb = datalabels[cnt]
            else:  lb = d
            plt.plot(data, 'o', color=c, label=lb)
            if(isinstance(minv, str)): minval = np.min([np.min(data), minval])
            else: minval = minv
            if(isinstance(maxv, str)): maxval = np.max([np.max(data), maxval])
            else: maxval = maxv
            cnt += 1
        plt.ylim(minval, maxval)
        plt.yticks(np.linspace(minval, maxval, npoints, endpoint=True), fontsize=16)
        plt.legend(loc='best', fontsize = 16)
        fpl = self.folder + '/Plots/' + self.wafer + '__' + '__'.join(map(str, dlist)) + '.png'
        plt.savefig(fpl, bbox_inches="tight");
        print("->  Plot saved in %s" % (fpl))
        if(show):
            plt.show()

    def analyze_all_wafers(self, LogSuffix='', plot=False, verboselevel=0):
        fy = open(self.folder+"/yield"+LogSuffix+".csv", 'w')
        self.summarylog = open(self.folder+"/PassFail_Summary"+LogSuffix+".csv", 'w')
        self.summarylog.write("\n{:s}, {:s}, {:s}, {:s}, ".format("WAFER", "N", "Chip ID", "Pass/Fail"))
        first = True
        cntw = 0
        cyield = {}
        for wp in os.listdir(self.folder):
            rt = self.import_data(wp, verboselevel=verboselevel)
            if(rt):
                cntw += 1
                print("Running chip " + wp)
                if(first):
                    fy.write("Wafer, ")
                    for cs in self.chipsum:
                        fy.write("{:s}, ".format(cs))
                        cyield[cs] = 0
                    first = False
                fy.write(" \n{:s}, ".format(wp))
                for cs in self.chipsum:
                    fy.write("{:7.3f}, ".format(100.0*sum(self.chipsum[cs])/90.0 ))
                    cyield[cs] += sum(100.0*self.chipsum[cs]/90.0)
                if(plot):
                    self.plot_stats()

        fy.write(" \n{:s}, ".format('TOTAL'))
        for cs in self.chipsum:
            fy.write("{:7.3f}, ".format(cyield[cs]/np.float(cntw)))
        fy.close()
        self.summarylog.close()

def analyze_all_wafers(LogSuffix='', plot=False, verboselevel=1):
    sa = ssa_wp_analyze()
    sa.analyze_all_wafers(LogSuffix=LogSuffix, plot=plot, verboselevel=verboselevel)
    return sa

#self = analyze_all_wafers(LogSuffix='_prova3', plot=False)

#analyze_all_wafers()
#sa = ssa_wp_analyze()
#wp = 'Wafer_N2XM21_11B5'
#rt = sa.import_data(wp, verboselevel=0)
#sa.chipsum

#   sa = ssa_wp_analyze()
#   sa.import_data("Wafer_N2XM21_11B5")
#sa = ssa_wp_analyze() # Create object
#sa.plot_stats('Wafer_W4') # Plot main set of statistics about the selected wafer


#sa.plot_wafer_scale('I_DVDD_calibrated', 'mA', 'min', 'max', reverse=1)
