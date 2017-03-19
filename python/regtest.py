import opl2
import crt

# Soundcard state
_registers = [0x20,0x00,0xff,0x0f,0x00,0x20,0x00,0xf6,0x5f,0x00,0x11,0x11,0x00]
_addresses = [0x23,0x43,0x63,0x83,0xe3,0x20,0x40,0x60,0x80,0xe0,0xa0,0xb0,0xc0]
_numRegisters = len(_registers)

#------------------------------------------------------------------------------
# Helpers
#==============================================================================
def printLabels():
	x = 0
	y = 1

	s1 = "; Carrier                 Modulator                Both"
	s2 = ";----------------------- ------------------------ --------------"
	s3 = ";Ctl KVol AD   SR   Wfm  Ctl  KVol AD   SR   Wfm  FLo  FHi+ Fdbk"

	lincrt.printAt(x, y+0, s1)
	lincrt.printAt(x, y+1, s2)
	lincrt.printAt(x, y+2, s3)

def printRegisters(registers, curRegister):
	x = 0
	y = 5
	for r in range(0, _numRegisters):
		# Get the hex value of this register.
		rstr = hex(_registers[r])[2:]
		# If it's one digit, pad with a leading '0'.
		if len(rstr) == 1:
			rstr = "0" + rstr
		# Print it.
		lincrt.printAt(x, y, rstr)
		# Add highlighting if it's the "current" register.
		if (r == curRegister):
			lincrt.printAt(x, y+1, "^^")
		else:
			lincrt.printAt(x, y+1, "  ")
		# Move on to the next one.
		x += 5

def applyRegisters(opl, registers):
	for r in range(0, _numRegisters):
		opl.writeReg(_addresses[r], _registers[r])

def getQuit(key):
	# Q or q
	return (key == 0x51) or (key == 0x71)

def getNewRegisterValue(key, registers, curRegister):
	newValue = 0
	newFlag = False

	# 0 through 9
	if (key >= 0x30) and (key <= 0x39):
		newFlag = True
		val = key - 0x30
		newValue = (registers[curRegister] << 4) & 0xff | val
	# A through F
	elif (key >= 0x41) and (key <= 0x46):
		newFlag = True
		val = key - 0x41 + 0xa
		newValue = (registers[curRegister] << 4) & 0xff | val
	# a through f
	elif (key >= 0x61) and (key <= 0x66):
		newFlag = True
		val = key - 0x61 + 0xa
		newValue = (registers[curRegister] << 4) & 0xff | val
	# Spacebar
	elif (key == 0x20):
		curRegister = 11
		newFlag = True
		newValue = registers[curRegister] ^ 0x20
	
	return (curRegister, newValue, newFlag)

def getNewActiveRegister(key, curRegister):
	# Previous register
	if (key == lincrt.kKeyLeft):
		return max(0, curRegister-1)
	# Next register
	elif (key == lincrt.kKeyRight):
		return min(_numRegisters-1, curRegister+1)
	else:
		return curRegister


#------------------------------------------------------------------------------
# Main
#==============================================================================
def main():
	curRegister = 0
	quitFlag = False

	newFlag = False
	newValue = None

	lastKey = None

	while(not quitFlag):
		printLabels()
		printRegisters(_registers, curRegister)

		key = lincrt.getKey()
		# hack: print keycode too :)
		if key != -1:
			lastKey = key
		lincrt.printAt(0, 0, "key code " + str(lastKey) + "     ")

		quitFlag = getQuit(key)
		curRegister = getNewActiveRegister(key, curRegister)
		(setRegister, newValue, newFlag) = getNewRegisterValue(
			key, _registers, curRegister)

		if (newFlag):
			_registers[setRegister] = newValue
			applyRegisters(opl, _registers)

		opl.play()

#------------------------------------------------------------------------------
# Call main
#==============================================================================
opl = opl2.OPL2()
# Enable other waveforms
opl.writeReg(0x01, 0x20)
lincrt = crt.CRT()
lincrt.wrapper(main)
