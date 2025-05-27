%{
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include "symbol_table.h"
    #include "utils.h"
    #include "syntax_tree.h"

    #define TYPE_INT 1
    #define TYPE_VOID 2

    extern int yylineno;
    extern char *yytext;
    
    extern char *currentScope;
    extern SymbolTable symtab;
    extern AstNode *syntax_tree = NULL;

    int errorCount = 0;

    void yyerror(const char *msg);

//   yydebug = 1;
//   %debug
%}

%union {
    char *sval;
    int   ival;
    AstNode *ast;
}

%token <sval> ID
%token <ival> NUM

%type <ast> program declaration_list declaration
%type <ast> var_declaration fun_declaration params param_list param
%type <ast> statement selection_stmt iteration_stmt return_stmt
%type <ast> expression_stmt expression simple_expression var call args arg_list
%type <ast> compound_stmt additive_expression factor
%type <ival> type_specifier relop addop mulop

%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

/* Tokens */
%token IF 1 
%token WHILE 2 
%token RETURN 3
%token INT 4 
%token VOID 5 
%token EQ 8
%token NEQ 9 
%token LT 10
%token LTE 11
%token GT 12
%token GTE 13
%token PLUS 14 
%token MINUS 15 
%token TIMES 16
%token DIV 17
%token ASSIGN 18 
%token SEMICOLON 19
%token COMMA 20
%token LPAREN 21
%token RPAREN 22
%token LBRACE 23
%token RBRACE 24
%token LBRACK 25
%token RBRACK 26
%token MOD 28


%%

program
    : declaration_list {
        syntax_tree = newNode(AST_PROGRAM);
        addChild(syntax_tree, $1);
    }
    ;

declaration_list
    : declaration_list declaration
    {
        addChild($1, $2);
        $$ = $1;
    }
    | declaration {
        $$ = $1;
    }
    ;

declaration
    : var_declaration
    | fun_declaration
    ;


var_declaration:
    type_specifier ID SEMICOLON
    {
        AstNode *n = newNode(AST_VAR_DECL);
        n->name = strdup($2);
        $$ = n;
        declareSymbol(
            &symtab, 
            $2, 
            currentScope, 
            SYMBOL_VAR, 
            yylineno, 
            $1
        );
        free($2);
    }
;

type_specifier:
    INT  { $$ = TYPE_INT;  }
    | VOID { $$ = TYPE_VOID; }
    ;

fun_declaration:
    type_specifier ID LPAREN  {
        declareSymbol(
            &symtab,
            $2,              // function name
            currentScope,
            SYMBOL_FUNC,
            yylineno,
            $1               // return type
        );
        pushScope($2); // enter function scope
    } params RPAREN compound_stmt {
        AstNode *n = newNode(AST_FUN_DECL);
        n->name = strdup($2); // function name
        addChild(n, $4); // parameters
        addChild(n, $6); // compound statement
        $$ = n;
        popScope();
        free($2);
    };

params
    : param_list
    | VOID
    ;

param_list
    : param_list COMMA param
    | param
    ;

param:
    type_specifier ID {
        declareSymbol(
            &symtab,
            $2,
            currentScope,
            SYMBOL_VAR,
            yylineno,
            $1
        );
        $$ = newNode(AST_PARAM);
        $$->name = strdup($2); // parameter name
        free($2);
    }
    | type_specifier ID LBRACK RBRACK {
        declareSymbol(
            &symtab,
            $2,
            currentScope,
            SYMBOL_VAR,
            yylineno,
            $1
        );
        $$ = newNode(AST_PARAM_ARRAY);
        $$->name = strdup($2); // parameter name
        free($2);
    }
;

compound_stmt
    : LBRACE local_declarations statement_list RBRACE {
        AstNode *n = newNode(AST_BLOCK);
        addChild(n, $2); // local declarations
        addChild(n, $3); // statement list
        $$ = n;
    }
    ;

local_declarations
    : local_declarations var_declaration
    | /* empty */
    ;

statement_list
    : statement_list statement
    | /* empty */
    ;

statement
    : expression_stmt
    | compound_stmt
    | selection_stmt
    | iteration_stmt
    | return_stmt
    ;

expression_stmt
    : expression SEMICOLON
    | SEMICOLON
    ;

selection_stmt
    : IF LPAREN expression RPAREN statement %prec LOWER_THAN_ELSE {
        AstNode *n = newNode(AST_IF);
        addChild(n, $3); // condition
        addChild(n, $5); // then statement
        $$ = n;
    }
    | IF LPAREN expression RPAREN statement ELSE statement {
        AstNode *n = newNode(AST_IF);
        addChild(n, $3); // condition
        addChild(n, $5); // then statement
        addChild(n, $7); // else statement
        $$ = n;
    }
    ;

iteration_stmt
    : WHILE LPAREN expression RPAREN statement
    ;

return_stmt
    : RETURN SEMICOLON
    | RETURN expression SEMICOLON
    ;

expression
    : var ASSIGN expression {
        AstNode *n = newNode(AST_ASSIGN);
        addChild(n, $1); // variable
        addChild(n, $3); // expression
        $$ = n;
    }
    | simple_expression
    ;

var
    : ID {
        useSymbol(
            &symtab, 
            $1, 
            currentScope, 
            yylineno
        );
        $$ = newIdNode($1);
        free($1);
    }
    | ID LBRACK expression RBRACK {
        useSymbol(
            &symtab, 
            $1, 
            currentScope, 
            yylineno
        );
        $$ = newIdNode($1);
        free($1);
    }
    ;

simple_expression:
    additive_expression relop additive_expression {
        AstNode *n = newNode(AST_BINOP);
        addChild(n, $1); // left operand
        addChild(n, $2); // operator
        addChild(n, $3); // right operand
        $$ = n;
    }
    | additive_expression {
        $$ = $1;
    }
    ;

relop
    : LTE { $$ = newOpNode("<="); }
    | LT { $$ = newOpNode("<"); }
    | GT { $$ = newOpNode(">"); }
    | GTE { $$ = newOpNode(">="); }
    | EQ { $$ = newOpNode("=="); }
    | NEQ { $$ = newOpNode("!="); }
    ;

additive_expression
    : additive_expression addop term
    | term
    ;

addop
    : PLUS { $$ = newOpNode("+"); }
    | MINUS { $$ = newOpNode("-"); }
    ;

term
    : term mulop factor
    | factor
    ;

mulop
    : TIMES { $$ = newOpNode("*"); }
    | DIV { $$ = newOpNode("/"); }
    | MOD { $$ = newOpNode("%"); }
    ;

factor
    : LPAREN expression RPAREN {
        $$ = $2; // return the expression inside parentheses
    }
    | var
    | call
    | NUM {
        $$ = newNumNode($1); // create a new AST node for the number
    }
    ;

call:
    ID LPAREN args RPAREN {
        useSymbol(
            &symtab, 
            $1, 
            currentScope, 
            yylineno
        );
        AstNode *n = newNode(AST_CALL);
        n->name = strdup($1); // function name
        addChild(n, $3); // arguments
        $$ = n;
        free($1);
    }
;

args
    : arg_list
    | /* empty */
    ;

arg_list
    : arg_list COMMA expression
    | expression
    ;

%%

void yyerror(const char *msg) {
    fprintf(stderr, "Line %d: %s\n", yylineno, msg);
    errorCount++;
}