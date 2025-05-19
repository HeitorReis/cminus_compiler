/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison implementation for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* C LALR(1) parser skeleton written by Richard Stallman, by
   simplifying the original so-called "semantic" parser.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

/* All symbols defined below should begin with yy or YY, to avoid
   infringing on user name space.  This should be done even for local
   variables, as they might otherwise be expanded by user macros.
   There are some unavoidable exceptions within include files to
   define necessary library symbols; they are noted "INFRINGES ON
   USER NAME SPACE" below.  */

/* Identify Bison output, and Bison version.  */
#define YYBISON 30802

/* Bison version string.  */
#define YYBISON_VERSION "3.8.2"

/* Skeleton name.  */
#define YYSKELETON_NAME "yacc.c"

/* Pure parsers.  */
#define YYPURE 0

/* Push parsers.  */
#define YYPUSH 0

/* Pull parsers.  */
#define YYPULL 1




/* First part of user prologue.  */
#line 1 "parser/parser.y"

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

#line 108 "parser.tab.c"

# ifndef YY_CAST
#  ifdef __cplusplus
#   define YY_CAST(Type, Val) static_cast<Type> (Val)
#   define YY_REINTERPRET_CAST(Type, Val) reinterpret_cast<Type> (Val)
#  else
#   define YY_CAST(Type, Val) ((Type) (Val))
#   define YY_REINTERPRET_CAST(Type, Val) ((Type) (Val))
#  endif
# endif
# ifndef YY_NULLPTR
#  if defined __cplusplus
#   if 201103L <= __cplusplus
#    define YY_NULLPTR nullptr
#   else
#    define YY_NULLPTR 0
#   endif
#  else
#   define YY_NULLPTR ((void*)0)
#  endif
# endif

#include "parser.tab.h"
/* Symbol kind.  */
enum yysymbol_kind_t
{
  YYSYMBOL_YYEMPTY = -2,
  YYSYMBOL_YYEOF = 0,                      /* "end of file"  */
  YYSYMBOL_YYerror = 1,                    /* error  */
  YYSYMBOL_YYUNDEF = 2,                    /* "invalid token"  */
  YYSYMBOL_IF = 3,                         /* IF  */
  YYSYMBOL_WHILE = 4,                      /* WHILE  */
  YYSYMBOL_RETURN = 5,                     /* RETURN  */
  YYSYMBOL_INT = 6,                        /* INT  */
  YYSYMBOL_VOID = 7,                       /* VOID  */
  YYSYMBOL_NUM = 8,                        /* NUM  */
  YYSYMBOL_ID = 9,                         /* ID  */
  YYSYMBOL_EQ = 10,                        /* EQ  */
  YYSYMBOL_NEQ = 11,                       /* NEQ  */
  YYSYMBOL_LT = 12,                        /* LT  */
  YYSYMBOL_LTE = 13,                       /* LTE  */
  YYSYMBOL_GT = 14,                        /* GT  */
  YYSYMBOL_GTE = 15,                       /* GTE  */
  YYSYMBOL_PLUS = 16,                      /* PLUS  */
  YYSYMBOL_MINUS = 17,                     /* MINUS  */
  YYSYMBOL_TIMES = 18,                     /* TIMES  */
  YYSYMBOL_DIV = 19,                       /* DIV  */
  YYSYMBOL_ASSIGN = 20,                    /* ASSIGN  */
  YYSYMBOL_SEMICOLON = 21,                 /* SEMICOLON  */
  YYSYMBOL_COMMA = 22,                     /* COMMA  */
  YYSYMBOL_LPAREN = 23,                    /* LPAREN  */
  YYSYMBOL_RPAREN = 24,                    /* RPAREN  */
  YYSYMBOL_LBRACE = 25,                    /* LBRACE  */
  YYSYMBOL_RBRACE = 26,                    /* RBRACE  */
  YYSYMBOL_LBRACK = 27,                    /* LBRACK  */
  YYSYMBOL_RBRACK = 28,                    /* RBRACK  */
  YYSYMBOL_ELSE = 29,                      /* ELSE  */
  YYSYMBOL_YYACCEPT = 30,                  /* $accept  */
  YYSYMBOL_program = 31,                   /* program  */
  YYSYMBOL_declaration_list = 32,          /* declaration_list  */
  YYSYMBOL_declaration = 33,               /* declaration  */
  YYSYMBOL_var_declaration = 34,           /* var_declaration  */
  YYSYMBOL_type_specifier = 35,            /* type_specifier  */
  YYSYMBOL_fun_declaration = 36,           /* fun_declaration  */
  YYSYMBOL_params = 37,                    /* params  */
  YYSYMBOL_param_list = 38,                /* param_list  */
  YYSYMBOL_param = 39,                     /* param  */
  YYSYMBOL_compound_decl = 40,             /* compound_decl  */
  YYSYMBOL_local_declarations = 41,        /* local_declarations  */
  YYSYMBOL_statement_list = 42,            /* statement_list  */
  YYSYMBOL_statement = 43,                 /* statement  */
  YYSYMBOL_matched_stmt = 44,              /* matched_stmt  */
  YYSYMBOL_unmatched_stmt = 45,            /* unmatched_stmt  */
  YYSYMBOL_other_stmt = 46,                /* other_stmt  */
  YYSYMBOL_expression_decl = 47,           /* expression_decl  */
  YYSYMBOL_iteration_decl = 48,            /* iteration_decl  */
  YYSYMBOL_return_decl = 49,               /* return_decl  */
  YYSYMBOL_expression = 50,                /* expression  */
  YYSYMBOL_var = 51,                       /* var  */
  YYSYMBOL_simple_expression = 52,         /* simple_expression  */
  YYSYMBOL_relational = 53,                /* relational  */
  YYSYMBOL_sum_expression = 54,            /* sum_expression  */
  YYSYMBOL_sum = 55,                       /* sum  */
  YYSYMBOL_term = 56,                      /* term  */
  YYSYMBOL_mult = 57,                      /* mult  */
  YYSYMBOL_factor = 58,                    /* factor  */
  YYSYMBOL_call = 59,                      /* call  */
  YYSYMBOL_args = 60,                      /* args  */
  YYSYMBOL_arg_list = 61                   /* arg_list  */
};
typedef enum yysymbol_kind_t yysymbol_kind_t;




#ifdef short
# undef short
#endif

/* On compilers that do not define __PTRDIFF_MAX__ etc., make sure
   <limits.h> and (if available) <stdint.h> are included
   so that the code can choose integer types of a good width.  */

#ifndef __PTRDIFF_MAX__
# include <limits.h> /* INFRINGES ON USER NAME SPACE */
# if defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stdint.h> /* INFRINGES ON USER NAME SPACE */
#  define YY_STDINT_H
# endif
#endif

/* Narrow types that promote to a signed type and that can represent a
   signed or unsigned integer of at least N bits.  In tables they can
   save space and decrease cache pressure.  Promoting to a signed type
   helps avoid bugs in integer arithmetic.  */

#ifdef __INT_LEAST8_MAX__
typedef __INT_LEAST8_TYPE__ yytype_int8;
#elif defined YY_STDINT_H
typedef int_least8_t yytype_int8;
#else
typedef signed char yytype_int8;
#endif

#ifdef __INT_LEAST16_MAX__
typedef __INT_LEAST16_TYPE__ yytype_int16;
#elif defined YY_STDINT_H
typedef int_least16_t yytype_int16;
#else
typedef short yytype_int16;
#endif

/* Work around bug in HP-UX 11.23, which defines these macros
   incorrectly for preprocessor constants.  This workaround can likely
   be removed in 2023, as HPE has promised support for HP-UX 11.23
   (aka HP-UX 11i v2) only through the end of 2022; see Table 2 of
   <https://h20195.www2.hpe.com/V2/getpdf.aspx/4AA4-7673ENW.pdf>.  */
#ifdef __hpux
# undef UINT_LEAST8_MAX
# undef UINT_LEAST16_MAX
# define UINT_LEAST8_MAX 255
# define UINT_LEAST16_MAX 65535
#endif

