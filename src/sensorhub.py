import smbus
import logging

logging.basicConfig(filename='sensorhub.py', encoding='utf-8', level=logging.DEBUG)

class SensorHub:
    # Register Map: https://wiki.52pi.com/index.php/DockerPi_Sensor_Hub_Development_Board_SKU:_EP-0106
    DEVICE_BUS              = 1
    DEVICE_ADDR             = 0x17

    TEMP_REG                = 0x01 # off-chip temp sensor unit:degC
    LIGHT_REG_L             = 0x02 # light brightness low 8-bit unit:lux
    LIGHT_REG_H             = 0x03 # light brightness high 8-bit unit:lux
    STATUS_REG              = 0x04 # status function
    ON_BOARD_TEMP_REG       = 0x05 # onboard temp sensor unit:degC
    ON_BOARD_HUMIDITY_REG   = 0x06 # onboard humidity unit:%
    ON_BOARD_SENSOR_ERROR   = 0x07 # 0(OK) - 1(ERROR)
    BMP280_TEMP_REG         = 0x08 # P. temperature unit:degC
    BMP280_PRESSURE_REG_L   = 0x09 # P. pressure low 8-bit unit:Pa
    BMP280_PRESSURE_REG_M   = 0x0A # P. pressure mid 8-bit unit:Pa
    BMP280_PRESSURE_REG_H   = 0x0B # P. pressure high 8-bit unit:Pa
    BMP280_STATUS           = 0x0C # 0(OK) - 1(ERROR) 
    HUMAN_DETECT            = 0x0D # 0(movement detect in 5s) - 1(no movement detect)

    def __init__(self): 
        self.bus = smbus.SMBus(self.DEVICE_BUS)
        self.a_receiveBuf = [0x00]
    
    def read(self):
        for i in range(self.TEMP_REG,self.HUMAN_DETECT + 1):
            self.a_receiveBuf.append(self.bus.read_byte_data(self.DEVICE_ADDR, i))

    def status(self): 
        switch(self.a_receiveBuf[self.STATUS_REG])

    def __clearReceiveBuf(self):
        self.a_receiveBuf = [0x00]

    def __dict__(self):
        recBuf = self.a_receiveBuf

        return dict({
            'temp_reg':                 recBuf[self.STATUS_REG] & 0x01,
            'light_reg_l':              recBuf[self.STATUS_REG] & 0x02,
            'light_reg_h':,             recBuf[]
            'status_reg':,
            'on_board_temp_reg':,
            'on_board_humidity_reg':    recBuf[self.ON_BOARD_HUMIDITY_REG],
            'bmp280_temp_reg':,
            'bmp280_pressure_reg_l':,
            'bmp280_pressure_reg_m':,
            'bmp280_pressure_reg_h':,
            'bmp280_status':,
            'human_detect':,
        })