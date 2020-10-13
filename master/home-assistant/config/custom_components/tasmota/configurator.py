import voluptuous as vol
import logging
import ptvsd
import urllib
import json

from homeassistant.core import callback
import homeassistant.components.mqtt as mqtt

from homeassistant.components.mqtt.light.schema_basic import ( 
    DEFAULT_ON_COMMAND_TYPE,
    CONF_BRIGHTNESS_SCALE,
    CONF_ON_COMMAND_TYPE,
    CONF_BRIGHTNESS_COMMAND_TOPIC,
    CONF_BRIGHTNESS_STATE_TOPIC,
    CONF_BRIGHTNESS_VALUE_TEMPLATE,
    CONF_COLOR_TEMP_COMMAND_TOPIC,
    CONF_COLOR_TEMP_STATE_TOPIC,
    CONF_WHITE_VALUE_STATE_TOPIC,
    CONF_WHITE_VALUE_COMMAND_TOPIC,
    CONF_WHITE_VALUE_SCALE,
    CONF_RGB_COMMAND_TOPIC,
    ATTR_BRIGHTNESS
)

from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC,
    CONF_AVAILABILITY_TOPIC,
    CONF_QOS,
    CONF_RETAIN,
    CONF_STATE_TOPIC,
    CONF_UNIQUE_ID,
    CONF_PAYLOAD_NOT_AVAILABLE,
    CONF_PAYLOAD_AVAILABLE
)

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME,
    CONF_BRIGHTNESS,
    CONF_COLOR_TEMP,
    CONF_DEVICE,
    CONF_EFFECT,
    CONF_HS,
    CONF_NAME,
    CONF_OPTIMISTIC,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
    CONF_RGB,
    CONF_STATE,
    CONF_VALUE_TEMPLATE,
    CONF_WHITE_VALUE,
    CONF_XY
)

from ..tasmota_information import (
    EVENT_TASMOTA_DETECTED,
    STATUS_NETWORK,
    STATUS_LOG,
    getDeviceByMac
)

from ..sarah import (
    CONF_INTERNAL_ID,
    CONF_TYPE
)

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

CONF_MAC_ADDRESS = "mac_address"

_TYPE_COMMON = "common"
_CONF_AUTO_CONFIG = "auto_config"
_ATTR_AUTO_CONFIG = "auto_configure"
_ATTR_CUSTOMIZE = "customize"

_AUTOCONFIGURE_ACTIVE = False

# cannot be checked generic way
_SPECIAL_CONFIG = {
    "SSID1": "IoT",
    "Password1": "sarah_is_awesome",
    "SSID2": "SARAH",
    "Password2": "sarah",
    "FriendlyName": "{internal_id}",
}

_INIT_CONFIG = {
    "MqttHost": "192.168.0.101",
    "MqttUser": "smart_device",
    "MqttClient": "{internal_id}",
    "Topic": "{internal_id}",
    "OtaUrl": "http://192.168.0.100:8888/840.bin",
    "GroupTopic": "sonoff"
}

_CONF_MULTIPRESS = {
    "StateText3": "DOUBLE",
    "ButtonTopic": "{internal_id}/multipress",
    "SetOption1": 1,          # Multipress support
    "SetOption11": 1,         # Multipress support
    "SetOption13": 0,         # Will not react instantly
    "SetOption32": 10         # HOLD after 1s
}

