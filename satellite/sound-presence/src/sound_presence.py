import sys
sys.path.insert(0, "./lib/pyAudioAnalysis/pyAudioAnalysis")

import paho.mqtt.publish as publish
import os, alsaaudio, time, audioop, numpy, scipy
import scipy.io.wavfile as wavfile
import audioFeatureExtraction as aF
import audioTrainTest as aT
import audioSegmentation as aS
import json
import yaml

class SoundPresence():

	def initialize(self):
		self.readConfig()

		self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)

		self.inp.setchannels(1)
		self.inp.setrate(self.Fs)
		self.inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
		self.inp.setperiodsize(512)

		self.pwmPrevious = 0
		self.pwmMin = 0
		self.pwmMax = 0

		while True:
			data, minPwmValue, maxPwmValue = self.capture()
			self.analyzePwm(minPwmValue, maxPwmValue)
			#self.analyzeFeatures(data)
			#self.saveToFile(data)


	def readConfig(self):
		with open("config.yaml", "r") as stream:
			try:
				config = yaml.load(stream)
				self.presenceDifferenceTrigger = config.get("presence_difference_trigger", 1.5)
				self.presenceMinMultiplayerTrigger = config.get("presence_min_multiplayer_trigger", 3)
				self.midTermBufferSizeSec = config.get("mid_term_buffer_size_sec", 1)
				self.duration = config.get("duration", 1)
				self.Fs = config.get("fs", 8000)
				self.outputDirectory = config.get("output_directory", "../temp")
				self.deviceName = config.get("device_name", "development_1")
				self.mqttHost = config.get("mqtt_host", "localhost")
			except yaml.YAMLError as exc:
				print(exc)


	def notifyPresence(self, target, pwm):
		dataString = "{ \"min\":  %s, \"max\": %s, \"target\": %s, \"current\": %s }" % (self.pwmMin, self.pwmMax, target, pwm)
		publish.single("/%s/audio-presence" % self.deviceName, dataString, hostname=self.mqttHost)


	def analyzePwm(self, min, max):
		differenceTarget = self.pwmPrevious * self.presenceDifferenceTrigger
		maximumTarget = self.presenceMinMultiplayerTrigger * self.pwmMin
		target = numpy.min([differenceTarget, maximumTarget])
		if self.pwmMin == 0 or min < self.pwmMin:
			self.pwmMin = min
		if self.pwmMax == 0 or max > self.pwmMax:
			self.pwmMax = max
		if max > target:
			self.notifyPresence(target, max)
			print("min: %s, max: %s, target: %s, current: %s" % (self.pwmMin, self.pwmMax, target, max))
		self.pwmPrevious = max


	def analyzeFeatures(self, data):
		values, features = aF.stFeatureExtraction(data, self.Fs, 0.1 * self.Fs, 0.1 * self.Fs)
		for index, feature in enumerate(features):
			print("%s:\t%s" % (feature, features[index]))


	def saveToFile(self, data):
		filePath = os.path.abspath("%s/%s.wav" % (self.outputDirectory, time.time()))
		wavfile.write(filePath, self.Fs, numpy.int16(data))


	def capture(self):
		midTermBufferSize = int(self.midTermBufferSizeSec * self.Fs)
		allData = []
		maxPwmValue = 0
		minPwmValue = 0
		midTermBuffer = []
		curWindow = []

		while len(allData) < self.duration * self.Fs:
			time.sleep(0.01)
			l, data = self.inp.read()
			if l:
				for i in range(l):
					curWindow.append(audioop.getsample(data, 2, i))		
				if (len(curWindow) + len(midTermBuffer) > midTermBufferSize):
					samplesToCopyToMidBuffer = midTermBufferSize - len(midTermBuffer)
				else:
					samplesToCopyToMidBuffer = len(curWindow)
				midTermBuffer = midTermBuffer + curWindow[0:samplesToCopyToMidBuffer];
				del(curWindow[0:samplesToCopyToMidBuffer])

				pwm = audioop.rms(data, 2)
				if pwm < minPwmValue or minPwmValue == 0:
					minPwmValue = pwm
				if pwm > maxPwmValue or maxPwmValue == 0:
					maxPwmValue = pwm

			if len(midTermBuffer) == midTermBufferSize:
				allData = allData + midTermBuffer
				midTermBuffer = []

		return allData, minPwmValue, maxPwmValue


if __name__ == '__main__':
	soundPresence = SoundPresence()
	soundPresence.initialize()
