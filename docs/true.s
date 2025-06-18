gcd: // x = u, y = v
move [x] to t1
move [y] to t2
[ans] = t2 - 0 (SET CPSR)
branch to link if equal (according to CPSR value)
t4 = t2 * t2 if not eq (according to CPSR value)
t4 = t1 / t4 if not eq (according to CPSR value)
t5 = t1 - t4 if not eq (according to CPSR value)
move t5 to [y] if not eq (according to CPSR value)
move t2 to [x] if not eq (according to CPSR value)
branch to gcd if not eq (according to CPSR value)

main:
x = input
y = input
move x to [x]
move y to [y]
branch to gcd
output [ans]

end