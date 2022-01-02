import smbus
from sensors.environment.environment import (
    TemperatureSensor,
    BrightnessSensor,
    HumiditySensor,
    PressureSensor,
    MotionSensor,
)


class SensorHub(
    TemperatureSensor, BrightnessSensor, HumiditySensor, PressureSensor, MotionSensor
):
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        status, _, _ = self.status()
        if status == self.BOARD_STATUS_ERROR:
            raise ValueError("Failed to initialize with status: {}".format(status))

        self.log.debug("Initialized with status: {}".format(status))

    def read(self):
        self._bus = smbus.SMBus(self.DEVICE_BUS)

        data_buffer = [0x00]
        for i in range(self.TEMP_REG, self.HUMAN_DETECT + 1):
            data_buffer.append(self._bus.read_byte_data(self.DEVICE_ADDR, i))
        self._bus.close()
        self._bus = None

        return data_buffer

    def get_data(self) -> dict:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "brightness": self.brightness,
            "motion": self.motion,
        }

    @property
    def temperature(self) -> int:
        data = self.read()
        return data[self.TEMP_REG]

    @property
    def brightness(self) -> int:
        data = self.read()
        return data[self.LIGHT_REG_H] << 8 | data[self.LIGHT_REG_L]

    @property
    def humidity(self) -> int:
        data = self.read()
        return data[self.ON_BOARD_HUMIDITY_REG]

    @property
    def pressure(self) -> int:
        data = self.read()
        return round(
            (
                data[self.BMP280_PRESSURE_REG_L]
                | data[self.BMP280_PRESSURE_REG_M] << 8
                | data[self.BMP280_PRESSURE_REG_H] << 16
            )
            / 100
        )

    @property
    def onboard_temperature(self) -> int:
        data = self.read()
        return data[self.ON_BOARD_TEMP_REG]

    @property
    def barometer_temperature(self) -> int:
        data = self.read()
        return data[self.BMP280_TEMP_REG]

    @property
    def motion(self) -> bool:
        data = self.read()
        return data[self.HUMAN_DETECT] == 1

    def status(self):
        warnings = []
        errors = []
        status = self.BOARD_STATUS_OK

        data = self.read()  # ensure not stale

        status_func_reg = data[self.STATUS_REG]
        bmp280_func_reg = data[self.BMP280_STATUS]

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
            # errors.append(msg)

        if bmp280_func_reg == 1:
            msg = "Onboard barometer sensor failure"
            errors.append(msg)

        if len(warnings) > 0:
            status = self.BOARD_STATUS_WARNING
        elif len(errors) > 0:
            status = self.BOARD_STATUS_ERROR

        self.log.debug("SensorHub status:\t{}".format(status))
        self.log.debug("\tWarnings:\t{}".format(len(warnings)))
        self.log.debug("\tErrors:\t\t{}".format(len(errors)))

        for warn in warnings:
            status = self.BOARD_STATUS_WARNING
            self.log.warn(warn)

        for err in errors:
            status = self.BOARD_STATUS_ERROR
            self.log.error(err)

        return status, warnings, errors