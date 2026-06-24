# Documentacao tecnica modular do compilador C-

Este documento organiza a documentacao do projeto por grupos funcionais. A divisao acompanha a arquitetura real do repositorio: front-end em C/Flex/Bison, geracao de IR em C, back-end e montador em Python, ferramentas de regressao, simulador de codigo de maquina e o processador alvo `Processor(v2026-1)`.

## Visao geral do pipeline

| Grupo | Arquivos principais | Responsabilidade | Artefatos gerados |
| --- | --- | --- | --- |
| Orquestracao | `main.c`, `Makefile` | Executar o fluxo, selecionar entradas e organizar diretorios de saida. | Logs em `docs/generated/diagnostics/` |
| Lexico e sintatico | `parser/lexer.l`, `parser/parser.y` | Transformar C- em tokens, validar a gramatica e construir a AST. | `docs/generated/frontend/syntax_tree/ast.txt` |
| Estruturas do front-end | `src/syntax_tree.*`, `src/symbol_table.*`, `src/utils.*`, `src/analysis_state.*` | Representar AST, escopos, simbolos e estado de erro. | Tabela de simbolos e diagnosticos |
| Semantica e IR | `src/semantic.*`, `src/ir.*` | Validar tipos, escopos, chamadas, retornos e gerar codigo intermediario. | `docs/generated/intermediate/semantic/ir/generated_IR.txt` |
| Back-end | `codegen/codegen.py`, `codegen/symbol_table.py`, `codegen/constants.py` | Traduzir IR para assembly, montar frames de pilha e alocar registradores. | `docs/generated/intermediate/codegen/assembly/generated_assembly.txt` |
| Montador | `codegen/assembler.py` | Resolver rotulos, expandir literais/desvios longos e codificar palavras de 32 bits. | `docs/generated/final/assembler/machine_code/generated_machine_code.txt` |
| Verificacao | `tools/run_analysis_regressions.py`, `codegen/assembler_regressions.py`, `tools/run_machine_code.py` | Validar front-end, montador e comportamento de maquina em modelo Python. | Relatorios em `docs/generated/batch/` e `docs/generated/diagnostics/machine_runner/` |
| Processador alvo | `Processor(v2026-1)/*.v`, `Processor(v2026-1)/modules/*.v` | Definir a arquitetura executora do codigo de maquina. | Projeto Quartus, ROM e simulacoes |

O contrato entre as fases e textual: o front-end grava a IR em arquivo, o back-end le essa IR, gera assembly, e o montador grava uma linha binaria de 32 bits por instrucao ou palavra de dados.

## Orquestracao e ciclo de build

### `main.c`

| Funcao | Logica implementada |
| --- | --- |
| `main(int argc, char **argv)` | Valida a linha de comando, abre o arquivo C-, reinicia o estado de analise, cria diretorios de saida, remove IR antiga, inicializa escopos e tabela de simbolos, declara `input()` e `output(int)`, chama `yyparse()`, bloqueia a continuidade se houver erro lexico/sintatico, imprime e salva a AST, executa `semanticAnalyze()`, valida `main`, imprime e salva a tabela de simbolos, libera a AST e fecha o arquivo. |
| `declareBuiltins(SymbolTable *table)` | Insere as funcoes nativas `input` e `output` no escopo global. `input` retorna `int` e nao recebe parametros; `output` retorna `void` e recebe um `int`. |
| `ensureDir(const char *path)` | Garante a existencia de um diretorio. Em caso de falha diferente de `EEXIST`, apenas emite aviso para nao abortar indevidamente a compilacao. |
| `ensureOutputDirs(void)` | Cria a arvore minima de diretorios sob `docs/generated/` usada por AST, tabela de simbolos e IR. |
| `writeAstFile(const AstNode *root)` | Abre `docs/generated/frontend/syntax_tree/ast.txt`, serializa a AST com indentacao e relata o caminho salvo. |
| `writeSymbolTableFile(const SymbolTable *table)` | Abre `docs/generated/frontend/symbol_table/symbol_table.txt`, serializa a tabela de simbolos e relata o caminho salvo. |

### `Makefile`

| Alvo | Funcao no fluxo |
| --- | --- |
| `make` / `all` | Executa `clean` e depois `run`; e um fluxo completo, nao apenas compilacao. |
| `bin/c-c` | Gera lexer/parser, compila objetos C e liga o executavel do front-end. |
| `run TEST=<id>` | Executa um caso de teste, grava log do front-end, chama `codegen/main.py` e, opcionalmente, o simulador com `TRACE=1`. |
| `run_all` | Executa a suite positiva configurada e copia os codigos de maquina finais para `docs/generated/batch/final_machine_code/`. |
| `run_all COMPLETE=1` | Alem de gerar os binarios, executa `tools/run_machine_code.py` para cada saida. |
| `test_analysis` | Roda a suite de regressao do front-end em diretorios temporarios. |
| `generate_analysis_vpp` / `generate_sysml_vpp` | Atualiza os diagramas SysML no arquivo `.vpp`. |
| `clean` | Remove `build/`, `bin/`, `parser.gv` e `parser.output`; nao limpa `docs/generated/`. |

