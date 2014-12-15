; ---------------------------------------------------------------------------
; Constants
; ===========================================================================
; ----- Constants for the file format -----
kNumLinesInPattern	equ	32
kNumLinesInPatternShift	equ	5		; (1<<5) == 32
kNumBytesInLine		equ	4
kNumBytesInLineShift	equ	2		; (1<<2) == 4
koNumChannels		equ	0x02		; Offsets of fields in header
koStartOfInstruments	equ	0x23
koStartOfOrders		equ	0x25
koStartOfSpFx		equ	0x27
koStartOfPatterns	equ	0x29

; ----- Constants for sizing stuff -----
kMaxChannels		equ	9

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
			jmp	.mainLoop
			ret
incSong:
	incbin		"testsong"

; ----- Variables updated at song load -----
aSong			dw	0x0000		; Address where song is loaded
numChannels		db	0x09

; ----- Variables updated during playback ----
; Global
playing			db	0x00		; Play/Stop
aOrder			dw	0x0000
pos			db	0x00
ticks			db	0xFF

; ----- Song parameters -----
speed			db	0x06

; Per-channel

; ----- Player API -----
reset:
			mov	bx,[aSong]
			; Update the number of channels
			mov	ah,[bx + koNumChannels]
			mov	[numChannels],ah
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
			mov	ah,[playing]
			and	ah,ah	
			jz	.done			; ...no? Bye.
			; Time for next line?
			mov	ah,[ticks]
			inc	ah
			cmp	ah,[speed]
			jb	.notyet
			call	getLine
			mov	byte [ticks],0xFF	; tick=(-1)
.notyet:		; Apply fx to all channels
			inc	byte [ticks]		; tick++
			mov	cl,[numChannels]
.updateChannel:		dec	cl
			call	effectTick
			call	spFxTick
			and	cl,cl
			jnz	.updateChannel
.done:			ret

; ----- Player helpers -----
getLine:
			xor	ecx,ecx
			mov	cl,[numChannels]
.updateChannel:
			dec	cx
			; Use (order, channel, pos) to find the appropriate line
			mov	bx,[aOrder]
			mov	si,cx
			movzx	dx,byte [bx+si]	; dx = pattern number
			shl	dx,(kNumLinesInPatternShift + kNumBytesInLineShift)
			mov	bx,[aSong]
			add	bx,[bx+koStartOfPatterns]
			add	bx,dx		; bx = pattern start address
			movzx	dx,byte [pos]
			shl	dx,kNumBytesInLineShift
			add	bx,dx		; bx = line start address
			; make channel play line
			; (TODO)
			and	cx,cx
			jnz	.updateChannel
.goToNextLine:
			; advance to next line
			inc	byte [pos]
			cmp	byte [pos],kNumLinesInPattern ; At end of ptns?
			jb	.ok
			; advance to line 0 of next order
			mov	byte [pos],0x00
			movzx	ax,byte [numChannels]
			add	word [aOrder], ax
			; at end of orders?
			mov	bx,[aSong]
			add	bx,[bx+koStartOfPatterns]
			cmp	word [aOrder],bx
			jb	.ok
			; ...if so, loop to the first order
			mov	bx,[aSong]
			add	bx,[bx+koStartOfOrders]
			mov	word [aOrder],bx
.ok:			ret

; Semantics:  These all act on channel CX.  Must not modify CX.
noteTick:		ret
instrTick:		ret 
volTick:		ret
effectTick:		ret
spFxTick:		ret

