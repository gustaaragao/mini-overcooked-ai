# GEMINI.md - Contexto do Projeto

Este arquivo fornece o contexto necessário para o Gemini CLI atuar no projeto **mini-overcooked-ai**.

## Visão Geral do Projeto

O **mini-overcooked-ai** é um projeto acadêmico para a disciplina de Inteligência Artificial. O objetivo é implementar um agente inteligente baseado em busca que solucione uma versão simplificada do jogo "Overcooked".

O projeto utiliza a biblioteca [aima-python](https://github.com/aimacode/aima-python) como base para a implementação dos algoritmos de busca e da arquitetura Ambiente-Agente.

### Principais Objetivos:
- Modelagem formal do problema (Estados, Ações, Transição, Objetivo, Custo).
- Implementação seguindo a arquitetura **Ambiente - Agente - Programa de Agente**.
- Uso de algoritmos de busca (BFS, A*, Greedy, etc.) para tomada de decisão.
- Desenvolvimento de heurísticas admissíveis e consistentes.
- Visualização do ambiente via terminal (`render()`).

## Tecnologias e Dependências

- **Linguagem:** Python
- **Biblioteca Base:** `aima-python`
- **Testes:** `pytest` (planejado)

## Estrutura do Projeto (Planejada)

De acordo com as especificações do projeto, a estrutura deve seguir:

- `/env`: Implementação do ambiente (mundo, percepções, execução de ações).
- `/agents`: Programas de agente (lógica de decisão e busca).
- `/problems`: Definições formais do problema (subclasses de `aima.search.Problem`).
- `/tests`: Testes automatizados.
- `main.py`: Ponto de entrada para execução e demonstração.

## Convenções de Desenvolvimento

- **Arquitetura:** Seguir estritamente o modelo do AIMA (Russell & Norvig).
- **Herança:** Estender classes base do `aima-python` (`Problem`, `Environment`, `Agent`).
- **Busca:** Algoritmos de busca devem residir no "Programa de Agente", gerando planos a partir de percepções.
- **Visualização:** O método `render()` no ambiente deve fornecer uma visão clara do estado atual no terminal.

## Arquivos Chave

- `README.md`: Documentação geral (em construção).
- `docs/Projeto de Implementação – Agentes Inteligentes e Busca.md`: Especificação detalhada do trabalho.
- `IDEIAS.md`: Brainstorming inicial sobre as mecânicas de jogo (ingredientes, pratos, pedidos, mapa).

## Comandos Úteis (TODO)

- **Instalação de Dependências:** `pip install -r requirements.txt` (ainda não criado)
- **Execução:** `python main.py`
- **Testes:** `pytest`
