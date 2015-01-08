org	0x100
top:
			push	0xB800
			pop	es

			; Raw hex test.  See if it respects a width of 5.
			;mov	si,pattern	; where to print FROM
			;mov	di,5		; where to print TO (x)
			;mov	al,5		; where to print TO (y)
			;mov	bx,drawHexLine	; function to use for printing each line
			;mov	ch,5		; number of bytes of input consumed per output line
			;mov	dl,7		; number of lines to print
			;mov	cl,0		; starting line
			;mov	dh,1		; if nonzero, number the lines
			;mov	bp,16
			;call	drawWindow

			; Pattern line.
			mov	si,pattern	; where to print FROM
			mov	di,5		; where to print TO (x)
			mov	al,5		; where to print TO (y)
			mov	bx,drawPatternLine; function to use for printing each line
			mov	ch,4		; number of bytes of input consumed per output line
			mov	dl,7		; number of lines to print
			mov	cl,0		; starting line
			mov	dh,1		; if nonzero, number the lines
			mov	bp,16
			call	drawWindow

			ret

; ---- Draw a window ----

; Semantics:
; ds:SI = where to print FROM
;    BP = length of the above
;    DI = where to print TO (x)
;    AL = where to print TO (y)
;
;    BX = function to use for printing each line
;    CH = number of bytes of input consumed per line of output
;    
;    CL = starting line
;    DL = number of lines to print
;    DH = if nonzero, number the lines

drawWindow:
			pusha
			; Where to print to?
			mul	byte [.k160]	; ax = 160y
			shl	di,1
			add	di,ax		; [es:di] = char at (x,y)

			; Where to print from?
			mov	al,cl
			mul	ch		; ax = cl*ch
			add	si,ax
			add	bp,si		; bp = last valid byte

			; Ok, print the lines
			mov	al,cl		; initial line number
.loop:			; Print line number?
			and	dh,dh
			jz	.printLine	; ...no
						; ...yes
			test	al,0x03		; lines 0,4,8,C,... are major
			jz	.majorLine	; is this one major?
.minorLine:		mov	ah,0x07		; minor = white
			jmp	.printLineNumber
.majorLine:		mov	ah,0x0C		; major = red
.printLineNumber:	call	drawHexByteInColor; print line number...
			add	di,4
			mov	byte [es:di],0x20; ...and a trailing space
			mov	byte [es:di+1],ah; ...in the same color
			add	di,2
.printLine:		; Bounds-check
			cmp	si,bp		; If line starts out-of-bounds
			ja	.advanceWritePtr; then don't print.
			; Print line
			call	bx		; OK, use the function pointer
			; Move on to the next line
.advanceWritePtr:	add	di,160		; bump write-ptr to next line
			and	dh,dh		; did we print line number?
			jz	.advanceReadPtr	; ...no
			sub	di,(4+2)	; ...yes, so don't bump as far
.advanceReadPtr:	push	cx		; jigger with registers
			movzx	cx,ch		; ...so that we can...
			add	si,cx		; ...bump read-ptr to next line
			pop	cx		; unjigger registers
			inc	al		; increment line number
			dec	dl
			jnz	.loop
.bail			popa
			ret
.k160			db	160

; ---- Draw one line in various formats ----

; Semantics:
; ds:SI = where to print from
; es:DI = where to print to
;    CH = number of hex bytes to print in a line

; Raw hex
drawHexLine:
			pusha
			movzx	cx,ch
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
			add	di,2
			; Leave a blank space
			mov	byte [es:di],0x20
			add	di,2
			; Next byte
			inc	si
			dec	cx
			jnz	.another
.bail:			popa
			ret
.numInputBytesInLine	equ	4

; Pattern line
drawPatternLine:
			pusha
.note:			movzx	ax,[si]
			btr	ax,7
			jnc	.noNote
			cmp	al,0x7F
			je	.noteOff
			div	byte [.notesInOctave]	; ah=note, al=octave
			; Print note
			movzx	bp,ah
			shl	bp,1
			mov	cx,[bp+.noteToText]	; lookup note & color
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
			jmp	.done
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
.done:			popa
			ret
.notesInOctave:		db	0xC
.noteToText:		db	'c',0x0F,
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

; ----- Drawing primitives -----
; Byte in AL
; Color in AH
; Destination [ES:DI]
drawHexByteInColor:
			pusha
			; High nybble
			movzx	bp,al
			push	bp
			shr	bp,4
			mov	al,[ds:bp+higits]
			mov	[es:di],ax
			add	di,2
			; Low nybble
			pop	bp
			and	bp,0x0F
			mov	al,[ds:bp+higits]
			mov	[es:di],ax
			popa
			ret

; ----- Important tables -----
higits:			db	'0','1','2','3','4','5','6','7'
			db	'8','9','A','B','C','D','E','F'



; ----- Dummy data to test printing -----
windowStuff:		db	0xDE, 0xAD, 0xBE, 0xEF
			db	0xCA, 0xFE, 0xBA, 0xBE
			db	0xDE, 0xFA, 0xCE, 0xD1
			db	0xDE, 0xCA, 0xDE, 0x69

pattern:		db	0x9C,0xC3,0x10,0x00
			db	0x00,0x00,0x0C,0x02
			db	0x9E,0x40,0x10,0x00
			db	0xFF,0x00,0x00,0x00