#if defined __UINT_LEAST8_MAX__ && __UINT_LEAST8_MAX__ <= __INT_MAX__
typedef __UINT_LEAST8_TYPE__ yytype_uint8;
#elif (!defined __UINT_LEAST8_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST8_MAX <= INT_MAX)
typedef uint_least8_t yytype_uint8;
#elif !defined __UINT_LEAST8_MAX__ && UCHAR_MAX <= INT_MAX
typedef unsigned char yytype_uint8;
#else
typedef short yytype_uint8;
#endif

#if defined __UINT_LEAST16_MAX__ && __UINT_LEAST16_MAX__ <= __INT_MAX__
typedef __UINT_LEAST16_TYPE__ yytype_uint16;
#elif (!defined __UINT_LEAST16_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST16_MAX <= INT_MAX)
typedef uint_least16_t yytype_uint16;
#elif !defined __UINT_LEAST16_MAX__ && USHRT_MAX <= INT_MAX
typedef unsigned short yytype_uint16;
#else
typedef int yytype_uint16;
#endif

#ifndef YYPTRDIFF_T
# if defined __PTRDIFF_TYPE__ && defined __PTRDIFF_MAX__
#  define YYPTRDIFF_T __PTRDIFF_TYPE__
#  define YYPTRDIFF_MAXIMUM __PTRDIFF_MAX__
# elif defined PTRDIFF_MAX
#  ifndef ptrdiff_t
#   include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  endif
#  define YYPTRDIFF_T ptrdiff_t
#  define YYPTRDIFF_MAXIMUM PTRDIFF_MAX
# else
#  define YYPTRDIFF_T long
#  define YYPTRDIFF_MAXIMUM LONG_MAX
# endif
#endif

#ifndef YYSIZE_T
# ifdef __SIZE_TYPE__
#  define YYSIZE_T __SIZE_TYPE__
# elif defined size_t
#  define YYSIZE_T size_t
# elif defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  define YYSIZE_T size_t
# else
#  define YYSIZE_T unsigned
# endif
#endif

#define YYSIZE_MAXIMUM                                  \
  YY_CAST (YYPTRDIFF_T,                                 \
           (YYPTRDIFF_MAXIMUM < YY_CAST (YYSIZE_T, -1)  \
            ? YYPTRDIFF_MAXIMUM                         \
            : YY_CAST (YYSIZE_T, -1)))

#define YYSIZEOF(X) YY_CAST (YYPTRDIFF_T, sizeof (X))


/* Stored state numbers (used for stacks). */
typedef yytype_int8 yy_state_t;

/* State numbers in computations.  */
typedef int yy_state_fast_t;

#ifndef YY_
# if defined YYENABLE_NLS && YYENABLE_NLS
#  if ENABLE_NLS
#   include <libintl.h> /* INFRINGES ON USER NAME SPACE */
#   define YY_(Msgid) dgettext ("bison-runtime", Msgid)
#  endif
# endif
# ifndef YY_
#  define YY_(Msgid) Msgid
# endif
#endif


#ifndef YY_ATTRIBUTE_PURE
# if defined __GNUC__ && 2 < __GNUC__ + (96 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_PURE __attribute__ ((__pure__))
# else
#  define YY_ATTRIBUTE_PURE
# endif
#endif

#ifndef YY_ATTRIBUTE_UNUSED
# if defined __GNUC__ && 2 < __GNUC__ + (7 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_UNUSED __attribute__ ((__unused__))
# else
#  define YY_ATTRIBUTE_UNUSED
# endif
#endif

/* Suppress unused-variable warnings by "using" E.  */
#if ! defined lint || defined __GNUC__
# define YY_USE(E) ((void) (E))
#else
# define YY_USE(E) /* empty */
#endif

/* Suppress an incorrect diagnostic about yylval being uninitialized.  */
#if defined __GNUC__ && ! defined __ICC && 406 <= __GNUC__ * 100 + __GNUC_MINOR__
# if __GNUC__ * 100 + __GNUC_MINOR__ < 407
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")
# else
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")              \
    _Pragma ("GCC diagnostic ignored \"-Wmaybe-uninitialized\"")
# endif
# define YY_IGNORE_MAYBE_UNINITIALIZED_END      \
    _Pragma ("GCC diagnostic pop")
#else
# define YY_INITIAL_VALUE(Value) Value
#endif
#ifndef YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_END
#endif
#ifndef YY_INITIAL_VALUE
# define YY_INITIAL_VALUE(Value) /* Nothing. */
#endif

#if defined __cplusplus && defined __GNUC__ && ! defined __ICC && 6 <= __GNUC__
# define YY_IGNORE_USELESS_CAST_BEGIN                          \
    _Pragma ("GCC diagnostic push")                            \
    _Pragma ("GCC diagnostic ignored \"-Wuseless-cast\"")
# define YY_IGNORE_USELESS_CAST_END            \
    _Pragma ("GCC diagnostic pop")
#endif
#ifndef YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_END
#endif


#define YY_ASSERT(E) ((void) (0 && (E)))

#if !defined yyoverflow

/* The parser invokes alloca or malloc; define the necessary symbols.  */

# ifdef YYSTACK_USE_ALLOCA
#  if YYSTACK_USE_ALLOCA
#   ifdef __GNUC__
#    define YYSTACK_ALLOC __builtin_alloca
#   elif defined __BUILTIN_VA_ARG_INCR
#    include <alloca.h> /* INFRINGES ON USER NAME SPACE */
#   elif defined _AIX
#    define YYSTACK_ALLOC __alloca
#   elif defined _MSC_VER
#    include <malloc.h> /* INFRINGES ON USER NAME SPACE */
#    define alloca _alloca
#   else
#    define YYSTACK_ALLOC alloca
#    if ! defined _ALLOCA_H && ! defined EXIT_SUCCESS
#     include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
      /* Use EXIT_SUCCESS as a witness for stdlib.h.  */
#     ifndef EXIT_SUCCESS
#      define EXIT_SUCCESS 0
#     endif
#    endif
#   endif
#  endif
# endif

# ifdef YYSTACK_ALLOC
   /* Pacify GCC's 'empty if-body' warning.  */
#  define YYSTACK_FREE(Ptr) do { /* empty */; } while (0)
#  ifndef YYSTACK_ALLOC_MAXIMUM
    /* The OS might guarantee only one guard page at the bottom of the stack,
       and a page size can be as small as 4096 bytes.  So we cannot safely
       invoke alloca (N) if N exceeds 4096.  Use a slightly smaller number
       to allow for a few compiler-allocated temporary stack slots.  */
#   define YYSTACK_ALLOC_MAXIMUM 4032 /* reasonable circa 2006 */
#  endif
# else
#  define YYSTACK_ALLOC YYMALLOC
#  define YYSTACK_FREE YYFREE
#  ifndef YYSTACK_ALLOC_MAXIMUM
#   define YYSTACK_ALLOC_MAXIMUM YYSIZE_MAXIMUM
#  endif
#  if (defined __cplusplus && ! defined EXIT_SUCCESS \
       && ! ((defined YYMALLOC || defined malloc) \
             && (defined YYFREE || defined free)))
#   include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#   ifndef EXIT_SUCCESS
#    define EXIT_SUCCESS 0
#   endif
#  endif
#  ifndef YYMALLOC
#   define YYMALLOC malloc
#   if ! defined malloc && ! defined EXIT_SUCCESS
void *malloc (YYSIZE_T); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
#  ifndef YYFREE
#   define YYFREE free
#   if ! defined free && ! defined EXIT_SUCCESS
void free (void *); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
# endif
#endif /* !defined yyoverflow */

#if (! defined yyoverflow \
     && (! defined __cplusplus \
         || (defined YYSTYPE_IS_TRIVIAL && YYSTYPE_IS_TRIVIAL)))

/* A type that is properly aligned for any stack member.  */
union yyalloc
{
  yy_state_t yyss_alloc;
  YYSTYPE yyvs_alloc;
};

