#!/usr/bin/python

import sys
import time
import logging
import spidev

#logging.basicConfig(filename='moisturesensorarray.log', level=logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.root.setLevel(logging.NOTSET)


class MoistureSensorArray:
    BUS = 0
    DEVICE = 0
    SPI_MAX_SPEED_HZ = 1000000

    def __init__(self, mcp3008_open_channels=[0, 1, 2, 3, 4, 5, 6, 7], max_data_age_seconds=60):
        self.__receive_time = 0
        self.__a_receiveBuf = []
        self.__mcp3008_open_channels = mcp3008_open_channels
        self.__max_data_age_seconds = max_data_age_seconds

    def read(self):
        self.__clear_receive_buf()
        spi = None
        logging.info("Receiving moisture sensor data")

        try:
            spi = self.__get_spi()
            for channel in self.__mcp3008_open_channels:
                channel_data = self.__read_channel(spi, channel)
                self.__a_receiveBuf.append(channel_data)

            self.__receive_time = time.time()
        except Exception as e:
            logging.error(e)
        finally:
            if spi:
                spi.close()
                spi = None

    def get_all_sensor_values(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf.copy()

    def get_sensor_value(self, channel):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf.copy()[channel]

    def __read_channel(self, spi, channel):
        val = spi.xfer2([1, (8+channel) << 4, 0])
        data = ((val[1] & 3) << 8) + val[2]

        return data

    def __is_state_data(self):
        logging.debug("Checking for stale data")
        epoch_time = time.time()
        logging.debug("Epoch time is {}, last receive time is {}".format(
            epoch_time, self.__receive_time))
        data_age = time.time() - self.__receive_time
        is_stale = epoch_time - self.__receive_time > self.__max_data_age_seconds
        logging.debug(
            "Data age is {} seconds; stale: {}".format(data_age, is_stale))

        return is_stale

    def __get_spi(self):
        spi = spidev.SpiDev()
        spi.open(self.BUS, self.DEVICE)
        spi.max_speed_hz = self.SPI_MAX_SPEED_HZ

        return spi

    def __clear_receive_buf(self):
        logging.debug("Re-initializing receive buffer")
        self.__a_receiveBuf = []

msa = MoistureSensorArray(max_data_age_seconds=1)
while True:
    print(msa.get_all_sensor_values())
    time.sleep(1)
