import sys
import time
import smbus
import logging

#logging.basicConfig(filename='sensorhub.log', level=logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.root.setLevel(logging.NOTSET)


class SensorHub:
    BOARD_STATUS_OK = "OK"
    BOARD_STATUS_ERROR = "ERROR"
    BOARD_STATUS_WARNING = "WARNING"

    # Register Map: https://wiki.52pi.com/index.php/DockerPi_Sensor_Hub_Development_Board_SKU:_EP-0106
    DEVICE_BUS = 1
    DEVICE_ADDR = 0x17

    TEMP_REG = 0x01  # off-chip temp sensor unit:degC
    LIGHT_REG_L = 0x02  # light brightness low 8-bit unit:lux
    LIGHT_REG_H = 0x03  # light brightness high 8-bit unit:lux
    STATUS_REG = 0x04  # status function
    ON_BOARD_TEMP_REG = 0x05  # onboard temp sensor unit:degC
    ON_BOARD_HUMIDITY_REG = 0x06  # onboard humidity unit:%
    ON_BOARD_SENSOR_ERROR = 0x07  # 0(OK) - 1(ERROR)
    BMP280_TEMP_REG = 0x08  # P. temperature unit:degC
    BMP280_PRESSURE_REG_L = 0x09  # P. pressure low 8-bit unit:Pa
    BMP280_PRESSURE_REG_M = 0x0A  # P. pressure mid 8-bit unit:Pa
    BMP280_PRESSURE_REG_H = 0x0B  # P. pressure high 8-bit unit:Pa
    BMP280_STATUS = 0x0C  # 0(OK) - 1(ERROR)
    HUMAN_DETECT = 0x0D  # 0(movement detect in 5s) - 1(no movement detect)

    EMPTY_RECEIVE_BUG = [0x00]

    def __init__(self, max_data_age_seconds=60):
        self.bus = smbus.SMBus(self.DEVICE_BUS)
        self.__a_receiveBuf = [0x00]
        self.__receive_time = 0
        self.__max_data_age_seconds = max_data_age_seconds

    def read(self):
        self.__clear_receive_buf()
        logging.info("Receiving SensorHub data")

        for i in range(self.TEMP_REG, self.HUMAN_DETECT + 1):
            self.__a_receiveBuf.append(
                self.bus.read_byte_data(self.DEVICE_ADDR, i))

        self.__receive_time = time.time()

    def get_external_temperature(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf[self.TEMP_REG]

    def get_onboard_temperature(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf[self.ON_BOARD_TEMP_REG]

    def get_onboard_brightness(self):
        if self.__is_state_data():
            self.read()

        return (self.__a_receiveBuf[self.LIGHT_REG_H] << 8 | self.__a_receiveBuf[self.LIGHT_REG_L])

    def get_onboard_humidity(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf[self.ON_BOARD_HUMIDITY_REG]

    def get_barometer_temperature(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf[self.BMP280_TEMP_REG]

    def get_barometer_pressure(self):
        if self.__is_state_data():
            self.read()

        return (self.__a_receiveBuf[self.BMP280_PRESSURE_REG_L] |
                self.__a_receiveBuf[self.BMP280_PRESSURE_REG_M] << 8 |
                self.__a_receiveBuf[self.BMP280_PRESSURE_REG_H] << 16)

    def get_livebody_detection(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf[self.HUMAN_DETECT] == 1

    def status(self):
        warnings = []
        errors = []
        status = self.BOARD_STATUS_OK
        if self.__is_state_data():
            self.read()

        status_func_reg = self.__a_receiveBuf[self.STATUS_REG]
        bmp280_func_reg = self.__a_receiveBuf[self.BMP280_STATUS]

        if status_func_reg & 0x02:
            msg = "No ext. temp sensor detected"
            warnings.append(msg)

        if status_func_reg & 0x01:
            msg = "Ext. temp sensor over-range (-30C~127C)"
            warnings.append(msg)

        if status_func_reg & 0x04:
            msg = "Onboard brightness sensor over-range (0Lux~1800Lux)"
            warnings.append(msg)

        if status_func_reg & 0x08:
            msg = "Onboard brightness sensor failure"
            errors.append(msg)

        if status_func_reg & 0x07:
            msg = "Onboard temp or humidity sensor error - data is not up-to-date"
            errors.append(msg)

        if bmp280_func_reg == 1:
            msg = "Onboard barometer sensor failure"
            errors.append(msg)

        if len(warnings) > 0:
            status = self.BOARD_STATUS_WARNING
        elif len(errors) > 0:
            status = self.BOARD_STATUS_ERROR

        logging.info("SensorHub status: {}".format(status))
        logging.debug("\tWarnings:\t{}".format(len(warnings)))
        logging.debug("\tErrors:\t\t{}".format(len(errors)))

        for warn in warnings:
            status = self.BOARD_STATUS_WARNING
            logging.warn(warn)

        for err in errors:
            status = self.BOARD_STATUS_ERROR
            logging.error(err)

        return status, warnings, errors

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

    def __clear_receive_buf(self):
        logging.debug("Re-initializing receive buffer")
        self.__a_receiveBuf = [0x00]

    def __iter__(self):
        status, _, _ = self.status()

        yield 'status',             status,
        yield 'stale_data',         self.__is_state_data(),
        yield 'ext_temp',           self.get_external_temperature(),
        yield 'onboard_temp',       self.get_onboard_temperature(),
        yield 'onboard_brightness', self.get_onboard_brightness(),
        yield 'onboard_humidity',   self.get_onboard_humidity(),
        yield 'baro_temp',          self.get_barometer_temperature(),
        yield 'baro_pressure',      self.get_barometer_pressure(),
        yield 'live_body_detect',   self.get_livebody_detection(),