/* The size of the maximum gap between one aligned stack and the next.  */
# define YYSTACK_GAP_MAXIMUM (YYSIZEOF (union yyalloc) - 1)

/* The size of an array large to enough to hold all stacks, each with
   N elements.  */
# define YYSTACK_BYTES(N) \
     ((N) * (YYSIZEOF (yy_state_t) + YYSIZEOF (YYSTYPE)) \
      + YYSTACK_GAP_MAXIMUM)

# define YYCOPY_NEEDED 1

/* Relocate STACK from its old location to the new one.  The
   local variables YYSIZE and YYSTACKSIZE give the old and new number of
   elements in the stack, and YYPTR gives the new location of the
   stack.  Advance YYPTR to a properly aligned location for the next
   stack.  */
# define YYSTACK_RELOCATE(Stack_alloc, Stack)                           \
    do                                                                  \
      {                                                                 \
        YYPTRDIFF_T yynewbytes;                                         \
        YYCOPY (&yyptr->Stack_alloc, Stack, yysize);                    \
        Stack = &yyptr->Stack_alloc;                                    \
        yynewbytes = yystacksize * YYSIZEOF (*Stack) + YYSTACK_GAP_MAXIMUM; \
        yyptr += yynewbytes / YYSIZEOF (*yyptr);                        \
      }                                                                 \
    while (0)

#endif

#if defined YYCOPY_NEEDED && YYCOPY_NEEDED
/* Copy COUNT objects from SRC to DST.  The source and destination do
   not overlap.  */
# ifndef YYCOPY
#  if defined __GNUC__ && 1 < __GNUC__
#   define YYCOPY(Dst, Src, Count) \
      __builtin_memcpy (Dst, Src, YY_CAST (YYSIZE_T, (Count)) * sizeof (*(Src)))
#  else
#   define YYCOPY(Dst, Src, Count)              \
      do                                        \
        {                                       \
          YYPTRDIFF_T yyi;                      \
          for (yyi = 0; yyi < (Count); yyi++)   \
            (Dst)[yyi] = (Src)[yyi];            \
        }                                       \
      while (0)
#  endif
# endif
#endif /* !YYCOPY_NEEDED */

/* YYFINAL -- State number of the termination state.  */
#define YYFINAL  9
/* YYLAST -- Last index in YYTABLE.  */
#define YYLAST   105

/* YYNTOKENS -- Number of terminals.  */
#define YYNTOKENS  30
/* YYNNTS -- Number of nonterminals.  */
#define YYNNTS  32
/* YYNRULES -- Number of rules.  */
#define YYNRULES  66
/* YYNSTATES -- Number of states.  */
#define YYNSTATES  106

/* YYMAXUTOK -- Last valid token kind.  */
#define YYMAXUTOK   257


/* YYTRANSLATE(TOKEN-NUM) -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex, with out-of-bounds checking.  */
#define YYTRANSLATE(YYX)                                \
  (0 <= (YYX) && (YYX) <= YYMAXUTOK                     \
   ? YY_CAST (yysymbol_kind_t, yytranslate[YYX])        \
   : YYSYMBOL_YYUNDEF)

/* YYTRANSLATE[TOKEN-NUM] -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex.  */
static const yytype_int8 yytranslate[] =
{
       0,     3,     4,     5,     6,     7,     8,     9,    10,    11,
      12,    13,    14,    15,    16,    17,    18,    19,    20,    21,
      22,    23,    24,    25,    26,    27,    28,    29,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     1,     2
};

#if YYDEBUG
/* YYRLINE[YYN] -- Source line where rule number YYN was defined.  */
static const yytype_int16 yyrline[] =
{
       0,    72,    72,    79,    82,    88,    91,    97,   103,   112,
     115,   121,   130,   133,   139,   142,   148,   152,   159,   165,
     168,   174,   177,   183,   184,   189,   192,   199,   202,   209,
     212,   215,   218,   224,   231,   237,   240,   246,   249,   255,
     260,   268,   271,   277,   278,   279,   280,   281,   282,   286,
     289,   295,   296,   300,   303,   309,   310,   314,   317,   320,
     323,   329,   336,   339,   345,   348,   351
};
#endif

/** Accessing symbol of state STATE.  */
#define YY_ACCESSING_SYMBOL(State) YY_CAST (yysymbol_kind_t, yystos[State])

#if YYDEBUG || 0
/* The user-facing name of the symbol whose (internal) number is
   YYSYMBOL.  No bounds checking.  */
static const char *yysymbol_name (yysymbol_kind_t yysymbol) YY_ATTRIBUTE_UNUSED;

/* YYTNAME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
   First, the terminals, then, starting at YYNTOKENS, nonterminals.  */
static const char *const yytname[] =
{
  "\"end of file\"", "error", "\"invalid token\"", "IF", "WHILE",
  "RETURN", "INT", "VOID", "NUM", "ID", "EQ", "NEQ", "LT", "LTE", "GT",
  "GTE", "PLUS", "MINUS", "TIMES", "DIV", "ASSIGN", "SEMICOLON", "COMMA",
  "LPAREN", "RPAREN", "LBRACE", "RBRACE", "LBRACK", "RBRACK", "ELSE",
  "$accept", "program", "declaration_list", "declaration",
  "var_declaration", "type_specifier", "fun_declaration", "params",
  "param_list", "param", "compound_decl", "local_declarations",
  "statement_list", "statement", "matched_stmt", "unmatched_stmt",
  "other_stmt", "expression_decl", "iteration_decl", "return_decl",
  "expression", "var", "simple_expression", "relational", "sum_expression",
  "sum", "term", "mult", "factor", "call", "args", "arg_list", YY_NULLPTR
};

static const char *
yysymbol_name (yysymbol_kind_t yysymbol)
{
  return yytname[yysymbol];
}
#endif

#define YYPACT_NINF (-90)

#define yypact_value_is_default(Yyn) \
  ((Yyn) == YYPACT_NINF)

#define YYTABLE_NINF (-14)

#define yytable_value_is_error(Yyn) \
  0

/* YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
   STATE-NUM.  */
static const yytype_int8 yypact[] =
{
       9,   -90,   -90,    11,     9,   -90,   -90,    17,   -90,   -90,
     -90,    39,   -90,    62,    28,    21,    29,    24,    54,   -90,
      49,    51,    55,     9,    58,    53,   -90,   -90,   -90,   -90,
     -90,     9,   -90,    73,     4,   -17,    60,    61,    26,   -90,
      38,    23,   -90,   -90,   -90,   -90,   -90,   -90,   -90,   -90,
     -90,    64,    66,   -90,    40,    52,   -90,   -90,    23,    23,
     -90,    67,    35,    23,    63,   -90,    23,   -90,   -90,   -90,
     -90,   -90,   -90,   -90,   -90,    23,    23,   -90,   -90,    23,
      65,    68,   -90,   -90,   -90,    69,    72,    70,   -90,   -90,
     -90,    56,    52,   -90,    14,    14,   -90,    23,   -90,   -90,
      71,   -90,   -90,    14,   -90,   -90
};

/* YYDEFACT[STATE-NUM] -- Default reduction number in state STATE-NUM.
   Performed when YYTABLE does not specify something else to do.  Zero
   means the default is an error.  */
static const yytype_int8 yydefact[] =
{
       0,     9,    10,     0,     2,     4,     5,     0,     6,     1,
       3,     0,     7,     0,     0,    10,     0,     0,    12,    15,
       0,    16,     0,     0,     0,     0,    20,    11,    14,     8,
      17,    22,    19,     0,     0,     0,     0,     0,     0,    60,
      39,     0,    18,    30,    21,    23,    24,    26,    29,    31,
      32,     0,    58,    38,    42,    50,    54,    59,     0,     0,
      35,     0,    63,     0,     0,    33,     0,    47,    48,    43,
      44,    45,    46,    51,    52,     0,     0,    55,    56,     0,
       0,     0,    36,    66,    65,     0,    62,     0,    57,    37,
      58,    41,    49,    53,     0,     0,    61,     0,    40,    27,
      23,    34,    64,     0,    25,    28
};

