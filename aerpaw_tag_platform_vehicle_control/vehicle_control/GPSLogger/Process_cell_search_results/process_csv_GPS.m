function [timestamp GPSx GPSy GPSz] = process_csv_GPS(fname)
x = textread (fname,'%s','delimiter',',');
%GPS csv file typical data format
%1,-78.6740031,35.7717933,11.163,0.522,2021-06-01 16:33:24.646836,3,7

%Every 6th element is a time stamp
%8 elements per line
N=length(x);
cnt=0;
for i=6:8:N
  cnt=cnt+1;
  t(cnt,1)=strptime(cell2mat(x(i))(1:end-7),"%Y-%m-%d %H:%M:%S");
  %seconds since 1970
  timestamp(cnt,1)=mktime(t(cnt));
  %add the milliseconds separately
  timestamp(cnt,1)=timestamp(cnt,1)+str2num(['0.' cell2mat(x(i))(end-5:end)]);
end
cnt=0;
for i=2:8:N
  cnt=cnt+1;
  GPSx(cnt,1)=str2num(cell2mat(x(i)));
  GPSy(cnt,1)=str2num(cell2mat(x(i+1)));
  GPSz(cnt,1)=str2num(cell2mat(x(i+2)));
end