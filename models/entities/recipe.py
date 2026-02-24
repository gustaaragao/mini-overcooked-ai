from typing import NamedTuple, Tuple


class RecipeStep(NamedTuple):
    """Uma etapa de uma receita: define qual ingrediente, em qual estado e em qual quantidade."""
    ingredient: str
    required_state: str  # RAW, CHOPPED ou COOKED
    quantity: int = 1


class Recipe(NamedTuple):
    """Receita nomeada composta de uma ou mais etapas (RecipeStep).

    Receitas simples têm apenas uma etapa (ex: cebola frita).
    Receitas complexas têm múltiplas etapas (ex: Sopa de Cebola = 3x COOKED).
    """
    name: str
    steps: Tuple[RecipeStep, ...]

    def required_ingredients(self) -> Tuple[Tuple[str, str], ...]:
        """Retorna uma lista plana de (nome, estado_requerido), repetida pela quantidade.

        Usado para verificar se um prato já satisfaz os requisitos da receita.
        """
        result = []
        for step in self.steps:
            for _ in range(step.quantity):
                result.append((step.ingredient, step.required_state))
        return tuple(result)

    def total_ingredients(self) -> int:
        """Total de unidades de ingredientes necessárias para completar a receita."""
        return sum(step.quantity for step in self.steps)
