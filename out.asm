gcd:
load t0, [v]
mov t1, 0
add t2, t0, t1
brz L0, t2
load t3, [u]
mov retval, t3
ret
b L1
L0:
bl gcd
mov t4, retval
mov retval, t4
ret
L1:
load t5, [u]
load t6, [u]
load t7, [v]
div t8, t6, t7
load t9, [v]
mul t10, t8, t9
sub t11, t5, t10
load t12, [u]
load t13, [v]
add t14, t12, t13
add t15, t11, t14
ret
main:
bl input
mov t16, retval
store [x], t16
bl input
mov t17, retval
store [y], t17
bl output
mov t18, retval
ret
