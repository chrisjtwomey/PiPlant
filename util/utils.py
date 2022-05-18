import re
import datetime
import operator
from functools import reduce
from reprlib import Repr
import reprlib

HSBK_HUE_MIN_VALUE = 0
HSBK_HUE_MAX_VALUE = 360
HSBK_KELVIN_MIN_VALUE = 2500
HSBK_KELVIN_MAX_VALUE = 9000
HSBK_FLT_MIN_VALUE = 0.0
HSBK_FLT_MAX_VALUE = 1.0
HSBK_FLT_PRECISION = 2
HSBK_FLT_SCALE = 0.01


def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    get_by_path(root, items[:-1])[items[-1]] = value


def del_by_path(root, items):
    """Delete a key-value in a nested object in root by item sequence."""
    del get_by_path(root, items[:-1])[items[-1]]

def dehumanize(human_str):
    # ensure str
    human_str = str(human_str)
    match = re.match(r"([0-9]+)([a-y]+)", human_str, re.I)
    try:
        if match:
            quantity, unit = match.groups()
            return _dehumanize_time(quantity, unit)
        else:
            return _dehumanize_boolean(human_str)
    except ValueError as ve:
        raise ValueError('Unable to dehumanize "{}": {}'.format(human_str, str(ve)))
    except Exception as e:
        raise ValueError(
            'Unexpected error dehumanizing "{}": {}'.format(human_str, str)
        )


def _dehumanize_time(quantity, unit):
    time_seconds = 0
    quantity = int(quantity)
    unit = unit.lower()

    if unit == "s" or unit == "secs" or unit == "seconds":
        time_seconds = quantity
    elif unit == "m" or unit == "mins" or unit == "minutes":
        time_seconds = quantity * 60
    elif unit == "h" or unit == "hr" or unit == "hours":
        time_seconds = quantity * 60 * 60
    elif unit == "d" or unit == "dy" or unit == "days":
        time_seconds = quantity * 60 * 60 * 24
    elif unit == "w" or unit == "wk" or unit == "weeks":
        time_seconds = quantity * 60 * 60 * 24 * 7
    else:
        raise ValueError(
            "Unsupported time format: {}. Supported formats: s(ecs), m(min), h(r), d(y), w(k)".format(
                unit
            )
        )

    return time_seconds


def _dehumanize_boolean(boolean_str):
    boolean_str_lw = boolean_str.lower()

    if boolean_str_lw == "on":
        return True
    elif boolean_str_lw == "off":
        return False
    elif boolean_str_lw == "enabled":
        return True
    elif boolean_str_lw == "disabled":
        return False
    elif boolean_str_lw == "true":
        return True
    elif boolean_str_lw == "false":
        return False
    else:
        raise ValueError("Unable to parse boolean: {}".format(boolean_str))


def hour_to_datetime(hour_str):
    nowdate = datetime.datetime.now()

    nowdate_str = nowdate.strftime("%d/%m/%Y")
    nowdatetime_str = nowdate_str + " " + hour_str

    dt = datetime.datetime.strptime(nowdatetime_str, "%d/%m/%Y %H:%M")

    return dt

