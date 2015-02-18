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

; ----- Constants for the instrument format -----
koCarrier		equ	0
koModulator		equ	5

koMisc			equ	0		; Per-operator
koKSLVol		equ	1
koAD			equ	2
koSR			equ	3
koWaveform		equ	4

koFeedback		equ	10		; Per-instrument
koA			equ	11
koB			equ	12
koC			equ	13
koD			equ	14
koE			equ	15

kNumBytesInInstr	equ	16
kNumBytesInInstrShift	equ	4		; (1 << 4) == 16

; ----- Constants for sizing virtual registers structure -----
kMaxChannels		equ	9

koNote			equ	0
koCoarse		equ	1
koFine			equ	2
koCarrierBaseVol	equ	4
koCarrierExtraVol	equ	5
koModulatorBaseVol	equ	6
koModulatorExtraVol	equ	7

; ---------------------------------------------------------------------------
; Memory Image
; ===========================================================================
[map all player.map]
top:

; ----- Test harness -----
org 0100h
			mov	word [aSong],incSong
			call	reset
			mov	byte [playing],0x01
.mainLoop:		call	tick
			mov	ah,0x01		; check for key
			int	0x16
			jnz	.bail
			call	waitVRet	; kill some time
			jmp	.mainLoop
.bail:			mov	ah,0x00		; eat the key
			int	0x16
			call	reset		; turn off any stuck notes
			call	tick
			ret

incSong:
	incbin		"testsong"

; ----- Variables updated at song load -----
aSong			dw	0x0000		; Address where song is loaded
numChannels		db	0x09

; ----- Variables updated during playback ----
; Global
playing:		db	0x00		; Play/Stop
aOrder:			dw	0x0000
pos:			db	0x00
ticks:			db	0x00
speed:			db	0x06

vrNoteOn:		dw	0x0000
vrNote:			times kMaxChannels db 0x00
vrCoarse:		times kMaxChannels db 0x00
vrFine:			times kMaxChannels dw 0x0000
vrCarrierVolKSL:	times kMaxChannels db 0x00
vrCarrierVolAdj:	times kMaxChannels db 0x00
vrModulatorVolKSL:	times kMaxChannels db 0x00
vrModulatorVolAdj:	times kMaxChannels db 0x00


; ----- Adlib card tables -----
; The real registers that are not virtualized by any virtual register.
; These give each instrument its unique timbre.
nonVirtRegInstOffsets:	db	0x00,0x02,0x03,0x04,0x05,0x07,0x08,0x09
nonVirtRegBases:	db	0x23,0x63,0x83,0xE3,0x20,0x60,0x80,0xE0
kNumNonVirt		equ	8

; Offsets of the per-op registers.  Add 0x0 for modulator, 0x3 for carrier.
operatorOffsets:	db	0x00,0x01,0x02,0x08,0x09,0x0A,0x10,0x11,0x12

semitoneToFNumTable:	dw	0x0158,0x016d,0x0183,0x019a
			dw	0x01b2,0x01cc,0x01e7,0x0204
			dw	0x0223,0x0244,0x0266,0x028b

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
			mov	byte [ticks],0x00
			; Stop playback
			mov	[playing],ah
			ret
.fail:			stc
			ret

tick:
			; Playing?
			mov	al,[playing]
			and	al,al
			jz	.killNotes
			; If ticks=0, grab a line.
			mov	al,[ticks]
			and	al,al
			jnz	.skip
			call	getLine
			; Apply fx to all channels
.skip:			xor	ch,ch
			mov	cl,[numChannels]
.updateChannel:		dec	cl
			call	lookUpLine
			call	applyEffect
			call	applySpFx
			call	applyVRegs
			and	cl,cl
			jnz	.updateChannel
			; Tick.
			inc	byte [ticks]
			mov	al,[ticks]
			; Time for new line?
			cmp	al,byte [speed]
			jb	.done		; nope
			; If ticks>=speed, set ticks=0 for next time
			; and prepare to grab the next line.
			mov	byte [ticks],0x00
			inc	byte [pos]
			call	fixUpSongVars
.done:			ret
.killNotes:		; Turn off any stuck notes.
			; Won't work if ADSR is set for infinite length.
			xor	ax,ax
			mov	[vrNoteOn],ax
			jmp	.skip

; ----- Traversing the song -----
getLine:
			xor	cx,cx
			mov	cl,[numChannels]
