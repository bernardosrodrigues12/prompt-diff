# Comparativo de versões — classificador de mensagens de suporte

Modelo: `gemini-3.5-flash-lite` · Dataset congelado: 20 casos (15 claros, 5 ambíguos) · Temperatura: 0
Rodadas: 11–12/11/2026, sequenciais na mesma sessão (mesmo modelo, delay e condições de rede)

| Métrica | v1 | v2 | v3 |
| --- | --- | --- | --- |
| Acerto | 16/20 (80%) | 17/20 (85%) | 18/20 (90%) |
| Claros | 13/15 | 13/15 | 14/15 |
| Ambíguos | 3/5 | 4/5 | 4/5 |
| Falhas de formato | 0 | 0 | 0 |
| Latência mediana (ms) | 6911 | 8432 | 6663 |
| Entrada mediana (tokens) | 314 | 507 | 496 |
| Saída mediana (tokens) | 4 | 4 | 4 |

## Leitura dos resultados

1. **Cada técnica corrigiu uma classe diferente de erro.** O few-shot (v2) corrigiu o caso 16 — a fronteira que seu exemplo difícil demonstrava (classificar pelo pedido imediato, não pela causa). O raciocínio guiado (v3) corrigiu o caso 05 — venceu a âncora da palavra "login" exigindo a checagem do estado da funcionalidade antes de olhar o vocabulário.

2. **Os casos 09 e 19 resistiram às três versões.** Quando três técnicas distintas erram os mesmos casos, o problema não é técnica: é o contrato. "Senha" aparece nas definições de `duvida_uso` e `conta_acesso` (caso 09), e o gabarito do 19 é discutível (dúvida com erro de consequência).

3. **A vencedora é também a mais barata entre as técnicas:** 496 tokens de entrada mediana contra 507 da v2 — o procedimento custa menos que o bloco de exemplos. O preço de ambas sobre a base: ~190 tokens por chamada (v1: 6.287 entrada total · v2: 10.147 · v3: 9.927).

4. **Zero falhas de formato nas 60 chamadas.** O contrato de saída rígido (uma palavra) aguentou as três técnicas.

## Latência

Mediana: v3 (6.663 ms) < v1 (6.911 ms) < v2 (8.432 ms). A vantagem da v3 sobre a v1 (~4%) está dentro do ruído de uma rodada única; a diferença robusta é a v2 ser a mais lenta (+22%). As médias foram descartadas: retentativas internas do SDK criaram registros de 31–69 s que distorceriam a comparação.

## Decisão

`v3.md` (raciocínio guiado) é o baseline da v4 (13/11): base v3 + exemplos da v2 + definições corrigidas de `duvida_uso`/`conta_acesso` (caso 09) e desempate mais afiado para o 19. Alvo: resolver 09 e/ou 19 sem perder os 18 acertos atuais. Mesma régua: dataset congelado, `evaluate.py` inalterado.

## Reprodução

    python src/generate_cases.py
    python src/run_version.py v1   # e v2, v3
    python src/evaluate.py