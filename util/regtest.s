; ---------------------------------------------------------------------------
; Memory image
; ===========================================================================
top:
org 0100h
			; Set register 01, bit 5.  This allows waveforms
			; other than sine.
			mov	ax,0x0120
			call	setRegister

			; Fall into the mainloop
.mainloop:
			mov	di,2*((80*0) + 0)	; y/x coords
			call	drawRegs
			call	keyboardHandler
			and	ax,ax
			jne	.quit
			call	commitRegs
			jmp	.mainloop
.quit:			
			mov	dword [registers],0x00000000
			mov	dword [registers+0x4],0x00000000
			mov	dword [registers+0x8],0x00000000
			mov	 word [registers+0xC],0x0000
			call	commitRegs
			ret

; ----- UI -----
keyboardHandler:
			mov	ah,0x01	; key present?
			int	0x16
			jz	.done	; nope
			mov	ah,0x00	; ok, remove from buffer
			int	0x16
			; was it quit?
			cmp	al,'q'
			je	.returnQuit
			; was it a nav key?
			cmp	al,'h'
			je	.left
			cmp	al,'l'
			je	.right
			; was it the noteon toggle?
			cmp	al,' '
			je	.noteonToggle
			; was it a hex digit?
			xor	bx,bx
.tryNextHigit:		cmp	al,[higits+bx]
			je	.hexFound
			inc	bx
			cmp	bx,0xF
			jbe	.tryNextHigit
			jmp	.done	; unknown key
.left:
			cmp	byte [.curRegister],0x00
			je	.done
			dec	byte [.curRegister]
			xor	ax,ax
			ret
.right:
			cmp	byte [.curRegister],kNumRegisters-1
			je	.done
			inc	byte [.curRegister]
			xor	ax,ax
			ret
.returnQuit:
			mov	ax,0xFFFF	; AX!=0 means QUIT!
			ret
.noteonToggle:
			xor	byte [registers+0xB],0x20
			xor	ax,ax
			ret
.hexFound:
			; digit in bx
			or	byte [.buf],bl
			inc	byte [.digitsEntered]
			cmp	byte [.digitsEntered],0x2
			jb	.prepNextDigit
			; digit ready
			mov	byte [.digitsEntered],0x0
			mov	al,byte [.buf]
			movzx	bx,byte [.curRegister]
			mov	[registers+bx],al
.prepNextDigit:		shl	[.buf],4
.done:			xor	ax,ax
			ret
.buf:			db	0x00
.digitsEntered:		db	0x00
.curRegister:		dw	0x0000

drawRegs:
			mov	ax,0xB800
			mov	es,ax
			xor	si,si
.nextReg:		mov	dl,[registers + si]
			movzx	bx,dl
			shr	bx,4
			mov	bl,[higits + bx]
			mov	[es:di],bl
			mov	bl,dl
			and	bl,0xF
			mov	bl,[higits + bx]
			add	di,2
			mov	[es:di],bl
			; Print mark?
			mov	al,0x20		; blank space
			cmp	si,[keyboardHandler.curRegister]
			jne	.noMark
			mov	al,0x11		; right arrow
.noMark:		add	di,2
			mov	byte [es:di],al
			add	di,2
			inc	si
			cmp	si,kNumRegisters
			jb	.nextReg
			ret

commitRegs:
			xor	si,si
.nextReg:		mov	al,[registers + si]
			mov	ah,[addresses + si]
			call	setRegister
			inc	si
			cmp	si,kNumRegisters
			jb	.nextReg
			ret

				; Carrier                 Modulator                Both
				;----------------------- ------------------------ --------------
				;Ctl KVol AD   SR   Wfm  Ctl  KVol AD   SR   Wfm  FLo  FHi+ Fdbk
registers:		db	0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
addresses:		db	0x23,0x43,0x63,0x83,0xE3,0x20,0x40,0x60,0x80,0xE0,0xA0,0xB0,0xC0
kNumRegisters		equ	13

; ----- Hardware -----
; Sets adlib register ah to the value al.
setRegister:
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
.killTime:
			in	al,dx
			loop	.killTime
			ret

; For debugging
;printAx:		push	cx
;			mov	cx,4
;.printDigit:		rol	ax,4
;			push	ax
;			movzx	eax,al
;			and	al,0xf
;			mov	al,[eax+higits]
;			mov	ah,0Eh
;			int	10h
;			pop	ax
;			loop	.printDigit
;			pop	cx
;			ret

higits:			db	'0','1','2','3','4','5','6','7'
			db	'8','9','a','b','c','d','e','f'

