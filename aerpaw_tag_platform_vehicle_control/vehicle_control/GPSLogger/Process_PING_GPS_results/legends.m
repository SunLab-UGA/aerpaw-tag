figure(1)
legend('Emulation','Testbed')
title('Based on GPS timestamps')
print -djpg altitutdevstime_GPS.jpg

figure(2)
legend('Emulation','Testbed')
title('Based on PING timestamps')
print -djpg altitutdevstime_ping.jpg

figure(3)
legend('Emulation','Testbed')
print -djpg delayvsdistance.jpg


figure(5)
legend('Emulation','Testbed')
print -djpg delayvstime.jpg

figure(7)
legend('Emulation','Testbed')
print -djpg distancevstime.jpg


figure(4)
print -djpg scatter3D.jpg
