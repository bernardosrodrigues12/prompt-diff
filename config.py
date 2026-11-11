from pathlib import Path

MODEL = "gemini-3.6-flash"

TEMPERATURE = 0

MAX_OUTPUT_TOKENS = 512

CATEGORIES = [
    "cobranca",
    "bug_tecnico",
    "duvida_uso",
    "solicitacao_recurso",
    "conta_acesso"    
]

ROOT = Path(__file__).resolve().parent
PROMPTS_FOLDER = ROOT / "prompts"
EVALS = ROOT / "evals"
CASES_FILE = EVALS / "cases.csv"