%clear all
%close all
%get gps coordinates with time stamps
%folder ='demo' %demo, test1, ..., test 4
%result = 'UE'  % UE or EPC

function N = main(folder,result)
  
fname_gps=[folder '/' 'GPS_DATA.csv'];
[timestamp_gps, GPSx, GPSy, GPSz] = process_csv_GPS(fname_gps);

%get delay measurements with time stamps

fname_ping=[folder '/' 'pingResults' result '.txt'];
%fname_ping='pingResultsEPC.txt';
[timestamp_ping, measurement,timestamp_for_csv,seq ] = process_txt_ping(fname_ping);

seq1=[];
N=max(seq);
for i=1:N
  if  not(any(seq==i))
    seq1=[seq1 ; i];
  endif
endfor

for i=1:length(seq1)
measurement1(i,1)=200;
if seq1(i) < min(seq)
timestamp_ping1(i,1)=timestamp_ping(1);
else
 timestamp_ping1(i,1)=interp1(seq,timestamp_ping,seq1(i) );
endif
num1=timestamp_ping1(i,1);

strtemp=num2str(num1-floor(num1));
while length(strtemp)<8
  strtemp=[strtemp '0'];
end
timestamp_for_csv1(i,:)=[strftime("%Y-%m-%d %H:%M:%S", gmtime(floor(num1)-4*60*60)) strtemp(2:8)];
endfor

seq=[seq;seq1];
timestamp_ping=[timestamp_ping;timestamp_ping1];
success=[ones(size(measurement)) ;zeros(size(measurement1))];
measurement=[measurement;measurement1];

timestamp_for_csv=[timestamp_for_csv;timestamp_for_csv1];


for i=1:length(timestamp_ping)
  i;
  if timestamp_ping(i)<timestamp_gps(1)
    mX(i,1)=GPSx(1);
    mY(i,1)=GPSy(1);
    mZ(i,1)=GPSz(1);
    elseif timestamp_ping(i)>timestamp_gps(end)
    mX(i,1)=GPSx(end);
    mY(i,1)=GPSy(end);
    mZ(i,1)=GPSz(end);
  else
    mX(i,1)=interp1(timestamp_gps,GPSx,timestamp_ping(i));
    mY(i,1)=interp1(timestamp_gps,GPSy,timestamp_ping(i));
    mZ(i,1)=interp1(timestamp_gps,GPSz,timestamp_ping(i));
    
  endif
endfor

  %maxind=max(find(timestamp_ping<timestamp_gps(1)));
  %mX=mX(maxind:end);
  %mY=mY(maxind:end);
  %mZ=mZ(maxind:end);
  %measurement=measurement(maxind:end);
  %timestamp_for_csv=timestamp_for_csv(maxind:end,:);
  %timestamp_ping=timestamp_ping(maxind:end);
  %success=success(maxind:end);
  
  pingindex=find((timestamp_ping<timestamp_gps(end)) + (timestamp_ping>timestamp_gps(1))-1);
  mX=mX(pingindex);
  mY=mY(pingindex);
  mZ=mZ(pingindex);
  measurement=measurement(pingindex);
  timestamp_for_csv=timestamp_for_csv(pingindex,:);
  timestamp_ping=timestamp_ping(pingindex);
  success=success(pingindex);
  
  

figure(1) 
hold on
plot((timestamp_gps-timestamp_gps(1)),GPSz,'x')
xlabel('time (s)')     
ylabel('Altitude (m)')


figure(2) 
hold on
plot((timestamp_ping-timestamp_gps(1)),mZ,'x')
xlabel('time (s)')     
ylabel('Altitude (m)')


##LW1:
##       "Latitude": 35.727451,
##       "Longitude": -78.695974,
       
%
 

 
origin_y=35.727451;
origin_x=-78.695974;

       
for i=1:length(timestamp_ping)
  mdistance(i,1)=sqrt((mX(i)-origin_x)^2 + (mY(i)-origin_y)^2)* 1.113195e5;
endfor
figure(3)
hold on
plot(mdistance,measurement,'x') 
xlabel('distance (m)')     
ylabel('delay (ms)')

figure(7) 
hold on
plot((timestamp_ping-timestamp_gps(1)),mdistance,'x')
xlabel('time (s)')
ylabel('distance(m)')     


figure(5)
hold on
plot((timestamp_ping-timestamp_ping(1)),measurement,'x') 
xlabel('time (s)')     
ylabel('delay (ms)')


%csv file format
%1,2021-07-16 13:02:58.093219,-78.6961094,35.7272784,0.004,-10
%ts=ctime(time());
%csvfilename=[ts(1:end-1), '_EPC_input.csv'];
%csvfilename=strrep(csvfilename,' ','_');
%csvfilename=strrep(csvfilename,':','_');
csvfilename=[folder '/' result '_input.csv'];

if isfile(csvfilename)
 delete(csvfilename)
end

for i=1:length(timestamp_ping)
  a=[num2str(i) ',' timestamp_for_csv(i,:) ',' num2str(mX(i),"%5.7f") ',' num2str(mY(i),"%5.7f") ',' num2str(mZ(i),"%5.7f") ',' num2str(success(i))]; 
   dlmwrite (csvfilename, a, "delimiter", "", "-append");
endfor
figure(4)
%subplot(1,2,2)
hold on
scatter3(mX,mY,mZ,10,measurement)
x0=min(mX);x1=max(mX);y0=min(mY);y1=y0+(x1-x0);
xlim([x0 x1   ]);
ylim([y0 y1]-(y1-y0)/2);
colormap(jet);
colorbar;
caxislim=[0 50];
caxis(caxislim)
xlabel('Longitude')
ylabel('Latitude')
zlabel('Altitude')
zlim([0 60]);
hcb=colorbar;
colorTitleHandle = get(hcb,'Title');
titleString = 'delay (ms)';
set(colorTitleHandle ,'String',titleString);
%title('Emulation')
%title('Testbed')