/* YYPGOTO[NTERM-NUM].  */
static const yytype_int8 yypgoto[] =
{
     -90,   -90,   -90,    86,    74,     2,   -90,   -90,   -90,   -22,
      75,   -90,   -90,   -20,   -89,    -8,   -90,   -90,   -90,   -90,
     -38,   -12,   -90,   -90,    16,   -90,    20,   -90,    22,   -90,
     -90,   -90
};

/* YYDEFGOTO[NTERM-NUM].  */
static const yytype_int8 yydefgoto[] =
{
       0,     3,     4,     5,     6,    16,     8,    17,    18,    19,
      43,    31,    34,    44,    45,    46,    47,    48,    49,    50,
      51,    52,    53,    75,    54,    76,    55,    79,    56,    57,
      85,    86
};

/* YYTABLE[YYPACT[STATE-NUM]] -- What to do in state STATE-NUM.  If
   positive, shift that token.  If negative, reduce the rule whose
   number is the opposite.  If YYTABLE_NINF, syntax error.  */
static const yytype_int8 yytable[] =
{
      61,    28,     7,    64,    12,   100,     7,    36,    37,    38,
      14,     9,    39,    40,   104,     1,     2,    36,    37,    38,
      80,    81,    39,    40,    84,    87,    11,    41,    89,    26,
      42,    39,    40,    33,    39,    40,    20,    41,    21,    26,
      83,     1,     2,    39,    40,   -13,    41,    60,    22,    41,
      67,    68,    69,    70,    71,    72,    73,    74,    41,   102,
      12,    62,    13,    90,    90,    63,    14,    90,     1,    15,
      77,    78,    73,    74,    99,   101,    23,    24,    25,    29,
      26,    30,    35,    58,    59,    65,    66,    88,    82,    94,
      10,    91,    95,    96,    97,   105,    92,    27,    98,     0,
     103,    93,     0,     0,     0,    32
};

static const yytype_int8 yycheck[] =
{
      38,    23,     0,    41,    21,    94,     4,     3,     4,     5,
      27,     0,     8,     9,   103,     6,     7,     3,     4,     5,
      58,    59,     8,     9,    62,    63,     9,    23,    66,    25,
      26,     8,     9,    31,     8,     9,     8,    23,     9,    25,
      62,     6,     7,     8,     9,    24,    23,    21,    24,    23,
      10,    11,    12,    13,    14,    15,    16,    17,    23,    97,
      21,    23,    23,    75,    76,    27,    27,    79,     6,     7,
      18,    19,    16,    17,    94,    95,    22,    28,    27,    21,
      25,    28,     9,    23,    23,    21,    20,    24,    21,    24,
       4,    75,    24,    24,    22,   103,    76,    22,    28,    -1,
      29,    79,    -1,    -1,    -1,    31
};

/* YYSTOS[STATE-NUM] -- The symbol kind of the accessing symbol of
   state STATE-NUM.  */
static const yytype_int8 yystos[] =
{
       0,     6,     7,    31,    32,    33,    34,    35,    36,     0,
      33,     9,    21,    23,    27,     7,    35,    37,    38,    39,
       8,     9,    24,    22,    28,    27,    25,    40,    39,    21,
      28,    41,    34,    35,    42,     9,     3,     4,     5,     8,
       9,    23,    26,    40,    43,    44,    45,    46,    47,    48,
      49,    50,    51,    52,    54,    56,    58,    59,    23,    23,
      21,    50,    23,    27,    50,    21,    20,    10,    11,    12,
      13,    14,    15,    16,    17,    53,    55,    18,    19,    57,
      50,    50,    21,    39,    50,    60,    61,    50,    24,    50,
      51,    54,    56,    58,    24,    24,    24,    22,    28,    43,
      44,    43,    50,    29,    44,    45
};

/* YYR1[RULE-NUM] -- Symbol kind of the left-hand side of rule RULE-NUM.  */
static const yytype_int8 yyr1[] =
{
       0,    30,    31,    32,    32,    33,    33,    34,    34,    35,
      35,    36,    37,    37,    38,    38,    39,    39,    40,    41,
      41,    42,    42,    43,    43,    44,    44,    45,    45,    46,
      46,    46,    46,    47,    48,    49,    49,    50,    50,    51,
      51,    52,    52,    53,    53,    53,    53,    53,    53,    54,
      54,    55,    55,    56,    56,    57,    57,    58,    58,    58,
      58,    59,    60,    60,    61,    61,    61
};

/* YYR2[RULE-NUM] -- Number of symbols on the right-hand side of rule RULE-NUM.  */
static const yytype_int8 yyr2[] =
{
       0,     2,     1,     2,     1,     1,     1,     3,     6,     1,
       1,     6,     1,     1,     3,     1,     2,     4,     4,     2,
       0,     2,     0,     1,     1,     7,     1,     5,     7,     1,
       1,     1,     1,     2,     5,     2,     3,     3,     1,     1,
       4,     3,     1,     1,     1,     1,     1,     1,     1,     3,
       1,     1,     1,     3,     1,     1,     1,     3,     1,     1,
       1,     4,     1,     0,     3,     1,     1
};


enum { YYENOMEM = -2 };

#define yyerrok         (yyerrstatus = 0)
#define yyclearin       (yychar = YYEMPTY)

#define YYACCEPT        goto yyacceptlab
#define YYABORT         goto yyabortlab
#define YYERROR         goto yyerrorlab
#define YYNOMEM         goto yyexhaustedlab


#define YYRECOVERING()  (!!yyerrstatus)

#define YYBACKUP(Token, Value)                                    \
  do                                                              \
    if (yychar == YYEMPTY)                                        \
      {                                                           \
        yychar = (Token);                                         \
        yylval = (Value);                                         \
        YYPOPSTACK (yylen);                                       \
        yystate = *yyssp;                                         \
        goto yybackup;                                            \
      }                                                           \
    else                                                          \
      {                                                           \
        yyerror (YY_("syntax error: cannot back up")); \
        YYERROR;                                                  \
      }                                                           \
  while (0)

/* Backward compatibility with an undocumented macro.
   Use YYerror or YYUNDEF. */
#define YYERRCODE YYUNDEF


/* Enable debugging if requested.  */
#if YYDEBUG

# ifndef YYFPRINTF
#  include <stdio.h> /* INFRINGES ON USER NAME SPACE */
#  define YYFPRINTF fprintf
# endif

# define YYDPRINTF(Args)                        \
do {                                            \
  if (yydebug)                                  \
    YYFPRINTF Args;                             \
} while (0)




# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)                    \
do {                                                                      \
  if (yydebug)                                                            \
    {                                                                     \
      YYFPRINTF (stderr, "%s ", Title);                                   \
      yy_symbol_print (stderr,                                            \
                  Kind, Value); \
      YYFPRINTF (stderr, "\n");                                           \
    }                                                                     \
} while (0)


/*-----------------------------------.
| Print this symbol's value on YYO.  |
`-----------------------------------*/

