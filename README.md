# Inkbird-IBS-P01B-MQTT
Reads Inkbird IBS-P01B Bluetooth sensor and publishes temperature value via MQTT

## Installation
Assuming bluetooth is up and running and python bluetooth packages are installed, run

```shell
git clone https://github.com/ptc/Inkbird-IBS-P01B-MQTT /opt/Inkbird-IBS-P01B-MQTT

cd /opt/Inkbird-IBS-P01B-MQTT
sudo pip3 install -r requirements.txt
```

## Configuration
Change [`config.ini`](config.ini.template), add the MAC of your Inkbrid device and don't forget to also set MQTT credentials.
To get the MAC, run a BTLE scanning app and search for your device. 

You can create the file by copying the template:

```shell
cp /opt/Inkbird-IBS-P01B-MQTT/config.{ini.template,ini}
vim /opt/Inkbird-IBS-P01B-MQTT/config.ini
```

## Daemon Mode
To add a systemd service, run the following commands and don't forget to set daemon mode to True in the configuration file.

```shell
sudo cp /opt/Inkbird-IBS-P01B-MQTT/template.service /etc/systemd/system/inkbird.service

sudo systemctl daemon-reload

sudo systemctl start inkbird.service
sudo systemctl status inkbird.service

sudo systemctl enable inkbird.service
```

## Home Assistant Sensor
The easiest way to use the device within Home Assistant is to define a MQTT sensor. 

```yaml
- platform: mqtt
  state_topic: 'garden/sensor/pool/temp/celsius'
  name: 'Water Temp'
  unit_of_measurement: '°C'
```

## Credit
Script inspired by:
- https://github.com/ThomDietrich/miflora-mqtt-daemon/
- https://github.com/viyh/inkbird