## Analise lexica e sintatica

### `parser/lexer.l`

O lexer reconhece palavras-chave, identificadores, numeros, operadores aritmeticos/relacionais, delimitadores, comentarios de bloco e erros lexicos. Cada token valido e retornado ao Bison com informacao semantica quando necessario: `NUM` usa `yylval.ival` e `ID` usa `yylval.sval`.

| Funcao/regra | Logica implementada |
| --- | --- |
| Regras de palavras-chave | Reconhecem `if`, `else`, `while`, `return`, `int` e `void` antes da regra de identificador, evitando que palavras reservadas sejam tratadas como `ID`. |
| Regras de operadores | Retornam tokens para comparacao (`EQ`, `NEQ`, `LTE`, `LT`, `GTE`, `GT`), atribuicao, aritmetica, modulo e pontuacao. |
| Regra de `NUM` | Converte o lexema decimal para inteiro com `atoi`, grava em `yylval.ival` e retorna `NUM`. |
| Regra de `ID` | Duplica o lexema com `strdup`, grava em `yylval.sval` e retorna `ID`. A memoria passa a ser responsabilidade da acao do parser. |
| Regra de erro `.` | Emite erro lexico com linha, chama `recordLexicalError()` e retorna `LEX_ERROR`. |
| `ignore_comment()` | Consome caracteres apos `/*` ate encontrar `*/`, atualizando manualmente `yylineno` quando encontra quebra de linha. |

### `parser/parser.y`

O parser implementa a gramatica de C- e tambem aciona a construcao da AST e da tabela de simbolos. As declaracoes sao registradas durante a reducao sintatica; as validacoes semanticas completas ficam em `src/semantic.c`.

| Regra/funcao | Logica implementada |
| --- | --- |
| `program` | Cria o no `AST_PROGRAM` e anexa todas as declaracoes globais. |
| `declaration_list` | Encadeia declaracoes globais por `nextSibling`. |
| `var_declaration` | Declara variavel escalar ou vetor no escopo atual, cria `AST_VAR_DECL` e preserva tipo, tamanho e linha. |
| `fun_declaration` | Declara a funcao no escopo global, abre escopo de funcao, processa parametros e corpo, cria `AST_FUN_DECL`, calcula tipos dos parametros e chama `setFunctionParams()`. |
| `params`, `param_list`, `param` | Representam parametros escalares e parametros-vetor (`int a[]`). Vetores-parametro usam `array_size = -1`. |
| `compound_stmt` e `block_scope` | Criam um escopo unico para cada bloco, preservam esse nome no no `AST_BLOCK` e fecham o escopo ao fim do bloco. |
| `statement_list` e `statement` | Organizam expressoes, blocos, condicionais, lacos e retornos. |
| `expression_stmt` | Retorna a expressao ou cria um bloco vazio para preservar a forma da AST em comandos vazios. |
| `selection_stmt` | Cria `AST_IF` com condicao, ramo `then` e ramo `else` opcional; usa precedencia para resolver o `dangling else`. |
| `iteration_stmt` | Cria `AST_WHILE` com condicao e corpo. |
| `return_stmt` | Cria `AST_RETURN`, com ou sem expressao filha. |
| `expression` | Distingue atribuicao (`AST_ASSIGN`) de expressoes simples. |
| `var` | Cria `AST_ID` para identificador simples ou `AST_ARRAY_ACCESS` para acesso indexado. |
| `simple_expression`, `additive_expression`, `term` | Constroem `AST_BINOP` com filhos na ordem `esquerda`, `AST_OP`, `direita`. |
| `relop`, `addop`, `mulop` | Criam nos `AST_OP`; `mulop` inclui `%`. |
| `factor`, `call`, `args`, `arg_list` | Representam parenteses, variaveis, chamadas de funcao, literais e listas de argumentos. |
| `yyerror(const char *msg)` | Evita duplicar erro sintatico quando o erro veio de token lexico pendente; caso contrario, registra erro sintatico com linha. |

## Estado de erro, AST, escopos e tabela de simbolos

### `src/analysis_state.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `resetAnalysisState()` | Zera contadores de erro lexico, sintatico e pendencia lexica antes de cada compilacao. |
| `recordLexicalError()` | Incrementa erros lexicos e marca que o proximo `yyerror` deve ser consumido sem emitir erro sintatico duplicado. |
| `recordSyntaxError()` | Incrementa erros sintaticos. |
| `consumePendingLexicalError()` | Retorna e limpa a pendencia lexica, permitindo que o parser diferencie erro de token invalido de erro gramatical real. |

