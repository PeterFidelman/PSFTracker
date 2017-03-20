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
	
	# Accessors
	def getNumChannels(self):
		return self._a[self.koNumChannels]

	def getNumInstr(self):
		return (self._a[self.koStartOfSpFx] - self._a[self.koStartOfInstruments]) / self.kNumBytesInInstr
	
	def getNumOrders(self):
		return (self._a[self.koStartOfPatterns] - self._a[self.koStartOfOrders]) / self.getNumChannels()

	def getNumPatterns(self):
		return (len(self._a) - self._a[self.koStartOfPatterns]) / (self.kNumLinesInPattern * self.kNumBytesInLine)

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

	def patternExists(self, p):
		if self.getOffsetToPattern(p) + self.kNumLinesInPattern * self.kNumBytesInLine >= len(self._a):
			return False
		else:
			return True

	# Stateless helper
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
			if (semitone == 0x7f):
				# noteoff
				note = -1;
			else:
				# general case
				note = semitone % 12
				octave = semitone / 12
		if (line[1] & 0x80):
			volume = line[1] & 0x3f
		if (line[1] & 0x40):
			instr = (line[2] & 0xf0) >> 4
		command = line[2] & 0x0f
		param = line[3]
		return (note, octave, instr, volume, command, param)

	def packLine(self, note, octave, volume, instr, command, param):
		patternLine = bytearray([0, 0, 0, 0])
		if note is not None and octave is not None:
			semitone = octave*12 + note
			patternLine[0] = 0x80 | semitone
		if volume is not None:
			patternLine[1] = 0x80 | volume
		if instr is not None:
			patternLine[1] |= 0x40
			patternLine[2] = (instr & 0xf) << 4
		if command is not None and param is not None:
			patternLine[2] |= (command & 0xf)
			patternLine[3] = param
		return patternLine

	# Mutators
	def loadFromFile(self, fileName):
		with open(fileName, 'rb') as fh:
			self._a = bytearray(fh.read())

	def saveToFile(self, fileName):
		with open(fileName, 'wb') as fh:
			fh.write(self._a)
	
	def insertInstrument(self, n):
		for i in range(16):
			self._a.insert(self._a[self.koStartOfInstruments] + n*16, 0x00)
		self._a[self.koStartOfSpFx] += 16
		self._a[self.koStartOfOrders] += 16
		self._a[self.koStartOfPatterns] += 16
	
	def appendInstrument(self):
		for i in range(16):
			self._a.insert(self._a[self.koStartOfSpFx], 0x00)
		self._a[self.koStartOfSpFx] += 16
		self._a[self.koStartOfOrders] += 16
		self._a[self.koStartOfPatterns] += 16
	
	def deleteInstrument(self, n):
		for i in range(16):
			self._a.pop(self._a[self.koStartOfInstruments] + n*16)
		self._a[self.koStartOfSpFx] -= 16
		self._a[self.koStartOfOrders] -= 16
		self._a[self.koStartOfPatterns] -= 16

	def insertOrder(self, n):
		for i in range(self.getNumChannels()):
			self._a.insert(self._a[self.koStartOfOrders] + n*self.getNumChannels(), 0x00)
		self._a[self.koStartOfPatterns] += self.getNumChannels();
	
	def appendOrder(self):
		for i in range(self.getNumChannels()):
			self._a.insert(self._a[self.koStartOfPatterns], 0x00)
		self._a[self.koStartOfPatterns] += self.getNumChannels()

	def deleteOrder(self, n):
		for i in range(self.getNumChannels()):
			self._a.pop(self._a[self.koStartOfOrders] + n*self.getNumChannels())
		self._a[self.koStartOfPatterns] -= self.getNumChannels()

	# left out because it would renumber all existing patterns
	def insertPattern(self, n):
		pass
	
	def appendPattern(self):
		for i in range(self.kNumBytesInLine * self.kNumLinesInPattern):
			self._a.append(0x00)
	
	# n left out:  this always deletes the last pattern
	def deletePattern(self):
		for i in range(self.kNumBytesInLine * self.kNumLinesInPattern):
			self._a.pop()

	def setInstrBytes(self, i, newBytes):
		offset = self.getOffsetToInstr(i)
		self._a[offset : offset + self.kNumBytesInInstr] = newBytes

	def setOrderBytes(self, o, newBytes):
		offset = self.getOffsetToOrder(o)
		self._a[offset : offset + self.getNumChannels()] = newBytes

	def setPatternLineBytes(self, order, line, channel, newBytes):
		pnum = self.getOrderBytes(order)[channel]
		oPattern = self.getOffsetToPattern(pnum)
		oLine = oPattern + self.kNumBytesInLine*line
		self._a[oLine:oLine+4] = newBytes
