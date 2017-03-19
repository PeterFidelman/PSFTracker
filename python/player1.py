import opl2
import song1

class Player:
	def __init__(self, song, opl):
		# soundcard
		self._opl = opl
		# song position
		self._line = 0
		self._order = 0
		self._tick = 0
		# player state
		self._speed = 6
		self._playing = True
		# song info
		self._song = song
		# virtual registers
		self._vrNoteOn		= 0x0000
		self._vrNote 		= [0x00] * 9
		self._vrCoarse		= [0x00] * 9
		self._vrFine		= [0x0000] * 9
		self._vrCarrierVolKSL	= [0x00] * 9
		self._vrCarrierVolAdj	= [0x00] * 9
		self._vrModulatorVolKSL	= [0x00] * 9
		self._vrModulatorVolAdj	= [0x00] * 9
		# Enable waveforms other than sine
		self._opl.writeReg(0x01, 0x20)

	# navigation override
	def getPosition(self):
		return (self._order, self._line, self._tick)

	def setPosition(self, order, line):
		self._order = order
		self._line = line
		self._tick = 0
		self.fixupPosition()

	def fixupPosition(self):
		if (self._line >= self._song.kNumLinesInPattern):
			self._line = 0
			self._order += 1
		elif (self._line < 0):
			self._line = self._song.kNumLinesInPattern-1
			self._order -= 1
		if (self._order >= self._song.getNumOrders()):
			self._order = 0
		elif (self._order < 0):
			self._order = self._song.getNumOrders()-1
	
	
	# play a tick
	def tick(self):
		if not self._playing:
			return

		# Time to grab a line?
		if (self._tick == 0):
			# Apply instr/vol/note to all channels.
			for ch in range(self._song.getNumChannels()-1,
					-1, -1):
				# Latch this line's instr/vol/note into this
				# channel's VRegs.  Do not apply fx, which must
				# be applied per-tick.
				linebytes = self._song.getPatternLineBytes(self._order, self._line, ch)
				self.applyInstr(ch, linebytes) #PRegs too
				self.applyNote(ch, linebytes)
				self.applyVol(ch, linebytes)

		# Apply fx to all channels
		for ch in range(self._song.getNumChannels()-1, -1, -1):
			# Apply fx to this channel's VRegs
			linebytes = self._song.getPatternLineBytes(self._order, self._line, ch)
			self.applyEffect(ch, linebytes)
			self.applySpFX(ch, linebytes)

			# Convert VRegs to physical register values and
			# write to the adlib card.
			self.commitVRegs(ch)

		# Tick
		self._tick += 1

		# Time for new line?
		if (self._tick == self._speed):
			self._tick = 0	# to grab a new line next time
			self._line += 1 # ...the next line
			self.fixupPosition()	#... which may require
						# moving on to the next
						# order
	
	# helper functions for tick

	def applyInstr(self, channel, lineBytes):
		new = lineBytes[1] & 0x40
		if not new:
			return
		num = (lineBytes[2] >> 4) & 0xf
		instrBytes = self._song.getInstrBytes(num)

		# Update volume VRegs
		self._vrCarrierVolKSL[channel] = instrBytes[
				self._song.kioCarrier + self._song.kioKSLVol]
		self._vrCarrierVolAdj[channel] = 0
		self._vrModulatorVolKSL[channel] = instrBytes[
				self._song.kioModulator + self._song.kioKSLVol]
		self._vrModulatorVolAdj[channel] = 0

		# Update real PRegs that were not virtualized by any VReg.
		# These give each instrument its unique timbre.

		# per-instrument registers (special case)

		# 1. pesky feedback register
		feedback = instrBytes[self._song.kioFeedback]
		self._opl.writeReg(0xc0 + channel, feedback)
		# 2. turn the note off but set the NoteOn VReg flag, so the next
		# VReg commit will turn the note back on.
		self._opl.writeReg(0xb0 + channel, 0x00)
		self._vrNoteOn |= (1 << channel)

		# per-op registers (general case)

		regChanFixups = [0, 1, 2, 8, 9, 0xa, 0x10, 0x11, 0x12]
		channelFixup = regChanFixups[channel]

		registerBases = [0x23, 0x63, 0x83, 0xe3, 0x20, 0x60, 0x80, 0xe0]
		instrOffsets = [0x00, 0x02, 0x03, 0x04, 0x05, 0x07, 0x08, 0x09]

		for n in range(len(instrOffsets)):
			self._opl.writeReg(registerBases[n] + channelFixup,
					instrBytes[instrOffsets[n]])

	def applyNote(self, channel, lineBytes):
		new = lineBytes[0] & 0x80
		if not new:
			return
		# mask out delta
		note = lineBytes[0] & 0x7f
		self._vrNote[channel] = note
		self._vrCoarse[channel] = 0
		self._vrFine[channel] = 0
		# if a NoteOff was specified, turn the note off.
		if (note == 0x7f):
			self._vrNoteOn &= ~(1 << channel)

	def applyVol(self, channel, lineBytes):
		new = lineBytes[1] & 0x80
		if not new:
			return
		# mask out deltas
		vol = lineBytes[1] & 0x3f
		self._vrCarrierVolAdj[channel] = vol

	def applyEffect(self, channel, lineBytes):
		cmd = lineBytes[2] & 0x0f
		param = lineBytes[3]

		if (cmd == 0x0):	# 0 - ARP
			arpPos = self._tick%3
			self._vrCoarse[channel] = (param >> (4*(2-arpPos)))&0xf
		elif (cmd == 0x1):	# 1 - SLIDE UP
			self._vrFine[channel] += param
		elif (cmd == 0x2):	# 2 - SLIDE DOWN
			self._vrFine[channel] -= param
		elif (cmd == 0xC):	# C - FINE NOTE CUT
			if (self._tick == param):
				self._vrNoteOn &= ~(1<<channel)
		elif (cmd == 0xE):	# E - MODULATOR VOLUME
			self._vrModulatorVolAdj[channel] = param
		elif (cmd == 0xF):	# F - SPEED
			self._speed = param

	def applySpFX(self, channel, lineBytes):
		pass
	
	def commitVRegs(self, channel):
		note = self._vrNote[channel]
		# apply coarse tuning
		note += self._vrCoarse[channel]
		# convert from semitone to f-number and octave
		semitoneToFNumTable = [0x0158,0x016d,0x0183,0x019a,
					0x01b2,0x01cc,0x01e7,0x0204,
					0x0223,0x0244,0x0266,0x028b]
		normalized = note % 12
		fnum = semitoneToFNumTable[normalized]
		octave = note / 12
		# apply fine tuning
		fnum += self._vrFine[channel]
		# F-NUMBER (low)
		self._opl.writeReg(0xa0 + channel, fnum&0xff)
		# F-NUMBER (high) & Octave & NoteOn
		value = ((fnum >> 8)&0x0f)
		value |= (octave << 2)
		if (self._vrNoteOn & (1 << channel)):
			value |= 0x20
		self._opl.writeReg(0xb0 + channel, value)
		# CARRIER VOLUME & KSL
		volume = self._vrCarrierVolKSL[channel]
		volume += self._vrCarrierVolAdj[channel] # Volume column
		regChanFixups = [0, 1, 2, 8, 9, 0xa, 0x10, 0x11, 0x12]
		channelFixup = regChanFixups[channel]
		self._opl.writeReg(0x43 + channelFixup, volume)
		# MODULATOR VOLUME & KSL
		volume = self._vrModulatorVolKSL[channel]
		volume += self._vrModulatorVolAdj[channel] # Mod. volume cmd
		self._opl.writeReg(0x40 + channelFixup, volume)
