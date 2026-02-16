
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
- `C` : Balcão (armazenamento e fonte de ingredientes)
- `S` : Fogão (cozimento)
- `T` : Tábua de Corte (preparação)
- `D` : Entrega
- `G` : Lixeira
- `E` : Balcão com Extintor
- `P` : Balcão com Prato (Sujo ou Limpo) --> TODO: Criar um model (Plate) para o prato

## 2. Estado Inicial
Definido via arquivos JSON em `layouts/`, contendo a posição inicial do agente, o layout do grid, e a lista de pedidos (`active_orders`).

## 3. Conjunto de Ações
- `Move(x, y)`: Move o agente para uma célula adjacente livre.
- `PickUp(item, state, x, y)`: Pega um item de um balcão ou estação adjacente.
- `PutDown(item, state, x, y)`: Coloca o item segurado em um balcão ou estação adjacente.
- `Chop(x, y)`: Processa um ingrediente em uma tábua de corte.
- `Wait(x, y)`: Aguarda o progresso de cozimento em um fogão.
- `Deliver(x, y)`: Entrega o prato finalizado.
- `Extinguish(x, y)`: Apaga o fogo em uma estação usando um extintor.

## 4. Modelo de Transição (result(s, a))
- Ações de movimento mudam a posição do agente.
- `PickUp`/`PutDown` alteram `held_item` e `grid_objects` ou `stations_state`.
- `Chop` incrementa o progresso na estação 'T' até que o ingrediente mude para `chopped`.
- O tempo progride globalmente para fogões ('S'), incrementando o progresso se houver um ingrediente `chopped`.
- Se o cozimento exceder o limite (`BURN_LIMIT`), a estação entra em estado `is_on_fire`.

## 5. Teste de objetivo (goal_test)
Verdadeiro quando `active_orders` está vazio.

## 6. Custo do caminho (path_cost)
- Custo unitário para a maioria das ações.
- Ações de `Wait` possuem custo levemente superior (1.1) para incentivar o agente a realizar outras tarefas produtivas enquanto espera.

# Classificação do Ambiente
- **Determinístico**: As ações resultam em estados previsíveis (mesmo o tempo de queima é fixo).
- **Totalmente Observável**: O agente conhece todo o grid e o estado de todas as estações.
- **Estático**: O ambiente só muda através das ações do agente (ou do progresso de tempo vinculado às ações).
- **Discreto**: Grade de células e estados bem definidos.
- **Agente Único**: Apenas um agente AI opera na cozinha.

# Algoritmos de Busca e Heurística
- **A* Search**: Utilizado para encontrar o plano ótimo.

## Heurísticas
A heurística $h(n)$ combina distância de Manhattan com custo de processamento:
- Se segurando nada: Distância ao ingrediente mais próximo + tempo de processamento futuro.
- Se segurando algo: Distância à próxima estação de processamento (Tábua -> Fogão -> Entrega) + tempo de processamento restante.
- **Fogo**: Se houver fogo, a prioridade máxima é buscar o extintor e apagar as chamas.

A heurística é admissível pois nunca sobrestima o custo real (sempre considera o caminho direto e o tempo mínimo de processamento).
