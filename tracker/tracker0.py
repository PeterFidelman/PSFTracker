import sys		# for sys.argv
import string		# for string.printable

# constants
kNumLinesInPattern	=	32
kNumBytesInLine		=	4
koNumChannels		=	0x02	# offset of field containing number of channels
koStartOfInstruments	=	0x23	# offset of field containing offset of first instrument
koStartOfSpFx		=	0x25	# offset of field containing offset of first spfx
koStartOfOrders		=	0x27	# offset of field containing offset of first order
koStartOfPatterns	=	0x29	# offset of field containing offset of first pattern

def main():
	# Open the file
	global fh
	global f
	global numChannels
	global pattern
	fh = open(sys.argv[1], 'rb')
	f = bytearray(fh.read())
	numChannels = f[koNumChannels]
	pattern = 0

	while inputLoop() == True:
		pass
	# End

def inputLoop():
	sHelp        = ["help", "h", "?"]
	sQuit        = ["quit", "q", "exit"]
	sInstruments = ["instruments", "instrument", "instr", "i"]
	sInstrumentAppend = ["ia"]
	sInstrumentInsert = ["ii"]
	sInstrumentDelete = ["id"]
	sOrders      = ["orders", "order", "ord", "o"]
	sOrderAppend = ["orderappend", "oappend", "oa"]
	sOrderInsert = ["orderinsert", "oinsert", "oi"]
	sOrderDelete = ["orderdelete", "orderdel", "odelete", "odel", "od"]
	sPatternAppend = ["patternappend", "pappend", "pa"]
	sPatternDelete = ["patterndelete", "patterndel", "pdelete", "pdel", "pd"]
	sPatterns    = ["patterns", "pattern", "pat", "p", ""]
	sWrite       = ["save", "write", "w"]
	global pattern
	global fh

	sCommandLine = raw_input("p[%02x]> " % pattern)
	commandList = sCommandLine.lower().split(" ")

	# System commands
	if commandList[0] in sQuit:
		return False
	
	elif commandList[0] in sHelp:
		print "Help\t\t\t"		+ str(sHelp)
		print "Quit\t\t\t"		+ str(sQuit)
		print "Instruments <n>\t\t"	+ str(sOrders)
		print "Orders <n>\t\t"		+ str(sOrders)
		print "  - append\t\t"		+ str(sOrderAppend)
		print "  - insert <n>\t\t"	+ str(sOrderInsert)
		print "  - delete <n>\t\t"	+ str(sOrderDelete)
		print "Patterns <n>\t\t"	+ str(sPatterns)
		print "  - append\t\t"		+ str(sPatternAppend)
		print "  - delete\t\t"		+ str(sPatternDelete)
		print "Write\t\t\t"		+ str(sWrite)

	elif commandList[0] in sWrite:
		fh.close()
		fh = open(sys.argv[1], 'wb')
		fh.write(f)
		fh.close()

	elif commandList[0] in ["%02x" % n for n in range(0x00, 0x100)]:
		# Hex digits - Edit a line in the pattern
		(note, octave, instrument, volume, cmd, param) = promptForNoteInfo()
		newLine = encodeLine(note, octave, instrument, volume, cmd, param)

		oPattern = getPatternOffset(pattern)
		oLine    = oPattern + kNumBytesInLine*int(commandList[0],16)
		f[oLine:oLine+4] = newLine

	# Instrument commands
	elif commandList[0] in sInstruments:
		if len(commandList) == 2:
			# Instrument was specified.  Let user change it.
			o = getInstrumentOffset(int(commandList[1], 16))
			f[o : o+16] = promptForInstrument()
			pass
		else:
			# No instrument.  Just print the instruments.
			printInstruments()

	elif commandList[0] in sInstrumentAppend:
		appendInstrument()

	elif commandList[0] in sInstrumentInsert:
		insertInstrument(int(commandList[1],16))

	elif commandList[0] in sInstrumentDelete:
		deleteInstrument(int(commandList[1],16))

	# Order commands
	elif commandList[0] in sOrders:
		if len(commandList) == 2:
			# Order was specified.  Let user change it.
			o = getOrderOffset(int(commandList[1], 16))
			f[o : o+numChannels] = promptForOrder()
		else:
			# No argument.  Just print the orders.
			printOrders()

	elif commandList[0] in sOrderAppend:
		appendOrder()

	elif commandList[0] in sOrderInsert:
		insertOrder(int(commandList[1],16))

	elif commandList[0] in sOrderDelete:
		deleteOrder(int(commandList[1],16))

	# Pattern commands
	elif commandList[0] in sPatterns:
		if len(commandList) == 1:
			# No pattern specified.  Print the last one.
			printPattern(pattern)
		else:
			pattern = int(commandList[1])
			#printPattern(pattern)

	elif commandList[0] in sPatternAppend:
		appendPattern()

	elif commandList[0] in sPatternDelete:
		deletePattern()
	
	else:
		print "Bad command or file name."

	# Fall through
	return True


