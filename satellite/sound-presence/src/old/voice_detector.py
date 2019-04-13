import sounddevice
import numpy
import json
import time
import paho.mqtt.client as mqtt

class VoiceDetector():


    def __init__(self):
        self.name = "development_1"
        self.server = "mqtt"
        self.topic = "SOUNDPRESENCE"
        self.notifyDifference = 0.2

        self.sound_level = 0
        self.sound_level_min = 100
        self.sound_level_max = 0

        self.client = mqtt.Client(self.name)
        self.client.connect(self.server, 1883, 60)
        self.client.publish(self.getTopic("ONLINE"))
        self.client.loop_start()

        self.collect_samples()


    def collect_samples(self):
        with sounddevice.Stream(callback=self.messure):
            sounddevice.sleep(100)
        self.check_sound_level()


    def messure(self, indata, outdata, frames, time, status):
        current_sound_level = numpy.linalg.norm(indata) * 1000

        if current_sound_level > self.sound_level:
            self.sound_level = current_sound_level


    def getNotifyLevel(self):
        return self.sound_level_min + self.sound_level_min * self.notifyDifference


    def check_sound_level(self):
        if self.sound_level > 0 and self.sound_level < self.sound_level_min:
            self.sound_level_min = self.sound_level

        if self.sound_level > self.sound_level_max:
            self.sound_level_max = self.sound_level

        if self.sound_level > self.getNotifyLevel():
            print("High sound level detected")
            self.send_data()

        self.collect_samples()


    def send_data(self):
        if self.sound_level > 0:
            print("Sending data: %s" % self.sound_level)
            self.client.publish(self.getTopic("LEVEL"), json.dumps({
                "level": self.sound_level,
                "min": self.sound_level_min,
                "max": self.sound_level_max
            }))
            self.sound_level = 0
            time.sleep(1000)


    def getTopic(self, topic):
        return self.topic + "/%s" % topic


if __name__ == "__main__":
    voice_detector = VoiceDetector()