### `src/syntax_tree.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `newNode(AstNodeKind kind)` | Aloca e inicializa um no generico da AST, com ponteiros nulos, linha zero e campos semanticos zerados. |
| `newIdNode(const char *name, int lineno)` | Cria `AST_ID`, duplica o nome e registra a linha. |
| `newNumNode(int value, int lineno)` | Cria `AST_NUM`, armazena o valor literal e registra a linha. |
| `newOpNode(const char *op, int lineno)` | Cria `AST_OP`, duplica o texto do operador e registra a linha. |
| `addChild(AstNode *parent, AstNode *child)` | Acrescenta um filho ao fim da lista de filhos do pai. A AST e n-aria por lista encadeada de filhos/irmaos. |
| `printAstToStream(FILE *out, const AstNode *node, int indent)` | Serializa a AST de forma recursiva, imprimindo tipo do no, nome/valor quando aplicavel e linha. |
| `printAst(const AstNode *node, int indent)` | Encaminha a impressao para `stdout`. |
| `freeAst(AstNode *node)` | Libera recursivamente filhos, nomes duplicados e o proprio no. |

### `src/utils.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `initScopeStack()` | Reinicia a pilha de escopos, o contador de blocos e `currentScope = "global"`. |
| `getScopeDepth()` | Retorna a profundidade atual da pilha de escopos. |
| `getScopeNameAt(int index)` | Retorna o nome de um escopo ativo por indice, ou `NULL` se o indice for invalido. |
| `isScopeActive(const char *name)` | Verifica se um escopo esta na cadeia ativa; `global` e sempre considerado ativo. |
| `pushScope(const char *name)` | Duplica o nome do escopo, empilha e atualiza `currentScope`. Aborta se ultrapassar `MAX_SCOPE_DEPTH`. |
| `pushBlockScope()` | Gera nome unico no formato `<escopo>#block<N>` e chama `pushScope()`. |
| `popScope()` | Libera o nome do topo, desempilha e restaura `currentScope` para o escopo anterior ou `global`. |

### `src/symbol_table.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `appendLine(LineNode **head, int line)` | Acrescenta uma linha em lista encadeada de declaracoes ou usos. |
| `findSymbol(...)` | Busca simbolo com nome e escopo exatos; e auxiliar interno. |
| `initSymbolTable(SymbolTable *table)` | Inicializa a lista de simbolos como vazia. |
| `declareSymbol(...)` | Declara ou atualiza um simbolo. Para funcoes, `dataType` representa retorno; para vetores, `dataType = TYPE_ARRAY`, `baseType` guarda o tipo base e `array_size` diferencia vetor declarado (`>0`) de parametro-vetor (`-1`). |
| `registerSymbolUse(Symbol *symbol, int useLine)` | Registra uma linha de uso para um simbolo resolvido. |
| `getSymbol(SymbolTable *table, const char *name, const char *scope)` | Retorna simbolo por nome e escopo exatos. |
| `resolveSymbol(SymbolTable *table, const char *name, const char *scope)` | Resolve identificadores procurando dos escopos ativos mais internos para os externos, depois o escopo informado e por fim `global`. |
| `setFunctionParams(...)` | Grava quantidade e tipos de parametros de uma funcao, copiando o vetor recebido. |
| `getParamCount(...)` | Retorna a quantidade de parametros de uma funcao ou `-1` se a consulta for invalida. |
| `getParamType(...)` | Retorna o tipo de um parametro por indice ou `-1` quando fora da faixa. |
| `printSymbolTableToStream(...)` | Serializa nome, escopo, especie, linhas de declaracao, linhas de uso e tipo. |
| `printSymbolTable(...)` | Encaminha a serializacao para `stdout`. |

Matriz de resolucao de identificadores:

| Situacao | Ordem de busca | Resultado esperado |
| --- | --- | --- |
| Variavel local em bloco interno | bloco atual -> blocos externos -> funcao -> global | usa a declaracao mais proxima. |
| Sombreamento de nome | escopo mais interno antes do externo | aceita declaracoes homonimas em escopos distintos. |
| Funcao chamada por nome | busca direta em `global` durante a chamada | funcoes sao globais. |
| Identificador inexistente | cadeia ativa + global sem sucesso | erro semantico de identificador nao declarado. |

## Analise semantica

### `src/semantic.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `semanticAnalyze(AstNode *root, SymbolTable *symtab)` | Ponto de entrada: remove IR antiga, valida que a raiz e `AST_PROGRAM`, reinicia escopos, percorre o programa, verifica `main`, e gera IR somente se nao houver erros. |
| `semanticError(...)` | Emite diagnostico com linha e incrementa contador de erros do contexto. |
| `typeName(ExpType type)` | Converte tipo interno para texto usado em mensagens. |
| `hasEarlierDeclaration(const Symbol *symbol, int line)` | Detecta redeclaracao verificando se ja existia linha de declaracao anterior para o mesmo simbolo. |
| `hasMainFunction(SymbolTable *symtab)` | Confirma existencia de funcao global `main`. |
| `analyzeProgram(...)` | Percorre declaracoes globais. |
| `analyzeDeclaration(...)` | Despacha declaracoes de variavel e funcao. |
| `analyzeVariableDeclaration(...)` | Valida redeclaracao, tipo `void` invalido para variaveis e vetores, e atualiza metadados do simbolo. |
| `analyzeFunctionDeclaration(...)` | Valida redeclaracao de funcao, parametros, retorno declarado, corpo de bloco e obrigatoriedade de retorno em funcoes `int`. |
| `analyzeBlock(...)` | Reproduz o escopo do bloco salvo na AST e analisa declaracoes locais antes de comandos. |
| `analyzeStatement(...)` | Valida `if`, `while`, `return`, blocos e expressoes usadas como comando. |
| `analyzeAssignmentTarget(...)` | Garante que o lado esquerdo da atribuicao seja variavel escalar ou elemento de vetor, nunca funcao nem vetor inteiro. |
| `analyzeArrayAccess(...)` | Valida existencia do vetor, especie de simbolo, tipo de vetor e tipo inteiro do indice. |
| `analyzeExpression(...)` | Infere tipos de literais, ids, binarios, atribuicoes, chamadas e acessos a vetor; registra usos e valida aridade/tipos de chamada. |
| `statementGuaranteesReturn(...)` | Determina se um comando garante retorno; `if` so garante quando ambos os ramos garantem. |
| `blockGuaranteesReturn(...)` | Determina se algum comando executavel do bloco garante retorno, ignorando declaracoes. |