# ----- Instrument functions -----
# Navigating
def getNumInstruments():
	return (f[koStartOfSpFx] - f[koStartOfInstruments]) / 16

def getInstrumentOffset(instrumentNumber):
	return f[koStartOfInstruments] + 16*instrumentNumber

def getInstrument(instrumentNumber):
	i = getInstrumentOffset(instrumentNumber)
	return f[i:i+16]

def printInstruments():
	for instrNumber in range(getNumInstruments()):
		instrOffset = getInstrumentOffset(instrNumber)

		s = "%02x: " % instrNumber
		s += "".join("%02x " % c for c in f[instrOffset : instrOffset+5]) + " "
		s += "".join("%02x " % c for c in f[instrOffset+5 : instrOffset+10]) + " "
		s += "".join("%02x " % f[instrOffset+10]) + " "
		s += "".join("%c" % (c if chr(c) in string.printable else '.') for c in f[instrOffset+11 : instrOffset+16])
		print s

#Mutating
def insertInstrument(n):
	for i in range(16):
		f.insert(f[koStartOfInstruments] + n*16, 0x00)
	f[koStartOfSpFx]     += 16
	f[koStartOfOrders]   += 16
	f[koStartOfPatterns] += 16

def appendInstrument():
	for i in range(16):
		f.insert(f[koStartOfSpFx], 0x00)
	f[koStartOfSpFx]     += 16
	f[koStartOfOrders]   += 16
	f[koStartOfPatterns] += 16

def deleteInstrument(n):
	for i in range(16):
		f.pop(f[koStartOfInstruments] + n*16)
	f[koStartOfSpFx]     -= 16
	f[koStartOfOrders]   -= 16
	f[koStartOfPatterns] -= 16


# ----- Order functions -----
# Navigating
def getNumOrders():
	return (f[koStartOfPatterns] - f[koStartOfOrders]) / numChannels

def getOrderOffset(orderLineNumber):
	return f[koStartOfOrders] + orderLineNumber*numChannels

def getOrder(orderLineNumber):
	i = getOrderOffset(orderLineNumber)
	return f[i:i+numChannels]

def printOrders():
#	print "".join("%02x " % c for c in f[f[koStartOfOrders] : f[koStartOfPatterns]])

	for orderLineNumber in range(getNumOrders()):
		orderLineOffset = f[koStartOfOrders] + orderLineNumber*numChannels

		s = "%02x: " % orderLineNumber
		s += "".join("%02x " % c for c in f[orderLineOffset : orderLineOffset+numChannels])
		print s

# Mutating
def insertOrder(n):
	for i in range(numChannels):
		f.insert(f[koStartOfOrders] + n*numChannels, 0x00)
	f[koStartOfPatterns] += numChannels

def appendOrder():
	for i in range(numChannels):
		f.insert(f[koStartOfPatterns], 0x00)
	f[koStartOfPatterns] += numChannels

def deleteOrder(n):
	for i in range(numChannels):
		f.pop(f[koStartOfOrders] + n*numChannels)
	f[koStartOfPatterns] -= numChannels


