Magic:			db      'X'

Version:		db	0x00

Channels:		db	0x04

Artist:			db      'e','d','l','i','n','f','a','n'
			db      ' ','(','p','e','t','e','r',')'

Title:			db      'T','e','s','t',' ','s','o','n'
			db      'g',' ','F','o','o','b','a','r'

StartOfInstruments:	dw      Instruments

StartOfSpFx:		dw	SpFx

StartOfOrders:		dw      Orders

StartOfPatterns:	dw      Patterns

Instruments:		db      0x20, 0x00, 0xF5, 0x0F, 0x00			; #0
			db	0x20, 0x00, 0x83, 0x48, 0x00
			db	0x00, 0x00, 0x00, 0x00, 0x00, 0x00

SpFx:			; TODO

Orders:			db	0x00,0x00,0x00,0x00
			; TODO - each pattern listed here probably needs a transposition byte too

Patterns:		;0
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
			db	0x00,0x00,0x00,0x00
