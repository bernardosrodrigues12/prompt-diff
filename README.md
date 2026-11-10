# prompt-diff

Suíte para comparar três versões de prompt (direta, few-shot e raciocínio guiado)
na mesma tarefa: classificar mensagens de suporte. Mede acertos, erros por
categoria, falhas de formato, tokens e latência, com comparação justa
(mesmo modelo, temperatura 0 e limite de tokens).

## Pré-requisitos

- Python 3.15 (testado na 3.15.2)
- Git

## Instalação

1. Crie e ative o ambiente virtual: `py -3.15 -m venv .venv`
2. Ative: `.venv\Scripts\activate` (Windows) ou `source .venv/bin/activate` (Linux/Mac)
3. Instale as dependências: `pip install -r requirements.txt`

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha `GOOGLE_API_KEY` com sua chave do Google AI Studio.
3. O `.env` nunca vai para o Git (regra no `.gitignore`).

## Como rodar

Em construção — os comandos entram aqui conforme os módulos em `src/` forem criados.

## Estrutura

prompt-diff/
  config.py      # fonte única: modelo, temperatura, tokens, caminhos, categorias
  prompts/       # v1.md, v2.md, v3.md e changelog.md
  testes/        # casos.csv e resultados por versão
  src/           # chamada_modelo.py, rodar_versao.py, avaliar.py