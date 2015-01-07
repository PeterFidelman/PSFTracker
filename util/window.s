org	0x100
top:
			push	0xB800
			pop	es

			; first "channel"
			mov	si,pattern
			add	si,0
			mov	di,160*1
			call	pl_patternLine

			mov	si,pattern
			add	si,4
			mov	di,160*2
			call	pl_patternLine

			mov	si,pattern
			add	si,8
			mov	di,160*3
			call	pl_patternLine

			mov	si,pattern
			add	si,0x0C
			mov	di,160*4
			call	pl_patternLine

			; second "channel"
			mov	si,pattern
			add	si,0
			mov	di,160*1
			add	di,18
			call	pl_patternLine

			mov	si,pattern
			add	si,4
			mov	di,160*2
			add	di,18
			call	pl_patternLine

			mov	si,pattern
			add	si,8
			mov	di,160*3
			add	di,18
			call	pl_patternLine

			mov	si,pattern
			add	si,0x0C
			mov	di,160*4
			add	di,18
			call	pl_patternLine

			ret


; ---- Print a line in various formats ----

; Semantics:
; ds:SI = where to print from
; es:DI = where to print to

; Raw hex
pl_rawHex:
			mov	cx,.numBytesInLine
.another:		
			mov	al,[si]
			; High nybble
			movzx	bp,al
			shr	bp,4
			mov	ah,[ds:bp+higits]
			mov	[es:di],ah
			add	di,2
			; Low nybble
			movzx	bp,al
			and	bp,0x0F
			mov	ah,[ds:bp+higits]
			mov	[es:di],ah
			add	di,2+2			; Leave a blank space
			; Next byte
			inc	si
			dec	cx
			jnz	.another
.bail:			ret
.numBytesInLine	equ	16

; Pattern line
pl_patternLine:
.note:
			movzx	ax,[si]
			btr	ax,7
			jnc	.noNote
			cmp	al,0x7F
			je	.noteOff
			div	byte [.notesInOctave]	; ah=note, al=octave
			; Print note
			movzx	bp,ah
			shl	bp,1
			mov	cx,[bp+notes]		; lookup note & color
			mov	[es:di],cx		; print note
			; Print octave
			add	di,2
			mov	cl,al
			add	cl,0x30			; octave+'0'
			mov	ch,0x07			; white
			mov	[es:di],cx		; print octave
			add	di,2
			jmp	.instr
.noteOff:
			mov	cx,0x072D		; 07=white, 2D=' '
			mov	[es:di],cx
			add	di,2
			mov	[es:di],cx
			add	di,2
			jmp	.instr
.noNote:
			mov	cx,0x0720		; 07=white, 20=' '
			mov	[es:di],cx
			add	di,2
			mov	[es:di],cx
			add	di,2
.instr:
			mov	al,[si+1]
			bt	ax,6	
			mov	ch,0x1b			; 1b=blue/CYAN
			jnc	.noInstr
			; Instrument nybble
			mov	al,[si+2]
			movzx	bp,al
			shr	bp,4
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
			jmp	.volume
.noInstr:
			mov	cl,0x20			; 20=' '
			mov	[es:di],cx
			add	di,2
.volume:
			mov	ch,0x02			; 02=black/green
			mov	al,[si+1]
			bt	ax,7
			jnc	.noVolume
			; High nybble
			movzx	bp,al
			and	bp,0x003F		; Mask off enable-bits
			shr	bp,4
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
			; Low nybble
			movzx	bp,al
			and	bp,0x0F
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
			jmp	.effect
.noVolume:
			mov	cl,0x20			; 20=' '
			mov	[es:di],cx
			add	di,2
			mov	[es:di],cx
			add	di,2

.effect:
			mov	al,[si+2]
			and	al,0x0F
			mov	ch,0x1d			; 1D=blue/MAGENTA
			; Check for 000 effect
			cmp	al,0x00
			jne	.not000
			cmp	byte [si+3],0x00
			jne	.not000
			; effect is 000, draw blank.
			mov	cl,0x20			; 20=' '
			mov	[es:di],cx
			add	di,2
			mov	[es:di],cx
			add	di,2
			mov	[es:di],cx
			add	di,2
			jmp	.bail
.not000:
			; Nontrivial effect
			movzx	bp,al
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
			; Param...
			mov	al,[si+3]
			mov	ch,0x1e			; 1E=blue/YELLOW
			; ...high nybble
			movzx	bp,al
			shr	bp,4
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
			; ...low nybble
			movzx	bp,al
			and	bp,0x0F
			mov	cl,[ds:bp+higits]
			mov	[es:di],cx
			add	di,2
.bail:			ret
.notesInOctave:		db	0xC


higits:			db	'0','1','2','3','4','5','6','7'
			db	'8','9','A','B','C','D','E','F'

notes:			db	'c',0x0F,
			db	'c',0x0C,
			db	'd',0x0F,
			db	'd',0x0C,
			db	'e',0x0F,
			db	'f',0x0F,
			db	'f',0x0C,
			db	'g',0x0F,
			db	'g',0x0C,
			db	'a',0x0F,
			db	'a',0x0C,
			db	'b',0x0F

; ----- Dummy data to test printing -----
windowStuff:		db	0xDE, 0xAD, 0xBE, 0xEF
			db	0xCA, 0xFE, 0xBA, 0xBE
			db	0xDE, 0xFA, 0xCE, 0xD1
			db	0xDE, 0xCA, 0xDE, 0x69

pattern:		db	0x9C,0xC3,0x10,0x00
			db	0x00,0x00,0x0C,0x02
			db	0x9E,0x40,0x10,0x00
			db	0xFF,0x00,0x00,0x00