.updateChannel:
			dec	cx
			call	lookUpLine
			; latch this line into virtual registers...
			; ... except for effect, which must be applied
			; per-tick.
			call	applyInstr
			call	applyNote
			call	applyVol
			and	cx,cx
			jnz	.updateChannel
			ret

; Use (order, channel, pos) to find the appropriate line.
; INPUT: channel in cl.
; OUTPUT: line start address in bx
lookUpLine:
			mov	bx,[aOrder]
			movzx	si,cl
			movzx	dx,byte [bx+si]	; dx = pattern number
			shl	dx,(kNumLinesInPatternShift + kNumBytesInLineShift)
			mov	bx,[aSong]
			add	bx,[bx+koStartOfPatterns]
			add	bx,dx		; bx = pattern start address
			movzx	dx,byte [pos]
			shl	dx,kNumBytesInLineShift
			add	bx,dx		; bx = line start address
			ret

; Check [pos].  If it's off the end of a pattern, update [aOrder] accordingly.
; INPUT, OUTPUT: void
fixUpSongVars:
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

; ----- Parsing pattern lines into registers -----

; Semantics:  Apply pattern line starting at address BX to channel CX.  Don't modify either register.
applyNote:		; Get note from line
			mov	dl,[bx]
			; Check for new note
			btr	dx,7
			jnc	.bail
			; Set virtual registers...
			; ... set the note frequency
			movzx	si,cl
			mov	[vrNote+si],dl
			; ... zero out the registers that should be reset
			; when encountering a new note
			mov	byte [vrCoarse+si],0x00
			shl	si,1
			mov	word [vrFine+si],0x0000
			; ... turn the note off, if a NoteOff was specified
			cmp	dl,0x7F
			jne	.bail
			btr	word [vrNoteOn],cx

.bail:			ret

applyVol:		; Get vol from line
			mov	dl,[bx+1]
			; Check for new vol
			bt	dx,7
			jnc 	.notNew
			; Set virtual register
			and	dl,0x3F			; Mask out deltas
			movzx	si,cl
			mov	byte [vrCarrierVolAdj+si],dl
.notNew:		ret

applyInstr:		; Get new-bits from line
			mov	dl,[bx+1]
			; Check for new instrument
			bt	dx,6
			jnc	.notNew
			; Find the instrument's contents
			movzx	dx,byte [bx+2]		; Get instr# from line
			shr	dx,4			; dx = instr number
			shl	dx,kNumBytesInInstrShift; dx = instr offset
			mov	si,word [aSong]
			add	si,[si+koStartOfInstruments]
			add	si,dx			; si = instr start addr
			movzx	bp,cl			; bp = channel #
			; Update virtual registers from instrument
			mov	dl,[si+koCarrier+koKSLVol]
			mov	[vrCarrierVolKSL+bp],dl	; carrier volume
			mov	dl,[si+koModulator+koKSLVol]
			mov	[vrModulatorVolKSL+bp],dl; modulator volume
			; ... zero out the virtual registers that should be
			; reset when encountering a new instrument
			mov	byte [bp+vrCarrierVolAdj],0x00
			mov	byte [bp+vrModulatorVolAdj],0x00
			; Update real registers that are not virtualized by
			; any virtual register.  These give each instrument
			; its unique timbre.

			; per-instrument registers (special case)
			mov	ah,0xC0
			add	ah,cl
			mov	al,[si+koFeedback]
			call	setAdlibRegister	; pesky feedback reg.
			mov	ah,0xB0
			add	ah,cl
			mov	al,0x00
			call	setAdlibRegister	; NoteOff reg. to 00
			bts	word [vrNoteOn],cx	; but set flag to 1.
			; This will flag the next virtual frequency commit
			; to turn the note back on (from 00).

			; per-op registers (general case)
			push	bx
			push	cx
			mov	cl,[bp+operatorOffsets]
			mov	bp,nonVirtRegInstOffsets
			mov	di,nonVirtRegBases
			mov	ch,kNumNonVirt
			; repeated...
.nextReg:		mov	ah,[di]			; ah = register base
			add	ah,cl			; ah = register address
			movzx	bx,byte [ds:bp]
			mov	al,[si+bx]		; al = byte from instr
			call	setAdlibRegister
			inc	di			; next register base
			inc	bp			; next byte from instr
			dec	ch
			jnz	.nextReg
			pop	cx
			pop	bx
.notNew:		ret

applyEffect:		;ret
			mov	ax,[bx+2]		; ah=param
			and	al,0x0F			; al=cmd
			movzx	si,al
			movzx	di,cl
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
			dw	.cmdE	; E - MODULATOR VOLUME
			dw	.cmdF	; F - SPEED
