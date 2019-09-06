import time
import threading

from . import light

_CONF_MOTION_INTERVAL = "motion_iterval"

class Timer():

    def __init__(self, hass, logger, config):
        self._hass = hass
        self._logger = logger
        self._config = config
        self._motion_interval = int(self._config[_CONF_MOTION_INTERVAL])
        self._internal_id = self._config[light.CONF_INTERNAL_ID]
        self._logger.info("Initializing motion timer: %s, %is" % (self._internal_id, self._motion_interval))
        self.last_motion_time = time.time()
        self.interval_time = time.time()
        self.start_timers()
        #hass.bus.listen(self._config["sensor.%s"], self.motion)

    def motion(self, entity, attribute, old, new, kwargs):
        self._logger.debug("Motion detected, time difference: %ss" % self.time_difference(self.last_motion_time))
        self.last_motion_time = time.time()
        self.interval_time = time.time()
        self.restart_timers()

    def time_difference(self, sinceTime):
        return time.time() - sinceTime

    def interval_finished(self):
        self._logger.debug("Interval was finished: %s" % self._config["internal_id"])
        self.interval_timer = None

    def restart_timers(self):
        self._logger.debug("Restarting interval: %s" % self._config["internal_id"])
        if self.interval_timer is not None:
            self.interval_timer.cancel()
            self.interval_timer = None

        self.start_timers()

    def start_timers(self):
        self.interval_timer = threading.Timer(self._motion_interval, self.interval_finished)
        self.interval_timer.start()