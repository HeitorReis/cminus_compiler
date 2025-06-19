main:
bl input
mov t0, retval
store [x], t0
bl input
mov t1, retval
store [y], t1
load t2, [x]
load t3, [y]
cmpgt t4, t2, t3
brz L0, t4
bl output
mov t5, retval
b L1
L0:
bl output
mov t6, retval
L1:
ret
