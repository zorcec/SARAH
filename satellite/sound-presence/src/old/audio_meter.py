import json
import subprocess
import sys
import os
import paho.mqtt.client as mqtt

class SoundPresence():


    def __init__(self):
        self.name = "development_1"
        self.server = "localhost"
        self.topic = "SOUNDPRESENCE"
        self.notifyDifference = 0.2
        self.debug = False

        self.sound_level_min = 10000
        self.sound_level_max = 0

        self.client = mqtt.Client(self.name)
        self.client.connect(self.server, 1883, 60)
        self.client.publish(self.getTopic("ONLINE"))
        self.client.loop_start()

        self.messure()


    def messure(self):
        sound_level_response = os.popen("soundmeter --seconds 1").read()
        sound_level = int(sound_level_response[0:-8].strip())
        if self.debug:
            print("Detected level: %s" % sound_level)
        self.check_sound_level(sound_level)
        self.messure()


    def getNotifyLevel(self):
        return self.sound_level_min + self.sound_level_min * self.notifyDifference


    def check_sound_level(self, sound_level):
        if sound_level > 0:
            if sound_level < self.sound_level_min:
                if self.debug:
                    print("New minimum: %s" % sound_level)
                self.sound_level_min = sound_level

            if sound_level > self.sound_level_max:
                if self.debug:
                    print("New maximum: %s" % sound_level)
                self.sound_level_max = sound_level

        self.send_data(sound_level)


    def send_data(self, sound_level):
        if sound_level > 0:
            if self.debug:
                print("Sending data: %s" % sound_level)
            self.client.publish(self.getTopic("LEVEL"), json.dumps({
                "level": sound_level,
                "min": self.sound_level_min,
                "max": self.sound_level_max
            }))

            if sound_level > self.getNotifyLevel():
                print("Sound presence detected")
                self.client.publish(self.getTopic("EVENT/PRESENCE"), json.dumps({
                    "data": sound_level
                }))


    def getTopic(self, topic):
        return self.topic + "/%s" % topic


if __name__ == "__main__":
    sound_presence = SoundPresence()
