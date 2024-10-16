clear all
%get gps coordinates with time stamps
fname_gps='GPS_DATA_2021-06-01_16_33_24.csv';
[timestamp_gps GPSx GPSy GPSz] = process_csv_GPS(fname_gps);
%get power measurements woth time stamps
fname_srs='SRS_Cell_search_data.csv';
[timestamp_srs measurement] = process_csv_srs_cellsearch(fname_srs);

% find the closest time stamp index in gps time stamp 
%corresponding to each measurement timestamp
indx=closest_index(timestamp_srs,timestamp_gps);

%Get the coordinates for each measurement
mX=GPSx(indx);
mY=GPSy(indx);
mZ=GPSz(indx);
%get relative measurement time
mSeconds=timestamp_srs-timestamp_srs(1);

%print results
[mX mY mZ measurement mSeconds]

