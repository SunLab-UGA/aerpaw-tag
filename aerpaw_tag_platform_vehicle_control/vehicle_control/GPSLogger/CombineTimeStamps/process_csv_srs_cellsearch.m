function [timestamp measurement] = process_csv_srs_cellsearch(fname)
x = textread (fname,'%s','delimiter',',');
%srs cell_search csv file typical data format
%Found CELL MHz, 3579.9,  EARFCN, 7399, PHYID, 1, PRB, 50,  ports, 1, PSS power dBm, -30.1,  PSR, 2.3, 2021-06-26 22:09:40:229


%Every 15th element is a time stamp
%15 elements per line
N=length(x);
cnt=0;
for i=15:15:N
  cnt=cnt+1;
  t(cnt,1)=strptime(cell2mat(x(i))(1:end-4),"%Y-%m-%d %H:%M:%S");
  %seconds since 1970
  timestamp(cnt,1)=mktime(t(cnt,1));
  %add the milliseconds separately
  timestamp(cnt,1)=timestamp(cnt,1)+str2num(['0.' cell2mat(x(i))(end-2:end)]);
end
cnt=0;
for i=12:15:N
  cnt=cnt+1;
  measurement(cnt,1)=str2num(cell2mat(x(i)));
end



 