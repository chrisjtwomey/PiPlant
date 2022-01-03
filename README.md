<img src="https://user-images.githubusercontent.com/5797356/133003822-0285ed8c-4045-4231-af81-9592cbb0f3a2.png" width="400" height="150">

---

A extensible suite for logging and displaying the living environment of house plants built on Raspberry Pi 4.

# Hardware

This project is designed to not require specific hardware to run. See [Adding or Changing Sensors](#adding-or-changing-sensors) to configure different hardware. The following is a list of hardware that this project was tested with:

* [Waveshare 3.7in E-Paper E-Ink Display HAT](https://www.waveshare.com/3.7inch-e-paper-hat.htm)
* [Aideepen Capacitive Soil Moisture Sensor v1.2](https://www.aideepen.com/products/capacitive-soil-moisture-sensor-module-not-easy-to-corrode-wide-voltage-wire-3-3-5-5v-corrosion-resistant-w-gravity-for-arduino)
* [DockerPi SensorHub v2.0](https://wiki.52pi.com/index.php?title=EP-0106)
* [MCP3008 ADC](https://www.adafruit.com/product/856)


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

# Configuration

Coming soon...

# Adding or Changing Sensors

Coming soon...
