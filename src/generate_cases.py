import csv
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal, get_args

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config

Kind = Literal["clear", "ambiguous"]

@dataclass
class Case:
    id: str
    message: str
    expected_category: str
    kind: Kind
    notes: str = ""

CASES: list[Case] = [
    Case(
        id="01",
        message="Fui cobrado duas vezes na mesma fatura deste mês, o valor de R$ 89,90 apareceu duplicado no meu cartão.",
        expected_category="cobranca",
        kind="clear",
    ),
    Case(
        id="02",
        message="Minha assinatura renovou por um valor diferente do que está anunciado no site, quero entender o motivo.",
        expected_category="cobranca",
        kind="clear",
    ),
    Case(
        id="03",
        message="Fiz a compra em outubro e não recebi a nota fiscal por e-mail, podem verificar?",
        expected_category="cobranca",
        kind="clear",
    ),
    Case(
        id="04",
        message="O aplicativo fecha sozinho sempre que tento exportar um relatório em PDF.",
        expected_category="bug_tecnico",
        kind="clear",
    ),
    Case(
        id="05",
        message="A página de login fica branca depois que clico em entrar, e não aparece nenhuma mensagem de erro.",
        expected_category="bug_tecnico",
        kind="clear",
    ),
    Case(
        id="06",
        message="Os gráficos do painel não carregam desde ontem, fica travado na mensagem de carregando.",
        expected_category="bug_tecnico",
        kind="clear",
    ),
    Case(
        id="07",
        message="Como faço para convidar outros membros da minha equipe para acessar o mesmo plano?",
        expected_category="duvida_uso",
        kind="clear",
    ),
    Case(
        id="08",
        message="Existe alguma forma de programar o envio automático de relatórios por e-mail no sistema?",
        expected_category="duvida_uso",
        kind="clear",
    ),
    Case(
        id="09",
        message="Não encontrei onde troco a senha da minha conta, podem me indicar o caminho no menu?",
        expected_category="duvida_uso",
        kind="clear",
    ),
    Case(
        id="10",
        message="Seria muito útil ter integração com o Google Calendar para sincronizar meus agendamentos.",
        expected_category="solicitacao_recurso",
        kind="clear",
    ),
    Case(
        id="11",
        message="Vocês pretendem aumentar o limite de tamanho para importação de arquivos CSV?",
        expected_category="solicitacao_recurso",
        kind="clear",
    ),
    Case(
        id="12",
        message="Sugiro um modo escuro para o painel administrativo, uso o sistema à noite e cansa a vista.",
        expected_category="solicitacao_recurso",
        kind="clear",
    ),
    Case(
        id="13",
        message="Perdi o acesso ao e-mail cadastrado e não consigo recuperar minha conta pelo fluxo normal.",
        expected_category="conta_acesso",
        kind="clear",
    ),
    Case(
        id="14",
        message="Um funcionário foi desligado da empresa e preciso remover o acesso dele à plataforma.",
        expected_category="conta_acesso",
        kind="clear",
    ),
    Case(
        id="15",
        message="Quero transferir a administração da conta para o e-mail de outro colega do time.",
        expected_category="conta_acesso",
        kind="clear",
    ),
    # --- ambiguous cases ---
    Case(
        id="16",
        message="Meu cartão foi recusado e agora o sistema bloqueou meu login, isso é problema de pagamento ou da minha conta?",
        expected_category="conta_acesso",
        kind="ambiguous",
        notes="Plausíveis: cobranca (causa) e conta_acesso (sintomo). Gabarito: conta_acesso, porque o pedido imediato do usuário é recuperar o acesso.",
    ),
    Case(
        id="17",
        message="Depois da última atualização o botão de exportar desapareceu, e preciso enviar o relatório ao meu gestor ainda hoje.",
        expected_category="bug_tecnico",
        kind="ambiguous",
        notes="Plausíveis: bug_tecnico (função existente sumiu) e duvida_uso (não sabe onde está). Gabarito: bug_tecnico, por ser regressão após atualização; a urgência não muda a categoria.",
    ),
    Case(
        id="18",
        message="Comprei o plano anual, mas os recursos premium não liberaram na minha conta e também não recebi a nota fiscal.",
        expected_category="cobranca",
        kind="ambiguous",
        notes="Plausíveis: cobranca, conta_acesso e bug_tecnico. Gabarito: cobranca, porque tudo desdobra da confirmação da compra; liberação e nota fiscal são consequências.",
    ),
    Case(
        id="19",
        message="Não sei se estou criando a automação do jeito certo, e quando tento salvar aparece um erro.",
        expected_category="duvida_uso",
        kind="ambiguous",
        notes="Plausíveis: duvida_uso e bug_tecnico. Gabarito: duvida_uso, porque a dúvida vem primeiro e o erro pode ser consequência do fluxo incorreto; se o erro persistir no fluxo correto, seria bug.",
    ),
    Case(
        id="20",
        message="Quero cancelar minha assinatura e apagar todos os meus dados do sistema.",
        expected_category="conta_acesso",
        kind="ambiguous",
        notes="Plausíveis: cobranca (cancelamento) e conta_acesso (gestão da conta). Gabarito: conta_acesso, porque o pedido central é sobre a conta e seus dados, não sobre valores.",
    )    
]

def validate(cases: list[Case]) -> None:
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case ids found")

    for case in cases:
        if case.expected_category not in config.CATEGORIES:
            raise ValueError(f"Case {case.id}: invalid category {case.expected_category!r}")
        if case.kind not in get_args(Kind):
            raise ValueError(f"Case {case.id}: invalid kind {case.kind!r}")


def main() -> None:
    validate(CASES)

    config.CASES_FILE.parent.mkdir(parents=True, exist_ok=True)

    fields = ["id", "message", "expected_category", "kind", "notes"]

    with open(config.CASES_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(case) for case in CASES)

    clear = sum(1 for case in CASES if case.kind == "clear")
    ambiguous = len(CASES) - clear
    print(f"Wrote {len(CASES)} cases ({clear} clear, {ambiguous} ambiguous) to {config.CASES_FILE}")


if __name__ == "__main__":
    main()