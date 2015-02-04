org 0x100
top:
		mov	ah,0x11
		int	0x16			; Key hit?
		jz	top			; ...no... redo from start
		call	getKey
		call	printAx			; Print what key it was
		cmp	al,0x1b			; ESC=exit?
		je	.bail
		jmp	top			; ...redo from start
.bail		ret

getKey:
		call	getScanCode
		cmp	ah,0xE0			; Was it an extended key?
		jne	.done
		call	getScanCode		; Yes, get the backing value
.done		ret

getScanCode:
		mov	ah,0x10
		int	0x16			; AH=Scan code, AL=Character
		ret

; For debugging only
printAx:
		push	cx
		mov	cx,4
.printDigit:	rol	ax,4
		push	ax
		movzx	eax,al
		and	al,0xf
		mov	al,[eax+.higits]
		mov	ah,0x0e
		int	0x10
		pop	ax
		loop	.printDigit
		pop	cx
		ret
.higits		db	'0','1','2','3','4','5','6','7'
		db	'8','9','a','b','c','d','e','f'
