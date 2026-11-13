# Changelog - evolução dos prompts

Formato por entrada: o que mudou, por quê, e o que a rodada mostrou.

## 2026-11-11 - v1 (baseline)
O que mudou: 
- primeira versão -> papel do classificador, 5 categorias com definição de 1 linha, 2 regras de desempate e formato de saída rígido (uma única palavra, como escrita na lista).

Por quê:
- sem um baseline não existe referência para afirmar se uma técnica melhora ou piora o resultado do prompt. A v1 é propositalmente simples, mas ainda cumpre a tarefa.

Resultado:
- 16/20 (80%).
- claros 13/15, ambíguos 3/5, zero falhas de formato.
- latência mediana: 6.911ms.
- entrada mediana: 314 tokens.

Aprendizado:
- os 2 erros em casos **claros** (05 e 09) foram o principal achado. Erro em caso claro não é falta e técnica, é sinal de definição mal delimitada.


## 2026-11-12 - v2 (few-shot) - exemplo de tom
O que mudou: base da v1 byte a byte + seção "## Exemplos" com 6 pares
mensagem→resposta, inserida entre as regras de desempate e o formato.

Por quê: 
- ancorar o formato de resposta e demonstrar em ação a regra de desempate 1
(pedido imediato > causa), que a v1 não aplicou sozinha no caso 16.

Decisões de desenho: 
- nenhum exemplo vem dos 20 casos.
- 5 exemplos fáceis, um por categoria, e 1 difícil que contém vocabulário de bug mas a resposta é conta_acesso.

Resultado: 
- 17/20 (+1) —> corrigiu exatamente o caso 16, o que o exemplo difícil demonstrava.
- Casos 05, 09 e 19 inalterados. Zero falhas de formato.
- Custo: entrada mediana 507 tokens (+193 por chamada. os 6 exemplos viajam em TODAS
as 20 chamadas; total 10.147 vs 6.287 da v1).
- Latência mediana 8.432 ms (+22% — a
mais lenta das três).

Aprendizado: 
- few-shot corrige a fronteira que ele demonstra. não conserta definições ambíguas.
- Técnica paga entrada por chamada. Custo é parte da comparação.

## 2026-11-12 -v3 (raciocínio guiado)
O que mudou: 
- base da v1 byte a byte + seção "## Procedimento de análise" com 4 passos:
    1. pedido imediato
    2. estado da funcionalidade 
    3. desempate  
    4. confirmação
    pedindo análise interna e mantendo a saída de uma palavra.

Por quê: 
- guiar o raciocínio pela estrutura da decisão do domínio.
- não um "pense passo a passo" genérico, mas um checklist que espelha exatamente as regras de desempate onde a v1 falhou.

Resultado: 
- 18/20 (+2 sobre a v1) —> corrigiu o caso 05 (a checagem do estado da
funcionalidade venceu a âncora da palavra "login", que nem o few-shot venceu).
- Casos 09 e 19 resistiram. Zero falhas de formato. 
- Custo: entrada mediana 496 tokens —> mais barata que a v2 (procedimento custa menos que bloco de exemplos).
- Latência mediana 6.663 ms (a menor, mas a margem de ~4% sobre a v1 está dentro do ruído de rodada única).

**Melhor Resultado Observado**: v3. Será usada de base para a v4, somando com exemplos da v2

## 2026-11-13 - Critério de Avaliação da v4 (antes da rodada)
Versão alvo: 
- v4 (base da v3 + exemplos da v2 + definições de duvida_uso e conta_acesso corrigidas + desempate ajustado para o caso de dúvida × bug).
- Comparada contra: v3 (melhor resultado observado).
- Conjunto: evals/validation_cases.csv — 30 casos novos (15 claros, 15 ambíguos).
- Limitação: o conjunto não é cego. Os casos foram escritos após observação dos erros 05, 09, 16 e 19 do conjunto de desenvolvimento, sem reler essas mensagens.

- Repetições: 5 execuções por caso, por versão (150 chamadas por versão).
- Métrica por caso: caso conta como acerto se ≥ 3 das 5 execuções estiverem corretas.
- Métrica geral: acertos nas 150 execuções, com a proporção por caso reportada junto.

- Critérios de melhora (todos precisam valer):
   1. A v4 tem mais casos com acerto por maioria que a v3, com McNemar exato pareado (bilateral) p < 0,05. Isso exige pelo menos 6 casos favoráveis à v4 e nenhum contrário, ou combinação equivalente.
   2. Nenhuma regressão nos casos claros: acertos da v4 ≥ acertos da v3 nos 15 casos claros.
   3. Zero falhas de formato nas 150 execuções da v4.

   Se algum critério falhar, a v3 permanece como referência e a conclusão registrada será: **"não há evidência de melhora da v4 sobre a v3 neste conjunto"**.

- Regra: estes critérios não são alterados depois da rodada. Se for necessário mudá-los, isso vira uma entrada nova, com a justificativa explícita.

## Infraestrutura: Mudanças que afetaram o experimento

- System Instruction: Os primeiros runs enviaram prompt e mensagem colados num único texto, e o modelo respondeu À META ao invés de classificar.
**Correção**: Prompt inteiro no canal de system_instructionn mensagem como turno do usário. As 7 chamadas afetadas foram descartadas. A mudança ocorreu antes de qualquer versão completar uma rodada, então a comparabilidade entre v1/v2/v3 foi preservada.
- Modelo: gemini-3.6-flash → gemini-3.5-flash-lite. Motivo: free tier do Flash = 5
  req/min e apenas 20 req/DIA (o run morre no meio); o experimento precisa de 60+
  chamadas. Flash-Lite: 500/dia. Todas as rodadas foram refeitas no lite, na mesma
  sessão. Cota conta por projeto, não por chave; reseta à meia-noite do Pacífico.
- Retry: backoff de 15s e 60s apenas para erros transitórios (429 por minuto, 503
  alta demanda). Cota diária (429 "per day") aborta com mensagem clara — não se cura
  esperando 1 minuto. Delay de 15s entre chamadas no runner.


## Lições da semana

1. Canal importa tanto quanto texto: a mesma instrução muda de comportamento quando entra como system instructio em vez de texto colado.
2. Mediana, não média: retentativas internas do SDK criaram registros de 31–110 s
   que inflariam a média ~81%. A média contava uma história falsa.
3. Técnica corrige fronteira demonstrável; definição ambígua nenhuma técnica conserta
   — o caso 09 ("senha" em duas definições) sobreviveu às três versões.
4. Registro bruto primeiro, julgamento depois: como os CSVs guardam a resposta crua,
   o evaluate.py re-julga de graça — nenhuma chamada de API gasta para mudar regra
   de avaliação.
5. Zero falha de formato nas 60 chamadas: contrato de saída rígido aguentou as três
   técnicas. É métrica chata e essencial.
