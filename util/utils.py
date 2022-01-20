import re
import datetime
import operator
from functools import reduce


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
        raise ValueError('Unexpected error dehumanizing "{}": {}'.format(human_str, str))


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


def parse_hsbk_map(hsbk_map, max_value=65535):
    hue = hsbk_map["hue"] if "hue" in hsbk_map else 0
    sat = hsbk_map["saturation"] if "saturation" in hsbk_map else 0
    brightness_raw = hsbk_map["brightness"] if "brightness" in hsbk_map else "0"
    kelvin = hsbk_map["kelvin"] if "kelvin" in hsbk_map else 0

    if "%" in brightness_raw:
        brightness = int(max_value / 100 * int(brightness_raw.split("%")[0]))
    else:
        brightness = int(brightness_raw)

    hsbk = [hue, sat, brightness, kelvin]

    return hsbk


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
