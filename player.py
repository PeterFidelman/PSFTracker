# constants
kNumLinesInPattern	=	32
kNumBytesInLine		=	4
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
	while True:
		play_a_line()
		# let user hit key before continuing
		dummy = raw_input()

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
	global numChannels, state, order, pos
	print "pos %d:" % pos
	for channel in range(0, numChannels):
		pattern_num = f[order + channel]
		pattern = f[aSong + oStartOfPatterns] + pattern_num*kNumLinesInPattern*kNumBytesInLine
		line = f[pattern + (pos * kNumBytesInLine)]

		print "chan", hex(channel), "ptn", hex(pattern_num), "line", hex(line)
	# move on to next line
	pos += 1
	print

	# move on to next order if we're at the end of this one
	if pos == kNumLinesInPattern:
		pos = 0
		order += numChannels

		# loop to start of song if we're out of orders
		if order == f[aSong + oStartOfPatterns] + aSong:
			order = f[aSong + oStartOfOrders] + aSong

# call main
main()
