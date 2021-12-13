import lifxlan
import logging
from lifxlan import Light, Group

log = logging.getLogger("LIFX Devicegroup")

def init_devicegroup_from_config(group_name, devices):
        return group_name, Group(devices)

def init_device_from_config(device_entry):
    mac = device_entry["mac"]
    ip = device_entry["ip"]
    lifx_device = Light(mac, ip)

    return lifx_device

def get_devicegroup_hsbk(devicegroup):
    try:
        hsbks = []
        devices = devicegroup.get_device_list()
        for device in devices:
            log.debug("Querying device for HSBK...\n\tMAC: {}\n\tIP: {}".format(device.mac_addr, device.ip_addr))

            hsbk = device.get_color()
            hsbks.append(hsbk)
        return hsbks
    except lifxlan.WorkflowException as e:
        # catch exception here as we don't want to stop on
        # communication errors
        log.error(
            'Error occurred communicating with LIFX lights')
        raise e

def get_devicegroup_power(devicegroup):
    try:
        powers = []
        devices = devicegroup.get_device_list()
        for device in devices:
            log.debug("Querying device for power...\n\tMAC: {}\n\tIP: {}".format(device.mac_addr, device.ip_addr))

            power = device.get_power() > 0
            powers.append(power)
        return powers
    except lifxlan.WorkflowException as e:
        # catch exception here as we don't want to stop on
        # communication errors
        log.error(
            'Error occurred communicating with devicegroup')
        raise e

def set_devicegroup_power(devicegroup, power):
    try:
        devicegroup.set_power(power)
        return [power] * len(devicegroup.get_device_list())
    except lifxlan.WorkflowException as e:
        # catch exception here as we don't want to stop on
        # communication errors
        log.error(
            'Error occurred communicating with LIFX lights')
        raise e

def set_devicegroup_hsbk(devicegroup, hsbk, transition_seconds=0):
    transition_ms = int(transition_seconds * 1000)
    log.debug("Setting HSBK for device group:\n\tHSBK: {0}".format(hsbk))
    if transition_seconds > 0:
        log.debug("HSBK transition time:\n\t{} seconds".format(transition_seconds))

    try:
        devicegroup.set_color(hsbk, duration=transition_ms)
        return [hsbk] * len(devicegroup.get_device_list())
    except lifxlan.WorkflowException as e:
        # catch exception here as we don't want to stop on
        # communication errors
        log.error(
            'Error occurred communicating with devicegroup')
        raise e