Principais invariantes semanticas:

| Regra | Implementacao |
| --- | --- |
| `main` global obrigatoria | `hasMainFunction()` e `report.missing_main`. |
| Variavel `void` invalida | `analyzeVariableDeclaration()` e validacao de parametros. |
| Chamada com aridade correta | `getParamCount()` comparado com total de argumentos. |
| Operadores binarios sobre `int` | `analyzeExpression()` exige `TYPE_INT` nos dois operandos. |
| Funcao `int` retorna valor | `blockGuaranteesReturn()` aplicado ao corpo. |

## Geracao de codigo intermediario

### `src/ir.c/h`

| Funcao | Logica implementada |
| --- | --- |
| `generate_ir(AstNode *root, SymbolTable *symtab)` | Cria lista de IR, reinicia contadores de temporarios/rotulos, emite declaracoes globais, percorre funcoes e remove codigo inalcançavel. |
| `generate_global_declarations(...)` | Emite `IR_DEC` para variaveis globais escalares (`.word 0`) e vetores (`.space tamanho`). |
| `generate_ir_for_node(...)` | Despacha nos de programa, funcao, bloco, `if`, `while`, `return`, atribuicao, chamada, declaracao e demais estruturas. |
| `generate_ir_for_expr(...)` | Produz operandos para literais, ids, atribuicoes, binarios, chamadas e acessos a vetor. O operador `%` e rebaixado para `div`, `mul` e `sub`. |
| `is_array_param(...)` | Distingue parametro-vetor de vetor alocado, pois parametro ja contem endereco base. |
| `emit(...)` | Aloca instrucao, copia operandos com seguranca e adiciona ao fim da lista encadeada. |
| `copy_operand(...)` | Duplica nomes e rotulos para evitar aliasing de ponteiros entre instrucoes. |
| `new_temp()` | Cria temporario `t<N>`. |
| `new_label()` | Cria rotulo `L<N>`. |
| `new_const(int value)` | Cria operando constante. |
| `new_name(const char *name)` | Cria operando de nome. |
| `remove_unreachable_code(IRList *list)` | Remove instrucoes apos `goto` ou `return` ate o proximo rotulo. |
| `print_operand(...)` | Serializa operando de IR. |
| `print_instruction_to_stream(...)` | Serializa uma instrucao de IR no formato textual consumido pelo back-end. |
| `print_ir(IRList *list, char *file_path)` | Imprime IR no terminal e no arquivo indicado. |
| `free_ir_instr(...)` | Libera uma instrucao individual, incluindo nomes/rotulos duplicados. |
| `free_ir(IRList *list)` | Libera a lista inteira de IR. |
| `kind_to_string(AstNodeKind kind)` | Converte especie de no da AST para diagnosticos de depuracao. |

Matriz de traducao AST -> IR:

| AST | IR gerada |
| --- | --- |
| Declaracao global escalar | `x := .word, 0` |
| Declaracao global/vetor local | `a := .space, N` |
| Atribuicao escalar | `x := valor` |
| Atribuicao em vetor | `end := base + indice`; `*end := valor` |
| Acesso a vetor | `end := base + indice`; `t := *end` |
| `if` | comparacao, `if_false`, labels de else/fim e `goto` de fechamento. |
| `while` | label inicial, condicao, `if_false` para fim, corpo e `goto` para inicio. |
| Chamada `int` | `arg ...`; `t := call f, n` |
| Chamada `void` | `arg ...`; `call f, n` |
| `return e` | `return e` |

Observacao importante: a memoria da maquina e enderecada por palavra, nao por byte. Por isso o IR atual soma o indice ao endereco base do vetor; nao multiplica por 4.

## Back-end Python e assembly

### `codegen/constants.py`

| Constante | Valor | Uso |
| --- | --- | --- |
| `STACK_WORDS` | `64` | Tamanho logico da pilha no modelo do compilador/simulador. |
| `INITIAL_SP` | `63` | Valor inicial de `sp` em `main`. |
| `DATA_SECTION_BASE` | `64` | Primeiro endereco conceitual usado para dados globais no gerador. |

### `codegen/symbol_table.py`

