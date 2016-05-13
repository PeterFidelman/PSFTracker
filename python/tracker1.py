import crt
import opl2
import player1
import song1
import sys		# for argv

def main():
	opl = opl2.OPL2()
	song = song1.Song()
	song.loadFromFile(sys.argv[1])
	player = player1.Player(song, opl)
	while inputLoop(opl, song, player) == True:
		pass

def inputLoop(opl, song, player):
	#view
	if player._tick == 0:
		patternView(song, player, x=0, y=1, height=16)
		orderView(song, player, x=0, y=18, height=5)
		instrView(song, x=32, y=18, height=5)
		lincrt.refresh()

	#model
	player.tick()
	opl.play()

	#controller
	key = lincrt.getKey()
	if (key == ord(' ')):
		player._playing = not player._playing
	if (key == ord('w')):
		(order, dont_care, dont_care) = player.getPosition()
		#player.setPosition(max(order-1, 0), 0)
		player.setPosition(order-1, 0)
	if (key == ord('s')):
		(order, dont_care, dont_care) = player.getPosition()
		player.setPosition(order+1, 0)
	if (key == ord('q')):
		return False
	else:
		return True

def orderView(song, player, x, y, height):
	(playingOrder, dont_care, dont_care) = player.getPosition()

	first = playingOrder
	last  = min(first+height, song.getNumOrders())

	for order in range(first, last):
		# Print line number
		lincrt.printAt(x, y+order-first, "%02x " % order)
		# Print order contents
		orderBytes = song.getOrderBytes(order)
		for channel in range(song.getNumChannels()):
			lincrt.printAt(x+3+channel*3, y+order-first, 
					"%02x " % orderBytes[channel])
	if (last-first) != height:
		for yyy in range((last-first), height):
			lincrt.printAt(x, y+yyy, ".."+("..."*song.getNumChannels()))

def instrView(song, x, y, height):
	for instr in range(min(height, song.getNumInstr())):
		xx = x
		instrBytes = song.getInstrBytes(instr)
		# Print line number
		lincrt.printAt(xx, y+instr, "%02x " % instr)
		xx += 3
		# Print instrument contents
		for byteno in range(song.kNumBytesInInstr-5):
			lincrt.printAt(xx, y+instr,
				"%02x " % instrBytes[byteno])
			xx+=3
		# Print instrument name
		for byteno in range(song.kNumBytesInInstr-5,
					song.kNumBytesInInstr):
			namechr = instrBytes[byteno]
			namechr = '' if namechr is 0 else chr(namechr)
			lincrt.printAt(xx, y+instr, namechr)
			xx+=1

	# Fill leftover lines with dots
	for instr in range(min(height, song.getNumInstr()), height):
		lincrt.printAt(x, y+instr, "."*41)


def patternView(song, player, x, y, height):
	(order, playingLine, dont_care) = player.getPosition()

	scrollMargin = height/2
	first = max(0, playingLine-(height-scrollMargin))
	last  = min(first+height, song.kNumLinesInPattern)
	first = last-height

	for line in range(first, last):
		# Line number
		lincrt.printAt(x, y+line-first, "%02x" % line)
		# Move curses cursor to mark the currently playing line
		lincrt.moveTo(x+3, y+playingLine-first)
		for chan in range(song.getNumChannels()):
			# The contents of the line
			lineBytes = song.getPatternLineBytes(order, line, chan)
			(note, octave, instr,
			volume, command, param) = song.unpackLine(lineBytes)

			# Where to print this line for this channel
			spotx = x+3 + chan*9
			spoty = y + line-first

			# Do it
			lincrt.printAt(spotx+0, spoty, noteToStr(note))
			lincrt.printAt(spotx+1, spoty,
				"." if octave is None else str(octave))
			lincrt.printAt(spotx+2, spoty,
				"." if instr is None else "%01x" % instr)
			lincrt.printAt(spotx+3, spoty,
				".." if volume is None else "%02x" % volume)

			# Command/param is a special case.  If both are zero,
			# don't bother printing either.
			if ((command == param) and (command == 0)):
				lincrt.printAt(spotx+5, spoty, "...")
			else:
				lincrt.printAt(spotx+5, spoty,
				"." if command is None else "%01x" % command)
				lincrt.printAt(spotx+6, spoty,
				".." if param is None else "%02x" % param)

def noteToStr(note):
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
	return notes[note]

# Call main
lincrt = crt.CRT()
lincrt.wrapper(main)
