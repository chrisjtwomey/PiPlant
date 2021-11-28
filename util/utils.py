import re

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
        raise("Unable to dehumanize \"{}\": {}".format(human_str, str(ve)))
    except Exception as e:
        raise("Unexpected error dehumanizing \"{}\": {}".format(human_str, str))

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
        raise ValueError("Unsupported time format: {}. Supported formats: s(ecs), m(min), h(r), d(y), w(k)".format(unit))

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