static void
yy_symbol_value_print (FILE *yyo,
                       yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  FILE *yyoutput = yyo;
  YY_USE (yyoutput);
  if (!yyvaluep)
    return;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/*---------------------------.
| Print this symbol on YYO.  |
`---------------------------*/

static void
yy_symbol_print (FILE *yyo,
                 yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  YYFPRINTF (yyo, "%s %s (",
             yykind < YYNTOKENS ? "token" : "nterm", yysymbol_name (yykind));

  yy_symbol_value_print (yyo, yykind, yyvaluep);
  YYFPRINTF (yyo, ")");
}

/*------------------------------------------------------------------.
| yy_stack_print -- Print the state stack from its BOTTOM up to its |
| TOP (included).                                                   |
`------------------------------------------------------------------*/

static void
yy_stack_print (yy_state_t *yybottom, yy_state_t *yytop)
{
  YYFPRINTF (stderr, "Stack now");
  for (; yybottom <= yytop; yybottom++)
    {
      int yybot = *yybottom;
      YYFPRINTF (stderr, " %d", yybot);
    }
  YYFPRINTF (stderr, "\n");
}

# define YY_STACK_PRINT(Bottom, Top)                            \
do {                                                            \
  if (yydebug)                                                  \
    yy_stack_print ((Bottom), (Top));                           \
} while (0)


/*------------------------------------------------.
| Report that the YYRULE is going to be reduced.  |
`------------------------------------------------*/

static void
yy_reduce_print (yy_state_t *yyssp, YYSTYPE *yyvsp,
                 int yyrule)
{
  int yylno = yyrline[yyrule];
  int yynrhs = yyr2[yyrule];
  int yyi;
  YYFPRINTF (stderr, "Reducing stack by rule %d (line %d):\n",
             yyrule - 1, yylno);
  /* The symbols being reduced.  */
  for (yyi = 0; yyi < yynrhs; yyi++)
    {
      YYFPRINTF (stderr, "   $%d = ", yyi + 1);
      yy_symbol_print (stderr,
                       YY_ACCESSING_SYMBOL (+yyssp[yyi + 1 - yynrhs]),
                       &yyvsp[(yyi + 1) - (yynrhs)]);
      YYFPRINTF (stderr, "\n");
    }
}

# define YY_REDUCE_PRINT(Rule)          \
do {                                    \
  if (yydebug)                          \
    yy_reduce_print (yyssp, yyvsp, Rule); \
} while (0)

/* Nonzero means print parse trace.  It is left uninitialized so that
   multiple parsers can coexist.  */
int yydebug;
#else /* !YYDEBUG */
# define YYDPRINTF(Args) ((void) 0)
# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)
# define YY_STACK_PRINT(Bottom, Top)
# define YY_REDUCE_PRINT(Rule)
#endif /* !YYDEBUG */


/* YYINITDEPTH -- initial size of the parser's stacks.  */
#ifndef YYINITDEPTH
# define YYINITDEPTH 200
#endif

/* YYMAXDEPTH -- maximum size the stacks can grow to (effective only
   if the built-in stack extension method is used).

   Do not make this value too large; the results are undefined if
   YYSTACK_ALLOC_MAXIMUM < YYSTACK_BYTES (YYMAXDEPTH)
   evaluated with infinite-precision integer arithmetic.  */

#ifndef YYMAXDEPTH
# define YYMAXDEPTH 10000
#endif






/*-----------------------------------------------.
| Release the memory associated to this symbol.  |
`-----------------------------------------------*/

static void
yydestruct (const char *yymsg,
            yysymbol_kind_t yykind, YYSTYPE *yyvaluep)
{
  YY_USE (yyvaluep);
  if (!yymsg)
    yymsg = "Deleting";
  YY_SYMBOL_PRINT (yymsg, yykind, yyvaluep, yylocationp);

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/* Lookahead token kind.  */
int yychar;

/* The semantic value of the lookahead symbol.  */
YYSTYPE yylval;
/* Number of syntax errors so far.  */
int yynerrs;




/*----------.
| yyparse.  |
`----------*/

int
yyparse (void)
{
    yy_state_fast_t yystate = 0;
    /* Number of tokens to shift before error messages enabled.  */
    int yyerrstatus = 0;

    /* Refer to the stacks through separate pointers, to allow yyoverflow
       to reallocate them elsewhere.  */

    /* Their size.  */
    YYPTRDIFF_T yystacksize = YYINITDEPTH;

    /* The state stack: array, bottom, top.  */
    yy_state_t yyssa[YYINITDEPTH];
    yy_state_t *yyss = yyssa;
    yy_state_t *yyssp = yyss;

    /* The semantic value stack: array, bottom, top.  */
    YYSTYPE yyvsa[YYINITDEPTH];
    YYSTYPE *yyvs = yyvsa;
    YYSTYPE *yyvsp = yyvs;

  int yyn;
  /* The return value of yyparse.  */
  int yyresult;
  /* Lookahead symbol kind.  */
  yysymbol_kind_t yytoken = YYSYMBOL_YYEMPTY;
  /* The variables used to return semantic value and location from the
     action routines.  */
  YYSTYPE yyval;



#define YYPOPSTACK(N)   (yyvsp -= (N), yyssp -= (N))

  /* The number of symbols on the RHS of the reduced rule.
     Keep to zero when no symbol should be popped.  */
  int yylen = 0;

  YYDPRINTF ((stderr, "Starting parse\n"));

  yychar = YYEMPTY; /* Cause a token to be read.  */

  goto yysetstate;


/*------------------------------------------------------------.
| yynewstate -- push a new state, which is found in yystate.  |
`------------------------------------------------------------*/
yynewstate:
  /* In all cases, when you get here, the value and location stacks
     have just been pushed.  So pushing a state here evens the stacks.  */
  yyssp++;


/*--------------------------------------------------------------------.
| yysetstate -- set current state (the top of the stack) to yystate.  |
`--------------------------------------------------------------------*/
yysetstate:
  YYDPRINTF ((stderr, "Entering state %d\n", yystate));
  YY_ASSERT (0 <= yystate && yystate < YYNSTATES);
  YY_IGNORE_USELESS_CAST_BEGIN
  *yyssp = YY_CAST (yy_state_t, yystate);
  YY_IGNORE_USELESS_CAST_END
  YY_STACK_PRINT (yyss, yyssp);

  if (yyss + yystacksize - 1 <= yyssp)
#if !defined yyoverflow && !defined YYSTACK_RELOCATE
    YYNOMEM;
#else
    {
      /* Get the current used size of the three stacks, in elements.  */
      YYPTRDIFF_T yysize = yyssp - yyss + 1;

# if defined yyoverflow
      {
        /* Give user a chance to reallocate the stack.  Use copies of
           these so that the &'s don't force the real ones into
           memory.  */
        yy_state_t *yyss1 = yyss;
        YYSTYPE *yyvs1 = yyvs;

        /* Each stack pointer address is followed by the size of the
           data in use in that stack, in bytes.  This used to be a
           conditional around just the two extra args, but that might
           be undefined if yyoverflow is a macro.  */
        yyoverflow (YY_("memory exhausted"),
                    &yyss1, yysize * YYSIZEOF (*yyssp),
                    &yyvs1, yysize * YYSIZEOF (*yyvsp),
                    &yystacksize);
        yyss = yyss1;
        yyvs = yyvs1;
      }
# else /* defined YYSTACK_RELOCATE */
      /* Extend the stack our own way.  */
      if (YYMAXDEPTH <= yystacksize)
        YYNOMEM;
      yystacksize *= 2;
      if (YYMAXDEPTH < yystacksize)
        yystacksize = YYMAXDEPTH;

      {
        yy_state_t *yyss1 = yyss;
        union yyalloc *yyptr =
          YY_CAST (union yyalloc *,
                   YYSTACK_ALLOC (YY_CAST (YYSIZE_T, YYSTACK_BYTES (yystacksize))));
        if (! yyptr)
          YYNOMEM;
        YYSTACK_RELOCATE (yyss_alloc, yyss);
        YYSTACK_RELOCATE (yyvs_alloc, yyvs);
#  undef YYSTACK_RELOCATE
        if (yyss1 != yyssa)
          YYSTACK_FREE (yyss1);
      }
# endif

      yyssp = yyss + yysize - 1;
      yyvsp = yyvs + yysize - 1;

      YY_IGNORE_USELESS_CAST_BEGIN
      YYDPRINTF ((stderr, "Stack size increased to %ld\n",
                  YY_CAST (long, yystacksize)));
      YY_IGNORE_USELESS_CAST_END

      if (yyss + yystacksize - 1 <= yyssp)
        YYABORT;
    }
#endif /* !defined yyoverflow && !defined YYSTACK_RELOCATE */


  if (yystate == YYFINAL)
    YYACCEPT;

  goto yybackup;


/*-----------.
| yybackup.  |
`-----------*/
yybackup:
  /* Do appropriate processing given the current state.  Read a
     lookahead token if we need one and don't already have one.  */

  /* First try to decide what to do without reference to lookahead token.  */
  yyn = yypact[yystate];
  if (yypact_value_is_default (yyn))
    goto yydefault;

  /* Not known => get a lookahead token if don't already have one.  */

  /* YYCHAR is either empty, or end-of-input, or a valid lookahead.  */
  if (yychar == YYEMPTY)
    {
      YYDPRINTF ((stderr, "Reading a token\n"));
      yychar = yylex ();
    }

  if (yychar <= YYEOF)
    {
      yychar = YYEOF;
      yytoken = YYSYMBOL_YYEOF;
      YYDPRINTF ((stderr, "Now at end of input.\n"));
    }
  else if (yychar == YYerror)
    {
      /* The scanner already issued an error message, process directly
         to error recovery.  But do not keep the error token as
         lookahead, it is too special and may lead us to an endless
         loop in error recovery. */
      yychar = YYUNDEF;
      yytoken = YYSYMBOL_YYerror;
      goto yyerrlab1;
    }
  else
    {
      yytoken = YYTRANSLATE (yychar);
      YY_SYMBOL_PRINT ("Next token is", yytoken, &yylval, &yylloc);
    }

  /* If the proper action on seeing token YYTOKEN is to reduce or to
     detect an error, take that action.  */
  yyn += yytoken;
  if (yyn < 0 || YYLAST < yyn || yycheck[yyn] != yytoken)
    goto yydefault;
  yyn = yytable[yyn];
  if (yyn <= 0)
    {
      if (yytable_value_is_error (yyn))
        goto yyerrlab;
      yyn = -yyn;
      goto yyreduce;
    }

  /* Count tokens shifted since error; after three, turn off error
     status.  */
  if (yyerrstatus)
    yyerrstatus--;

  /* Shift the lookahead token.  */
  YY_SYMBOL_PRINT ("Shifting", yytoken, &yylval, &yylloc);
  yystate = yyn;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END

  /* Discard the shifted token.  */
  yychar = YYEMPTY;
  goto yynewstate;


/*-----------------------------------------------------------.
| yydefault -- do the default action for the current state.  |
`-----------------------------------------------------------*/
yydefault:
  yyn = yydefact[yystate];
  if (yyn == 0)
    goto yyerrlab;
  goto yyreduce;


/*-----------------------------.
| yyreduce -- do a reduction.  |
`-----------------------------*/
yyreduce:
  /* yyn is the number of a rule to reduce with.  */
  yylen = yyr2[yyn];

  /* If YYLEN is nonzero, implement the default value of the action:
     '$$ = $1'.

     Otherwise, the following line sets YYVAL to garbage.
     This behavior is undocumented and Bison
     users should not rely upon it.  Assigning to YYVAL
     unconditionally makes the parser a bit smaller, and it avoids a
     GCC warning that YYVAL may be used uninitialized.  */
  yyval = yyvsp[1-yylen];


  YY_REDUCE_PRINT (yyn);
  switch (yyn)
    {
  case 2: /* program: declaration_list  */
#line 72 "parser/parser.y"
                     {
        printf("Program parsed successfully.\n");
        syntax_tree = yyvsp[0];
    }
#line 1228 "parser.tab.c"
    break;

  case 3: /* declaration_list: declaration_list declaration  */
#line 79 "parser/parser.y"
                                 {
        yyval = traversal(yyvsp[-1], yyvsp[0]);
    }
#line 1236 "parser.tab.c"
    break;

  case 4: /* declaration_list: declaration  */
#line 82 "parser/parser.y"
                  {
        yyval = yyvsp[0];
    }
#line 1244 "parser.tab.c"
    break;

  case 5: /* declaration: var_declaration  */
#line 88 "parser/parser.y"
                    {
        yyval = yyvsp[0];
    }
#line 1252 "parser.tab.c"
    break;

  case 6: /* declaration: fun_declaration  */
#line 91 "parser/parser.y"
                      {
        yyval = yyvsp[0];
    }
#line 1260 "parser.tab.c"
    break;

  case 7: /* var_declaration: type_specifier ID SEMICOLON  */
#line 97 "parser/parser.y"
                                {
        yyval = createDeclVarNode(declVar, yyvsp[-2]);
        yyval->name = strdup(yytext);
        yyval->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, yyvsp[-2]->type);
    }
#line 1271 "parser.tab.c"
    break;

  case 8: /* var_declaration: type_specifier ID LBRACK NUM RBRACK SEMICOLON  */
#line 103 "parser/parser.y"
                                                    {
        yyval = createArrayDeclVarNode(expNum, declVar, yyvsp[-5]);
        yyval->name = strdup(yytext);
        yyval->line = yylineno;
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, yyvsp[-5]->type);
    }
#line 1282 "parser.tab.c"
    break;

  case 9: /* type_specifier: INT  */
#line 112 "parser/parser.y"
        {
        yyval = createDeclNode(declIdType); yyval->type = Integer;
    }
#line 1290 "parser.tab.c"
    break;

  case 10: /* type_specifier: VOID  */
#line 115 "parser/parser.y"
           {
        yyval = createDeclNode(declIdType); yyval->type = Void;
    }
#line 1298 "parser.tab.c"
    break;

  case 11: /* fun_declaration: type_specifier ID LPAREN params RPAREN compound_decl  */
#line 121 "parser/parser.y"
                                                         {
        yyval = createDeclFuncNode(declFunc, yyvsp[-5], yyvsp[-2], yyvsp[0]); paramsCount = 0;
        int funcLine = functionCurrentLine;
        currentScope = strdup(yytext); /* update scope to function name */
        insertSymbolInTable(functionName, "global", FUNC, funcLine - 1, yyvsp[-5]->type);
    }
#line 1309 "parser.tab.c"
    break;

  case 12: /* params: param_list  */
#line 130 "parser/parser.y"
               {
        yyval = yyvsp[0];
    }
#line 1317 "parser.tab.c"
    break;

  case 13: /* params: VOID  */
#line 133 "parser/parser.y"
           {
        yyval = createEmptyParams(expId);
    }
#line 1325 "parser.tab.c"
    break;

  case 14: /* param_list: param_list COMMA param  */
#line 139 "parser/parser.y"
                           {
        yyval = traversal(yyvsp[-2], yyvsp[0]);
    }
#line 1333 "parser.tab.c"
    break;

  case 15: /* param_list: param  */
#line 142 "parser/parser.y"
            {
        yyval = yyvsp[0];
    }
#line 1341 "parser.tab.c"
    break;

  case 16: /* param: type_specifier ID  */
#line 148 "parser/parser.y"
                      {
        yyval = createDeclVarNode(declVar, yyvsp[-1]);
        insertSymbolInTable(expName, currentScope, VAR, yylineno, yyvsp[-1]->type);
    }
#line 1350 "parser.tab.c"
    break;

  case 17: /* param: type_specifier ID LBRACK RBRACK  */
#line 152 "parser/parser.y"
                                      {
        yyval = createArrayArg(declVar, yyvsp[-3]);
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, yyvsp[-3]->type);
    }
#line 1359 "parser.tab.c"
    break;

  case 18: /* compound_decl: LBRACE local_declarations statement_list RBRACE  */
#line 159 "parser/parser.y"
                                                    {
        yyval = traversal(yyvsp[-2], yyvsp[-1]);
    }
#line 1367 "parser.tab.c"
    break;

  case 19: /* local_declarations: local_declarations var_declaration  */
#line 165 "parser/parser.y"
                                       {
        yyval = traversal(yyvsp[-1], yyvsp[0]);
    }
#line 1375 "parser.tab.c"
    break;

  case 20: /* local_declarations: %empty  */
#line 168 "parser/parser.y"
                  {
        yyval = NULL;
    }
#line 1383 "parser.tab.c"
    break;

  case 21: /* statement_list: statement_list statement  */
#line 174 "parser/parser.y"
                             {
        yyval = traversal(yyvsp[-1], yyvsp[0]);
    }
#line 1391 "parser.tab.c"
    break;

  case 22: /* statement_list: %empty  */
#line 177 "parser/parser.y"
                  {
        yyval = NULL;
    }
#line 1399 "parser.tab.c"
    break;

  case 25: /* matched_stmt: IF LPAREN expression RPAREN matched_stmt ELSE matched_stmt  */
#line 189 "parser/parser.y"
                                                               {
        yyval = createIfStmt(stmtIf, yyvsp[-4], yyvsp[-2], yyvsp[0]);
    }
#line 1407 "parser.tab.c"
    break;

  case 26: /* matched_stmt: other_stmt  */
#line 192 "parser/parser.y"
               {
        yyval = yyvsp[0];
    }
#line 1415 "parser.tab.c"
    break;

  case 27: /* unmatched_stmt: IF LPAREN expression RPAREN statement  */
#line 199 "parser/parser.y"
                                          {
        yyval = createIfStmt(stmtIf, yyvsp[-2], yyvsp[0], NULL);
    }
#line 1423 "parser.tab.c"
    break;

  case 28: /* unmatched_stmt: IF LPAREN expression RPAREN matched_stmt ELSE unmatched_stmt  */
#line 202 "parser/parser.y"
                                                                 {
        yyval = createIfStmt(stmtIf, yyvsp[-4], yyvsp[-2], yyvsp[0]);
    }
#line 1431 "parser.tab.c"
    break;

  case 29: /* other_stmt: expression_decl  */
#line 209 "parser/parser.y"
                    {
        yyval = yyvsp[0];
    }
#line 1439 "parser.tab.c"
    break;

  case 30: /* other_stmt: compound_decl  */
#line 212 "parser/parser.y"
                  {
        yyval = yyvsp[0];
    }
#line 1447 "parser.tab.c"
    break;

  case 31: /* other_stmt: iteration_decl  */
#line 215 "parser/parser.y"
                   {
        yyval = yyvsp[0];
    }
#line 1455 "parser.tab.c"
    break;

  case 32: /* other_stmt: return_decl  */
#line 218 "parser/parser.y"
                {
        yyval = yyvsp[0];
    }
#line 1463 "parser.tab.c"
    break;

  case 33: /* expression_decl: expression SEMICOLON  */
#line 224 "parser/parser.y"
                         {
        yyval = yyvsp[-1];
    }
#line 1471 "parser.tab.c"
    break;

  case 34: /* iteration_decl: WHILE LPAREN expression RPAREN statement  */
#line 231 "parser/parser.y"
                                             {
        yyval = createWhileStmt(stmtWhile, yyvsp[-2], yyvsp[0]);
    }
#line 1479 "parser.tab.c"
    break;

  case 35: /* return_decl: RETURN SEMICOLON  */
#line 237 "parser/parser.y"
                     {
        yyval = createStmtNode(stmtReturn);
    }
#line 1487 "parser.tab.c"
    break;

  case 36: /* return_decl: RETURN expression SEMICOLON  */
#line 240 "parser/parser.y"
                                  {
        yyval = createStmtNode(stmtReturn); yyval->child[0] = yyvsp[-1];
    }
#line 1495 "parser.tab.c"
    break;

  case 37: /* expression: var ASSIGN expression  */
#line 246 "parser/parser.y"
                          {
        yyval = createAssignStmt(stmtAttrib, yyvsp[-2], yyvsp[0]); yyval->op = ASSIGN;
    }
#line 1503 "parser.tab.c"
    break;

  case 38: /* expression: simple_expression  */
#line 249 "parser/parser.y"
                        {
        yyval = yyvsp[0];
    }
#line 1511 "parser.tab.c"
    break;

  case 39: /* var: ID  */
#line 255 "parser/parser.y"
       {
        yyval = createExpVar(expId);
        yyval->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, Integer);
    }
