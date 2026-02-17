
# Especificação Formal do Problema

## 0. Simplificações
- Não podemos remover a panela do fogão. (Posso remover essa simplificação)
- Os mapas são iguais ao do jogo original, exceto por dois pontos:
    - Apenas um cozinheiro --> Apenas um agente
    - Sem obstáculos
- A fila de pedidos é simplificada.

## 1. Ambiente
O ambiente é uma grade 2D representando uma cozinha. Cada célula pode conter (ou ser):

- `.` : Chão (passável)
- `#` : Parede (impasável)
- `C` : Balcão (armazenamento)
- `S` : Fogão (cozimento)
- `T` ou `B` : Tábua de Corte (preparação/corte)
- `D` : Entrega
- `G` : Lixeira
- `E` : Balcão com Extintor
- `P` : Balcão com Prato (Sujo ou Limpo)
- `O` : Fonte Infinita de Cebola (Onion Source)
- `W` : Pia (Sink) para lavar pratos sujos

## 2. Estado Inicial
Definido via arquivos JSON em `layouts/`, contendo a posição inicial do agente, o layout do grid, e a lista de pedidos (`active_orders`).

## 3. Conjunto de Ações
- `Move(x, y)`: Move o agente para uma célula adjacente livre.
- `PickUp(item, state, x, y)`: Pega um item de um balcão ou estação adjacente. Pode ser usado para pegar um ingrediente diretamente em um prato limpo que o agente esteja segurando.
- `PutDown(item, state, x, y)`: Coloca o item segurado em um balcão ou estação adjacente. Se colocado em um prato no balcão, inicia a montagem.
- `Chop(x, y)`: Processa um ingrediente em uma tábua de corte ('T' ou 'B').
- `Wait(x, y)`: Aguarda o progresso de cozimento em um fogão ou lavagem na pia.
- `Deliver(x, y)`: Entrega o prato finalizado.
- `Extinguish(x, y)`: Apaga o fogo em uma estação usando um extintor.

## 4. Modelo de Transição (result(s, a))
- Ações de movimento mudam a posição do agente.
- `PickUp`/`PutDown` alteram `held_item` e `grid_objects` ou `stations_state`.
- `Chop` incrementa o progresso na estação 'T' ou 'B' até que o ingrediente mude para `chopped`.
- O tempo progride globalmente para fogões ('S') e pias ('W').
- Fogões incrementam o progresso se houver um ingrediente `chopped`, podendo chegar a `cooked` e, se exceder o limite (`BURN_LIMIT`), entrar em estado `is_on_fire`.
- Pias incrementam o progresso se houver um prato `dirty`, mudando-o para `clean` após o tempo necessário.
- `Deliver` remove o prato com comida, completa o pedido e gera um prato sujo em um balcão de retorno ou disponível.

## 5. Teste de objetivo (goal_test)
Verdadeiro quando `active_orders` está vazio.

## 6. Custo do caminho (path_cost)
- Custo unitário para a maioria das ações.
- Ações de `Wait` possuem custo levemente superior (1.1) para incentivar o agente a realizar outras tarefas produtivas enquanto espera.

# Classificação do Ambiente
- **Determinístico**: As ações resultam em estados previsíveis.
- **Totalmente Observável**: O agente conhece todo o grid e o estado de todas as estações.
- **Estático**: O ambiente só muda através das ações do agente (ou do progresso de tempo vinculado às ações).
- **Discreto**: Grade de células e estados bem definidos.
- **Agente Único**: Apenas um agente AI opera na cozinha.

# Algoritmos de Busca e Heurística
- **A* Search**: Utilizado para encontrar o plano ótimo.

## Heurísticas
A heurística $h(n)$ combina distância de Manhattan com custo de processamento e bônus de progresso. A prioridade é definida da seguinte forma:

1.  **Fogo**: Se houver fogo, a prioridade máxima é buscar o extintor (se não estiver segurando um) e apagar as chamas.
2.  **Entrega**: Se o agente estiver segurando um prato com comida (`WITH_FOOD`) ou um prato limpo com ingredientes cozidos/cortados, ele prioriza a entrega ou a finalização do prato.
3.  **Processamento**: Se não houver emergências, o agente busca ingredientes, leva para as tábuas de corte, depois para os fogões e, finalmente, para os pratos.

A heurística $h(n)$ é calculada como:
$h(n) = \min(\text{distância\_Manhattan\_alvos}) + \text{custo\_extra\_processamento} + (60 - \text{bonus\_progresso})$

- `bonus_progresso` aumenta conforme o agente avança na cadeia de produção (ex: segurar prato com comida dá um bônus maior que segurar cebola crua).
- `custo_extra_processamento` reflete o tempo fixo necessário em estações (ex: `CHOP_DURATION`, `COOK_DURATION`).

A heurística busca ser informativa para guiar o A* eficientemente, priorizando estados que levam à conclusão dos pedidos.
