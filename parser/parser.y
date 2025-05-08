%{
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include "syntax_tree.h"
  #include "node.h"
  #include "utils.h"
  #include "symbol_table.h"
  #include "semantic.h"
  
  treeNode *syntax_tree;
  SymbolTable tabela;

  extern int tokenNUM;
  extern int parseResult;

  extern char *functionName;
  extern char *currentScope;
  extern char *expName;
  extern int functionCurrentLine;
  extern char *variableName;

  extern char *argName;

  extern int yylineno;
  extern char *yytext;

  void insertSymbolInTable(char *name, char *scope, SymbolType type, int line, primitiveType dataType) {
    Symbol *symbol = findSymbol(&tabela, name, scope);
    if (symbol) {
        addLine(symbol, line);
    } else {
        insertSymbol(&tabela, name, scope, type, line, dataType);
    }
  }
%}

/* Tokens */
%token IF WHILE RETURN INT VOID NUM ID
%token EQ NEQ LT LTE GT GTE
%token PLUS MINUS TIMES DIV ASSIGN
%token SEMICOLON COMMA LPAREN RPAREN LBRACE RBRACE LBRACK RBRACK
%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%%

programa:
    declaracao_lista       { syntax_tree = $1; }
  ;

declaracao_lista:
    declaracao_lista declaracao { $$ = traversal($1, $2); }
  | declaracao                 { $$ = $1;        }
  ;

declaracao:
    var_declaracao             { $$ = $1; }
  | fun_declaracao             { $$ = $1; }
  ;

/* ===== definição de tipo_especificador ===== */
tipo_especificador:
    INT  { $$ = createDeclNode(declIdType); $$->type = Integer; }
  | VOID { $$ = createDeclNode(declIdType); $$->type = Void;    }
  ;

var_declaracao:
    tipo_especificador ID SEMICOLON {
        $$ = createDeclVarNode(declVar, $1);
        $$->key.name = strdup(yytext);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type);
    }
  | tipo_especificador ID LBRACK NUM RBRACK SEMICOLON {
        $$ = createArrayDeclVarNode(expNum, declVar, $1);
        $$->key.name = strdup(yytext);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, $1->type);
    }
  ;

fun_declaracao:
    tipo_especificador ID LPAREN params RPAREN composto_decl {
        $$ = createDeclFuncNode(declFunc, $1, $4, $6);
        paramsCount = 0;
        currentScope = strdup(yytext);
        insertSymbolInTable(functionName, "global", FUNC, functionCurrentLine - 1, $1->type);
    }
  ;

params:
    param_lista           { $$ = $1; }
  | VOID                  { $$ = createEmptyParams(expId); }
  ;

param_lista:
    param_lista COMMA param { $$ = traversal($1, $3); }
  | param                   { $$ = $1;            }
  ;

param:
    tipo_especificador ID {
        $$ = createDeclVarNode(declVar, $1);
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type);
    }
  | tipo_especificador ID LBRACK RBRACK {
        $$ = createArrayArg(declVar, $1);
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, $1->type);
    }
  ;

composto_decl:
    LBRACE local_declaracoes statement_lista RBRACE               { $$ = traversal($2, $3); }
  | SEMICOLON                                                  { $$ = NULL;        }
  | LBRACE local_declaracoes statement_lista fun_declaracao RBRACE { $$ = traversal(traversal($2,$3), $4); }
  | LBRACE local_declaracoes fun_declaracao statement_lista RBRACE { $$ = traversal(traversal($2,$3), $4); }
  ;

local_declaracoes:
    local_declaracoes var_declaracao { $$ = traversal($1, $2); }
  | /* empty */                     { $$ = NULL;        }
  ;

statement_lista:
    statement_lista statement { $$ = traversal($1, $2); }
  | /* empty */              { $$ = NULL;        }
  ;

statement:
    expressao_decl   { $$ = $1; }
  | composto_decl    { $$ = $1; }
  | selecao_decl     { $$ = $1; }
  | iteracao_decl    { $$ = $1; }
  | retorno_decl     { $$ = $1; }
  ;

expressao_decl:
    expressao SEMICOLON { $$ = $1; }
  ;

/* if/else com precedência de dangling else */
selecao_decl:
    IF LPAREN expressao RPAREN statement %prec LOWER_THAN_ELSE { $$ = createIfStmt(stmtIf, $3, $5, NULL); }
  | IF LPAREN expressao RPAREN statement ELSE statement        { $$ = createIfStmt(stmtIf, $3, $5, $7); }
  ;

iteracao_decl:
    WHILE LPAREN expressao RPAREN statement { $$ = createWhileStmt(stmtWhile, $3, $5); }
  ;

retorno_decl:
    RETURN SEMICOLON              { $$ = createStmtNode(stmtReturn); }
  | RETURN expressao SEMICOLON   { $$ = createStmtNode(stmtReturn); $$->child[0] = $2; }
  ;

expressao:
    expressao ASSIGN expressao { $$ = createAssignStmt(stmtAttrib, $1, $3); $$->key.op = ASSIGN; }
  | simples_expressao          { $$ = $1; }
  ;

simples_expressao:
    soma_expressao relacional soma_expressao { $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op; }
  | soma_expressao                          { $$ = $1; }
  ;

relacional:
    LT  { $$ = createExpNode(expOp); $$->key.op = LT;  $$->line = yylineno; }
  | LTE { $$ = createExpNode(expOp); $$->key.op = LTE; $$->line = yylineno; }
  | GT  { $$ = createExpNode(expOp); $$->key.op = GT;  $$->line = yylineno; }
  | GTE { $$ = createExpNode(expOp); $$->key.op = GTE; $$->line = yylineno; }
  | EQ  { $$ = createExpNode(expOp); $$->key.op = EQ;  $$->line = yylineno; }
  | NEQ { $$ = createExpNode(expOp); $$->key.op = NEQ; $$->line = yylineno; }
  ;

soma_expressao:
    soma_expressao soma termo { $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op; }
  | termo                    { $$ = $1;                       }
  ;

soma:
    PLUS  { $$ = createExpNode(expOp); $$->key.op = PLUS;  }
  | MINUS { $$ = createExpNode(expOp); $$->key.op = MINUS; }
  ;

termo:
    termo mult fator { $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op; }
  | fator           { $$ = $1;                         }
  ;

mult:
    TIMES { $$ = createExpNode(expOp); $$->key.op = TIMES; }
  | DIV   { $$ = createExpNode(expOp); $$->key.op = DIV;   }
  ;

/* ===== refatorado: todo acesso e chamada ficam em fator ===== */
fator:
    LPAREN expressao RPAREN {
        $$ = $2;
    }
  | ID LPAREN args RPAREN {
        expName = strdup(yytext);
        $$ = createExpCallNode(expName, $3);
        $$->line = yylineno;
    }
  | ID {
        expName = strdup(yytext);
        $$ = createExpVar(expId);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, Integer);
    }
  | NUM {
        $$ = createExpNum(expNum);
    }
  ;

args:
    arg_lista { $$ = $1; }
  | /* empty */ { $$ = NULL; }
  ;

arg_lista:
    arg_lista COMMA expressao { $$ = traversal($1, $3); argsCount++; }
  | expressao                { $$ = $1; argsCount++; }
  | param                    { $$ = $1; argsCount++; }
  ;

%%

int yyerror(char *errorMsg) {
  printf("(!) ERRO SINTATICO: Linha: %d | Token: %s\n", yylineno, yytext);
  return 1;
}

treeNode *parse() {
    parseResult = yyparse();
    return syntax_tree;
}
