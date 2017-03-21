import crt
import opl2
import player1
import song1
import sys		# for argv

lastInstr = None

def main():
	# set up the song and the means to play it
	opl = opl2.OPL2()
	song = song1.Song()
	song.loadFromFile(sys.argv[1])
	player = player1.Player(song, opl)
	# load ui elements
	patternView = PatternView(song, player, x=0, y=1, h=32)
	orderView = OrderView(song, player, x=0, y=34, h=5)
	instrView = InstrView(song, x=32, y=34, h=5)
	# set up the main loop
	mainLoop = MainLoop(opl, song, player, [patternView, orderView, instrView])
	# run
	while mainLoop.tick() == True:
		pass

class MainLoop:
	opl = None
	song = None
	player = None
	views = []
	# which view currently has keyboard focus; represented as an index into
	# the "views" list.
	activeViewIdx = 0

	# "views" is a list of the views that will be drawn and polled for
	# user input every tick.
	def __init__(self, opl, song, player, views):
		self.opl = opl
		self.song = song
		self.player = player
		self.views = views
		# the first view in the list gets focus at ui startup
		self.activeViewIndex = 0
	
	# returns False to quit, or True to keep going
	def tick(self):
		# draw ui "views"
		if self.player._tick == 0:
			index = 0
			for view in self.views:
				view.draw(index == self.activeViewIndex)
				index += 1
			lincrt.refresh()
		# run song "controller"
		self.player.tick()
		# run opl "view" to produce audio output :)
		self.opl.play()
		# take input from ui "controller"
		key = lincrt.getKey()
		# ...and dispatch to the active "view"
		keyConsumed = self.views[self.activeViewIndex].signal(key)
		if keyConsumed:
			# if it used the key, redraw it (because something
			# interesting probably happened)
			self.views[self.activeViewIndex].draw(True)
		else:
			# if it doesn't use the key, feed it to a global key handler
			if (key == 27):
				# esc == quit
				return False
			if (key == ord(' ')):
				self.player._playing = not self.player._playing
			elif (key == ord('`')):
				# ` == cycle views forward
				self.activeViewIndex = (self.activeViewIndex + 1) % len(self.views)
				self.views[self.activeViewIndex].draw(True)
			elif (key == ord('~')):
				# ~ == cycle views backward
				self.activeViewIndex = (self.activeViewIndex + len(self.views)-1) % len(self.views)
				self.views[self.activeViewIndex].draw(True)
			elif (key == ord("|")):
				self.song.saveToFile(sys.argv[1])
		return True

# helper
# returns None to delete the byte or "NO_CHANGE" if this was not a request to
# change the byte value, otherwise the new byte value
def getNewByteValue(key, curByte):
	newByte = 0

	# 0 through 9
	if (key >= 0x30) and (key <= 0x39):
		val = key - 0x30
		newByte = (curByte << 4) & 0xff | val
	# A through F
	elif (key >= 0x41) and (key <= 0x46):
		val = key - 0x41 + 0xa
		newByte = (curByte << 4) & 0xff | val
	# a through f
	elif (key >= 0x61) and (key <= 0x66):
		val = key - 0x61 + 0xa
		newByte = (curByte << 4) & 0xff | val
	# delete or backspace
	elif (key == 330) or (key == 263):
		return None
	else:
		return "NO_CHANGE"
	return newByte


