import re

def expand(expression: str) -> list[str]:
    """
    Transforms a complex search expression with logical operators into a list
    of all possible combinations that, when searched together, are equivalent 
    to the original expression.
    
    Handles nested parentheses, AND (E) and OR (OU) operators.
    
    Args:
        expression: A search expression string with operators "E" (AND) and "OU" (OR)
                   and parentheses for grouping.
    
    Returns:
        List of strings representing all possible term combinations
    
    Example:
        >>> expr = "(((doença OU doenças) E (rara OU raras)) OU ((medicamento) E (órfão)))"
        >>> expand(expr)
        ['doença rara', 'doença raras', 'doenças rara', 'doenças raras', 'medicamento órfão']
    """
    # Valida parênteses
    if '()' in expression:
        raise ValueError("Parênteses vazios não permitidos")
    if expression.count('(') != expression.count(')'):
        raise ValueError("Parênteses desequilibrados na expressão")
    # Normalize the expression: convert to standard symbols
    expr = expression.replace(" E ", " AND ").replace(" OU ", " OR ")
    
    def tokenize(expression: str) -> list[str]:
        """Convert expression to a list of tokens (terms, operators, parentheses)"""
        # First, insert spaces around parentheses to make them separate tokens
        expr_with_spaces = re.sub(r'([()])', r' \1 ', expression)
        # Split by whitespace and filter out empty strings
        tokens = [token for token in expr_with_spaces.split() if token]
        return tokens
    
    def parse_expression(tokens: list[str]) -> list[str]:
        """Parse expression using a recursive descent parser"""
        def parse_or() -> list[str]:
            left = parse_and()
            while i[0] < len(tokens) and tokens[i[0]] == "OR":
                i[0] += 1  # Consume "OR"
                right = parse_and()
                left = left + right  # Union of sets for OR operation
            return left
        
        def parse_and() -> list[str]:
            left = parse_primary()
            while i[0] < len(tokens) and tokens[i[0]] == "AND":
                i[0] += 1  # Consume "AND"
                right = parse_primary()
                # Cartesian product for AND operation
                product_result = []
                for l in left:
                    for r in right:
                        product_result.append(f"{l} {r}")
                left = product_result
            return left
        
        def parse_primary() -> list[str]:
            if i[0] >= len(tokens):
                return []
            
            if tokens[i[0]] == "(":
                i[0] += 1  # Consume "("
                result = parse_or()
                if i[0] < len(tokens) and tokens[i[0]] == ")":
                    i[0] += 1  # Consume ")"
                return result
            else:
                # It's a term (a word)
                term = tokens[i[0]]
                i[0] += 1
                return [term]
        
        # Use a mutable index
        i = [0]
        return parse_or()
    
    # Clean up the tokens
    tokens = tokenize(expr)
    
    # Parse the expression
    result = parse_expression(tokens)
    
    # Remove duplicates and sort
    return sorted(list(set(result)))