| Classe/funcao | Logica implementada |
| --- | --- |
| `Type` | Classe base para tipos do back-end. |
| `IntegerType.__init__()` | Define tamanho de inteiro como uma palavra. |
| `IntegerType.__repr__()` | Retorna `INT` para logs. |
| `ArrayType.__init__(base_type, num_elements)` | Guarda tipo base, quantidade de elementos e tamanho total em palavras. |
| `ArrayType.__repr__()` | Retorna representacao textual do vetor. |
| `Symbol.__init__(name, symbol_type, scope, address)` | Representa uma variavel do back-end com nome, tipo, escopo e endereco. |
| `Symbol.__repr__()` | Retorna texto de depuracao do simbolo. |
| `SymbolTable.__init__()` | Cria dicionario interno de simbolos por nome. |
| `SymbolTable.add_symbol(symbol)` | Insere simbolo e registra em log. |
| `SymbolTable.get_symbol(name)` | Busca simbolo pelo nome. |

### `codegen/codegen.py`

| Funcao/classe | Logica implementada |
| --- | --- |
| `is_ir_temp(name)` | Detecta temporarios `tN` e temporarios de retorno `t_ret_N`. |
| `is_integer_literal(token)` | Reconhece inteiros positivos e negativos em texto. |
| `DataMemoryManager.__init__()` | Inicializa base da secao de dados, proximo deslocamento e mapa variavel-endereco. |
| `DataMemoryManager.register_variable(var_name, size)` | Reserva endereco para variavel global, reaproveitando endereco se ja existir. |
| `DataMemoryManager.get_address(var_name)` | Retorna endereco de variavel global registrada. |
| `DataMemoryManager.generate_data_directives(symbol_table)` | Emite diretivas `.space` e `.word` ordenadas por endereco. |
| `RegisterAllocator.__init__(func_context)` | Define registradores caller-saved (`r4`-`r11`), callee-saved (`r12`-`r26`), registrador de spill (`r30`) e estruturas LRU. |
| `RegisterAllocator.ensure_var_in_reg(var_name)` | Garante valor em registrador, carregando constantes, temporarios, locais, parametros ou globais conforme a origem. |
| `RegisterAllocator.get_address_in_reg(var_name)` | Calcula endereco de variavel local/parametro (`fp +/- offset`) ou global (`movi` do endereco). |
| `RegisterAllocator.get_reg_for_temp(temp_name)` | Aloca registrador para temporario e marca como sujo. |
| `RegisterAllocator.free_reg_if_temp(reg)` | Libera registrador quando ele contem temporario descartavel. |
| `RegisterAllocator.update_var_from_reg(dest_var, src_reg)` | Atualiza mapeamento apos atribuicao. |
| `RegisterAllocator.spill_all_dirty()` | Salva variaveis reais modificadas para pilha ou memoria global antes de pontos perigosos. |
| `RegisterAllocator.spill_all_for_call()` | Antes de chamada, salva variaveis reais e derrama temporarios, pois a chamada pode sobrescrever registradores. |
| `RegisterAllocator.invalidate_non_temps()` | Remove mapeamentos de variaveis reais ao cruzar rotulos. |
| `RegisterAllocator.invalidate_all()` | Limpa todos os mapeamentos apos desvios incondicionais. |
| `RegisterAllocator.invalidate_vars(var_names)` | Remove mapeamentos das variaveis indicadas. |
| `RegisterAllocator._get_free_reg()` | Retorna registrador livre ou escolhe um candidato LRU para spill. |
| `RegisterAllocator._spill_reg(reg, force)` | Salva registrador em memoria global ou pilha de temporarios e libera o registrador. |
| `RegisterAllocator._assign_reg_to_var(reg, var_name)` | Mantem mapas bidirecionais registrador-variavel. |
| `RegisterAllocator._unassign_reg(reg)` | Remove mapeamentos e devolve registrador para a fila livre. |
| `RegisterAllocator._mark_as_used(reg)` | Atualiza ordem LRU. |
| `FunctionContext.__init__(name, data_manager)` | Armazena instrucoes, layout de pilha, parametros, locais, ultimo comparador e alocador da funcao. |
| `FunctionContext.add_instruction(instruction)` | Anexa instrucao assembly e limpa estado de ultima instrucao quando recebe rotulo. |
| `FunctionContext.emit_frame_address(target_reg, offset)` | Emite `addi`, `subi` ou `mov` para calcular `fp + offset`. |
| `FunctionContext.new_label(prefix)` | Gera rotulo local de retorno/chamada. |
| `emit_pending_args(func_ctx)` | Move os tres primeiros argumentos para `r1`-`r3` e empilha excedentes em ordem reversa. |
| `cleanup_pending_args(func_ctx, pushed_count)` | Restaura `sp` apos argumentos empilhados e limpa fila de argumentos pendentes. |
| `emit_call(func_ctx, func_name, dest)` | Emite chamada nativa (`input`, `output`) ou chamada de usuario com rotulo de retorno, `lr`, `bl` e captura de `retval`. |
| `translate_instruction(instr_parts, func_ctx)` | Traduz uma linha de IR para assembly, cobrindo rotulos, `goto`, `param`, comparacoes, aritmetica, enderecos, loads/stores indiretos, chamadas, argumentos e retornos. |
| `generate_assembly(ir_list)` | Controla todo o back-end: identifica funcoes, coleta globais, isola IR por funcao, calcula parametros/locais/layout de pilha, traduz instrucoes, monta prologo/epilogo e adiciona `.data`. |

