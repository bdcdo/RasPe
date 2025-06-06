import re
import polars as pl

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

def remove_duplicates(df: pl.DataFrame, exclude_cols: list[str]) -> pl.DataFrame:
    """Remove duplicatas do DataFrame e agrupa os termos de busca.
    
    Este método remove linhas duplicadas no DataFrame, excluindo as colunas
    especificadas em exclude_cols e a coluna 'termo_busca'. Para registros
    que são duplicados, os valores da coluna 'termo_busca' são agrupados em uma lista.
    
    Args:
        df: DataFrame a ser processado.
        exclude_cols: Lista adicional de colunas para excluir ao detectar duplicatas.
        
    Returns:
        pl.DataFrame: DataFrame sem duplicatas e com termos de busca agrupados.
    """
    self.logger.debug(f"Removendo duplicatas. Colunas excluídas: {self.exclude_cols_from_dedup}")
    
    # Verificar se há coluna termo_busca
    if "termo_busca" not in df.columns:
        self.logger.debug("Coluna termo_busca não encontrada, retornando DataFrame original")
        return df
    
    # Preparar lista de colunas para deduplicação
    all_exclude_cols = ["termo_busca", *self.exclude_cols_from_dedup]
    dedup_cols = [col for col in df.columns if col not in all_exclude_cols]
    
    if not dedup_cols:
        self.logger.debug("Nenhuma coluna disponível para deduplicação")
        return df
    
    # Verificar se há duplicatas
    dedup_counts = df.group_by(dedup_cols).count()
    n_duplicates = dedup_counts.filter(pl.col("count") > 1).height
    
    if n_duplicates == 0:
        self.logger.debug("Nenhuma duplicata encontrada")
        return df
    
    self.logger.info(f"Encontradas {n_duplicates} entradas duplicadas")
    
    # Agrupar termos de busca para duplicatas
    agregado = df.group_by(dedup_cols).agg(
        pl.col("termo_busca").alias("termo_busca_list"),
        *[pl.col(col).first().alias(col) for col in self.exclude_cols_from_dedup]
    )
    
    # Converter a coluna de termos para o formato apropriado
    result = agregado.with_columns([
        pl.when(pl.col("termo_busca_list").list.len() > 1)
            .then(pl.col("termo_busca_list").list.join(", "))
            .otherwise(pl.col("termo_busca_list").list.first())
            .alias("termo_busca")
    ]).drop("termo_busca_list")
    
    self.logger.info(f"Remoção de duplicatas concluída. Linhas reduzidas de {df.height} para {result.height}")
    return result

def _create_download_dir(self) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    path = f"{self.download_path}/{self.nome_buscador}/{timestamp}"
    os.makedirs(path)
    
    self.logger.debug(f"Criado diretório de download em {path}")
    
    return path