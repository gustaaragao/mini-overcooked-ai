
# Especificação Formal do Problema

## 0. Simplificações
- Apenas um cozinheiro --> apenas um agente.
- Mapas baseados no Overcooked original, sem obstáculos dinâmicos.
- A fila de pedidos é sequencial (não há novos pedidos chegando durante a simulação).
- A panela (tile `K`) não pode ser removida do fogão — ela é fixa no mapa.

## 1. Ambiente

O ambiente é uma grade 2D representando uma cozinha. Cada célula pode conter (ou ser):

| Tile | Descrição |
|------|-----------|
| `.`  | Chão (passável) |
| `#`  | Parede (impasável) |
| `C`  | Balcão (armazenamento genérico) |
| `S`  | Fogão (cozimento simples — 1 ingrediente) |
| `T` / `B` | Tábua de Corte (preparação/corte) |
| `K`  | Panela no fogão |
| `D`  | Entrega |
| `G`  | Lixeira (Usada para descartar ingredientes em estado `BURNT`) |
| `E`  | Balcão com Extintor |
| `P`  | Balcão com Prato (sujo ou limpo) |
| `O`  | Fonte Infinita de Cebola |
| `V`  | Fonte Infinita de Tomate |
| `W`  | Pia (lavar pratos sujos) |

## 2. Estado

```
KitchenState(
    agent_pos       : (x, y)
    held_item       : Ingredient | Plate | Extinguisher | Pot | None
    layout          : grade estática (imutável)
    grid_objects    : ((pos, item), ...)  — itens sobre balcões
    active_orders   : (Order, ...)
    delivered_orders: (Order, ...)
    stations_state  : ((pos, StationState), ...)  — fogões, tábuas, pias, panelas
    time            : int
)
```

**Fila de Prioridade em `active_orders`:**
- A tupla `active_orders` funciona como uma **Priority Queue** (Fila de Prioridade).
- Em sua inicialização, os pedidos base são ordenados pelo menor tempo de limite (deadline), calculado por `(instant + duration)`. Dessa forma, o agente sempre focará em processar o pedido que está mais perto de expirar, visando maximizar a pontuação.

### Receitas (`Recipe`)

```
Recipe(
    name  : str
    steps : (RecipeStep, ...)
)

RecipeStep(
    ingredient    : str
    required_state: str   # RAW | CHOPPED | COOKED
    quantity      : int
)
```

Cada `Order` pode ter um campo opcional `recipe` que descreve a receita do pedido (`RecipeStep` descreve os ingredientes
e seu processamento).

### Panela (`Pot`)

```
Pot(
    ingredients: (str, ...)   # nomes dos ingredientes já adicionados
    state      : str          # EMPTY | FILLING | COOKING | READY
    progress   : int
)
```

A panela começa `EMPTY`. Cada `PutInPot` adiciona um ingrediente:
- Ao adicionar o **último** ingrediente necessário --> estado passa para `COOKING`.
- Após `POT_COOK_DURATION` ticks --> estado passa para `READY`.
- Em `READY`, o agente pode `ServeFromPot` --> o conteúdo vai para o prato.

## 3. Estado Inicial

Definido via arquivos JSON em `layouts/`. O campo `A` no layout define a posição inicial do agente. Tiles `P` e `E` geram objetos iniciais (`Plate(CLEAN)`, `Extinguisher`) nos balcões correspondentes. Tile `K` gera uma `StationState` com `Pot()` vazio.

## 4. Conjunto de Ações

| Ação | Descrição |
|------|-----------|
| `Move(x, y)` | Move o agente para uma célula `.` adjacente |
| `PickUp(item, state, x, y)` | Pega item de balcão, estação, fonte (`O`/`V`) ou do conteúdo da estação |
| `PutDown(item, state, x, y)` | Coloca item em balcão (`C`, `E`, `P`) ou estação (`S`, `T`, `B`, `W`) |
| `PutInPot(ingredient, x, y)` | Coloca ingrediente `CHOPPED` na panela `K` |
| `ServeFromPot(x, y)` | Transfere sopa pronta da panela para o prato limpo |
| `Chop(x, y)` | Processa ingrediente na tábua de corte (incrementa progresso) |
| `Wait(x, y)` | Aguarda cozimento (`S`/`K`) ou lavagem (`W`) |
| `Deliver(x, y)` | Entrega prato `WITH_FOOD` na estação `D`, validando receita |
| `Extinguish(x, y)` | Apaga fogo com extintor |

## 5. Modelo de Transição (`result(s, a)`)

