import json
import alsaaudio
import audioop
import threading
import time
import paho.mqtt.client as mqtt

class SoundPresence():


    def __init__(self):
        self.name = "development_1"
        self.server = "localhost"
        self.topic = "SOUNDPRESENCE"
        self.notifyDifference = 0.1

        self.sound_level = 0
        self.sound_level_min = 1000
        self.sound_level_max = 0

        self.client = mqtt.Client(self.name)
        self.client.connect(self.server, 1883, 60)
        self.client.publish(self.getTopic("ONLINE"))
        self.client.loop_start()

        self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL)
        self.inp.setchannels(1)
        self.inp.setrate(8000)
        self.inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.inp.setperiodsize(128)

        self.collect_samples()


    def collect_samples(self):
        print("Collecting samples")
        # read data from device
        l, data = self.inp.read()
        if l:
            # return the maximum of the absolute value of all samples in a fragment.
            sound_level = audioop.rms(data, 2)
            print(sound_level)
            self.check_sound_level(sound_level)

        threading.Timer(5.0, self.collect_samples).start()


    def getNotifyLevel(self):
        return self.sound_level_min + self.sound_level_min * self.notifyDifference


    def check_sound_level(self, sound_level):
        if sound_level > 0:
            if sound_level > self.getNotifyLevel():
                print("High sound level detected")
                self.send_data()

            if sound_level < self.sound_level_min:
                print("New minimum: %s" % self.sound_level)
                self.sound_level_min = sound_level

            if sound_level > self.sound_level_max:
                print("New maximum: %s" % self.sound_level)
                self.sound_level_max = sound_level


    def send_data(self):
        if self.sound_level > 0:
            print("Sending data: %s" % self.sound_level)
            self.client.publish(self.getTopic("LEVEL"), json.dumps({
                "level": self.sound_level,
                "min": self.sound_level_min,
                "max": self.sound_level_max
            }))


    def getTopic(self, topic):
        return self.topic + "/%s" % topic


if __name__ == "__main__":
    sound_presence = SoundPresence()