.cmd0:			; 0 - ARP
			;and	ah,ah
			;jz	.bail		; 000 is nop
			push	cx
			mov	dl,ah
			movzx	ax,byte [ticks]
			mov	cl,3
			div	cl		; ah = remainder = arp pos
			mov	cl,2
			sub	cl,ah
			shl	cl,2
			shr	dl,cl		; dl = param >> 4*(2-arpPos)
			and	dl,0x0F		; last nybble only, please
			mov	[di+vrCoarse],dl
			pop	cx
			ret
.cmd1:			; 1 - SLIDE UP
			movzx	ax,ah
			shl	di,1
			add	[di+vrFine],ax
			ret
.cmd2:			; 2 - SLIDE DOWN
			movzx	ax,ah
			shl	di,1
			sub	[di+vrFine],ax
			ret
.cmd3:			; 3 - SLIDE TO NOTE
			ret
.cmd4:			; 4 - VIBRATO
			ret
.cmdB:			; B - POSITION JUMP
			ret
.cmdC:			; C - FINE NOTE CUT
			movzx	ax,ah
			cmp	al,[ticks]
			jne	.bail
			btc	word [vrNoteOn],cx	; turn off note
			ret
.cmdD:			; D - PATTERN BREAK
			ret
.cmdE:			; E - MODULATOR VOLUME
			mov	[di+vrModulatorVolAdj],ah
			ret
.cmdF:			; F - SPEED
			movzx	ax,ah
			mov	[speed],al
.bail:			ret


applySpFx:		ret

; Semantics:  Apply VRegs of channel CL.
applyVRegs:
			; calculate semitone
			mov	di,cx			; di = channel
			movzx	si,byte [di+vrNote]	; si = semitone
			xor	ax,ax
			mov	al,[di+vrCoarse]
			add	si,ax			; apply coarse tuning
			; convert from semitone to f-number and octave
			xor	ch,ch
.normalize:		cmp	si,12
			jb	.done
			sub	si,12
			inc	ch			; Octave
			jmp	.normalize
.done:			and	ch,0x7			; max octave
			shl	si,1
			mov	dx,[si+semitoneToFNumTable] ; F-Num
			add	dx,[di+vrFine]		; apply fine tuning
			; F-NUMBER (low)
			mov	ah,0xA0
			add	ah,cl			; HW Register
			mov	al,dl			; F-Num (lo)
			call	setAdlibRegister
			; F-NUMBER (high) & Octave & NoteOn
			mov	ah,0xB0
			add	ah,cl			; HW Register
			mov	al,dh			; F-Num (hi)
			shl	ch,2
			or	al,ch			; Octave
			mov	cx,di
			bt	[vrNoteOn],cx
			jnc	.noNoteOn		; NoteOff
			or	al,0x20			; NoteOn
.noNoteOn:		call	setAdlibRegister
			; CARRIER VOLUME & KSL
			mov	ah,0x43
			add	ah,[di+operatorOffsets] ; HW Register
			mov	al,[di+vrCarrierVolKSL] ; Volume, KSL
			add	al,[di+vrCarrierVolAdj] ; Volume column
			call	setAdlibRegister
			; MODULATOR VOLUME & KSL
			mov	ah,0x40
			add	ah,[di+operatorOffsets]   ;HW Register
			mov	al,[di+vrModulatorVolKSL] ;Volume,KSL
			add	al,[di+vrModulatorVolAdj] ;Mod. volume cmd
			call	setAdlibRegister
			ret

;----- Hardware writes -----
; Sets adlib register ah to the value al.
setAdlibRegister:
			pusha
			mov	dx,0x388
			xchg	al,ah
			out	dx,al	; address
			mov	cx,6
			call	.killTime
			xchg	al,ah
			inc	dx
			out	dx,al	; data
			mov	cx,35
			call	.killTime
			popa
			ret
.killTime:		in	al,dx
			loop	.killTime
			ret

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
;printAx:		push	cx
;			mov	cx,4
;.printDigit:		rol	ax,4
;			push	ax
;			movzx	eax,al
;			and	al,0xf
;			mov	al,[eax+.higits]
;			mov	ah,0Eh
;			int	10h
;			pop	ax
;			loop	.printDigit
;			pop	cx
;			ret
;.higits:		db	'0','1','2','3','4','5','6','7'
;			db	'8','9','a','b','c','d','e','f'
;
