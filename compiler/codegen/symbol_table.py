

class Type:
    """A base class to represent types in our language."""
    pass

class IntegerType(Type):
    """Represents the simple 'int' type."""
    def __init__(self):
        self.size = 1 # Each integer occupies 1 memory word.

    def __repr__(self):
        return "INT"

class ArrayType(Type):
    """Represents an array type, like 'int vec[10]'."""
    def __init__(self, base_type, num_elements):
        self.base_type = base_type
        self.num_elements = num_elements
        # The total size of the array is the size of its base type
        # multiplied by the number of elements.
        self.size = base_type.size * num_elements

    def __repr__(self):
        return f"ARRAY(size={self.num_elements}, base_type={self.base_type})"

class Symbol:
    """
    Represents a single entry in our symbol table (e.g., a variable).
    This acts as a "dossier" for each identifier.
    """
    def __init__(self, name, symbol_type, scope, address=None):
        self.name = name
        self.type = symbol_type
        self.scope = scope # E.g., "global" or a function name like "main"
        self.address = address # The base memory address allocated for this symbol

    def __repr__(self):
        return f"<Symbol(name='{self.name}', type={self.type}, scope='{self.scope}', addr={self.address})>"

class SymbolTable:
    """
    The main data structure that manages all symbols in the program.
    It will hold all the Symbol objects we create.
    """
    def __init__(self):
        self.symbols = {} # A simple dictionary to store symbols by name

    def add_symbol(self, symbol):
        """Adds a new symbol to the table."""
        print(f"[SymbolTable] Adding symbol: {symbol}")
        self.symbols[symbol.name] = symbol

    def get_symbol(self, name):
        """Retrieves a symbol by its name."""
        return self.symbols.get(name)