_TYPES = {
    _TYPE_COMMON: {
        CONF_OPTIMISTIC: False,
        CONF_RETAIN: False,
        CONF_QOS: 1,
        CONF_COMMAND_TOPIC: "cmnd/{internal_id}/POWER",
        CONF_STATE_TOPIC: "stat/{internal_id}/POWER",
        CONF_AVAILABILITY_TOPIC: "tele/{internal_id}/LWT",
        CONF_PAYLOAD_ON: "ON",
        CONF_PAYLOAD_OFF: "OFF",
        CONF_PAYLOAD_AVAILABLE: "Online",
        CONF_PAYLOAD_NOT_AVAILABLE: "Offline",
        CONF_ON_COMMAND_TYPE: DEFAULT_ON_COMMAND_TYPE,
        _CONF_AUTO_CONFIG: {
            "Timezone": 2,
            "Longitude":2.294442,
            "Latitude":48.858360,
            "PowerOnState": 0,
            "LedState": 0,
            "Sleep": 250,
            "SerialLog": 0,
            "WiFiPower": 8,
            "TelePeriod": 55,
            "SaveData": 3600,          # Save every hour (max)
            "SetOption31": 0           # Disable status LED blinking during Wi-Fi and MQTT connection problems. (1 is ON )
        }
    },
    "led_controller_rgb": {
        CONF_BRIGHTNESS_SCALE: 100,
        CONF_BRIGHTNESS_COMMAND_TOPIC: "cmnd/{internal_id}/DIMMER",
        CONF_RGB_COMMAND_TOPIC: "cmnd/{internal_id}/Color",
        _CONF_AUTO_CONFIG: {
            "PwmFrequency": 1760
        }
    },
    "led_controller_rgbw": {
        CONF_BRIGHTNESS_SCALE: 100,
        CONF_BRIGHTNESS_COMMAND_TOPIC: "cmnd/{internal_id}/DIMMER",
        CONF_RGB_COMMAND_TOPIC: "cmnd/{internal_id}/Color",
        CONF_WHITE_VALUE_COMMAND_TOPIC: "cmnd/{internal_id}/Channel4" ,
        CONF_WHITE_VALUE_SCALE: 100,
        _CONF_AUTO_CONFIG: {
            "PwmFrequency": 1760
        }
    },
    "dimmer": {
        CONF_BRIGHTNESS_SCALE: 100,
        CONF_BRIGHTNESS_COMMAND_TOPIC: "cmnd/{internal_id}/DIMMER",
        _CONF_AUTO_CONFIG: {
            "PwmFrequency": 1760,
            "DimmerRange": "25,100"
        }
    },
    "touch": {
        _CONF_AUTO_CONFIG: {
            "SetOption13": 1,         # Will react instantly
            "SetOption32": 10         # HOLD after 1s
        }
    },
    "switch": {
        _CONF_AUTO_CONFIG: {}
    }
}