#line 1521 "parser.tab.c"
    break;

  case 40: /* var: ID LBRACK expression RBRACK  */
#line 260 "parser/parser.y"
                                  {
        yyval = createArrayExpVar(expId, yyvsp[-1]);
        yyval->line = yylineno;
        insertSymbolInTable(variableName, currentScope, ARRAY, yylineno, Integer);
    }
#line 1531 "parser.tab.c"
    break;

  case 41: /* simple_expression: sum_expression relational sum_expression  */
#line 268 "parser/parser.y"
                                             {
        yyval = createExpOp(expOp, yyvsp[-2], yyvsp[0]); yyval->op = yyvsp[-1]->op;
    }
#line 1539 "parser.tab.c"
    break;

  case 42: /* simple_expression: sum_expression  */
#line 271 "parser/parser.y"
                     {
        yyval = yyvsp[0];
    }
#line 1547 "parser.tab.c"
    break;

  case 43: /* relational: LT  */
#line 277 "parser/parser.y"
        { yyval = createExpNode(expId); yyval->op = LT;  yyval->line = yylineno; }
#line 1553 "parser.tab.c"
    break;

  case 44: /* relational: LTE  */
#line 278 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = LTE; yyval->line = yylineno; }
#line 1559 "parser.tab.c"
    break;

  case 45: /* relational: GT  */
