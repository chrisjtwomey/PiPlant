<img src="https://user-images.githubusercontent.com/5797356/133003822-0285ed8c-4045-4231-af81-9592cbb0f3a2.png" width="400" height="150">

---

A extensible suite for logging and displaying the living environment of house plants built on Raspberry Pi 4.

# Hardware

This project is designed to not require specific hardware to run. See [Adding or Changing Sensors](#adding-or-changing-sensors) to configure different hardware. The following is a list of hardware that this project was tested with:

* [Waveshare 3.7in E-Paper E-Ink Display HAT](https://www.waveshare.com/3.7inch-e-paper-hat.htm)
* [Aideepen Capacitive Soil Moisture Sensor v1.2](https://www.aideepen.com/products/capacitive-soil-moisture-sensor-module-not-easy-to-corrode-wide-voltage-wire-3-3-5-5v-corrosion-resistant-w-gravity-for-arduino)
* [DockerPi SensorHub v2.0](https://wiki.52pi.com/index.php?title=EP-0106)
* [MCP3008 ADC](https://www.adafruit.com/product/856)
* [LIFX A60](https://lifxshop.eu/products/lifx-colour-e27)
* [LIFX Z](https://lifxshop.eu/products/lifx-lightstrip-2m)


# Capabilities

* Aggregates data from a variety of environment sensors of your plant, including soil moisture, temperature, humidity, air pressure, and brightness.
* Aggregates performance data from your Raspberry Pi.
* Sensors are plug n' play and makes it easy to support your own sensors via the `config.yaml`, see [Adding or Changing Sensors](#adding-or-changing-sensors) for more info.
* Stores aggregated data in a pre-packaged [SQLite](https://www.sqlite.org/index.html) database, or can be configured to send to remote SQL storage. 
* Renders data visually to any display using [Pillow](https://pillow.readthedocs.io/en/stable/):
    * Hygrometer data page
    * Environment data page
    * Historical data page
    * RPi data page
* Automates the day/night schedule for smart bulbs used for houseplants, if configured and the smart bulbs have an exposed API.
* Ability to give smart bulbs motion-activated capabilties.

# Installation

## Pre-requisites

1. Enable the I2C interface with `raspi-config`:
    ```
    sudo raspi-config
    ```

2. Clone the project in a suitable directory:
    ```
    git clone https://github.com/chrisjtwomey/PiPlant.git
    ```

## Deploy as a Docker container

1. Update and upgrade system:
    ```
    sudo apt-get update && sudo apt-get upgrade
    ```

2. Install Docker 
    ```
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```

3. Build the PiPlant docker image:
    ```
    sudo docker build -t piplant:latest .
    ```

4. Run the built docker image:
    ```
    sudo docker run -d --name piplant --privileged piplant:latest
    ```
    The container needs the `--privileged` flag to access the GPIO pins.

5. To check the logs for debugging:
    ```
    sudo docker logs -f piplant
    ```

## Run PiPlant directly

1. Ensure Python 3.9 is installed on your Raspberry Pi:
    ```
    which python3
    /usr/local/bin/python3

    python3 --version
    Python 3.9.9
    ```
    If the `which` command does not return anything or if the version is not `3.9`, you can install Python3 with `apt-get`
    ```
    sudo apt-get install python3
    ```

2. Install the `pip` tool:
    ```
    sudo apt-get install python3-pip
    ```

    Install project requirements 
    ```
    python3 -m pip install -r requirements.txt
    ```

3. Run PiPlant directly:
    ```
    python3 piplant.py
    ```

## Run PiPlant in mock-mode without Raspberry Pi

You can run PiPlant without the need for real-life sensors. Each sensor package currently in PiPlant has a mock class that is used when PiPlant is configured in mock-mode.

To enable mock-mode, add `mock: true` to the PiPlant `config.yaml`:
```
---
piplant:
  mock: true
```

Individual sensors can also be run in mock-mode, for example:
```
sensors:
    hygrometers:
      - package: 
          module: sensors.hygrometer.aideepen
          class: CapacitiveHygrometer
          kwargs:
            mock: true
```

# Adding or Changing Sensors

A sensor can be imported automatically through `config.yaml`, as long as the sensor implements one of the defined interfaces:

| Interface         | module                          |
|-------------------|---------------------------------|
| Hygrometer        | sensors.hygrometer.hygrometer   |
| TemperatureSensor | sensors.environment.environment |
| HumiditySensor    | sensors.environment.environment |
| PressureSensor    | sensors.environment.environment |
| BrightnessSensor  | sensors.environment.environment |
| MotionSensor      | sensors.environment.environment |
| DeviceSensor      | sensors.device.device           |

The following is an example of the file structure of a valid package:
```
hygrometer
├── aideepen
│   ├── capacitivehygrometer.py
│   └── mock
│       └── capacitivehygrometer.py
└── hygrometer.py

2 directories, 3 files
```
The following is an example of how to import the package in `config.yaml`:
```
sensors:
    hygrometers:
      - package: 
          module: sensors.hygrometer.aideepen
          class: CapacitiveHygrometer
```

# Configuration

## PiPlant

| Property      | Description                                        | Default |
|---------------|----------------------------------------------------|---------|
| poll_interval | The time to wait between data refreshes            | 5s      |
| debug         | Flag to turn on verbose logging                    | False   |
| mock          | Flag to enable mock-mode on all sensors            | False   |
| sensors       | A dictionary containing the lists of sensor types  |         |

### Sensors

| Property    | Description                                                                                     |
|-------------|-------------------------------------------------------------------------------------------------|
| hygrometers | A list of hygrometer sensors that measures soil moisture for each plant                         |
| environment | A dictionary of environment sensor packages for temperature, humidity, pressure, and brightness |
| device      | A list of device sensors that measure Raspberry Pi performance stats                            |

#### Environment

| Property    | Description                                                                              |
|-------------|------------------------------------------------------------------------------------------|
| temperature | A sensor of type `TemperatureSensor` that returns the air temperature in degrees Celsius |
| humidity    | A sensor of type `HumiditySensor` that returns the air humidity as a percentage          |
| pressure    | A sensor of type `PressureSensor` that returns the air pressure as hectopascals          |
| brightness  | A sensor of type `BrightnessSensor` that returns the brightness as lux                   |

### Sensor

```
package: 
  module: sensors.hygrometer.aideepen
  class: CapacitiveHygrometer
  kwargs:
    mock: true
```

| Property      | Description                                                                                             | Required |
|---------------|---------------------------------------------------------------------------------------------------------|----------|
| module        | The absolute or relative path of the module that contains the real sensor class or mock class           | Yes      |
| remote_module | The name of the remote module that contains the real sensor, loaded via Pip                             | No       |
| class         | The name of the class in `module` or `remote_module` to import. The mock class must be the same name, if exists | Yes       |
| kwargs        | A dictionary containing the key-value arguments that are passed into the class instance __init__ method | No       |


## EPaper

| Property           | Description                                                                      | Default |
|--------------------|----------------------------------------------------------------------------------|---------|
| driver             | Contains the package of the ePaper driver to communicate with the ePaper display |         |
| enabled            | A flag to render to the ePaper display or not                                    | True    |
| refresh_interval   | The time to wait between refreshing the ePaper display                           | 1hr     |
| skip_splash_screen | A flag to display the PiPlant logo on start-up or not                            | False   |

## LightManager

| Property              | Description                                                                                     | Default |
|-----------------------|-------------------------------------------------------------------------------------------------|---------|
| autodiscovery         | A flag to automatically discover light devices of a certain `device_type` (not implemented yet) | False   |
| device_query_interval | The time to wait between refreshing the light devices current status                            | 2m      |
| device_type           | The type of light device manager to use                                                         | lifx    |
| device_groups         | A list of groups of device lights for schedules or motion detection managers                            |         |
| geo_city              | The geolocation city where PiPlant is located.                                               | Dublin    |
| motion_detection      | A config block for configuration motion-detection triggered lights                              |         |
| schedules             | A list of schedules for transitioning light HSBKs                                               |         |

### device_group

```
device_groups:
  - <group_name>:
      - mac: <mac address>
        ip: <ip address>
```

| Property | Description                                   | Required |
|----------|-----------------------------------------------|----------|
| mac      | The mac address of the light device           | Yes      |
| ip       | The accessible IP address of the light device | Yes      |

### motion_detection

| Property      | Description                                                        | Default |
|---------------|--------------------------------------------------------------------|---------|
| sensor        | Contains the package of the motion detection sensor                |         |
| timeout       | The time to wait to turn of light device if no motion was detected | 15m     |
| device_groups | A list of `device_group` names for the motion detection to manage  |         |

#### on_motion_trigger / on_motion_timeout

| Property      | Description                                                       | Default |
|---------------|-------------------------------------------------------------------|---------|
| transition    | The time to fade to the target `hsbk` state                       |         |
| hsbk          | The target HSBK state                                             | 15m     |
| device_groups | A list of `device_group` names for the motion detection to manage |         |

### schedule


| Property      | Description                                                                        | Default |
|---------------|------------------------------------------------------------------------------------|---------|
| name          | The name of the schedule                                                           |         |
| time          | A 24-hour time string (eg. "13:00") of when the current schedule will be triggered | 15m     |
| hsbk          | The target HSBK state                                                              |         |
| device_groups | A list of `device_group` names for the schedule to manage                          |         |

#### HSBK

| Property   | Description                                    |
|------------|------------------------------------------------|
| hue        | An integer for the hue value (0-65535)         |
| saturation | An integer for the saturation value (0-65535)  |
| brightness | An percentage string for the brightness value  |
| kelvin     | An integer for the kelvin value (2500-9000)    |