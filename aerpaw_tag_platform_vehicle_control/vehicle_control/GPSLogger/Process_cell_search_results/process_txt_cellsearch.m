function [timestamp measurement,timestamp_for_csv] = process_txt_ping(fname)
%x = textread (fname,'%s','delimiter',',');
x = textread (fname,'%s', 'delimiter', '\n');

%txt file typical data format
%[2021-07-16 13:01:15.419317] 64 bytes from 172.16.0.1: icmp_seq=1 ttl=64 time=43.5 ms


%Every 15th element is a time stamp
%15 elements per line
N=length(x);
cnt=0;
for i=1:N
  stri=cell2mat(x(i));
  if length(findstr(stri,'Found CELL MHz'))==1
  %stri
  cnt=cnt+1;
  str_ts= stri(strfind(stri,'2021-')+(0:22));
  str_ts= [str_ts(1:19) '.' str_ts(21:end)];
  timestamp_for_csv(cnt,:)=str_ts;
  t(cnt,1)=strptime(str_ts(1:end-4),"%Y-%m-%d %H:%M:%S");
  %seconds since 1970
  timestamp(cnt,1)=mktime(t(cnt,1));
  %add the milliseconds separately
  %i
  timestamp(cnt,1)=timestamp(cnt,1)+str2num(['0.' str_ts(end-2:end)]);  
  measurement(cnt,1)=str2num(stri(strfind(stri,'PSS power dBm, ')+(15:18)));
  endif
  
end
%cnt=0;
%measurement=0;
%for i=12:15:N
%  cnt=cnt+1;
%  measurement(cnt,1)=str2num(cell2mat(x(i)));
%end



 