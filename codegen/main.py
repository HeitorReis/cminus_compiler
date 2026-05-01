# Importa a função e a classe diretamente dos seus arquivos correspondentes
from pathlib import Path

from codegen import generate_assembly
from assembler import FullCode

# Caminhos relativos à raiz do projeto, separados por módulo e função.
ir_path = Path("docs/generated/intermediate/semantic/ir/generated_IR.txt")
assembly_path = Path("docs/generated/intermediate/codegen/assembly/generated_assembly.txt")
machine_code_path = Path("docs/generated/final/assembler/machine_code/generated_machine_code.txt")
debug_assembly_path = Path("docs/generated/diagnostics/assembler/assembly_to_machine.txt")
debug_machine_code_path = Path("docs/generated/diagnostics/assembler/machine_code_decoded.txt")

for output_path in (
    assembly_path,
    machine_code_path,
    debug_assembly_path,
    debug_machine_code_path,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

# Lê o Código Intermediário
try:
    with open(ir_path, "r") as file:
        source_code = file.read()
except FileNotFoundError:
    print(f"Erro: Arquivo de IR não encontrado em '{ir_path}'")
    exit(1)

# Gera o código assembly
final_assembly = generate_assembly(source_code.splitlines())

print("--- ASSEMBLY CODE READY FOR YOUR ASSEMBLER ---")
print(final_assembly)
print("---------------------------------------------")

# Escreve o assembly gerado para ser usado pelo montador
with open(assembly_path, 'w') as file:
    file.write(final_assembly)

# Lê o arquivo de assembly recém-gerado
with open(assembly_path, 'r') as assembly_file:
    assembly_lines = assembly_file.readlines()

machine_code = FullCode(assembly_lines)

with open(debug_assembly_path, "w") as debug_assembly_file:
    debug_assembly_file.write(machine_code.debug_output)

if 'Error' not in machine_code.response:
    # Escreve o código de máquina puro no ficheiro de saída
    with open(machine_code_path, 'w') as machine_code_file:
        machine_code_file.write(machine_code.full_code)
    
    # Imprime a versão de depuração detalhada no terminal
    print("--- DEBUG OUTPUT ---")
    print(machine_code.debug_output)
    print(f"Mapeamento assembly->máquina salvo em: {debug_assembly_path}")
    print(f"\nCódigo de máquina gerado com sucesso em: {machine_code_path}")
else:
    # Imprime a mensagem de erro detalhada
    print(f"Falha na montagem: {machine_code.response}")

debug_log = machine_code.decode_machine_code()
print("--- MACHINE CODE DECODED ---")
with open(debug_machine_code_path, "w") as debug_file:
    debug_file.write(debug_log)
