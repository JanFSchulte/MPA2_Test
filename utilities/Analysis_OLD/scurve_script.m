clear; 
close all;

filename = 'C:\Users\sscarfi\MPA\Chip3\Chip3_cal_scurve_trim__cal_10.csv';
%filename = 'C:\Users\sscarfi\MPA\Chip3\Scurve_gain_noise\Chip3_noise_scurve_trim__cal_30.csv';

M = csvread(filename,2,2);

Plot=1;                   %to display plots
Npixel = 120;             %Npixel = length(M(:,1));
Ncurve = length(M(1,:));
MPArow = 16;              %Number of rows

LimSup = 1000;            %Number of hits
k = 1;                    %Problem Index

%plot all the pixels or single pixel
i=0
if i == 0
  for i = 1:(Npixel*MPArow)
    if Plot==1
      plot(M(i,:))
      hold on
    end
  end
elseif (i > Npixel*MPArow)
  disp('Value exceeds maximum value.')
elseif (i > 0) && (i < Npixel*MPArow)
  for i = 10
    if Plot==1
      hold on
      plot(M(i,:))
    end
  end
end

%find and plot problematic pixels
for i = 1:(Npixel*MPArow)
  PixelResponse = M(i,220:256);
  if any (PixelResponse>=LimSup)
    if Plot==1
      plot(M(i,:))
      hold on;
    end
    IdxProblem(k) = i;
    X = sprintf('Idxproblem = %d', i);
    disp(X)
    k=k+1;
  end
end

for i = 1:(Npixel*MPArow)
  PixelResponse = M(i,:);
  if all (PixelResponse==0)
    if Plot==1
      figure;
      hold on;
      plot(M(i,:))
    end
    IdxProblem(k) = i;
    X = sprintf('Idxproblem = %d', i);
    disp(X)
    k=k+1;
  end
end

for i = 1:(Npixel*MPArow)
  PixelResponse = M(i,:);
  if all (PixelResponse<=(LimSup*0.8))
    if Plot==1
      figure;
      hold on;
      plot(M(i,:))
    end
    IdxProblem(k) = i;
    X = sprintf('Idxproblem = %d', i);
    disp(X)
    k=k+1;
  end
end

%plot all the rows or single rows setting j
j=1
k=0
if k == 0
  for j = 1:MPArow
    for i = 1+(Npixel*(j-1)):Npixel+(Npixel*(j-1))
      if Plot==1
        hold on
        LEGEND = cell(i,1);
        plot(M(i,:))
        LEGEND{i-(Npixel*(j-1))} = num2str(i-(Npixel*(j-1)));
      end
    end
    figure;
    legend(LEGEND);
  end
elseif (j > MPArow)
  disp('Value exceeds maximum value.')
elseif (j > 0) && (j <= MPArow)
  if Plot==1
    LEGEND = cell(Npixel,1);
  end
  for i = 1+(Npixel*(j-1)):Npixel+(Npixel*(j-1))
    if Plot==1
      plot(M(i,:))
      hold on
      LEGEND{i-(Npixel*(j-1))} = num2str(i-(Npixel*(j-1)));
    end
  end
  if Plot==1
    legend(LEGEND);
  end
end


%plot pixels 1,2,119,120 for all the rows
k=0
if k == 0
  for j = 1:MPArow
      %LEGEND = cell(2,1);
      index1 = 1+Npixel*(j-1)
      index2 = 2+Npixel*(j-1)
      index119 = 119+Npixel*(j-1)
      index120 = 120+Npixel*(j-1)
      figure;   hold on
      A1 = plot(M(index1,:),'-o'); M1 = '1';
      A2 = plot(M(index2,:),'-+'); M2 = '2';
      A3 = plot(M(index119,:),'-x'); M3 = '3';
      A4 = plot(M(index120,:),'-d'); M4 = '4';
      legend([A1;A2;A3;A4], [M1;M2;M3;M4]);
  end
elseif (j > MPArow)
  disp('Value exceeds maximum value.')
end
