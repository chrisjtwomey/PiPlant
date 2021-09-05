import time
import psutil
import logging
from gpiozero import CPUTemperature, LoadAverage, DiskUsage, PiBoardInfo

log = logging.getLogger(__name__)

class BoardStats:
    MIN_CPU_DEGC=30
    MAX_CPU_DEGC=100
    MIN_LOAD_AVG=0
    MAX_LOAD_AVG=2
    
    def __init__(self, max_data_age_seconds=60):
        self.__receive_time = 0
        self.__a_receiveBuf = []
        self.__cpu_temp = CPUTemperature(min_temp=self.MIN_CPU_DEGC, max_temp=self.MAX_CPU_DEGC)
        self.__disk_usage = DiskUsage()
        self.__load_avg = LoadAverage(min_load_average=self.MIN_LOAD_AVG, max_load_average=self.MAX_LOAD_AVG)
        self.__max_data_age_seconds = max_data_age_seconds

    def read(self):
        self.__clear_receive_buf()
        log.info("Receiving board stats data")

        try:
            

            for adc in self.__adcs:
                channel_data = adc.value
                self.__a_receiveBuf.append(channel_data)

            self.__receive_time = time.time()
        except Exception as e:
            log.error(e)

    def get_all_sensor_values(self):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf.copy()

    def get_sensor_value(self, channel):
        if self.__is_state_data():
            self.read()

        return self.__a_receiveBuf.copy()[channel]

    def __is_state_data(self):
        log.debug("Checking for stale data")
        epoch_time = time.time()
        log.debug("Epoch time is {}, last receive time is {}".format(
            epoch_time, self.__receive_time))
        data_age = time.time() - self.__receive_time
        is_stale = epoch_time - self.__receive_time > self.__max_data_age_seconds
        log.debug(
            "Data age is {} seconds; stale: {}".format(data_age, is_stale))

        return is_stale

    def __clear_receive_buf(self):
        log.debug("Re-initializing receive buffer")
        self.__a_receiveBuf = []

class MemoryUsage:
    def __init__(self):
        self._usage = 0
        self._capacity = 0
        
    @property
    def usage(self):
        memory = psutil.virtual_memory()
        # Divide from Bytes -> KB -> MB
        available = round(memory.available/1024.0/1024.0,1)
        total = round(memory.total/1024.0/1024.0,1)
        return str(available) + 'MB free / ' + str(total) + 'MB total ( ' + str(memory.percent) + '% )'
