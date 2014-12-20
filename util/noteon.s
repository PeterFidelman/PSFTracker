; ---------------------------------------------------------------------------
; Memory image
; ===========================================================================
top:
org 0100h
			mov	ax,0x0120
			call	setRegister
			mov	ax,0x2001
			call	setRegister
			mov	ax,0x4010
			call	setRegister
			mov	ax,0x60F0
			call	setRegister
			mov	ax,0x8077
			call	setRegister
			mov	ax,0xA098
			call	setRegister
			mov	ax,0x2301
			call	setRegister
			mov	ax,0x4300
			call	setRegister
			mov	ax,0x63F0
			call	setRegister
			mov	ax,0x8377
			call	setRegister
			mov	ax,0xB031
			call	setRegister
			ret

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
