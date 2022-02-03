close all
clear

CHIP = 'MPA';
if strcmp(CHIP,'MPA')       
    Npixel = 1920;
else
    Npixel = 120;
end
N_CHIP = 3;
N_CAL = 20;
N_ROWPERTIME = 4;
trimming = 'noise';  %'cal'

Files = dir(['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ... 
             '\Noise_curves_trimming\' num2str(N_ROWPERTIME) 'rowPerTime_cal' num2str(N_CAL) '\' ...
             'Chip' num2str(N_CHIP) '_' trimming '_scurve_trim*.csv']);

filesave_mean = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                 '\Noise_curves_trimming\' num2str(N_ROWPERTIME) 'rowPerTime_cal' num2str(N_CAL) '\' ...
                 'Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_' num2str(N_CAL) '_mean.png'];
        
filesave_mean_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                      '\Noise_curves_trimming\' num2str(N_ROWPERTIME) 'rowPerTime_cal' num2str(N_CAL) '\' ...
                      'Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_' num2str(N_CAL) '_mean_hist.png'];
        
filesave_sigma = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                  '\Noise_curves_trimming\' num2str(N_ROWPERTIME) 'rowPerTime_cal' num2str(N_CAL) '\' ....
                  'Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_' num2str(N_CAL) '_sigma.png'];
        
filesave_sigma_hist = ['C:\Users\sscarfi\' CHIP '\Chip' num2str(N_CHIP) ...
                       '\Noise_curves_trimming\' num2str(N_ROWPERTIME) 'rowPerTime_cal' num2str(N_CAL) '\' ...
                       'Chip' num2str(N_CHIP) '_' trimming '_scurve_cal_' num2str(N_CAL) '_sigma_hist.png'];


N_Files = numel(Files);

N               = cell(1,N_Files);
IdxIssue        = cell(1,N_Files);
THDAC_mean      = cell(1,N_Files);
THDAC_sigma     = cell(1,N_Files);
CoeffMeanDist 	= cell(1,N_Files);
CoeffSigmaDist  = cell(1,N_Files);

Fmean       = figure;
Fmean_hist  = figure;
Fsigma      = figure; 
Fsigma_hist = figure;

for n = 1:N_Files
    filename = [Files(n).folder '\' Files(n).name];
    %[N{n}, IdxIssue{n}, THDAC_mean{n}, THDAC_sigma{n}, CoeffMeanDist{n}, CoeffSigmaDist{n}] = NoiseParametersPixels(filename, Npixel, false);
    [N{n}, IdxIssue{n}, THDAC_mean{n}, THDAC_sigma{n}] = NoiseParametersPixels(filename, Npixel, false);
    
    figure(Fmean);
    plot(THDAC_mean{n});
    if strcmp(CHIP,'MPA')       
        xlabel('Pixel');
        ylabel('mean THDAC[LSB]');
    else
        xlabel('Strip');
        ylabel('mean THDAC[LSB]');
    end
    hold on;
    
    figure(Fmean_hist);
    [~,p] = histfit2(THDAC_mean{n},round(sqrt(Npixel-length(IdxIssue{n}(1,:))));
    if strcmp(CHIP,'MPA')      
        xlabel('mean THDAC[LSB]');
        ylabel('Number of Pixels');
    else
        xlabel('mean THDAC[LSB]');
        ylabel('Number of Strips');
    end
    CoeffMeanDist{n} = [p.mean p.sigma];
    hold on;
    
    figure(Fsigma);
    plot(THDAC_sigma{n});
    if strcmp(CHIP,'MPA')       
        xlabel('Pixel');
        ylabel('sigma THDAC[LSB]');
    else
        xlabel('Strip');
        ylabel('sigma THDAC[LSB]');
    end
    hold on;

    figure(Fsigma_hist);
    [~,p] = histfit2(THDAC_sigma{n},round(sqrt(Npixel-length(IdxIssue{n}(1,:))));
    if strcmp(CHIP,'MPA')   
        xlabel('sigma THDAC[LSB]');
        ylabel('Number of Pixels');
    else
        xlabel('sigma THDAC[LSB]');
        ylabel('Number of Strips');
    end
    CoeffSigmaDist{n} = [p.mean p.sigma];
    hold on;
end

saveas(Fmean,filesave_mean);
saveas(Fmean_hist,filesave_mean_hist);
saveas(Fsigma,filesave_sigma);
saveas(Fsigma_hist,filesave_sigma_hist);


