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
			;mov	ah,00h
			;int	16h
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
speed			db	0x06

; Virtual registers
;	note   (semitones) ------                   carrier volume (base) ---.
;	coarse (semitones +/-)---|----.             carrier volume (col +/-)-|----.
;	fine   (F-NUMBER  +/-)---|----|-------.     modul.  volume (base)----|----|----.
;	                         |    |       |     modul.  volume (col +/-)-|----|----|----.
;	                         |    |       |                              |    |    |    |
;				---- ---- ---------                         ---- ---- ---- ----
virtualRegisters:
	times kMaxChannels db	0x00,0x00,0x00,0x00,                        0x00,0x00,0x00,0x00	;ch0
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch1
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch2
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch3
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch4
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch5
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch6
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch7
			;db	0x00 0x00 0x00 0x00                         0x00 0x00 0x00 0x00	;ch8

; ----- Adlib card tables -----
; Locations of real registers
registerBases:		db	0x20,0x40,0x60,0x80,0xE0	; Carrier
			db	0x23,0x43,0x63,0x83,0xE3	; Modul
			db	0xC0

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
			cmp	ah,[speed]
			jb	.notyet
			call	getLine
			mov	byte [ticks],0xFF	; tick=(-1)
.notyet:		; Apply fx to all channels
			inc	byte [ticks]		; tick++
			xor	ecx,ecx
			mov	cl,[numChannels]
.updateChannel:		dec	cl
			call	applyEffect
			call	applySpFx
			call	latchRegs
			and	cl,cl
			jnz	.updateChannel
.done:			ret

; ----- Traversing the song -----
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
			call	applyNote
			call	applyVol
			call	applyInstr
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

; ----- Parsing pattern lines into registers -----

; Semantics:  Apply pattern line starting at address BX to channel CX.  Don't modify either register.
applyNote:		; Get note from line
			mov	dl,[bx]
			; Check for new note
			btr	dx,7
			jnc	.notNew
			; Set virtual registers
			lea	di,[virtualRegisters + ecx*8]
			mov	[di],dl			; Set note vreg
			inc	di
			mov	byte [di],0		; Set coarse vreg
			lea	di,[virtualRegisters + ecx*8 + koCarrierExtraVol]
			mov	byte [di],0		; Set carrier vol+- vreg
.notNew:		ret

applyVol:		; Get vol from line
			mov	dl,[bx+1]
			; Check for new vol
			bt	dx,7
			jnc 	.notNew
			; Set virtual register
			and	dl,0x3F			; dl = vol column value
			lea	di,[virtualRegisters + ecx*8 + koCarrierExtraVol]
			mov	[di],dl			; Set carrier vol+- vreg
.notNew:		ret

applyInstr:		; Get new-bits from line
			mov	dl,[bx+1]
			; Check for new instrument
			bt	dx,6
			jnc	.notNew
			; Set virtual registers
			movzx	dx,byte [bx+2]		; Get instr# from line
			shr	dx,4			; dx = instr number
			shl	dx,kNumBytesInInstrShift; dx = instr offset
			movzx	esi,word [aSong]
			add	si,[si+koStartOfInstruments]
			add	si,dx			; si = instr start addr
			mov	dl,[si+koCarrier+koKSLVol] ; dl = carrier volume and KSL
			lea	di,[virtualRegisters + ecx*8]
			mov	[di+koCarrierBaseVol],dl ; Set carrier vol vreg
			mov	dl,[si+koModulator+koKSLVol] ; dl = modul volume and KSL
			mov	[di+koModulatorBaseVol],dl ; Set modul vol vreg
			mov	byte [di+koModulatorExtraVol],0	; Set modul vol+- vreg
			mov	byte [di+koFine],0	; Set fine tune vreg
			; Set real registers
			mov	bp,cx
			xor	edi,edi
.setReg:		mov	al,[esi+edi]
			mov	ah,[registerBases+di]
			cmp	si,10
			jge	.perInstr
.perOp:			add	ah,[operatorOffsets+bp]
			sub	ah,cl
.perInstr:		add	ah,cl
			call	setAdlibRegister
			inc	di
			cmp	di,11
			jl	.setReg
			; Set note-on
			; TODO.  How?
.notNew:		ret

applyEffect:		ret
applySpFx:		ret

latchRegs:		mov	bp,cx
			mov	di,[virtualRegisters+ecx*8]
			mov	si,[di+koNote]	; si = semitone
			add	si,[di+koCoarse]; apply coarse tuning
			; convert from semitone to f-number and octave
			xor	cl,cl
.normalize:		cmp	si,12
			jl	.done
			sub	si,12
			inc	cl
			jmp	.normalize
.done:			mov	dx,[si+semitoneToFNumTable]
			add	dx,[di+koFine]  ; apply fine tuning
			; dx = F-NUMBER
			; cl = Octave

			; F-NUMBER (low)
			mov	ah,0xA0
			add	ah,[operatorOffsets+bp]
			mov	al,dl		; F-Num (lo)
			call	setAdlibRegister
			; F-NUMBER (high) & Octave & Note-On 
			add	ah,0x10
			mov	al,dh		; F-Num (hi)
			shl	cl,2
			or	al,cl		; Octave
			or	al,0x20		; Note-On (TODO doesn't belong here!)
			call	setAdlibRegister
			; Carrier volume & KSL
			sub	ah,0x70
			mov	al,[di+koCarrierBaseVol]
			add	al,[di+koCarrierExtraVol]
			call	setAdlibRegister
			; Modulator volume & KSL
			add	ah,0x3
			mov	al,[di+koModulatorBaseVol]
			add	al,[di+koModulatorExtraVol]
			call	setAdlibRegister
			mov	cx,bp
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
