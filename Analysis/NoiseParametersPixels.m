function [N, THDAC_mean, THDAC_sigma, IdxIssue, CoeffMeanDist, CoeffSigmaDist] = NoiseParametersPixels(filename, Npixel, Plot)
N = csvread(filename,2,2);

%Npixel = 1920; %length(N(:,1));

MAX = NaN(Npixel,1);
IND = NaN(Npixel,1);

THDAC_mean = NaN(Npixel,1);
THDAC_sigma = NaN(Npixel,1);
x = (1:256);

LimSup=100;
k = 1;

for n = 1:Npixel
    PixelResponse = N(n,:);
    [MAX(n),IND(n)] = max(PixelResponse);
%     if Plot
%         figure;
%         hold on;
%         plot(PixelResponse);
%     end
    
    if all (PixelResponse<=(LimSup)) || (IND(n) < 2)
        IdxIssue(:,k) = [n; 0; 0];
        k = k+1;
    else
        f = fit (x', PixelResponse', 'gauss1');
        MyCoeffs = coeffvalues(f);
        THDAC_mean(n)= MyCoeffs(2);
        THDAC_sigma(n) = MyCoeffs(3);
%         if Plot
%             if THDAC_sigma(n)<1
%                 figure;
%                 hold on;
%                 plot(PixelResponse);
%             end
%         end
        if (THDAC_mean(n) >= 256) || (THDAC_sigma(n) >= 50) 
            IdxIssue(:,k) = [n; THDAC_mean(n); THDAC_sigma(n)];
            k = k+1;
            THDAC_mean(n) = NaN;
            THDAC_sigma(n) = NaN;
        end
    end
%     if Plot
%         plot(f, x, PixelResponse);
%         xlabel('THDAC[LSB]:');
%         ylabel('Counts');
%     end
end

if Plot
    figure;
    plot(THDAC_mean);
    xlabel('Pixel');
    ylabel('mean THDAC[LSB]');

    % figure;
    % histogram(THDAC_mean)
    % xlabel('THDAC[LSB]');
    % ylabel('Number of Pixels');

    figure;
    [~,p] = histfit2(THDAC_mean,round(sqrt(Npixel)));
    xlabel('mean THDAC[LSB]');
    ylabel('Number of Pixels');
    CoeffMeanDist = [p.mean p.sigma];

    figure;
    plot(THDAC_sigma);
    xlabel('Pixel');
    ylabel('sigma THDAC[LSB]');

    % figure;
    % histogram(THDAC_sigma)
    % xlabel('sigma THDAC[LSB]');
    % ylabel('Number of Pixels');

    figure;
    [~,p] = histfit2(THDAC_sigma,round(sqrt(Npixel)));
    xlabel('sigma THDAC[LSB]');
    ylabel('Number of Pixels');
    CoeffSigmaDist = [p.mean p.sigma];
end