class PatternView:
	song = None
	player = None
	x = 0
	y = 0
	h = 0

	# (offset, name) tuple
	columns = [	(0, "Note/Octave"),
				(2, "Instrument"),
				(3, "Volume"),
				(5, "Effect"),
				(6, "Param")]

	activeChannel = 0
	activeColumnIndex = 0
	octave = 3

	def __init__(self, song, player, x, y, h):
		self.song = song
		self.player = player
		self.x = x
		self.y = y
		self.h = h
	
	def draw(self, isActive):
		(order, playingLine, dont_care) = self.player.getPosition()
		scrollMargin = self.h/2
		first = max(0, playingLine-(self.h-scrollMargin))
		last  = min(first+self.h, self.song.kNumLinesInPattern)
		first = last-self.h
		for line in range(first, last):
			# Line number
			lincrt.printAt(self.x, self.y+line-first, "%02x" % line)
			for chan in range(self.song.getNumChannels()):
				# The contents of the line
				lineBytes = self.song.getPatternLineBytes(order, line, chan)
				(note, octave, instr,
				volume, command, param) = self.song.unpackLine(lineBytes)
				# Where to print this line for this channel
				spotx = self.x+3 + chan*9
				spoty = self.y + line-first
				# Do it
				lincrt.printAt(spotx+0, spoty, self._noteToStr(note))
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
		if (isActive):
			# Move curses cursor to mark the currently playing line
			lincrt.moveTo(self.x+3 + self.activeChannel*9 + self.columns[self.activeColumnIndex][0],
							self.y+playingLine-first)

	# returns True if the key was recognized and consumed, otherwise False
	def signal(self, key):
		global lastInstr
		(order, line, position) = self.player.getPosition()

		if (self.activeColumnIndex == 0):
			# special "note column" stuff
			retval = self._getNoteValue(key, self.octave)
			if retval != "NOT_A_NOTE":
				lineBytes = self.song.getPatternLineBytes(order, line, self.activeChannel)
				(note, octave, instr, volume, command, param) = self.song.unpackLine(lineBytes)
				if retval == "DELETE":
					note = None
					octave = None
				else:
					(note, octave) = retval
					instr = lastInstr	# use instrument from instrument view
				lineBytes = self.song.packLine(note, octave, volume, instr, command, param)
				self.song.setPatternLineBytes(order, line, self.activeChannel, lineBytes)
				return True
		else:
			# if it's any other column, pressing a hex key does hex entry
			lineBytes = self.song.getPatternLineBytes(order, line, self.activeChannel)
			(note, octave, instr, volume, command, param) = self.song.unpackLine(lineBytes)
			cName = self.columns[self.activeColumnIndex][1]
			newByte = None
			if (cName == "Instrument"):
				newByte = getNewByteValue(key, 0 if instr == None else instr)
				instr = newByte
			elif (cName == "Volume"):
				newByte = getNewByteValue(key, 0 if volume == None else volume)
				volume = newByte
			elif (cName == "Effect"):
				newByte = getNewByteValue(key, 0 if command == None else command)
				command = newByte
			elif (cName == "Param"):
				newByte = getNewByteValue(key, 0 if param == None else param)
				param = newByte
			if newByte != "NO_CHANGE":
				lineBytes = self.song.packLine(note, octave, volume, instr, command, param)
				self.song.setPatternLineBytes(order, line, self.activeChannel, lineBytes)
				return True

		if (key == 262):
			#home == go to start of pattern
			self.player.setPosition(order, 0)
			return True
		if (key == 360):
			#end == go to end of pattern
			self.player.setPosition(order, self.song.kNumLinesInPattern-1)
			return True
		if (key == 339):
			#pgup == go to previous pattern
			self.player.setPosition(order-1, 0)
			return True
		if (key == 338):
			#pgdn == go to next pattern
			self.player.setPosition(order+1, 0)
			return True
		if (key == 261):
			#right == go to next column in channel
			self.activeColumnIndex = (self.activeColumnIndex + 1) % len(self.columns)
			#if hit last column, go to next channel
			if self.activeColumnIndex == 0:
				self.activeChannel = (self.activeChannel + 1) % self.song.getNumChannels()
		if (key == 260):
			#left == go to prev column in channel
			self.activeColumnIndex = (self.activeColumnIndex + len(self.columns) - 1) % len(self.columns)
			#if passed first column, go to prev channel
			if self.activeColumnIndex == len(self.columns)-1:
				self.activeChannel = (self.activeChannel + self.song.getNumChannels()-1) % self.song.getNumChannels()
		if (key == 259):
			#up == go up a line
			newLine = line if (line-1 < 0) else line-1
			self.player.setPosition(order, newLine)
			return True
		if (key == 258):
			#down == go to next line
			newLine = line if (line+1 >= self.song.kNumLinesInPattern) else line+1
			self.player.setPosition(order, newLine)
			return True
		if (key == ord("	")):
			# tab == go to next channel
			self.activeChannel = (self.activeChannel + 1) % self.song.getNumChannels()
			return True
		if (key == 353):
			# shift-tab == go to previous channel
			self.activeChannel = (self.activeChannel + self.song.getNumChannels()-1) % self.song.getNumChannels()
			return True
		if (key >= 0 and key <= 255 and chr(key) in "!@#$%^&*("):
			# change octave on SHIFT+1-9
			self.octave = "!@#$%^&*(".find(chr(key))
		else:
			return False

	def _noteToStr(self, note):
		notes = {-1: "-",
			 0: "C",
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

	# return the new (note, octave) or "NOT_A_NOTE" if this key wasn't a note or
	# "DELETE" if the note should be deleted
	# TODO Make the return code for this function nicer, maybe store the possible
	# out of band values in a tuple?
	def _getNoteValue(self, keyCode, baseOctave):
		kKeyOff = "1"
		kHighOctave = "q2w3er5t6y7ui9o0p"
		kLowOctave =  "zsxdcvgbhnjm,l.;/"

		if (keyCode == 330) or (keyCode == 263):
			# delete or backspace
			return "DELETE"
		if (keyCode <= 255 and keyCode >= 0):
			key = chr(keyCode)
			if key in kKeyOff:
				return (0x7F, 0)
			if key in kHighOctave:
				return (kHighOctave.find(key), baseOctave+1)
			if key in kLowOctave:
				return (kLowOctave.find(key), baseOctave)
		return "NOT_A_NOTE"



class OrderView:
	song = None
	player = None
	x = 0
	y = 0
	h = 0
	# the active channel that should be highlighted
	activeChannel = 0

	def __init__(self, song, player, x, y, h):
		self.song = song
		self.player = player
		self.x = x
		self.y = y
		self.h = h
	
	def draw(self, isActive):
		(playingOrder, dont_care, dont_care) = self.player.getPosition()
		first = playingOrder
		last = min(first+self.h, self.song.getNumOrders())
		for order in range(first, last):
			# Print line number
			lincrt.printAt(self.x, self.y+order-first, "%02x " % order)
			# Print order contents
			orderBytes = self.song.getOrderBytes(order)
			for channel in range(self.song.getNumChannels()):
				lincrt.printAt(self.x+3+channel*3, self.y+order-first, 
						"%02x " % orderBytes[channel])
		if (last-first) != self.h:
			for yyy in range((last-first), self.h):
				lincrt.printAt(self.x, self.y+yyy, ".."+("..."*self.song.getNumChannels()))
		if (isActive):
			lincrt.moveTo(self.x+3+self.activeChannel*3, self.y)
	
	# returns True if the key was recognized and consumed, otherwise False
	def signal(self, key):
		(order, dontCare, dontCare) = self.player.getPosition()

		if (key == 262):
			#home == go to start of song
			self.player.setPosition(0, 0)
			return True
		if (key == 360):
			#end == go to end of song
			self.player.setPosition(self.song.getNumOrders()-1, 0)
			return True
		if (key == 259):
			#up == go to previous order
			self.player.setPosition(order-1, 0)
			return True
		if (key == 258):
			#down == go to next order
			self.player.setPosition(order+1, 0)
			return True
		if (key == ord("	")) or (key == 261):
			# tab or right == go to next channel
			self.activeChannel = (self.activeChannel + 1) % self.song.getNumChannels()
			return True
		if (key == 353) or (key == 260):
			# shift-tab or left == go to previous channel
			self.activeChannel = (self.activeChannel + self.song.getNumChannels()-1) % self.song.getNumChannels()
			return True
		if (key == ord("+")):
			# + == append pattern
			self.song.appendPattern()
			# ...and switch this channel to the new pattern
			b = self.song.getOrderBytes(order)
			b[self.activeChannel] = self.song.getNumPatterns()-1
			self.song.setOrderBytes(order, b)
			return True
		if (key == ord("-")):
			# - == remove pattern
			victim = self.song.getNumPatterns()-1
			self.song.deletePattern()
			b = self.song.getOrderBytes(order)
			if b[self.activeChannel] == victim:
				b[self.activeChannel] = self.song.getNumPatterns()-1
				self.song.setOrderBytes(order, b)
			# TODO walk the rest of the song and remove other references to the pattern
			return True
		if (key == 331):
			# insert == insert order
			self.song.insertOrder(order)
			return True
		if (key == 330):
			# delete == remove order
			self.song.deleteOrder(order)
			return True
		if (key == 10):
			# enter == append order
			self.song.appendOrder()
			return True
		else:
			# if a hex value, change current order byte
			b = self.song.getOrderBytes(order)
			retval = getNewByteValue(key, b[self.activeChannel])
			if (retval == None):
				b[self.activeChannel] = 0
				self.song.setOrderBytes(order, b)
				return True
			elif (retval != "NO_CHANGE"):
				if(self.song.patternExists(retval)):
					b[self.activeChannel] = retval
				else:
					b[self.activeChannel] = 0
				self.song.setOrderBytes(order, b)
				return True

		return False

class InstrView:
	song = None
	x = 0
	y = 0
	h = 0
	# The index of the instrument to draw on the first line (i.e. the
	# scroll position of the instruments view)
	first = 0
	# The byte within the active instrument that should be highlighted
	activeByte = 0

	def __init__(self, song, x, y, h):
		self.song = song
		self.x = x
		self.y = y
		self.h = h
		# hack
		lincrt.printAt(self.x, self.y-1, "   cc KV AD SR Wv cc KV AD SR Wv FB")
	
	def draw(self, isActive):
		#for instr in range(min(self.h, self.song.getNumInstr())):
		for instr in range(self.first, min(self.h+self.first, self.song.getNumInstr())):
			xx = self.x
			instrBytes = self.song.getInstrBytes(instr)
			# Print line number
			lincrt.printAt(xx, self.y+instr-self.first, "%02x " % instr)
			xx += 3
			# Print instrument contents
			for byteno in range(self.song.kNumBytesInInstr-5):
				lincrt.printAt(xx, self.y+instr-self.first,
					"%02x " % instrBytes[byteno])
				xx+=3
			# Print instrument name
			for byteno in range(self.song.kNumBytesInInstr-5,
						self.song.kNumBytesInInstr):
				namechr = instrBytes[byteno]
				namechr = '.' if namechr is 0 else chr(namechr)
				lincrt.printAt(xx, self.y+instr-self.first, namechr)
				xx+=1
		# Fill leftover lines with dots
		for instr in range(min(self.h, self.song.getNumInstr()), self.h):
			lincrt.printAt(self.x, self.y+instr-self.first, "."*41)
		if (isActive):
			ab = self.activeByte
			xOffset = 0
			while (ab > self.song.kNumBytesInInstr-5):
				ab -= 1
				xOffset += 1
			xOffset += ab * 3
			lincrt.moveTo(self.x+3 + xOffset, self.y)
	
	# returns True if the key was recognized and consumed, otherwise False
	def signal(self, key):
		global lastInstr
		if (key == 259):
			#up == go to previous instrument
			self.first = 0 if self.first == 0 else self.first-1
			lastInstr = self.first
			return True
		if (key == 258):
			#down == go to next instrument
			self.first = self.first if self.first >= self.song.getNumInstr()-1 else self.first+1
			lastInstr = self.first
			return True
		if (key == ord("	")) or (key == 261):
			# tab or right == go to next byte
			self.activeByte = (self.activeByte + 1) % self.song.kNumBytesInInstr
			return True
		if (key == 353) or (key == 260):
			# shift-tab or left == go to previous byte
			self.activeByte = (self.activeByte + self.song.kNumBytesInInstr-1) % self.song.kNumBytesInInstr
			return True
		if (key == 331):
			# insert == add instrument
			self.song.insertInstrument(self.first)
			return True
		if (key == 330):
			# delete == remove instrument
			self.song.deleteInstrument(self.first)
			return True
		if (key == 10):
			# enter == append instrument
			self.song.appendInstrument()
			return True
		else:
			# if a hex value, change current instr byte
			b = self.song.getInstrBytes(self.first)
			retval = getNewByteValue(key, b[self.activeByte])
			if (retval == None):
				b[self.activeByte] = 0
				self.song.setInstrBytes(self.first, b)
				return True
			elif (retval != "NO_CHANGE"):
				b[self.activeByte] = retval
				self.song.setInstrBytes(self.first, b)
				return True
		return False

# Call main
lincrt = crt.CRT()
lincrt.wrapper(main)