# ----- Pattern functions -----
# Navigating
def getPatternOffset(patternNumber):
	return f[koStartOfPatterns] + 32*4*patternNumber

def getPattern(patternNumber):
	i = getPatternOffset(patternNumber)
	return f[i:i+(kNumLinesInPattern*kNumBytesInLine)]

def printPattern(patternNumber):
	try:
		p = getPattern(patternNumber)
		for i in range(0, kNumLinesInPattern):
			(note, octave, instrument, volume, command, param) = decodeLine(p[(i*4):(i*4)+4])
			print ("%02x:\t" % i) + lineToString(note, octave, instrument, volume, command, param)
	except:
		print "That pattern doesn't exist.  Nice try."

#Mutating
def insertPattern(n):
	# Left out because it would involve renumbering all existing patterns
	pass

def appendPattern():
	for i in range(kNumBytesInLine * kNumLinesInPattern):
		f.append(0x00)

def deletePattern():
	# Always deletes the last pattern.
	for i in range(kNumBytesInLine * kNumLinesInPattern):
		f.pop()


# ----- Instrument packing -----
def promptForInstrument():
	done = False
	while not done:
		try:
			sInstr = raw_input("instr> ")
			instrBytes = bytearray.fromhex(sInstr)
			if len(instrBytes) != 16:
				raise Exception('Please try again')
			return instrBytes
		except:
			done = False

# ----- Order line packing -----
def promptForOrder():
	done = False
	while not done:
		try:
			sOrder = raw_input("order> ")
			orderBytes = bytearray.fromhex(sOrder)
			if len(orderBytes) != numChannels:
				raise Exception('Please try again')
			return orderBytes
		except:
			done = False
	

# ----- Pattern line packing and unpacking -----
# Keyboard-input --> note-info
def promptForNoteInfo():

	done = False
	while not done:
		try:
			sNoteInfo = raw_input("line> ")
			lNoteInfo = sNoteInfo.split(" ")
			(note, octave) = strToNoteAndOctave(lNoteInfo[0])
			(instrument)   = strToInstr(lNoteInfo[1])
			(volume)       = strToVolume(lNoteInfo[2])
			(cmd, param)   = strToCmdAndParam(lNoteInfo[3])
			done = True
		except:
			done = False
	return (note, octave, instrument, volume, cmd, param)
	
def strToNoteAndOctave(s):
	if (len(s) != 2):
		return (None, None)
	notes = {"C": 0,
		 "c": 1,
		 "D": 2,
		 "d": 3,
		 "E": 4,
		 "F": 5,
		 "f": 6,
		 "G": 7,
		 "g": 8,
		 "A": 9,
		 "a": 10,
		 "B": 11}
	try:
		note = notes[s[0]]
		octave = int(s[1])
		return (note, octave)
	except:
		return (None, None)

def strToInstr(s):
	try:
		return int(s, 16)
	except:
		return None

def strToVolume(s):
	try:
		if (len(s) == 0):
			return None
		return int(s, 16)
	except:
		return None

def strToCmdAndParam(s):
	try:
		if (len(s) != 3):
			return (None, None)
		cmd = int(s[0], 16)
		param = int(s[1:], 16)
		return (cmd, param)
	except:
		return (0, 0)

# Note-info --> pattern-line
def encodeLine(note, octave, instr, volume, command, param):
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

# Pattern-line --> note-info
def decodeLine(line):
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

# Note-info --> screen
def lineToString(note, octave, instr, volume, command, param):
	notes = {0: "C",
		 1: "c",
		 2: "D",
		 3: "d",
		 4: "E",
		 5: "F",
		 6: "f",
		 7: "G",
		 8: "g",
		 9: "A",
		 10: "a",
		 11: "B",
		 None: "."}
	return "%s%s\t%s\t%s\t%s%s" % (notes[note], octave if octave is not None else '.',
							"." if instr is None else "%01x" % instr,
							".." if volume is None else "%02x" % volume,
							"%x" % command,
							"%02x" % param)

# ----- Call main() -----
main()
