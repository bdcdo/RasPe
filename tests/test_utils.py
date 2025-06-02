"""Testes para funções utilitárias."""
import pytest

from src.legiscraper.utils import expand

@pytest.mark.parametrize(
    "expr, esperado",
    [
        ("", []),
        ("a OU b", ["a", "b"]),
        ("a E b", ["a b"]),
        ("(a OU b) E (c OU d)", ["a c", "a d", "b c", "b d"]),
        ("((a OU b) E (c OU d)) OU e", ["a c", "a d", "b c", "b d", "e"]),
        ("  (  a  OU  b  )  E  c  ", ["a c", "b c"]),
        ("(a@test OU b.test) E (c#1 OU d-2)", ["a@test c#1", "a@test d-2", "b.test c#1", "b.test d-2"]),
        ("x", ["x"]),
    ],
)
def test_expand(expr: str, esperado: list[str]):
    """Expande expressão booleana em lista de termos."""
    resultado = expand(expr)
    assert sorted(resultado) == sorted(esperado)

@pytest.mark.parametrize(
    "expr",
    [
        "()",
        "a E (b OU c) E ()",
        "(a E (b OU c)",
    ],
)
def test_expand_errors(expr: str):
    """Levanta ValueError para expressões inválidas."""
    with pytest.raises(ValueError):
        expand(expr)
