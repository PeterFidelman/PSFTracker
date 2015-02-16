def main():
	while True:
		sNoteAndOctave = raw_input("<note><octave>      or ENTER : ")
		sInstr         = raw_input("<instrument>        or ENTER : ")
		sVolume        = raw_input("<volume>            or ENTER : ")
		sCmdAndParam   = raw_input("<cmd><param><param> or ENTER : ")

		(note, octave) = strToNoteAndOctave(sNoteAndOctave)
		(instrument)   = strToInstr(sInstr)
		(volume)       = strToVolume(sVolume)
		(cmd, param)   = strToCmdAndParam(sCmdAndParam)

		# note-info
		print note, octave, instrument, volume, cmd, param
		# pattern-line
		line = encodeLine(note, octave, instrument, volume, cmd, param)
		print "".join("%02x " % c for c in line)
		# screen
		(note, octave, instrument, volume, cmd, param) = decodeLine(line)
		print lineToString(note, octave, instrument, volume, cmd, param)
	
# ----- Keyboard-input --> note-info -----
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
	note = notes[s[0]]
	octave = int(s[1])
	return (note, octave)

def strToInstr(s):
	if (len(s) != 1):
		return None
	return int(s, 16)

def strToVolume(s):
	if (len(s) == 0):
		return None
	return int(s, 16)

def strToCmdAndParam(s):
	if (len(s) != 3):
		return (None, None)
	cmd = int(s[0], 16)
	param = int(s[1:], 16)
	return (cmd, param)

# ----- Note-info --> pattern-line -----
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

# ----- Pattern-line --> note-info -----
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

# ----- Note-info --> screen -----
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
		 11: "B"}
	return "%s%s\t%s\t%s\t%s\t%s" % (notes[note], octave,
							".." if instr is None else "%02x" % instr,
							".." if volume is None else "%02x" % volume,
							"%x" % command,
							"%02x" % param)

# ----- Call main() -----
main()