#line 279 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = GT;  yyval->line = yylineno; }
#line 1565 "parser.tab.c"
    break;

  case 46: /* relational: GTE  */
#line 280 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = GTE; yyval->line = yylineno; }
#line 1571 "parser.tab.c"
    break;

  case 47: /* relational: EQ  */
#line 281 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = EQ;  yyval->line = yylineno; }
#line 1577 "parser.tab.c"
    break;

  case 48: /* relational: NEQ  */
#line 282 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = NEQ; yyval->line = yylineno; }
#line 1583 "parser.tab.c"
    break;

  case 49: /* sum_expression: sum_expression sum term  */
#line 286 "parser/parser.y"
                            {
        yyval = createExpOp(expOp, yyvsp[-2], yyvsp[0]); yyval->op = yyvsp[-1]->op;
    }
#line 1591 "parser.tab.c"
    break;

  case 50: /* sum_expression: term  */
#line 289 "parser/parser.y"
           {
        yyval = yyvsp[0];
    }
#line 1599 "parser.tab.c"
    break;

  case 51: /* sum: PLUS  */
#line 295 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = PLUS; }
#line 1605 "parser.tab.c"
    break;

  case 52: /* sum: MINUS  */
#line 296 "parser/parser.y"
            { yyval = createExpNode(expId); yyval->op = MINUS; }
#line 1611 "parser.tab.c"
    break;

  case 53: /* term: term mult factor  */
#line 300 "parser/parser.y"
                     {
        yyval = createExpOp(expOp, yyvsp[-2], yyvsp[0]); yyval->op = yyvsp[-1]->op;
    }
#line 1619 "parser.tab.c"
    break;

  case 54: /* term: factor  */
#line 303 "parser/parser.y"
             {
        yyval = yyvsp[0];
    }
#line 1627 "parser.tab.c"
    break;

  case 55: /* mult: TIMES  */
#line 309 "parser/parser.y"
          { yyval = createExpNode(expId); yyval->op = TIMES; }
#line 1633 "parser.tab.c"
    break;

  case 56: /* mult: DIV  */
#line 310 "parser/parser.y"
            { yyval = createExpNode(expId); yyval->op = DIV;   }
#line 1639 "parser.tab.c"
    break;

  case 57: /* factor: LPAREN expression RPAREN  */
#line 314 "parser/parser.y"
                             {
        yyval = yyvsp[-2];
    }
#line 1647 "parser.tab.c"
    break;

  case 58: /* factor: var  */
#line 317 "parser/parser.y"
          {
        yyval = yyvsp[0];
    }
#line 1655 "parser.tab.c"
    break;

  case 59: /* factor: call  */
#line 320 "parser/parser.y"
           {
        yyval = yyvsp[0];
    }
#line 1663 "parser.tab.c"
    break;

  case 60: /* factor: NUM  */
