#!/usr/bin/env python3

import ssl
import sys
from time import sleep
from bluepy import btle
import paho.mqtt.client as mqtt
import logging
from configparser import ConfigParser
import os.path
import argparse
import sdnotify

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')
        
# Argparse

project_name = 'Inkbird MQTT Sensor for Bluetooth pool sensor'
project_url = 'https://github.com/ptc/Inkbird-IBS-P01B-MQTT'

parser = argparse.ArgumentParser(description=project_name, epilog='For further details see: ' + project_url)
parser.add_argument('--config_dir', help='set directory where config.ini is located', default=sys.path[0])
parser.add_argument('--nodaemon', help='one time execution, no daemon mode', default=True)
parse_args = parser.parse_args()

# Load configuration file
config_dir = parse_args.config_dir
nodaemon_arg = parse_args.nodaemon

config = ConfigParser(delimiters=('=', ), inline_comment_prefixes=('#'))
config.optionxform = str
try:
    with open(os.path.join(config_dir, 'config.ini')) as config_file:
        config.read_file(config_file)
except IOError:
    logging.error('No configuration file "config.ini"')
    sys.exit(1)

topic = config['MQTT'].get('topic', "/test/sensor/pool") 
mac = config['Sensors'].get('PoolSensor', 'PoolSensor')
read_interval = int(config['General'].get('read_interval', 3600))
run_as_daemon = config['Daemon'].get('enabled', True)

if nodaemon_arg:
    run_as_daemon = False

bt_interface = config['General'].get('adapter', "hci0")

# Eclipse Paho callbacks - http://www.eclipse.org/paho/clients/python/docs/#callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info('MQTT connection established')
        print()
    else:
        logging.error('Connection error with result code {} - {}'.format(str(rc), mqtt.connack_string(rc)))
        #kill main thread
        os._exit(1)


def on_publish(client, userdata, mid):
    #print_line('Data successfully published.')
    pass

# MQTT connection
logging.info('Connecting to MQTT broker ...')
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish

if config['MQTT'].getboolean('tls', False):
    # According to the docs, setting PROTOCOL_SSLv23 "Selects the highest protocol version
    # that both the client and server support. Despite the name, this option can select
    # “TLS” protocols as well as “SSL”" - so this seems like a resonable default
    mqtt_client.tls_set(
        ca_certs=config['MQTT'].get('tls_ca_cert', None),
        keyfile=config['MQTT'].get('tls_keyfile', None),
        certfile=config['MQTT'].get('tls_certfile', None),
        tls_version=ssl.PROTOCOL_SSLv23
    )

mqtt_username = config['MQTT'].get('username')
mqtt_password = config['MQTT'].get('password', None)

if mqtt_username:
    mqtt_client.username_pw_set(mqtt_username, mqtt_password)
try:
    mqtt_client.connect(config['MQTT'].get('hostname', 'localhost'),
                        port=int(config['MQTT'].get('port', '1883')),
                        keepalive=config['MQTT'].getint('keepalive', 60))
except:
    logging.error('MQTT connection error. Please check your settings in the configuration file "config.ini"')
    sys.exit(1)
else:
    mqtt_client.loop_start()
    sleep(1.0) # some slack to establish the connection

n = sdnotify.SystemdNotifier()
n.notify("READY=1")

def float_value(nums):
    # check if temp is negative
    num = (nums[1]<<8)|nums[0]
    if nums[1] == 0xff:
        num = -( (num ^ 0xffff ) + 1)
    return float(num) / 100

def c_to_f(temperature_c):
    return 9.0/5.0 * temperature_c + 32

def read_current_value():
    try:
        dev = btle.Peripheral(mac, addrType=btle.ADDR_TYPE_PUBLIC)
        # First two bytes on characteristic at 0x0024 contain current 
        # temperature in Celsius as little endian value
        readings = dev.readCharacteristic(0x0024)
        return readings
    except Exception as e:
        logging.error("Error reading BTLE: {}".format(e))
        return False

while True:
    current_value = read_current_value()
    if not current_value:
        continue

    logging.info("raw data: {}".format(current_value))

    # little endian, first two bytes are temp
    temperature_c = float_value(current_value[0:2])
    logging.debug("temperature: {}".format(temperature_c))

    result = mqtt_client.publish('{}/celsius'.format(topic),temperature_c)

    if result[0] == 0:
        logging.debug("mqtt: sent {}, {}".format(topic,temperature_c))
    else:
        logging.info("mqtt: failed to send {}".format(topic))

    if run_as_daemon:
        logging.debug('Going to sleep for {} seconds ...'.format(read_interval))
        sleep(read_interval)
    else:
        logging.info('One time execution done, exiting')
        mqtt_client.disconnect()
        break
    
