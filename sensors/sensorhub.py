import smbus
from .polledsensor import PolledSensor


class SensorHub(PolledSensor):
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

    def __init__(self, poll_interval=1):
        self._external_temperature = 0
        self._onboard_temperature = 0
        self._onboard_brightness = 0
        self._onboard_humidity = 0
        self._barometer_temperature = 0
        self._barometer_pressure = 0
        self._livebody_detection = False

        super().__init__(poll_interval=poll_interval)
        self._value = dict()

        status, _, _ = self.status()

        if status == self.BOARD_STATUS_ERROR:
            raise ValueError(
                "Failed to initialize with status: {}".format(status))

        self.log.debug("Initialized with status: {}".format(status))

    def getValue(self):
        self._bus = smbus.SMBus(self.DEVICE_BUS)

        data_buffer = [0x00]
        for i in range(self.TEMP_REG, self.HUMAN_DETECT + 1):
            data_buffer.append(
                self._bus.read_byte_data(self.DEVICE_ADDR, i))
        self._bus.close()
        self._bus = None

        return data_buffer

    @property
    def external_temperature(self):
        return self.value[self.TEMP_REG]

    @property
    def onboard_temperature(self):
        return self.value[self.ON_BOARD_TEMP_REG]

    @property
    def onboard_brightness(self):
        return (self.value[self.LIGHT_REG_H] << 8 | self.value[self.LIGHT_REG_L])

    @property
    def onboard_humidity(self):
        return self.value[self.ON_BOARD_HUMIDITY_REG]

    @property
    def barometer_temperature(self):
        return self.value[self.BMP280_TEMP_REG]

    @property
    def barometer_pressure(self):
        return round((self.value[self.BMP280_PRESSURE_REG_L] |
                      self.value[self.BMP280_PRESSURE_REG_M] << 8 |
                      self.value[self.BMP280_PRESSURE_REG_H] << 16) / 100)

    @property
    def livebody_detection(self):
        return self.value[self.HUMAN_DETECT] == 1

    def status(self):
        warnings = []
        errors = []
        status = self.BOARD_STATUS_OK

        self.value  # ensure not stale

        status_func_reg = self._value[self.STATUS_REG]
        bmp280_func_reg = self._value[self.BMP280_STATUS]

        if status_func_reg & 0x02:
            msg = "No ext. temp sensor detected"
            warnings.append(msg)

        if status_func_reg & 0x01:
            msg = "Ext. temp sensor over-range (-30C~127C)"
            warnings.append(msg)

        if status_func_reg & 0x04:
            msg = "Onboard brightness sensor over-range (0Lux~1800Lux)"
            warnings.append(msg)

        if status_func_reg & 0x07:
            msg = "Onboard temp or humidity sensor error - data is not up-to-date"
            warnings.append(msg)

        if status_func_reg & 0x08:
            msg = "Onboard brightness sensor failure"
            errors.append(msg)

        if bmp280_func_reg == 1:
            msg = "Onboard barometer sensor failure"
            errors.append(msg)

        if len(warnings) > 0:
            status = self.BOARD_STATUS_WARNING
        elif len(errors) > 0:
            status = self.BOARD_STATUS_ERROR

        self.log.debug("SensorHub status: {}".format(status))
        self.log.debug("\tWarnings:\t{}".format(len(warnings)))
        self.log.debug("\tErrors:\t\t{}".format(len(errors)))

        for warn in warnings:
            status = self.BOARD_STATUS_WARNING
            self.log.warn(warn)

        for err in errors:
            status = self.BOARD_STATUS_ERROR
            self.log.error(err)

        return status, warnings, errors

    def __iter__(self):
        yield 'ext_temp',           self.external_temperature,
        yield 'onboard_temp',       self.onboard_temperature,
        yield 'onboard_brightness', self.onboard_brightness,
        yield 'onboard_humidity',   self.onboard_humidity,
        yield 'baro_temp',          self.barometer_temperature,
        yield 'baro_pressure',      self.barometer_pressure,
        yield 'livebody_detection', self.livebody_detection,
