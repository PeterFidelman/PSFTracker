import pyopl
import pyaudio

# ----------------------------------------------------------------------------
# OPL2 emulator using pyopl and pyaudio
# ============================================================================

class OPL2:
	def __init__(self):
		# ----- No sane person would change these values. -----
		self.samplesPerSecond = 44100
		self.samplesPerBuffer = 44100/70/2	# Buffer half a tick.
		self.bytesPerSample = 2
		self.channels = 2

		# ----- Set up PyOPL. -----
		self.opl = pyopl.opl(
			self.samplesPerSecond,
			self.bytesPerSample,
			self.channels)

		# The buffer of samples that PyOPL fills and PyAudio plays.
		self.buf = bytearray(
			self.samplesPerBuffer *
			self.bytesPerSample *
			self.channels)

		# This points to the same memory as self.buf.
		self.pyaudio_buf = buffer(self.buf)

		# ----- Set up PyAudio. -----
		self.audio = pyaudio.PyAudio()

		# The stream through which PyAudio will play the sound.
		self.pyaudio_stream = self.audio.open(
			format = self.audio.get_format_from_width(
				self.bytesPerSample),
			channels = self.channels,
			rate = self.samplesPerSecond,
			output = True)

	def writeReg(self, reg, value):
		self.opl.writeReg(reg, value)
	
	def playHalfATick(self):
		self.opl.getSamples(self.buf)
		self.pyaudio_stream.write(self.pyaudio_buf)
	
	def play(self):
		# One 70Hz tick = two bufferfuls.
		self.playHalfATick()
		self.playHalfATick()
