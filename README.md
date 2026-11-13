# prompt-diff

Comparativo de técnicas de prompt engineering para classificar mensagens de suporte em cinco categorias. O experimento usa dataset congelado, temperatura 0, critérios declarados antes das rodadas de validação e avaliação automatizada com teste estatístico pareado.

## O que o projeto mede

- **Técnicas comparadas:** v1 (instrução direta), v2 (few-shot) e v3 (raciocínio guiado), com uma v4 derivada da v3 e avaliada no conjunto de validação.
- **Métricas:** acerto por caso e por execução, erros por categoria, falhas de formato, tokens de entrada e saída e latência (mediana).
- **Controles:** mesmo modelo, temperatura 0 e limite de tokens para todas as versões.

## Resultados

Detalhes completos, incluindo a tabela de custo e a discussão de cada caso, estão em [comparison.md](comparison.md). O histórico de decisões está em [prompts/changelog.md](prompts/changelog.md).

### Conjunto de desenvolvimento (20 casos, 1 execução por caso)

| Métrica | v1 | v2 | v3 |
| --- | --- | --- | --- |
| Acerto | 16/20 (80%) | 17/20 (85%) | 18/20 (90%) |
| Claros | 13/15 | 13/15 | 14/15 |
| Ambíguos | 3/5 | 4/5 | 4/5 |

A v3 teve o melhor resultado observado, mas a diferença não é estatisticamente significativa. Entre v1 e v3, há dois casos discordantes, ambos favoráveis à v3, e o McNemar exato dá p = 0,5.

### Conjunto de validação (30 casos, 5 execuções por caso)

| Métrica | v3 | v4 |
| --- | --- | --- |
| Casos aprovados (maioria 3 de 5) | 25/30 (83%) | 26/30 (87%) |
| Execuções corretas | 124/150 | 132/150 |
| Claros | 15/15 | 15/15 |
| Ambíguos | 10/15 | 11/15 |
| Falhas de formato | 0 | 0 |

**Conclusão:** não há evidência de melhora da v4 sobre a v3 neste conjunto. Houve um caso favorável à v4 e nenhum contrário (p = 1,0). Os critérios declarados antes da rodada não foram cumpridos.

**Limitação:** o conjunto de validação não é cego. Os casos foram escritos depois de observar os erros do conjunto de desenvolvimento.

## Aprendizados

- Com 20 casos e uma execução, diferenças de um ou dois casos não permitem afirmar que uma técnica é melhor.
- Declarar o critério antes da rodada evita escolher a técnica olhando o resultado.
- Repetir a mesma chamada em temperatura 0 mostrou quase nenhuma variação, então a repetição serve mais para confirmar estabilidade do que para medir variância.
- Um conjunto de validação só vale como teste quando é escrito antes de qualquer ajuste de prompt.

## Estrutura

```text
prompt-diff/
├── config.py              # fonte única: modelo, temperatura, limite de tokens, caminhos e categorias
├── prompts/
│   ├── v1.md, v2.md, v3.md, v4.md
│   └── changelog.md       # decisões, critérios pré-registrados e resultados
├── evals/
│   ├── cases.csv          # desenvolvimento: 20 casos
│   ├── validation_cases.csv  # validação: 30 casos
│   ├── results_*.csv      # resultados do desenvolvimento
│   └── validation/        # resultados da validação
├── src/
│   ├── call_model.py      # chamada à API
│   ├── generate_cases.py  # geração do conjunto de desenvolvimento
│   ├── run_version.py     # executa uma versão sobre um conjunto
│   └── evaluate.py        # pontua, aplica critérios e calcula McNemar
├── comparison.md          # relatório comparativo
└── requirements.txt
```

## Pré-requisitos

- Python 3.15 (testado na 3.15.2)
- Git
- Chave de API do Google AI Studio

## Instalação

```cmd
py -3.15 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux ou macOS, ative o ambiente com `source .venv/bin/activate`.

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha `GOOGLE_API_KEY` com sua chave.
3. O `.env` não vai para o Git (regra no `.gitignore`).

## Como reproduzir

Conjunto de desenvolvimento (20 casos, 1 execução por caso):

```cmd
python src/generate_cases.py
python src/run_version.py v1
python src/run_version.py v2
python src/run_version.py v3
python src/evaluate.py
```

Conjunto de validação (30 casos, 5 execuções por caso):

```cmd
python src/run_version.py v3 --set validation
python src/run_version.py v4 --set validation
python src/evaluate.py --set validation --baseline v3 --target v4
```

Cada execução de validação gera 150 chamadas. Com o intervalo de 15 s entre chamadas, uma rodada leva cerca de 38 minutos. O limite gratuito do modelo usado é de 500 chamadas por dia.

Rodadas de validação são de uma vez só. O `run_version.py` recusa sobrescrever um resultado existente, a menos que se use `--force`. Use `--force` apenas para descartar uma rodada interrompida antes de qualquer avaliação, e registre isso no changelog.

`generate_cases.py` gera apenas o conjunto de desenvolvimento. O conjunto de validação foi escrito manualmente e não deve ser regenerado.

## Limitações conhecidas

- **Sem timeout nas chamadas à API.** Uma queda de rede pode deixar o processo travado, e o Ctrl+C pode não responder no Windows. A correção está planejada em commit separado.
- **Gabaritos em discussão:** V17 e V29 no conjunto de validação, e os casos 09 e 19 no desenvolvimento. Qualquer revisão deve ser registrada no changelog como entrada nova, sem substituir o resultado original.
- **Modelo único:** todos os resultados são de `gemini-3.5-flash-lite`, com temperatura 0. Outros modelos podem se comportar de forma diferente.

## Licença

MIT. Veja [LICENSE](LICENSE).