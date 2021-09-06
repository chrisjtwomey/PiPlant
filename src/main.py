#!/usr/bin/env python3

import time
import logging.config
from piplantmon import PiPlantMon

logging.config.fileConfig('./logging.ini')

if __name__ == '__main__':
    ppm = PiPlantMon(poll_interval=5)
    while True:
        ppm.run()

        time.sleep(1)