"""Funções utilitárias relacionadas a receitas e validação de pedidos.

Centraliza a lógica de comparação de ingredientes para que possa ser usada
tanto pelo `KitchenProblem` (actions/result/heurística) quanto pelo
`KitchenAgent` (seleção de sub-objetivos).
"""

from collections import Counter
from typing import List

from models.entities import Order, Plate, Pot
from models.states import KitchenState


def order_satisfied_by_plate(plate: Plate, order: Order) -> bool:
    """Verifica se os conteúdos do prato satisfazem o pedido ativo.

    Se o pedido tiver uma `Recipe` associada, valida via
    `recipe.required_ingredients()` — que expande cada `RecipeStep`
    respeitando a quantidade (`quantity`).
    Caso contrário, compara `plate.contents` diretamente com
    `order.ingredients`.

    Exemplo (Sopa de Cebola):
        recipe exige Counter({"Onion": 3})
        plate.contents == ("Onion", "Onion", "Onion")  → True
    """
    if order.recipe:
        required = Counter(name for name, _ in order.recipe.required_ingredients())
    else:
        required = Counter(order.ingredients)
    return Counter(plate.contents) == required


def pot_required_ingredients(order: Order) -> List[str]:
    """Retorna lista plana de ingredientes necessários para a receita, com repetições.

    Expande cada `RecipeStep` de acordo com seu `quantity`. Se não houver
    receita, usa diretamente `order.ingredients`.

    Exemplo:
        RecipeStep("Onion", "CHOPPED", quantity=3) → ["Onion", "Onion", "Onion"]

    Usada pela heurística (estimar ingredientes faltando) e pelo agente
    (identificar o próximo ingrediente a buscar).
    """
    if order.recipe:
        return [name for name, _ in order.recipe.required_ingredients()]
    return list(order.ingredients)


def pot_needed_ingredients(pot: Pot, state: KitchenState) -> List[str]:
    """Retorna a lista de ingredientes que ainda faltam ser adicionados à panela.

    Subtrai os ingredientes já presentes em `pot.ingredients` da lista
    exigida pela receita do pedido ativo. Usada em `actions()` para
    decidir se o agente pode executar `PutInPot`.
    """
    if not state.active_orders:
        return []
    order = state.active_orders[0]
    needed = list(pot_required_ingredients(order))
    for ing in pot.ingredients:
        if ing in needed:
            needed.remove(ing)
    return needed


def pot_needed_count_for_order(active_orders, current_ingredients) -> int:
    """Retorna o número de ingredientes ainda faltando na panela (inteiro).

    Usado em `result()` após um `PutInPot` para decidir se a panela
    passa para `COOKING` (retorna 0) ou permanece em `FILLING`.
    """
    if not active_orders:
        return 0
    order = active_orders[0]
    needed = list(pot_required_ingredients(order))
    for ing in current_ingredients:
        if ing in needed:
            needed.remove(ing)
    return len(needed)
