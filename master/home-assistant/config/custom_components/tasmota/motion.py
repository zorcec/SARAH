import time
import threading
import ptvsd
import asyncio

from homeassistant.core import callback

ptvsd.enable_attach()
#ptvsd.wait_for_attach()

from . import light

_CONF_MOTION_INTERVAL = "motion_iterval"
_CONF_MOTION_TRACKERS = "motion_trackers"
_EVENT_SENSORIO_MOTION = "sensorio:motion"

class Timer():

    def __init__(self, hass, logger, config, device):
        self._hass = hass
        self._logger = logger
        self._config = config
        self._device = device
        self._motion_interval = int(self._config[_CONF_MOTION_INTERVAL])
        self._internal_id = self._config[light.CONF_INTERNAL_ID]
        self._logger.info("Initializing motion timer: %s, %is" % (self._internal_id, self._motion_interval))
        self._interval_timer = None
        self._last_motion_time = time.time()
        self._interval_time = time.time()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self.listen_for_events()
        self.start_timers()

    def turn_on(self):
        self._loop.run_until_complete(self._device.async_turn_on())
    
    def turn_off(self):
        self._loop.run_until_complete(self._device.async_turn_off())

    def listen_for_events(self):
        _motion_trackers = self._config[_CONF_MOTION_TRACKERS]

        def motion(event):
            internal_id = event.data.get("internal_id")
            _is_movement = True if event.data.get("data") == "1" else False
            _is_relevant = False
            for _motion_tracker in _motion_trackers:
                if internal_id == _motion_tracker:
                    """Relevant motion"""
                    self.turn_on()
                    _is_relevant = True
            if _is_relevant:
                if _is_movement:
                    self._logger.debug("Motion detected")
                    self.stop_timers()
                else:
                    self._logger.debug("Starting countdown")
                    self._last_motion_time = time.time()
                    self._interval_time = time.time()
                    self.restart_timers()

        self._hass.bus.async_listen(_EVENT_SENSORIO_MOTION, motion)

    def time_difference(self, sinceTime):
        return time.time() - sinceTime

    def interval_finished(self):
        self._logger.debug("Interval was finished: %s" % self._config["internal_id"])
        self._interval_timer = None
        self.turn_off()

    def restart_timers(self):
        self._logger.debug("Restarting interval: %s" % self._config["internal_id"])
        self.stop_timers()
        self.start_timers()

    def start_timers(self):
        self._interval_timer = threading.Timer(self._motion_interval, self.interval_finished)
        self._interval_timer.start()

    def stop_timers(self):
        if self._interval_timer is not None:
            self._interval_timer.cancel()
            self._interval_timer = None