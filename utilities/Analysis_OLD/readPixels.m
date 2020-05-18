function [M,MAX,IND,IdxProblem] = readPixels(filename)
%UNTITLED11 Summary of this function goes here
%   Detailed explanation goes here

M = csvread(filename,2,2);

Npixel = length(M(:,1));
Ncurve = length(M(1,:));

MAX = NaN(Npixel,1);
IND = NaN(Npixel,1);

LimSup = 1000;
Npoints = 10;
F = figure;
k = 1;

LEGEND = cell(Npixel,1);

for n = 1:Npixel
    PixelResponse = M(n,:);
    [MAX(n),IND(n)] = max(PixelResponse);
    FindTrans = PixelResponse;
    FindTrans(FindTrans<(LimSup/2))  = 0;
    FindTrans(FindTrans>=(LimSup/2)) = LimSup;
    
    TransitionIndex = find((diff(FindTrans)~=0));
    if ~isempty(TransitionIndex)
        if  TransitionIndex + Npoints <= Ncurve
            TransitionIndex = TransitionIndex(end);
            PixelResponseTrans = PixelResponse((TransitionIndex-Npoints):(TransitionIndex+Npoints));
            plot(PixelResponseTrans,'-o');
            hold on
        else
            IdxProblem(k) = n;
            k = k+1;
        end
    else
        IdxProblem(k) = n;
        k = k+1;
    end
    
            LEGEND{n} = num2str(n);
    
end

legend(LEGEND);


end

