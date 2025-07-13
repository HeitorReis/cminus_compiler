# Importa a função e a classe diretamente dos seus arquivos correspondentes
from codegen import generate_assembly
from assembler import FullCode

# Caminhos relativos à raiz do projeto
ir_path = "docs/output/generated_IR.txt"
assembly_path = "docs/output/generated_assembly.txt"
machine_code_path = "docs/output/generated_machine_code.txt"

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

if 'Error' not in machine_code.response:
    # Escreve o código de máquina puro no ficheiro de saída
    with open(machine_code_path, 'w') as machine_code_file:
        machine_code_file.write(machine_code.full_code)
    
    # Imprime a versão de depuração detalhada no terminal
    print("--- DEBUG OUTPUT ---")
    print(machine_code.debug_output)
    print(f"\nCódigo de máquina gerado com sucesso em: {machine_code_path}")
else:
    # Imprime a mensagem de erro detalhada
    print(f"Falha na montagem: {machine_code.response}")