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
    extern AstNode *syntax_tree;

    int errorCount = 0;

    void yyerror(const char *msg);

//   yydebug = 1;
//   %debug
%}

%union {
    char *sval;
    int   ival;
    struct AstNode *ast;
}

%token <sval> ID
%token <ival> NUM

%type <ast> program declaration_list declaration
%type <ast> var_declaration fun_declaration 
%type <ast> params param_list param
%type <ast> statement selection_stmt iteration_stmt return_stmt
%type <ast> expression_stmt expression simple_expression var call args arg_list
%type <ast> compound_stmt additive_expression
%type <ival> type_specifier
%type <ast> relop addop mulop
%type <ast> local_declarations statement_list
%type <ast> factor term

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

program:
    declaration_list {
        syntax_tree = newNode(AST_PROGRAM);
        for (AstNode *n = $1; n; ) {
            AstNode *next = n->nextSibling; // save next node
            n->nextSibling = NULL; // detach current node from the list
            addChild(syntax_tree, n); // add current node to the syntax tree
            n = next; // move to the next node
        }
    }
    ;

declaration_list
    : declaration_list declaration
    {
        AstNode *n = $1;
        while (n->nextSibling) n = n->nextSibling; // traverse to the end of the list
        n->nextSibling = $2; // append the new declaration
        $$ = $1;
        printf("[PARSER DBG] declaration_list: added %s\n", $2->name);
    }
    | declaration { $$ = $1; }
    ;

declaration
    : var_declaration { $$ = $1; }
    | fun_declaration { $$ = $1; }
    ;


var_declaration:
    type_specifier ID SEMICOLON
    {
        declareSymbol(
            &symtab, 
            $2, 
            currentScope, 
            SYMBOL_VAR, 
            yylineno, 
            $1
        );
        AstNode *n = newNode(AST_VAR_DECL);
        n->name = strdup($2);
        $$ = n;
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
        if ($5) addChild(n, $5); // parameters
        if ($7) addChild(n, $7); // compound statement
        $$ = n;
        popScope();
        free($2);
        printf(
            "[PARSER DBG] fun_declaration: name=%s, params=%p, body=%p\n",
            $2, 
            (void*)$5, 
            (void*)$7
            );
    };

params
    : param_list { $$ = $1; }
    | VOID { $$ = NULL; }
    ;

param_list
    : param_list COMMA param {
        addChild($1, $3); // add parameter to the list
        $$ = $1; // return the updated list
    }
    | param {
        AstNode *n = newNode(AST_PARAM_LIST);
        addChild(n, $1); // single parameter
        $$ = n; // return the parameter list
    }
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

compound_stmt: 
    LBRACE local_declarations statement_list RBRACE {
        AstNode *n = newNode(AST_BLOCK);
        if ($2) addChild(n, $2); // local declarations
        if($3) {
            AstNode *stmts = $3;
            while(stmts) {
                AstNode *next = stmts->nextSibling; // save next node
                stmts->nextSibling = NULL; // detach current statement
                addChild(n, stmts); // add current statement to the block
                stmts = next; // move to the next statement
            }
        }
        $$ = n;
        printf(
            "[PARSER DBG] compound_stmt: decls=%p stmts=%p\n",
            (void*)$2,
            (void*)$3
            );
    }
    ;

local_declarations: 
    local_declarations var_declaration {
        AstNode *cur = $1;
        while (cur->nextSibling) cur = cur->nextSibling;
        cur->nextSibling = $2;
        $$ = $1;
        }
    | var_declaration {
        $$ = $1;   /* a single VAR_DECL */
        }
    | /* empty */ { $$ = NULL; }
    ;

statement_list:
    statement_list statement {
        AstNode *n = $1;
        while (n->nextSibling) n = n->nextSibling; // traverse to the end of the list
        n->nextSibling = $2; // append the new statement
        $$ = $1; // return the updated list
    }
    | statement { $$ = $1; } // single statement
    ;

statement
    : expression_stmt { $$ = $1; }
    | compound_stmt { $$ = $1; }
    | selection_stmt { $$ = $1; }
    | iteration_stmt { $$ = $1; }
    | return_stmt { $$ = $1; }
    ;

expression_stmt
    : expression SEMICOLON { $$ = $1; }
    | SEMICOLON { $$ = NULL; }
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
    : WHILE LPAREN expression RPAREN statement {
        AstNode *n = newNode(AST_WHILE);
        addChild(n, $3); // condition
        addChild(n, $5); // body statement
        $$ = n;
    }
    ;

return_stmt
    : RETURN SEMICOLON { 
        AstNode *n = newNode(AST_RETURN);
        $$ = n; // return without expression
    }
    | RETURN expression SEMICOLON {
        AstNode *n = newNode(AST_RETURN);
        if ($2) 
            addChild(n, $2); // return expression
        $$ = n;
    }
    ;

expression
    : var ASSIGN expression {
        AstNode *n = newNode(AST_ASSIGN);
        addChild(n, $1); // variable
        addChild(n, $3); // expression
        $$ = n;
        printf(
            "[PARSER DBG] assignment: var=%p expr=%p\n",
            (void*)$1,
            (void*)$3
            );
    }
    | simple_expression { $$ = $1; }
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
        printf(
            "[PARSER DBG] binop: left=%p op=%p right=%p\n",
            (void*)$1, 
            (void*)$2, 
            (void*)$3
            );
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
    : additive_expression addop term {
        AstNode *n = newNode(AST_BINOP);
        addChild(n, $1); // left operand
        addChild(n, $2); // operator
        addChild(n, $3); // right operand
        $$ = n;
    }
    | term { $$ = $1; }
    ;

addop
    : PLUS { $$ = newOpNode("+"); }
    | MINUS { $$ = newOpNode("-"); }
    ;

term
    : term mulop factor {
        AstNode *n = newNode(AST_BINOP);
        addChild(n, $1); // left operand
        addChild(n, $2); // operator
        addChild(n, $3); // right operand
        $$ = n;
    }
    | factor { $$ = $1; }
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
    | var { $$ = $1; } // variable
    | call { $$ = $1; } // function call
    | NUM { $$ = newNumNode($1); } // create a new AST node for the number
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
    : arg_list { $$ = $1; }
    | /* empty */ { $$ = NULL;}
    ;

arg_list
    : arg_list COMMA expression {
        addChild($1, $3); // add expression to argument list
        $$ = $1; // return the updated list
    }
    | expression {
        AstNode *n = newNode(AST_ARG_LIST);
        addChild(n, $1); // single argument
        $$ = n; // return the argument list
    }
    ;

%%

void yyerror(const char *msg) {
    fprintf(stderr, "Line %d: %s\n", yylineno, msg);
    errorCount++;
}