#line 323 "parser/parser.y"
          {
        yyval = createExpNum(expNum);
    }
#line 1671 "parser.tab.c"
    break;

  case 61: /* call: ID LPAREN args RPAREN  */
#line 329 "parser/parser.y"
                          {
        yyval = createExpCallNode(strdup(yyvsp[-3]->name), yyvsp[-1]);
        yyval->line = yylineno;
    }
#line 1680 "parser.tab.c"
    break;

  case 62: /* args: arg_list  */
#line 336 "parser/parser.y"
             {
        yyval = yyvsp[0];
    }
#line 1688 "parser.tab.c"
    break;

  case 63: /* args: %empty  */
#line 339 "parser/parser.y"
                  {
        yyval = NULL;
    }
#line 1696 "parser.tab.c"
    break;

  case 64: /* arg_list: arg_list COMMA expression  */
#line 345 "parser/parser.y"
                              {
        yyval = traversal(yyvsp[-2], yyvsp[0]); argsCount++;
    }
#line 1704 "parser.tab.c"
    break;

  case 65: /* arg_list: expression  */
#line 348 "parser/parser.y"
                 {
        yyval = yyvsp[0]; argsCount++;
    }
#line 1712 "parser.tab.c"
    break;

  case 66: /* arg_list: param  */
#line 351 "parser/parser.y"
            { 
        yyval = yyvsp[0]; argsCount++;
    }
#line 1720 "parser.tab.c"
    break;


#line 1724 "parser.tab.c"

      default: break;
    }
  /* User semantic actions sometimes alter yychar, and that requires
     that yytoken be updated with the new translation.  We take the
     approach of translating immediately before every use of yytoken.
     One alternative is translating here after every semantic action,
     but that translation would be missed if the semantic action invokes
     YYABORT, YYACCEPT, or YYERROR immediately after altering yychar or
     if it invokes YYBACKUP.  In the case of YYABORT or YYACCEPT, an
     incorrect destructor might then be invoked immediately.  In the
     case of YYERROR or YYBACKUP, subsequent parser actions might lead
     to an incorrect destructor call or verbose syntax error message
     before the lookahead is translated.  */
  YY_SYMBOL_PRINT ("-> $$ =", YY_CAST (yysymbol_kind_t, yyr1[yyn]), &yyval, &yyloc);

  YYPOPSTACK (yylen);
  yylen = 0;

  *++yyvsp = yyval;

  /* Now 'shift' the result of the reduction.  Determine what state
     that goes to, based on the state we popped back to and the rule
     number reduced by.  */
  {
    const int yylhs = yyr1[yyn] - YYNTOKENS;
    const int yyi = yypgoto[yylhs] + *yyssp;
    yystate = (0 <= yyi && yyi <= YYLAST && yycheck[yyi] == *yyssp
               ? yytable[yyi]
               : yydefgoto[yylhs]);
  }

  goto yynewstate;


/*--------------------------------------.
| yyerrlab -- here on detecting error.  |
`--------------------------------------*/
yyerrlab:
  /* Make sure we have latest lookahead translation.  See comments at
     user semantic actions for why this is necessary.  */
  yytoken = yychar == YYEMPTY ? YYSYMBOL_YYEMPTY : YYTRANSLATE (yychar);
  /* If not already recovering from an error, report this error.  */
  if (!yyerrstatus)
    {
      ++yynerrs;
      yyerror (YY_("syntax error"));
    }

  if (yyerrstatus == 3)
    {
      /* If just tried and failed to reuse lookahead token after an
         error, discard it.  */

      if (yychar <= YYEOF)
        {
          /* Return failure if at end of input.  */
          if (yychar == YYEOF)
            YYABORT;
        }
      else
        {
          yydestruct ("Error: discarding",
                      yytoken, &yylval);
          yychar = YYEMPTY;
        }
    }

  /* Else will try to reuse lookahead token after shifting the error
     token.  */
  goto yyerrlab1;


/*---------------------------------------------------.
| yyerrorlab -- error raised explicitly by YYERROR.  |
`---------------------------------------------------*/
yyerrorlab:
  /* Pacify compilers when the user code never invokes YYERROR and the
     label yyerrorlab therefore never appears in user code.  */
  if (0)
    YYERROR;
  ++yynerrs;

  /* Do not reclaim the symbols of the rule whose action triggered
     this YYERROR.  */
  YYPOPSTACK (yylen);
  yylen = 0;
  YY_STACK_PRINT (yyss, yyssp);
  yystate = *yyssp;
  goto yyerrlab1;


/*-------------------------------------------------------------.
| yyerrlab1 -- common code for both syntax error and YYERROR.  |
`-------------------------------------------------------------*/
yyerrlab1:
  yyerrstatus = 3;      /* Each real token shifted decrements this.  */

  /* Pop stack until we find a state that shifts the error token.  */
  for (;;)
    {
      yyn = yypact[yystate];
      if (!yypact_value_is_default (yyn))
        {
          yyn += YYSYMBOL_YYerror;
          if (0 <= yyn && yyn <= YYLAST && yycheck[yyn] == YYSYMBOL_YYerror)
            {
              yyn = yytable[yyn];
              if (0 < yyn)
                break;
            }
        }

      /* Pop the current state because it cannot handle the error token.  */
      if (yyssp == yyss)
        YYABORT;


      yydestruct ("Error: popping",
                  YY_ACCESSING_SYMBOL (yystate), yyvsp);
      YYPOPSTACK (1);
      yystate = *yyssp;
      YY_STACK_PRINT (yyss, yyssp);
    }

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END


  /* Shift the error token.  */
  YY_SYMBOL_PRINT ("Shifting", YY_ACCESSING_SYMBOL (yyn), yyvsp, yylsp);

  yystate = yyn;
  goto yynewstate;


/*-------------------------------------.
| yyacceptlab -- YYACCEPT comes here.  |
`-------------------------------------*/
yyacceptlab:
  yyresult = 0;
  goto yyreturnlab;


/*-----------------------------------.
| yyabortlab -- YYABORT comes here.  |
`-----------------------------------*/
yyabortlab:
  yyresult = 1;
  goto yyreturnlab;


/*-----------------------------------------------------------.
| yyexhaustedlab -- YYNOMEM (memory exhaustion) comes here.  |
`-----------------------------------------------------------*/
yyexhaustedlab:
  yyerror (YY_("memory exhausted"));
  yyresult = 2;
  goto yyreturnlab;


/*----------------------------------------------------------.
| yyreturnlab -- parsing is finished, clean up and return.  |
`----------------------------------------------------------*/
yyreturnlab:
  if (yychar != YYEMPTY)
    {
      /* Make sure we have latest lookahead translation.  See comments at
         user semantic actions for why this is necessary.  */
      yytoken = YYTRANSLATE (yychar);
      yydestruct ("Cleanup: discarding lookahead",
                  yytoken, &yylval);
    }
  /* Do not reclaim the symbols of the rule whose action triggered
     this YYABORT or YYACCEPT.  */
  YYPOPSTACK (yylen);
  YY_STACK_PRINT (yyss, yyssp);
  while (yyssp != yyss)
    {
      yydestruct ("Cleanup: popping",
                  YY_ACCESSING_SYMBOL (+*yyssp), yyvsp);
      YYPOPSTACK (1);
    }
#ifndef yyoverflow
  if (yyss != yyssa)
    YYSTACK_FREE (yyss);
#endif

  return yyresult;
}

#line 356 "parser/parser.y"



int yyerror(char *errorMsg) {
  printf("(!) ERRO SINTATICO: Linha: %d | Token: %s\n", yylineno, yytext);
  return 1;
}

treeNode *parse() {
    extern int yydebug;
    yydebug = 1; // ✅ Ativa impressão detalhada das reduções

    printf("Parsing...\n");
    parseResult = yyparse();
    if (parseResult == 0) {
        printf("Parsing completed successfully.\n");
    } else {
        printf("Parsing failed.\n");
    } 
    return syntax_tree; 
}

