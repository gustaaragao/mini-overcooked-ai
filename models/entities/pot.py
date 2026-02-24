from typing import NamedTuple, Tuple


class Pot(NamedTuple):
    """Panela que aceita múltiplos ingredientes picados para fazer sopas.

    Estado:
        - EMPTY:   nenhum ingrediente ainda
        - FILLING: ingredientes sendo adicionados (ainda não atingiu o total)
        - COOKING: atingiu o total de ingredientes; cozinhando
        - READY:   sopa pronta para servir
    """
    ingredients: Tuple[str, ...] = ()
    state: str = "EMPTY"   # EMPTY, FILLING, COOKING, READY
    progress: int = 0