def parse_hsbk_map(hsbk_map):
    parsed_hsbk = {}

    if "hue" in hsbk_map:
        hue = hsbk_map["hue"]

        if not isinstance(hue, int):
            raise ValueError("HSBK hue {} is not an integer".format(hue))

        if not (HSBK_HUE_MIN_VALUE <= hue <= HSBK_HUE_MAX_VALUE):
            raise ValueError("HSBK hue value {} not in range ({} - {})".format(hue, HSBK_HUE_MIN_VALUE, HSBK_HUE_MAX_VALUE))
        
        parsed_hsbk["hue"] = hue
    
    if "saturation" in hsbk_map:
        sat = hsbk_map["saturation"]

        if isinstance(sat, str):
            sat = percentage_string_as_float(sat, scale=HSBK_FLT_SCALE, precision=HSBK_FLT_PRECISION)

        if not (HSBK_FLT_MIN_VALUE <= sat <= HSBK_FLT_MAX_VALUE):
            raise ValueError("HSBK saturation value {} not in range ({} - {})".format(sat, HSBK_FLT_MIN_VALUE, HSBK_FLT_MAX_VALUE))

    if "brightness" in hsbk_map:
        brightness = hsbk_map["brightness"]

        if isinstance(brightness, str):
            brightness = percentage_string_as_float(brightness, scale=HSBK_FLT_SCALE, precision=HSBK_FLT_PRECISION)

        if not (HSBK_FLT_MIN_VALUE <= brightness <= HSBK_FLT_MAX_VALUE):
            raise ValueError("HSBK brightness value {} not in range ({} - {})".format(brightness, HSBK_FLT_MIN_VALUE, HSBK_FLT_MAX_VALUE))

        parsed_hsbk["brightness"] = brightness

    if "kelvin" in hsbk_map:
        kelvin = hsbk_map["kelvin"]

        if not isinstance(kelvin, int):
            raise ValueError("HSBK kelvin {} is not an integer".format(kelvin))

        if not (HSBK_KELVIN_MIN_VALUE <= kelvin <= HSBK_KELVIN_MAX_VALUE):
            raise ValueError("HSBK kelvin value {} not in range ({} - {})".format(kelvin, HSBK_KELVIN_MIN_VALUE, HSBK_KELVIN_MAX_VALUE))

        parsed_hsbk["kelvin"] = int(kelvin)

    return parsed_hsbk

def percentage_string_as_float(val, scale=0.01, precision=2):
    if "%" in val:
        return round(int(val.replace("%", "")) * scale, precision)
    else:
        return round(int(val) * scale, precision)

def find_paths_to_key(d, *target_keys):
    def traverse(dic, path=None):
        if not path:
            path = []
        if isinstance(dic, dict):
            for x in dic.keys():
                local_path = path[:]
                local_path.append(x)
                for b in traverse(dic[x], local_path):
                    yield b
        else:
            yield path, dic

    target_paths = list()
    paths = list(traverse(d))
    for (keys, _) in paths:
        if any(target_key in keys for target_key in target_keys):
            target_paths.append(keys)

    return target_paths


def get_config_prop_by_keys(
    config, *keys, default=None, required=True, dehumanized=False
):
    val = default
    found_vals = [get_by_path(config, keys)]

    if len(found_vals) == 0:
        if default is None and required is True:
            raise KeyError("{} not in config but is required".format(".".join(keys)))
    else:
        val = found_vals[0]

    if dehumanized:
        val = dehumanize(val)

    return val


def get_config_prop(config, prop, default=None, required=True, dehumanized=False):
    val = default

    if prop not in config:
        if default is None and required is True:
            raise KeyError("{} not in config but is required".format(prop))
    else:
        val = config[prop]

    if dehumanized:
        val = dehumanize(val)

    return val


def avg(values: list[int]) -> int:
    return round(sum(values) / len(values))


def percentage_angle_in_range(minAng, maxAng, val_percent):
    return int(minAng + (maxAng - minAng) * (val_percent / 100))

def normalize_to_range(x, old_r_min, old_r_max, new_r_min, new_r_max, decimals=2):
    return round(((x - old_r_min) / (old_r_max - old_r_min)) * (new_r_max - new_r_min) + new_r_min, decimals)

def repr_schedules(schedules):
    repr = "Schedules:\n\t{}".format(
        "\n\t".join(
            [
                "{: >10}: {: >10}".format(sched["name"], sched["time"])
                for sched in schedules
            ]
        )
    )
    return repr


def repr_device_groups(device_groups):
    repr = "Device groups:\n\t"

    for dg in device_groups:
        repr += "{}:\n\t\t{}".format(
            dg.name, "\n\t\t".join([str(dev) for dev in dg.devices])
        )

    return repr


def repr_sensors(sensors):
    return "Sensors:\n\t{}".format("\n\t".join([str(sensor) for sensor in sensors]))
