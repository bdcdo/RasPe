import re
import os
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import polars as pl

# Import functions from utils.py
from buscraper.utils import expand, remove_duplicates, create_download_dir


class TestExpand:
    """Testes para a função expand() que converte expressões de busca complexas."""

    def test_simple_or_expression(self):
        """Testa expressão simples com operador OU."""
        expr = "termo1 OU termo2"
        result = expand(expr)
        assert result == ["termo1", "termo2"]

    def test_simple_and_expression(self):
        """Testa expressão simples com operador E."""
        expr = "termo1 E termo2"
        result = expand(expr)
        assert result == ["termo1 termo2"]

    def test_complex_expression(self):
        """Testa expressão complexa com operadores aninhados."""
        expr = "(doença OU doenças) E (rara OU raras)"
        result = expand(expr)
        assert sorted(result) == sorted([
            "doença rara", 
            "doença raras", 
            "doenças rara", 
            "doenças raras"
        ])

    def test_nested_expression(self):
        """Testa expressão com múltiplos níveis de aninhamento."""
        expr = "((termo1 OU termo2) E termo3) OU (termo4 E termo5)"
        result = expand(expr)
        assert sorted(result) == sorted([
            "termo1 termo3",
            "termo2 termo3",
            "termo4 termo5"
        ])

    def test_example_from_docstring(self):
        """Testa o exemplo do docstring."""
        expr = "(((doença OU doenças) E (rara OU raras)) OU ((medicamento) E (órfão)))"
        result = expand(expr)
        expected = ['doença rara', 'doença raras', 'doenças rara', 'doenças raras', 'medicamento órfão']
        assert sorted(result) == sorted(expected)
        
    def test_complex_multiline_expression(self):
        """Testa expressão complexa com múltiplas linhas e termos."""
        expr = """
        (
        ((doença OU síndrome OU patologia) E (rara OU ultrarrara)) OU
        ((doenças OU síndromes OU patologias) E ((raras OU ultrarraras))) OU 
        (medicamento E órfão) OU
        (medicamentos E órfãos) OU
        (terapia E órfã) OU
        (terapias E órfãs)
        )
        """
        result = expand(expr)
        
        expected = [
            # Combinações de singular + singular
            'doença rara', 'doença ultrarrara', 
            'síndrome rara', 'síndrome ultrarrara', 
            'patologia rara', 'patologia ultrarrara',
            
            # Combinações de plural + plural
            'doenças raras', 'doenças ultrarraras',
            'síndromes raras', 'síndromes ultrarraras',
            'patologias raras', 'patologias ultrarraras',
            
            # Outras combinações
            'medicamento órfão',
            'medicamentos órfãos',
            'terapia órfã',
            'terapias órfãs'
        ]
        
        assert sorted(result) == sorted(expected)

    def test_unbalanced_parentheses(self):
        """Testa se a função detecta parênteses desequilibrados."""
        expr = "(termo1 E termo2"
        with pytest.raises(ValueError, match="Parênteses desequilibrados"):
            expand(expr)

    def test_empty_parentheses(self):
        """Testa se a função detecta parênteses vazios."""
        expr = "termo1 E () E termo2"
        with pytest.raises(ValueError, match="Parênteses vazios"):
            expand(expr)


class TestRemoveDuplicates:
    """Testes para a função remove_duplicates() que elimina duplicatas em DataFrames."""

    def test_no_termo_busca_column(self):
        """Testa quando não existe a coluna termo_busca."""
        df = pl.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = remove_duplicates(df, [])
        
        # Deve retornar o DataFrame original
        assert result.equals(df)

    def test_no_duplicates(self):
        """Testa quando não existem duplicatas."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "valor": ["a", "b", "c"],
            "termo_busca": ["termo1", "termo2", "termo3"]
        })
        result = remove_duplicates(df, [])
        
        # Deve retornar um DataFrame similar ao original
        assert result.height == df.height

    def test_with_duplicates(self):
        """Testa quando existem duplicatas para serem removidas."""
        df = pl.DataFrame({
            "id": [1, 1, 2],
            "valor": ["a", "a", "b"],
            "termo_busca": ["termo1", "termo2", "termo3"],
            "col_exclude": ["ex1", "ex2", "ex3"]  # Coluna a ser excluída da deduplicação
        })
        
        result = remove_duplicates(df, ["col_exclude"])
        
        # Deve reduzir para 2 linhas (removendo duplicatas)
        assert result.height == 2
        
        # Verifica se os termos de busca foram agregados
        first_row = result.filter(pl.col("id") == 1).select("termo_busca").item()
        assert "termo1" in first_row and "termo2" in first_row

    def test_no_dedup_cols(self):
        """Testa quando todas as colunas são excluídas da deduplicação."""
        df = pl.DataFrame({
            "termo_busca": ["t1", "t2"],
            "col1": ["a", "b"]
        })
        
        result = remove_duplicates(df, ["col1"])
        
        # Como todas as colunas são excluídas, deve retornar o DataFrame original
        assert result.equals(df)


class TestCreateDownloadDir:
    """Testes para a função create_download_dir que cria diretórios para downloads."""

    @patch("os.makedirs")
    @patch("buscraper.utils.datetime")
    def test_create_directory(self, mock_datetime, mock_makedirs):
        """Testa a criação do diretório de download."""
        # Configura o mock para retornar uma data fixa
        mock_datetime.now.return_value.strftime.return_value = "20250606123456"
        
        # Parâmetros para a função
        download_path = "/tmp/downloads"
        nome_buscador = "test_buscador"
        
        # Chama a função
        result = create_download_dir(download_path, nome_buscador)
        
        # Verifica o caminho criado
        expected_path = "/tmp/downloads/test_buscador/20250606123456"
        assert result == expected_path
        
        # Verifica se o diretório foi criado
        mock_makedirs.assert_called_once_with(expected_path)
