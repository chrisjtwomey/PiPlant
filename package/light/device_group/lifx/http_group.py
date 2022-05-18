import requests
import urllib.parse
import util.utils as utils
from ..device_group import DeviceGroup, DeviceGroupError

class LifxHTTPGroup(DeviceGroup):
    LIFX_MAX_VALUE = 65535
    HUE_MAX_VALUE = 360
    MIN_VALUE = 0

    def __init__(
        self, name, token, query_interval="2m", retry_interval="0s", max_retries=0
    ):
        self.group_id = name
        self.req_header = {
            "Authorization": "Bearer %s" % token,
        }
        devices = self.get_devices()
        super().__init__(name, devices, query_interval, retry_interval, max_retries)

    def get_devices(self) -> list:
        response = requests.get("https://api.lifx.com/v1/lights/group:{}".format(self.group_id), headers=self.req_header)
        data = response.json()

        return data

    def set_power(self, power, transition_seconds=0) -> None:
        if power == self.power:
            return

        def _set_power(power, transition_seconds):
            duration = transition_seconds * 1000
            power_flag = "on" if power else "off"
            try:
                response = requests.put("https://api.lifx.com/v1/lights/group:{}/state".format(self.name), headers=self.req_header, data={
                    "power": power_flag
                })
            except requests.exceptions.RequestException as re:
                raise DeviceGroupError(re)
            except Exception as e:
                raise e

        return self.do(_set_power, power, transition_seconds)

    def get_power(self) -> list:
        def _get_power():
            power = []

            try:
                response = requests.get("https://api.lifx.com/v1/lights/group:{}".format(self.name), headers=self.req_header)
                data = response.json()

                for device in data:
                    power.append(device["power"] == "on")
            except requests.exceptions.RequestException as re:
                raise DeviceGroupError("not all devices returned ok")
            except Exception as e:
                raise e

            return power

        return self.do(_get_power)

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        if hsbk == self.hsbk:
            return

        def _set_hsbk(hsbk, transition_seconds):
            duration = transition_seconds * 1000
            payload = {}
            color = ""
            
            if "hue" in hsbk:
                color += "hue:{} ".format(hsbk["hue"])
            if "saturation" in hsbk:
                color += "saturation:{} ".format(hsbk["saturation"])
            if "brightness" in hsbk:
                brightness = hsbk["brightness"]
                color += "brightness:{} ".format(brightness)
                payload = payload | {
                    "power": "on" if brightness > utils.HSBK_FLT_MIN_VALUE else "off"
                }
            if "kelvin" in hsbk:
                color += "kelvin:{}".format(hsbk["kelvin"])

            if len(color) > 0:
                payload["color"] = color
                
            self.log.debug("LIFX payload: {}".format(payload))

            try:    
                res = requests.put("https://api.lifx.com/v1/lights/group:{}/state".format(self.name), 
                    headers=self.req_header, data=payload)
                body = res.json()
                self.log.debug("LIFX response body: {}".format(body))

                if res.ok:
                    results = body["results"]
                    for device in results:
                        if device["status"] == "timed_out":
                            raise DeviceGroupError("Device {} timed out".format(device["id"]))
                else:
                    raise Exception(res.json()["error"])
            except requests.exceptions.RequestException as re:
                raise DeviceGroupError(re)
            except Exception as e:
                raise e

        return self.do(_set_hsbk, hsbk, transition_seconds)

    def get_hsbk(self) -> list:
        def _get_hsbk():
            hsbk = []

            try:
                response = requests.get("https://api.lifx.com/v1/lights/group:{}".format(self.name), headers=self.req_header)
                data = response.json()

                for device in data:
                    hsbk = device["color"] | {"brightness": round(device["brightness"], utils.HSBK_FLT_PRECISION)}
            except requests.exceptions.RequestException as re:
                raise DeviceGroupError(re)
            except Exception as e:
                raise e

            return hsbk

        return self.do(_get_hsbk)

    def _normalize_to_range(self, x, old_r_min, old_r_max, new_r_min, new_r_max):
        return round(((x - old_r_min) / (old_r_max - old_r_min)) * (new_r_max - new_r_min) + new_r_min, 2)

    def __repr__(self) -> str:
        return ", ".join(
            [
                "LIFX::{}::{}".format(device.get_ip_addr(), device.get_mac_addr())
                for device in self.devices
            ]
        )
