; ---------------------------------------------------------------------------
; Constants
; ===========================================================================
; ----- Constants for the file format -----
kNumLinesInPattern	equ	32
kNumLinesInPatternShift	equ	5		; (1<<5) == 32
kNumBytesInLine		equ	3
koStartOfOrders		equ	0x22		; Offsets of fields in header
koStartOfSpFx		equ	0x24
koStartOfPatterns	equ	0x26

; ----- Constants for sizing virtual registers structure -----
kMaxChannels		equ	1

koNote			equ	0
koCoarse		equ	1
koFine			equ	2
;kNumVRegsInChannel	equ	8
kNumVRegsInChannelShift	equ	3		; (1 << 3) == 8

; ---------------------------------------------------------------------------
; Memory Image
; ===========================================================================
top:

; ----- Test harness -----
org 0100h
			mov	word [aSong],incSong
			call	reset
			mov	byte [playing],0x01
.mainLoop:		call	tick
			call	waitVRet
			jmp	.mainLoop
			ret
incSong:
	incbin		"testsong"

; ----- Variables updated at song load -----
aSong			dw	0x0000		; Address where song is loaded

; ----- Variables updated during playback ----
; Global
playing			db	0x00		; Play/Stop
aOrder			dw	0x0000
pos			db	0x00
ticks			db	0xFF
speed			db	0x06

; ----- Player API -----
reset:
			mov	bx,[aSong]
			; Go to the beginning of the song
			mov	ax,[bx + koStartOfOrders]
			cmp	ax,[bx + koStartOfPatterns]	; No orders?
			je	.fail
			add	ax,bx
			mov	[aOrder],ax			; First order
			xor	ax,ax
			mov	[pos],ah			; First line
			mov	byte [ticks],0xFF
			; Stop playback
			mov	[playing],ah
			ret
.fail:			stc
			ret

tick:
			; Playing?
			mov	al,[playing]
			and	al,al
			jz	.done			; ...no? Bye.
			; Time for next line?
			mov	al,[speed]
			dec	al
			cmp	[ticks],al
			jb	.notyet
			call	getLine
			mov	byte [ticks],0xFF	; tick=(-1)
.notyet:		inc	byte [ticks]		; tick++
			; apply FX
.apply:			call	applyEffect		; TODO
			;call	applySpFx		; TODO
			call	applyVRegs
			movzx	ax,byte [ticks]		; DEBUG
			call	printAx			; DEBUG
.done:			ret

; ----- Traversing the song -----
getLine:
			; Use (order, pos) to find the appropriate line
			mov	bx,[aOrder]
			movzx	dx,byte [bx]	; dx = pattern number

			shl	dx,kNumLinesInPatternShift
			mov	si,dx
			shl	dx,1			; x2...
			add	dx,si			; x3 bytes per line
			mov	bx,[aSong]
			add	bx,[bx+koStartOfPatterns]
			add	bx,dx		; bx = pattern start address
			movzx	dx,byte [pos]
			mov	si,dx
			shl	dx,1			; x2...
			add	dx,si			; x3 bytes per line
			add	bx,dx		; bx = line start address
			; update virtual registers and NoteOff
			call	applyNote
.goToNextLine:
			; advance to next line
			inc	byte [pos]
			cmp	byte [pos],kNumLinesInPattern ; At end of ptns?
			jb	.ok
			; advance to line 0 of next order
			mov	byte [pos],0x00
			inc	word [aOrder]	; advance #ch (1) to next order
			; at end of orders?
			mov	bp,[aSong]
			add	bp,[bp+koStartOfPatterns]
			cmp	word [aOrder],bp
			jb	.ok
			; ...if so, loop to the first order
			mov	bp,[aSong]
			add	bp,[bp+koStartOfOrders]
			mov	word [aOrder],bp
.ok:			ret

; ----- Parsing pattern lines into registers -----

; Semantics:  Apply pattern line starting at address BX.
;	      Don't modify this register.
;	      Because there's only 1 channel, CX is fair game.
applyNote:
			; Get note from line
			movzx	ax,[bx]
			; Check for new note
			btr	ax,7
			jnc	.notNew
			; Check for note-off
			cmp	ax,0x007f
			jne	.notNoteOff
			call	spkr_Off
			ret
.notNoteOff:
			mov	[vrNote],al
			mov	byte [vrCoarse],0x00
			mov	word [vrFine],0x0000
			call	spkr_On
.notNew:		ret

; Ditto
applyVRegs:
			xor	cx,cx
			movzx	si,byte [vrNote]
			add	si,word [vrCoarse]	; coarse tune
.normalizeFreq:
			cmp	si,0x000c
			jb	.doneNormalizing
			sub	si,0x000c
			inc	cl
			jmp	.normalizeFreq
