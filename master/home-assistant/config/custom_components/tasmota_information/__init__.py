import voluptuous as vol
import logging
import urllib.request
import urllib.parse
import json
import ptvsd
import threading

from ipaddress import ip_address

from ..sarah import (
    CONF_INTERNAL_ID
)

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

EVENT_TASMOTA_DETECTED = "new_tasmota_detected"
STATUS_MQTT = "StatusMQT"
STATUS_NETWORK = "StatusNET"
STATUS_LOG = "StatusLOG"

_logger = logging.getLogger(__name__)
_information = {}

def collect_information(hass, config):
    _config = config.get("tasmota_configurator")
    _logger.info("Gathering information ...")
    task = threading.Thread(target=_get_information, args=(hass, config))
    task.start()

def getDeviceByMac(mac_address):
    return _information.get(mac_address)

def _get_information(hass, config):
    _ip_addreses = _generate_ips(config.get("ip_range"))
    for _ip_address in _ip_addreses:
        try:
            # _logger.debug("Checking: %s" % _ip_address)
            response = urllib.request.urlopen("http://%s/cm?cmnd=STATUS%%200" % _ip_address, timeout=1)
            _data = json.loads(response.read())
            _mac = _data.get(STATUS_NETWORK, {}).get("Mac")
            _information[_mac] = _data
            _notify_new_device_detected(_ip_address, _data, hass)
        except:
            pass

def _notify_new_device_detected(ip_address, data, hass):
    _logger.info("New device detected: %s" % data.get(STATUS_MQTT).get("MqttClient"))
    _mac = data.get(STATUS_NETWORK, {}).get("Mac")
    hass.bus.async_fire(EVENT_TASMOTA_DETECTED, {
            "data": data,
            "ip": ip_address,
            "mac": _mac
        })

def _generate_ips(ip_range):
    _parts = ip_range.split('-')
    start_int = int(ip_address(_parts[0]).packed.hex(), 16)
    end_int = int(ip_address(_parts[1]).packed.hex(), 16)
    return [ip_address(ip).exploded for ip in range(start_int, end_int)]

async def async_setup(hass, config):
    collect_information(hass, config.get("tasmota_information"))
    return True