Convencao de registradores:

| Nome logico | Registrador | Papel |
| --- | --- | --- |
| `retval` | `r0` | Valor de retorno. |
| Argumentos rapidos | `r1`, `r2`, `r3` | Tres primeiros argumentos. |
| Temporarios/caller-saved | `r4`-`r11` | Calculos de curta duracao. |
| Callee-saved preferenciais | `r12`-`r26` | Valores de maior vida util. |
| `pseudo` | `r27` | Registrador auxiliar para literais/enderecos no montador. |
| `lr` | `r28` | Link logico do assembly. No RTL existe tambem link dedicado de hardware. |
| `sp` | `r29` | Ponteiro de pilha. |
| `spill` | `r30` | Scratch para spill e enderecos de frame. |
| `fp` | `r31` | Ponteiro de frame. |

Layout de frame:

| Regiao | Offset relativo a `fp` | Quem escreve | Uso |
| --- | --- | --- | --- |
| Parametros em `r1`-`r3` | negativos | callee no prologo | Permitir acesso uniforme por endereco de frame. |
| Variaveis locais | negativos | callee | Estado local da funcao. |
| Temporarios derramados | negativos, conforme necessario | alocador | Pressao de registradores. |
| Parametros excedentes | positivos | caller antes da chamada | 4o argumento em diante. |
| `fp` e `lr` salvos | topo do frame de funcoes nao-main | callee | Retorno seguro em recursao. |

## Montador e codificacao binaria

### `codegen/assembler.py`

| Funcao/classe | Logica implementada |
| --- | --- |
| `is_integer_literal(token)` | Reconhece literais inteiros. |
| `twos_complement(value, bits)` | Valida faixa e codifica valor com sinal em complemento de dois. |
| `register_bits(register_name)` | Valida `r0` a `r31` e retorna cinco bits. |
| `ParsedInstruction` | Dataclass com texto original, mnemonico, operacao base, condicao, suporte e operandos. |
| `FullCode.__init__(assembly_code_lines)` | Executa parsing, rotulacao, estabilizacao de layout, literal pool, codificacao e captura erros em `response`. |
| `FullCode._parse_source()` | Separa secoes `.text` e `.data`, rotulos, instrucoes e diretivas `.space`/`.word`. |
| `FullCode._parse_instruction(line)` | Converte linha assembly em `ParsedInstruction`; trata `ret:` como pseudo-retorno. |
| `FullCode._split_mnemonic(mnemonic)` | Separa operacao, sufixo de condicao e sufixo de suporte em ordem robusta. |
| `FullCode._parse_operands(base_op, operands_text, supp)` | Interpreta operandos de branch, `in`, `out`, `load`, `store`, `mov` e operacoes binarias. |
| `FullCode._build_data_labels()` | Atribui enderecos sequenciais aos rotulos de dados. |
| `FullCode._stabilize_text_layout()` | Recalcula tamanhos de instrucoes ate estabilizar expansoes de literais e branches longos. |
| `FullCode._rebuild_text_labels()` | Reconstrui tabela de rotulos de texto e tabela simbolica combinada. |
| `FullCode._resolve_symbol_or_int(token)` | Resolve literal, rotulo de texto ou rotulo de dados. |
| `FullCode._plan_instruction(instruction, current_address)` | Decide se a instrucao cabe em uma palavra ou exige literal/branch longo. |
| `FullCode._assign_literal_addresses()` | Aloca constantes fora de faixa em literal pool apos dados explicitos. |
| `FullCode._encode()` | Expande cada instrucao planejada, codifica, anexa dados/literais e monta listagens. |
| `FullCode._expand_instruction(instruction, plan, current_address)` | Expande `ret`, `movi` literal e branch longo via `r27`. |
| `FullCode._encode_concrete(concrete, current_address)` | Codifica campos `Cond`, `Type`, `Supp`, `Funct`, `Rd`, `Rh` e `Operand2`. |
| `FullCode.decode_machine_code()` | Decodifica palavras binarias para log humano com linha assembly correspondente. |

Formato de instrucao usado pelo montador e pelo processador:

| Campo | Bits | Conteudo |
| --- | --- | --- |
| `Cond` | `[31:28]` | Condicao: `do`, `eq`, `neq`, `gt`, `gteq`, `lt`, `lteq`. |
| `Type` | `[27:26]` | `00` processamento, `01` memoria, `11` branch. |
| `Supp` | `[25:24]` | `na`, `s`, `i`, `is`. |
| `Funct` | `[23:20]` | Operacao dentro do tipo. |
| `Rd` | `[19:15]` | Registrador destino. |
| `Rh` | `[14:10]` | Registrador fonte/base. |
| `Operand2` | `[9:0]` | Imediato de 10 bits com sinal ou `Ro[9:5]` com padding zero. |

