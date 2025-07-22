
from codegen import generate_assembly
from assembler import FullCode


ir_path = "docs/output/generated_IR.txt"
assembly_path = "docs/output/generated_assembly.txt"
machine_code_path = "docs/output/generated_machine_code.txt"


try:
    with open(ir_path, "r") as file:
        source_code = file.read()
except FileNotFoundError:
    print(f"Erro: Arquivo de IR não encontrado em '{ir_path}'")
    exit(1)


final_assembly = generate_assembly(source_code.splitlines())

print("--- ASSEMBLY CODE READY FOR YOUR ASSEMBLER ---")
print(final_assembly)
print("---------------------------------------------")


with open(assembly_path, 'w') as file:
    file.write(final_assembly)


with open(assembly_path, 'r') as assembly_file:
    assembly_lines = assembly_file.readlines()

machine_code = FullCode(assembly_lines)

if 'Error' not in machine_code.response:

    with open(machine_code_path, 'w') as machine_code_file:
        machine_code_file.write(machine_code.full_code)


    print("--- DEBUG OUTPUT ---")
    print(machine_code.debug_output)
    print(f"\nCódigo de máquina gerado com sucesso em: {machine_code_path}")
else:

    print(f"Falha na montagem: {machine_code.response}")

debug_log = machine_code.decode_machine_code()
print("--- MACHINE CODE DECODED ---")
with open("docs/output/debug_machine_code.txt", "w") as debug_file:
    debug_file.write(debug_log)