.doneNormalizing:
			shl	si,1
			mov	ax,[freqTable+si]	; note
			shr	ax,cl			; octave
			add	ax,word [vrFine]	; fine tune
			call	spkr_SetFreq
			ret

applyEffect:		mov	ax,[bx+1]		; al=cmd, ah=param
			movzx	si,al
			cmp	si,0xF
			je	.cmdF
			shl	si,1
			jmp	[.jumpTab+si]
.jumpTab		dw	.cmd0	; 0 - ARP
			dw	.cmd1	; 1 - SLIDE UP
			dw	.cmd2	; 2 - SLIDE DOWN
			dw	.cmd3	; 3 - SLIDE TO NOTE
			dw	.cmd4	; 4 - VIBRATO
			dw	.bail	; 5 - ---
			dw	.bail	; 6 - ---
			dw	.bail	; 7 - ---
			dw	.bail	; 8 - ---
			dw	.bail	; 9 - ---
			dw	.bail	; A - ---
			dw	.cmdB	; B - POSITION JUMP
			dw	.cmdC	; C - FINE NOTE CUT
			dw	.cmdD	; D - PATTERN BREAK
			dw	.bail	; E - ---
			dw	.cmdF	; F - SPEED
.cmd0:			; 0 - ARP
			;and	ah,ah
			;jz	.bail		; 000 is nop
			mov	dx,ax
			movzx	ax,byte [ticks]
			mov	cl,3
			div	cl		; ah = remainder = arp pos
			mov	ch,ah		; ch = remainder = arp pos
			mov	cl,2
			sub	cl,ch
			shl	cl,2
			shr	dx,8
			shr	dl,cl		; dl = param >> 4*(2-arpPos)
			and	dl,0x0F		; last nybble only, please
			mov	[vrCoarse],dx
			ret
.cmd1:			; 1 - SLIDE UP
			movzx	ax,ah
			shl	ax,2	; calibrate slide to be more noticable
			sub	[vrFine],ax
			ret
.cmd2:			; 2 - SLIDE DOWN
			movzx	ax,ah
			shl	ax,2	; calibrate slide to be more noticable
			add	[vrFine],ax
			ret
.cmd3:			; 3 - SLIDE TO NOTE
			ret
.cmd4:			; 4 - VIBRATO
			ret
.cmdB:			; B - POSITION JUMP
			ret
.cmdC:			; C - FINE NOTE CUT
			cmp	ah,[ticks]
			jne	.bail
			call	spkr_Off
			ret
.cmdD:			; D - PATTERN BREAK
			ret
.cmdF:			; F - SPEED
			movzx	ax,ah
			mov	[speed],ax
.bail:			ret

applySpFx:		ret

vrNote:			times 1	db	0x00
vrCoarse:		times 1	dw	0x0000
vrFine:			times 1	dw	0x0000

;----- Hardware writes -----
; Set PIT2 to "frequency" AX
spkr_SetFreq:
			push	ax
			; Set PIT control word to:
			;  channel   2
			;  read/load 3 (LSB then MSB)
			;  mode num  3 (square wave)
			;  BCD?      0 (counter is binary, not BCD)
			mov	al,10_11_011_0b
			out	0x43,al
			pop	ax
			; Set PIT2 counter to AX
			out	0x42,al
			shr	ax,8
			out	0x42,al
			ret

; Turn on the PC speaker
; (connect it to PIT channel 2)
spkr_On:
			; When port 0x61 bit 0 and 1 are set, the PC
			; speaker will follow PIT2.
			in	al,0x61
			or	al,0x03
			out	0x61,al
			ret

; Turn off the PC speaker
spkr_Off:
			; When port 0x61 bit 0 is clear, the PC speaker
			; will follow port 0x61 bit 1.  So if you clear
			; both bits 0 and 1, the speaker disconnects from
			; PIT2 and also turns off.
			in	al,0x61
			and	al,0xFC
			out	0x61,al
			ret

; PC speaker control words for C-1 through B-1.
; (Calculated as 0x1234DD / freq).
; Divide by 2 to move up an octave.
freqTable:		dw	0x8e88,0x8683,0x7ef6,0x77d8
			dw	0x7120,0x6ac7,0x64c6,0x5f1e
			dw	0x59c9,0x54be,0x4ffc,0x4b7d

; For mainloop timing
waitVRet:
			mov	dx,0x03DA
.inVRet:		in	al,dx
			test	al,8
			jnz	.inVRet
.noVRet:		in	al,dx
			test	al,8
			jz	.noVRet
			ret

; For debugging
printAx:		push	cx
			mov	cx,4
.printDigit:		rol	ax,4
			push	ax
			movzx	eax,al
			and	al,0xf
			mov	al,[eax+.higits]
			mov	ah,0Eh
			int	10h
			pop	ax
			loop	.printDigit
			pop	cx
			ret
.higits:		db	'0','1','2','3','4','5','6','7'
			db	'8','9','a','b','c','d','e','f'

