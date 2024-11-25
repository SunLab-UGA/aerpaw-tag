# aerpaw-tag
Project files for a non-canonical aerpaw deployment to power/read wilot tags and manage the aerpaw aerial drone

# The drone will fly according to the plan show below   
<img src="images/AERPAW_TAG_FLIGHTPLAN_whitebg.png" alt="Flightplan Diagram" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>

# A system diagram is given below   
<img src="images/AERPAW_TAG_DIAGRAM_whitebg.png" alt="System Diagram" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>

# Phone payload loading instructions   
Both the USB-C of the phone and the power for the buck converter should be on the same side.   
Correct installation prevents erroneous phone button pressing during flight.   
<img src="images/phone_install.png" alt="Physical Phone Payload Install" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>

# Phone gateway-bridge setup
Login with the provided credentials. The credentials are kept within the Google Keep app.  
<img src="images/photos/Screenshot_20241017-125702.png" alt="signin" width="300" style="background:white;padding:10px;border-radius:5px;">
  <div style="page-break-after: always"></div>
   
(if required) Use the gmail app to fufill two-factor authentication.  
<img src="images/photos/Screenshot_20241017-131809.png" alt="2factor" width="300" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>

Ensure the gateway mode is turned on.  
<img src="images/photos/Screenshot_20241017-125756.png" alt="gateway mode activation" width="300" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>   

# Check connectivity via MQTT
You may check if the setup is correct by viewing the data via MQTT.  
Here is a simple webclient setup.   
https://www.hivemq.com/demos/websocket-client/   
Click ```Connect``` (no need to change anything)  
<img src="images/screenshots/Screenshot 2024-10-17 184119.png" alt="MQTT" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div> 

Once connected, click ```Add New Topic Subscription```  
<img src="images/screenshots/Screenshot 2024-10-17 184131.png" alt="MQTT" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>  

Change the topic to ```sunlab``` and click ```Subscribe```   
<img src="images/screenshots/Screenshot 2024-10-17 184144.png" alt="MQTT" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>

The first message show, but check to see if it is just a "retained" message.   
A retained mesage does not show current connectivity.   
You should see messages about activity and temperature when the tags are present.  
(eg. The message shown below is an activity message stating that the tag is no longer actively being seen)  
<img src="images/screenshots/Screenshot 2024-10-17 184201.png" alt="MQTT" width="750" style="background:white;padding:10px;border-radius:5px;">
   <div style="page-break-after: always"></div>