# class to interact with the InfluxDB database

import sys
import os
import requests
import datetime
import time

import influxdb_client as dbc
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException


import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class INFLUX:
    def __init__(self, known_locations=None, known_zones=None):
        '''if known_locations and known_zones are not provided, 
        they are set to None and the location and zone names will not be available in the dashboard'''
        # pull the environment variables
        self.influxdb_url = os.getenv("INFLUXDB_URL")
        self.influxdb_user = os.getenv("INFLUXDB_ADMIN_USER")
        self.influxdb_password = os.getenv("INFLUXDB_ADMIN_PASSWORD")
        self.influxdb_bucket = os.getenv("INFLUXDB_BUCKET")
        self.influxdb_org = os.getenv("INFLUXDB_ORG")
        self.influxdb_token = os.getenv("INFLUXDB_ADMIN_TOKEN")

        logging.info(f"{self.influxdb_url=}, \
                        {self.influxdb_user=}, \
                        {self.influxdb_password=}, \
                        {self.influxdb_bucket=}, \
                        {self.influxdb_org=}, \
                        {self.influxdb_token=}")

        # known locations and zones (are used to show the location and zone names in the dashboard)
        self.known_locations = known_locations
        self.known_zones = known_zones
        
    def connect(self):
        '''Connect to the InfluxDB database'''
        # create a client
        self.db_client = dbc.InfluxDBClient(url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org)
        self.write_api = self.db_client.write_api(write_options=SYNCHRONOUS)
        # check if connected
        try:
            self.db_client.ready()
            logging.info("Connected to InfluxDB")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to InfluxDB: {e}")
            return False
        
    def check(self):
        '''Check if InfluxDB is running'''
        try:
            logging.info(f"checking {self.influxdb_url}/health")
            response = requests.get(f"{self.influxdb_url}/health")
            response.raise_for_status() #
            logging.info(f"InfluxDB health check: {response.json()}")
            return True
        except Exception as e:
            logging.error(f"InfluxDB health check failed: {e}")
            return False
        
    # def simple_write(self):
    #     '''Write a simple point to the InfluxDB database, 
    #     used for testing and tracking the mqtt/app.py connections'''
    #     point = dbc.Point("mqtt_app_status").tag("status", "connected")
    #     results = self.write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
    #     logging.info(f"database write {results=}")
    #     return results
    
    # def simple_query(self):
    #     '''Query the InfluxDB database to find the point we just wrote
    #      used for testing and tracking the mqtt/app.py connections'''
    #     query = f'from(bucket: "{self.influxdb_bucket}") |> range(start: -1m)'
    #     tables = self.db_client.query_api().query(query, org=self.influxdb_org)
    #     if len(tables) == 0:
    #         logging.error("No query results")
    #         return False
    #     for table in tables:
    #         for row in table.records:
    #             logging.info(f"Query result: {row.values}")
    #     return tables
    
    def simple_write_and_verify(self):
        '''Write a simple point and verify the write by querying the data'''
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        logging.info(f"Writing point to InfluxDB: {now}")
        point = dbc.Point("mqtt_app_status").field("connected",1).time(now)
        try:
            self.write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
            self.write_api.flush() # ensure the singlewrite is processed
            logging.info("Database write successful.")
            time.sleep(0.25) # ensure plenty of time for the write to be processed
            # Query to verify the write
            query = f'''
            from(bucket: "{self.influxdb_bucket}")
                |> range(start: -5s)
                |> filter(fn: (r) => r._measurement == "mqtt_app_status")'''
                # |> filter(fn: (r) => r.status == "connected")
            # '''
            tables = self.db_client.query_api().query(query, org=self.influxdb_org)
            if tables:
                for table in tables:
                    for record in table.records:
                        logging.info(f"Verified write: {record.values}")
                return True
            else:
                logging.warning("Write verification failed: No matching records found.")
                return False
        except ApiException as e:
            logging.error(f"InfluxDB API exception during write/verify: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during write/verify: {e}")
            return False


    def write(self, data, measurement_name="tag_event"):
        '''Write the custom mqtt data string to the InfluxDB database\n
        data format: \n
        {{assetId}} {{categoryId}} {{eventName}} {{start}} {{end}} {{ownerId}} {{confidence}} {{value}} {{createdOn}} [{{#keySet}}{{key}}:{{{value}}},{{/keySet}}]
        '''
        data = data.split(" ")
        key_set = str(data[9]).strip('[]').split(",")[:-1] #remove the last empty element

        logging.debug(f"keyset={key_set}")

        #basic point for influxdb
        point = (dbc.Point(f"{measurement_name}")
                .tag("assetId", data[0])
                .tag("categoryId", data[1])
                .tag("eventName", data[2])
                .tag("ownerId", data[5])
                .field("start", data[3])
                .field("end", data[4])
                .field("confidence", data[6])
                .field("value", data[7])
                .field("createdOn", data[8])
        )
        # add additional fields from the key_set if availible
        for k in key_set:
            key_value = k.split(":")
            key = key_value[0]
            value = key_value[1]
            #parse the value to float in these cases
            if key in ["temperature", "active", "latitude", "longitude", "distance"]:
                logging.debug(f"{key} field!") 
                point.field(key, float(value))
            #parse the connectivity (boolean)
            elif key in ["connectivity"]:
                logging.debug(f"{key} field!")
                if value == "1":
                    point.field(key, True)
                elif value == "0":
                    point.field(key, False)
                else:
                    logging.error("unknown connectivity value!?")
                    point.field(key, value)
            #parse outOfOrder (string to boolean)
            elif key in ["outOfOrder"]:
                logging.debug(f"{key} field!")
                point.field(key, value) # keep as string
            #parse the location and zone to a name if known
            elif key in ["location"]:
                # remove the quotes
                value = value.strip('"')
                logging.debug(f"{key} field! {value=}")
                if value in self.known_locations: #sunlab location
                    point.field("location", self.known_locations[value]) # replace the location with the name
                else:
                    logging.warning("unknown location!")
                    point.field("location", value)
            #parse the zone to a name if known
            elif key in ["zone"]:
                # remove the quotes
                value = value.strip('"')
                logging.debug(f"{key} field! {value=}")
                if value in self.known_zones:
                    point.field("zone", self.known_zones[value]) # replace the zone with the name
                else:
                    logging.warning("unknown zone!")
                    point.field("zone", value)
            else: #other keys
                logging.warning(f"unknown field! {key=}, {value=}")
                point.field(key, value)

        # write the point to the database
        self.write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
        logging.info(f"Writing point to InfluxDB: {point.to_line_protocol()}")
        return

    def check_permissions(self):
        '''Check if the provided token has the necessary permissions to write'''
        url = f"{self.influxdb_url}/api/v2/authorizations"
        headers = {
            "Authorization": f"Token {self.influxdb_token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            authorizations = response.json()
            # Check if the token has the necessary write permissions
            for authorization in authorizations['authorizations']:
                if authorization['id'] == self.influxdb_token:
                    for permission in authorization['permissions']:
                        logging.info(f"Permission: {permission['action']} on {permission['resource']['type']}")
                        if permission['action'] == 'write' and permission['resource']['type'] == 'buckets':
                            return True
            return False
        except Exception as e:
            logging.error(f"Error checking permissions: {e}")
            return False

    def check_bucket_health(self):
        '''Check if the bucket is accessible with the provided token'''
        try:
            # List buckets to verify read access and token permissions
            buckets = self.db_client.buckets_api().find_bucket_by_name(self.influxdb_bucket)
            if buckets:
                logging.info(f"Bucket '{self.influxdb_bucket}' is accessible")
                return True
            else:
                logging.warning(f"Bucket '{self.influxdb_bucket}' not found or accessible")
                return False
        except Exception as e:
            logging.error(f"Bucket health check failed: {e}")
            return False


    