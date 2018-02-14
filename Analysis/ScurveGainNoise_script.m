close all
clear

CHIP = 'SSA'; 
N_CHIP = 3;
trimming = 'cal';  %'cal' 'noise'

if strcmp(CHIP,'MPA')    
    Files = dir(['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ... 
                 '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_trim__cal_*.csv']);
    filesave_mean       = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                            '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_mean.png'];
                          
    filesave_gain_hist  = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                            '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_gain_hist.png'];

    filesave_offset_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                            '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_offset_hist.png'];

    filesave_sigma      = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                            '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_sigma.png'];

    filesave_sigma_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                           '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_sigma_hist.png'];
else          
    Files = dir(['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ... 
                 '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_trim0__cal_*.csv']);

    filesave_mean       = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                           '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_cal_mean.png'];
                          
    filesave_gain_hist  = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                           '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_cal_gain_hist.png'];

    filesave_offset_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                            '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_cal_offset_hist.png'];

    filesave_sigma      = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                           '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_cal_sigma.png'];

    filesave_sigma_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                           '\Scurve_gain_noise\Chip' num2str(N_CHIP) '_scurve_cal_sigma_hist.png'];
end

N_Files = numel(Files);

N               = cell(1,N_Files);
IdxIssue        = cell(1,N_Files);
THDAC_mean      = cell(1,N_Files);
THDAC_sigma 	= cell(1,N_Files);
CALDAC          = cell(1,N_Files);
CoeffGainDist 	= cell(1,N_Files);
CoeffOffsetDist = cell(1,N_Files);
CoeffSigmaDist  = cell(1,N_Files);

if strcmp(CHIP,'MPA')    
    Npixel          = 1920;
    Hits            = 300;
    CALDAC_values   = [10:10:30]*9/256; %fC
    K               = 370/256; %mV
else 
    Npixel          = 119;
    Hits            = 1000;
    CALDAC_values   = [50:10:90]*11/256; %fC
    K               = (660-146)/256; %mV
end

Fmean        = figure;
Fgain_hist   = figure;
Foffset_hist = figure;
Fsigma       = figure;
Fsigma_hist  = figure;

for n = 1:N_Files
    filename = [Files(n).folder '\' Files(n).name];
    %[N{n}, IdxIssue{n},THDAC_mean{n},THDAC_sigma{n}] = ScurveGainNoise(filename,false);
    [N{n}, IdxIssue{n}, THDAC_mean{n}, THDAC_sigma{n}] = ScurveGainNoise(filename, Npixel, Hits, false);
    
    if strcmp(CHIP,'MPA') 
        THDAC_mean{n} = THDAC_mean{n}*K; 
    else
        THDAC_mean{n} = 146 + THDAC_mean{n}*K;
    end
    CALDAC{1,n} = CALDAC_values(n)*ones(1,length(THDAC_mean{n}));
    
    figure(Fmean);
    plot(CALDAC{1,n}(:),THDAC_mean{n}(:),'o');
    xlabel('CALDAC[fC]');
    ylabel('mean THDAC[LSB]');
    hold on;
    
    figure(Fsigma);
    plot(CALDAC{1,n}(:),THDAC_sigma{n}(:),'o');  
    xlabel('CALDAC[fC]');
    ylabel('sigma THDAC[LSB]');
    hold on;
end

Npixel = length(THDAC_mean{1});

gain = NaN(1,Npixel);
offset = NaN(1,Npixel);
  
for n = 1:Npixel
    if strcmp(CHIP,'MPA')   
        p = polyfit(CALDAC_values,[THDAC_mean{1}(n) THDAC_mean{2}(n) THDAC_mean{3}(n)],1);
    else
        p = polyfit(CALDAC_values,[THDAC_mean{1}(n) THDAC_mean{2}(n) THDAC_mean{3}(n) THDAC_mean{4}(n) THDAC_mean{5}(n)],1);
    end
    gain(n) = p(1);
    offset(n) = p(2);
end

figure(Fgain_hist);
[~,p] = histfit2(gain,round(sqrt(Npixel)));
if strcmp(CHIP,'MPA')     
    xlabel('Gain[mV/fC]');
    ylabel('Number of Pixels');
else
    xlabel('Gain[mV/fC]');
    ylabel('Number of Strips');
end
CoeffGainDist = [p.mean p.sigma];
    
figure(Foffset_hist);
[~,p] = histfit2(offset,round(sqrt(Npixel)));
if strcmp(CHIP,'MPA')     
    xlabel('Offset[mV]');
    ylabel('Number of Pixels');
else
    xlabel('Offset[mV]');
    ylabel('Number of Strips');
end
CoeffOffsetDist = [p.mean p.sigma]; 

lines = NaN(1,N_Files);
for n = 1:N_Files
    figure(Fsigma_hist);
    [~,p] = histfit2(THDAC_sigma{n}(:),round(sqrt(Npixel-length(IdxIssue{n}(1,:)))));
    if strcmp(CHIP,'MPA')    
        xlabel('sigma THDAC[LSB]');
        ylabel('Number of Pixels');
    else
        xlabel('sigma THDAC[LSB]');
        ylabel('Number of Strips');
    end
    Fsigma_hist.Children(1).Children(1).Color = circshift([1 0 0],n-1);
    lines(n) = Fsigma_hist.Children(1).Children(1);
    CoeffSigmaDist{n} = [p.mean p.sigma]; 
    hold on;
end
legend(lines,{'a','b','c'});

saveas(Fmean, filesave_mean);
saveas(Fgain_hist, filesave_gain_hist);
saveas(Foffset_hist, filesave_offset_hist);

saveas(Fsigma, filesave_sigma);
saveas(Fsigma_hist, filesave_sigma_hist);