class Configurator():

    def __init__(self, hass, config):
        self._hass = hass
        self._logger = logging.getLogger(__name__)
        self._internal_id = config.get(CONF_INTERNAL_ID)
        self._config = self._get_config(config)
        self._mac_address = self._config.get(CONF_MAC_ADDRESS)
        self._should_auto_configure = config.get(_ATTR_AUTO_CONFIG, False)

        if self._mac_address is not None:
            self._device_information = getDeviceByMac(self._mac_address)
            if self._device_information is None:
                self._listen_for_new_devices()
            else:
                self._configure_device()

    def getConfig(self):
        return self._config

    def _get_config(self, config):
        self.set_config(config, _TYPES.get(_TYPE_COMMON))
        if CONF_TYPE in config and config.get(CONF_TYPE) in _TYPES:
            self.set_config(config, _TYPES.get(config.get(CONF_TYPE)))
        return config

    def set_config(self, config, data):
        _data = self._prepareConfigData(config, data)
        if "multipress" in config:
            _data[_CONF_AUTO_CONFIG] = {
                **_data[_CONF_AUTO_CONFIG],
                **self._prepareConfigData(config, _CONF_MULTIPRESS)
            }
        if "customize" in config:
            _data[_CONF_AUTO_CONFIG] = {
                **_data[_CONF_AUTO_CONFIG],
                **self._prepareConfigData(config, config.get(_ATTR_CUSTOMIZE, {}))
            }
        for key in _data:
            _value = _data.get(key)
            if isinstance(_value, dict):
                config[key] = {
                    **config.get(key, {}),
                    **_value
                }
            else:
                config.setdefault(key, _value)
    
    def _prepareConfigData(self, config, data):
        _data = {}
        _environment_values = {
            "internal_id": self._internal_id
        }
        for key in data:
            _computedValue = data.get(key)
            if isinstance(_computedValue, str):
                _computedValue = _computedValue.format(**_environment_values)
            elif isinstance(_computedValue, dict):
                _computedValue = self._prepareConfigData(config, _computedValue)
            _data.setdefault(key, _computedValue)

        return _data

    def _configure_device(self):
        _backlogCmd = ""

        _init_config = self._get_init_config()
        _backlogCmd += self._get_backlog_cmd(_init_config)

        _auto_config = self._config.get(_CONF_AUTO_CONFIG)
        _backlogCmd += self._get_backlog_cmd(_auto_config)

        _special_config = self._get_special_config()
        _backlogCmd += self._get_backlog_special_cmd(_special_config)

        if (_AUTOCONFIGURE_ACTIVE or self._should_auto_configure) and _backlogCmd is not "":
            self._configure_via_http(_backlogCmd)

    def _configure_via_http(self, cmd):
        _ip_address = self._device_information.get(STATUS_NETWORK, {}).get("IPAddress")
        _url = "http://%s/cm?cmnd=backlog %s" % (_ip_address, cmd)
        _clean_url = self._encode_url(_url)
        self._logger.debug("Url: %s" % _clean_url)
        urllib.request.urlopen(_clean_url, timeout=5)

    def _encode_url(self, url):
         return url.replace(" ", "%20").replace(";", "%3B")

    def _configure_via_mqtt(self, cmd):
        _conf_topic = "cmnd/%s/backlog" % self._config.get(CONF_INTERNAL_ID)
        mqtt.async_publish(self._hass, _conf_topic, cmd)

    def _get_init_config(self):
        return self._prepareConfigData(self._config, _INIT_CONFIG)

    def _get_special_config(self):
        return self._prepareConfigData(self._config, _SPECIAL_CONFIG)

    def _get_backlog_cmd(self, config):
        _backlogCmd = ""
        _ip_address = self._device_information.get(STATUS_NETWORK, {}).get("IPAddress")
        for _current_config_name in config:
            _current_config_value = config[_current_config_name]
            _option_found = False
            for category in self._device_information:
                category_info = self._device_information.get(category)
                for _config_name in category_info:
                    _config_value = category_info.get(_config_name)
                    if _current_config_name == _config_name:
                        _option_found = True
                        if _current_config_value != _config_value:
                            # self._logger.debug("New configuration for %s: %s, %s => %s" % (self._internal_id, _current_config_name, _config_value, _current_config_value))
                            _backlogCmd += "%s %s;" % (_config_name, _current_config_value)
            if _option_found == False:
                # self._logger.debug("Configuration not found for %s: %s, %s" % (self._internal_id, _current_config_name, _current_config_value))
                _backlogCmd += "%s %s;" % (_current_config_name, _current_config_value)
            

        return _backlogCmd

    def _get_backlog_special_cmd(self, config):
        _backlogCmd = ""

        _ip_address = self._device_information.get(STATUS_NETWORK, {}).get("IPAddress")
        _configured_ssids = self._device_information.get(STATUS_LOG, {}).get("SSId")
        if not config.get("SSID1") in _configured_ssids or not config.get("SSID2") in _configured_ssids:
            self._logger.debug("New SSID configuration for %s" % (self._internal_id))
            _backlogCmd += "SSID1 %s;" % config.get("SSID1")
            _backlogCmd += "Password1 %s;" % config.get("Password1")
            _backlogCmd += "SSID2 %s;" % config.get("SSID2")
            _backlogCmd += "Password2 %s;" % config.get("Password2")

        _configured_friendly_names = self._device_information.get("Status", {}).get("FriendlyName", [])
        if not config.get("FriendlyName") in _configured_friendly_names:
            _backlogCmd += "FriendlyName %s;" % config.get("FriendlyName")

        return _backlogCmd


    def _listen_for_new_devices(self):

        def tasmota_detected(event):
            _mac = event.data.get("mac")
            _data = event.data.get("data")
            if _mac == self._mac_address:
                self._device_information = getDeviceByMac(self._mac_address)
                self._configure_device()

        self._hass.bus.async_listen(EVENT_TASMOTA_DETECTED, tasmota_detected)
