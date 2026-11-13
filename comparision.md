# Comparativo de versões — classificador de mensagens de suporte

Modelo: `gemini-3.5-flash-lite` · Temperatura: 0 · Sistema: `system instruction` com o prompt da versão

## 1. Conjunto de desenvolvimento (dev)

Dataset: `evals/cases.csv`, 20 casos (15 claros, 5 ambíguos), 1 execução por caso.
Rodadas de 11 e 12/11/2026, sequenciais, na mesma sessão.

| Métrica | v1 | v2 | v3 |
| --- | --- | --- | --- |
| Acerto | 16/20 (80%) | 17/20 (85%) | 18/20 (90%) |
| Claros | 13/15 | 13/15 | 14/15 |
| Ambíguos | 3/5 | 4/5 | 4/5 |
| Falhas de formato | 0 | 0 | 0 |
| Latência mediana (ms) | 6.911 | 8.432 | 6.663 |
| Entrada mediana (tokens) | 314 | 507 | 496 |
| Saída mediana (tokens) | 4 | 4 | 4 |

### Casos errados por versão

- **v1:** 05, 09, 16, 19
- **v2:** 05, 09, 19 (corrigiu o 16)
- **v3:** 09, 19 (corrigiu o 05 e o 16)

### Leitura

1. **O 16 foi corrigido pela v2 e pela v3.** O few-shot corrigiu o caso que o exemplo demonstrava. O raciocínio guiado corrigiu o 16 e também o 05, por exigir a checagem do estado da funcionalidade antes de olhar o vocabulário.
2. **Os casos 09 e 19 resistiram às três versões.** Quando técnicas diferentes erram os mesmos casos, o problema pode estar no contrato, não só na técnica. No 09, a palavra "senha" aparece em duas definições. O gabarito do 19 é discutível e deve ser revisado em outra rodada, com registro no changelog.
3. **Custo de entrada:** a v1 é a mais barata (314 tokens). A v2 adiciona cerca de 193 tokens por chamada com os exemplos. A v3 adiciona cerca de 182 e fica 11 tokens abaixo da v2.
4. **Zero falha de formato em 60 chamadas.** O contrato de saída de uma palavra funcionou nas três técnicas.

### Teste pareado (dev)

- **v1 × v3:** discordam nos casos 05 e 16, e os dois favorecem a v3. McNemar exato bilateral: **p = 0,5**.
- **v1 × v2:** discordam no caso 16, favorável à v2. **p = 1,0**.
- **v2 × v3:** discordam no caso 05, favorável à v3. **p = 1,0**.

Com essas contagens, nenhuma diferença entre as versões é estatisticamente significativa. O placar mostra o melhor resultado observado nesta amostra, não uma técnica comprovadamente superior.

### Latência

A mediana da v3 (6.663 ms) fica 4% abaixo da v1 (6.911 ms). A v2 é 22% mais lenta que a v1. Com uma rodada e diferenças desse tamanho, a latência não permite conclusão. Médias foram descartadas porque retentativas internas do SDK criaram registros de latência muito altos.

## 2. Conjunto de validação (validation)

Dataset: `evals/validation_cases.csv`, 30 casos (15 claros, 15 ambíguos), 5 execuções por caso, regra de maioria (3 de 5). Os casos foram escritos depois de observados os erros 05, 09, 16 e 19 do dev, então o conjunto **não é cego**.

Critério e changelog registrados antes da rodada da v4. Ver `prompts/changelog.md`.

Comparação v4 × v3, saída de `python src/evaluate.py --set validation --baseline v3 --target v4`:

| Métrica | v3 | v4 |
| --- | --- | --- |
| Casos aprovados | 25/30 (83%) | 26/30 (87%) |
| Execuções corretas | 124/150 (83%) | 132/150 (88%) |
| Claros | 15/15 | 15/15 |
| Ambíguos | 10/15 | 11/15 |
| Falhas de formato | 0 | 0 |
| Latência mediana (ms) | 869 | 1.031 |
| Entrada mediana (tokens) | 492 | 854 |
| Saída mediana (tokens) | 4 | 4 |

Casos reprovados:

- **v3:** V17, V20, V21, V24, V29
- **v4:** V17, V21, V24, V29

Pareado por caso: **1 favorável à v4** (V20), 0 contrários, **p = 1,0**.

### Critérios declarados antes da rodada

1. McNemar p < 0,05 com mais casos favoráveis que contrários: **falhou**.
2. Nenhuma regressão nos casos claros: **ok** (15/15 nas duas).
3. Zero falhas de formato: **ok**.

**Conclusão:** não há evidência de melhora da v4 sobre a v3 neste conjunto. Os casos V17, V21, V24 e V29 continuam reprovados nas duas versões. A v4 tem custo de entrada cerca de 74% maior que a v3 neste conjunto.

### Limitações

- O conjunto não é cego.
- Com um caso discordante, o teste não tem poder estatístico.
- A v4 foi escrita a partir dos erros do dev. Por isso, **não deve ser rodada no dev**: o resultado estaria contaminado.
- Nenhum gabarito foi alterado depois da rodada.

## 3. Decisão

A v3 permanece como referência. A v4 não superou a v3 no conjunto de validação com o critério declarado. Qualquer nova versão exige novo conjunto ou novo critério, declarado antes da rodada, e não pode ser comparada com estes resultados como se fossem de um experimento cego.

## 4. Reprodução

```cmd
python src/generate_cases.py
python src/run_version.py v1
python src/run_version.py v2
python src/run_version.py v3
python src/evaluate.py

python src/run_version.py v3 --set validation
python src/run_version.py v4 --set validation
python src/evaluate.py --set validation --baseline v3 --target v4