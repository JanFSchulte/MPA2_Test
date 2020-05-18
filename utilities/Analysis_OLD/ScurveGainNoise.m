function [N, IdxIssue, THDAC_mean, THDAC_sigma] = ScurveGainNoise(filename, Npixel, Hits, Plot)

N = csvread(filename,2,2);

%Npixel = 1920; %length(N(:,1));

MAX = NaN(Npixel,1);
IND = NaN(Npixel,1);

THDAC_mean = NaN(Npixel,1);
THDAC_sigma = NaN(Npixel,1);

%Hits=300;
Npoints = 21; %!!odd

k = 1;


for n = 1:Npixel
    PixelResponse = N(n,:);
    [MAX(n),IND(n)] = max(PixelResponse);
    %     if Plot
    %         hold on;
    %         plot(PixelResponse);
    %     end
    
    if all (PixelResponse<=(Hits)) || any(PixelResponse(250:end)>Hits)  %(IND(n) < 2)
        IdxIssue(:,k) = [n; 0; 0];
        k = k+1;
    else
        IdxIssue(:,k) = [0; 0; 0];
        FindTrans = PixelResponse;
        FindTrans(FindTrans<(Hits/2))  = 0;
        FindTrans(FindTrans>=(Hits/2)) = Hits;
        TransitionIndex = find((diff(FindTrans)~=0));
        Idx0 = TransitionIndex(end);
        X = (Idx0-(Npoints-1)/2):1:(Idx0+(Npoints-1)/2);
        Y = PixelResponse(X)/Hits;
        
        
        sigma = 1;
        exitloop = false;
        while ~exitloop
            
            ft=fittype('1-(1/2)*(1+erf((X-mean)/(sigma*sqrt(2))))', 'independent', 'X', 'dependent', 'Y' );
            startPoints = [Idx0 sigma];
            fitresult=fit(X',Y',ft, 'Start', startPoints);
            if fitresult.sigma<0.2 && sigma<3
                sigma = sigma+0.5;
            else
                exitloop = true;
            end
        end
        
        THDAC_mean(n,1)  = fitresult.mean;
        THDAC_sigma(n,1) = fitresult.sigma;
        
        if Plot
            plot(X,Y,'o');hold on;plot(fitresult,X,Y);
        end
        
    end
end
