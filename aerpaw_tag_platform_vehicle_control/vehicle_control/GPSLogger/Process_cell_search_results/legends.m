figure(1)
legend('exp1','exp2')
title('Based on GPS timestamps')
print -djpg altitutdevstime_GPS.jpg

figure(2)
legend('exp1','exp2')
title('Based on measurement timestamps')
print -djpg altitutdevstime_measurement.jpg

figure(3)
legend('exp1','exp2')
print -djpg powervsdistance.jpg


figure(5)
legend('exp1','exp2')
print -djpg powervstime.jpg

figure(7)
legend('exp1','exp2')
print -djpg distancevstime.jpg


figure(4)
%print -djpg scatter3D.jpg
%print -djpg scatter3D_holdon.jpg
%print -djpg scatter3D_holdon_zoom.jpg
print -djpg scatter3D.jpg
