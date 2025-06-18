test_fn:
load t0, [v]
mov t1, 0
cmpeq t2, t0, t1
brz L0, t2
mov t3, 1
mov retval, t3
ret
b L1
L0:
mov t4, 2
mov retval, t4
ret
L1:
ret
main:
bl test_fn
mov t5, retval
store [x], t5
mov t6, 1
mov retval, t6
ret
ret
