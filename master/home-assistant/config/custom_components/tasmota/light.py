import voluptuous as vol
import logging
import ptvsd
import asyncio

<<<<<<< HEAD
from homeassistant.core import callback

=======
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd
import homeassistant.components.mqtt as mqtt
import homeassistant.helpers.config_validation as cv

from homeassistant.components.mqtt.light.schema_basic import ( 
<<<<<<< HEAD
    MqttLight
=======
    MqttLight,
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
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd
)

from homeassistant.const import ( 
    CONF_PLATFORM, 
    CONF_NAME
)

from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC
)

from . import motion
from . import configurator

from ..sarah import (
    CONF_INTERNAL_ID,
    CONF_TYPE
)

<<<<<<< HEAD
# centralize
_EVENT_SENSORIO_MOTION = "sensorio:motion"
_TOPIC_MOTION_EVENT = "motion_event_topic"
=======
_TYPE_COMMON = "common"
_CONF_AUTO_CONFIG = "auto_config"

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
            "PowerOnState": 0,
            "LedState": 0,
            "Sleep": 0,
            "SetOption31": 1           # Disable status LED blinking during Wi-Fi and MQTT connection problems. (1 is ON )
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
        _CONF_AUTO_CONFIG: {}
    },
    "touch": {
        _CONF_AUTO_CONFIG: {
            "SetOption13": 1,         # Will react instantly
            "SetOption32": 10         # HOLD after 1s
        }
    },
    "switch": {
        _CONF_AUTO_CONFIG: {
            "SetOption13": 1,
            "SetOption15": 0           # 0 is basic PWM control, no dimmer and color
        }
    }
}
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_INTERNAL_ID): cv.string,
    vol.Required(CONF_TYPE): cv.string
}, extra = vol.ALLOW_EXTRA)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Tasmota light through configuration.yaml."""
    await _async_setup_entity(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities, config_entry=None, discovery_hash=None):
    internal_id = config.get(CONF_INTERNAL_ID, None)
    async_add_entities([await TasmotaLight(hass, config_entry, internal_id, discovery_hash).create(config)])

class TasmotaLight(MqttLight):

    def __init__(self, hass, config_entry, internal_id, discovery_hash):
        """Initializes a Tasmota light."""
<<<<<<< HEAD
        self._internal_id = internal_id
        self._hass = hass
        self._config_entry = config_entry
        self._discovery_hash = discovery_hash
=======
        self._internal_id = config.get(CONF_INTERNAL_ID, None)
        self._hass = hass
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd
        self._loop = asyncio.new_event_loop()
        self._config = self._get_config(config)
        _LOGGER.info("Initializing %s" % self._internal_id)
<<<<<<< HEAD
        asyncio.set_event_loop(self._loop)

    async def create(self, config):
        self.configurator = configurator.Configurator(self._hass, config)
        self._config = self.configurator.getConfig()
        MqttLight.__init__(self, config, self._config_entry, self._discovery_hash)

        self.refresh()

        if "motion_iterval" in self._config:
            self.motionTimer = motion.Timer(self._hass, _LOGGER, self._config, self)

        if "motion_event_topic" in self._config:
            await self.simulate_sensorio_motion()

        return self
=======
        MqttLight.__init__(self, self._config, config_entry, discovery_hash)
        asyncio.set_event_loop(self._loop)

        self.refresh()
        self.configureDevice()

        if "motion_iterval" in config:
            self.motionTimer = motion.Timer(hass, _LOGGER, config, self)

    def _get_config(self, config):
        self.set_config(config, _TYPES.get(_TYPE_COMMON))
        if CONF_TYPE in config and config.get(CONF_TYPE) in _TYPES:
            self.set_config(config, _TYPES.get(config.get(CONF_TYPE)))
        return config

    def set_config(self, config, data):
        _data = self._prepareConfigData(data)
        if "multipress" in config:
            _data[_CONF_AUTO_CONFIG] = {
                **_data[_CONF_AUTO_CONFIG],
                **self._prepareConfigData(_CONF_MULTIPRESS)
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
    
    def _prepareConfigData(self, data):
        _data = {}
        _environment_values = {
            "internal_id": self._internal_id
        }
        for key in data:
            _computedValue = data.get(key)
            if isinstance(_computedValue, str):
                _computedValue = _computedValue.format(**_environment_values)
            elif isinstance(_computedValue, dict):
                _computedValue = self._prepareConfigData(_computedValue)
            _data.setdefault(key, _computedValue)
        return _data
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd

    def refresh(self):
        _request_topics = [
            self._config.get(CONF_COMMAND_TOPIC)
        ]
        for _request_topic in _request_topics:
            mqtt.async_publish(self._hass, _request_topic, "")

<<<<<<< HEAD
    async def simulate_sensorio_motion(self):

        @callback
        def event_message(topic, payload, qos):
            """Handle received MQTT message."""
            _data = "0"
            if payload == "ON":
                _data = "1"
            _LOGGER.debug("Simulating sensorio event: %s, %s, %s" % (self._internal_id, _EVENT_SENSORIO_MOTION, _data))
            self._hass.bus.async_fire(_EVENT_SENSORIO_MOTION, {
                "data": _data,
                "internal_id": self._internal_id
            })
            
        if self._config.get(_TOPIC_MOTION_EVENT):
            _LOGGER.debug("Simulating sensorio motion on tasmota: %s, %s" % (self._internal_id, self._config.get(_TOPIC_MOTION_EVENT)))
            await mqtt.async_subscribe(self._hass, self._config.get(_TOPIC_MOTION_EVENT), event_message)
=======
    def configureDevice(self):
        _auto_config = self._config.get(_CONF_AUTO_CONFIG)
        for _conf_topic in _auto_config:
            _conf_value = _auto_config.get(_conf_topic)
            _conf_topic = "cmnd/%s/%s" % (self._internal_id, _conf_topic)
            mqtt.async_publish(self._hass, _conf_topic, _conf_value)
>>>>>>> 23050ec8e152904322783ac24d3102681dd73bcd

    def turn_on(self):
        self._loop.run_until_complete(self.async_turn_on())
    
    def turn_off(self):
        self._loop.run_until_complete(self.async_turn_off())
