import appdaemon.plugins.hass.hassapi as hass
import time
import threading

class Test(hass.Hass):

  def initialize(self):
    self.log("Initializing")
    self.last_motion_time = time.time()
    self.presence_time = time.time()
    self.listen_state(self.motion, "sensor.development_sensorio_motion", new="1")
    self.start_timers()

  def motion(self, entity, attribute, old, new, kwargs):
    self.log("Motion detected, time difference: %ss" % self.time_difference(self.last_motion_time))
    self.last_motion_time = time.time()
    self.presence_time = time.time()
    self.restart_timers();

  def time_difference(self, sinceTime):
    return time.time() - sinceTime

  def short_presence(self):
    self.log("Short presence is over")
    self.short_presence_timer = None

  def long_presence(self):
    self.log("Long presence is over")
    self.long_presence_timer = None

  def restart_timers(self):
    self.log("Restarting presence timers")

    if self.short_presence_timer is not None:
      self.short_presence_timer.cancel()
      self.short_presence_timer = None

    if self.long_presence_timer is not None:
      self.long_presence_timer.cancel()
      self.long_presence_timer = None

    self.start_timers()

  def start_timers(self):
    self.short_presence_timer = threading.Timer(10.0, self.short_presence)
    self.long_presence_timer = threading.Timer(15.0, self.long_presence)
    self.short_presence_timer.start()
    self.long_presence_timer.start()
