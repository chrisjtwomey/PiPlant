#!/usr/bin/env python3

import time
import logging.config
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor

logging.config.fileConfig('logging.ini')

if __name__ == '__main__':
    poll_interval = 5
    sms = [
        SoilMoistureSensor(adc_channel=0, poll_interval=poll_interval),
        SoilMoistureSensor(adc_channel=1, poll_interval=poll_interval),
        SoilMoistureSensor(adc_channel=2, poll_interval=poll_interval),
        SoilMoistureSensor(adc_channel=3, poll_interval=poll_interval),
        SoilMoistureSensor(adc_channel=4, poll_interval=poll_interval),
    ]
    sh = SensorHub(poll_interval=poll_interval)
    while True:
        for sm in sms: 
            print(sm.value)
        print(dict(sh))
        
        time.sleep(1)