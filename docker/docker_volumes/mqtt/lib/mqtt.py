# class which handles the mqtt connection (subscribe only)

import sys
import os
import random
import time
from paho.mqtt import client as mqtt_client

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class MQTT:
    def __init__(self):
        # pull the environment variables
        self.broker = os.getenv("MQTT_HOST")
        self.port = int(os.getenv("MQTT_PORT"))
        self.topic = os.getenv("MQTT_TOPIC")
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.client = None
        
    
    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.debug(f"Connected to MQTT Broker! {self.broker}")
            else:
                logging.error(f"Failed to connect to {self.broker}, return code {rc}")
                # failed to connect, exit after 5 seconds to allow docker to restart the container and try again
                time.sleep(5)
                exit(1)

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                logging.error(f"Disconnected from MQTT Broker! {self.broker}")
                # exit to allow docker to restart the container and try again
                exit(1)
            else:
                logging.debug(f"Disconnected from MQTT Broker {self.broker} gracfully.")
                exit(0)

        # Set Connecting Client ID
        self.client = mqtt_client.Client(self.client_id)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
        except Exception as e:
            logging.error(f"Failed to connect to {self.broker}, {e}")
            exit(1)
    
    def subscribe(self, callback):
        def on_message(client, userdata, msg):
            callback(msg)
        self.client.subscribe(self.topic)
        self.client.on_message = on_message
        logging.info(f"Subscribed to topic: {self.topic}")
        logging.info("looping forever and waiting for messages")
        try:
            # looping forever is blocking, callbacks handle the messages and control the flow
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info("Exiting the application with a keyboard interrupt")
            self.client.disconnect()
            exit(0)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            self.client.disconnect()
            exit(1)

if __name__ == "__main__":
    from  datetime import datetime as dt
    # set environment variables
    os.environ["MQTT_HOST"] = 'broker.hivemq.com'
    os.environ["MQTT_PORT"] = '1883'
    os.environ["MQTT_TOPIC"] = 'sunlab'
    mqtt = MQTT()
    mqtt.connect_mqtt()
    def print_message(message):
        '''Print the message and note if the message is retained'''
        print(dt.now(), end="|")
        print(message.payload.decode(), end="|")
        print("Retained:", message.retain)
    mqtt.subscribe(print_message) # print the messages

