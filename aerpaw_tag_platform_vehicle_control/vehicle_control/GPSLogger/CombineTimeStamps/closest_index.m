function indx=closest_index(t_meas,t_gps)
V = t_meas;
N = t_gps;

A = repmat(N,[1 length(V)]);
[minValue,indx] = min(abs(A-V'));