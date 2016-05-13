import curses

class CRT:
	def __init__(self):
		self.stdscr = curses.initscr()
		self.stdscr.nodelay(1)
		curses.noecho()
		curses.cbreak()
		self.stdscr.keypad(1)

	def moveTo(self, x, y):
		self.stdscr.move(y, x)

	def printAt(self, x, y, string):
		(oldy, oldx) = self.stdscr.getyx()
		self.stdscr.addstr(y, x, string)
		self.stdscr.move(oldy, oldx)
	
	def getKey(self):
		return self.stdscr.getch()
	
	def wrapper(self, function):
		try:
			function()
		finally:
			self.stdscr.keypad(0)
			curses.nocbreak()
			curses.echo()
			curses.endwin()
	
	def refresh(self):
		self.stdscr.refresh()

	kKeyNone	= -1
	kKeyUp		= 0x103
	kKeyDown	= 0x102
	kKeyLeft	= 0x104
	kKeyRight	= 0x105
	kKeyF1		= 0x109
	kKeyF2		= 0x10a

# Sample usage:  Something like...
#
#	def main():
#		lincrt.printAt(5, 5, "hello")
#	
#	lincrt = CRT()
#	lincrt.wrapper(main)
