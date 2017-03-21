import pyopl
import alsaaudio
import time

# ----------------------------------------------------------------------------
# OPL2 emulator using pyopl and pyaudio
# ============================================================================

class OPL2:
	def __init__(self):
		# ----- No sane person would change these values. -----
		self.samplesPerSecond = 44100
		self.samplesPerBuffer = self.samplesPerSecond/70/2	# Buffer half a tick
		self.bytesPerSample = 2
		self.channels = 1

		# ----- Set up PyOPL. -----
		self.opl = pyopl.opl(
			self.samplesPerSecond,
			self.bytesPerSample,
			self.channels)

		# The buffer of samples that PyOPL fills and the soundcard empties
		self.buf = bytearray(
			self.samplesPerBuffer *
			self.bytesPerSample *
			self.channels)

		self.pyaudio_buf = buffer(self.buf)

		#self.out = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NONBLOCK)
		self.out = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL)
		self.out.setchannels(self.channels)
		self.out.setrate(self.samplesPerSecond)
		self.out.setformat(alsaaudio.PCM_FORMAT_S16_LE)

	def writeReg(self, reg, value):
		self.opl.writeReg(reg, value)
	
	def playHalfATick(self):
		self.opl.getSamples(self.buf)
		#self.pyaudio_stream.write(self.pyaudio_buf)
		self.out.write(self.pyaudio_buf)
	
	def play(self):
		# One 70Hz tick = two bufferfuls.
		self.playHalfATick()
		self.playHalfATick()
		#time.sleep(.6/70)