- `Move` altera `agent_pos`.
- `PickUp`/`PutDown` alteram `held_item`, `grid_objects` ou `stations_state`.
- `PutInPot` adiciona ingrediente à `Pot.ingredients`; ao completar, muda para `COOKING`.
- `ServeFromPot` copia `Pot.ingredients` para `Plate.contents` e reseta a `Pot` para vazia.
- `Chop` incrementa progresso na `StationState`; ao atingir `CHOP_DURATION`, ingrediente --> `CHOPPED`.
- **Progresso global por tick** (aplicado em todo `result`):
  - Fogão (`S`): ingrediente `CHOPPED` --> progresso; ao atingir `COOK_DURATION` --> `COOKED`; ao atingir `BURN_LIMIT` --> `BURNT` + fogo.
  - Pia (`W`): prato `DIRTY` --> progresso; ao atingir `WASH_DURATION` --> `CLEAN`.
  - Panela (`K`): estado `COOKING` --> progresso; ao atingir `POT_COOK_DURATION` --> `READY`.
- `Deliver` valida `Plate.contents` contra `order.recipe` (ou `order.ingredients`); remove pedido de `active_orders` e gera prato `DIRTY`.

## 6. Teste de Objetivo (`goal_test`)

Verdadeiro quando `len(active_orders) == 0`.

## 7. Custo do Caminho (`path_cost`)

- Custo 1 para a maioria das ações.
- `Wait` tem custo 1.1 para incentivar o agente a realizar tarefas paralelas.

---

# Classificação do Ambiente

| Dimensão | Classificação | Justificativa |
|----------|---------------|---------------|
| Observabilidade | **Totalmente observável** | O agente recebe todo o `KitchenState` como percepção |
| Dinamismo | **Estático** | O ambiente só muda via ações do agente (ou progresso vinculado a elas) |
| Determinismo | **Determinístico** | Cada `(estado, ação)` produz exatamente um novo estado |
| Discretização | **Discreto** | Grade de células e estados finitos bem definidos |
| Número de agentes | **Agente único** | Um único agente AI opera na cozinha |

---

# Algoritmos de Busca e Heurística

## Algoritmos de Busca Utilizados

Os algoritmos de busca clássicos vistos no AIMA foram adaptados com limites de segurança em `agents/algorithms/search.py`:

- **A\* padrão do AIMA (`astar_search_with_limit`)**: Principal algoritmo utilizado. Para evitar laços infinitos e `TimeoutError` em níveis abertos com grande espaço de ramificação, foram adicionados limites de taxa de expansões e tempo.
- **Busca de Custo Uniforme (UCS)**: Implementada via **A\* parametrizado com heurística nula (`h(n) = 0`)**. Quando o agente precisa buscar um caminho para um sub-objetivo rápido (onde heurísticas globais são insuficientes ou causam mínimos locais), ele dispara a busca garantindo ser ótima, pois A* com admissibilidade trivial no limite se torna UCS.
- **Não utilizados (mas mapeados na codebase)**: `weighted_astar_search` e `greedy_best_first_search`. Destinados a fins comparativos; não foram usados na branch principal pois o BFS Guloso tende a colidir com as bancadas devido aos obstáculos do nível e Weighted A* sacrifica a optimalidade do caminho, o que seria penalizado pela contagem restrita de `max_steps`.

O programa do agente utiliza uma estratégia de **Decomposição por Sub-Objetivos**. Em vez de tentar planejar uma receita completa (espaço de busca intratável), o agente avalia as percepções e define lógicas geradoras de `funções goal_test` simples. Esses testes locais são despachados para o Uniform Cost Search (`astar_search(problem, lambda n: 0)`), mantendo o processamento restrito e viável. Apenas quando não há objetivo intermediário dedutível, ele passa à formulação macro heurística (`astar_search_with_limit(problem, self.heuristic)`).

## Heurística `h(n)`

A heurística é admissível e estima o custo mínimo restante usando **distância de Manhattan** + custos fixos de processamento:

### Prioridade (em ordem):
1. **Fogo**: custo = distância ao extintor + distância ao fogo.
2. **Prato `WITH_FOOD`**: custo = distância à entrega.
3. **Panela `READY`**: custo = distância ao prato limpo + distância à panela + distância à entrega.
4. **Panela `COOKING`**: custo = `POT_COOK_DURATION - progresso` + distância à entrega.
5. **Panela `FILLING`**: soma de (fonte --> tábua + `CHOP_DURATION` + tábua --> panela) para cada ingrediente faltando + `POT_COOK_DURATION` + distância à entrega.
6. **Sem panela (receita simples)**: custo estimado para o ciclo fonte --> tábua --> fogão --> prato --> entrega.

## Receitas Suportadas (Levels 1-1 a 1-6)

| Level | Tipo | Receitas |
|-------|------|---------|
| 1-1 | Sopa | Sopa de Cebola (3× cebola picada --> panela --> servir) |
| 1-2 | Sopa | Sopa de Cebola, Sopa de Tomate, Sopa Mista |
| 1-3 | Sopa | Mesmas do 1-2 (sem pia) |
| 1-4 | Hambúrguer | Simples, com Alface, com Tomate, Completo |
| 1-5 | Sopa | Sopa de Cebola e Sopa de Tomate (cozinha dividida) |
| 1-6 | Hambúrguer | Simples, com Tomate, Completo (cozinha maior) |

---