Para programas gerados pelo compilador, `load` e `store` usam endereco em registrador: `load: rd = [ro]` e `store: [ro] = rh`. O RTL atual de `DataMemory.v` recebe o endereco pelos bits de `Ro`, por isso o pipeline evita depender de enderecamento imediato em instrucoes de memoria.

## Ferramentas de regressao e simulacao

### `codegen/assembler_regressions.py`

| Funcao | Logica implementada |
| --- | --- |
| `assert_success(machine_code, context)` | Falha o teste se `FullCode.response` indicar erro. |
| `run_conditional_parse_regression()` | Verifica parsing de condicao + imediato em `addeqi`. |
| `run_long_branch_regression()` | Cria alvo distante e confirma expansao de branch longo. |

### `tools/run_analysis_regressions.py`

| Funcao/classe | Logica implementada |
| --- | --- |
| `FrontendRun` | Dataclass com `returncode`, `stdout`, `stderr` e IR opcional. |
| `assert_true(condition, message)` | Helper de assercao. |
| `run_frontend(binary, fixture)` | Executa `bin/c-c` em diretorio temporario e captura IR gerada. |
| `test_valid_case(...)` | Exige AST, tabela de simbolos e IR em caso valido. |
| `test_lexical_case(...)` | Confirma erro lexico sem cascata sintatica/semantica. |
| `test_syntax_case(...)` | Confirma erro sintatico sem execucao semantica. |
| `test_semantic_case(...)` | Confirma erro por retorno ausente sem IR. |
| `test_undeclared_identifier_case(...)` | Confirma diagnostico de identificador nao declarado. |
| `test_missing_main_case(...)` | Confirma erro dedicado para ausencia de `main`. |
| `test_vpp_case(repo_root)` | Gera VPP temporario e valida nomes, blocos, acoes e fluxos SysML esperados. |
| `main()` | Resolve caminhos, executa a bateria de testes e retorna codigo de saida. |

### `tools/run_machine_code.py`

| Funcao/classe | Logica implementada |
| --- | --- |
| `mask32`, `to_signed32`, `sign_extend` | Normalizam valores para semantica de 32 bits e imediatos assinados. |
| `verilog_divide(lhs, rhs)` | Reproduz divisao inteira com sinal semelhante ao Verilog. |
| `parse_int(text)` | Interpreta inteiros em decimal, hexadecimal ou binario. |
| `prompt_for_input_value(cycle, pc)` | Solicita entrada interativa quando uma instrucao `in` bloqueia. |
| `DecodedInstruction` | Dataclass com campos decodificados de uma palavra de 32 bits. |
| `StepTrace` | Dataclass de rastreamento por ciclo. |
| `ProcessorState` | Estado de registradores, link, PC, flags, memoria, saidas e parada temporaria. |
| `ProcessorState.register_variables()` | Exporta registradores, flags, PC, link e saidas em dicionario. |
| `MachineRunResult` | Resultado de execucao, trace e resumo final. |
| `MachineRunResult.to_dict()` | Serializa resultado para JSON. |
| `decode_instruction(word)` | Extrai condicao, tipo, suporte, funcao, registradores, imediato e sinais de branch/link. |
| `evaluate_condition(cond, flags)` | Aplica a logica de condicao sobre flags Z/N. |
| `compute_alu_result(...)` | Simula ALU para processamento, memoria e branch. |
| `load_machine_words(...)` | Le palavras binarias de arquivo ou argumentos inline. |
| `build_instruction_memory(machine_words)` | Monta ROM de 1024 palavras. |
| `format_decoded_instruction(word)` | Gera texto humano para uma instrucao decodificada. |
| `parse_assembly_listing_line(line)` | Le linhas `binario -> assembly` de diagnostico. |
| `load_assembly_listing(...)` | Valida se a listagem corresponde exatamente ao binario executado. |
| `select_analysis_output_path(...)` | Decide quando gravar `result_analysis.txt`. |
| `build_analysis_report(...)` | Renderiza relatorio textual de execucao e estado final. |
| `run_machine_code(...)` | Executa ciclo a ciclo o modelo de `Processor(v2026-1)`, incluindo `in`, `out`, flags, memoria, branch, link e parada temporaria. |
| `build_arg_parser()` | Define CLI do simulador. |
| `main()` | Processa argumentos, executa o modelo, imprime JSON/relatorio e grava saida quando aplicavel. |

## Gerador de diagramas SysML

### `tools/generate_vpp_analysis_diagram.py`

O arquivo e grande porque manipula diretamente a base SQLite interna de arquivos Visual Paradigm. As funcoes estao agrupadas abaixo por responsabilidade:

