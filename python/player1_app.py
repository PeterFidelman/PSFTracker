import opl2
import player1
import song1
import sys		# for argv

def main():
	song = song1.Song()
	song.loadFromFile(sys.argv[1])

	opl = opl2.OPL2()
	player = player1.Player(song, opl)

	while True:
		player.tick()
		opl.play()

		# Display neat-o visualizations.
		(order, channel, tick) = player.getPosition()
		print (order, channel, tick),
		print "\t",
		print [hex(i) for i in song._a[song.getOffsetToOrder(order): song.getOffsetToOrder(order)+song.getNumChannels()]]

main()
