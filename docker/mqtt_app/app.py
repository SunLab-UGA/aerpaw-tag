# used to connect to a mqtt broker and subscribe to a topic
# the data is then stored in an influxdb database

import sys
import logging
import datetime
# enable logging to stdout (the container will keep the log files)
logging.basicConfig(stream=sys.stdout, level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.info("Starting the application")

from lib import MQTT, INFLUX
logging.info("Libraries imported")

# ============================================================================= CONSTANTS 
known_locations = {"32f85872-4293-4aa4-b690-09a933b84759":"sunlab"}
known_zones = {"1c07881a-bb1b-409a-b0da-4c464a8772b3":"Lab1",
               "b1e0b0a2-0b0a-4b0b-8b0a-0b0a0b0a0b0a":"Lab1",
               "cb662456-0e18-46fb-8d72-16173909fe93":"Lab2"}

logging.info(f"Known locations ({len(known_locations)}) and zones ({len(known_zones)}) set")
logging.info("Creating the InfluxDB and MQTT clients")

# ============================================================================= FUNCTIONS

def write_file_log(msg, file_path='mqtt_raw_log.txt'):
    '''
    write the message to the file as a plain text log
    '''
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"{time}|{msg}\n"
    with open(file_path, "a") as f:
        f.write(msg)

# ============================================================================= INITIALIZE

# create the influxdb client
influx = INFLUX(known_locations=known_locations, known_zones=known_zones)
logging.info("InfluxDB client created")
if influx.check():
    logging.info("InfluxDB running")
else:
    logging.error("InfluxDB not running")
    exit(1) # the container will restart, and we will try again

if influx.connect():
    logging.info("InfluxDB client connected")
else:
    logging.error("InfluxDB client failed to connect")
    exit(1)

# more permission checking...
influx.check_permissions()
influx.check_bucket_health()

# logging.info("logging connection status to InfluxDB") # also checks if writing is successful
# influx.simple_write() # will raise an exception if the write fails

logging.info("Performing simple_query to InfluxDB")
if influx.simple_write_and_verify():
    logging.info("InfluxDB simple_query successful")
else:
    logging.error("InfluxDB simple_query failed")
    exit(1)

# create the mqtt client
mqtt = MQTT()
logging.info("MQTT client created")
mqtt.connect_mqtt()
logging.info("MQTT client connected")

def store_influxdb(msg):
    '''
    callback function to store the message in the influxdb database
    if the message is retained, it is not stored
    '''
    line = msg.payload.decode()
    logging.info(f"Message received: {line}")
    if msg.retain: 
        logging.info("Previous message was marked 'retained', and not stored")
        return
    write_file_log(msg=line)    
    # else parse and store the message
    influx.write(line, measurement_name="tag_event")

# subscribe and add the callback
mqtt.subscribe(store_influxdb) # loops forever here, nothing after this line will run
logging.info("Error in Mqtt loop? How did we get here?")
