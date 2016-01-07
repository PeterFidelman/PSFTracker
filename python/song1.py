class Song:
	# Song format constants
	kNumLinesInPatternShift	=	5
	kNumLinesInPattern	=	1<<kNumLinesInPatternShift
	kNumBytesInLineShift	=	2
	kNumBytesInLine		=	1<<kNumBytesInLineShift	
	kNumBytesInInstrShift	=	4
	kNumBytesInInstr	=	1<<kNumBytesInInstrShift
	koNumChannels		=	0x02
	koStartOfInstruments	=	0x23
	koStartOfSpFx		=	0x25
	koStartOfOrders		=	0x27
	koStartOfPatterns	=	0x29

	# Instrument format constants
	kioCarrier		=	0		# Extra offsets
	kioModulator		=	5
	kioMisc			=	0		# Per-operator...
	kioKSLVol		=	1		# ...
	kioAD			=	2		# ...
	kioSR			=	3		# ...
	kioWaveform		=	4		# .
	kioFeedback		=	10		# Per-instrument
	kioA			=	11		# ...
	kioB			=	12		# ...UNUSED
	kioC			=	13		# ...UNUSED
	kioD			=	14		# ...UNUSED
	kioE			=	15		# ...UNUSED.
	
	def __init__(self):
		# Have not loaded a song yet.
		self._a = None
	
	def loadFromFile(self, fileName):
		with open(fileName, 'rb') as fh:
			self._a = bytearray(fh.read())

	# Accessor helpers
	def getNumChannels(self):
		return self._a[self.koNumChannels]

	def getNumInstr(self):
		return (self._a[self.koStartOfSpFx] - self._a[self.koStartOfInstruments]) / self.kNumBytesInInstr
	
	def getNumOrders(self):
		return (self._a[self.koStartOfPatterns] - self._a[self.koStartOfOrders]) / self.getNumChannels()

	def getOffsetToInstr(self, i):
		return (self._a[self.koStartOfInstruments] +
			(i<<self.kNumBytesInInstrShift))

	def getOffsetToSpFX(self, s):
		return None

	def getOffsetToOrder(self, o):
		return self._a[self.koStartOfOrders] + o*self.getNumChannels()

	def getOffsetToPattern(self, p):
		return (self._a[self.koStartOfPatterns] +
		(p<<(self.kNumLinesInPatternShift + self.kNumBytesInLineShift)))
	
	# Accessors
	def getInstrBytes(self, i):
		offset = self.getOffsetToInstr(i)
		return self._a[offset : offset + self.kNumBytesInInstr]
	
	def getSpFXBytes(self, s):
		pass
	
	def getOrderBytes(self, o):
		offset = self.getOffsetToOrder(o)
		return self._a[offset : offset + self.getNumChannels()]

	def getPatternBytes(self, p):
		offset = self.getOffsetToPattern(p)
		return self._a[offset : (offset << (
		self.kNumBytesInLineShift + self.kNumLinesInPatternShift))]
	
	def getPatternLineBytes(self, order, line, channel):
		pnum = self.getOrderBytes(order)[channel]
		pattern = self.getPatternBytes(pnum)
		offset = line << self.kNumBytesInLineShift
		return pattern[offset : offset + self.kNumBytesInLine]

	# More accessors
	def unpackLine(self, line):
		# 'line' is a bytearray
		note = None
		octave = None
		volume = None
		instr = None
		command = None
		param = None
		if (line[0] & 0x80):
			semitone = line[0] & 0x7f
			note = semitone % 12
			octave = semitone / 12
		if (line[1] & 0x80):
			volume = line[1] & 0x3f
		if (line[1] & 0x40):
			instr = (line[2] & 0xf0) >> 4
		command = line[2] & 0x0f
		param = line[3]
		return (note, octave, instr, volume, command, param)
