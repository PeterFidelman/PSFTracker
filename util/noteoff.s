; ---------------------------------------------------------------------------
; Memory image
; ===========================================================================
top:
org 0100h
			mov	ax,0xB000
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