| Grupo | Funcoes/classes |
| --- | --- |
| Especificacoes de modelo | `ActivityNodeSpec`, `EdgeSpec`, `BlockSpec`, `AssociationSpec` |
| Tempo, texto e ids | `now_ms`, `now_s`, `quote`, `name_literal`, `encode_text`, `blob_to_text`, `generate_id` |
| Consultas e extracao | `find_one`, `extract_child_ids`, `extract_simple_ids`, `extract_preview_id`, `fetch_existing_ids` |
| Renderizacao de definicoes | `render_ref_list`, `render_path_refs`, `render_simple_refs`, `render_root_model_definition`, `render_root_diagrams_definition`, `render_relationship_container_definition`, `render_parent_activity_definition`, `render_activity_model_definition`, `render_activity_node_shape_definition`, `render_controlflow_model_definition`, `render_controlflow_shape_definition`, `render_activity_diagram_definition` |
| Diagramas de blocos | `model_address`, `render_sysml_block_definition`, `render_block_shape_definition`, `render_association_model_definition`, `render_association_shape_definition`, `render_block_diagram_definition` |
| Geometria e imagem | `compute_edge_geometry`, `make_png`, `select_template_details` |
| Persistencia VPP | `upsert_project_file`, `collect_descendant_ids`, `ids_for_relationships_in_diagram`, `find_or_create_model`, `find_or_create_diagram`, `update_project_diagram_refs`, `cleanup_legacy_content`, `cleanup_orphan_project_files` |
| Conteudo dos diagramas | `lane_x`, `build_activity_specs`, `build_block_specs`, `build_module_hierarchy_specs`, `build_traceability_specs` |
| Geracao dos diagramas | `generate_activity_diagram`, `generate_block_diagram`, `append_model_view`, `append_child_refs`, `generate_encoder_diagram`, `generate_module_hierarchy_diagram`, `generate_traceability_diagram`, `main` |

## Processador alvo `Processor(v2026-1)`

O projeto Quartus usa familia `Cyclone IV E`, dispositivo `EP4CE115F29C7` e entidade top-level `Processor`. A ROM de instrucao tem 1024 palavras de 32 bits e e inicializada por `modules/single_port_rom_init.txt`. A RAM de dados tem 64 palavras de 32 bits.

| Modulo Verilog | Funcao |
| --- | --- |
| `Processor` | Top-level: conecta `CLOCK_50`, chaves, LEDs, displays, clocks divididos, sinais perifericos e modulo `integrated`. |
| `integrated` | Datapath principal: conecta controle, PC, ROM, banco de registradores, ALU, RAM, CPSR e saida. |
| `ControlUnit` | Decodifica campos da instrucao, sinais de load/store, branch, link, imediato, condicao e parada temporaria por `in`. |
| `PC_main` | Atualiza PC na borda de descida: incrementa, desvia por imediato relativo, desvia por registrador absoluto ou carrega link dedicado. |
| `InstructionMemory` | ROM de 1024 palavras lida no `fast_clock`. |
| `registerBank` | Banco de 32 registradores gerais e registrador de link dedicado. Escrita ocorre em `posedge clock`; leitura em `posedge fast_clock`. |
| `ALUControl` | Escolhe `Operand2` entre imediato estendido e `RoValue`, depois chama `alu`. |
| `alu` | Executa operacoes aritmeticas/logicas, `in`, `out`, passagem de dados de memoria e valor de branch. |
| `DataMemory` | RAM de 64 palavras; escreve no `clock` e le no `fast_clock`. |
| `CPSR_module`, `CPSRegister`, `FlagDecoder`, `FlagVerifier` | Avaliam condicoes, atualizam flags Z/N e liberam ou bloqueiam escrita/execucao. |
| `mux_write_in_reg` | Seleciona entre resultado da ALU e saida da RAM para escrita no banco de registradores. |
| `output_manager`, `output_module`, `to_display` | Registram saida e convertem valores para displays de sete segmentos. |
| `freqDiv` | Gera `clock` lento e `fast_clock` a partir de `CLOCK_50`. |

Matriz de branch atual:

| Classe | Bits relevantes | Efeito |
| --- | --- | --- |
| Branch imediato | `Type=11`, `i=1`, `Funct[22]=0` | `PC := PC + immediate` |
| Branch por registrador | `Type=11`, `i=0`, `Funct[22]=0` | `PC := RoValue` |
| Branch-and-link imediato | `Type=11`, `i=1`, `Funct[23]=1`, `Funct[22]=0` | `Link := PC+1`; `PC := PC + immediate` |
| Branch-and-link por registrador | `Type=11`, `i=0`, `Funct[23]=1`, `Funct[22]=0` | `Link := PC+1`; `PC := RoValue` |
| Retorno por link dedicado | `Type=11`, `Funct[22]=1` | `PC := LinkValue` |

Sinais de uso em bancada:

| Sinal | Uso |
| --- | --- |
| `SW[16]` | Reset do processador e do detector de entrada. |
| `SW[15]` | Sinal periferico para `in`; durante parada, a liberacao ocorre na transicao `1 -> 0`. |
| `SW[17]` | Pausa o clock efetivo quando em nivel alto. |
| `SW[7:0]` | Valor de entrada usado por `in`. |
| `LEDR[0]` | Indica `write_condition`. |
| `output_value` / `HEX6-HEX7` | Ultimo valor emitido por `out`. |
| `pc` / `HEX0-HEX3` | Endereco de instrucao atual. |
