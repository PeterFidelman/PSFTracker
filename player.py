# constants
kNumLinesInPattern	=	32
kNumBytesInLine		=	5
oNumChannels		=	0x02	# offset of field containing number of channels
oStartOfInstruments	=	0x23	# offset of field containing offset of first instrument
oStartOfSpFx		=	0x25	# offset of field containing offset of first spfx
oStartOfOrders		=	0x27	# offset of field containing offset of first order
oStartOfPatterns	=	0x29	# offset of field containing offset of first pattern

# variables updated at song load
aSong		=	0	# address at which song is loaded - not used in this demonstrator
numChannels	=	0

# variables updated at play time
state		=	0	# play/stop
order		=	0
pos		=	0

# load song
fh = open('format', 'rb')
f  = bytearray(fh.read())

def main():
	init_reset()
	play_a_line()
	play_a_line()
	play_a_line()

# init/reset song
def init_reset():
	global numChannels, state, order, pos
	pos = 0
	numChannels = f[aSong + oNumChannels]
	order = f[aSong + oStartOfOrders]
	if order == f[aSong + oStartOfPatterns] + aSong:
		print "the song is zero length"
	print hex(numChannels)

def play_a_line():
	print "pos %d:", pos
	global numChannels, state, order, pos
	for channel in range(0, numChannels):
		pattern_num = f[order + channel]
		pattern = f[aSong + oStartOfPatterns] + pattern_num*kNumLinesInPattern*kNumBytesInLine
		line = f[pattern + (pos * kNumBytesInLine)]

		print hex(pattern_num), hex(pattern), hex(line)
	pos += 1
	print

# call main
main()
