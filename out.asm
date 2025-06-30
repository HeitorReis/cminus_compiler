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
load t5, [x]
mov arg0, t5
bl output
mov t6, retval
b L1
L0:
load t7, [y]
mov arg0, t7
bl output
mov t8, retval
L1:
ret
